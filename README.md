# Halpert

## Odoo

### Create Snapshot
```bash
SNAPSHOT_NAME=...
SNAPSHOT_DIR=path/to/snapshots

python3 -m halpert.functions.odoo.snapshot.create --name $SNAPSHOT_NAME --snapshot-dir $SNAPSHOT_DIR
```