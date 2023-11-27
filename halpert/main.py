import arrow
import logging
from tabulate import tabulate
from pydantic import BaseModel, Field
from typing import Dict, List
from .types import Sample, OdooSample, Function


logger = logging.getLogger(__name__)


def monkey_patch_function_call(function: Function, sample_idx: int, halpert: 'Halpert'):
  original_call = function.call
  def call(*args, **kwargs):
    if not sample_idx in halpert.sample_functions_:
      halpert.sample_functions_[sample_idx] = []
    halpert.sample_functions_[sample_idx].append(function.slug)

    return original_call(*args, **kwargs)
  function.call = call


class Halpert(BaseModel):
  samples: List[Sample]
  odoo_snapshot_dir: str | None = None

  sample_functions_: Dict[int, List[str]] = Field(default_factory=dict)
  sample_quiz_: Dict[int, List[Sample.Evaluation.QuizItem]] = Field(default_factory=dict)


  def prepare(self, sample: Sample) -> List[Function]:
    if isinstance(sample, OdooSample):
      from halpert.functions.odoo.snapshot.restore import restore as restore_odoo_snapshot

      if not self.odoo_snapshot_dir:
        raise ValueError('odoo_snapshot_dir must be set when using OdooSample')
      restore_odoo_snapshot(sample.snapshot, self.odoo_snapshot_dir)
    
    def utcnow():
      return arrow.get(sample.date)
    arrow.utcnow = utcnow

    idx = self.samples.index(sample)
    functions = [Function(**f.dict()) for f in sample.functions]
    for f in functions:
      monkey_patch_function_call(f, idx, self)
    return functions


  def submit(self, sample: Sample, quiz: List[Sample.Evaluation.QuizItem]):
    idx = self.samples.index(sample)
    self.sample_quiz_[idx] = quiz


  def evaluate(self):
    assert list(range(len(self.samples))) == sorted(self.sample_functions_.keys())
    assert list(range(len(self.samples))) == sorted(self.sample_quiz_.keys())
    
    quiz_answers = []
    results = []
    for index, sample in enumerate(self.samples):
      function_slugs_called = self.sample_functions_[index]
      quiz = self.sample_quiz_[index]

      quiz_answers_correct = [
        expected.answer == (quiz[i].answer if i < len(quiz) else False)
        for i, expected in enumerate(sample.expected.quiz)
      ]
      quiz_answers.extend([{
        'Sample': sample.name,
        'Question': expected.question,
        'Expected': expected.answer,
        'Actual': quiz[i].answer if i < len(quiz) else '',
        'Correct': quiz_answers_correct[i],
      } for i, expected in enumerate(sample.expected.quiz)])

      expected_functions_used = set(function_slugs_called) & set(sample.expected.functions)

      results.append({
        'Sample': sample.name,
        'Quiz Score': sum(quiz_answers_correct) / len(quiz_answers_correct),
        'Functions Score': len(expected_functions_used) / len(sample.expected.functions),
        'Steps': len(function_slugs_called),
      })
    
    table = tabulate({ k: [r[k] for r in quiz_answers] for k in quiz_answers[0].keys() }, headers='keys')
    logger.info('Quiz Answers:\n' + table)

    table = tabulate({ k: [r[k] for r in results] for k in results[0].keys() }, headers='keys')
    logger.info('Evaluation:\n' + table)

