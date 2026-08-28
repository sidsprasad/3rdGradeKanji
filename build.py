"""Build the interactive kanji study document (one kanji per screen, with a pager)."""
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
if missing and '--allow-missing' not in sys.argv:
    sys.exit('refusing to build with missing content')

E = html.escape
MAX_READINGS = 8


def reading_spans(rs, cls):
    out, seen = [], set()
    for r in rs:
        r = r.strip().replace('-', '')
        if not r:
            continue
        # KANJIDIC lists one reading under several okurigana splits
        # (う.まれる and うま.れる are both うまれる) - key on the bare kana
        key = r.replace('.', '')
        if key in seen:
            continue
        seen.add(key)
        if '.' in r:
            base, oku = r.split('.', 1)
            out.append('<span class="rd %s">%s<i>%s</i></span>' % (cls, E(base), E(oku)))
        else:
            out.append('<span class="rd %s">%s</span>' % (cls, E(r)))
    extra = len(out) - MAX_READINGS
    if extra > 0:
        out = out[:MAX_READINGS] + ['<span class="rd more">+%d rarer</span>' % extra]
    return ''.join(out)


GRADE_NAME = {1: '1st grade', 2: '2nd grade', 3: '3rd grade'}

cards, index_cells = [], []

for r in ordered:
    k = r['k']
    if k not in content:
        continue
    c = content[k]
    rank = r['rank']
    st = strokes[k]
    comp = [x for x in comps[k]['comp'] if x != k][:6]
    rad = comps[k]['rad']

    words = ''.join(
        '<li class="word">'
        '<div class="wtop"><span class="wjp">%s</span>'
        '<span class="wrd">%s</span><span class="wen">%s</span></div>'
        '<div class="wex"><span class="exjp">%s</span><span class="exen">%s</span></div>'
        '</li>' % (E(w['w']), E(w['r']), E(w['e']), E(w['s']), E(w['t']))
        for w in c['w'])

    meta = ['<span class="chip">#%d most common</span>' % rank,
            '<span class="chip">%s</span>' % GRADE_NAME.get(r['grade'], ''),
            '<span class="chip">%d strokes</span>' % r['sc']]
    if rad:
        meta.append('<span class="chip">radical %s</span>' % E(rad))
    if comp:
        meta.append('<span class="chip parts">parts %s</span>' % E(' '.join(comp)))

    search = E(k + ' ' + c['kw'] + ' ' + ' '.join(x['w'] + x['r'] + x['e'] for x in c['w'])).lower()

    cards.append("""
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
    <h3>Stroke order <span class="hint">%d strokes &mdash; grey is what you have already drawn</span></h3>
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
        rank, E(k), rank, search,
        E(k), rank,
        E(c['kw']), ''.join(meta),
        reading_spans(r['on'], 'on') or '<span class="none">&mdash;</span>',
        reading_spans(r['kun'], 'kun') or '<span class="none">&mdash;</span>',
        E(c['mn']),
        len(st['s']), E(k),
        words,
        '<div class="tracebox trace">%s</div>' % E(k),
        '<div class="tracebox"></div>' * 5,
    ))

    index_cells.append(
        '<button class="icell" data-goto="%d" title="%s"><span class="ik">%s</span>'
        '<span class="in">%d</span></button>' % (rank, E(c['kw']), E(k), rank))

stroke_data = json.dumps({k: strokes[k] for k in content}, ensure_ascii=False, separators=(',', ':'))

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=Newsreader:opsz,wght@6..72,400;6..72,500&'
         'family=IBM+Plex+Sans:wght@400;500;600&'
         'family=IBM+Plex+Mono:wght@400;500;600&display=swap">')

CSS = """
/* Palette from traditional Japanese pigments: washi paper, sumi ink,
   shu vermilion (the seal and correction red), ai indigo, kuchiba brown. */
:root{
  --paper:#f4f5f1; --panel:#fcfcfa; --ink:#15171a; --muted:#6b706c; --line:#dbded6;
  --shu:#c4331d; --shu-soft:#fbeeea; --ai:#2a4f6e; --kuchiba:#8a6a3b; --ghost:#c7cbc2;
  --shadow:0 1px 2px rgba(21,23,26,.05),0 10px 28px -16px rgba(21,23,26,.22);
  --jp:"Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic",YuGothic,"Meiryo",sans-serif;
  --ui:"IBM Plex Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --display:"Newsreader",Georgia,"Times New Roman",serif;
  --mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --paper:#15171a; --panel:#1d2023; --ink:#e7e9e3; --muted:#9aa099; --line:#2e3236;
    --shu:#ec6a4d; --shu-soft:#2b1a15; --ai:#83aecb; --kuchiba:#c69a63; --ghost:#454a4d;
    --shadow:0 1px 2px rgba(0,0,0,.45),0 10px 28px -16px rgba(0,0,0,.7);
  }
}
:root[data-theme="dark"]{
  --paper:#15171a; --panel:#1d2023; --ink:#e7e9e3; --muted:#9aa099; --line:#2e3236;
  --shu:#ec6a4d; --shu-soft:#2b1a15; --ai:#83aecb; --kuchiba:#c69a63; --ghost:#454a4d;
  --shadow:0 1px 2px rgba(0,0,0,.45),0 10px 28px -16px rgba(0,0,0,.7);
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--ui);
  font-size:16px;line-height:1.55;-webkit-text-size-adjust:100%}
.wrap{max-width:780px;margin:0 auto;padding:0 18px 60px}
:focus-visible{outline:2px solid var(--shu);outline-offset:2px;border-radius:2px}
.hidden{display:none !important}
@media (prefers-reduced-motion:reduce){*{animation:none !important;transition:none !important}}

/* ---- navigation bar ---- */
.bar{position:sticky;top:0;z-index:50;background:var(--paper);
  border-bottom:1px solid var(--line);padding:9px 0}
@supports (backdrop-filter:blur(1px)){
  .bar{background:color-mix(in srgb,var(--paper) 88%,transparent);backdrop-filter:blur(12px)}
}
.barin{max-width:780px;margin:0 auto;padding:0 18px;display:flex;gap:7px;align-items:center}
.btn{font-family:var(--mono);font-size:12px;letter-spacing:.05em;text-transform:uppercase;
  padding:9px 11px;border-radius:2px;border:1px solid var(--line);
  background:var(--panel);color:var(--muted);cursor:pointer;white-space:nowrap;line-height:1}
.btn:hover{border-color:var(--shu);color:var(--shu)}
.btn[aria-pressed="true"]{background:var(--shu);border-color:var(--shu);color:#fff}
.btn.nav{font-size:15px;padding:8px 13px}
.counter{font-family:var(--mono);font-size:.72rem;color:var(--muted);min-width:76px;
  text-align:center;font-variant-numeric:tabular-nums;letter-spacing:.02em}
.counter b{color:var(--ink);font-weight:600}
.spacer{flex:1}

/* ---- master list ---- */
.listwrap{position:sticky;top:53px;z-index:40;background:var(--panel);
  border-bottom:1px solid var(--line);box-shadow:var(--shadow);display:none}
.listwrap.open{display:block}
.listin{max-width:780px;margin:0 auto;padding:14px 18px 18px}
.listin input{width:100%;font:inherit;font-size:15px;padding:9px 12px;border-radius:2px;
  border:1px solid var(--line);background:var(--paper);color:var(--ink);margin-bottom:12px}
.listin input::placeholder{color:var(--muted)}
.index{display:grid;grid-template-columns:repeat(auto-fill,minmax(54px,1fr));gap:0;
  max-height:52vh;overflow-y:auto;border-top:1px solid var(--line);border-left:1px solid var(--line)}
.icell{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1px;
  padding:8px 2px;background:var(--panel);color:var(--ink);cursor:pointer;
  border:0;border-right:1px solid var(--line);border-bottom:1px solid var(--line);font:inherit}
.icell:hover{background:var(--shu-soft);color:var(--shu)}
.icell.here{background:var(--shu);color:#fff}
.icell.here .in{color:rgba(255,255,255,.75)}
.ik{font-family:var(--jp);font-size:1.3rem;line-height:1.1}
.in{font-family:var(--mono);font-size:.58rem;color:var(--muted);font-variant-numeric:tabular-nums}
.nohits{padding:22px 0;text-align:center;color:var(--muted);font-size:.9rem}

/* ---- entry card ---- */
.deck{padding-top:22px}
.card{display:none;background:var(--panel);border:1px solid var(--line);border-radius:4px;
  box-shadow:var(--shadow);padding:26px}
.card.current{display:block}
.hero{display:flex;gap:22px;align-items:flex-start}
.glyphbox{position:relative;flex:0 0 auto}
/* the glyph sits in a manuscript-paper cell, quartered like genko yoshi */
.glyph{font-family:var(--jp);font-size:100px;line-height:1;width:136px;height:136px;
  display:flex;align-items:center;justify-content:center;border:1px solid var(--line);
  background:
    linear-gradient(var(--line),var(--line)) center/100% 1px no-repeat,
    linear-gradient(var(--line),var(--line)) center/1px 100% no-repeat,var(--panel)}
.rank{position:absolute;top:-10px;left:-10px;background:var(--shu);color:#fff;
  font-family:var(--mono);font-size:.66rem;font-weight:600;padding:3px 6px;border-radius:2px;
  font-variant-numeric:tabular-nums}
.heroinfo{min-width:0;flex:1}
.heroinfo h2{font-family:var(--display);font-weight:500;margin:0 0 10px;font-size:1.7rem;
  letter-spacing:-.01em;line-height:1.15;text-wrap:balance}
.meta{display:flex;flex-wrap:wrap;gap:4px 6px;margin-bottom:14px}
.chip{font-family:var(--mono);font-size:.63rem;letter-spacing:.03em;color:var(--muted);
  border:1px solid var(--line);border-radius:2px;padding:2px 6px;font-variant-numeric:tabular-nums}
.chip.parts{font-family:var(--jp);font-size:.72rem;letter-spacing:0}
.readings{display:flex;flex-direction:column;gap:6px}
.rrow{display:flex;gap:10px;align-items:baseline}
.rlab{font-family:var(--mono);font-size:.6rem;font-weight:600;letter-spacing:.11em;
  color:var(--muted);flex:0 0 26px;padding-top:2px}
.rvals{display:flex;flex-wrap:wrap;gap:4px}
.rd{font-family:var(--jp);font-size:1rem;padding:1px 8px;border-radius:2px;background:var(--paper);
  border:1px solid var(--line)}
.rd i{font-style:normal;opacity:.45}
.rd.on{color:var(--ai)} .rd.kun{color:var(--kuchiba)}
.rd.more{color:var(--muted);font-family:var(--ui);font-size:.75rem;border-style:dashed}
.none{color:var(--muted)}

.section{margin-top:24px;padding-top:20px;border-top:1px solid var(--line)}
.section h3{font-family:var(--mono);font-size:.63rem;text-transform:uppercase;letter-spacing:.13em;
  color:var(--muted);margin:0 0 12px;font-weight:600}
.hint{text-transform:none;letter-spacing:.02em;font-weight:400;opacity:.85}
.mn{margin:0;font-size:1rem;line-height:1.65;max-width:62ch}

/* stroke order */
.strokes{display:flex;flex-wrap:wrap;gap:5px}
.frame{width:54px;height:54px;border:1px solid var(--line);background:var(--paper);flex:0 0 auto}
.frame.full{border-color:var(--shu);background:var(--shu-soft);width:112px;height:112px;
  margin-right:5px}
.frame svg{display:block;width:100%;height:100%}

/* words */
.words{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:15px}
.word{padding-left:14px;border-left:2px solid var(--line)}
.word:hover{border-left-color:var(--shu)}
.wtop{display:flex;flex-wrap:wrap;gap:4px 10px;align-items:baseline}
.wjp{font-family:var(--jp);font-size:1.28rem;font-weight:600}
.wrd{font-family:var(--jp);font-size:.88rem;color:var(--shu)}
.wen{font-size:.89rem;color:var(--muted)}
.wex{margin-top:4px;display:flex;flex-direction:column;gap:1px}
.exjp{font-family:var(--jp);font-size:1rem}
.exen{font-size:.85rem;color:var(--muted)}

/* practice cells - manuscript paper */
.tracerow{display:flex;gap:6px;flex-wrap:wrap}
.tracebox{width:58px;height:58px;border:1px solid var(--line);background:
  linear-gradient(var(--line),var(--line)) center/100% 1px no-repeat,
  linear-gradient(var(--line),var(--line)) center/1px 100% no-repeat,var(--paper);
  display:flex;align-items:center;justify-content:center;
  font-family:var(--jp);font-size:44px;line-height:1;color:transparent}
.tracebox.trace{color:var(--ghost)}

/* quiz mode: hide the answer until you commit to one */
body.quiz .glyph{color:transparent}
body.quiz .glyphbox::after{content:"?";position:absolute;inset:0;display:flex;align-items:center;
  justify-content:center;font-family:var(--display);font-size:56px;color:var(--line);
  pointer-events:none}
body.quiz .strokes,body.quiz .tracebox.trace{opacity:0}
body.quiz.reveal .glyph{color:var(--ink)}
body.quiz.reveal .glyphbox::after{content:""}
body.quiz.reveal .strokes,body.quiz.reveal .tracebox.trace{opacity:1}
.revealbtn{display:none;margin-top:16px}
body.quiz .revealbtn{display:inline-block}
body.quiz.reveal .revealbtn{display:none}

footer{color:var(--muted);font-size:.78rem;padding:26px 0;text-align:center;
  max-width:62ch;margin:26px auto 0;border-top:1px solid var(--line)}
footer p{margin:0 0 7px}
footer kbd{font-family:var(--mono);font-size:.72rem;border:1px solid var(--line);
  border-radius:2px;padding:1px 5px;color:var(--ink)}

@media (max-width:600px){
  .wrap{padding:0 12px 50px}
  .card{padding:17px}
  .hero{gap:14px}
  .glyph{font-size:70px;width:100px;height:100px}
  .heroinfo h2{font-size:1.3rem}
  .frame,.tracebox{width:48px;height:48px}
  .frame.full{width:101px;height:101px}
  .tracebox{font-size:36px}
  .barin{padding:0 12px;gap:5px}
  .btn{padding:9px 8px;font-size:11px}
  .btn.nav{font-size:15px;padding:8px 11px}
  .counter{min-width:58px;font-size:.66rem}
  .listin{padding:12px 12px 14px}
  .index{grid-template-columns:repeat(auto-fill,minmax(46px,1fr))}
}

/* printing this page gives the full-size version, one kanji per sheet */
@media print{
  .bar,.listwrap,footer,.noprint,.revealbtn{display:none !important}
  body{background:#fff;font-size:10.5pt}
  .wrap{max-width:none;padding:0}
  .deck{padding:0}
  .card{display:block !important;break-inside:avoid;page-break-after:always;break-after:page;
    box-shadow:none;border:none;padding:0;margin:0}
  .section{break-inside:avoid}
}
"""

BODY = """%s
<div class="bar">
  <div class="barin">
    <button class="btn nav" id="prev" title="Previous kanji (left arrow)" aria-label="Previous kanji">&larr;</button>
    <span class="counter" id="counter"></span>
    <button class="btn nav" id="next" title="Next kanji (right arrow)" aria-label="Next kanji">&rarr;</button>
    <button class="btn" id="rand" title="Jump to a random kanji (press R)">Random</button>
    <span class="spacer"></span>
    <button class="btn" id="listbtn" aria-pressed="false" title="Show the full list (press L)">List</button>
    <button class="btn" id="quiz" aria-pressed="false" title="Hide the kanji so you can write it from the meaning">Quiz</button>
    <button class="btn" id="theme" title="Light or dark" aria-label="Toggle light or dark">&#9680;</button>
  </div>
</div>

<div class="listwrap" id="listwrap">
  <div class="listin">
    <input id="q" type="search" placeholder="Search kanji, reading, meaning or number&hellip;" autocomplete="off">
    <div class="index" id="index">%s</div>
    <div class="nohits hidden" id="nohits">Nothing matches that search.</div>
  </div>
</div>

<div class="wrap">
  <div class="deck" id="deck">%s
    <button class="btn revealbtn" id="reveal">Reveal answer</button>
  </div>
  <footer>
    <p>Ordered by how often each kanji appears in real newspaper text, most common first.
       Frequency from the Mainichi Shinbun corpus (KANJIDIC); stroke order from KanjiVG;
       readings checked against JMdict.</p>
    <p class="noprint"><kbd>&larr;</kbd> <kbd>&rarr;</kbd> to move, <kbd>R</kbd> for a random kanji,
       <kbd>L</kbd> for the list.</p>
  </footer>
</div>
"""

JS = """
const S = __STROKE_DATA__;
const cards = [...document.querySelectorAll('.card')];
const cells = [...document.querySelectorAll('.icell')];
const counter = document.getElementById('counter');
let active = cards.map((_, i) => i);   // indices into cards matching the current filter
let pos = 0;                            // position within active

/* ---------- stroke diagrams ---------- */
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
    const hiOn=(i===hi);
    p.setAttribute('stroke', hiOn?'var(--shu)':'var(--ghost)');
    p.setAttribute('stroke-width', hiOn?'5.5':'4');
    svg.appendChild(p);
  }
  if(nums) for(const [x,y,n] of nums){
    const t=document.createElementNS(NS,'text');
    t.setAttribute('x',x); t.setAttribute('y',y);
    t.setAttribute('font-size','8.5'); t.setAttribute('fill','var(--shu)');
    t.setAttribute('font-family','monospace'); t.setAttribute('font-weight','700');
    t.setAttribute('stroke','var(--shu-soft)'); t.setAttribute('stroke-width','2.2');
    t.setAttribute('paint-order','stroke fill');
    t.textContent=n;
    svg.appendChild(t);
  }
  return svg;
}
function renderStrokes(box){
  if(!box || box.dataset.done) return;
  box.dataset.done='1';
  const d=S[box.dataset.for];
  if(!d) return;
  const full=document.createElement('div');
  full.className='frame full';
  full.appendChild(svgFrame(d.s,d.s.length,-1,d.n));
  box.appendChild(full);
  for(let i=1;i<=d.s.length;i++){
    const f=document.createElement('div');
    f.className='frame';
    f.appendChild(svgFrame(d.s,i,i-1,null));
    box.appendChild(f);
  }
}

/* ---------- paging ---------- */
function show(p, scroll){
  if(!active.length) return;
  pos = (p + active.length) % active.length;
  const card = cards[active[pos]];
  cards.forEach(c=>c.classList.remove('current'));
  card.classList.add('current');
  document.body.classList.remove('reveal');
  renderStrokes(card.querySelector('.strokes'));
  // pre-render the neighbours so paging feels instant
  renderStrokes(cards[active[(pos+1)%active.length]].querySelector('.strokes'));
  renderStrokes(cards[active[(pos-1+active.length)%active.length]].querySelector('.strokes'));
  counter.innerHTML = (active.length===cards.length)
    ? '<b>'+card.dataset.rank+'</b> / '+cards.length
    : '<b>'+(pos+1)+'</b> of '+active.length;
  cells.forEach(c=>c.classList.toggle('here', c.dataset.goto===card.dataset.rank));
  history.replaceState(null,'','#k'+card.dataset.rank);
  try{ localStorage.setItem('kanji-at', card.dataset.rank); }catch(e){}
  if(scroll!==false) window.scrollTo(0,0);
}
const go = d => show(pos+d);
document.getElementById('next').onclick = ()=>go(1);
document.getElementById('prev').onclick = ()=>go(-1);
document.getElementById('rand').onclick = ()=>show(Math.floor(Math.random()*active.length));

/* jump straight to any kanji from the master list */
cells.forEach(c=>c.onclick=()=>{
  const rank=c.dataset.goto;
  const i=cards.findIndex(x=>x.dataset.rank===rank);
  let at=active.indexOf(i);
  if(at<0){ active=cards.map((_,n)=>n); at=i; }   // clear the filter so we can reach it
  show(at);
  closeList();
});

/* ---------- master list + search ---------- */
const listwrap=document.getElementById('listwrap'), listbtn=document.getElementById('listbtn');
const q=document.getElementById('q'), nohits=document.getElementById('nohits');
function openList(){ listwrap.classList.add('open'); listbtn.setAttribute('aria-pressed','true'); q.focus(); }
function closeList(){ listwrap.classList.remove('open'); listbtn.setAttribute('aria-pressed','false'); }
listbtn.onclick = ()=> listwrap.classList.contains('open') ? closeList() : openList();

q.addEventListener('input',()=>{
  const v=q.value.trim().toLowerCase();
  active=[];
  cards.forEach((c,i)=>{
    const hit = !v || c.dataset.search.includes(v) || c.dataset.k===v || c.dataset.rank===v;
    if(hit) active.push(i);
    cells[i].classList.toggle('hidden',!hit);
  });
  nohits.classList.toggle('hidden', active.length>0);
  if(active.length) show(0,false);
});

/* ---------- quiz ---------- */
const qb=document.getElementById('quiz');
qb.onclick=()=>{
  const on=document.body.classList.toggle('quiz');
  document.body.classList.remove('reveal');
  qb.setAttribute('aria-pressed',on?'true':'false');
  try{ localStorage.setItem('kanji-quiz', on?'1':''); }catch(e){}
};
document.getElementById('reveal').onclick=()=>document.body.classList.add('reveal');
try{ if(localStorage.getItem('kanji-quiz')){ document.body.classList.add('quiz'); qb.setAttribute('aria-pressed','true'); } }catch(e){}

/* ---------- theme ---------- */
try{ const t=localStorage.getItem('kanji-theme'); if(t) document.documentElement.dataset.theme=t; }catch(e){}
document.getElementById('theme').onclick=()=>{
  const cur=document.documentElement.dataset.theme
    || (matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
  const nx = cur==='dark'?'light':'dark';
  document.documentElement.dataset.theme=nx;
  try{ localStorage.setItem('kanji-theme',nx); }catch(e){}
};

/* ---------- keyboard ---------- */
addEventListener('keydown',e=>{
  if(e.target.tagName==='INPUT'){
    if(e.key==='Escape'){ q.value=''; q.dispatchEvent(new Event('input')); closeList(); }
    return;
  }
  if(e.metaKey||e.ctrlKey||e.altKey) return;
  if(e.key==='ArrowRight'){ go(1); e.preventDefault(); }
  else if(e.key==='ArrowLeft'){ go(-1); e.preventDefault(); }
  else if(e.key==='r'||e.key==='R'){ show(Math.floor(Math.random()*active.length)); }
  else if(e.key==='l'||e.key==='L'){ listwrap.classList.contains('open')?closeList():openList(); }
  else if(e.key===' '&&document.body.classList.contains('quiz')){
    document.body.classList.add('reveal'); e.preventDefault();
  }
  else if(e.key==='Escape'){ closeList(); }
});

/* ---------- swipe, for the phone ---------- */
let tx=0,ty=0;
const deck=document.getElementById('deck');
deck.addEventListener('touchstart',e=>{tx=e.changedTouches[0].clientX;ty=e.changedTouches[0].clientY;},{passive:true});
deck.addEventListener('touchend',e=>{
  const dx=e.changedTouches[0].clientX-tx, dy=e.changedTouches[0].clientY-ty;
  if(Math.abs(dx)>60 && Math.abs(dx)>Math.abs(dy)*1.6) go(dx<0?1:-1);
},{passive:true});

/* printing wants every card drawn */
addEventListener('beforeprint',()=>cards.forEach(c=>renderStrokes(c.querySelector('.strokes'))));

/* ---------- opening position: URL hash, else where you left off ---------- */
(function(){
  const m=/^#k(\\d+)$/.exec(location.hash);
  let rank = m ? m[1] : null;
  if(!rank){ try{ rank=localStorage.getItem('kanji-at'); }catch(e){} }
  const i = rank ? cards.findIndex(c=>c.dataset.rank===rank) : 0;
  show(i>=0?i:0, false);
})();
"""
JS = JS.replace("__STROKE_DATA__", stroke_data)

TITLE = 'Kanji Through Third Grade'
body_html = BODY % (FONTS, ''.join(index_cells), ''.join(cards))

full = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n%s\n<script>%s</script>\n</body>\n</html>\n'
        % (TITLE, CSS, body_html, JS))
open('kanji.html', 'w', encoding='utf-8').write(full)
print('wrote kanji.html  %.2f MB' % (os.path.getsize('kanji.html') / 1048576))

art = '<title>%s</title>\n<style>%s</style>\n%s\n<script>%s</script>\n' % (TITLE, CSS, body_html, JS)
open('artifact.html', 'w', encoding='utf-8').write(art)
print('wrote artifact.html %.2f MB' % (os.path.getsize('artifact.html') / 1048576))
