import json
import logging
from pydantic.dataclasses import dataclass
from dataclasses import field, asdict
from halpert.types import Function
from typing import List, Tuple, Literal
from halpert.util.openai import complete


@dataclass
class Input:
  message: str

@dataclass
class Output:
  message: str | None

@dataclass
class Context:
  persona: str
  history: List[Tuple[Literal['input', 'output'], str]] = field(default_factory=list)


@dataclass
class PersonaResponse:
  reasoning: str
  should_respond: bool
  message: str | None


logger = logging.getLogger(__name__)


async def send_message_call(input: Input, context: Context) -> Output:
  context.history.append(('input', input.message))
  completion = complete(
    messages=[
      { 'role': 'system', 'content': f'You are role playing the following persona: {context.persona}. Use the process function to either respond with a message or not when someone sends you a message. Make sure to closely follow the persona.' },
      *[{
        'role': 'user' if source == 'input' else 'assistant',
        'content': message,
      } for source, message in context.history]
    ],
    tools=[{
      'type': 'function',
      'function': {
        'name': 'process',
        'description': 'Process a message by either responding with a message or not.',
        'parameters': PersonaResponse.__pydantic_model__.schema(),
      }
    }],
    model='gpt-4-1106-preview'
  )

  args = completion.choices[0].message.tool_calls[0].function.arguments
  response = PersonaResponse(**json.loads(args))
  logger.debug(f'Persona Response: {json.dumps(asdict(response), indent=2)}')

  output = Output(message=response.message)
  if output.message:
    context.history.append(('output', input.message))
  return output


def send_message_with_context(persona: str, history: List[Tuple[Literal['input', 'output'], str]] = []) -> Function:
  context = Context(persona=persona, history=history)
  return Function(
    name='Send Message',
    description='Send a message',
    Input=Input,
    Output=Output,
    call=lambda input: send_message_call(input, context),
  )


send_message = send_message_with_context(persona='Helpful assistant')
