import json, urllib.request, urllib.parse, concurrent.futures, time
info = json.load(open('data/kanji_info.json',encoding='utf-8'))
def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 (kanji-study-sheet)'})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode('utf-8'))
        except Exception:
            if i == tries-1: raise
            time.sleep(2*(i+1))
def one(k):
    return k, get(f"https://kanjiapi.dev/v1/words/{urllib.parse.quote(k)}")
lex = {}   # written -> {reading: [glosses]}
prio = {}  # written+reading -> priority tags
bad=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
    futs={ex.submit(one,k):k for k in info}
    for f in concurrent.futures.as_completed(futs):
        try: k, words = f.result()
        except Exception as e: bad.append(futs[f]); continue
        for w in words:
            gl=[g for m in w.get('meanings',[]) for g in m.get('glosses',[])]
            for v in w.get('variants',[]):
                wr=v.get('written'); pr=v.get('pronounced')
                if not wr or not pr: continue
                lex.setdefault(wr,{}).setdefault(pr,[])
                for g in gl[:4]:
                    if g not in lex[wr][pr]: lex[wr][pr].append(g)
                if v.get('priorities'):
                    prio[wr+'|'+pr]=sorted(set(prio.get(wr+'|'+pr,[]))|set(v['priorities']))
json.dump(lex, open('data/lexicon.json','w',encoding='utf-8'), ensure_ascii=False, separators=(',',':'))
json.dump(prio, open('data/priorities.json','w',encoding='utf-8'), ensure_ascii=False, separators=(',',':'))
print("lex entries", len(lex), "prio", len(prio), "failed kanji", len(bad), ''.join(bad))
