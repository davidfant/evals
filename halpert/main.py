from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from .types import Sample, Function

@dataclass
class Halpert:
  samples: List[Sample]
  functions: List[Function]
  evaluations: Dict[int, Sample.Evaluation] = field(default_factory=dict)


  def submit(self, sample: Sample, evaluation: Sample.Evaluation):
    idx = self.samples.index(sample)
    self.evaluations[idx] = evaluation


  def evaluate(self):
    assert len(self.samples) == len(self.evaluations)
    
    for index, sample in enumerate(self.samples):
      evaluation = self.evaluations[index]
      quiz_answers_correct = [
        sample.expected.quiz[i].answer == evaluation.quiz[i].answer
        for i in range(len(sample.expected.quiz))
      ]

      expected_functions_used = set(evaluation.functions) & set(sample.expected.functions)

      # TODO: create some kind of evaluation


  def iter(self) -> List[Tuple[Sample, List[Function]]]:
    return [
      (sample, [f for f in self.functions if f.name in sample.functions])
      for sample in self.samples
    ]
  
