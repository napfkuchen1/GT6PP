#!/usr/bin/env python3
"""Diagnostic: log entry of given guest functions into generated ppu_recomp_*.cpp ([A22EN] fn tid lr).
usage: trace_enter.py 8CAAEC 8CA548 ...   (backs up each touched file to work/_bk_a22 first; idempotent per fn)
Restore afterwards by copying work/_bk_a22/<file> back."""
import sys, glob, shutil, os
for fn in sys.argv[1:]:
    name = "func_%08X" % int(fn, 16)
    for p in sorted(glob.glob("gt6/generated/ppu_recomp_*.cpp")):
        s = open(p, "rb").read().decode("latin-1")
        key = "void " + name + "(ppu_context* ctx) {"
        i = s.find(key)
        if i < 0:
            continue
        tag = "[A22EN] " + name
        if tag in s:
            print(fn, "already"); break
        bk = os.path.join("work", "_bk_a22", os.path.basename(p))
        if not os.path.exists(bk):
            os.makedirs(os.path.dirname(bk), exist_ok=True); shutil.copy(p, bk)
        j = s.find("PPU_MM_SNAP", i) + len("PPU_MM_SNAP")
        hook = '        { static int n; if (n++ < 6) fprintf(stderr, "' + tag + ' tid=%llu lr=%08X' + '\\n' + '", (unsigned long long)ctx->thread_id, (uint32_t)ctx->lr); }'
        s = s[:j] + chr(10) + hook + s[j:]
        open(p, "wb").write(s.encode("latin-1")); print(fn, "patched", os.path.basename(p)); break
    else:
        print(fn, "NOT FOUND")
