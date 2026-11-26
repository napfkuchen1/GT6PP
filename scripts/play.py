#!/usr/bin/env python
"""play.py - interactive control of ONE running gt6.exe (menu questions without timed probe runs).

  play.py start [--name N] [--vol DIR] [--env "K=V;K=V"] [--save-src DIR] [--persist DIR] [--keep-db]
  play.py shot [out.png] [--scale 2]
  play.py press <name|0xmask> [reports]
  play.py wait <log regex> | --change | --stable SEC   [--timeout SEC] [--from-start]
  play.py status
  play.py dump [--snap] [--mem <hex>:<hexlen>,...]
  play.py quit [--keep-hdd0]

State isolation as in probe.ps1: per-run hdd0 copy (fresh userdb), empty hdd1, own savedata root,
work\\play_<name>_<ts>\\. Non-headless. Input goes through PAD_FILE. Screenshots are taken from outside
(PrintWindow). --persist DIR keeps savedata + userdb-bearing hdd0 in DIR across sessions (live-save runs).
Refuses to start while a probe.ps1 run or another gt6.exe is active.
"""
import argparse, ctypes, json, os, re, shutil, struct, subprocess, sys, time, zlib
from ctypes import wintypes
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "work" / "play_current.json"
EXE = ROOT / "gt6" / "build" / "gt6.exe"
ELF = ROOT / "work" / "bin" / "EMAIN.elf"
DEFAULT_VOL = "work/gt6_vol_a45"
BUTTONS = {"select": 0x0001, "l3": 0x0002, "r3": 0x0004, "start": 0x0008, "up": 0x0010, "right": 0x0020,
           "down": 0x0040, "left": 0x0080, "l2": 0x0100, "r2": 0x0200, "l1": 0x0400, "r1": 0x0800,
           "triangle": 0x1000, "circle": 0x2000, "cross": 0x4000, "x": 0x4000, "square": 0x8000}
ERR_RX = re.compile(rb"(?i)LWM-LONG|exception|access violation|0xC00000|unhandled|fatal|null call|skipped call|"
                    rb"stack overflow|assert|\[crash|abort|unresolved NID|device removed|HALT")
FLIP = b"SetPrepareFlip"
CHUNK = 8 << 20


def die(msg):
    print("play: " + msg)
    sys.exit(1)


# ---------------------------------------------------------------- processes
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
u32 = ctypes.WinDLL("user32", use_last_error=True)
gdi = ctypes.WinDLL("gdi32", use_last_error=True)
k32.OpenProcess.restype = wintypes.HANDLE
k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
k32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
k32.CloseHandle.argtypes = [wintypes.HANDLE]
k32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                           ctypes.POINTER(wintypes.DWORD)]


def alive(pid):
    h = k32.OpenProcess(0x1000, False, pid)
    if not h:
        return False
    try:
        code = wintypes.DWORD()
        if not k32.GetExitCodeProcess(h, ctypes.byref(code)) or code.value != 259:
            return False
        buf = ctypes.create_unicode_buffer(1024)
        n = wintypes.DWORD(1024)
        k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n))
        return buf.value.lower().endswith("gt6.exe")  # guards against pid reuse
    finally:
        k32.CloseHandle(h)


def busy_processes():
    q = ("Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'gt6.exe' -or ($_.Name -match "
         "'^(pwsh|powershell)\\.exe$' -and $_.CommandLine -match '(probe|boot-batch)\\.ps1' -and "
         "$_.ProcessId -ne $PID -and $_.CommandLine -notmatch 'Get-CimInstance') } | "
         "ForEach-Object { '{0} {1}' -f $_.ProcessId, $_.Name }")
    r = subprocess.run(["pwsh", "-NoProfile", "-Command", q], capture_output=True, text=True, timeout=60)
    if r.returncode:
        die("process check failed: " + r.stderr[:300])
    return [x for x in r.stdout.split("\n") if x.strip()]


def load():
    if not STATE.exists():
        die("no session (run: play.py start)")
    return json.loads(STATE.read_text())


def save(s):
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(s, indent=1))
    os.replace(tmp, STATE)


# ---------------------------------------------------------------- per-run hdd0
def junction(dst, src):
    r = subprocess.run(["cmd", "/c", "mklink", "/J", str(dst), str(src)], capture_output=True)
    if r.returncode:
        die(f"mklink failed for {dst}")


def new_run_hdd0(src, dst):
    """Mirror of New-RunHdd0 in probe.ps1: junctions for big read-only parts, small parts copied."""
    usr = Path("game") / "BCES01893" / "USRDIR"
    (dst / usr).mkdir(parents=True)
    for level, skip in ((Path("."), "game"), (Path("game"), "BCES01893"),
                        (Path("game") / "BCES01893", "USRDIR"), (usr, None)):
        for e in os.scandir(src / level):
            if e.name == skip:
                continue
            t = dst / level / e.name
            if e.is_dir():
                if level == usr and e.name in ("db", "replay", "savedata", "PDIPFS"):
                    shutil.copytree(e.path, t)
                else:
                    junction(t, e.path)
            else:
                shutil.copy2(e.path, t)


def remove_tree_keep_targets(p):
    """Delete a run hdd0; junctions are unlinked, never entered."""
    if not os.path.lexists(p):
        return
    if os.path.isjunction(p) or os.path.islink(p):
        os.rmdir(p)
        return
    for e in os.scandir(p):
        if os.path.isjunction(e.path) or e.is_symlink() or e.is_dir(follow_symlinks=False):
            remove_tree_keep_targets(e.path)
        else:
            os.chmod(e.path, 0o666)
            os.remove(e.path)
    os.rmdir(p)


# ---------------------------------------------------------------- start / quit
def cmd_start(a):
    if STATE.exists():
        s = load()
        if alive(s["pid"]):
            die(f"session already running (pid {s['pid']}); use quit first")
        STATE.unlink()
    busy = busy_processes()
    if busy:
        die("refusing: probe run or gt6.exe active: " + "; ".join(b.strip() for b in busy))
    if not EXE.exists() or not ELF.exists():
        die("missing gt6.exe or EMAIN.elf")
    if shutil.disk_usage(ROOT).free < 100 << 30:
        die("less than 100 GB free")
    pairs = {}
    for p in filter(None, (a.env or "").split(";")):
        if "=" not in p:
            die(f"bad --env entry '{p}'")
        k, v = p.split("=", 1)
        if k == "PS3_HEADLESS":
            die("PS3_HEADLESS is a presence flag; play.py is always non-headless")
        pairs[k] = v
    vol = pairs.get("GT6_VOL_ROOT") or a.vol
    if not (ROOT / vol / "projects" / "gt6" / "boot" / "boot.adc").exists():
        die(f"vol root {vol} has no boot.adc")
    ts = time.strftime("%Y%m%d_%H%M%S")
    run = ROOT / "work" / f"play_{a.name}_{ts}"
    run.mkdir(parents=True)
    src0 = ROOT / "work" / "gt6_hdd0"
    if a.persist:
        base = (ROOT / a.persist).resolve()
        hdd0, gd, fresh = base / "hdd0", base / "gamedata", not (base / "hdd0").exists()
    else:
        hdd0, gd, fresh = run / "hdd0", run / "gamedata", True
    if fresh:
        new_run_hdd0(src0, hdd0)
        if not a.keep_db:
            for f in (hdd0 / "game" / "BCES01893" / "USRDIR" / "db").glob("userdb*.dat"):
                f.unlink()
    sd = gd / "dev_hdd0" / "home" / "00000001" / "savedata"
    sd.mkdir(parents=True, exist_ok=True)
    if a.save_src:
        for d in Path(a.save_src).iterdir():
            if d.is_dir():
                shutil.copytree(d, sd / d.name, dirs_exist_ok=True)
    (run / "hdd1").mkdir()
    pad = run / "pad.txt"
    pad.write_text("")
    env = {k: v for k, v in os.environ.items()
           if k.upper() not in ("PS3_HEADLESS", "PAD_SCRIPT", "RSX_CAP", "RSX_CAP_DIR")}
    env.update({"GT6_UNBUF": "1", "PS3_VERBOSE": "0", "GT6_VOL_ROOT": vol, "GT6_HDD0": str(hdd0),
                "GT6_HDD1": str(run / "hdd1"), "PS3_GAMEDATA_ROOT": str(gd), "PAD_FILE": str(pad),
                "RSX_CAP_DIR": str(run), "PS3_WD_FILE": str(run / "wd.txt")})
    env.update(pairs)
    for c in sorted((ROOT / "tools" / "llvm-mingw").glob("*/bin/clang.exe"))[:1]:
        env["PATH"] = str(c.parent) + os.pathsep + env.get("PATH", "")
    log = run / "run.log"
    flags = 0x00000200 | 0x08000000  # new process group, no console
    with open(log, "wb") as out, open(str(log) + ".err", "wb") as err:
        kw = dict(cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=out, stderr=err, close_fds=True)
        try:  # break away from the caller's job object so the game survives this command
            proc = subprocess.Popen([str(EXE), str(ELF)], creationflags=flags | 0x01000000, **kw)
        except OSError:
            proc = subprocess.Popen([str(EXE), str(ELF)], creationflags=flags, **kw)
    (run / "boot.txt").write_text(f"play exe={EXE} env=" + ";".join(
        f"{k}={env[k]}" for k in ["GT6_VOL_ROOT", *pairs]) + "\n")
    save({"pid": proc.pid, "run": str(run), "t0": time.time(), "hdd0": str(hdd0), "persist": bool(a.persist),
          "pos": {}, "flips": 0, "wait_pos": {}})
    time.sleep(3)
    if proc.poll() is not None:
        die(f"gt6.exe exited at once, code 0x{proc.returncode & 0xFFFFFFFF:08X}; see {log}")
    print(f"started pid {proc.pid} run {run.relative_to(ROOT)} vol {vol}")


def cmd_quit(a):
    s = load()
    run = Path(s["run"])
    was = alive(s["pid"])
    if was:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(s["pid"])], capture_output=True)
        for _ in range(50):
            if not alive(s["pid"]):
                break
            time.sleep(0.2)
        else:
            die("could not kill gt6.exe")
    with open(run / "boot.txt", "a") as f:
        f.write(f"END {int(time.time() - s['t0'])}s {'quit' if was else 'exited by itself'}\n")
    if not s["persist"] and not a.keep_hdd0:
        time.sleep(0.5)
        remove_tree_keep_targets(s["hdd0"])
    STATE.unlink()
    print(f"quit ({'killed' if was else 'was already dead'}) after {int(time.time() - s['t0'])}s")


# ---------------------------------------------------------------- log
def logs(s):
    return [os.path.join(s["run"], "run.log"), os.path.join(s["run"], "run.log.err")]


def read_new(path, pos):
    """Yield complete-line blocks appended after pos, with the new offset."""
    if not os.path.exists(path):
        return
    with open(path, "rb") as f:
        f.seek(pos)
        while True:
            b = f.read(CHUNK)
            if not b:
                return
            cut = b.rfind(b"\n") + 1
            if not cut:
                if len(b) < CHUNK:
                    return
                cut = len(b)
            pos += cut
            f.seek(pos)
            yield b[:cut], pos


def cmd_status(a):
    s = load()
    errs, count, pads, new_flips = {}, 0, [], 0
    for p in logs(s):
        for block, pos in read_new(p, s["pos"].get(p, 0)):
            s["pos"][p] = pos
            new_flips += block.count(FLIP)
            for line in block.split(b"\n"):
                if b"PAD_FILE press" in line:
                    pads.append(line)
                if ERR_RX.search(line):
                    count += 1
                    key = re.sub(rb"0x[0-9A-Fa-f]+|\d+", b"#", line[:100])
                    n, first = errs.get(key, (0, line))
                    errs[key] = (n + 1, first)
    s["flips"] += new_flips
    now = time.time()
    dt = now - s.get("status_t", s["t0"])
    s["status_t"] = now
    save(s)
    w = find_window(s["pid"])
    print(f"alive={alive(s['pid'])} t={int(now - s['t0'])}s flips={s['flips']} (+{new_flips} in {dt:.0f}s) "
          f"log={sum(os.path.getsize(p) for p in logs(s) if os.path.exists(p)) >> 20}MB")
    if w:
        print("window: " + window_title(w))
    for line in pads[-3:]:
        print("pad: " + line.decode("ascii", "replace").strip())
    print(f"new error lines: {count}")
    for n, first in sorted(errs.values(), key=lambda v: -v[0])[:12]:
        print(f"  {n}x {first.decode('ascii', 'replace').strip()[:170]}")


def cmd_dump(a):
    """On-demand watchdog sample or snapshot (PS3_WD_FILE in ppu_loader.cpp); output goes to a file."""
    s = load()
    if not alive(s["pid"]):
        die("gt6.exe is not running")
    run = Path(s["run"])
    t = int(time.time() - s["t0"])
    err = logs(s)[1]
    start = os.path.getsize(err)
    if a.snap:
        snapdir = run / f"snap_{t:05d}"
        cmd = f"snap {snapdir}"
    else:
        cmd = f"wd {a.mem}" if a.mem else "wd"
    ctl = run / "wd.txt"
    ctl.write_text(cmd + "\n")
    t0 = time.time()
    while True:
        time.sleep(0.5)
        try:
            if ctl.stat().st_size == 0:
                break
        except OSError:
            pass
        if not alive(s["pid"]):
            die("gt6.exe died")
        if time.time() - t0 > a.timeout:
            die("no answer (exe without PS3_WD_FILE support, or no lv2 syscall yet)")
    if a.snap:
        print(f"snapshot {snapdir}")
        return
    with open(err, "rb") as f:
        f.seek(start)
        keep = [l for l in f.read().split(b"\n") if l.startswith((b"[WATCHDOG]", b"[WDDUMP]", b"[GSTACK"))]
    out = run / f"wd_{t:05d}.txt"
    out.write_bytes(b"\n".join(keep) + b"\n")
    print(f"{out} {len(keep)} lines t={t}s")


# ---------------------------------------------------------------- window capture
u32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
u32.GetDC.restype = wintypes.HDC
u32.GetDC.argtypes = [wintypes.HWND]
u32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
u32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
u32.IsIconic.argtypes = [wintypes.HWND]
u32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
u32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
u32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
u32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
gdi.CreateCompatibleDC.restype = wintypes.HDC
gdi.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi.CreateCompatibleBitmap.restype = wintypes.HBITMAP
gdi.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi.SelectObject.restype = wintypes.HGDIOBJ
gdi.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
gdi.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT, ctypes.c_void_p,
                          ctypes.c_void_p, wintypes.UINT]
gdi.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi.DeleteDC.argtypes = [wintypes.HDC]


def find_window(pid):
    found = []
    proto = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def cb(h, _):
        p = wintypes.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(p))
        if p.value == pid:
            c = ctypes.create_unicode_buffer(64)
            u32.GetClassNameW(h, c, 64)
            if c.value == "ps3recomp_d3d12":
                found.append(h)
        return True

    u32.EnumWindows(proto(cb), 0)
    return found[0] if found else None


def window_title(h):
    b = ctypes.create_unicode_buffer(256)
    u32.GetWindowTextW(h, b, 256)
    return b.value


def grab(s):
    """Return (w, h, BGRA bytes) of the game window's client area."""
    try:
        u32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except AttributeError:
        pass
    hwnd = find_window(s["pid"])
    if not hwnd:
        die("no game window (not created yet, or process gone)")
    if u32.IsIconic(hwnd):
        u32.ShowWindow(hwnd, 4)  # SW_SHOWNOACTIVATE
        time.sleep(0.5)
    r = wintypes.RECT()
    u32.GetClientRect(hwnd, ctypes.byref(r))
    w, h = r.right, r.bottom
    if w <= 0 or h <= 0:
        die("empty client area")
    sdc = u32.GetDC(None)
    mdc = gdi.CreateCompatibleDC(sdc)
    bmp = gdi.CreateCompatibleBitmap(sdc, w, h)
    old = gdi.SelectObject(mdc, bmp)
    ok = u32.PrintWindow(hwnd, mdc, 1 | 2)  # PW_CLIENTONLY | PW_RENDERFULLCONTENT
    gdi.SelectObject(mdc, old)
    bi = ctypes.create_string_buffer(struct.pack("<IiiHHIIiiII", 40, w, -h, 1, 32, 0, 0, 0, 0, 0, 0), 44)
    buf = ctypes.create_string_buffer(w * h * 4)
    n = gdi.GetDIBits(mdc, bmp, 0, h, buf, bi, 0)
    gdi.DeleteObject(bmp)
    gdi.DeleteDC(mdc)
    u32.ReleaseDC(None, sdc)
    if not ok or n != h:
        die(f"capture failed (PrintWindow={ok}, lines={n})")
    return w, h, buf.raw


def thumb(img, cols=64, rows=36):
    """Coarse grid of (r,g,b) samples for change detection."""
    w, h, d = img
    out = []
    for j in range(rows):
        row = (j * h + h // 2) // rows * w * 4
        for i in range(cols):
            o = row + (i * w + w // 2) // cols * 4
            out.append((d[o + 2], d[o + 1], d[o]))
    return out


def diff_pct(a, b):
    return 100.0 * sum(1 for x, y in zip(a, b) if sum(abs(p - q) for p, q in zip(x, y)) > 30) / len(a)


def write_png(path, img, scale):
    w, h, d = img
    ow, oh = w // scale, h // scale
    raw = bytearray()
    for y in range(oh):
        row = d[y * scale * w * 4:(y * scale * w + w) * 4]
        rgb = bytearray(ow * 3)
        step = 4 * scale
        rgb[0::3] = row[2::step][:ow]
        rgb[1::3] = row[1::step][:ow]
        rgb[2::3] = row[0::step][:ow]
        raw.append(0)
        raw += rgb

    def chunk(t, b):
        return struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b))

    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", ow, oh, 8, 2, 0, 0, 0))
                           + chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b""))
    return ow, oh


def cmd_shot(a):
    s = load()
    img = grab(s)
    t = int(time.time() - s["t0"])
    out = Path(a.out) if a.out else Path(s["run"]) / f"shot_{t:05d}.png"
    ow, oh = write_png(out, img, max(1, a.scale))
    tn = thumb(img)
    nonblack = 100.0 * sum(1 for c in tn if max(c) >= 16) / len(tn)
    print(f"{out} {ow}x{oh} t={t}s non-black={nonblack:.0f}%")


# ---------------------------------------------------------------- press / wait
def cmd_press(a):
    s = load()
    if not alive(s["pid"]):
        die("gt6.exe is not running")
    key = a.button.lower()
    mask = BUTTONS.get(key)
    if mask is None:
        if not re.fullmatch(r"0x[0-9a-f]{1,4}", key) or int(key, 16) == 0:
            die("button must be a name (" + " ".join(BUTTONS) + ") or 0xmask")
        mask = int(key, 16)
    pad = Path(s["run"]) / "pad.txt"
    # remember the log position so a following 'wait' only sees what came after this press
    s["wait_pos"] = {p: os.path.getsize(p) for p in logs(s) if os.path.exists(p)}
    save(s)
    tmp = pad.with_suffix(".new")
    tmp.write_text(f"0x{mask:04X} {a.reports}\n")
    for _ in range(50):
        try:
            os.replace(tmp, pad)
            break
        except PermissionError:
            time.sleep(0.02)
    else:
        die("pad file locked")
    t0 = time.time()
    while time.time() - t0 < a.timeout:
        time.sleep(0.1)
        try:
            if pad.stat().st_size == 0:
                print(f"press 0x{mask:04X} x{a.reports} taken after {time.time() - t0:.1f}s "
                      f"(t={int(time.time() - s['t0'])}s)")
                return
        except OSError:
            pass
        if not alive(s["pid"]):
            die("gt6.exe died")
    pad.write_text("")
    die(f"press not taken within {a.timeout}s (title not polling the pad); cleared")


def cmd_wait(a):
    s = load()
    if not (a.regex or a.change or a.stable):
        die("wait needs a regex, --change or --stable SEC")
    rx = re.compile(a.regex.encode()) if a.regex else None
    pos = {} if a.from_start else dict(s.get("wait_pos", {}))
    base = thumb(grab(s)) if (a.change or a.stable) else None
    t0 = still_since = time.time()
    while True:
        if rx:
            for p in logs(s):
                for block, end in read_new(p, pos.get(p, 0)):
                    pos[p] = end
                    m = rx.search(block)
                    if m:
                        ls = block.rfind(b"\n", 0, m.start()) + 1
                        line = block[ls:block.find(b"\n", m.start())]
                        s["wait_pos"] = pos
                        save(s)
                        print(f"match after {time.time() - t0:.1f}s t={int(time.time() - s['t0'])}s: "
                              + line.decode("ascii", "replace").strip()[:200])
                        return
        if base is not None:
            cur = thumb(grab(s))
            d = diff_pct(base, cur)
            if a.change and d >= a.thresh:
                print(f"screen changed {d:.0f}% after {time.time() - t0:.1f}s t={int(time.time() - s['t0'])}s")
                return
            if a.stable:
                if d >= a.thresh:
                    base, still_since = cur, time.time()
                elif time.time() - still_since >= a.stable:
                    print(f"screen stable {a.stable:.0f}s (<{a.thresh}%) t={int(time.time() - s['t0'])}s")
                    return
        if not alive(s["pid"]):
            print("gt6.exe exited while waiting")
            sys.exit(3)
        if time.time() - t0 >= a.timeout:
            s["wait_pos"] = pos
            save(s)
            print(f"timeout after {a.timeout:.0f}s t={int(time.time() - s['t0'])}s")
            sys.exit(2)
        time.sleep(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("start")
    p.add_argument("--name", default="menu")
    p.add_argument("--vol", default=DEFAULT_VOL)
    p.add_argument("--env", default="")
    p.add_argument("--save-src")
    p.add_argument("--persist")
    p.add_argument("--keep-db", action="store_true")
    p.set_defaults(fn=cmd_start)
    p = sub.add_parser("shot")
    p.add_argument("out", nargs="?")
    p.add_argument("--scale", type=int, default=2)
    p.set_defaults(fn=cmd_shot)
    p = sub.add_parser("press")
    p.add_argument("button")
    p.add_argument("reports", nargs="?", type=int, default=4)
    p.add_argument("--timeout", type=float, default=30)
    p.set_defaults(fn=cmd_press)
    p = sub.add_parser("wait")
    p.add_argument("regex", nargs="?")
    p.add_argument("--change", action="store_true")
    p.add_argument("--stable", type=float, default=0)
    p.add_argument("--thresh", type=float, default=5.0)
    p.add_argument("--timeout", type=float, default=120)
    p.add_argument("--from-start", action="store_true")
    p.set_defaults(fn=cmd_wait)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    p = sub.add_parser("dump")
    p.add_argument("--snap", action="store_true")
    p.add_argument("--mem")
    p.add_argument("--timeout", type=float, default=120)
    p.set_defaults(fn=cmd_dump)
    p = sub.add_parser("quit")
    p.add_argument("--keep-hdd0", action="store_true")
    p.set_defaults(fn=cmd_quit)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
