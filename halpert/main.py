from pydantic import BaseModel, Field
from typing import Dict, List, Tuple
from .types import Sample, OdooSample, Function


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

  sample_functions_: Dict[int, List[str]] = Field(default_factory=dict)
  sample_quiz_: Dict[int, List[Sample.Evaluation.QuizItem]] = Field(default_factory=dict)


  def get_functions(self, sample: Sample) -> List[Function]:
    idx = self.samples.index(sample)
    functions = [Function(**f.dict()) for f in sample.functions]
    for f in functions:
      monkey_patch_function_call(f, idx, self)
    return functions
  
  # TODO: prepare fn


  def submit(self, sample: Sample, quiz: List[Sample.Evaluation.QuizItem]):
    idx = self.samples.index(sample)
    self.sample_quiz_[idx] = quiz


  def evaluate(self):
    assert list(range(len(self.samples))) == sorted(self.sample_functions_.keys())
    assert list(range(len(self.samples))) == sorted(self.sample_quiz_.keys())
    
    for index, sample in enumerate(self.samples):
      function_slugs_called = self.sample_functions_[index]
      quiz = self.sample_quiz_[index]

      quiz_answers_correct = [
        sample.expected.quiz[i].answer == (quiz[i].answer if i < len(quiz) else None)
        for i in range(len(sample.expected.quiz))
      ]

      expected_functions_used = set(function_slugs_called) & set(sample.expected.functions)

      # TODO: create some kind of evaluation

