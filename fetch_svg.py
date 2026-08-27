import json, re, urllib.request, concurrent.futures, time

info = json.load(open('data/kanji_info.json',encoding='utf-8'))
kanji = list(info.keys())

def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 (kanji-study-sheet)'})
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.read().decode('utf-8')
        except Exception:
            if i == tries-1: raise
            time.sleep(1.5*(i+1))

def one(k):
    code = format(ord(k), '05x')
    svg = get(f"https://raw.githubusercontent.com/KanjiVG/kanjivg/master/kanji/{code}.svg")
    # stroke paths, in document order
    paths = re.findall(r'<path id="kvg:[^"]*-s(\d+)"[^>]*\sd="([^"]+)"', svg)
    paths.sort(key=lambda p: int(p[0]))
    ds = [p[1] for p in paths]
    # stroke number label positions
    nums = re.findall(r'<text transform="matrix\([^)]*?\s([\d.]+)\s+([\d.]+)\)">(\d+)</text>', svg)
    labels = [[float(x), float(y), int(n)] for x,y,n in nums]
    labels.sort(key=lambda t: t[2])
    return k, ds, labels

out = {}
bad = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
    futs = {ex.submit(one,k): k for k in kanji}
    for f in concurrent.futures.as_completed(futs):
        try:
            k, ds, labels = f.result()
            out[k] = {'s': ds, 'n': labels}
        except Exception as e:
            bad.append((futs[f], str(e)[:60]))

print("ok", len(out), "bad", len(bad), bad[:5])
mismatch = [(k, len(v['s']), info[k]['stroke_count']) for k,v in out.items() if len(v['s']) != info[k]['stroke_count']]
print("stroke count mismatches vs kanjidic:", len(mismatch), mismatch[:10])
nolabel = [k for k,v in out.items() if len(v['n']) != len(v['s'])]
print("label mismatches:", len(nolabel), ''.join(nolabel[:20]))
json.dump(out, open('data/strokes.json','w',encoding='utf-8'), ensure_ascii=False, separators=(',',':'))
import os; print("size KB", round(os.path.getsize('data/strokes.json')/1024))
