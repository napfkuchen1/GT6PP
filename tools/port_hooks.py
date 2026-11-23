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
    if s != o:
        p.write_text(s, encoding="latin-1"); n += 1
want = set(STREAM) | set(GUARDED) | {OPEN}
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
