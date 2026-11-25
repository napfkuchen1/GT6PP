#!/usr/bin/env python
"""Classify boot probe runs: boot-outcome.py <run-dir> [...] (one line per run)."""
import glob, os, re, sys

def classify(d):
    text = ""
    for f in glob.glob(os.path.join(d, "run.log*")):
        text += open(f, encoding="utf-8", errors="replace").read()
    boot = open(os.path.join(d, "boot.txt"), errors="replace").read().strip().splitlines()
    gpb = re.findall(r"([A-Za-z0-9_]+\.gpb)", text)
    return "%s | %s | hot=%d long=%d pure=%d gpb=%d last=%s" % (
        os.path.basename(d.rstrip("/\\")), boot[-1].split(" (")[0],
        len(re.findall(r"HOTREAD8\b", text)), text.count("too long"),
        len(re.findall(r"purecall|pure virtual", text)), len(gpb), gpb[-1] if gpb else "-")

for pat in sys.argv[1:]:
    for d in sorted(glob.glob(pat)):
        if os.path.exists(os.path.join(d, "boot.txt")):
            print(classify(d))
