from halpert import Function
from pydantic import BaseModel

async def resolve(x):
  return x

class Input(BaseModel):
  a: int
  b: int
  
class Output(BaseModel):
  result: int

add = Function(
  name='Add',
  description='Add two numbers',
  Input=Input,
  Output=Output,
  call=lambda input: resolve(Output(result=input.a + input.b)),
)
