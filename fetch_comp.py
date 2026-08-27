import json, re, urllib.request, concurrent.futures, time, os
info=json.load(open('data/kanji_info.json',encoding='utf-8'))
os.makedirs('data/svg',exist_ok=True)
def get(url,tries=4):
    for i in range(tries):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (kanji-study-sheet)'})
            with urllib.request.urlopen(req,timeout=25) as r: return r.read().decode('utf-8')
        except Exception:
            if i==tries-1: raise
            time.sleep(1.5*(i+1))
def one(k):
    code=format(ord(k),'05x')
    p=f'data/svg/{code}.svg'
    if os.path.exists(p): svg=open(p,encoding='utf-8').read()
    else:
        svg=get(f"https://raw.githubusercontent.com/KanjiVG/kanjivg/master/kanji/{code}.svg")
        open(p,'w',encoding='utf-8').write(svg)
    # top-level element groups = direct components
    els=re.findall(r'<g id="kvg:[0-9a-f]+-g\d+"[^>]*kvg:element="([^"]+)"',svg)
    rad=re.search(r'kvg:element="([^"]+)"[^>]*kvg:radical="general"',svg)
    rad2=re.search(r'kvg:radical="general"[^>]*',svg)
    comps=[]
    for e in els:
        if e!=k and e not in comps: comps.append(e)
    return k, comps, (rad.group(1) if rad else None)
out={}
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
    for k,c,r in ex.map(one, list(info)):
        out[k]={'comp':c,'rad':r}
json.dump(out,open('data/components.json','w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
print("ok",len(out))
for k in ['日','明','時','語','親','聞']:
    print(k, out[k])
