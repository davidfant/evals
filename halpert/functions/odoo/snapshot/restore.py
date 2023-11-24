import os
import argparse
import tempfile
import zipfile
import shutil
import logging

logger = logging.getLogger(__name__)

def restore_filestore(
  filestore_dir: str,
  odoo_filestore_dir: str,
):
  if not os.path.exists(filestore_dir):
    raise Exception(f'Filestore dir not found: {filestore_dir}')
  if not os.path.exists(odoo_filestore_dir):
    raise Exception(f'Odoo filestore dir not found: {odoo_filestore_dir}')
  
  logger.debug(f'Restoring filestore from {filestore_dir} to {odoo_filestore_dir}')
  shutil.rmtree(odoo_filestore_dir)
  shutil.copytree(filestore_dir, odoo_filestore_dir)


def restore_database(
  dump_path: str,
  odoo_database_url: str,
):
  if not os.path.exists(dump_path):
    raise Exception(f'Dump file not found: {dump_path}')
  
  database_name = odoo_database_url.split('/')[-1]
  # replace database name with postgres database name
  postgres_database_url = '/'.join(odoo_database_url.split('/')[:-1]) + '/postgres'

  logger.debug(f'Dropping database {database_name}')
  os.system(f'psql {postgres_database_url} -c "DROP DATABASE IF EXISTS {database_name} WITH (FORCE)" > /dev/null')

  logger.debug(f'Creating database {database_name}')
  os.system(f'psql {postgres_database_url} -c "CREATE DATABASE {database_name}" > /dev/null')
  
  logger.debug(f'Restoring database from {dump_path}')
  os.system(f'psql {odoo_database_url} < {dump_path} > /dev/null')


def restore(
  name: str,
  snapshot_dir: str,
  odoo_database_url: str,
  odoo_filestore_dir: str,
):
  snapshot_path = os.path.join(snapshot_dir, f'{name}.zip')

  with tempfile.TemporaryDirectory() as temp_dir:
    logger.debug(f'Extracting snapshot {snapshot_path} to {temp_dir}')
    with zipfile.ZipFile(snapshot_path, 'r') as zip_ref:
      zip_ref.extractall(temp_dir)
    
    restore_filestore(os.path.join(temp_dir, 'filestore'), odoo_filestore_dir)
    restore_database(os.path.join(temp_dir, 'dump.sql'), odoo_database_url)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--name', type=str, required=True)
  parser.add_argument('--snapshot-dir', type=str, required=True)
  parser.add_argument('--database-url', type=str, default='postgres://odoo:odoo@localhost:8070/odoo')
  parser.add_argument('--odoo-filestore-dir', type=str, required=True)
  args = parser.parse_args()

  logging.basicConfig(level=logging.DEBUG)

  restore(
    name=args.name,
    snapshot_dir=args.snapshot_dir,
    odoo_database_url=args.database_url,
    odoo_filestore_dir=args.odoo_filestore_dir,
  )
