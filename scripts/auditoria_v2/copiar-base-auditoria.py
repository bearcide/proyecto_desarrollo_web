"""Copia consistente de una base de auditoría a un archivo nuevo, sin cambiar la fuente."""
import argparse
import sqlite3
from contextlib import closing
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('origen', type=Path)
parser.add_argument('destino', type=Path)
args = parser.parse_args()
source, dest = args.origen.resolve(), args.destino.resolve()
assert all(db.name.startswith('demo_pagos_auditoria_') and db.suffix == '.sqlite3' for db in (source, dest))
assert source.parent == dest.parent and source.is_file()
with dest.open('xb'):
    pass
dest.chmod(0o600)
with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)) as reader:
    with closing(sqlite3.connect(dest)) as writer:
        reader.backup(writer)
print(dest)
