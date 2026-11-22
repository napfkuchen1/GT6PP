#!/usr/bin/env python
"""Offline walker for PS3_SNAP_AT snapshots (work/snap_<ts>/).

Usage (PowerShell):
  C:\\Users\\Daniel\\AppData\\Local\\Programs\\Python\\Python313\\python.exe -I scripts\\snap_walk.py <snapdir> <cmd> [args]

Commands (all addresses hex; output is capped, never dumps whole RAM):
  threads                 threads.txt (one line per thread, regs trimmed)
  sync [RX]               sync.txt, optional regex filter
  obj <ea> [len=0x80]     object fields as be32; each pointer annotated:
                          ->vtable(slots)/OPD(code)/heap/stack/ELF-data
  vt <ea> [slots=48]      vtable: slot offset, raw ptr, OPD->code addr
  opd <ea>                OPD (code, toc) at ea
  dis <code_ea> [n=40]    disassemble guest code (capstone, PPC64 BE) from ELF
  callee <ea>             Hyp. 35 chain: [ea+0x14] -> obj -> vtable -> slot 0x54 -> disassemble
  find32 <val> [max=20]   search main RAM + HLE heap for be32 value (aligned)
  stack <tid> [n=64]      stack words of a thread with annotations
Env: SNAP_ELF=<path> overrides work\\bin\\EMAIN.elf
"""
import os, re, struct, sys, mmap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ELF = os.environ.get("SNAP_ELF", os.path.join(ROOT, "work", "bin", "EMAIN.elf"))
MAIN_BASE, MAIN_SIZE = 0x00010000, 0x10000000
HLE_BASE, HLE_SIZE = 0x50000000, 0x08000000


class Mem:
    def __init__(self, d):
        self.d = d
        self.regions = []   # (base, size, buffer, name)
        self._open(os.path.join(d, "ram_main.bin"), MAIN_BASE, "main")
        self._open(os.path.join(d, "ram_hle.bin"), HLE_BASE, "hle")
        for fn in sorted(os.listdir(d)):
            m = re.match(r"reg_([0-9A-Fa-f]{8})\.bin$", fn)
            if m:
                self._open(os.path.join(d, fn), int(m.group(1), 16), "main" if int(m.group(1), 16) == MAIN_BASE else "reg")
        for fn in sorted(os.listdir(d)):
            m = re.match(r"stack_(\d+)_([0-9A-Fa-f]{8})\.bin$", fn)
            if m:
                self._open(os.path.join(d, fn), int(m.group(2), 16), "stack%s" % m.group(1))
        self.elf = []   # (vaddr, bytes, flags)
        self._load_elf()

    def _open(self, p, base, name):
        if not os.path.exists(p):
            return
        f = open(p, "rb")
        sz = os.path.getsize(p)
        if sz == 0:
            return
        self.regions.append((base, sz, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ), name))

    def _load_elf(self):
        if not os.path.exists(ELF):
            return
        from elftools.elf.elffile import ELFFile
        with open(ELF, "rb") as f:
            e = ELFFile(f)
            for s in e.iter_segments():
                if s["p_type"] == "PT_LOAD":
                    self.elf.append((s["p_vaddr"], s.data(), s["p_flags"]))

    def region(self, ea):
        for b, sz, buf, n in self.regions:
            if b <= ea < b + sz:
                return n
        for v, data, fl in self.elf:
            if v <= ea < v + len(data):
                return "elf"
        return None

    def read(self, ea, n, prefer_elf=False):
        order = (self._elf_read, self._snap_read) if prefer_elf else (self._snap_read, self._elf_read)
        for fn in order:
            r = fn(ea, n)
            if r is not None:
                return r
        return None

    def _snap_read(self, ea, n):
        for b, sz, buf, _ in self.regions:
            if b <= ea and ea + n <= b + sz:
                return buf[ea - b:ea - b + n]
        return None

    def _elf_read(self, ea, n):
        for v, data, _ in self.elf:
            if v <= ea and ea + n <= v + len(data):
                return data[ea - v:ea - v + n]
        return None

    def u32(self, ea, prefer_elf=False):
        r = self.read(ea, 4, prefer_elf)
        return None if r is None else struct.unpack(">I", r)[0]

    def is_code(self, ea):
        for v, data, fl in self.elf:
            if v <= ea < v + len(data) and (fl & 1):
                return True
        return False


def tag(m, val):
    """Annotate a be32 value."""
    if val == 0:
        return ""
    if m.is_code(val):
        return "CODE"
    if m.region(val) is None:
        return ""
    # OPD?
    w0 = m.u32(val, prefer_elf=True)
    if w0 is not None and m.is_code(w0) and val & 3 == 0:
        w1 = m.u32(val + 4)
        return "OPD->%08X toc=%s" % (w0, "%08X" % w1 if w1 is not None else "?")
    # vtable-like: first words are OPD/code pointers
    if val & 3 == 0:
        ws = [m.u32(val + 4 * i) for i in range(3)]
        if all(w is not None and w and (m.is_code(w) or (m.region(w) and m.is_code(m.u32(w, True) or 0))) for w in ws):
            return "VTABLE?"
    return "ptr[%s]" % m.region(val)


def cmd_obj(m, ea, ln):
    for off in range(0, ln, 4):
        v = m.u32(ea + off)
        if v is None:
            print("+%03X ????????" % off)
            continue
        print("+%03X %08X  %s" % (off, v, tag(m, v)))


def code_of_slot(m, val):
    if val is None:
        return None
    if m.is_code(val):
        return val
    w0 = m.u32(val, prefer_elf=True)
    if w0 is not None and m.is_code(w0):
        return w0
    return None


def cmd_vt(m, ea, n):
    for i in range(n):
        v = m.u32(ea + 4 * i)
        print("+%03X %08X -> code %s" % (4 * i, v or 0, ("%08X" % code_of_slot(m, v)) if code_of_slot(m, v) else "-"))


def cmd_dis(m, ea, n):
    from capstone import Cs, CS_ARCH_PPC, CS_MODE_64, CS_MODE_BIG_ENDIAN
    md = Cs(CS_ARCH_PPC, CS_MODE_64 | CS_MODE_BIG_ENDIAN)
    data = m.read(ea, 4 * n, prefer_elf=True)
    if data is None:
        print("no data at %08X" % ea)
        return
    cnt = 0
    for i in md.disasm(bytes(data), ea):
        print("%08X  %s %s" % (i.address, i.mnemonic, i.op_str))
        cnt += 1
    if cnt < n:
        for k in range(cnt, n):  # capstone stops on unknown opcode
            w = struct.unpack(">I", data[4 * k:4 * k + 4])[0]
            print("%08X  .long %08X" % (ea + 4 * k, w))


def cmd_callee(m, ea):
    obj = m.u32(ea + 0x14)
    print("callee %08X  [+0x14] = %08X  %s" % (ea, obj or 0, tag(m, obj or 0)))
    if not obj:
        return
    vt = m.u32(obj)
    print("obj %08X vtable = %08X" % (obj, vt or 0))
    if not vt:
        return
    slot = m.u32(vt + 0x54)
    code = code_of_slot(m, slot)
    print("vtable+0x54 = %08X -> code %s" % (slot or 0, "%08X" % code if code else "-"))
    if code:
        cmd_dis(m, code, 48)


def cmd_threads(m, d):
    p = os.path.join(d, "threads.txt")
    for line in open(p):
        if line.startswith("thread"):
            print(line.rstrip())


def cmd_sync(d, rx):
    r = re.compile(rx) if rx else None
    n = 0
    for line in open(os.path.join(d, "sync.txt")):
        if r is None or r.search(line):
            print(line.rstrip())
            n += 1
            if n >= 120:
                print("... capped")
                break


def cmd_find32(m, val, mx):
    pat = struct.pack(">I", val)
    found = 0
    for b, sz, buf, n in m.regions:
        if n.startswith("stack"):
            continue
        pos = 0
        while found < mx:
            i = buf.find(pat, pos)
            if i < 0:
                break
            if i % 4 == 0:
                print("%08X  (%s)" % (b + i, n))
                found += 1
            pos = i + 1


def cmd_stack(m, d, tid, n):
    sp = None
    for line in open(os.path.join(d, "threads.txt")):
        mt = re.match(r"thread %s .* sp=([0-9A-F]{8})" % tid, line)
        if mt:
            sp = int(mt.group(1), 16)
    if sp is None:
        print("tid not found")
        return
    for i in range(n):
        v = m.u32(sp + 4 * i)
        print("sp+%03X %08X  %s" % (4 * i, v or 0, tag(m, v or 0)))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    d, cmd, a = sys.argv[1], sys.argv[2], sys.argv[3:]
    h = lambda i, dflt=None: int(a[i], 16) if len(a) > i else dflt
    m = Mem(d)
    if cmd == "threads": cmd_threads(m, d)
    elif cmd == "sync": cmd_sync(d, a[0] if a else None)
    elif cmd == "obj": cmd_obj(m, h(0), h(1, 0x80))
    elif cmd == "vt": cmd_vt(m, h(0), int(a[1]) if len(a) > 1 else 48)
    elif cmd == "opd": print("code=%08X toc=%08X" % (m.u32(h(0), True), m.u32(h(0) + 4, True)))
    elif cmd == "dis": cmd_dis(m, h(0), int(a[1]) if len(a) > 1 else 40)
    elif cmd == "callee": cmd_callee(m, h(0))
    elif cmd == "find32": cmd_find32(m, h(0), int(a[1]) if len(a) > 1 else 20)
    elif cmd == "stack": cmd_stack(m, d, a[0], int(a[1]) if len(a) > 1 else 64)
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
