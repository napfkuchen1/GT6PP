#!/usr/bin/env python3
"""Add a one-line stderr log of r3 after a direct call site in generated cpp. Idempotent.
usage: log_ret.py <file> <lr_hex> <func_name> <tag>"""
import sys
from pathlib import Path
p = Path(sys.argv[1]); lr, fn, tag = sys.argv[2], sys.argv[3], sys.argv[4]
s = p.read_bytes().decode("latin-1")
old = "ctx->lr = 0x%s; %s(ctx); DRAIN_TRAMPOLINE(ctx);" % (lr, fn)
nl = chr(92) + "n"
new = old + ' { static int n_; if (n_++ < 8) fprintf(stderr, "[RET %s] r3=%%llx lr=%s' % (tag, lr) + nl + '", (unsigned long long)ctx->gpr[3]); }'
if ("[RET %s]" % tag) in s:
    print("already")
else:
    assert s.count(old) == 1, s.count(old)
    p.write_bytes(s.replace(old, new).encode("latin-1"))
    print("patched", tag)
