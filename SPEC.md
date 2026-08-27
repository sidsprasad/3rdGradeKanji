# Authoring spec — kanji study pages

You are writing study content for a learner preparing for a Japanese naturalization
interview. They must be able to *write* every kanji taught up to 3rd grade of Japanese
elementary school (440 kanji), and know the common words built from them.

The 440 kanji are already sorted by real newspaper frequency (most common first) and the
stroke-order diagrams are already generated. Your job is ONLY the written content for the
kanji in your assigned rank range.

## Getting your reference data

From the project root, run:

```
PYTHONIOENCODING=utf-8 python ref.py <START> <END>
```

That prints one line per kanji: rank, the kanji, frequency/grade/stroke count, the ON
readings, the KUN readings, the English meanings, and the component breakdown from
KanjiVG. Use those readings and components — do not invent them.

## What you write

Write exactly one JSON object to `content/bNN.json` (the filename you were given),
covering exactly the kanji in your range, **in the same order `ref.py` printed them**.

```json
{
"日":{"kw":"day / sun","mn":"A picture of the sun. The old form was a circle with a dot in the middle; the brush squared the circle off, and the dot became the line inside.","w":[
 {"w":"日","r":"ひ","e":"day; sun","s":"日がのぼる。","t":"The sun rises."},
 {"w":"今日","r":"きょう","e":"today","s":"今日は雨です。","t":"It is raining today."},
 {"w":"日本","r":"にほん","e":"Japan","s":"日本に住んでいます。","t":"I live in Japan."},
 {"w":"毎日","r":"まいにち","e":"every day","s":"毎日日本語を話します。","t":"I speak Japanese every day."},
 {"w":"日曜日","r":"にちようび","e":"Sunday","s":"日曜日は休みです。","t":"Sunday is my day off."}]}
}
```

Fields:

- `kw` — a 1–4 word English keyword for the kanji. Slashes to separate senses.
- `mn` — the mnemonic. One or two sentences. **Build it out of the kanji's actual
  components** (the `COMP:` field from `ref.py`), naming them so the learner sees the
  parts they must write. A genuine etymology is better than an invented story when you
  know it; an invented story is fine when you don't, as long as it uses the real parts.
  Write it so it helps someone *reproduce the shape from memory*. Plain prose, no
  markdown, no bullet points.
- `w` — **5 words** (4 is acceptable only when the kanji genuinely has no 5th common
  word — rare kanji like 午). Order them most common first. Include the single-kanji word
  and/or the okurigana verb/adjective form first when one exists (日 → ひ; 生 →
  生きる/生まれる), then the most common compounds. Every word must actually contain the
  kanji.
  - `w` word as written, `r` its reading in kana, `e` short English gloss,
    `s` a Japanese example sentence containing the word, `t` the English translation.
- Sentences: short (roughly 5–12 characters of content), natural, everyday. Prefer
  situations a working adult in Japan actually meets — city hall, work, family, trains,
  the weather. Where a kanji has civic meaning (選挙, 議員, 県, 区役所, 憲法…) prefer a
  sentence that would be useful to someone taking a naturalization interview.
  End every Japanese sentence with 。
- English: British or American spelling is fine, be consistent within your file. Natural
  English, not word-for-word glossing.

## Hard rules

- **Never leave a placeholder.** No "PLACEHOLDER", no "TODO", no half-written sentence,
  no stray text in a language other than Japanese/English. Every one of the five fields
  must be real, finished content.
- Readings must be kana only, and must be the reading that word actually takes
  (連濁/rendaku included: 手 + 紙 → てがみ; 出 + 口 → でぐち).
- Do not reuse the same compound word twice within the same kanji's list.
- Valid JSON, UTF-8. No trailing commas. No comments.

## Verify before you finish

```
PYTHONIOENCODING=utf-8 python validate.py bNN
```

This checks the JSON parses, that no placeholders remain, that every word contains its
kanji and appears in its sentence, and **that every reading matches JMdict**. It must
print `problems: 0`.

If it reports `READING?`, your reading disagrees with the dictionary — fix the reading
(or pick a different word). If it reports `word not in lexicon`, that word is not in
JMdict at all; usually it is a proper noun or something you mis-typed — replace it with a
real, common word. Do not edit `validate.py` to silence a problem; fix the content.

Report back: your file path, the kanji count, and the final validator line.
