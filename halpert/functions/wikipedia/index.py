import os
import json
import asyncio
import logging
from tqdm import tqdm
from elasticsearch import Elasticsearch

logger = logging.getLogger('halpert')

async def main(index_name: str = 'wikipedia', host: str = 'http://localhost:9200'):
  es = Elasticsearch([host])

  settings = {
    'mappings': {
      'properties': {
        'id': { 'type': 'keyword' },
        'slug': { 'type': 'text' },
        'title': { 'type': 'text' },
        'markdown': { 'type': 'text' },
        'text': { 'type': 'text' }
      }
    }
  }

  if es.indices.exists(index=index_name):
    # TODO: return?z
    es.indices.delete(index=index_name)

  es.indices.create(index=index_name, body=settings)

  cache_dir = os.path.expanduser('~/.cache/halpert/wikipedia/simple')
  for filename in tqdm(os.listdir(cache_dir), desc='Indexing Wikipedia'):
    path = os.path.join(cache_dir, filename)
    sample = json.load(open(path))
    es.index(index=index_name, id=sample['id'], body=sample)


if __name__ == '__main__':
  asyncio.run(main())
