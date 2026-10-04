"""Build the reviewed Shuaib story into a self-contained static payload."""
import hashlib
import json
import re
import sys
import build_story as b
import build_musa as h
ROOT = b.ROOT
DEST = ROOT / 'data/stories/07-shuaib.json'

def load_lexicon():
    h.load_lexicon()
    for raw in (ROOT / 'data/stories/07-shuaib.lexicon.tsv').read_text(encoding='utf-8').splitlines():
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

    for ident, words in INFLECTIONS.items():
        assert ident in b.lexicon, ident
        for word in words.split(): b.forms.setdefault(word, []).append(ident)

INFLECTIONS = {'ability-v':'استطعت', 'open':'افتح', 'prophet':'نبيين', 'father':'أبوين',
               'choose-take':'اتخذتمو', 'hand':'يدي', 'fabricate':'يفترى', 'be-harsh':'يقس',
               'forbid':'ينها', 'come-back':'عدنا تعودن نعود', 'sh-repeat':'ترددون',
               'sh-frighten':'يخيفون', 'sh-retain':'وعت', 'sh-grieve':'آسى',
               'sh-stone':'رجمنا رجمو', 'sh-smart':'أذكياؤ', 'spoil-perish':'أتلف',
               'sh-measure':'مكيال',
               'sh-enrich':'أغنا', 'first':'أولون',
               }
FORCED = {'أَصَلَاتُكَ':'prayer', 'بِالْحَقِّ':'truth', 'بَقِيَّتُ':'remainder',
          'بَلَّغَ':'convey', 'سَعِيدٌ':'m-happy', 'عُدْنَا':'come-back',
          'كَذَّبَتْ':'deny-ii', 'كَذَّبُوا':'deny-ii', 'لِأُولِي':'possessor',
          'وَتَخَلَّصُوا':'liberate-self', 'أَخَافُ':'fear'}
FORCED.update({'وَذَلَّتْ':'sh-be-fluent', 'أَثْرَوْا':'sh-become-rich', 'يَفْضُلُ':'sh-remain-profit',
               'الْيَمَنِ':'sh-yemen', 'نُهِبَ':'sh-plunder', 'يَغْنَوْا':'sh-live-place',
               'أَعَزُّ':'sh-mightier', 'أَبْلَغِهِمْ':'sh-eloquent', 'بِذَلِكَ':'that', 'سِرًّا':'secret',
               'حَسَنًا':'sh-good', 'بِالْبِرِّ':'sh-virtue', 'وَالْظَّنِّ':'sh-thought-n',
               'حَيَاتِكُمْ':'life-n', 'عَصْرٍ':'sh-era', 'تَعَرُّضٍ':'sh-exposure-n',
               'التَّلَفِ':'sh-ruin-n', 'أَتْلَفَهُ':'sh-destroy', 'وَشَقَّ':'sh-burden',
               'لَوْلَا':'sh-unless', 'وَلَوْلَا':'sh-unless', 'بَيَانًا':'sh-eloquence-n',
               'تِيهٍ':'sh-pride-tiih', 'وَسِعَ':'sh-encompass', 'وَالْهَلَاكِ':'sh-destruction',
               'الْعَمَلُ':'deed', 'يَسْتَوِي':'sh-equal', 'صَالِحٍ':'salih', 'الْأَوَّلُونَ':'first',
               'أَغْنَاهُ':'sh-enrich', 'يُرْضِي':'sh-make-pleased', 'أَعْجَبَكَ':'sh-make-marvel',
               'فَكَثَّرَكُمْ':'sh-multiply', 'وَأَفْهَمَهُمْ':'sh-show-understand',
               'فَأَسْقِطْ':'sh-fall-cause', 'أَخْذِ':'sh-wages-taking', 'لَنُخْرِجَنَّكَ':'bring-out'})
FORCED['وَالْيَقِينِ']='sh-certainty-n'
FORCED['تُوعِدُونَ']='sh-threaten-iv'

def choose(ids, vocal):
    if {'sh-diminution','sh-withhold'} <= set(ids): return 'sh-diminution' if 'بَخْس' in vocal else 'sh-withhold'
    return h.choose(ids, vocal)

def resolve(vocal):
    if vocal in FORCED: return h.forced_resolve(vocal, FORCED[vocal])
    return h.resolve(vocal)

PASSIVE = {'أُنْفِقَ':('was spent','خرچ کیا گیا'), 'فَسُرِقَ':('was stolen','چوری ہوا'),
           'نُهِبَ':('was plundered','لوٹ لیا گیا'), 'سُلِّطَ':('was given power over','مسلط کیا گیا'),
           'يُفْتَرَى':('is fabricated','گھڑا جاتا ہے')}

def light(vocal):
    if vocal in PASSIVE: return re.sub(r'[ًٌٍ]$', '', vocal)
    if b.bare(vocal) in b.SELECTIVE: return b.SELECTIVE[b.bare(vocal)]
    ident,_=resolve(vocal)
    if ident in ('sh-virtue','sh-thought-n'):
        return b.bare(vocal).replace('بر','بِرّ').replace('ظن','ظَنّ')
    return ''.join(c for c in vocal if not b.MARKS.fullmatch(c) or c=='\u0651')

def make_line(vocal, ident, pages):
    result=b.make_line(vocal, ident, pages)
    for index, token in enumerate(result['tokens']):
        if token['vocalized'] in PASSIVE:
            en, ur = PASSIVE[token['vocalized']]
            token['usage']=b.bilingual(en+'; passive', ur+'؛ مجہول')
        rest=b.bare(''.join(t['vocalized']+t['after'] for t in result['tokens'][index+1:])).lstrip()
        target=None
        if token['vocalized']=='إِنْ' and rest.startswith('أريد إلا'): target='negation-in'
        if token['vocalized']=='وَإِنْ' and rest.startswith('نظنك'): target='sh-emphatic-in'
        if token['vocabularyId']=='what' and rest.startswith(('لكم من إله','أنا عليكم','حمله على','أريد أن أخالفكم','يكون لنا','نفقه','أنت علينا','أنت إلا','توفيقي إلا')):
            target='negation-ma'
        if target:
            token['vocabularyId']=target
            next(p for p in token['parts'] if p['role']=='stem')['vocabularyId']=target
    return result

def main():
    load_lexicon()
    b.choose, b.resolve, b.light = choose, resolve, light
    b.lexicon['negation-in'] = {'id': 'negation-in', 'partOfSpeech': 'particle', 'lemma': 'إِنْ', 'root': None, 'meanings': b.bilingual('not (with إلا)', 'نہیں؛ الا کے ساتھ نفی'), 'rootNote': b.bilingual('Function word.', 'حرف۔')}
    text = (ROOT / 'data/stories/07-shuaib.vocalized.txt').read_text(encoding='utf-8')
    refs = [(12, 111), (11, 84), (11, 85), (5, 100), (11, 86), (7, 85), (7, 86), (11, 87), (11, 88), (11, 91), (11, 92), (7, 88), (7, 88), (7, 89), (26, 185), (26, 186), (26, 187), (7, 91), (7, 92), (7, 93)]
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
            sections.append({'id': sid, 'number': int(number), 'sourceSectionNumber': int(number), 'title': heading['text'], 'titleVocalized': title,
                             'titleEnglish': english, 'titleTokens': heading['tokens'], 'lines': []})
        elif raw.startswith('@'):
            pages = [int(p) for p in raw[1:].split(',')]
        elif raw:
            section = sections[-1]
            section['lines'].append(make_line(raw, f"{section['id']}-l{len(section['lines'])+1:03d}", pages.copy()))
    template = json.loads((ROOT / 'data/stories/03-nooh.json').read_text(encoding='utf-8'))
    source = ROOT / 'books/Qisas Story 7 Sayyiduna Shuaib (AS).pdf'
    checksum = hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else json.loads(DEST.read_text(encoding='utf-8'))['source']['sha256']
    editorial = template['editorial'].copy()
    editorial.update({'method': 'Manual transcription checked against all nine rendered PDF pages; editorial grammatical vocalization and bilingual vocabulary.',
        'corrections': [],
        'notes': ['PDF page 1 is the cover (printed page 173); narrative PDF pages 2–9 correspond to printed pages 174–181.',
                  'All 14 printed chapters and deliberate repetitions are retained. Reading units are sentences or connected passages rather than physical PDF lines.',
                  'The Quran excerpts use modern imlai spelling and verified verse links.',
                  'Added vocalization, morphology and bilingual glosses are editorial preparation.'],
        'referenceSources': [{'label': 'Source story PDF', 'path': 'books/' + source.name}, {'label': 'Quran references', 'url': 'https://quran.com'}, {'label': 'Quranic Arabic Corpus', 'url': 'https://corpus.quran.com'}]})
    story = {k: template[k] for k in ('schemaVersion', 'language', 'direction', 'meaningLanguages')}
    story.update({'id': '07-shuaib', 'number': 7, 'titleEnglish': 'Shuaib and the People of Madyan', 'titleUrdu': 'حضرت شعیب اور اہل مدین',
        'description': b.bilingual('Read Shuaib’s call to faith, honest trade and fair weights and measures, in 14 chapters.', 'حضرت شعیب کی ایمان، دیانت دار تجارت اور پورے ناپ تول کی دعوت؛ ۱۴ ابواب۔'),
        'source': {'file': 'books/' + source.name, 'sha256': checksum, 'pdfPages': 9, 'coverPage': 1, 'printedPageRange': [174,181]},
        'editorial': editorial, 'sections': sections})
    for key, vocal in [('title', 'شُعَيْبٌ'), ('subtitle', 'قِصَّةُ سَيِّدِنَا شُعَيْبٍ')]:
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
