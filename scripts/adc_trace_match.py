# Match [A40V] trace segments to ADC source functions. Run from repo root:
#   python -X utf8 scripts/adc_trace_match.py <from_ms> <run.log.err> <file.adc>...  (columns: ms task line n-candidates file:function)
import sys,re,glob,collections,subprocess,os
sys.path.insert(0,'tools'); import adch_disasm as A, io, contextlib
S=sys.argv[1]; log=sys.argv[2]; files=sys.argv[3:]
OPN=A.OPNAMES
funcs=collections.defaultdict(list)  # (adc,src,fn) -> [(line,op)]
for f in files:
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf):
        try: A.main(['x',f])
        except Exception as e: pass
    cur=None; stack=[]
    for ln in buf.getvalue().splitlines():
        m=re.match(r"(\s*)== \S+ (\S+): source='([^']*)'",ln)
        if m: cur=(os.path.basename(f),m.group(3),m.group(2),len(m.group(1))); continue
        m=re.match(r"(\s*)[0-9A-F]+\|\s*(\d+)\|\s*\d+\| (\w+)",ln)
        if m and cur:
            funcs[(cur[0],cur[1],cur[2],len(m.group(1)))].append((int(m.group(2)),m.group(3)))
bylo=collections.defaultdict(list)
for k,v in funcs.items():
    seg=None
    for l,o in v:
        if l and (not seg or seg[0]!=l): seg=[l,[]]; bylo[l].append((k,seg[1]))
        if l: seg[1].append(o)
rows=[r for r in open(log,encoding='latin-1') if '[A40V]' in r]
segs=[]
for r in rows:
    d=dict(x.split('=',1) for x in r.split()[1:] if '=' in x)
    if int(d['ms'])<int(S) : continue
    t=d['task'];l=int(d['line']);o=OPN[int(d['op'])]
    if segs and segs[-1][1]==t and segs[-1][2]==l: segs[-1][3].append(o)
    else: segs.append([d['ms'],t,l,[o]])
def sub(a,b):
    return any(b[i:i+len(a)]==a for i in range(len(b)-len(a)+1))
for ms,t,l,ops in segs:
    if not l: continue
    c=collections.Counter()
    for k,s in bylo.get(l,[]):
        if sub(ops,s): c[(k[1].split('/')[-1],k[2])]+=1
    print(ms,t[-4:],l,len(c),' '.join('%s:%s'%k for k in list(c)[:4]))
