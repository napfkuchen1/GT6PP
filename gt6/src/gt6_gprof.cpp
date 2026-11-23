/* Guest-PC sampler for gt6 (GT6_GPROF=1). Port of boot_main.cpp guest_prof_thread.
 * Every ~5 ms samples cia + prof_pc (last syscall/HLE callsite) of each running
 * guest thread; every 5 s (GT6_GPROF_SEC) prints top sites per sample window.
 * cia/prof_pc are refreshed at syscalls only: a thread parked in a wait shows
 * its wait callsite. Started from a static initializer, no main() change. */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "sys_ppu_thread.h"

namespace {
struct Site { uint32_t tid, cia, ppc; uint32_t hits; };
Site sites[512];

DWORD WINAPI gprof_thread(LPVOID)
{
    int nsites = 0; unsigned total = 0;
    int period = 5000;
    if (const char* e = getenv("GT6_GPROF_SEC")) period = atoi(e) * 1000;
    ULONGLONG t0 = GetTickCount64();
    for (;;) {
        Sleep(5);
        for (int i = 0; i < PPU_THREAD_MAX; i++) {
            ppu_thread_info* t = &g_ppu_threads[i];
            if (t->state != PPU_THREAD_STATE_RUNNING) continue;
            uint32_t cia = (uint32_t)t->ctx.cia, ppc = t->prof_pc;
            if (!cia && !ppc) continue;
            uint32_t tid = (uint32_t)(i + 1);
            total++;
            int f = -1;
            for (int k = 0; k < nsites; k++)
                if (sites[k].tid == tid && sites[k].cia == cia && sites[k].ppc == ppc) { f = k; break; }
            if (f < 0 && nsites < 512) { f = nsites++; sites[f] = { tid, cia, ppc, 0 }; }
            if (f >= 0) sites[f].hits++;
        }
        ULONGLONG now = GetTickCount64();
        if ((int)(now - t0) >= period) {
            fprintf(stderr, "[gprof] t=%llus %u samples; top sites:\n", (unsigned long long)(now / 1000), total);
            for (int rank = 0; rank < 25; rank++) {
                int best = -1; uint32_t bh = 0;
                for (int k = 0; k < nsites; k++) if (sites[k].hits > bh) { bh = sites[k].hits; best = k; }
                if (best < 0) break;
                fprintf(stderr, "[gprof]  tid=%-3u cia=0x%08X pc=0x%08X %5.1f%% entry=0x%llX %s\n",
                        sites[best].tid, sites[best].cia, sites[best].ppc,
                        100.0 * bh / (total ? total : 1),
                        (unsigned long long)g_ppu_threads[sites[best].tid - 1].entry_addr,
                        g_ppu_threads[sites[best].tid - 1].name);
                sites[best].hits = 0;
            }
            fflush(stderr);
            nsites = 0; total = 0; t0 = now;
        }
    }
}
struct Starter { Starter() { if (getenv("GT6_GPROF")) CreateThread(NULL, 0, gprof_thread, NULL, 0, NULL); } } g_starter;
}
