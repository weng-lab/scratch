#!/usr/bin/env python
# CREATE DATE: 30 Nov 2016
# AUTHOR: William Stafford Noble and Michael Purcaro:
#         https://github.com/weng-lab/scratch/blob/master/purcaro/exp/download-dnase.py
from __future__ import print_function
import argparse
import sys
import urllib
import json
import requests
import tempfile
import os
import shutil
import dateutil.parser
import operator

USAGE = """USAGE: download-dnase.py <file>

  Input is a list of ENCODE DNase-seq experiment IDs.  The program
  gets the first replicate narrow peak BED file for each experiment.

"""

###############################################################################
def eprint(*args, **kwargs):
    # Python-like print on stderr
    # from http://stackoverflow.com/a/14981125
    print(*args, file=sys.stderr, **kwargs)

###############################################################################
class QueryDCC:
    # get and parse JSON metadata from encodeproject.org

    def __init__(self, host=None, auth=True, cache=None):
        self.auth = auth
        self.host = "https://www.encodeproject.org"
        if host:
            self.host = host
        self.cache = cache

    def getURL(self, url):
        r = requests.get(url)
        if 200 != r.status_code:
            raise Exception("could not download " + url)
        return r.content

    def getIDs(self, url):
        # gets a list of experiment accessions
        ret = self.getURL(url)
        ret = json.loads(ret)
        eids = []
        for e in ret["@graph"]:
            eid = e["@id"]
            if not eid:
                continue
            eid = eid.split('/')[-2]
            eids.append(eid)
        return eids

###############################################################################
class ExpFileSimple:
    def __init__(self, fileJson):
        self.fileJson = fileJson

        self.accession = self.fileJson["accession"]
        self.status = self.fileJson["status"]
        self.file_name = os.path.basename(self.fileJson["href"])
        self.file_type = self.fileJson["file_type"]
        self.url = "https://www.encodeproject.org" + self.fileJson["href"]

        # date fields in older metadata didn't have time zones...
        self.date_created = dateutil.parser.parse(fileJson["date_created"]).replace(tzinfo=None)
        self.assembly = fileJson.get("assembly", None)
        self.biological_replicates = fileJson.get("biological_replicates", None)
        self.technical_replicates = fileJson.get("technical_replicates", None)

    def __getitem__(self, item):
        if "date_created" == item:
            return self.date_created
        raise Exception("unknown item " + str(item))

    def download(self, dstFnp):
        r = requests.get(self.url)
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(r.content)
            fnpTmp = f.name
        shutil.move(fnpTmp, dstFnp)

    def isBedNarrowPeak(self):
        return "bed narrowPeak" == self.file_type

    def isRightFile(self, assembly, bioReps, techReps, debug):
        if assembly != self.assembly:
            return False
        if self.status not in ["released", "archived"]: # some experiments only have "archived" files...
            if debug: eprint("\tisFirstRepBedNarrowPeak", "mismatch status")
            return False
        if not self.isBedNarrowPeak():
            return False
        if debug: eprint(bioReps, self.biological_replicates)
        if bioReps != self.biological_replicates:
            if debug: eprint("\tisFirstRepBedNarrowPeak", "mismatch bioReps")
            return False
        if debug: print(self.accession, self.biological_replicates, self.technical_replicates)
        if techReps:
            if not self.technical_replicates or techReps != self.technical_replicates[0]:
                if debug: eprint("\tisFirstRepBedNarrowPeak", "mismatch tech reps")
                return False
        return True

###############################################################################
class ExpSimple:
    def __init__(self, accession):
        self.accession = accession

        url = "https://www.encodeproject.org/experiments/" + accession + "/?format=json"
        response = urllib.urlopen(url)
        self.expJson = json.loads(response.read())

        try:
            self.lab = self.expJson["lab"]["title"]
        except:
            self.lab = "" # some experiments don't have labs??
        self.description = self.expJson["description"]
        self.files = [ExpFileSimple(x) for x in self.expJson["files"]]

    def getFirstRepBedNarrowPeak(self, assembly, debug):
        preferredBioAndTechReps = [ ([1], '1_1'),
                                    ([2], '2_1'),
                                    ([1,2], None),
                                    ([], None) ]

        for bioReps, techReps in preferredBioAndTechReps:
            beds = filter(lambda x: x.isRightFile(assembly, bioReps, techReps, debug),
                          self.files)
            if len(beds) > 0:
                break

        if 0 == len(beds):
            eprint("\tERROR", self.accession, assembly, "no first rep narrowPeak beds found")
            eprint("\t" + self.lab, self.description)
            return None

        if 1 != len(beds):
            bed = max(beds, key=operator.itemgetter("date_created")) # get the most recent file...
            return bed
            eprint("\tERROR", self.accession, assembly, "multiple first rep narrowPeak beds found")
            eprint("\t" + self.lab, self.description)
            eprint("\t" + ",".join([x.accession for x in beds]))
            return None
        return beds[0]

###############################################################################
def querydcc(args):
    # get a list of DNase experiment IDs from the portal
    qd = QueryDCC()

    # url is based on Cricket's total processed DNase url from her google doc
    # https://docs.google.com/spreadsheets/d/1S1rBEqs-C2GB2ilu5GMOHeSQcQ_Y8iFCrTPObX9mnyU/edit#gid=1988961282
    # also removes experiments w/ "low read depth" red badges
    url = "https://www.encodeproject.org/search/?type=Experiment&assay_title=DNase-seq&files.analysis_step_version.analysis_step.pipelines.title=DNase-HS+pipeline+%28paired-end%29&files.analysis_step_version.analysis_step.pipelines.title=DNase-HS+pipeline+%28single-end%29&files.file_type=bigBed+broadPeak&files.lab.name=encode-processing-pipeline&status=released&award.rfa=ENCODE3&award.rfa=Roadmap&award.rfa=ENCODE2&award.rfa=ENCODE2-Mouse&assembly=" + args.assembly + "&audit.ERROR.category!=extremely+low+read+depth&limit=all&format=json"

    ids = qd.getIDs(url)
    sys.stderr.write("Found %d accession IDs from ENCODE portal.\n" % len(ids))
    return ids

###############################################################################
def processIDs(assembly, ids, debug):
    for myID in sorted(ids):
        sys.stderr.write("Retrieving %s.\n" % myID)

        # Use Michael's fancy class to get the right file.
        e = ExpSimple(myID)
        f = e.getFirstRepBedNarrowPeak(assembly, debug)
        if f is None:
            sys.stderr.write("\tCould not find %s.\n" % myID)
            sys.exit(1)

        # Download it to match the original experiment ID.
        fn = myID + ".bed.gz"
        if os.path.exists(fn):
            sys.stderr.write("\tAlready downloaded %s to %s\n"
                             % (f.url, fn))
        else:
            sys.stderr.write("\tDownloading %s to %s\n"
                             % (f.url, fn))
            f.download(fn)
    return 0

###############################################################################
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action="store_true", default=False)
    parser.add_argument('--querydcc', action="store_true", default=False)
    parser.add_argument('--ids', type=str, default="")
    parser.add_argument('--assembly', type=str, default="hg19")
    parser.add_argument("files", nargs='*', default="")
    args = parser.parse_args()
    return args

###############################################################################
# MAIN
###############################################################################
def main():
    # Parse the command line.
    args = parse_args()

    if args.ids:
        ids = sorted(list(set(args.ids.split(','))))
        return processIDs(args.assembly, ids, args.debug)

    if args.querydcc:
        ids = querydcc(args)
    else:
        if 1 != len(args.files):
            sys.stderr.write(USAGE)
            sys.exit(1)
        idFileName = args.files[0]

        # Read the IDs
        with open(idFileName, "r") as f:
            ids = [x.rstrip() for x in f]
        sys.stderr.write("Read %d IDs accession from %s.\n" % (len(ids), idFileName))

    # download each exp
    return processIDs(args.assembly, ids, args.debug)

if __name__ == "__main__":
    sys.exit(main())
