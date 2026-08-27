"""Cross-batch QA: catch style drift and thin content between separately authored batches."""
import json, glob, re, statistics, collections, sys

ordered = json.load(open('data/ordered.json', encoding='utf-8'))
rank = {r['k']: r['rank'] for r in ordered}

files = sorted(glob.glob('content/b*.json'))
allc = {}
rows = []

for f in files:
    d = json.load(open(f, encoding='utf-8'))
    allc.update(d)
    mn = [len(v['mn']) for v in d.values()]
    nw = [len(v['w']) for v in d.values()]
    sent = [len(w['s']) for v in d.values() for w in v['w']]
    kw = [len(v['kw']) for v in d.values()]
    rows.append((f.split('\\')[-1], len(d), round(statistics.mean(mn)), min(mn), max(mn),
                 round(statistics.mean(nw), 2), round(statistics.mean(sent), 1), round(statistics.mean(kw), 1)))

print('%-12s %5s %s' % ('file', 'kanji', 'mnemonic_len(avg/min/max)  words/kanji  sentence_len  kw_len'))
for r in rows:
    print('%-12s %5d      %4d /%3d /%4d          %5.2f        %5.1f       %4.1f' %
          (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]))

print('\ntotal kanji: %d' % len(allc))

issues = []

# coverage + ordering
for r in ordered:
    if r['k'] not in allc:
        issues.append('MISSING content for %s (rank %d)' % (r['k'], r['rank']))

# thin or bloated content
for k, v in allc.items():
    if len(v['mn']) < 45:
        issues.append('thin mnemonic  %s (#%d): %s' % (k, rank[k], v['mn']))
    if len(v['mn']) > 400:
        issues.append('very long mnemonic %s (#%d): %d chars' % (k, rank[k], len(v['mn'])))
    if len(v['w']) < 5:
        issues.append('only %d words  %s (#%d)' % (len(v['w']), k, rank[k]))
    if len(v['kw']) > 42:
        issues.append('long keyword  %s (#%d): %s' % (k, rank[k], v['kw']))
    seen = collections.Counter(w['w'] for w in v['w'])
    for w, n in seen.items():
        if n > 1:
            issues.append('duplicate word %s within %s (#%d)' % (w, k, rank[k]))
    for w in v['w']:
        if len(w['s']) > 42:
            issues.append('long sentence %s (%s #%d): %s' % (w['w'], k, rank[k], w['s']))
        if len(w['s']) < 5:
            issues.append('tiny sentence %s (%s #%d): %s' % (w['w'], k, rank[k], w['s']))
        if not w['s'].rstrip().endswith(('。', '？', '！')):
            issues.append('sentence lacks 。 %s (%s #%d): %s' % (w['w'], k, rank[k], w['s']))
        # latin letters / cyrillic / hangul leaking into Japanese fields
        if re.search(r'[A-Za-zЀ-ӿ가-힯]', w['s']):
            issues.append('non-Japanese text in sentence %s (%s #%d): %s' % (w['w'], k, rank[k], w['s']))
        if re.search(r'[Ѐ-ӿ가-힯]', w['e'] + w['t']):
            issues.append('non-English text in gloss/translation %s (%s #%d)' % (w['w'], k, rank[k]))
        if re.search(r'[぀-ヿ一-鿿]', w['t']):
            issues.append('Japanese left in English translation %s (%s #%d): %s' % (w['w'], k, rank[k], w['t']))

# how often is the single-kanji / okurigana form offered first?
solo_first = sum(1 for v in allc.values()
                 if re.match(r'^[一-鿿][぀-ゟ]*$', v['w'][0]['w']))
print('kanji whose first word is the standalone/okurigana form: %d' % solo_first)

# most-reused words across the whole document
cnt = collections.Counter(w['w'] for v in allc.values() for w in v['w'])
print('most reused words: %s' % ', '.join('%s×%d' % (w, n) for w, n in cnt.most_common(8)))

print('\nissues: %d' % len(issues))
for i in issues[:80]:
    print('  ' + i)
if len(issues) > 80:
    print('  ... and %d more' % (len(issues) - 80))
