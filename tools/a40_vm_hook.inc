// Arbeit40 script VM trace hook (env GT6_A40VM=<sec>). Paste before func_00AA41FC in gt6/generated/ppu_recomp_023.cpp
// and call a40_vm(ctx); right after label loc_00AA4374. Prints [A40V] records (task, opcode, line, string operand).
#include <time.h>
#include <string.h>
#include <stdlib.h>
extern "C" __declspec(dllimport) int __stdcall IsBadReadPtr(const void*, unsigned long long);
static void a40_str(uint32_t p, char* out){ out[0]=0; if(p<0x10000u||p>=0xE0000000u||IsBadReadPtr(vm_base+p,48)) return;
  const unsigned char* c=(const unsigned char*)(vm_base+p); int i=0; while(i<47&&c[i]>=32&&c[i]<127){out[i]=(char)c[i];i++;} out[i]=0; if(c[i]!=0&&i<47) out[0]=0; }
static void a40_vm(ppu_context* ctx){ PPU_MM_SNAP static int from=-2; if(from==-2){const char* e=getenv("GT6_A40VM"); from=e?atoi(e):-1;} if(from<0) return;
  long ms=(long)clock(); if(ms<from*1000L) return; static uint32_t seen[1<<20]; static long win=-1; static int n=0;
  uint32_t rec=(uint32_t)ctx->gpr[10], task=(uint32_t)ctx->gpr[8]; uint32_t h=(rec>>2)&((1u<<20)-1); long w=ms/30000; if(w!=win){memset(seen,0,sizeof seen); win=w;}
  if(seen[h]==rec||n>=600000) return; seen[h]=rec; n++;
  uint32_t w0=vm_read32(rec), w1=vm_read32(rec+4), w2=vm_read32(rec+8); char a[48],b[48],c[48]; a40_str(w1,a);
  b[0]=0; if(w1>=0x10000u&&w1<0xE0000000u&&!IsBadReadPtr(vm_base+w1,4)) a40_str(vm_read32(w1),b); a40_str(w2,c);
  fprintf(stderr,"[A40V] ms=%ld tid=%llu task=%08X rec=%08X op=%u line=%u w1=%08X w2=%08X s=%s|%s|%s\n",ms,(unsigned long long)ctx->thread_id,task,rec,w0>>24,w0&0xFFFFFF,w1,w2,a,b,c); }
