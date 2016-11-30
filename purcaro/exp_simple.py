#!/usr/bin/env python

import sys
import urllib
import json

class ExpFileSimple:
    def __init__(self, fileJson):
        self.fileJson = fileJson

        self.assembly = None
        if "assembly" in fileJson:
            self.assembly = fileJson["assembly"]
        self.file_type = self.fileJson["file_type"]
        self.url = "https://www.encodeproject.org" + self.fileJson["href"]
                
        self.biological_replicates = None
        if "biological_replicates" in self.fileJson:
            self.biological_replicates = self.fileJson["biological_replicates"]
        
        self.technical_replicates = None
        if "technical_replicates" in self.fileJson:
            self.technical_replicates = self.fileJson["technical_replicates"]
        
    def isBedNarrowPeak(self):
        return "bed narrowPeak" == self.file_type

class ExpSimple:
    def __init__(self, accession):
        self.accession = accession

        url = "https://www.encodeproject.org/experiments/" + accession + "/?format=json"
        response = urllib.urlopen(url)
        self.expJson = json.loads(response.read())
        
    def getBedNarrowPeak(self):
        for fileJson in self.expJson["files"]:
            f = ExpFileSimple(fileJson)
            if f.isBedNarrowPeak():
                print(f.assembly, f.biological_replicates, f.technical_replicates, f.url)
        
def main():
    e = ExpSimple("ENCSR749BWV")
    e.getBedNarrowPeak()

if __name__ == "__main__":
    sys.exit(main())
