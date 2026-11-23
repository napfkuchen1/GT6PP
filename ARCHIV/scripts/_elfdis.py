"""Shared helpers: load EMAIN.elf code segments, disassemble PPC64 BE with capstone."""
import os, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ELF = os.environ.get("SNAP_ELF", os.path.join(ROOT, "work", "bin", "EMAIN.elf"))


def load_segments(path=ELF):
    from elftools.elf.elffile import ELFFile
    segs = []
    with open(path, "rb") as f:
        e = ELFFile(f)
        for s in e.iter_segments():
            if s["p_type"] != "PT_LOAD":
                continue
            segs.append((s["p_vaddr"], s.data(), s["p_flags"]))
    return segs


def code_segments(segs):
    return [(v, d) for v, d, fl in segs if fl & 1]


def read(segs, ea, n):
    for v, d, _ in segs:
        if v <= ea < v + len(d):
            return d[ea - v: ea - v + n]
    return b""


def md():
    import capstone as cs
    m = cs.Cs(cs.CS_ARCH_PPC, cs.CS_MODE_64 | cs.CS_MODE_BIG_ENDIAN)
    m.detail = False
    return m


def fmt(i):
    return "%08X  %-8s %s" % (i.address, i.mnemonic, i.op_str)


def parse_int(s):
    return int(s, 0)


def disasm_all(md, buf, base, block=0x10000):
    """Block-wise capstone; resyncs after undecodable words so scans cover the whole range."""
    n = len(buf)
    for b in range(0, n, block):
        blk = bytes(buf[b:b + block])
        off = 0
        while off < len(blk):
            last = None
            for ins in md.disasm(blk[off:], base + b + off):
                last = ins
                yield ins
            off = (last.address - base - b + 4) if last else off + 4
