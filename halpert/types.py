from abc import ABC
from pydantic import BaseModel
from typing import List, Callable, Awaitable, Type


class Function(BaseModel, ABC):
  name: str
  description: str
  icon: str | None = None

  Input: Type[BaseModel]
  Output: Type[BaseModel]

  call: Callable[['Function.Input'], Awaitable['Function.Output']]

  @property
  def slug(self):
    return self.name.lower().replace(' ', '_')


class Sample(BaseModel):
  class Evaluation(BaseModel):
    class QuizItem(BaseModel):
      question: str
      answer: str

    functions: List[str]
    quiz: List[QuizItem]

  name: str
  instructions: str
  date: str = '2023-11-26'
  functions: List[Function]
  expected: Evaluation
  Input: Type[BaseModel] | None = None
  input: BaseModel | None = None


class OdooSample(Sample):
  snapshot: str

