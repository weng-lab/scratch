#!/usr/bin/env python

import os, sys, json
import StringIO

from helpers_trackhub import Track, PredictionTrack, BigGenePredTrack, BigWigTrack, bedFilters, bigWigFilters, VistaTrack

sys.path.append(os.path.join(os.path.dirname(__file__), '../../utils'))
from utils import Utils
from files_and_paths import Dirs
from web_epigenomes import WebEpigenome

BIB5 = "http://bib5.umassmed.edu/~purcarom/annotations_demo/"

eidToBigWigFileID = {"ENCSR172RHR" : "ENCFF301ECS",
                     "ENCSR179PIH" : "ENCFF138KVI",
                     "ENCSR196VDE" : "ENCFF803VYR",
                     "ENCSR292QBA" : "ENCFF329CUO",
                     "ENCSR312QVY" : "ENCFF592CFE",
                     "ENCSR337EDG" : "ENCFF849GKV",
                     "ENCSR358ESL" : "ENCFF989TMR",
                     "ENCSR367FCW" : "ENCFF147ZSW",
                     "ENCSR469VGZ" : "ENCFF142WSR",
                     "ENCSR488VEQ" : "ENCFF483YHV",
                     "ENCSR636NXY" : "ENCFF377GSQ",
                     "ENCSR661HDP" : "ENCFF128FJP",
                     "ENCSR666HFH" : "ENCFF479KSE",
                     "ENCSR687EAW" : "ENCFF091VKI",
                     "ENCSR742DUR" : "ENCFF385BSB",
                     "ENCSR793WUR" : "ENCFF957FAN",
                     "ENCSR935RRY" : "ENCFF877NOP",
                     "ENCSR959HKR" : "ENCFF617HTH",
                     "ENCSR064DGY" : "ENCFF478ATY",
                     "ENCSR080GQM" : "ENCFF337DHW",
                     "ENCSR157LYR" : "ENCFF096GTH",
                     "ENCSR196ENU" : "ENCFF079KZH",
                     "ENCSR293ORS" : "ENCFF749FRR",
                     "ENCSR335WME" : "ENCFF987TFU",
                     "ENCSR417TXZ" : "ENCFF937LBE",
                     "ENCSR425FLT" : "ENCFF588JVO",
                     "ENCSR464MQU" : "ENCFF686SHG",
                     "ENCSR581FAT" : "ENCFF247FWC",
                     "ENCSR641EME" : "ENCFF577TCZ",
                     "ENCSR765SJF" : "ENCFF884JJT",
                     "ENCSR831YAX" : "ENCFF354SIU",
                     "ENCSR871CGP" : "ENCFF167FIF",
                     "ENCSR929GXP" : "ENCFF350NWQ",
                     "ENCSR953LFI" : "ENCFF990QBR",
                     "ENCSR871KVM" : "ENCFF309IVZ"}

class dummy:
    def __init__(self, fileID):
        self.fileID = fileID
        self.url = os.path.join(BIB5, "bigwigs", fileID + ".bigWig")

    def isBigWig(self):
        return self.url.endswith(".bigWig")

class TrackHub:
    def __init__(self, args, epigenomes, row):
        self.args = args
        self.epigenomes = epigenomes
        self.assembly = row[0]
        self.assays = row[1]
        self.tissue_ids = json.loads(row[2])
        self.loci = row[3]
        self.hubNum = row[4]

        self.priority = 1

    def Custom(self):
        lines = []
        #lines += ["browser hide all"]
        #lines += ["browser pack knownGene refGene ensGene"]

        f = StringIO.StringIO()
        map(lambda line: f.write(line + "\n"), lines)

        return f.getvalue()

    def ParsePath(self, path):
        if not path:
            raise Exception("no path")

        if 1 == len(path):
            if path[0].startswith("hub_") and path[0].endswith(".txt"):
                return self.makeHub()
            if path[0].startswith("genomes_") and path[0].endswith(".txt"):
                return self.makeGenomes()
            return "ERROR"

        if 2 != len(path):
            raise Exception("path too long")

        if path[0] in ["hg19", "hg38", "mm9", "mm10"]:
            if path[0] == self.assembly:
                if path[1].startswith("trackDb_") and path[1].endswith(".txt"):
                    return self.makeTrackDb()

        raise Exception("invalid path")

    def makeHub(self):
        f = StringIO.StringIO()
        t = ""
        if self.args.debug:
            t += "debug "
        t += "ENCODE Encyclopedia Annotations " + self.assembly
        for r in [["hub", t],
                  ["shortLabel", t],
                  ["longLabel", t],
                  ["genomesFile", "genomes_{hubNum}.txt".format(hubNum=self.hubNum)],
                  ["email", "zhiping.weng@umassmed.edu"]]:
            f.write(" ".join(r) + "\n")
        return f.getvalue()

    def makeGenomes(self):
        return """genome\t{assembly}
trackDb\t{assembly}/trackDb_{hubNum}.txt""".format(assembly = self.assembly,
                                                   hubNum = self.hubNum)

    def makeTrackDb(self):
        epis = self.epigenomes.GetByAssemblyAndAssays(self.assembly, self.assays)
        epis = filter(lambda e: e.web_id() in self.tissue_ids, epis.epis)

        lines = []
        lines += [self.genes()]

        for wepi in sorted(epis, key=lambda e: e.epi.biosample_term_name):
            if "Both" == self.assays:
                lines += [self.predictionTrackHub(wepi)]
            for exp in wepi.exps():
                lines += [self.trackhubExp(exp)]

        lines += [self.vista()]
        lines += [self.phastcons()]

        lines = filter(lambda x: x, lines)

        f = StringIO.StringIO()
        map(lambda line: f.write(line + "\n"), lines)

        return f.getvalue()

    def phastcons(self):
        if "mm9" == self.assembly:
            url = os.path.join(BIB5, "conservation", "mm9.phastCons30way.bw")
        if "mm10" == self.assembly:
            url =  "http://hgdownload.cse.ucsc.edu/goldenPath/mm10/phastCons60way/mm10.60way.phastCons.bw"
        if "hg19" == self.assembly:
            url = "http://hgdownload.cse.ucsc.edu/goldenPath/hg19/phastCons100way/hg19.100way.phastCons.bw"

        desc = "phastCons"

        track = BigWigTrack(desc, self.priority, url, "0,255,0").track()
        self.priority += 1
        return track

    def genes(self):
        if "hg19" == self.assembly:
            return None

        byAssembly = {"mm9" : "Comprehensive M1",
                      "mm10" : "Comprehensive M8",
                      "hg19" : "Comprehensive 24"}
        desc = "GENCODE Genes " + byAssembly[self.assembly]

        byAssemblyURl = {"mm9" : os.path.join(BIB5, "genes", "gencode.vM1.annotation.bb"),
                         "mm10" : os.path.join(BIB5, "genes", "gencode.vM8.annotation.bb"),
                         "hg19" : os.path.join(BIB5, "genes", "gencode.v24.annotation.bb")}
        url = byAssemblyURl[self.assembly]

        track = BigGenePredTrack(desc, self.priority, url).track()
        self.priority += 1
        return track

    def vista(self):
        if "mm10" != self.assembly:
            return None

        desc = "VISTA"
        url = os.path.join(BIB5, "mm10.bb")

        track = VistaTrack(desc, self.priority, url).track()
        self.priority += 1
        return track

    def predictionTrackHub(self, wepi):
        fnp = wepi.predictionFnp()
        if not os.path.exists(fnp):
            return None

        desc = Track.MakeDesc("enhancer predictions",
                              wepi.epi.age_display,
                              wepi.epi.biosample_term_name)

        url = os.path.join(BIB5, "Enhancer-Prediction-Tracks",
                           os.path.basename(fnp))

        track = PredictionTrack(desc, self.priority, url).track()
        self.priority += 1
        return track

    def trackhubExp(self, exp):
        bigWigs = bigWigFilters(self.assembly, exp.files)
        if not bigWigs:
            if "mm10" == self.assembly:
                bigWigs = [dummy(eidToBigWigFileID[exp.encodeID])]

        bigWig = bigWigs[0]

        url = bigWig.url
        if url.startswith("https://www.encodeproject.org"):
            if ".bed.gz" in url:
                url = os.path.join(BIB5, "bedToBigBed", bigWig.fileID + ".bb")

        if exp.isH3K27ac():
            name = "H3K27ac Signal"
            color = "18,98,235"
        elif exp.isDNaseSeq():
            name = "DNase Signal"
            color = "255,121,3"
        else:
            raise Exception("unexpected exp")

        desc = Track.MakeDesc(name, exp.age, exp.biosample_term_name)

        track = BigWigTrack(desc, self.priority, url, color).track()
        self.priority += 1
        return track
