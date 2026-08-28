"""Build the compact printable sheet: 440 kanji, 5 per A4 page, static SVG stroke order."""
import json, glob, os, html

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

ordered = json.load(open('data/ordered.json', encoding='utf-8'))
strokes = json.load(open('data/strokes.json', encoding='utf-8'))
comps = json.load(open('data/components.json', encoding='utf-8'))

content = {}
for f in sorted(glob.glob('content/b*.json')):
    content.update(json.load(open(f, encoding='utf-8')))

E = html.escape
PER_PAGE = 5
WORDS_ON_SHEET = 3
TRACE_BOXES = 6


def clean_reading(rs, limit):
    """Bare kana, de-duplicated across KANJIDIC's differing okurigana splits."""
    out, seen = [], set()
    for r in rs:
        r = r.strip().replace('-', '')
        if not r:
            continue
        key = r.replace('.', '')
        if key in seen:
            continue
        seen.add(key)
        out.append(r.replace('.', '・'))   # katakana middle dot marks the okurigana split
        if len(out) >= limit:
            break
    return '　'.join(out)


def stroke_svg(k):
    """One numbered diagram: grey strokes, black numbers haloed so they survive B/W printing."""
    d = strokes[k]
    parts = ['<svg class="so" viewBox="0 0 109 109" xmlns="http://www.w3.org/2000/svg">']
    for p in d['s']:
        parts.append('<path d="%s" fill="none" stroke="#9aa0a6" stroke-width="4.2" '
                     'stroke-linecap="round" stroke-linejoin="round"/>' % p)
    for x, y, n in d['n']:
        parts.append('<text x="%s" y="%s" font-size="10" font-family="Helvetica,Arial,sans-serif" '
                     'font-weight="700" fill="#111" stroke="#fff" stroke-width="2.6" '
                     'paint-order="stroke fill">%d</text>' % (x, y, n))
    parts.append('</svg>')
    return ''.join(parts)


GRADE = {1: 'G1', 2: 'G2', 3: 'G3'}

entries = []
for r in ordered:
    k = r['k']
    c = content[k]
    ws = ''.join(
        '<div class="w"><span class="wj">%s</span><span class="wr">%s</span>'
        '<span class="we">%s</span></div>' % (E(w['w']), E(w['r']), E(w['e']))
        for w in c['w'][:WORDS_ON_SHEET])

    entries.append("""<div class="e">
  <div class="cellcol">
    <div class="gl">%s</div>
    <div class="sobox">%s</div>
  </div>
  <div class="info">
    <div class="ln1"><span class="kw">%s</span><span class="tag">#%d</span>
      <span class="tag">%s</span><span class="tag">%s</span></div>
    <div class="rl"><b>ON</b> %s &nbsp;<b>KUN</b> %s</div>
    <div class="mn">%s</div>
    <div class="ws">%s</div>
  </div>
  <div class="tr">%s</div>
</div>""" % (
        E(k), stroke_svg(k),
        E(c['kw']), r['rank'], GRADE.get(r['grade'], ''),
        '1 stroke' if r['sc'] == 1 else '%d strokes' % r['sc'],
        E(clean_reading(r['on'], 3)) or '—',
        E(clean_reading(r['kun'], 3)) or '—',
        E(c['mn']),
        ws,
        '<div class="tb"></div>' * TRACE_BOXES,
    ))

# group into pages so a kanji can never be split across a page break
pages = []
for i in range(0, len(entries), PER_PAGE):
    pages.append('<div class="page">%s</div>' % ''.join(entries[i:i + PER_PAGE]))

# front index: every kanji with its rank, so the sheet doubles as a checklist
idx = ''.join('<span class="ic"><b>%s</b>%d</span>' % (E(r['k']), r['rank']) for r in ordered)
index_page = ('<div class="page idxpage"><h1>Kanji through 3rd grade</h1>'
              '<p class="sub">All %d kanji taught in Japanese elementary school years 1&ndash;3, '
              'ordered by how often they appear in newspaper text &mdash; most common first. '
              'Numbers on each diagram give the stroke order. Tick them off as you learn to write them.</p>'
              '<div class="idx">%s</div></div>' % (len(ordered), idx))

CSS = """
@page{size:A4;margin:9mm 8mm}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{font-family:"IBM Plex Sans","Segoe UI",Helvetica,Arial,sans-serif;color:#111;background:#fff;
  font-size:8pt;line-height:1.34;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.jp,.gl,.wj,.rl,.ic b{font-family:"Yu Mincho","Hiragino Mincho ProN","MS Mincho",
  "Yu Gothic","Hiragino Sans",serif}

.page{page-break-after:always;break-after:page;height:279mm;display:flex;flex-direction:column}
.page:last-child{page-break-after:auto;break-after:auto}

/* one kanji */
.e{flex:1 1 0;display:flex;gap:3.5mm;align-items:stretch;
   border-bottom:.4pt solid #bbb;padding:2mm 0;min-height:0}
.e:last-child{border-bottom:0}

.cellcol{display:flex;gap:2mm;flex:0 0 auto;align-items:flex-start}
.gl{width:20mm;height:20mm;flex:0 0 auto;display:flex;align-items:center;justify-content:center;
  font-size:15mm;line-height:1;border:.5pt solid #333;
  background:linear-gradient(#ddd,#ddd) center/100% .3pt no-repeat,
             linear-gradient(#ddd,#ddd) center/.3pt 100% no-repeat}
.sobox{width:20mm;height:20mm;flex:0 0 auto;border:.4pt solid #ccc}
.so{display:block;width:100%;height:100%}

.info{flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:.7mm}
.ln1{display:flex;align-items:baseline;gap:1.6mm;flex-wrap:wrap}
.kw{font-size:10.5pt;font-weight:600;line-height:1.15}
.tag{font-size:6pt;color:#666;border:.4pt solid #ccc;border-radius:1pt;padding:0 1.1mm;
  white-space:nowrap;font-variant-numeric:tabular-nums}
.rl{font-size:8pt;color:#222}
.rl b{font-size:5.8pt;color:#888;font-weight:700;letter-spacing:.04em;
  font-family:"IBM Plex Sans","Segoe UI",Helvetica,Arial,sans-serif}
.mn{font-size:6.9pt;color:#444;line-height:1.32}
.ws{display:flex;flex-direction:column;gap:.15mm;margin-top:.4mm}
.w{display:flex;gap:1.6mm;align-items:baseline;font-size:7.4pt}
.wj{font-size:9pt;font-weight:600;flex:0 0 auto}
.wr{color:#777;flex:0 0 auto}
.we{color:#333;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}

/* practice cells */
.tr{flex:0 0 auto;display:flex;flex-direction:column;gap:1mm;justify-content:flex-start}
.tb{width:13mm;height:13mm;border:.4pt solid #999;
  background:linear-gradient(#e2e2e2,#e2e2e2) center/100% .3pt no-repeat,
             linear-gradient(#e2e2e2,#e2e2e2) center/.3pt 100% no-repeat}

/* the trace cells run as a horizontal strip, not a column */
.tr{flex-direction:row;align-items:flex-start}

/* front index */
.idxpage{display:block}
.idxpage h1{font-size:16pt;margin:0 0 2mm;font-weight:600}
.sub{font-size:8.5pt;color:#555;margin:0 0 5mm;max-width:150mm;line-height:1.45}
.idx{display:grid;grid-template-columns:repeat(16,1fr);gap:0;
  border-top:.4pt solid #ccc;border-left:.4pt solid #ccc}
.ic{display:flex;flex-direction:column;align-items:center;justify-content:center;
  padding:1.1mm 0;border-right:.4pt solid #ccc;border-bottom:.4pt solid #ccc;
  font-size:5.4pt;color:#888;font-variant-numeric:tabular-nums}
.ic b{font-size:10pt;color:#111;font-weight:400;line-height:1.1}
"""

doc = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
       '<title>Kanji through 3rd grade &mdash; practice sheets</title>\n'
       '<style>%s</style>\n</head>\n<body>\n%s\n%s\n</body>\n</html>\n'
       % (CSS, index_page, ''.join(pages)))

open('kanji-print.html', 'w', encoding='utf-8').write(doc)
print('wrote kanji-print.html  entries=%d  pages=%d (+1 index)  %.0f KB'
      % (len(entries), len(pages), os.path.getsize('kanji-print.html') / 1024))
