#!/usr/bin/env python

import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../../utils'))
from epigenome import Epigenomes
from helpers_metadata import ExpFile
from files_and_paths import Dirs

UrlBase = "http://egg2.wustl.edu/roadmap/data/byFileType/signal/consolidated/macs2signal/foldChange/"

class RoadmapExp:
    def __init__(self, eid, assay_term_name, biosample_term_name, files):
        self.encodeID = eid
        self.assay_term_name = assay_term_name
        self.biosample_term_name = biosample_term_name
        self.age = None

        self.files = None
        if files.strip():
            fn = eid + "-H3K27ac.fc.signal.bigwig"
            if "DNase-seq" == assay_term_name:
                fn = eid + "-DNase.fc.signal.bigwig"

            expF = ExpFile.fromRoadmap(eid)
            expF.url = os.path.join(UrlBase, fn)
            expF.output_type = "fold change over control"
            expF.file_type = "bigWig"

            self.files = [expF]

    def isH3K27ac(self):
        return "H3K27ac" == self.assay_term_name

    def isDNaseSeq(self):
        return "DNase-seq" == self.assay_term_name

class RoadmapEpigenome:
    def __init__(self, eid, biosample_term_name, DNase, H3K27ac):
        self.biosample_term_name = biosample_term_name
        self.age_display = None
        self.eid = eid

        self.DNaseExp = None
        if DNase.files:
            self.DNaseExp = DNase

        self.H3K27acExp = None
        if H3K27ac.files:
            self.H3K27acExp = H3K27ac

    def hasDNase(self):
        return self.DNaseExp

    def hasH3K27ac(self):
        return self.H3K27acExp

    def DNase(self):
        return filter(lambda x: x, [self.DNaseExp])

    def H3K27ac(self):
        return filter(lambda x: x, [self.H3K27acExp])

    def hasBothDNaseAndH3K27ac(self):
        return self.hasDNase() and self.hasH3K27ac()

    def predictionFnp(self, DNase, H3K27ac):
        path = os.path.join(Dirs.encyclopedia, "Enhancer-Prediction-Tracks")
        fn = "{eid}_predictions.bigBed".format(eid = self.eid)
        return os.path.join(path, fn)

class RoadmapMetadata:
    def __init__(self):
        fnp = os.path.realpath(os.path.join(os.path.dirname(__file__), "roadmap.tsv"))
        with open(fnp) as f:
            data = [line.rstrip().split('\t') for line in f]
        headers = data[:3]
        data = data[3:]

        if 0:
            print headers[0][1]
            print headers[0][14]
            print headers[1][33]
            print headers[1][35]

            print data[0][1] # EID
            print data[0][14] # biosample_term_name approx....
            print data[0][33] # H3K27ac tag align files
            print data[0][35] # DNase tag align files

        self.epigenomes = Epigenomes("ROADMAP", "hg19")

        for r in data:
            DNase = RoadmapExp(r[1], "DNase-seq", r[14], r[35])
            H3K27ac = RoadmapExp(r[1], "H3K27ac", r[14], r[33])
            epi = RoadmapEpigenome(r[1], r[14], DNase, H3K27ac)
            self.epigenomes.addEpigenome(epi)

        print "found", len(self.epigenomes), "epigenomes for ROADMAP hg19"

def main():
    r = RoadmapMetadata().epigenomes

if __name__ == '__main__':
    main()
