#!/usr/bin/env python

import os, sys, json

def tsvToJson(fnp):
    print fnp
    with open(fnp) as f:
        lines = [line.rstrip().split('\t') for line in f]

    if "_summary_Table" in fnp:
        header = zip(lines[0], lines[1])
        header = [" ".join(x).strip() for x in header]
        for idx, e in enumerate(header):
            if not e:
                header[idx] = "empty" + str(idx)
        # print "\n".join(header)
        # skip 3rd line
        lines = lines[3:]
    else:
        header = lines[0]
        lines = lines[1:]

    headerTokens = set()
    for e in header:
        if e in headerTokens:
            print "problem: duplicate header token found:", e
            sys.exit(-1)
        headerTokens.add(e)

    data = [dict(zip(header, line)) for line in lines]

    for idx, e in enumerate(data):
        for key, val in e.iteritems():
            if ';' in val:
                data[idx][key] = val.split(';')
    outFnp = fnp + ".json"
    with open(outFnp, 'w') as f:
        json.dump(data, f)
    print "\tOK! wrote", outFnp

d = os.path.expanduser("~/Dropbox/0roadmap/")

for fn in sorted(os.listdir(d)):
    if not fn.endswith(".tsv"):
        continue
    fnp = os.path.join(d, fn)
    tsvToJson(fnp)
