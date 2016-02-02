#!/usr/bin/env python

import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../../utils'))
from files_and_paths import Dirs

class Coord:
    def __init__(self, chrom, start, end):
        self.chrom = chrom
        self.start = start
        self.end = end

    def __repr__(self):
        return "{chrom}:{start}-{end}".format(chrom=self.chrom,
                                              start=self.start,
                                              end=self.end)

    def resize(self, halfWindow):
        # 1-based coords for UCSC Genome Browser
        self.start = str(max(1, int(self.start) - halfWindow))
        self.end = str(int(self.end) + halfWindow)

    @classmethod
    def parse(cls, loci):
        try:
            toks = loci.split(':')
            chrom = toks[0]
            start = toks[1].split('-')[0]
            end = toks[1].split('-')[1]
            return cls(chrom, start, end)
        except:
            return None

class UcscSearch:
    def __init__(self, epigenomes, db, host, params, uid):
        self.epigenomes = epigenomes
        self.db = db
        self.host = host
        self.params = params
        self.uid = uid

    def Coord(self):
        if self.coord:
            return str(self.coord)
        return "None"

    def parse(self):
        self.assembly = self.params["assembly"]
        self.assays = self.params["assays"]

        self.tissue_ids = self.params[self.assembly + self.assays]

        if isinstance(self.tissue_ids, basestring):
            self.tissue_ids = [self.tissue_ids]
        self.tissue_ids.sort()

        self.loci = self.params["loci"].strip()

        self.hubNum = self.db.insertOrUpdate(self.assembly, self.assays,
                                             self.tissue_ids, self.loci,
                                             self.uid)

        self.coord = None
        if self.loci.lower().startswith("chr"):
            self.coord = Coord.parse(self.loci)
        elif self.loci.isdigit() and 1 == len(self.tissue_ids):
            # a ranked peak
            try:
                coord = self.getRankedPeakCoord()
                if coord:
                    coord.resize(7500)
                self.coord = coord
            except:
                raise
                pass

    def getRankedPeakCoord(self):
        wepis = self.epigenomes.GetByAssemblyAndAssays(self.assembly, self.assays)
        wepis = filter(lambda e: e.web_id() in self.tissue_ids, wepis.epis)

        if 1 != len(wepis):
            return

        wepi = wepis[0]

        fnp = wepi.predictionFnp().replace(".bigBed", ".bed")
        if not os.path.exists(fnp):
            print "file not found", fnp
            return

        rank = int(self.loci) - 1

        if rank < 0:
            raise Exception("invalid rank")

        row = None
        with open(fnp) as f:
            # http://stackoverflow.com/a/2081880
            for i, line in enumerate(f):
                if i == rank:
                    row = line
                    break
                if i > rank:
                    break
        if not row:
            raise Exception("invalid rank")

        toks = row.rstrip().split('\t')
        return Coord(toks[0], toks[1], toks[2])

    def ucscParams(self):
        if self.coord:
            ucscParams = ["db=" + self.assembly,
                          "position=" + str(self.coord)]
        else:
            # snp or gene
            if self.assembly in ["hg19", "hg38"]:
                org = "Human"
            elif self.assembly in ["mm9", "mm10"]:
                org = "Mouse"
            else:
                raise Exception("unknown assembly")
            ucscParams = ["clade=mammal",
                          "org=" + org,
                          "db=" + self.assembly,
                          "position=" + self.loci,
                          "hgt.positionInput=" + self.loci,
                          "hgt.suggestTrack=knownGene",
                          "Submit=submit"]
        if 0:
            customUrl = os.path.join(self.host,
                                     "annotations",
                                     "trackhubCustom",
                                     self.uid,
                                     str(self.hubNum))
            ucscParams.append("hgt.customText=" + customUrl)
        if 0:
            ucscParams = ["udcTimeout=1"] + ucscParams
        return ucscParams

    def configureUcscHubLink(self):
        ucscParams = self.ucscParams()

        urlBase = "https://genome.ucsc.edu/cgi-bin/hgTracks?"

        self.trackhubUrl = os.path.join(self.host,
                                        "annotations",
                                        "trackhub",
                                        self.uid,
                                        "hub_{hubNum}.txt".format(hubNum =
                                                                  self.hubNum))
        ucscParams.append("hubClear=" + self.trackhubUrl)

        self.trackdbUrl = os.path.join(self.host,
                                       "annotations",
                                       "trackhub",
                                       self.uid,
                                       self.assembly,
                                       "trackDb_{hubNum}.txt".format(hubNum =
                                                                     self.hubNum))

        url = urlBase + "&".join(ucscParams)
        return url
