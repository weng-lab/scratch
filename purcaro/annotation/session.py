#!/usr/bin/env python

import os, sys, json, psycopg2, argparse

sys.path.append(os.path.join(os.path.dirname(__file__), '../../utils/'))
from utils import Utils
from dbs import DBS

def setupDB(cur):
    cur.execute("""
DROP TABLE IF EXISTS sessions;
CREATE TABLE sessions
(id serial PRIMARY KEY,
uid text,
session_id text
) """)

class Sessions:
    def __init__(self, dbs):
        if not dbs:
            dbs = DBS.pgdsn("Annotations")
            dbs["application_name"] = os.path.realpath(__file__)
        self.dbs = dbs
        self._conn = psycopg2.connect(**dbs)
        self._conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED)

    def insert(self, session_id, uid):
        with self._conn:
            with self._conn.cursor() as curs:
                curs.execute("""
INSERT INTO sessions
(session_id, uid)
VALUES (
%(session_id)s,
%(uid)s
)""", {"session_id" : session_id,
       "uid" : uid
})

    def insertOrUpdate(self, session_id, uid):
        with self._conn:
            with self._conn.cursor() as curs:
                curs.execute("""
SELECT id FROM sessions
WHERE session_id = %(session_id)s
""", {"session_id" : session_id})
                if (curs.rowcount > 0):
                    curs.execute("""
UPDATE sessions
SET
uid = %(uid)s
WHERE session_id = %(session_id)s
""", {"session_id" : session_id,
      "uid" : uid
})
                else:
                    curs.execute("""
INSERT INTO sessions
(session_id, uid)
VALUES (
%(session_id)s,
%(uid)s
)""", {"session_id" : session_id,
       "uid" : uid
})

    def get(self, session_id):
        with self._conn:
            with self._conn.cursor() as curs:
                curs.execute("""
SELECT uid
FROM sessions
WHERE session_id = %(session_id)s
""", {"session_id" : session_id})
                uid = curs.fetchone()
                if uid:
                    return uid[0]
                return None

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
