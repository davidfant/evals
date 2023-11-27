import os
import subprocess
import argparse
import tempfile
import zipfile
import shutil
import logging

logger = logging.getLogger(__name__)

default_database_url = 'postgres://odoo:odoo@localhost:8070/odoo'
default_filestore_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'filestore', 'odoo')

def restore_filestore(
  filestore_dir: str,
  odoo_filestore_dir: str,
):
  if not os.path.exists(filestore_dir):
    raise Exception(f'Filestore dir not found: {filestore_dir}')
  if os.path.exists(odoo_filestore_dir):
    logger.debug(f'Removing existing filestore dir: {odoo_filestore_dir}')
    shutil.rmtree(odoo_filestore_dir)
  
  logger.debug(f'Restoring filestore from {filestore_dir} to {odoo_filestore_dir}')
  if not os.path.exists(os.path.dirname(odoo_filestore_dir)):
    os.makedirs(os.path.dirname(odoo_filestore_dir))
  shutil.copytree(filestore_dir, odoo_filestore_dir)


def restore_database(
  dump_path: str,
  odoo_database_url: str,
):
  if not os.path.exists(dump_path):
    raise Exception(f'Dump file not found: {dump_path}')

  # delete and recreate schema public
  logger.debug(f'Dropping schema public')
  subprocess.run(f'psql {odoo_database_url} -c "DROP SCHEMA IF EXISTS public CASCADE" > /dev/null', shell=True, check=True)
  subprocess.run(f'psql {odoo_database_url} -c "CREATE SCHEMA public" > /dev/null', shell=True, check=True)
  
  logger.debug(f'Restoring database from {dump_path}')
  subprocess.run(f'psql {odoo_database_url} < {dump_path} > /dev/null', shell=True, check=True)


def restore(
  name: str,
  snapshot_dir: str,
  odoo_database_url: str = default_database_url,
  odoo_filestore_dir: str = default_filestore_dir,
):
  snapshot_path = os.path.join(snapshot_dir, f'{name}.zip')
  logger.info(f'Restoring snapshot {name} from {snapshot_path}')

  with tempfile.TemporaryDirectory() as temp_dir:
    logger.debug(f'Extracting snapshot {snapshot_path} to {temp_dir}')
    with zipfile.ZipFile(snapshot_path, 'r') as zip_ref:
      zip_ref.extractall(temp_dir)
    
    restore_filestore(os.path.join(temp_dir, 'filestore'), odoo_filestore_dir)
    restore_database(os.path.join(temp_dir, 'dump.sql'), odoo_database_url)
  
  logger.info(f'Restored snapshot {name}')


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--name', type=str, required=True)
  parser.add_argument('--snapshot-dir', type=str, required=True)
  parser.add_argument('--database-url', type=str, default=default_database_url)
  args = parser.parse_args()

  logging.basicConfig(level=logging.DEBUG)

  restore(
    name=args.name,
    snapshot_dir=args.snapshot_dir,
    odoo_database_url=args.database_url,
  )
