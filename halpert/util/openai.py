import os
import json
import logging
import hashlib
import openai
# from openai import OpenAI
# from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam, ChatCompletion, ChatCompletionNamedToolChoiceParam
from typing import List, Dict

ChatCompletionMessageParam = Dict
ChatCompletionToolParam = Dict
ChatCompletionNamedToolChoiceParam = str


logger = logging.getLogger(__name__)


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
  messages: List[ChatCompletionMessageParam],
  model: str,
  tools: List[ChatCompletionToolParam] = [],
  tool_choice: ChatCompletionNamedToolChoiceParam | None = None,
):
  hash = create_hash(messages, model, tools, tool_choice)
  cache_path = os.path.join(os.path.expanduser('~'), '.cache', 'halpert', 'openai-0.27.8', f'{hash}.json')
  if os.path.exists(cache_path):
    logger.info(f'Loading from cache: {cache_path}')
    with open(cache_path, 'r') as f:
      # return ChatCompletion(**json.load(f))
      return openai.openai_object.OpenAIObject.construct_from(json.load(f))

  # completion = OpenAI().chat.completions.create(
  completion = openai.ChatCompletion.create(
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
    # json.dump(completion.dict(), f, indent=2)
    json.dump(completion, f, indent=2)
  return completion
