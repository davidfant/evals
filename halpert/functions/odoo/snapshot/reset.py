import logging
import subprocess

logger = logging.getLogger(__name__)

def main():
  logger.debug('Removing existing filestore dir')
  subprocess.run('docker exec -it odoo /bin/bash -c "rm -rf /var/lib/odoo/filestore/odoo"', shell=True, check=True)

  username = 'odoo'
  password = 'odoo'
  database = 'odoo'
  host = 'odoo-db'
  container_name = 'odoo'

  logger.debug('Dropping database')
  subprocess.run(f'docker exec -it {container_name} /bin/bash -c "PGPASSWORD={password} psql -d postgres -U {username} -h {host} -c \\"DROP DATABASE IF EXISTS {database} WITH (FORCE)\\"" > /dev/null', shell=True, check=True)

  logger.debug('Initializing Odoo')
  subprocess.run(f'docker exec -it {container_name} /bin/bash -c "odoo --init base --database {database} --without-demo all --db_host {host} --db_user {username} --db_password {password} --stop-after-init" > /dev/null', shell=True, check=True)

  logger.info('Reset Odoo')


if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  main()
