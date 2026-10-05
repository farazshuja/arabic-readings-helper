# Arabic reading data

Story 1 is **من كسر الأصنام — قصة سيدنا إبراهيم**, reconstructed from all 15 pages of `books/Qisas Story 1 Sayyiduna Ibrahim (AS).pdf`. It contains 16 sections and 183 reading units. Long printed lines have been joined into sentences or short passages; these are stable logical lines, not lines that depend on screen width.

Story 2 is **قصة يوسف — قصة سيدنا يوسف**, transcribed and checked against all 27 pages of `books/Qisas Story 2 Sayyiduna Yusuf  (AS).pdf`. It contains 25 sections and 286 reading units, with English/Urdu meanings, morphology, retained disambiguating marks, and Quran references. Editorial corrections and explanations are recorded in its JSON.

Story 3 is **سفينة نوح — قصة سيدنا نوح**, transcribed and checked against all 19 pages of `books/Qisas Story 3 Sayyiduna Nooh (AS).pdf`. It contains 22 sections and 193 reading units. The self-contained `stories/03-nooh.json` includes 466 English/Urdu vocabulary entries, noun/verb forms, roots, source pages, Quran references, and documented editorial corrections.

Story 4 is **العاصفة — قصة سيدنا هود**, transcribed and checked against all 11 pages of `books/Qisas Story 4 Sayyiduna Hud (AS).pdf`. It contains 11 sections, 110 reading units and 380 English/Urdu vocabulary entries. The self-contained `stories/04-hud.json` includes both reading modes, morphology, roots, source pages, 12 Quran references and documented source corrections.

Story 5 is **ناقة ثمود — قصة سيدنا صالح**, transcribed and checked against all 12 pages of `books/Qisas Story 5 Sayyiduna Salih (AS).pdf`. It contains 13 sections, 109 reading units and 423 English/Urdu vocabulary entries. The self-contained `stories/05-salih.json` includes both reading modes, noun/verb forms, roots, source pages, 15 Quran references, and the final hadith source. Original chapter numbers 12–24 are retained in `sourceSectionNumber`.

Story 6 is **موسى — قصة سيدنا موسى**, transcribed from all 83 PDF pages. It contains 46 chapters across two parts, 759 reading units and 226 Quran excerpt references. Both reading modes, English/Urdu vocabulary, noun/verb forms, roots and page provenance are embedded in `stories/06-musa.json`. Cover pages 1 and 41 are excluded from narrative coverage; original part and chapter numbers are retained.

Story 7 is **شعيب — قصة سيدنا شعيب**, transcribed and checked against all nine PDF pages. It contains 14 chapters, 39 reading units, 433 English/Urdu vocabulary entries and 20 Quran excerpt references. The self-contained `stories/07-shuaib.json` includes both reading modes, noun/verb forms, roots and source-page provenance (printed pages 174–181).

Story 8 is **داود وسليمان — قصة سيدنا داود وسيدنا سليمان**, transcribed and checked against all twelve PDF pages. It contains 15 chapters, 84 reading units, 604 English/Urdu vocabulary entries and 41 Quran excerpt references, including An-Naml 27:20–44. The self-contained `stories/08-dawood-sulaiman.json` includes both reading modes, noun/verb forms, roots, contextual meanings and source-page provenance (printed pages 184–194). Pronoun corrections are documented in the JSON.

Story 9 is **أيوب ويونس — قصة سيدنا أيوب وسيدنا يونس**, transcribed and checked against all six PDF pages. The supplied Story 9 PDF contains both prophets’ stories. It includes seven chapters (original numbers 16–22), 21 reading units, 319 English/Urdu vocabulary entries and six Quran verse references. Both reading modes, morphology, roots, contextual meanings and the two footnotes crediting Ibn Kathir are embedded in `stories/09-ayyub-yunus.json`; narrative pages correspond to printed pages 196–200.

Story 10 is **زكريّا — قصة سيدنا زكريا**, transcribed and checked against all six PDF pages. It contains eight chapters, 27 reading units, 682 word occurrences, 336 English/Urdu vocabulary entries and eleven Quran verse references. The story includes Maryam’s care and Yahya’s upbringing. Both reading modes, noun/verb forms, roots, contextual meanings and page provenance (printed pages 202–206) are embedded in `stories/10-zakariyya.json`.

## Files

- `stories.json`: lightweight home-screen catalog. Each record supplies the title, summary, counts, and story JSON path.
- `stories/01-ibrahim.json` through `stories/10-zakariyya.json`: self-contained story text and dictionaries. The catalog lists their exact filenames; the website loads only the selected story file.
- `stories/01-ibrahim.vocalized.txt`: editable, reviewed transcription used by the build script. `#` starts a section; `@` lists one-based PDF pages.
- `stories/01-ibrahim.lexicon.tsv`: editable bilingual vocabulary source. It is a pipe-delimited file; its header describes the columns.
- `stories/02-yusuf.vocalized.txt` and `stories/02-yusuf.lexicon.tsv`: Story 2 transcription and bilingual lexical additions. Its builder reuses common vocabulary from Story 1, and embeds every required entry in the final JSON.
- `stories/03-nooh.vocalized.txt` and `stories/03-nooh.lexicon.tsv`: Story 3 transcription and bilingual lexical additions. Its builder reuses reviewed vocabulary and resolution rules from the earlier stories; the resulting JSON includes everything the browser needs for this story.

- `stories/04-hud.vocalized.txt` and `stories/04-hud.lexicon.tsv`: Story 4 transcription and bilingual lexical additions, built with `scripts/build_hud.py`. Common entries are reused during preparation and embedded in its JSON.

- `stories/05-salih.vocalized.txt` and `stories/05-salih.lexicon.tsv`: Story 5 transcription and bilingual lexical additions, built with `scripts/build_salih.py`. Common vocabulary and clitic rules are reused during preparation; every required entry is embedded in its JSON.

The browser loads the catalog and selected story as static assets. After loading a story, text toggles and dictionary cards work entirely in browser memory, without a database, API, or further vocabulary requests. To support use after closing/reopening the browser without internet, the eventual website will also need asset caching, such as a service worker. Opening via `file://` may block `fetch`; use a static site origin or import the JSON during the frontend build.

## Text and word contract

| Field | Use |
| --- | --- |
| `sections[].lines[].id` | Stable key for each reading unit and its toggle state. |
| `text` | Default reading text: shadda and selected disambiguating vowels retained. |
| `textBare` | Completely stripped harakat, if needed. Hamza, madda and alif maqsura remain. |
| `vocalized` | Full editorial tashkil, including grammatical endings for connected reading. |
| `leading` | Punctuation before the first word, such as the opening Quran bracket. |
| `tokens[]` | Ordered clickable words, with the same three text variants. |
| `tokens[].after` | Exact spaces/punctuation after the word; preserve when rendering. |
| `tokens[].vocabularyId` | Exact key into this story's `vocabulary` object. |
| `tokens[].parts` | Attached conjunctions, articles, prepositions and pronouns, each linked to an entry. |
| `tokens[].usage` | Optional occurrence-specific English/Urdu meaning, e.g. a passive verb. |
| `sourcePages` | One-based PDF page numbers for tracing the passage. Printed page numbers are PDF page + 2 for Story 1, PDF page + 17 for Story 2, PDF page + 44 for Story 3, and PDF page + 66 for Stories 4 and 5. |
| `references` | Quran excerpts with verse references and links. |

For rendering, append `leading`, then for every token append a clickable word followed by `after`. This reconstructs the line exactly. Do not split `text` on spaces or infer meanings from a root: the token links already distinguish **مَلِك** from other readings and **مَنْ** from **مِنْ**. Section headings, the story title, and subtitle also have token arrays.

Toggle each line between `text` and `vocalized`. For its copy icon, copy that entire selected variant using `navigator.clipboard.writeText(...)`; handle a denied clipboard request in the UI. Clipboard access normally requires HTTPS or localhost and a user click. “Full i'rabs” here means visible harakat/tashkil; this data does not provide a word-by-word syntactic parsing lesson.

## Vocabulary cards

All entries include `lemma`, `partOfSpeech`, `root`, and `meanings.en` / `meanings.ur`. Both meaning languages are present even for function words, attached pronouns and proper names.

- Nouns and adjectives include `noun.singular` and `noun.plural` (an array).
- Verbs include `verb.madi`, `verb.mudari`, and `verb.masdar` (an array). Dictionary forms are third-person masculine singular; the actual sentence form is in `token.vocalized`.
- `root` is a space-separated Arabic root, or `null` with a `rootNote`. Foreign names and particles are not given invented roots.
- Empty plural/masdar arrays and a `null` mudari are intentional. Display `formNote`, rather than showing an unexplained blank or generating a guessed form. For example, **ليس** is a defective verb.
- English and Urdu senses are written for this story; they are not exhaustive dictionary definitions. In the form tables, collective/abstract words and fixed expressions have explanatory notes where needed.

For **يبيع**, the card supplies **بَاعَ / يَبِيعُ / بَيْعٌ**, root **ب ي ع**, English **sell**, Urdu **بیچنا**. For **الأصنام**, it supplies **صَنَمٌ / أَصْنَامٌ**, root **ص ن م**, English **idol**, Urdu **بت**.

For a compound word such as **ويمنعهم**, show the main verb card and then the English/Urdu meanings of its prefix **وَ** and suffix **هُمْ** using `parts`. These parts decompose attached clitics, not every inflectional ending. `surfaceBare` reconstructs the word; `underlying` and `note` explain contracted spellings such as **مِنَّا** and **لِلَّهِ**. A card can prioritize `token.usage` when present, followed by the base dictionary meaning and form table. Use `dir="rtl" lang="ur"` for Urdu and `dir="rtl" lang="ar"` for Arabic; keep English left-to-right.

## Minimal frontend integration

```js
const catalog = await fetch('data/stories.json').then(r => r.json());
const selected = catalog.stories[0];
const story = await fetch(`data/${selected.file}`).then(r => r.json());

function renderLine(line, showHarakat, container, openCard) {
  const field = showHarakat ? 'vocalized' : 'text';
  container.replaceChildren(document.createTextNode(line.leading));
  container.dir = 'rtl';
  container.lang = 'ar';
  for (const token of line.tokens) {
    const word = document.createElement('button');
    word.type = 'button';
    word.textContent = token[field];
    word.onclick = () => openCard({
      surface: token.vocalized,
      usage: token.usage,
      entry: story.vocabulary[token.vocabularyId],
      parts: token.parts.map(p => ({ ...p, entry: story.vocabulary[p.vocabularyId] }))
    });
    container.append(word, document.createTextNode(token.after));
  }
}

// Call inside the line's copy-button handler; await and handle rejection.
async function copyLine(line, showHarakat) {
  await navigator.clipboard.writeText(showHarakat ? line.vocalized : line.text);
}
```

Style the word buttons as inline text and give them visible keyboard focus. Use a button with `aria-expanded` for the line's harakat toggle, and an accessible dialog/popover for the vocabulary card. Set focus management and dismissal behavior in the eventual frontend. All story strings should be rendered as text, not injected as HTML.

## Editorial review and rebuilding

The JSON includes source SHA-256, a correction log, vocalization policies, and references. The text has been checked against the page images; the original narrative and deliberate repetitions are preserved. Quran quotations use standard modern **imlai** spelling and retain the excerpts printed in the story, rather than expanding them into full verses. They are not a facsimile of Uthmani orthography or recitation notation. Verse references are linked to [Quran.com](https://quran.com); lexical context can also be checked with the [Quranic Arabic Corpus](https://corpus.quran.com).

The added vocalization, morphology and bilingual glosses are an editorial preparation, not a certified Arabic-language review. A qualified Arabic editor should review them before public release. Historical/theological statements remain those of the supplied beginner story.

From the repository root, using any Python 3 runtime:

```powershell
python scripts/build_story.py
python scripts/build_yusuf.py
python scripts/build_nooh.py
python scripts/build_hud.py
python scripts/build_salih.py
python scripts/build_musa.py
python scripts/build_shuaib.py
python scripts/build_dawood_sulaiman.py
python scripts/build_ayyub_yunus.py
python scripts/build_zakariyya.py
python scripts/validate_story.py
```

The build uses only the Python standard library, fails on unmapped/ambiguous words, and requires no network. If you add new inflected forms, add exact mappings in the lexicon or build script, and verify their context. Validation checks unique IDs, all vocabulary references, both languages, morphology fields, source-page coverage, the source checksum, contextual distinctions, and exact reconstruction of every line in both reading modes.
