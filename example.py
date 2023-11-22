import os
import json
import asyncio
import argparse
import logging
import coloredlogs
import hashlib
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam, ChatCompletion, ChatCompletionNamedToolChoiceParam
from tqdm import tqdm
from typing import List, Set
from halpert import Halpert, Sample, Function
from dataclasses import asdict
from pydantic.dataclasses import dataclass
import halpert.functions.wikipedia


logger = logging.getLogger('halpert')


async def resolve(x):
  return x


def create_hash(*args) -> str:
  data: List[str] = []
  for arg in args:
    if isinstance(arg, list):
      data.extend([create_hash(i) for i in arg])
    elif isinstance(arg, dict):
      data.append(json.dumps(arg, sort_keys=True))
    elif hasattr(arg, 'json'):
      data.append(arg.json())
    else:
      data.append(arg)
  return (
    hashlib
      .md5(json.dumps(data, sort_keys=True).encode('utf-8'))
      .hexdigest()
  )


def complete(
  openai: OpenAI,
  messages: List[ChatCompletionMessageParam],
  tools: List[ChatCompletionToolParam],
  model: str,
  tool_choice: ChatCompletionNamedToolChoiceParam | None = None,
):
  hash = create_hash(messages, model, tools, tool_choice)
  cache_path = os.path.join(os.path.expanduser('~'), '.cache', 'halpert', 'openai', f'{hash}.json')
  if os.path.exists(cache_path):
    logger.info(f'Loading from cache: {cache_path}')
    with open(cache_path, 'r') as f:
      return ChatCompletion(**json.load(f))

  completion = openai.chat.completions.create(
    messages=messages,
    tools=tools,
    model=model,
    temperature=0,
    seed=42,
    tool_choice=tool_choice or 'auto',
  )
  if not os.path.exists(os.path.dirname(cache_path)):
    os.makedirs(os.path.dirname(cache_path))
  with open(cache_path, 'w') as f:
    json.dump(completion.dict(), f, indent=2)
  return completion

async def run_agent(
  sample: Sample,
  functions: List[Function],
  openai: OpenAI,
  model: str,
) -> Sample.Evaluation:
  functions_called: Set[str] = set()
  messages: List[ChatCompletionMessageParam] = [{
    'role': 'system',
    'content': 'You are a helpful AI assistant. Follow the instructions and use the available functions to complete the task. Always call functions, and never respond with a text message! Do not make any assumptions about the task, and do not use any outside knowledge.',
  }, {
    'role': 'user',
    'content': sample.instructions,
  }]

  looping = True
  while looping:
    completion = complete(
      openai,
      messages=messages,
      tools=[{
        'type': 'function',
        'function': {
          'name': f.slug,
          'description': f.description,
          'parameters': f.Input.__pydantic_model__.schema(),
        },
      } for f in functions] + [{
        'type': 'function',
        'function': {
          'name': 'done',
          'description': 'Call this function when you are done with the task.',
          'parameters': { 'type': 'object', 'properties': {} },
        },
      }],
      model=model,
    )

    logger.info(f'Agent Step: {completion.json(indent=2)}')

    choice = completion.choices[0]
    if choice.finish_reason != 'tool_calls':
      logger.warning(f'Unexpected finish reason: {choice.finish_reason}')
      break

    messages.append({
      'role': 'assistant',
      'tool_calls': choice.message.dict()['tool_calls'],
    })

    for tc in choice.message.tool_calls:
      if tc.function.name == 'done':
        messages.pop()
        looping = False
        break
      elif fn := next((f for f in functions if f.slug == tc.function.name), None):
        functions_called.add(fn.slug)
        output = await fn.call(fn.Input(**json.loads(tc.function.arguments)))
        messages.append({
          'role': 'tool',
          'tool_call_id': tc.id,
          'content': json.dumps(asdict(output)),
        })

        logger.info(f'Function call: {fn.slug}({tc.function.arguments}) -> {json.dumps(asdict(output), indent=2)}')
      else:
        logger.warning(f'Unexpected function call: {tc.function.name}')
        looping = False
        break
  
  completion = complete(
    openai,
    messages=[{
      'role': 'system',
      'content': 'You are a helpful AI assistant. Answer the questions based on the messages so far using the answer function. Question:\n' + '\n'.join([f'{i}. {q.question}' for i, q in enumerate(sample.expected.quiz)]),
    }] + messages[1:],
    tools=[{
      'type': 'function',
      'function': {
        'name': 'answer',
        'description': 'Call this function to answer all questions. If you do not know the answer to a specific question, enter an empty string. VERY IMPORTANT: answer all questions, even if you do not know the answer to some of them.',
        'parameters': {
          'type': 'object',
          'properties': {
            'num_questions': { 'type': 'integer' },
            'answers': {
              'type': 'array',
              'items': { 'type': 'string' },
            },
          },
          'required': ['answers'],
        },
      },
    }],
    model=model,
    tool_choice={ 'type': 'function', 'function': { 'name': 'answer' } },
  )

  logger.info(f'Agent Questions: {completion.json(indent=2)}')
  answers = json.loads(completion.choices[0].message.tool_calls[0].function.arguments)['answers']

  return Sample.Evaluation(
    functions=list(functions_called),
    quiz=[
      Sample.Evaluation.QuizItem(question=q.question, answer=a)
      for q, a in zip(sample.expected.quiz, answers)
    ],
  )



async def run():
  parser = argparse.ArgumentParser()
  parser.add_argument('--model', type=str, default='gpt-4-1106-preview')
  parser.add_argument('--openai-api-key', type=str, required=True)
  args = parser.parse_args()

  openai = OpenAI(api_key=args.openai_api_key)

  coloredlogs.install(fmt='%(levelname)s %(asctime)s %(name)s %(message)s', level=logging.DEBUG)

  @dataclass
  class AddInput:
    a: int
    b: int
  
  @dataclass
  class AddOutput:
    result: int

  functions = [
    Function(
      name='add',
      description='Add two numbers',
      Input=AddInput,
      Output=AddOutput,
      call=lambda input: resolve(AddOutput(result=input.a + input.b)),
    ),
    halpert.functions.wikipedia.search,
    halpert.functions.wikipedia.read_page,
  ]
  samples = [
    Sample(
      name='Add two numbers',
      instructions='What is 1782937829 + 973912412?',
      functions=['add'],
      expected=Sample.Evaluation(
        functions=['add'],
        quiz=[
          Sample.Evaluation.QuizItem(question='What is the first term?', answer='1782937829'),
          Sample.Evaluation.QuizItem(question='What is the second term?', answer='973912412'),
          Sample.Evaluation.QuizItem(question='What is the sum?', answer='2756850241'),
        ],
      )
    ),
    Sample(
      name='Search Wikipedia',
      instructions='Research the year 1092',
      functions=[
        halpert.functions.wikipedia.search.slug,
        halpert.functions.wikipedia.read_page.slug,
      ],
      expected=Sample.Evaluation(
        functions=[
          halpert.functions.wikipedia.search.slug,
          halpert.functions.wikipedia.read_page.slug,
        ],
        quiz=[
          Sample.Evaluation.QuizItem(question='What day of the week did the year start?', answer='Thursday'),
          Sample.Evaluation.QuizItem(question='What did England annex?', answer='Cumbria'),
        ],
      ),
    ),
  ]

  eval = Halpert(samples, functions)

  for sample, functions in tqdm(eval.iter()):
    logger.info(f'Running sample: {sample.name}')
    evaluation = await run_agent(sample, functions, openai, args.model)
    logger.info(f'Evaluation: {json.dumps(asdict(evaluation), indent=2)}')
    eval.submit(sample, evaluation)

  eval.evaluate()


if __name__ == '__main__':
  asyncio.run(run())
