# GT6PP roadmap: to a race that is playable at 60 FPS with an XInput pad

Snapshot of 2026-11-26. Live checklist: `docs/analysis/STATE.md` (single source of truth); this file is not
read by the loop guard. IDs `R*` exist only here.

## Where we are

Game 1.22 (EU, BCES01893) on ps3recomp v0.20. The Home menu is reached, the opening movie plays to the end,
the dealer works and a car can be bought. No race has been driven yet.

M1 (main menu): 15 items checked off, 16 open.

Done (evidence in the checklist files): T1, T2, G1, I1a, I1b, I1c, C1, C2, G4, G5, G6a, G6b, G6c, S3, D3.

## Target (proposed acceptance, not yet agreed)

One complete race on one track, started from the menu, driven with a physical XInput pad: 60 FPS (59.94)
sustained, no crash or stall, audio, result saved and still there after a restart, none of the W* workarounds
costing frame rate.

## Known frame rates

| Scene | Measured | Note |
|---|---|---|
| Car view | 4.8-5 FPS | after lifting the SPU job modules (was 0.9); rest still interpreted (D4) |
| Attract demo (race) | 0.29 FPS | measured before the SPU lifting, not re-measured (D1) |
| Opening movie | 60 pictures/s | paced correctly (I1b) |
| Driven race | not measured | not reached yet |

The gap in race scenes is therefore unknown and may be large. R3 comes before any estimate.

## Phase 1: finish M1

| ID | Open point |
|---|---|
| I2 | tutorial/intro flow runs without the skip overlay (next step) |
| I3 | movie audio: decoder wired, not verified by ear |
| L1 | live run with window, persistent save, real pad input |
| G2 | car-name text in the dealer list smeared |
| G3 | dealer tile backing covers only part of each tile |
| G6d | showroom washed out (parked, bypass in place) |
| G7 | popups drawn on top of each other: compare with the original |
| D2 | idle demo cannot be cancelled by input during the countdown: check |
| S1 | car-view stall: fixes in, verify over more runs |
| S2 | boot crash 0xC00000FD, 1 of 8 runs |

## Phase 2: XInput

State: the runtime already has an XInput backend (`third_party/ps3recomp-v020/libs/input/cellPad.c`): DLL
loaded at run time, buttons, both sticks with dead zone, analog L2/R2 as pressure values, rumble, keyboard
input. A pad is ignored while the window has no focus (`PAD_BACKGROUND=1` overrides). It has **not** been
verified with a physical pad on the current line; scripted input (`PAD_SCRIPT`, `PAD_FILE`) is what all runs
use.

| ID | Open point |
|---|---|
| R1 | menu fully controllable with a physical XInput pad, including hot-plug (covered partly by L1) |
| R2 | in a race: steering, analog throttle and brake, rumble, no noticeable input lag |

## Phase 3: first race (M2)

| ID | Open point |
|---|---|
| R3 | a race loads from the menu; record a frame-time profile (PPU, SPU, RSX translation, waits) |
| D1 | attract demo loads very slowly; likely shares causes with R3 (unverified) |
| R4 | race renders correctly: track, cars, HUD |
| R5 | race can be finished, results screen, save persists |
| R6 | race audio (engine, effects, music) |

## Phase 4: 60 FPS

Order follows the R3 profile; the list below is the known candidates.

| ID | Open point |
|---|---|
| D4 | recompile the remaining interpreted SPU code (images 76 and 74, policy module) |
| R7 | find and recompile SPU jobs that only run in races |
| W2 | remove one-core pinning (`PPU_ONECORE=1`): guest threads need real parallelism |
| R8 | cost of the D3D12 backend, including render-target readback into guest memory |
| R9 | stable frame pacing at 59.94 with the 60 Hz guest vblank and host vsync |
| W1 | confirm the spliced interpreter bodies with a full re-lift |
| W3 | remove `GCM_PARK_GRACE_MS=5000` (FIFO resync) |
| W4 | remove the `GCM_SEMA_BLOCK=500-560` workaround |

## Risks

- Race performance is the biggest unknown; nothing measured supports a date or effort estimate.
- Race code paths (SPU jobs, shaders, physics timing) are untested and will likely show new blockers.
- Several stability fixes depend on timing workarounds that may break once pinning is removed.
