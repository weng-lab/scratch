def bedFilters(assembly, files):
    bfs = [lambda x: x.assembly == assembly and x.isBedNarrowPeak() and '1' in x.bio_rep and '2' in x.bio_rep,
           lambda x: x.assembly == assembly and x.isBedNarrowPeak() and x.bio_rep == '1',
           lambda x: x.assembly == assembly and x.isBedNarrowPeak(),
           lambda x: x.assembly == assembly and x.isBedBroadPeak() and x.bio_rep == '1',
           lambda x: x.assembly == assembly and x.isBedBroadPeak()
           ]
    for bf in bfs:
        beds = filter(bf, files)
        if beds:
            beds = filter(lambda x: not x.isHotSpot(), beds)
            return beds

def bigWigFilters(assembly, files):
    files = filter(lambda x: x.isBigWig(), files)
    bfs = [lambda x: x.output_type == "fold change over control",
           lambda x: x.output_type == "signal of unique reads" and
           '1' == x.bio_rep,
           lambda bw: bw.isRawSignal() and bw.bio_rep == '1',
           lambda bw: bw.isSignal() and bw.bio_rep == '1',
           lambda bw: bw.isSignal()
           ]
    for bf in bfs:
        bigWigs = filter(bf, files)
        if bigWigs:
            return bigWigs

class Track(object):
    def __init__(self, desc, priority, url):
        self.desc = desc
        self.priority = priority

        self.url = url
        if self.url.startswith("https://www.encodeproject.org"):
            if not self.url.endswith("?proxy=true"):
                self.url += "?proxy=true"
            self.url = self.url.replace("https://www.encodeproject.org",
                                        "http://www.encodeproject.org")

        self.visibility = "dense"
        self.type = None

        self.color = None
        self.height = None

    @staticmethod
    def MakeDesc(name, age, biosample_term_name):
        desc = [biosample_term_name]
        if age and "unknown" != age:
            desc += [age]
        desc += [name]
        desc = " ".join(desc)
        return desc

    def track(self):
        if not self.type:
            raise Exception("unknown type")
        track = ["track " + self.desc.replace(" ", "_"),
                 "type " + self.type,
                 "shortLabel " + self.desc,
                 "longLabel " + self.desc,
                 "itemRgb on",
                 "autoScale on",
                 "visibility " + self.visibility,
                 "priority " + str(self.priority),
                 "bigDataUrl " + self.url]
        if self.color:
            track += ["color " + self.color]
        if self.height:
            track += [self.height]
        track += ["\n"]
        return "\n".join(track)

class PredictionTrack(Track):
    def __init__(self, desc, priority, url):
        super(PredictionTrack, self).__init__(desc, priority, url)
        self.color = "6,218,147"
        self.type = "bigBed 8"

class VistaTrack(Track):
    def __init__(self, desc, priority, url):
        super(VistaTrack, self).__init__(desc, priority, url)
        self.color = None
        self.type = "bigBed 5"

class BigWigTrack(Track):
    def __init__(self, desc, priority, url, color):
        super(BigWigTrack, self).__init__(desc, priority, url)
        self.color = color
        self.type = "bigWig"
        self.height = "maxHeightPixels 128:64:8"
        self.visibility = "full"

class BigGenePredTrack(Track):
    def __init__(self, desc, priority, url):
        super(BigGenePredTrack, self).__init__(desc, priority, url)
        self.color = "6,218,147"
        self.type = "bigBed 12 + 8"
        self.visibility = "pack"

def officialVistaTrack(assembly):
    byAssembly = {"mm9": """
track VISTAenhancers
bigDataUrl http://portal.nersc.gov/dna/RD/ChIP-Seq/VISTA_enhancer_e/mm9_ext_latest.bb
shortLabel VISTA Enhancers
longLabel Potential Enhancer Sequences Assayed in Mouse
type bigBed 9 +
itemRgb on
url http://enhancer.lbl.gov/cgi-bin/imagedb3.pl?form=presentation&show=1&experiment_id=$P&organism_id=$p
urlLabel Vista Enhancer Browser (elementID:organismID(1 for human, 2 for mouse))
bedNameLabel VISTA Enhancers
html http://portal.nersc.gov/dna/RD/ChIP-Seq/VISTA_enhancer_e/VistaEnhancerTrackHub/enhancerAssay.html
visibility full""",
                  "mm10" : """
track VISTAenhancers
bigDataUrl http://portal.nersc.gov/dna/RD/ChIP-Seq/VISTA_enhancer_e/mm10_ext_latest.bb
shortLabel VISTA Enhancers
longLabel Potential Enhancer Sequences Assayed in Mouse
type bigBed 9 +
itemRgb on
url http://enhancer.lbl.gov/cgi-bin/imagedb3.pl?form=presentation&show=1&experiment_id=$P&organism_id=$p
urlLabel Vista Enhancer Browser (elementID:organismID(1 for human, 2 for mouse))
bedNameLabel VISTA Enhancers
html http://portal.nersc.gov/dna/RD/ChIP-Seq/VISTA_enhancer_e/VistaEnhancerTrackHub/enhancerAssay.html
visibility full""",
                  "hg19" : """
track VISTAenhancers
bigDataUrl http://portal.nersc.gov/dna/RD/ChIP-Seq/VISTA_enhancer_e/hg19_ext_latest.bb
shortLabel VISTA Enhancers
longLabel Potential Enhancer Sequences Assayed in Mouse
type bigBed 9 +
itemRgb on
url http://enhancer.lbl.gov/cgi-bin/imagedb3.pl?form=presentation&show=1&experiment_id=$P&organism_id=$p
urlLabel Vista Enhancer Browser
bedNameLabel VISTA Enhancers (elementID:organismID(1 for human, 2 for mouse))
html http://portal.nersc.gov/dna/RD/ChIP-Seq/VISTA_enhancer_e/VistaEnhancerTrackHub/enhancerAssay.html
visibility full"""}
    return byAssembly[assembly]
