import asyncio
from elasticsearch import AsyncElasticsearch
from typing import List
from halpert.types import Function
from pydantic.dataclasses import dataclass

@dataclass
class Input:
  link: str

@dataclass
class Output:
  @dataclass
  class Page:
    title: str
    content: str
  
  page: Page | None

async def read_page_call(
  input: Input,
  index_name: str = 'wikipedia',
  host: str = 'http://localhost:9200',
  snippet_size: int = 300,
) -> Output:
  async with AsyncElasticsearch([host]) as es:
    slug = input.link.replace('/wiki/', '')
    # match document by slug
    response = await es.search(index=index_name, query={
      'match': { 'slug': slug },
    }, size=1)

    if len(response['hits']['hits']) == 0:
      return Output(page=None)
    hit = response['hits']['hits'][0]['_source']
    return Output(page=Output.Page(
      title=hit['title'],
      content=hit['markdown'],
    ))


read_page = Function(
  name='Read Wikipedia Page',
  description='Read a Wikipedia page by a link',
  Input=Input,
  Output=Output,
  call=lambda input: read_page_call(input),
)
