import json, urllib.request, urllib.parse, concurrent.futures, os, time

def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 (kanji-study-sheet)'})
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read().decode('utf-8'))
        except Exception as e:
            if i == tries-1: raise
            time.sleep(1.5*(i+1))

grades = {}
for g in (1,2,3):
    grades[g] = get(f"https://kanjiapi.dev/v1/kanji/grade-{g}")
    print(f"grade {g}: {len(grades[g])}")

all_k = [(k,g) for g in (1,2,3) for k in grades[g]]
print("total", len(all_k))

def fetch_one(item):
    k,g = item
    q = urllib.parse.quote(k)
    d = get(f"https://kanjiapi.dev/v1/kanji/{q}")
    d['grade_src'] = g
    return k, d

out = {}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
    for k, d in ex.map(fetch_one, all_k):
        out[k] = d

json.dump(out, open('data/kanji_info.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
print("saved", len(out))
missing_freq = [k for k,v in out.items() if not v.get('freq_mainichi_shinbun')]
print("no freq:", len(missing_freq), ''.join(missing_freq))
