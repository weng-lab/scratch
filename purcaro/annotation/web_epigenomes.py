#!/usr/bin/env python

import os, sys
from collections import defaultdict
from itertools import groupby
import cPickle as pickle

import numpy as np

from roadmap import RoadmapMetadata

sys.path.append(os.path.join(os.path.dirname(__file__), '../../utils'))
from metadataws import MetadataWS
from files_and_paths import Datasets

class WebEpigenomesLoader:
    def __init__(self):
        byAssembly = {}

        m = MetadataWS(Datasets.all_mouse)
        byAssembly["mm9"] = m.chipseq_tf_annotations_mm9()
        byAssembly["mm10"] = m.chipseq_tf_annotations_mm10()

        m = MetadataWS(Datasets.all_human)
        #byAssembly["hg19"] = m.chipseq_tf_annotations_hg19()
        byAssembly["hg19"] = RoadmapMetadata().epigenomes

        if 0:
            self.cache()

        self.byAssemblyAssays = defaultdict(lambda : defaultdict(None))
        for assembly in ["mm9", "mm10", "hg19"]:
            for assays in ["Both", "H3K27ac", "DNase"]:
                epis = byAssembly[assembly].GetByAssays(assays)
                if epis:
                    epis = [WebEpigenome(epi, assays) for epi in epis]
                    self.byAssemblyAssays[assembly][assays] = WebEpigenomes(assembly, assays, epis)

    def cache(self):
        cacheDir = os.path.join(os.path.dirname(__file__), "cache")
        cacheFnp = os.path.join(cacheDir, "pickle.MouseEncodeJson.p")
        if not os.path.exists(cacheFnp):
            mej = MouseEncodeJson()
            pickle.dump(mej, open(cacheFnp, "wb"))
        else:
            mej = pickle.load(open(cacheFnp, "rb"))

    def GetByAssemblyAndAssays(self, assembly, assays):
        return self.byAssemblyAssays[assembly][assays]

    def Walk(self, assembly, assays):
        return self.GetByAssemblyAndAssays(assembly, assays).Walk()

    def Header(self, assembly, assays):
        return self.GetByAssemblyAndAssays(assembly, assays).Header()

class WebEpigenome:
    def __init__(self, epi, assays):
        self.epi = epi
        self.assays = assays
        self.DNase = None
        self.H3K27ac = None

        if len(self.epi.DNase()) > 1:
            print self.epi
            for e in self.epi.DNase():
                print "\t", e
            raise Exception("multiple DNase experiments found")
        if len(self.epi.H3K27ac()) > 1:
            print self.epi
            for e in self.epi.H3K27ac():
                print "\t", e
            raise Exception("multiple H3K27ac experiments found")

        if "Both" == self.assays:
            self.DNase = epi.DNase()[0]
            self.H3K27ac = epi.H3K27ac()[0]
        elif "H3K27ac" == self.assays:
            self.H3K27ac = epi.H3K27ac()[0]
        elif "DNase" == self.assays:
            self.DNase = epi.DNase()[0]
        else:
            raise Exception("unknown assay type " + self.assays)

    def web_id(self):
        s = self.epi.biosample_term_name
        if self.epi.age_display:
            s = "_".join([self.epi.biosample_term_name, self.epi.life_stage, self.epi.age_display])
        return s.lower().replace(' ', '_')

    def pretty_age(self):
        s = ""
        if self.epi.age_display:
            s = self.epi.life_stage + " " + self.epi.age_display
        if "embryonic" in s:
            s = s.replace("embryonic ", "e").replace(" day", "")
        elif "postnatal" in s:
            s = s.replace(" day", "").replace("postnatal ", "p")
        return s

    def web_title(self):
        s = self.epi.biosample_term_name
        if self.epi.age_display:
            s = self.pretty_age()
        return s

    def web_title_single(self):
        return self.pretty_age()

    def isActive(self):
        return self.web_id() in ["midbrain_embryonic_11.5_day", "hindbrain_embryonic_11.5_day",
                                 "limb_embryonic_11.5_day", "neural_tube_embryonic_11.5_day",
                                 "brain_embryonic_14.5_day", "fetal_intestine_large"]

    def exps(self):
        if "H3K27ac" == self.assays:
            return [self.H3K27ac]
        if "DNase" == self.assays:
            return [self.DNase]
        if "Both" == self.assays:
            return [self.DNase, self.H3K27ac]
        raise Exception("unknown assay type " + self.assays)

    def predictionFnp(self):
        return self.epi.predictionFnp(self.DNase, self.H3K27ac)

class WalkRow:
    def __init__(self, row):
        self.row = row

    def hasSingleEntry(self):
        return 1 == np.count_nonzero(self.row)

    def Walk(self):
        justOne = self.hasSingleEntry()

        for exps in self.row:
            if exps == 0:
                yield None, None, None
            else:
                for c in exps:
                    if justOne:
                        yield c.web_id(), c.web_title_single(), c
                    else:
                        yield c.web_id(), c.web_title(), c

class WebEpigenomes:
    def __init__(self, assembly, assays, epis):
        self.assembly = assembly
        self.assays = assays
        self.epis = epis

        self.setupMatrix()

    def Header(self):
        for c in self.m[0]:
            if not c:
                yield "biosample"
            else:
                yield c

    def Walk(self):
        for row in self.m[1:]:
            yield row[0], WalkRow(row[1:]).Walk()

    def adjust_biosample_term_name(self, b):
        if "embryonic facial prominence" == b:
            b = "embryonic facial<br>prominence"
        b  = b.replace("negative", "-").replace("positive", "+").replace("--", "-").replace("-+", "+")
        return b

    def setupMatrix(self):
        rows = set()
        cols = set()

        epis = self.epis
        keyfunc = lambda x: x.epi.biosample_term_name
	epis.sort(key=keyfunc)

        for biosample_term_name, wepis in groupby(epis, keyfunc):
            rows.add(biosample_term_name)
            for wepi in wepis:
                cols.add(wepi.pretty_age())

        cols = sorted(list(cols))
        cols = ["Biosample"] + cols
        if "" in cols:
            idx = cols.index("")
            cols += [cols.pop(idx)]
        self.m = np.zeros([len(rows) + 1, len(cols)], dtype=object)

        # header row
        self.m[0] = np.array(cols)

        rowIdx = 1
        for biosample_term_name, wepis in groupby(epis, keyfunc):
            self.m[rowIdx][0] = self.adjust_biosample_term_name(biosample_term_name)
            for wepi in wepis:
                colIdx = cols.index(wepi.pretty_age())
                if 0 == self.m[rowIdx][colIdx]:
                    self.m[rowIdx][colIdx] = []
                self.m[rowIdx][colIdx].append(wepi)
            rowIdx += 1

def main():
    we = WebEpigenomesLoader()

    for biosample_term_name, cols in we.Walk("mm10", "Both"):
        for wid, webtitle in cols:
            pass


if __name__ == '__main__':
    main()
