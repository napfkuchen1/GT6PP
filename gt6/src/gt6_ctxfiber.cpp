/*
 * cellFiberPpuContext* (libfiber "context" API) on host Windows fibers.
 *
 * GT6 imports _cellFiberPpuContextAttributeInitialize (0x31252EC3),
 * cellFiberPpuContextInitialize (0x72086315), cellFiberPpuContextRun
 * (0xABA1C563), cellFiberPpuContextFinalize (0xB3A48079) and
 * cellFiberPpuContextReturnToThread (0x01036193). ps3recomp v0.20 has no
 * handler for them, so the runtime faked CELL_OK and the fiber body (entry
 * 0x1637760, a PDI cooperative-thread loop) never ran. Names: RPCS3 ref log.
 * Guest call sites: 0xAF0254 (create + Initialize), 0xAF03B4 (Run), 0xAF0230
 * (ReturnToThread(0)).
 *
 * Semantics modelled:
 *   Initialize(ctx, entryOPD, arg, stack, stackSize, attr)
 *   Run(ctx, u32* cause, 0, 0): runs the fiber on the calling PPU thread until
 *       it calls ReturnToThread(cause) or its entry returns; *cause = cause.
 *       A later Run resumes after the ReturnToThread call.
 *   ReturnToThread(cause): fiber side, switches back into Run.
 *   Finalize(ctx): frees the host fiber.
 */
#include "ppu_context.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>

extern "C" {
void     vm_write32(uint64_t addr, uint32_t val);
uint32_t vm_read32(uint64_t addr);
void     ps3_hle_register_ctx(unsigned int nid, const char* name, void (*fn)(ppu_context*));
extern PPU_THREAD_LOCAL ppu_context* g_active_ctx;
extern void (*g_ppu_thread_entry_trampoline)(ppu_context*);
}

namespace {

constexpr unsigned HOST_STACK = 4u * 1024u * 1024u;
constexpr uint32_t STACK_PAD  = 0x100;

struct CFiber {
    CFiber*      next;
    uint32_t     ea, opd, stack, size;
    uint64_t     arg;
    void*        host;     /* host fiber */
    void*        back;     /* fiber of the Run caller */
    int          state;    /* 0 ready/suspended, 1 running, 2 done */
    uint32_t     cause;
    ppu_context  ctx;
};

CRITICAL_SECTION g_cs;
INIT_ONCE        g_once = INIT_ONCE_STATIC_INIT;
CFiber*          g_list;
thread_local CFiber* t_cur;

BOOL CALLBACK init_cs(PINIT_ONCE, PVOID, PVOID*) { InitializeCriticalSection(&g_cs); return TRUE; }
void ensure() { InitOnceExecuteOnce(&g_once, init_cs, nullptr, nullptr); }

bool logging() {
    static int on = -1;
    if (on < 0) { const char* e = getenv("GT6_CTXFIBER_LOG"); on = e ? 1 : 0; }
    return on != 0;
}

CFiber* find(uint32_t ea) {
    for (CFiber* f = g_list; f; f = f->next) if (f->ea == ea) return f;
    return nullptr;
}

VOID CALLBACK fiber_main(void* p)
{
    CFiber* f = (CFiber*)p;
    f->ctx.gpr[1] = ((uint64_t)f->stack + f->size - STACK_PAD) & ~0xFull;
    f->ctx.gpr[3] = f->arg;
    f->ctx.cia    = f->opd;
    if (g_ppu_thread_entry_trampoline) g_ppu_thread_entry_trampoline(&f->ctx);
    f->cause = (uint32_t)f->ctx.gpr[3];
    f->state = 2;
    if (logging()) fprintf(stderr, "[CTXFIBER] entry returned ctx=%08X r3=%u\n", f->ea, f->cause);
    for (;;) SwitchToFiber(f->back);   /* an ended fiber is never resumed */
}

void ret(ppu_context* c, int64_t v) { c->gpr[3] = (uint64_t)v; }

void h_attr_init(ppu_context* c) { ret(c, 0); }

void h_init(ppu_context* c)
{
    ensure();
    const uint32_t ea = (uint32_t)c->gpr[3];
    if (!ea || !c->gpr[4]) { ret(c, (int32_t)0x80760001); return; }   /* CELL_FIBER_ERROR_NULL_POINTER-ish */
    CFiber* f = (CFiber*)calloc(1, sizeof *f);
    f->ea = ea; f->opd = (uint32_t)c->gpr[4]; f->arg = c->gpr[5];
    f->stack = (uint32_t)c->gpr[6]; f->size = (uint32_t)c->gpr[7];
    ppu_context* parent = g_active_ctx ? g_active_ctx : c;
    f->ctx.gpr[13]   = parent->gpr[13];
    f->ctx.thread_id = parent->thread_id;
    f->host = CreateFiberEx(0, HOST_STACK, 0, fiber_main, f);
    EnterCriticalSection(&g_cs);
    f->next = g_list; g_list = f;
    LeaveCriticalSection(&g_cs);
    if (logging()) fprintf(stderr, "[CTXFIBER] init ctx=%08X opd=%08X arg=%llX stack=%08X size=%X tid=%u\n",
                           ea, f->opd, (unsigned long long)f->arg, f->stack, f->size, (unsigned)c->thread_id);
    ret(c, 0);
}

void h_run(ppu_context* c)
{
    ensure();
    const uint32_t ea = (uint32_t)c->gpr[3], cause_ea = (uint32_t)c->gpr[4];
    EnterCriticalSection(&g_cs);
    CFiber* f = find(ea);
    int st = f ? f->state : -1;
    if (f && st == 0) f->state = 1;
    LeaveCriticalSection(&g_cs);
    if (!f || st != 0) { ret(c, (int32_t)0x80760007); return; }   /* STAT */
    if (!IsThreadAFiber()) ConvertThreadToFiber(nullptr);
    f->back = GetCurrentFiber();
    /* The fiber runs on the caller's PPU thread: its TLS (r13) and thread id are the caller's. */
    f->ctx.gpr[13]   = c->gpr[13];
    f->ctx.thread_id = c->thread_id;
    ppu_context* saved = g_active_ctx;
    CFiber* saved_cur = t_cur;
    t_cur = f; g_active_ctx = &f->ctx;
    if (logging()) fprintf(stderr, "[CTXFIBER] run ctx=%08X tid=%u\n", ea, (unsigned)c->thread_id);
    const uint64_t r31_pre = c->gpr[31], r1_pre = c->gpr[1];
    const uint32_t sl_pre = vm_read32((uint32_t)c->gpr[1] + 0x9C);
    const uint32_t hd_pre = vm_read32((uint32_t)c->gpr[1] + 0xA0 + 0x74);
    if (logging() && hd_pre) fprintf(stderr, "[CTXFIBER] pre head=%08X [head]=%08X\n", hd_pre, vm_read32(hd_pre));
    SwitchToFiber(f->host);
    if (logging()) { uint32_t hd = vm_read32((uint32_t)c->gpr[1] + 0xA0 + 0x74);
        fprintf(stderr, "[CTXFIBER] head=%08X [head]=%08X [head+4]=%08X hd_pre=%08X\n", hd, hd ? vm_read32(hd) : 0, hd ? vm_read32(hd+4) : 0, hd_pre); }
    if (logging()) fprintf(stderr, "[CTXFIBER] caller r1=%llX r31 pre=%llX post=%llX r1post=%llX r31slot pre=%08X post=%08X\n",
        (unsigned long long)r1_pre, (unsigned long long)r31_pre, (unsigned long long)c->gpr[31],
        (unsigned long long)c->gpr[1], sl_pre, vm_read32((uint32_t)c->gpr[1] + 0x9C));
    g_active_ctx = saved; t_cur = saved_cur;
    if (f->state == 1) f->state = 0;           /* suspended by ReturnToThread: runnable again */
    if (cause_ea) vm_write32(cause_ea, f->cause);
    if (logging()) fprintf(stderr, "[CTXFIBER] back ctx=%08X cause=%u state=%d\n", ea, f->cause, f->state);
    ret(c, 0);
}

void h_return(ppu_context* c)
{
    CFiber* f = t_cur;
    if (!f) { ret(c, (int32_t)0x80760006); return; }   /* PERM */
    f->cause = (uint32_t)c->gpr[3];
    SwitchToFiber(f->back);                    /* resumes here on the next Run */
    ret(c, 0);
}

void h_fin(ppu_context* c)
{
    ensure();
    const uint32_t ea = (uint32_t)c->gpr[3];
    EnterCriticalSection(&g_cs);
    CFiber** pp = &g_list; CFiber* f = nullptr;
    for (; *pp; pp = &(*pp)->next) if ((*pp)->ea == ea) { f = *pp; *pp = f->next; break; }
    LeaveCriticalSection(&g_cs);
    if (f && f->state != 1) { if (f->host) DeleteFiber(f->host); free(f); }
    if (logging()) fprintf(stderr, "[CTXFIBER] fin ctx=%08X found=%d\n", ea, f ? 1 : 0);
    ret(c, 0);
}

} // namespace

extern "C" void gt6_ctxfiber_register(void)
{
    ps3_hle_register_ctx(0x31252EC3u, "_cellFiberPpuContextAttributeInitialize", h_attr_init);
    ps3_hle_register_ctx(0x72086315u, "cellFiberPpuContextInitialize", h_init);
    ps3_hle_register_ctx(0xABA1C563u, "cellFiberPpuContextRun", h_run);
    ps3_hle_register_ctx(0xB3A48079u, "cellFiberPpuContextFinalize", h_fin);
    ps3_hle_register_ctx(0x01036193u, "cellFiberPpuContextReturnToThread", h_return);
}
