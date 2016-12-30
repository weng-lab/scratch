#!/usr/bin/env python

from __future__ import print_function
import os
import sys
import requests
from requests.auth import HTTPBasicAuth
import shutil
import tempfile

class EncodeDownloadExample:
    
    @staticmethod
    def download(url, fnp, auth=None):

        if not auth:
            r = requests.get(url)
        if auth or 403 == r.status_code:
            keyFnp = os.path.expanduser('~/.encode.txt')
            if os.path.exists(keyFnp):
                with open(keyFnp) as f:
                    toks = f.read().strip().split('\n')
                r = requests.get(url, auth=HTTPBasicAuth(toks[0], toks[1]))
            else:
                raise Exception("no ENCODE password file found at: " +
                                keyFnp)
        if 200 != r.status_code:
            Utils.quietPrint(quiet, "could not download", url)
            Utils.quietPrint(quiet, "status_code:", r.status_code)
            return False

        #with open(fnpTmp, "wb") as f:
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(r.content)
            fnpTmp = f.name
        shutil.move(fnpTmp, fnp)
        print("downloaded", url, "to", fnp)
        
def main():
    outFnp = "/tmp/deleteme.tmp"
    url = "https://www.encodeproject.org/files/ENCFF494REJ/@@download/ENCFF494REJ.tsv"
    EncodeDownloadExample.download(url, outFnp, auth=True)

if __name__ == "__main__":
    sys.exit(main())
        
