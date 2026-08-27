import json
info=json.load(open('data/kanji_info.json',encoding='utf-8'))
rows=[]
for k,v in info.items():
    rows.append({'k':k,'freq':v['freq_mainichi_shinbun'],'grade':v['grade_src'],
                 'sc':v['stroke_count'],'on':v['on_readings'],'kun':v['kun_readings'],
                 'mean':v['meanings']})
rows.sort(key=lambda r:r['freq'])
for i,r in enumerate(rows,1): r['rank']=i
json.dump(rows, open('data/ordered.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
print("total",len(rows))
print("freq range", rows[0]['freq'], "->", rows[-1]['freq'])
print("top 30:", ''.join(r['k'] for r in rows[:30]))
print("bottom 15:", ''.join(r['k'] for r in rows[-15:]))
from collections import Counter
print("grade spread in first 100:", Counter(r['grade'] for r in rows[:100]))
