import asyncio
from elasticsearch import AsyncElasticsearch
from typing import List
from halpert.types import Function
from dataclasses import asdict
from pydantic.dataclasses import dataclass

@dataclass
class Input:
  query: str

@dataclass
class Output:
  @dataclass
  class Result:
    link: str
    title: str
    snippet: str
  
  results: List[Result]

async def search_call(
  input: Input,
  index_name: str = 'wikipedia',
  host: str = 'http://localhost:9200',
  snippet_size: int = 300,
) -> Output:
  async with AsyncElasticsearch([host]) as es:
    response = await es.search(index=index_name, query={
      'multi_match': {
        'query': input.query,
        'fields': ['title^2', 'text'],
        # 'fields': ['title', 'text'],
      },
    }, highlight={
      'fields': {
        'title': { 'pre_tags': [''], 'post_tags': [''] },
        'text': { 'pre_tags': [''], 'post_tags': [''], 'fragment_size': snippet_size },
      },
    }, size=10)
  
    return Output(results=[Output.Result(
      link='/wiki/' + hit['_source']['slug'],
      title=hit['_source']['title'],
      snippet=hit['highlight'].get('text', [hit['_source']['text'][:snippet_size]])[0]
     ) for hit in response['hits']['hits']])


search = Function(
  name='Search Wikipedia',
  description='Search Wikipedia by a query',
  Input=Input,
  Output=Output,
  call=lambda input: search_call(input),
)


if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument('--query', type=str, required=True)
  parser.add_argument('--index-name', type=str, default='wikipedia')
  parser.add_argument('--host', type=str, default='http://localhost:9200')
  args = parser.parse_args()

  loop = asyncio.get_event_loop()
  results = loop.run_until_complete(search_call(Input(query=args.query), args.index_name, args.host))
  import json
  print(json.dumps(asdict(results), indent=2))
  print(len(results))
