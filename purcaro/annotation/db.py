#!/usr/bin/env python

import os, sys, json, psycopg2, argparse

sys.path.append(os.path.join(os.path.dirname(__file__), '../../utils/'))
from utils import Utils
from dbs import DBS

def setupDB(cur):
    cur.execute("""
DROP TABLE IF EXISTS search;
CREATE TABLE search
(id serial PRIMARY KEY,
assembly text,
assays text,
tissues text,
loci text,
uid text UNIQUE NOT NULL,
hubNum integer
) """)

class AnnotationDB:
    def __init__(self, dbs):
        if not dbs:
            dbs = DBS.pgdsn("Annotations")
            dbs["application_name"] = os.path.realpath(__file__)
        self.dbs = dbs
        self._conn = psycopg2.connect(**dbs)
        self._conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED)

    def insertOrUpdate(self, assembly, assays, tissues, loci, uid):
        with self._conn:
            with self._conn.cursor() as curs:
                curs.execute("""
SELECT id FROM search
WHERE uid = %(uid)s
""", {"uid" : uid})
                if (curs.rowcount > 0):
                    curs.execute("""
UPDATE search
SET
assembly = %(assembly)s,
assays = %(assays)s,
tissues = %(tissues)s,
loci = %(loci)s,
hubNum = hubNum + 1
WHERE uid = %(uid)s
RETURNING hubNum;
""", {"assembly" : assembly,
      "assays" : assays,
      "tissues" : json.dumps(tissues),
      "loci" : loci,
      "uid" : uid
})
                    hubNum = curs.fetchone()[0]
                else:
                    curs.execute("""
INSERT INTO search
(assembly, assays, tissues, loci, uid, hubNum)
VALUES (
%(assembly)s,
%(assays)s,
%(tissues)s,
%(loci)s,
%(uid)s,
%(hubNum)s
) RETURNING hubNum;
""", {"assembly" : assembly,
       "assays" : assays,
       "tissues" : json.dumps(tissues),
       "loci" : loci,
       "uid" : uid,
       "hubNum" : 0
})
                    hubNum = curs.fetchone()[0]
        return hubNum

    def get(self, uid):
        with self._conn:
            with self._conn.cursor() as curs:
                curs.execute("""
SELECT assembly, assays, tissues, loci, hubNum
FROM search
WHERE uid = %(uid)s
""", {"uid" : uid})
                return curs.fetchone()

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--local', action="store_true", default=False)
    args = parser.parse_args()
    return args

def main():
    args = parse_args()

    if args.local:
        dbs = DBS.localAnnotations()
    else:
        dbs = DBS.pgdsn("Annotations")
    dbs["application_name"] = os.path.realpath(__file__)
    with psycopg2.connect(**dbs) as conn:
        with conn.cursor() as cur:
            setupDB(cur)

if __name__ == '__main__':
    main()
