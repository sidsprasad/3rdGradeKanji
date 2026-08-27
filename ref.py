import json,sys
rows=json.load(open('data/ordered.json',encoding='utf-8'))
comp=json.load(open('data/components.json',encoding='utf-8'))
a,b=int(sys.argv[1]),int(sys.argv[2])
for r in rows[a-1:b]:
    c=comp[r['k']]
    on='/'.join(r['on'][:5]) or '-'
    kun='/'.join(r['kun'][:6]) or '-'
    print(f"{r['rank']}\t{r['k']}\tf{r['freq']} g{r['grade']} {r['sc']}str\tON:{on}\tKUN:{kun}\tEN:{','.join(r['mean'][:4])}\tCOMP:{''.join(c['comp'][:6]) or '-'}")
