#!/usr/bin/env python3
"""Minimal SELF -> ELF decrypter (APP + NPDRM). Needs `cryptography` and a scetool-style
keys file (gt6/data/keys, never committed). Usage:
  self_decrypt_np.py in.SELF out.elf [klicensee_hex]   (klicensee only for NPDRM SELFs)
"""
import sys, struct, zlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

NP_KLIC_KEY = bytes.fromhex("F2FBCA7A75B04EDC1390638CCDFDD1EE")

def ecb(k, d):
    x = Cipher(algorithms.AES(k), modes.ECB()).decryptor(); return x.update(d) + x.finalize()
def cbc(k, iv, d):
    x = Cipher(algorithms.AES(k), modes.CBC(iv)).decryptor(); return x.update(d) + x.finalize()
def ctr(k, iv, d):
    x = Cipher(algorithms.AES(k), modes.CTR(iv)).decryptor(); return x.update(d) + x.finalize()

def load_keys(path):
    out, cur = {}, None
    for l in open(path, encoding="utf-8", errors="replace"):
        l = l.strip()
        if l.startswith("["): cur = {}
        elif "=" in l and cur is not None:
            k, _, v = l.partition("="); cur[k.strip()] = v.strip()
            if k.strip() == "ctype":
                out[(cur["self_type"], int(cur["revision"], 16))] = (bytes.fromhex(cur["erk"]), bytes.fromhex(cur["riv"]))
    return out

def main():
    src, dst = sys.argv[1], sys.argv[2]
    klic = bytes.fromhex(sys.argv[3]) if len(sys.argv) > 3 else None
    keys = load_keys(__file__.replace("\\", "/").rsplit("/tools/", 1)[0] + "/gt6/data/keys")
    d = open(src, "rb").read()
    assert d[:4] == b"SCE\0"
    rev, typ, meta, hlen = struct.unpack(">HHIQ", d[8:24])
    _, ai, eo, po, so, sio, vo, ci, cs = struct.unpack(">QQQQQQQQQ", d[0x20:0x68])
    selftype = struct.unpack(">QIIQ", d[ai:ai + 24])[2]
    st = "NPDRM" if selftype == 8 else "APP"
    erk, riv = keys[(st, rev)]
    ms = meta + 0x20
    root = d[ms:ms + 0x40]
    if st == "NPDRM":
        root = cbc(ecb(NP_KLIC_KEY, klic), bytes(16), root)
    r = cbc(erk, riv, root)
    assert r[16:32] == bytes(16) and r[48:64] == bytes(16), "metadata key wrong"
    mk, mi = r[0:16], r[32:48]
    rest = d[ms + 0x40: hlen]
    dec = ctr(mk, mi, rest)
    siglen, _, scount, kcount, opt, _ = struct.unpack(">QIIIIQ", dec[:0x20])
    secs = []
    for i in range(scount):
        o = 0x20 + i * 0x30
        secs.append(struct.unpack(">QQIIIIIIII", dec[o:o + 0x30])[:10])
    kb = 0x20 + scount * 0x30
    ks = [dec[kb + i * 16: kb + i * 16 + 16] for i in range(kcount)]
    ehdr = d[eo:eo + 0x40]
    e_phoff, e_shoff = struct.unpack(">QQ", ehdr[0x20:0x30])
    e_phnum, e_shentsize, e_shnum = struct.unpack(">H", ehdr[0x38:0x3a])[0], struct.unpack(">H", ehdr[0x3a:0x3c])[0], struct.unpack(">H", ehdr[0x3c:0x3e])[0]
    phs = [struct.unpack(">IIQQQQQQ", d[po + i * 0x38: po + i * 0x38 + 0x38]) for i in range(e_phnum)]
    out = bytearray(max([p[2] + p[5] for p in phs] + [e_shoff + e_shnum * 0x40]))
    out[0:0x40] = ehdr
    out[e_phoff:e_phoff + e_phnum * 0x38] = d[po:po + e_phnum * 0x38]
    out[e_shoff:e_shoff + e_shnum * 0x40] = d[so:so + e_shnum * 0x40]
    n = 0
    for (off, size, stype, idx, hashed, shi, enc, ki, ii, comp) in secs:
        if stype != 2: continue
        data = d[off:off + size]
        if enc == 3: data = ctr(ks[ki], ks[ii], data)
        if comp == 2: data = zlib.decompress(data)
        p = phs[idx]
        out[p[2]:p[2] + len(data)] = data; n += 1
    open(dst, "wb").write(out)
    print("ok", st, "sections", n, "bytes", len(out))

main()
