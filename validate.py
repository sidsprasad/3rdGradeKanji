import json, sys, glob, os, re

lex = json.load(open('data/lexicon.json', encoding='utf-8'))
info = json.load(open('data/kanji_info.json', encoding='utf-8'))

KANA = re.compile(r'^[぀-ゟ゠-ヿーー]+$')

def norm(r):
    return r.replace('・', '').replace('-', '').strip()

files = sorted(glob.glob('content/b*.json'))
if len(sys.argv) > 1:
    files = [f for f in files if any(a in f for a in sys.argv[1:])]

problems = []
seen = {}
total_k = total_w = 0

for f in files:
    try:
        data = json.load(open(f, encoding='utf-8'))
    except Exception as e:
        problems.append((f, '-', 'INVALID JSON: %s' % e)); continue
    for k, v in data.items():
        total_k += 1
        if k in seen:
            problems.append((f, k, 'duplicate kanji (also in %s)' % seen[k]))
        seen[k] = f
        if k not in info:
            problems.append((f, k, 'not in grade 1-3 list'))
        for field in ('kw', 'mn', 'w'):
            if not v.get(field):
                problems.append((f, k, 'missing field %s' % field))
        if len(v.get('w', [])) < 4:
            problems.append((f, k, 'only %d words' % len(v.get('w', []))))
        for w in v.get('w', []):
            total_w += 1
            blob = w.get('w','')+w.get('r','')+w.get('e','')+w.get('s','')+w.get('t','')
            if 'PLACEHOLDER' in blob or 'TODO' in blob:
                problems.append((f, k, 'PLACEHOLDER in %s' % w.get('w')))
            for field in ('w','r','e','s','t'):
                if not w.get(field):
                    problems.append((f, k, 'word %s missing %s' % (w.get('w'), field)))
            word = w.get('w','')
            if k not in word:
                problems.append((f, k, 'word %s does not contain the kanji' % word))
            # verbs/adjectives conjugate, so require the kanji stem (up to first kana)
            stem = re.split(r'[぀-ゟ゠-ヿ]', word)[0] or word
            if word and word not in w.get('s','') and stem not in w.get('s',''):
                problems.append((f, k, 'sentence does not contain word %s' % word))
            r = norm(w.get('r',''))
            if r and not KANA.match(r):
                problems.append((f, k, 'reading not kana: %s (%s)' % (r, word)))
            # verify reading against JMdict-derived lexicon
            if word in lex:
                readings = {norm(x) for x in lex[word]}
                if r and r not in readings:
                    problems.append((f, k, 'READING? %s = %s ; jmdict has %s'
                                     % (word, r, '/'.join(sorted(readings)[:6]))))
            else:
                problems.append((f, k, 'word not in lexicon: %s (%s)' % (word, r)))

print('files: %d  kanji: %d  words: %d' % (len(files), total_k, total_w))
print('problems: %d' % len(problems))
for p in problems:
    print('  %s  %s  %s' % p)
