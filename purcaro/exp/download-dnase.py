#!/usr/bin/env python
# CREATE DATE: 30 Nov 2016
# AUTHOR: William Stafford Noble
#         Shamelessly cribbed from Michael Purcaro:
#         https://github.com/weng-lab/scratch/blob/master/purcaro/exp_simple.py
import sys
import urllib
import json
import subprocess
import os

USAGE = """USAGE: download-dnase.py <file>

  Input is a list of ENCODE DNase-seq experiment IDs.  The program
  gets the first replicate narrow peak BED file for each experiment.

"""

###############################################################################
class ExpFileSimple:
    def __init__(self, fileJson):
        self.fileJson = fileJson

        self.file_type = self.fileJson["file_type"]
        self.url = "https://www.encodeproject.org" + self.fileJson["href"]

        self.assembly = fileJson.get("assembly", None)
        self.biological_replicates = fileJson.get("biological_replicates", None)
        self.technical_replicates = fileJson.get("technical_replicates", None)
        
    def isBedNarrowPeak(self):
        return "bed narrowPeak" == self.file_type

###############################################################################
class ExpSimple:
    def __init__(self, accession):
        self.accession = accession

        url = "https://www.encodeproject.org/experiments/" + accession + "/?format=json"
        response = urllib.urlopen(url)
        self.expJson = json.loads(response.read())
        
    def getBedNarrowPeak(self):
        returnValue = ""
        
        for fileJson in self.expJson["files"]:
            f = ExpFileSimple(fileJson)
            foundIt = False
            if (f.isBedNarrowPeak()
#                and f.assembly == "hg19"
#                and f.biological_replicates == "[1]"
#                and f.technical_replicates == "1_1"
            ):
#                print(f.assembly, f.biological_replicates, f.technical_replicates, f.url)
#                sys.stdout.write("f.assembly=%s " % f.biological_replicates)
#                sys.stdout.write("f.biological_replicates=%s " % f.biological_replicates)
#                sys.stdout.write("f.technical_replicates=%s\n" % f.technical_replicates)
                returnValue = f.url
                break
        return(returnValue)
        

###############################################################################
# MAIN
###############################################################################
def main():

    # Parse the command line.
    if (len(sys.argv) != 2):
        sys.stderr.write(USAGE)
        sys.exit(1)
    idFileName = sys.argv[1]

    # Read the IDs and download each one.
    idFile = open(idFileName, "r")
    for myID in idFile:
        myID = myID.rstrip()
        sys.stderr.write("Retrieving %s.\n" % myID)

        # Use Michael's fancy class to get the right URL.
        e = ExpSimple(myID)
        url = e.getBedNarrowPeak()
        if (url == ""):
            sys.stdout.write("Could not find %s.\n" % myID)

        # Download the associated file.
        # (Yes, I know I could use a Python module to do this ...)
        command="wget --no-host-directories %s" % url
        sys.stderr.write("%s\n" % command)
        returnValue = subprocess.call(command, shell=True)
        if (returnValue != 0):
            sys.stderr.write("Non-zero exit (%d) from command: %s\n"
                             % (returnValue, command))
            sys.exit(1)

        # Rename it to match the original experiment ID.
        name = url.split("/")[-1]
        sys.stderr.write("Renaming from %s to %s.bed.gz.\n"
                         % (name, myID))
        os.rename(name, "%s.bed.gz" % myID)
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
    
