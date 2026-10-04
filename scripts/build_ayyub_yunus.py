"""Build the reviewed Ayyub and Yunus story into a self-contained static payload."""
import hashlib
import json
import re
import sys
import build_story as b
import build_dawood_sulaiman as h
import build_musa as m
ROOT = b.ROOT
DEST = ROOT / 'data/stories/09-ayyub-yunus.json'

def load_lexicon():
    h.load_lexicon()
    for raw in (ROOT / 'data/stories/09-ayyub-yunus.lexicon.tsv').read_text(encoding='utf-8').splitlines():
        if not raw or raw.startswith('#'):
            continue
        ident, pos, root, first, second, masdar, en, ur, extra = raw.split('|')
        entry = {'id': ident, 'partOfSpeech': pos, 'lemma': first, 'root': None if root == '-' else root, 'meanings': b.bilingual(en, ur)}
        if pos == 'verb':
            entry['verb'] = {'madi': first, 'mudari': None if second == '-' else second, 'masdar': [] if masdar == '-' else masdar.split('، ')}
        elif pos in ('noun', 'adjective'):
            entry['noun'] = {'singular': first, 'plural': [] if second == '-' else second.split('، ')}
            if second == '-':
                entry['formNote'] = b.bilingual('Collective, abstract or comparative use; no plural supplied for this sense.', 'اسم جمع، مجرد معنی یا تقابلی استعمال؛ اس معنی کی جمع نہیں دی گئی۔')
        if root == '-':
            entry['rootNote'] = b.bilingual('Proper name or function word; no derivational root assigned.', 'اسم خاص یا حرف؛ اشتقاقی مادہ مقرر نہیں کیا گیا۔')
        b.lexicon[ident] = entry
        for form in [first, *([] if second == '-' else second.split('، ')), *extra.split()]:
            b.forms.setdefault(b.bare(form), []).append(ident)
            stem=b.bare(form)
            if pos in ('noun','adjective'):
                b.forms.setdefault(stem+'ا',[]).append(ident)
                if stem.endswith('ة'): b.forms.setdefault(stem[:-1]+'ت',[]).append(ident)
        if pos == 'verb':
            stem=b.bare(first)
            for ending in ('ت','تم','وا','و','نا'):
                if not stem.endswith(('ى','ا')): b.forms.setdefault(stem+ending,[]).append(ident)
            present=b.bare(second)
            for prefix in ('ي','ت','أ','ن'):
                base=prefix+present[1:]
                for ending in ('','ون','وا','و'):
                    b.forms.setdefault(base+ending,[]).append(ident)

    for ident in set(FORCED.values()):
        assert ident in b.lexicon, ident

    for ident, words in INFLECTIONS.items():
        assert ident in b.lexicon, ident
        for word in words.split(): b.forms.setdefault(word, []).append(ident)

INFLECTIONS = {'merciful':'رحيمة', 'ds-precise':'دقيقة', 'hear':'اسمع', 'ay-answer':'استجبنا', 'ay-heal':'عافا', 'ay-enjoy':'متعنا', 'ay-isolate':'أفرد', 'ay-block':'تسد', 'ay-restrict':'نقدر'}
FORCED = {'أَبْعَدَ':'ds-farther','أَشَدَّ':'more-intense','الْجَلِيسُ':'ay-companion','النُّونِ':'ay-fish','فَرَفَعَ':'raise-up','مَسَّنِيَ':'touch','وَرَدَّ':'return-object','وَرَفْعِ':'ay-raising','يَذْكُرُ':'remember','يَشُقُّ':'tear','يَكْذِبُ':'lie','كَثِيرٍ':'ay-kathir','نَقْدِرَ':'ay-restrict','وَنَجَّيْنَاهُ':'ay-rescue','أَجْلِهِ':'term','الْأَسَدِ':'ay-lion','كَثِيرٌ':'many','نُنْجِي':'ay-rescue-iv','وَاسْتَجَابَ':'ay-answer','وَتُسَدُّ':'ay-block','أَظْهُرِهِمْ':'ay-back','فَنَفَعَهَا':'ay-benefit','تَبَارَكَ':'ay-blessed','فَتُخْرِجُ':'bring-out','أَنِّي':'anna','وَسِخَالُهَا':'ay-lamb','فَلَا':'not','مَالَهُ':'wealth','سَلْوَى':'ay-solace','سَلِيمًا':'ay-sound','سَلِيمٌ':'ay-sound','الْحَالِكُ':'ay-dark','وَذَا':'possessor','فَلَوْلَا':'ay-if-only','آخِرِهِ':'ay-last','آخَرُ':'other','يَحْنُو':'ay-affection','وَحِكْمَتُهَا':'wisdom'}

def choose(ids, vocal):
    if 'what' in ids and 'ay-ma-exclamation' in ids: return 'what'
    if {'sh-diminution','sh-withhold'} <= set(ids): return 'sh-diminution' if 'بَخْس' in vocal else 'sh-withhold'
    return h.choose(ids, vocal)

def resolve(vocal):
    if vocal in FORCED: return m.forced_resolve(vocal, FORCED[vocal])
    return h.resolve(vocal)

PASSIVE = {'فَابْتُلِيَ': ('was tested', 'آزمایا گیا'), 'ابْتُلِيَ': ('was tested', 'آزمایا گیا'), 'وَأُفْرِدَ': ('was isolated', 'الگ کر دیا گیا'), 'وَتُسَدُّ': ('are closed', 'بند کر دیے جاتے ہیں')}

def light(vocal):
    if vocal in PASSIVE: return re.sub(r'[ًٌٍ]$', '', vocal)
    ident,_=resolve(vocal)
    key=b.bare(vocal)
    if ident == 'sovereignty': return key.replace('ملك','مُلك')
    if ident in ('king','queen'): return key.replace('ملك','مَلِك').replace('ملوك','مُلوك')
    if ident == 'ay-cast': return key.replace('ملقى','مُلقى')
    if ident == 'ay-loser': return key.replace('مدحض','مُدْحَض')
    if key in b.SELECTIVE: return b.SELECTIVE[key]
    return ''.join(c for c in vocal if not b.MARKS.fullmatch(c) or c=='\u0651')

def make_line(vocal, ident, pages):
    result=b.make_line(vocal, ident, pages)
    for index, token in enumerate(result['tokens']):
        if token['vocalized'] in PASSIVE:
            token['usage']=b.bilingual(PASSIVE[token['vocalized']][0]+'; passive', PASSIVE[token['vocalized']][1]+'؛ مجہول')
        usage = {'أَجْلِهِ': ('his sake; for him (من أجله)', 'اس کی خاطر؛ اس کے لیے'),
                 'مَسَّنِيَ': ('afflicted me; touched me with suffering', 'مجھے تکلیف پہنچی'),
                 'الضُّرُّ': ('suffering; affliction', 'تکلیف؛ بیماری'),
                 'دَقِيقَةً': ('fine; finely ground (here)', 'باریک؛ باریک پسی ہوئی'),
                 'تَخْتَلِفُ': ('come and go; move about (here)', 'آنا جانا؛ حرکت کرنا'),
                 'الدَّوَابُّ': ('creatures; crawling creatures (here)', 'جاندار؛ رینگنے والے جاندار'),
                 'بَعَثَهُ': ('He sent him', 'اسے بھیجا'),
                 'أَظْهُرِهِمْ': ('their midst (من بين أظهرهم)', 'ان کے درمیان'),
                 'نَقْدِرَ': ('constrain him; restrict him', 'اس پر تنگی کرنا'),
                 'النُّونِ': ('the fish; Yunus is Dhun-Nun, the man of the fish', 'مچھلی؛ ذوالنون حضرت یونس کا لقب ہے')}
        if token['vocalized'] in usage:
            token['usage']=b.bilingual(*usage[token['vocalized']])
        rest=b.bare(''.join(t['vocalized']+t['after'] for t in result['tokens'][index+1:])).lstrip()
        if token['vocabularyId']=='what' and rest.startswith(('أشد الظلام','أبعد السلام')):
            token['vocabularyId']='ay-ma-exclamation'
            next(p for p in token['parts'] if p['role']=='stem')['vocabularyId']='ay-ma-exclamation'
    return result

def main():
    load_lexicon()
    b.choose, b.resolve, b.light = choose, resolve, light
    b.lexicon['negation-in'] = {'id': 'negation-in', 'partOfSpeech': 'particle', 'lemma': 'إِنْ', 'root': None, 'meanings': b.bilingual('not (with إلا)', 'نہیں؛ الا کے ساتھ نفی'), 'rootNote': b.bilingual('Function word.', 'حرف۔')}
    text = (ROOT / 'data/stories/09-ayyub-yunus.vocalized.txt').read_text(encoding='utf-8')
    refs = [(21,83),(21,84),(10,98),(37,141),(21,87),(21,88)]
    quotes = re.findall('﴿(.*?)﴾', text)
    assert len(quotes) == len(refs)
    b.QUOTES = [(b.bare(q), s, a) for q, (s, a) in zip(quotes, refs)]
    failures = {}
    for word in set(b.WORDS.findall('\n'.join(r[2:].split('|')[1] if r.startswith('# ') else r for r in text.splitlines() if not r.startswith('@')))):
        try:
            resolve(word)
        except ValueError as exc:
            failures[word] = str(exc)
    if failures:
        for word in sorted(failures, key=b.bare):
            print(failures[word])
        sys.exit(1)
    sections, pages = [], []
    for raw in text.splitlines():
        if raw.startswith('# '):
            number, title, english = raw[2:].split('|')
            sid = f's{int(number):02d}'
            heading = make_line(title, sid + '-title', [])
            sections.append({'id': sid, 'number': int(number), 'sourceSectionNumber': int(number)+15, 'title': heading['text'], 'titleVocalized': title,
                             'titleEnglish': english, 'titleTokens': heading['tokens'], 'lines': []})
        elif raw.startswith('@'):
            pages = [int(p) for p in raw[1:].split(',')]
        elif raw:
            section = sections[-1]
            section['lines'].append(make_line(raw, f"{section['id']}-l{len(section['lines'])+1:03d}", pages.copy()))
    template = json.loads((ROOT / 'data/stories/03-nooh.json').read_text(encoding='utf-8'))
    source = ROOT / 'books/Qisas Story 9 Sayyiduna Ayyub (AS).pdf'
    checksum = hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else json.loads(DEST.read_text(encoding='utf-8'))['source']['sha256']
    editorial = template['editorial'].copy()
    editorial.update({'method': 'Manual transcription checked against all six rendered PDF pages; editorial grammatical vocalization and bilingual vocabulary.',
        'corrections': [],
        'notes': ['The supplied Story 9 PDF contains both Ayyub and Yunus. Its cover is PDF page 1 (printed page 195); narrative PDF pages 2–6 correspond to printed pages 196–200.',
                  'All seven chapters are retained; original chapter numbers 16–22 appear in sourceSectionNumber.',
                  'The two footnotes crediting Ibn Kathir are retained as parenthesized reading units on their source pages.',
                  'Quran passages are split at verse boundaries and use modern imlai spelling with verified verse links.',
                  'Added vocalization, morphology and bilingual glosses are editorial preparation.'],
        'referenceSources': [{'label': 'Source story PDF', 'path': 'books/' + source.name}, {'label': 'Quran references', 'url': 'https://quran.com'}, {'label': 'Quranic Arabic Corpus', 'url': 'https://corpus.quran.com'}]})
    story = {k: template[k] for k in ('schemaVersion', 'language', 'direction', 'meaningLanguages')}
    story.update({'id': '09-ayyub-yunus', 'number': 9, 'titleEnglish': 'Ayyub and Yunus', 'titleUrdu': 'حضرت ایوب اور یونس',
        'description': b.bilingual('Read about Ayyub’s patience and Yunus’s prayer, in seven chapters.', 'حضرت ایوب کے صبر اور حضرت یونس کی دعا کا قصہ؛ سات ابواب۔'),
        'source': {'file': 'books/' + source.name, 'sha256': checksum, 'pdfPages': 6, 'coverPage': 1, 'printedPageRange': [196,200]},
        'editorial': editorial, 'sections': sections})
    for key, vocal in [('title', 'أَيُّوبُ وَيُونُسُ'), ('subtitle', 'قِصَّةُ سَيِّدِنَا أَيُّوبَ وَسَيِّدِنَا يُونُسَ')]:
        heading = make_line(vocal, key, [1])
        story[key], story[key + 'Vocalized'], story[key + 'Tokens'] = heading['text'], vocal, heading['tokens']
    lines = [l for s in sections for l in s['lines']]
    all_tokens = [l['tokens'] for l in lines] + [s['titleTokens'] for s in sections] + [story['titleTokens'], story['subtitleTokens']]
    used = {p['vocabularyId'] for tokens in all_tokens for t in tokens for p in t['parts']}
    story['vocabulary'] = {k: v for k, v in b.lexicon.items() if k in used}
    story['counts'] = {'sections': len(sections), 'lines': len(lines), 'wordOccurrences': sum(len(l['tokens']) for l in lines),
                       'vocabularyEntries': len(story['vocabulary'])}
    DEST.write_text(json.dumps(story, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    b.update_catalog(story, DEST.name)
    print(json.dumps(story['counts']))


if __name__ == '__main__':
    main()
