import asyncio
from elasticsearch import AsyncElasticsearch

async def search_documents(query: str, index_name: str = 'wikipedia', host: str = 'http://localhost:9200'):
  async with AsyncElasticsearch([host]) as es:
    response = await es.search(index=index_name, query={
      'multi_match': {
        'query': query,
        'fields': ['title^2', 'text'],
        # 'fields': ['title', 'text'],
      },
    }, highlight={
      'fields': {
        'title': { 'pre_tags': [''], 'post_tags': [''] },
        'text': { 'pre_tags': [''], 'post_tags': [''], 'fragment_size': 300 },
      },
    }, size=10)

    return [{
      'id': hit['_id'],
      'title': hit['_source']['title'],
      'snippet': hit['highlight'].get('text', [hit['_source']['text'][:300]])[0]
    } for hit in response['hits']['hits']]


if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument('--query', type=str, required=True)
  parser.add_argument('--index-name', type=str, default='wikipedia')
  parser.add_argument('--host', type=str, default='http://localhost:9200')
  args = parser.parse_args()

  loop = asyncio.get_event_loop()
  results = loop.run_until_complete(search_documents(args.query, args.index_name, args.host))
  import json
  print(json.dumps(results, indent=2))
  print(len(results))
