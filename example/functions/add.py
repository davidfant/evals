from halpert import Function
from pydantic.dataclasses import dataclass

async def resolve(x):
  return x

@dataclass
class Input:
  a: int
  b: int
  
@dataclass
class Output:
  result: int

add = Function(
  name='Add',
  description='Add two numbers',
  Input=Input,
  Output=Output,
  call=lambda input: resolve(Output(result=input.a + input.b)),
)
