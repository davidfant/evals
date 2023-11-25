import os
import re
import json
import aiohttp
import asyncio
import argparse
import logging
from tqdm import tqdm
from typing import Dict, AsyncGenerator
from bs4 import BeautifulSoup
from datasets import Dataset
from markdownify import MarkdownConverter, ATX
from markdown import markdown


cache_dir = os.path.expanduser('~/.cache/halpert/wikipedia')


def content(html: str) -> str:
  soup = BeautifulSoup(html, 'html.parser')
  for el in soup(['script', 'style']):
    el.extract()
  for el in soup.find_all(attrs={ 'role': 'note' }):
    el.extract()
  for el in soup.find_all(class_='mw-editsection'):
    el.extract()
  md = MarkdownConverter(strip=['img'], heading_style=ATX).convert_soup(soup)
  md = re.sub(r'\n\n+', '\n\n', md).strip()
  return md


async def load_sample(page_id: int, language: str = 'en') -> Dict:
  cache_path = os.path.join(cache_dir, language, f'{page_id}.json')
  if os.path.exists(cache_path):
    logging.debug(f'Loading from cache: {cache_path}')
    return json.load(open(cache_path, 'r'))

  # https://en.wikipedia.org/w/api.php?action=parse&page=Elon_Musk&format=json&prop=text
  async with aiohttp.ClientSession() as session:
    async with session.get(f'https://{language}.wikipedia.org/w/api.php', params={
      'action': 'parse',
      'pageid': page_id,
      'format': 'json',
      'prop': 'text|revid',
    }) as r:
      response = await r.json()

      soup = BeautifulSoup(response['parse']['text']['*'], 'html.parser')
      for el in soup(['script', 'style']):
        el.extract()
      for el in soup.find_all(attrs={ 'role': 'note' }):
        el.extract()
      for el in soup.find_all(class_='mw-editsection'):
        el.extract()
      for el in soup.find_all(class_='new'):
        el.name = 'span'
        el.attrs = {}
      
      md = MarkdownConverter(strip=['img'], heading_style=ATX).convert_soup(soup)
      md = re.sub(r'\n\n+', '\n\n', md).strip()
      text = BeautifulSoup(markdown(md), features='html.parser').get_text()
      title = response['parse']['title']

      sample = {
        'id': response['parse']['pageid'],
        'slug': title.replace(' ', '_'),
        'title': title,
        'revision_id': response['parse']['revid'],
        'markdown': md,
        'text': text,
      }

      if not os.path.exists(os.path.dirname(cache_path)):
        os.makedirs(os.path.dirname(cache_path))
      json.dump(sample, open(cache_path, 'w'))
      logging.debug(f'Loaded sample: {page_id} {sample["title"]}')
      return sample


async def list_pages(language: str = 'en') -> AsyncGenerator[int, None]:
  params = {
    'action': 'query',
    'list': 'allpages',
    'aplimit': 'max',
    'format': 'json',
  }
  while True:
    logging.info(f'Loading pages: {params}')
    async with aiohttp.ClientSession() as session:
      async with session.get(f'https://{language}.wikipedia.org/w/api.php', params=params) as r:
        response = await r.json()
        for page in response['query']['allpages']:
          yield page['pageid']
        
        if 'continue' not in response:
          break

        params['apcontinue'] = response['continue']['apcontinue']


async def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--language', type=str, default='simple')
  parser.add_argument('--log-level', type=str)
  parser.add_argument('--concurrency', type=int, default=10)
  parser.add_argument('--cache-only', action='store_true')
  parser.add_argument('--limit', type=int)
  args = parser.parse_args()

  if args.log_level:
    logging.basicConfig(level=args.log_level)


  if args.cache_only:
    language_cache_dir = os.path.join(cache_dir, args.language)
    samples = []

    file_names = os.listdir(language_cache_dir)
    if args.limit:
      file_names = file_names[:args.limit]
    for file_name in tqdm(file_names):
      path = os.path.join(language_cache_dir, file_name)
      logging.info(f'Loading from cache: {path}')
      samples.append(json.load(open(path)))
  else:
    tasks = []
    semaphore = asyncio.Semaphore(args.concurrency)
    count = 0
    async for page in list_pages(args.language):
      if args.limit and count >= args.limit:
        break

      logging.info(f'Loading page #{count}: {page}')
      async with semaphore:
        task = asyncio.create_task(load_sample(page, args.language))
        count += 1
        tasks.append(task)
        if len(tasks) >= 10:
          await asyncio.gather(*tasks)
          tasks = []

    samples = await asyncio.gather(*tasks)

  dataset = Dataset.from_dict({ k: [s[k] for s in samples] for k in samples[0].keys() })
  dataset.push_to_hub(f'davidfant/wikipedia-{args.language}')


if __name__ == '__main__':
  asyncio.run(main())
