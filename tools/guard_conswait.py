#!/usr/bin/env python3
"""Workaround (Arbeit17): consumer wait 8A7AD0 for tid30 '9qstY' never finishes (obj+0x240 ahead of obj+0x1d8,
producer 8A8890 gated by obj+0x1d0). Guard: treat the wait condition as satisfied, i.e. skip the lwcond wait and
fall through to the obj+0x240 store (loc_008A7B4C). Opt-out: env GT6_NO_CONSWAIT=1 (the real wait is then kept).
Idempotent, EOL-agnostic. Applied to the generated cpp by post-lift.ps1."""
import sys
from pathlib import Path

p = Path(sys.argv[1] if len(sys.argv) > 1 else "gt6/generated/ppu_recomp_018.cpp")
s = p.read_bytes().decode("latin-1")
eol = "\r\n" if "\r\n" in s[:4000] else "\n"
if "8A7AD0 consumer-wait guard" in s:
    print("already")
    sys.exit(0)
label = "loc_008A7AF4:" + eol
i = s.find(label)
assert i > 0, "label loc_008A7AF4 not found"
branch = "        if ((!((ctx->cr >> 2) & 1))) goto loc_008A7B4C;" + eol
j = s.find(branch, i)
assert j > 0 and j - i < 400, "consumer wait branch not found"
hook = ('        if (((ctx->cr >> 2) & 1) && getenv("GT6_NO_CONSWAIT") == nullptr) { static int n; '
        'if (n++ < 3) fprintf(stderr, "[GT6] 8A7AD0 consumer-wait guard: skipping wait' + chr(92) + 'n"); '
        'goto loc_008A7B4C; }' + eol)
s = s[:j] + hook + s[j:]
p.write_bytes(s.encode("latin-1"))
print("patched")
