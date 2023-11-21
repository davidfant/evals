import os
import json
import asyncio
import argparse
import logging
import coloredlogs
import hashlib
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam, ChatCompletion
from tqdm import tqdm
from typing import List, Set
from halpert import Halpert, Sample, Function
from dataclasses import asdict


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
):
  hash = create_hash(messages, model)
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
    'content': 'You are a helpful AI assistant. Follow the instructions and use the available functions to complete the task.',
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
          'name': f.name,
          'description': f.description,
          'parameters': f.input_schema,
        },
      } for f in functions] + [{
        'type': 'function',
        'function': {
          'name': 'done',
          'description': 'Call this function when you are done with the task.',
          'parameters': {
            'type': 'object',
            'properties': {},
          },
        },
      }],
      model=model,
    )

    logger.info(f'Agent Step: {completion.json(indent=2)}')

    choice = completion.choices[0]
    if choice.finish_reason != 'tool_calls':
      logger.warning(f'Unexpected finish reason: {choice.finish_reason}')
      break

    messages.append(choice.message)

    for tc in choice.message.tool_calls:
      if tc.function.name == 'done':
        messages.pop()
        looping = False
        break
      elif fn := next((f for f in functions if f.name == tc.function.name), None):
        functions_called.add(fn.name)
        output = await fn.call(json.loads(tc.function.arguments))
        messages.append({
          'role': 'tool',
          'tool_call_id': tc.id,
          'content': json.dumps(output),
        })
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
        'description': 'Call this function to answer all questions. If you do not know the answer to a specific question, leave it blank.',
        'parameters': {
          'type': 'object',
          'properties': {
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
  parser.add_argument('--model', type=str, default='gpt-3.5-turbo-1106')
  parser.add_argument('--openai-api-key', type=str, required=True)
  args = parser.parse_args()


  openai = OpenAI(api_key=args.openai_api_key)

  coloredlogs.install(fmt='%(levelname)s %(asctime)s %(name)s %(message)s', level=logging.DEBUG)


  functions = [
    Function(
      name='add',
      description='Add two numbers',
      input_schema={
        'type': 'object',
        'properties': {
          'a': { 'type': 'number' },
          'b': { 'type': 'number' },
        },
        'required': ['a', 'b'],
      },
      output_schema={
        'type': 'object',
        'properties': {
          'result': { 'type': 'number' },
        },
        'required': ['result'],
      },
      call=lambda input: resolve({ 'result': input['a'] + input['b'] }),
    ),
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
    )
  ]

  halpert = Halpert(samples, functions)

  for sample, functions in tqdm(halpert.iter()):
    logger.info(f'Running sample: {sample.name}')
    evaluation = await run_agent(sample, functions, openai, args.model)
    logger.info(f'Evaluation: {json.dumps(asdict(evaluation), indent=2)}')
    halpert.submit(sample, evaluation)

  halpert.evaluate()


if __name__ == '__main__':
  asyncio.run(run())
