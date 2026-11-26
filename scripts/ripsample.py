#!/usr/bin/env python
"""ripsample.py - sample the busy host threads of a running gt6.exe.

  python -I scripts/ripsample.py [--secs 10] [--threads 4] [--pid N]

Per busy thread: top leaf symbols and top call chains (return addresses scanned
off the stack, so a chain may contain stale entries). Symbols: gt6/build/gt6.map.
"""
import argparse, bisect, collections, ctypes as C, os, re, sys, time
from ctypes import wintypes as W

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
k = C.WinDLL("kernel32", use_last_error=True)
ps = C.WinDLL("psapi", use_last_error=True)
for f, res, args in (
        ("OpenProcess", W.HANDLE, (W.DWORD, W.BOOL, W.DWORD)),
        ("OpenThread", W.HANDLE, (W.DWORD, W.BOOL, W.DWORD)),
        ("CreateToolhelp32Snapshot", W.HANDLE, (W.DWORD, W.DWORD)),
        ("SuspendThread", W.DWORD, (W.HANDLE,)), ("ResumeThread", W.DWORD, (W.HANDLE,)),
        ("GetThreadContext", W.BOOL, (W.HANDLE, C.c_void_p)),
        ("GetThreadTimes", W.BOOL, (W.HANDLE,) + (C.c_void_p,) * 4),
        ("ReadProcessMemory", W.BOOL, (W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.c_void_p)),
        ("CloseHandle", W.BOOL, (W.HANDLE,))):
    getattr(k, f).restype, getattr(k, f).argtypes = res, args
ps.EnumProcessModules.argtypes = (W.HANDLE, C.c_void_p, W.DWORD, C.c_void_p)
ps.GetModuleBaseNameW.argtypes = (W.HANDLE, C.c_void_p, W.LPWSTR, W.DWORD)
ps.EnumProcesses.argtypes = (C.c_void_p, W.DWORD, C.c_void_p)


class TE(C.Structure):
    _fields_ = [(n, W.DWORD) for n in ("size", "usage", "tid", "pid", "base", "delta", "flags")]


def find_pid():
    ids, got = (W.DWORD * 8192)(), W.DWORD()
    ps.EnumProcesses(ids, C.sizeof(ids), C.byref(got))
    for pid in ids[:got.value // 4]:
        h = k.OpenProcess(0x410, False, pid)
        if not h:
            continue
        name = C.create_unicode_buffer(260)
        ps.GetModuleBaseNameW(h, None, name, 260)
        k.CloseHandle(h)
        if name.value.lower() == "gt6.exe":
            return pid
    sys.exit("no gt6.exe running")


def threads(pid):
    snap = k.CreateToolhelp32Snapshot(4, 0)
    e = TE(); e.size = C.sizeof(e)
    out = []
    ok = k.Thread32First(snap, C.byref(e))
    while ok:
        if e.pid == pid:
            out.append(e.tid)
        ok = k.Thread32Next(snap, C.byref(e))
    k.CloseHandle(snap)
    return out


def cpu(h):
    t = [C.c_ulonglong() for _ in range(4)]
    k.GetThreadTimes(h, *[C.byref(x) for x in t])
    return (t[2].value + t[3].value) / 1e7


def load_map(path):
    rx = re.compile(r"^\s*[0-9a-f]{4}:[0-9a-f]{8}\s+(\S+)\s+([0-9a-f]{16})\s")
    syms, pref = [], 0x140000000
    for line in open(path, encoding="latin-1"):
        m = rx.match(line)
        if m and int(m[2], 16) >= pref:
            syms.append((int(m[2], 16) - pref, m[1]))
    syms.sort()
    return [s[0] for s in syms], [s[1] for s in syms]


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--secs", type=float, default=10)
    a.add_argument("--threads", type=int, default=4)
    a.add_argument("--pid", type=int)
    o = a.parse_args()
    pid = o.pid or find_pid()
    ph = k.OpenProcess(0x410, False, pid)
    mods, got = (C.c_void_p * 1024)(), W.DWORD()
    ps.EnumProcessModules(ph, mods, C.sizeof(mods), C.byref(got))
    bases = []
    for m in mods[:got.value // 8]:
        name = C.create_unicode_buffer(260)
        ps.GetModuleBaseNameW(ph, m, name, 260)
        bases.append((m, name.value))
    base = bases[0][0]
    bases.sort()
    offs, names = load_map(os.path.join(ROOT, "gt6", "build", "gt6.map"))
    end = base + offs[-1]

    def sym(addr):
        if base <= addr < end:
            return names[bisect.bisect_right(offs, addr - base) - 1]
        i = bisect.bisect_right([b[0] for b in bases], addr) - 1
        return "[%s]" % bases[i][1] if i >= 0 else "?"

    hs = {t: k.OpenThread(0x004A, False, t) for t in threads(pid)}   # suspend|context|query
    c0 = {t: cpu(h) for t, h in hs.items() if h}
    time.sleep(1.0)
    busy = sorted(((cpu(hs[t]) - c0[t], t) for t in c0), reverse=True)[:o.threads]
    leaf = {t: collections.Counter() for _, t in busy}
    chain = {t: collections.Counter() for _, t in busy}
    raw = (C.c_ubyte * 1248)()
    ctx = (C.addressof(raw) + 15) & ~15
    stack = (C.c_ulonglong * 512)()
    stop = time.time() + o.secs
    while time.time() < stop:
        for _, t in busy:
            h = hs[t]
            if k.SuspendThread(h) == 0xFFFFFFFF:
                continue
            C.c_uint32.from_address(ctx + 0x30).value = 0x100003   # control|integer
            ok = k.GetThreadContext(h, ctx)
            rip = C.c_ulonglong.from_address(ctx + 0xF8).value
            rsp = C.c_ulonglong.from_address(ctx + 0x98).value
            read = ok and k.ReadProcessMemory(ph, rsp, stack, C.sizeof(stack), None)
            k.ResumeThread(h)
            if not ok:
                continue
            leaf[t][sym(rip)] += 1
            seen = [sym(rip)]
            for v in (stack if read else ()):
                if base + 0x1000 <= v < end:
                    s = sym(v)
                    if s not in seen and not s.startswith("??_"):
                        seen.append(s)
                        if len(seen) == 7:
                            break
            chain[t][" < ".join(seen)] += 1
        time.sleep(0.02)
    for d, t in busy:
        n = sum(leaf[t].values()) or 1
        print("thread %d cpu=%.2fs/s samples=%d" % (t, d, n))
        print("  leaf: " + ", ".join("%s %d%%" % (s, 100 * c // n) for s, c in leaf[t].most_common(5)))
        for s, c in chain[t].most_common(3):
            print("  %2d%% %s" % (100 * c // n, s[:330]))


if __name__ == "__main__":
    main()
