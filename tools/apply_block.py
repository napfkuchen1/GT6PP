#!/usr/bin/env python3
"""Apply the A22_BLOCK oracle-emulation patch: main (tid1) sleeps forever after MGOM.start returns
(call site 0x007A0AC0 in gt6/generated/ppu_recomp_016.cpp) when env A22_BLOCK is set.
Run with: probe.ps1 -Env "GT6_PUMP_ITERS=0;A22_BLOCK=1". Backs up to work/_bk_a22/ppu_recomp_016.cpp. Idempotent."""
import os, shutil
p = "gt6/generated/ppu_recomp_016.cpp"
bk = "work/_bk_a22/ppu_recomp_016.cpp"
s = open(p, "rb").read().decode("latin-1")
if "A22_BLOCK" in s:
    print("already"); raise SystemExit
os.makedirs(os.path.dirname(bk), exist_ok=True)
if not os.path.exists(bk): shutil.copy(p, bk)
k = "ctx->lr = 0x007A0AC0; func_006171D0(ctx); DRAIN_TRAMPOLINE(ctx);"
i = s.index(k) + len(k)
s = s[:i] + ' if (getenv("A22_BLOCK")) { for(;;) { std::this_thread::sleep_for(std::chrono::seconds(1)); } }' + s[i:]
s = s.replace('#include "ppu_recomp.h"', '#include "ppu_recomp.h"\n#include <thread>\n#include <chrono>', 1)
open(p, "wb").write(s.encode("latin-1")); print("patched")
