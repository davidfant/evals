from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Callable, Awaitable

@dataclass
class Function(ABC):
  name: str
  description: str

  input_schema: Dict
  output_schema: Dict

  call: Callable[[Dict], Awaitable[Dict]]


@dataclass
class Sample:
  @dataclass
  class Evaluation:
    @dataclass
    class QuizItem:
      question: str
      answer: str

    functions: List[str]
    quiz: List[QuizItem]

  name: str
  instructions: str
  functions: List[str]

  expected: Evaluation
