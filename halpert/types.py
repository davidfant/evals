from abc import ABC, abstractmethod
from pydantic.dataclasses import dataclass
from typing import List, Dict, Callable, Awaitable, Type

@dataclass
class Function(ABC):
  name: str
  description: str

  Input: Type[dataclass]
  Output: Type[dataclass]

  call: Callable[[dataclass], Awaitable[dataclass]]

  @property
  def slug(self):
    return self.name.lower().replace(' ', '_')


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
