from abc import ABC, abstractmethod
from pydantic.dataclasses import dataclass
from typing import List, Dict, Callable, Awaitable, Type, Any as Dataclass

@dataclass
class Function(ABC):
  name: str
  description: str

  Input: Type[Dataclass]
  Output: Type[Dataclass]

  call: Callable[['Function.Input'], Awaitable['Function.Output']]

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
  functions: List[Function]
  expected: Evaluation
  Input: Type[Dataclass] | None = None
  input: Dataclass | None = None

