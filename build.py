"""Build the kanji study document from the fetched data + authored content."""
import json, glob, os, html, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

ordered = json.load(open('data/ordered.json', encoding='utf-8'))
strokes = json.load(open('data/strokes.json', encoding='utf-8'))
comps = json.load(open('data/components.json', encoding='utf-8'))

content = {}
for f in sorted(glob.glob('content/b*.json')):
    content.update(json.load(open(f, encoding='utf-8')))

missing = [r['k'] for r in ordered if r['k'] not in content]
print('kanji ordered: %d   authored: %d   missing: %d' % (len(ordered), len(content), len(missing)))
if missing:
    print('  missing: ' + ''.join(missing))
    if '--allow-missing' not in sys.argv:
        sys.exit('refusing to build with missing content (pass --allow-missing to override)')

E = html.escape

def reading_spans(rs, cls):
    out = []
    for r in rs:
        r = r.strip()
        if not r:
            continue
        if '.' in r:
            base, oku = r.split('.', 1)
            out.append('<span class="rd %s">%s<i>%s</i></span>' % (cls, E(base), E(oku)))
        else:
            out.append('<span class="rd %s">%s</span>' % (cls, E(r.replace('-', ''))))
    return ''.join(out)

GRADE_NAME = {1: '1st grade', 2: '2nd grade', 3: '3rd grade'}

PAGE_SIZE = 10  # kanji per page — keeps each page light to load

entries = []  # one entry per authored kanji, in rank order

for r in ordered:
    k = r['k']
    if k not in content:
        continue
    c = content[k]
    rank = r['rank']
    st = strokes[k]
    comp = [x for x in comps[k]['comp'] if x != k][:6]
    rad = comps[k]['rad']

    words = []
    for w in c['w']:
        words.append(
            '<li class="word">'
            '<div class="wtop"><span class="wjp">%s</span>'
            '<span class="wrd">%s</span>'
            '<span class="wen">%s</span></div>'
            '<div class="wex"><span class="exjp">%s</span>'
            '<span class="exen">%s</span></div>'
            '</li>' % (E(w['w']), E(w['r']), E(w['e']), E(w['s']), E(w['t']))
        )

    meta = []
    meta.append('<span class="chip">#%d most common</span>' % rank)
    meta.append('<span class="chip">%s</span>' % GRADE_NAME.get(r['grade'], ''))
    meta.append('<span class="chip">%d strokes</span>' % r['sc'])
    if rad:
        meta.append('<span class="chip">radical %s</span>' % E(rad))
    if comp:
        meta.append('<span class="chip parts">parts %s</span>' % E(' '.join(comp)))

    on = reading_spans(r['on'], 'on')
    kun = reading_spans(r['kun'], 'kun')

    card_html = ("""
<section class="card" id="k%d" data-k="%s" data-rank="%d" data-search="%s">
  <div class="hero">
    <div class="glyphbox"><div class="glyph">%s</div><div class="rank">%d</div></div>
    <div class="heroinfo">
      <h2>%s</h2>
      <div class="meta">%s</div>
      <div class="readings">
        <div class="rrow"><span class="rlab">ON</span><div class="rvals">%s</div></div>
        <div class="rrow"><span class="rlab">KUN</span><div class="rvals">%s</div></div>
      </div>
    </div>
  </div>

  <div class="section">
    <h3>How to remember it</h3>
    <p class="mn">%s</p>
  </div>

  <div class="section">
    <h3>Stroke order <span class="hint">%d strokes — grey shows what you have already drawn</span></h3>
    <div class="strokes" data-for="%s"></div>
  </div>

  <div class="section">
    <h3>Words to know</h3>
    <ol class="words">%s</ol>
  </div>

  <div class="section practice">
    <h3>Write it</h3>
    <div class="tracerow">%s%s</div>
  </div>
</section>""" % (
        rank, E(k), rank,
        E(k + ' ' + c['kw'] + ' ' + ' '.join(x['w'] + x['r'] + x['e'] for x in c['w'])).lower(),
        E(k), rank,
        E(c['kw']), ''.join(meta), on or '<span class="none">—</span>', kun or '<span class="none">—</span>',
        E(c['mn']),
        len(st['s']), E(k),
        ''.join(words),
        '<div class="tracebox trace">%s</div>' % E(k) * 1,
        '<div class="tracebox"></div>' * 5,
    ))

    entries.append({'k': k, 'rank': rank, 'kw': c['kw'], 'card': card_html})

# Pagination is derived purely from the number of authored entries at build
# time (not hand-assigned), so page boundaries always match whatever content
# currently exists, independent of how the build happened to run.
total_pages = max(1, (len(entries) + PAGE_SIZE - 1) // PAGE_SIZE)


def page_num(i):
    return i // PAGE_SIZE + 1


def page_file(n):
    return 'kanji.html' if n == 1 else 'kanji-%d.html' % n


for i, e in enumerate(entries):
    e['page'] = page_num(i)

# Lightweight global index: every kanji, linking straight to the page (and
# in-page anchor) that will actually contain it once split up.
index_cells = [
    '<a class="icell" href="%s#k%d" title="%s"><span class="ik">%s</span><span class="in">%d</span></a>'
    % (page_file(e['page']), e['rank'], E(e['kw']), E(e['k']), e['rank'])
    for e in entries
]

pages = [entries[i:i + PAGE_SIZE] for i in range(0, len(entries), PAGE_SIZE)]


def pager_html(n):
    if n > 1:
        prev = '<a class="btn pnav" href="%s">&larr; Prev</a>' % page_file(n - 1)
    else:
        prev = '<span class="btn pnav" aria-disabled="true">&larr; Prev</span>'
    if n < total_pages:
        nxt = '<a class="btn pnav" href="%s">Next &rarr;</a>' % page_file(n + 1)
    else:
        nxt = '<span class="btn pnav" aria-disabled="true">Next &rarr;</span>'
    return ('<nav class="pager noprint">%s<span class="pageinfo">Page %d of %d</span>%s</nav>'
            % (prev, n, total_pages, nxt))


CSS = """
:root{
  --bg:#faf8f5; --panel:#ffffff; --ink:#1c1a17; --muted:#6b6560; --line:#e6e0d8;
  --accent:#b4472e; --accent-soft:#fdf0ec; --on:#2f6f8f; --kun:#8a5a2b; --grey:#c9c2b8;
  --shadow:0 1px 2px rgba(0,0,0,.05),0 8px 24px -12px rgba(0,0,0,.15);
  --jp:"Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic",YuGothic,"Noto Sans JP","Meiryo",sans-serif;
  --ui:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
}
:root:not([data-theme="light"]){}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --bg:#14130f; --panel:#1d1b17; --ink:#ece7df; --muted:#a49c92; --line:#2f2c26;
    --accent:#e4795c; --accent-soft:#2a1d18; --on:#7fb8d4; --kun:#d3a172; --grey:#4a453d;
    --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px -12px rgba(0,0,0,.6);
  }
}
:root[data-theme="dark"]{
  --bg:#14130f; --panel:#1d1b17; --ink:#ece7df; --muted:#a49c92; --line:#2f2c26;
  --accent:#e4795c; --accent-soft:#2a1d18; --on:#7fb8d4; --kun:#d3a172; --grey:#4a453d;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px -12px rgba(0,0,0,.6);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--ui);
  font-size:16px;line-height:1.55;-webkit-text-size-adjust:100%;}
.wrap{max-width:820px;margin:0 auto;padding:0 16px 96px}

/* top bar */
.bar{position:sticky;top:0;z-index:50;background:color-mix(in srgb,var(--bg) 88%, transparent);
  backdrop-filter:blur(12px);border-bottom:1px solid var(--line);padding:10px 0;margin-bottom:8px}
.barin{max-width:820px;margin:0 auto;padding:0 16px;display:flex;gap:8px;align-items:center}
.barin input{flex:1;min-width:0;font:inherit;font-size:15px;padding:9px 12px;border-radius:10px;
  border:1px solid var(--line);background:var(--panel);color:var(--ink)}
.barin input::placeholder{color:var(--muted)}
.btn{font:inherit;font-size:14px;padding:9px 11px;border-radius:10px;border:1px solid var(--line);
  background:var(--panel);color:var(--ink);cursor:pointer;white-space:nowrap}
.btn:hover{border-color:var(--accent);color:var(--accent)}
.btn[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}

header.top{padding:40px 0 8px}
header.top h1{font-size:1.6rem;margin:0 0 6px;letter-spacing:-.02em}
header.top p{color:var(--muted);margin:0 0 4px;font-size:.95rem}

/* index */
.indexwrap{margin:20px 0 8px;border:1px solid var(--line);border-radius:14px;background:var(--panel);
  box-shadow:var(--shadow);overflow:hidden}
.indexwrap summary{padding:14px 16px;cursor:pointer;font-weight:600;font-size:.95rem}
.index{display:grid;grid-template-columns:repeat(auto-fill,minmax(58px,1fr));gap:6px;padding:0 14px 16px}
.icell{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1px;
  padding:7px 2px;border:1px solid var(--line);border-radius:9px;text-decoration:none;color:var(--ink);
  background:var(--bg)}
.icell:hover{border-color:var(--accent);background:var(--accent-soft)}
.ik{font-family:var(--jp);font-size:1.35rem;line-height:1.1}
.in{font-size:.62rem;color:var(--muted);font-variant-numeric:tabular-nums}

/* pager */
.pager{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:18px 0}
.pageinfo{font-size:.82rem;color:var(--muted);font-variant-numeric:tabular-nums}
.pnav[aria-disabled="true"]{opacity:.4;pointer-events:none}

/* card */
.card{background:var(--panel);border:1px solid var(--line);border-radius:16px;
  box-shadow:var(--shadow);padding:22px;margin:18px 0;scroll-margin-top:74px}
.hero{display:flex;gap:20px;align-items:flex-start}
.glyphbox{position:relative;flex:0 0 auto}
.glyph{font-family:var(--jp);font-size:104px;line-height:1;padding:6px 10px;
  border:2px dashed var(--line);border-radius:12px;min-width:132px;text-align:center}
.rank{position:absolute;top:-9px;left:-9px;background:var(--accent);color:#fff;font-size:.68rem;
  font-weight:700;padding:2px 7px;border-radius:999px;font-variant-numeric:tabular-nums}
.heroinfo{min-width:0;flex:1}
.heroinfo h2{margin:2px 0 8px;font-size:1.5rem;letter-spacing:-.01em;line-height:1.2}
.meta{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:12px}
.chip{font-size:.7rem;color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:2px 8px}
.chip.parts{font-family:var(--jp)}
.readings{display:flex;flex-direction:column;gap:5px}
.rrow{display:flex;gap:9px;align-items:baseline}
.rlab{font-size:.62rem;font-weight:700;letter-spacing:.09em;color:var(--muted);flex:0 0 26px;padding-top:2px}
.rvals{display:flex;flex-wrap:wrap;gap:5px}
.rd{font-family:var(--jp);font-size:1rem;padding:1px 8px;border-radius:7px;background:var(--bg);
  border:1px solid var(--line)}
.rd i{font-style:normal;opacity:.5}
.rd.on{color:var(--on)} .rd.kun{color:var(--kun)}
.none{color:var(--muted)}

.section{margin-top:22px;padding-top:18px;border-top:1px solid var(--line)}
.section h3{font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);
  margin:0 0 10px;font-weight:700}
.hint{text-transform:none;letter-spacing:0;font-weight:400;opacity:.8}
.mn{margin:0;font-size:1rem;line-height:1.65}

/* strokes */
.strokes{display:flex;flex-wrap:wrap;gap:6px}
.frame{width:56px;height:56px;border:1px solid var(--line);border-radius:8px;background:var(--bg);flex:0 0 auto}
.frame.full{border-color:var(--accent);background:var(--accent-soft);width:112px;height:112px;
  margin-right:4px}
.frame svg{display:block;width:100%;height:100%}

/* words */
.words{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:14px}
.word{padding-left:13px;border-left:3px solid var(--line)}
.word:hover{border-left-color:var(--accent)}
.wtop{display:flex;flex-wrap:wrap;gap:5px 10px;align-items:baseline}
.wjp{font-family:var(--jp);font-size:1.28rem;font-weight:600}
.wrd{font-family:var(--jp);font-size:.9rem;color:var(--accent)}
.wen{font-size:.9rem;color:var(--muted)}
.wex{margin-top:3px;display:flex;flex-direction:column;gap:1px}
.exjp{font-family:var(--jp);font-size:1rem}
.exen{font-size:.85rem;color:var(--muted)}

/* practice */
.tracerow{display:flex;gap:8px;flex-wrap:wrap}
.tracebox{width:58px;height:58px;border:1px solid var(--line);border-radius:8px;background:
  linear-gradient(var(--line),var(--line)) center/100% 1px no-repeat,
  linear-gradient(var(--line),var(--line)) center/1px 100% no-repeat,var(--bg);
  background-blend-mode:normal;display:flex;align-items:center;justify-content:center;
  font-family:var(--jp);font-size:44px;line-height:1;color:transparent}
.tracebox.trace{color:var(--grey)}

/* practice mode: hide the answer */
body.quiz .glyph{color:transparent}
body.quiz .glyphbox::after{content:"?";position:absolute;inset:0;display:flex;align-items:center;
  justify-content:center;font-size:56px;color:var(--line);pointer-events:none}
body.quiz .strokes,body.quiz .tracebox.trace{opacity:0}
body.quiz .card:hover .glyph{color:var(--ink)}
body.quiz .card:hover .glyphbox::after{content:""}
body.quiz .card:hover .strokes,body.quiz .card:hover .tracebox.trace{opacity:1}

.hidden{display:none !important}
.empty{padding:40px 0;text-align:center;color:var(--muted)}
footer{color:var(--muted);font-size:.8rem;padding:30px 0;text-align:center;border-top:1px solid var(--line);margin-top:30px}

@media (max-width:560px){
  .wrap{padding:0 11px 80px}
  .card{padding:16px;border-radius:14px}
  .hero{gap:13px}
  .glyph{font-size:74px;min-width:98px;padding:4px 7px}
  .heroinfo h2{font-size:1.24rem}
  .frame,.tracebox{width:50px;height:50px}
  .frame.full{width:104px;height:104px}
  .tracebox{font-size:38px}
  .barin{padding:0 11px}
  .index{grid-template-columns:repeat(auto-fill,minmax(50px,1fr))}
}

@media print{
  .bar,.indexwrap,header.top,footer,.noprint{display:none !important}
  body{background:#fff;font-size:11pt}
  .wrap{max-width:none;padding:0}
  .card{break-inside:avoid;page-break-after:always;break-after:page;box-shadow:none;
    border:none;padding:0;margin:0}
  .section{break-inside:avoid}
  .glyph{border-color:#ccc}
}
"""

JS_TEMPLATE = """
const S = %s;

function svgFrame(paths, upto, hi, nums){
  const NS='http://www.w3.org/2000/svg';
  const svg=document.createElementNS(NS,'svg');
  svg.setAttribute('viewBox','0 0 109 109');
  for(let i=0;i<upto;i++){
    const p=document.createElementNS(NS,'path');
    p.setAttribute('d',paths[i]);
    p.setAttribute('fill','none');
    p.setAttribute('stroke-linecap','round');
    p.setAttribute('stroke-linejoin','round');
    const isHi = (i===hi);
    p.setAttribute('stroke', isHi ? 'var(--accent)' : 'var(--grey)');
    p.setAttribute('stroke-width', isHi ? '5.5' : '4');
    svg.appendChild(p);
  }
  if(nums){
    for(const [x,y,n] of nums){
      const t=document.createElementNS(NS,'text');
      t.setAttribute('x',x); t.setAttribute('y',y);
      t.setAttribute('font-size','8.5'); t.setAttribute('fill','var(--accent)');
      t.setAttribute('font-family','sans-serif'); t.setAttribute('font-weight','700');
      t.setAttribute('stroke','var(--panel)'); t.setAttribute('stroke-width','2.2');
      t.setAttribute('paint-order','stroke fill');
      t.textContent=n;
      svg.appendChild(t);
    }
  }
  return svg;
}

function renderStrokes(box){
  if(box.dataset.done) return;
  box.dataset.done='1';
  const k=box.dataset.for, d=S[k];
  if(!d) return;
  const full=document.createElement('div');
  full.className='frame full';
  full.appendChild(svgFrame(d.s, d.s.length, -1, d.n));
  box.appendChild(full);
  for(let i=1;i<=d.s.length;i++){
    const f=document.createElement('div');
    f.className='frame';
    f.appendChild(svgFrame(d.s, i, i-1, null));
    box.appendChild(f);
  }
}

const io=new IntersectionObserver((es)=>{
  for(const e of es) if(e.isIntersecting){ renderStrokes(e.target); io.unobserve(e.target); }
},{rootMargin:'600px 0px'});
document.querySelectorAll('.strokes').forEach(b=>io.observe(b));

function renderAll(){ document.querySelectorAll('.strokes').forEach(renderStrokes); }
window.addEventListener('beforeprint', renderAll);

// search
const q=document.getElementById('q'), cards=[...document.querySelectorAll('.card')];
const empty=document.getElementById('empty');
q.addEventListener('input',()=>{
  const v=q.value.trim().toLowerCase();
  let n=0;
  for(const c of cards){
    const hit = !v || c.dataset.search.includes(v) || c.dataset.k===v || c.dataset.rank===v;
    c.classList.toggle('hidden',!hit);
    if(hit){ n++; if(v) renderStrokes(c.querySelector('.strokes')); }
  }
  empty.classList.toggle('hidden', n>0);
  document.getElementById('idx').classList.toggle('hidden', !!v);
});

// theme
const tb=document.getElementById('theme');
try{ const saved=localStorage.getItem('kanji-theme'); if(saved) document.documentElement.dataset.theme=saved; }catch(e){}
tb.addEventListener('click',()=>{
  const cur=document.documentElement.dataset.theme
    || (matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
  const next = cur==='dark'?'light':'dark';
  document.documentElement.dataset.theme=next;
  try{ localStorage.setItem('kanji-theme',next); }catch(e){}
});

// quiz mode
const qb=document.getElementById('quiz');
qb.addEventListener('click',()=>{
  const on=document.body.classList.toggle('quiz');
  qb.setAttribute('aria-pressed', on?'true':'false');
  try{ localStorage.setItem('kanji-quiz', on?'1':''); }catch(e){}
});
try{ if(localStorage.getItem('kanji-quiz')){ document.body.classList.add('quiz'); qb.setAttribute('aria-pressed','true'); } }catch(e){}
"""

BODY_TEMPLATE = """
<div class="bar">
  <div class="barin">
    <input id="q" type="search" placeholder="Search kanji, reading, meaning or number…" autocomplete="off">
    <button class="btn" id="quiz" aria-pressed="false" title="Hide the kanji so you can practise writing it from the meaning">Quiz</button>
    <button class="btn" id="theme" title="Light / dark">◐</button>
  </div>
</div>

<div class="wrap">
  <header class="top">
    <h1>Kanji through 3rd grade — %d characters</h1>
    <p>Every kanji Japanese children learn in elementary school years 1&ndash;3, ordered from
       most to least common in real newspaper text. Split into pages of %d so each page stays
       light to load — this is page %d of %d, kanji #%d&ndash;#%d.</p>
    <p class="noprint" style="font-size:.85rem">Tap <b>Quiz</b> to hide the kanji and its stroke order &mdash;
       the meaning and readings stay visible, so you can practise writing it from memory.
       Hover or tap a card to reveal. Print this page to get a PDF, one kanji per sheet.</p>
  </header>

  <details class="indexwrap" id="idx">
    <summary>All %d kanji &mdash; jump to one</summary>
    <div class="index">%s</div>
  </details>

  %s

  <div id="empty" class="empty hidden">Nothing matches that search.</div>

  %s

  %s

  <footer>
    Frequency ranking from the Mainichi Shinbun corpus (KANJIDIC).
    Stroke order data from KanjiVG (CC BY-SA 3.0). Word readings checked against JMdict.
  </footer>
</div>
"""

TITLE = 'Kanji to 3rd Grade'

index_html = ''.join(index_cells)


def render_page(page_entries, n):
    stroke_data = json.dumps({e['k']: strokes[e['k']] for e in page_entries},
                              ensure_ascii=False, separators=(',', ':'))
    js = JS_TEMPLATE % stroke_data
    pager = pager_html(n)
    body = BODY_TEMPLATE % (
        len(ordered), PAGE_SIZE, n, total_pages,
        page_entries[0]['rank'], page_entries[-1]['rank'],
        len(entries), index_html,
        pager, ''.join(e['card'] for e in page_entries), pager,
    )
    title = TITLE if total_pages == 1 else '%s — page %d/%d' % (TITLE, n, total_pages)
    return title, body, js


def full_doc(title, body, js):
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            '<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n%s\n<script>%s</script>\n</body>\n</html>\n'
            % (title, CSS, body, js))


written = []
for n, page_entries in enumerate(pages, start=1):
    title, body, js = render_page(page_entries, n)
    fname = page_file(n)
    open(fname, 'w', encoding='utf-8').write(full_doc(title, body, js))
    written.append(fname)

print('wrote %d page(s): %s' % (len(written), ', '.join(written)))
print('kanji.html  %.2f MB' % (os.path.getsize('kanji.html') / 1048576))

# artifact variant of page 1: no doctype/html/head/body wrapper
title1, body1, js1 = render_page(pages[0], 1)
art = '<title>%s</title>\n<style>%s</style>\n%s\n<script>%s</script>\n' % (title1, CSS, body1, js1)
open('artifact.html', 'w', encoding='utf-8').write(art)
print('wrote artifact.html %.2f MB' % (os.path.getsize('artifact.html') / 1048576))
