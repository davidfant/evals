from dataclasses import dataclass, field, replace
from typing import Dict, List, Tuple
from .types import Sample, Function


def monkey_patch_function_call(function: Function, sample_idx: int, halpert: 'Halpert'):
  original_call = function.call
  def call(*args, **kwargs):
    if not sample_idx in halpert._sample_functions:
      halpert._sample_functions[sample_idx] = []
    halpert._sample_functions[sample_idx].append(function.slug)

    return original_call(*args, **kwargs)
  function.call = call


@dataclass
class Halpert:
  samples: List[Sample]
  functions: List[Function]

  _sample_functions: Dict[int, List[str]] = field(default_factory=dict)
  _sample_quiz: Dict[int, List[Sample.Evaluation.QuizItem]] = field(default_factory=dict)


  def get_functions(self, sample: Sample) -> List[Function]:
    idx = self.samples.index(sample)
    functions = [replace(f) for f in self.functions if f.slug in sample.functions]
    for f in functions:
      monkey_patch_function_call(f, idx, self)
    return functions


  def submit(self, sample: Sample, quiz: List[Sample.Evaluation.QuizItem]):
    idx = self.samples.index(sample)
    self._sample_quiz[idx] = quiz


  def evaluate(self):
    assert list(range(len(self.samples))) == sorted(self._sample_functions.keys())
    assert list(range(len(self.samples))) == sorted(self._sample_quiz.keys())
    
    for index, sample in enumerate(self.samples):
      function_slugs_called = self._sample_functions[index]
      quiz = self._sample_quiz[index]

      quiz_answers_correct = [
        sample.expected.quiz[i].answer == (quiz[i].answer if i < len(quiz) else None)
        for i in range(len(sample.expected.quiz))
      ]

      expected_functions_used = set(function_slugs_called) & set(sample.expected.functions)

      # TODO: create some kind of evaluation

