#!/usr/bin/env python3
"""1.22 guest hooks (ported from the 1.00 set, addresses mapped by fuzzy match, see docs/analysis/PORT.md).
Idempotent text patches on gt6/generated/ppu_recomp_*.cpp. Usage: port_hooks.py [gen_dir]"""
import sys
from pathlib import Path
root = Path(sys.argv[1] if len(sys.argv) > 1 else "gt6/generated")
DECL = (
    'extern "C" void gt6_pfs_host_open_prepare(uint32_t path_ea, uint32_t file_ea);\n'
    'extern "C" void gt6_pfs_host_open_commit(uint32_t file_ea, uint32_t ret_ea);\n'
    'extern "C" int gt6_pfs_stream_read_override(ppu_context* ctx);\n'
    'extern "C" int gt6_pfs_stream_seek_override(ppu_context* ctx);\n'
    'extern "C" int gt6_pfs_stream_tell_override(ppu_context* ctx);\n'
    'extern "C" int gt6_guest_file_vtable_valid(uint32_t object_ea);\n')
INC = '#include "ppu_recomp.h"\n'
# 1.22 address -> hook line (1.00 origin in comment)
STREAM = {
    "00AAAC5C": "if (gt6_pfs_stream_read_override(ctx)) return;\n",  # 9F4AA0
    "00AAB164": "if (gt6_pfs_stream_seek_override(ctx)) return;\n",  # 9F49D8
    "00AAB0B8": "if (gt6_pfs_stream_tell_override(ctx)) return;\n",  # 9F4930
}
GUARD = ("        if (!gt6_guest_file_vtable_valid((uint32_t)ctx->gpr[3])) {\n"
         "            ctx->gpr[3] = 0;\n            return;\n        }\n")
GUARDED = ("00AAA4B0", "00AAA530", "00AAF354")  # 9F3EB0, 9F3F2C, 9F7FF0
OPEN = "00AB080C"  # 9F8E40
STAT = "00AADA6C"  # guest file stat: report overlay file sizes
FSTAT = "00ABD328"  # device stat of an open stream: report served file size
n = 0
done = set()
for p in sorted(root.glob("ppu_recomp_*.cpp")):
    s = p.read_text(encoding="latin-1"); o = s
    if INC in s and "gt6_pfs_stream_read_override" not in s:
        s = s.replace(INC, INC + DECL, 1)
    for name, hook in [(k, v) for k, v in STREAM.items()] + [(k, GUARD.lstrip()) for k in GUARDED]:
        key = f"void func_{name}(ppu_context* ctx) {{\n    PPU_MM_SNAP\n"
        if key in s:
            done.add(name)
            seg = s[s.find(key):s.find(key) + len(key) + len(hook) + 40]
            if hook not in seg:
                s = s.replace(key, key + "        " + hook, 1)
    define = f"void func_{OPEN}(ppu_context* ctx) {{"
    if define in s and f"gt6_orig_func_{OPEN}" not in s:
        s = s.replace(define, f"void gt6_orig_func_{OPEN}(ppu_context* ctx) {{", 1)
        s += ("\n/* Host-open wrapper (1.00 0x9F8E40): r3 path, r4 FileObject = success return. */\n"
              f"void func_{OPEN}(ppu_context* ctx)\n{{\n"
              "    const uint32_t _path = (uint32_t)ctx->gpr[3];\n    const uint32_t _file = (uint32_t)ctx->gpr[4];\n"
              "    gt6_pfs_host_open_prepare(_path, _file);\n"
              f"    gt6_orig_func_{OPEN}(ctx);\n"
              "    gt6_pfs_host_open_commit(_file, (uint32_t)ctx->gpr[3]);\n}\n")
        done.add(OPEN)
    define = f"void func_{STAT}(ppu_context* ctx) {{"
    if define in s and f"gt6_orig_func_{STAT}" not in s:
        s = s.replace(define, f"void gt6_orig_func_{STAT}(ppu_context* ctx) {{", 1)
        s += ("\n/* Stat wrapper: r3 out struct, r4 path. */\n"
              'extern "C" void gt6_pfs_stat_fix(uint32_t out_ea, uint32_t path_ea);\n'
              f"void func_{STAT}(ppu_context* ctx)\n{{\n"
              "    const uint32_t _out = (uint32_t)ctx->gpr[3];\n    const uint32_t _path = (uint32_t)ctx->gpr[4];\n"
              f"    gt6_orig_func_{STAT}(ctx);\n    DRAIN_TRAMPOLINE(ctx);\n"
              "    gt6_pfs_stat_fix(_out, _path);\n}\n")
    if f"gt6_orig_func_{STAT}" in s:
        done.add(STAT)
    define = f"void func_{FSTAT}(ppu_context* ctx) {{"
    if define in s and f"gt6_orig_func_{FSTAT}" not in s:
        s = s.replace(define, f"void gt6_orig_func_{FSTAT}(ppu_context* ctx) {{", 1)
        s += ("\n/* Stream stat wrapper: r4 stream, r5 out struct. */\n"
              'extern "C" void gt6_pfs_fstat_fix(uint32_t stream_ea, uint32_t out_ea);\n'
              f"void func_{FSTAT}(ppu_context* ctx)\n{{\n"
              "    const uint32_t _stream = (uint32_t)ctx->gpr[4];\n    const uint32_t _out = (uint32_t)ctx->gpr[5];\n"
              f"    gt6_orig_func_{FSTAT}(ctx);\n    DRAIN_TRAMPOLINE(ctx);\n"
              "    if ((uint32_t)ctx->gpr[3] == 0) gt6_pfs_fstat_fix(_stream, _out);\n}\n")
    if f"gt6_orig_func_{FSTAT}" in s:
        done.add(FSTAT)
    if s != o:
        p.write_text(s, encoding="latin-1"); n += 1
want = set(STREAM) | set(GUARDED) | {OPEN, STAT, FSTAT}
print("files patched", n, "hooks present", len(done & want), "/", len(want), "missing", sorted(want - done))

# ---- part 2: script hooks + menu pump (1.00 origin in comments; fuzzy map 2026-11-23) ----
DECL2 = (
    'extern "C" void gt6_script_path_hint(uint32_t reader_ea, uint32_t str_ea);\n'
    'extern "C" int gt6_script_read_override(ppu_context* ctx);\n'
    'extern "C" int gt6_script_seek_override(ppu_context* ctx);\n'
    'extern "C" void gt6_menu_project_request(ppu_context* ctx);\n'
    'extern "C" void gt6_menu_project_tick(ppu_context* ctx, uint32_t worker_arg);\n'
    'extern "C" void gt6_menu_project_sync_pump(ppu_context* ctx);\n')
ENTRY = {  # 1.22 func -> hook right after PPU_MM_SNAP
    "00A67E1C": "if (gt6_script_read_override(ctx)) return;\n",  # 9BB020
    "00A67F60": "gt6_script_path_hint((uint32_t)ctx->gpr[3], (uint32_t)ctx->gpr[4]);\n",  # 9BB11C
    "00A67DC4": "if (gt6_script_seek_override(ctx)) return;\n",  # 9BAFE0 (match .42, neighbour order ok)
    "006171D0": "gt6_menu_project_request(ctx);\n",  # 568C94 MGOM.start pending-project setter
}
SYNC_SITE = "        ctx->lr = 0x00617218; func_00AE2844(ctx);"  # 568CCC A21D50 wait
SYNC_CALL = "        gt6_menu_project_sync_pump(ctx);\n"
PUMP_LABEL = "loc_00AD16AC:\n"  # A12170 loop label loc_00A121AC (worker idle loop)
PUMP_CALL = "        gt6_menu_project_tick(ctx, (uint32_t)ctx->gpr[25]);\n"
done2 = set()
for p in sorted(root.glob("ppu_recomp_*.cpp")):
    s = p.read_text(encoding="latin-1"); o = s
    if INC in s and "gt6_script_read_override" not in s:
        s = s.replace(INC, INC + DECL2, 1)
    for name, hook in ENTRY.items():
        key = f"void func_{name}(ppu_context* ctx) {{\n    PPU_MM_SNAP\n"
        if key in s:
            done2.add(name)
            if (key + "        " + hook) not in s:
                s = s.replace(key, key + "        " + hook, 1)
    if SYNC_SITE in s:
        done2.add("sync")
        if SYNC_CALL + SYNC_SITE not in s: s = s.replace(SYNC_SITE, SYNC_CALL + SYNC_SITE, 1)
    if s.count(PUMP_LABEL) == 1:
        done2.add("pump")
        if PUMP_LABEL + PUMP_CALL not in s: s = s.replace(PUMP_LABEL, PUMP_LABEL + PUMP_CALL, 1)
    if s != o:
        p.write_text(s, encoding="latin-1")
print("part2 hooks present", len(done2), "/", len(ENTRY) + 2, "missing", sorted((set(ENTRY) | {"sync", "pump"}) - done2))

# ---- part 3: FileDeviceHost flush guard (1.00 A08A00 -> 1.22 AC7418, Flush A08B8C -> AC75B0; fuzzy 2026-11-23) ----
# Runtime off-switch: env GT6_NO_FDFLUSH=1 (checked at call time).
INIT_ANCHOR = "        ctx->lr = 0x00AC74DC; func_00AAA8EC(ctx); DRAIN_TRAMPOLINE(ctx);\n"
INIT_CLEAR = "        if (!getenv(\"GT6_NO_FDFLUSH\")) vm_write32(ctx->gpr[29] + 0x1C2C, 0); /* local stream destroyed */\n"
FLUSH_KEY = "void func_00AC75B0(ppu_context* ctx) {\n    PPU_MM_SNAP\n"
FLUSH_GUARD = "        if (!getenv(\"GT6_NO_FDFLUSH\") && vm_read8(ctx->gpr[3] + 0x1C29) == 0) return; /* no read active */\n"
done3 = set()
for p in sorted(root.glob("ppu_recomp_*.cpp")):
    s = p.read_text(encoding="latin-1"); o = s
    if "void func_00AC7418(" in s and INIT_ANCHOR in s:
        done3.add("init")
        if INIT_ANCHOR + INIT_CLEAR not in s: s = s.replace(INIT_ANCHOR, INIT_ANCHOR + INIT_CLEAR, 1)
    if FLUSH_KEY in s:
        done3.add("flush")
        if FLUSH_KEY + FLUSH_GUARD not in s: s = s.replace(FLUSH_KEY, FLUSH_KEY + FLUSH_GUARD, 1)
    if s != o:
        if "<stdlib.h>" not in s and "<cstdlib>" not in s: s = s.replace(INC, INC + "#include <stdlib.h>\n", 1)
        p.write_text(s, encoding="latin-1")
print("part3 hooks present", sorted(done3), "/ init,flush")

# ---- part 4: file-cache fill (1.00 func_00B5B260 -> 1.22 func_00C1FE74; fuzzy by A26510->AE6C34, B5A944->C1F604, F7666C->109DCA8) ----
# Env off-switch GT6_NO_CACHEFILL=1. Anchor: after AE6C34 result test, success path jumps to loc_00C20488.
FN4 = "void func_00C1FE74(ppu_context* ctx)"
CALL4 = "ctx->lr = 0x00C2036C; func_00AE6C34(ctx); DRAIN_TRAMPOLINE(ctx);"
BR4 = "if ((!((ctx->cr >> 1) & 1))) goto loc_00C20488;"
# The calls clobber volatile cr fields; the anchor branch still needs the AE6C34 compare (cr7), so save/restore cr.
CRSAVE = "        { const auto _cr = ctx->cr;\n"
CRREST = "        ctx->cr = _cr; }\n"
FILL4 = ("        if (!getenv(\"GT6_NO_CACHEFILL\")) { uint32_t _o=(uint32_t)ctx->gpr[31]; uint32_t _b=vm_read32(_o+0x28); uint32_t _s=vm_read32(_o+0x30);\n"
         "          if(_b && _s){\n"
         "            ctx->gpr[3]=_o; ctx->gpr[4]=0; ctx->lr=0x00C20374; func_00C1F604(ctx); DRAIN_TRAMPOLINE(ctx);\n"
         "            ctx->gpr[3]=_o; ctx->gpr[4]=_b; ctx->gpr[5]=_s; ctx->lr=0x00C20374; func_0109DCA8(ctx); DRAIN_TRAMPOLINE(ctx);\n"
         "          } }\n")
n4 = 0
for p in sorted(root.glob("ppu_recomp_*.cpp")):
    s = p.read_text(encoding="latin-1")
    a = s.find(FN4)
    if a < 0: continue
    e = s.find("\nvoid func_", a + 20); e = len(s) if e < 0 else e
    body = s[a:e]
    if "GT6_NO_CACHEFILL" in body:
        if "_cr = ctx->cr" in body: print("part4 already"); continue
        c = body.find(CALL4); f = body.find("if (!getenv(\"GT6_NO_CACHEFILL", c); b = body.find(BR4, c)
        if not 0 <= f < b: print("part4 upgrade anchors missing"); continue
        nb = body[:f] + CRSAVE.lstrip() + "        " + body[f:b].rstrip() + "\n" + CRREST + "        " + body[b:]
        s = s[:a] + nb + s[e:]
        p.write_text(s, encoding="latin-1"); n4 += 1; continue
    c = body.find(CALL4); b = body.find(BR4, c) if c >= 0 else -1
    if b < 0: print("part4 anchors missing"); continue
    nb = body[:b] + CRSAVE.lstrip() + FILL4 + CRREST + "        " + body[b:]
    s = s[:a] + nb + s[e:]
    if "<stdlib.h>" not in s: s = s.replace(INC, INC + "#include <stdlib.h>\n", 1)
    p.write_text(s, encoding="latin-1"); n4 += 1
print("part4 patched", n4)

# ---- part 5: stream read job file size (1.22 func_00AAB258 loads FileObject+0xC8 = 1.00 TOC size) ----
LOAD5 = "        ctx->gpr[26] = vm_read64(ctx->gpr[30] + 0xC8);\n"
DECL5 = 'extern "C" void gt6_pfs_size_fix(uint32_t file_ea);\n'
CALL5 = "        gt6_pfs_size_fix((uint32_t)ctx->gpr[30]);\n"
n5 = 0
for p in sorted(root.glob("ppu_recomp_*.cpp")):
    s = p.read_text(encoding="latin-1")
    a = s.find("ctx->lr = 0x00AAB32C;")
    if a < 0: continue
    i = s.rfind(LOAD5, 0, a)
    if i < 0: continue
    if not s[:i].endswith(CALL5):
        s = s[:i] + CALL5 + s[i:]
        if DECL5 not in s: s = s.replace(INC, INC + DECL5, 1)
        p.write_text(s, encoding="latin-1")
    n5 += 1
print("part5 hooks present", n5, "/ 1")
