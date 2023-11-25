import os
import asyncio
import aiohttp
import argparse
import logging

async def main(
  odoo_host: str,
  odoo_database: str,
  odoo_master_password: str,
  output_path: str,
):
  async with aiohttp.ClientSession() as session:
    data = {
      'master_pwd': odoo_master_password,
      'name': odoo_database,
      'backup_format': 'zip',
    }
    async with session.post(
      f'{odoo_host}/web/database/backup',
      data=data,
    ) as resp:
      if resp.status != 200:
        raise Exception(f'Failed to create a backup. Status: {resp.status}')
      
      logging.info(f'Saving backup to: {output_path}')
      
      with open(output_path, 'wb') as file:
        while True:
          chunk = await resp.content.read(1024)
          if not chunk:
            break
          file.write(chunk)
      
      logging.info('Done')


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--name', type=str, required=True)
  parser.add_argument('--snapshot-dir', type=str, required=True)
  parser.add_argument('--host', type=str, default='http://localhost:8069')
  parser.add_argument('--database', type=str, default='odoo')
  parser.add_argument('--master-password', type=str, default='odoo')
  args = parser.parse_args()

  logging.basicConfig(level=logging.DEBUG)

  output_path = os.path.join(args.snapshot_dir, f'{args.name}.zip')
  asyncio.run(main(
    odoo_host=args.host,
    odoo_database=args.database,
    odoo_master_password=args.master_password,
    output_path=output_path,
  ))
