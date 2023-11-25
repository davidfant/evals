import os
import json
import asyncio
import logging
from tqdm import tqdm
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from datasets import load_dataset, Dataset

logger = logging.getLogger('halpert')

def generate_data(dataset: Dataset, index_name: str):
  for sample in tqdm(dataset, desc='Indexing'):
    yield {
      "_index": index_name,
      "_id": sample['id'],
      "_source": sample
    }

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
    es.indices.delete(index=index_name)

  es.indices.create(index=index_name, body=settings)

  dataset = load_dataset('davidfant/wikipedia-simple')['train']
  bulk(es, generate_data(dataset, index_name))
  


if __name__ == '__main__':
  asyncio.run(main())
