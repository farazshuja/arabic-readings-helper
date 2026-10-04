"""Build the reviewed Salih story into a self-contained static payload."""
import hashlib
import json
import re
import sys
import build_story as b
import build_hud as h
ROOT = b.ROOT
DEST = ROOT / 'data/stories/05-salih.json'

def load_lexicon():
    h.load_lexicon()
    for raw in (ROOT / 'data/stories/05-salih.lexicon.tsv').read_text(encoding='utf-8').splitlines():
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
    for ident, words in INFLECTIONS.items():
        for word in words.split():
            b.forms.setdefault(word, []).append(ident)
    b.lexicon['scent-wind']['meanings'] = b.bilingual('wind', 'ہوا')
    b.lexicon['one-night']['meanings'] = b.bilingual('one (day), in ذات يوم: one day', 'ذات یوم میں ایک دن')
    b.lexicon['fall']['meanings'] = b.bilingual('fall; befall', 'گرنا؛ پیش آنا')
    b.lexicon['occupation']['meanings'] = b.bilingual('occupation; preoccupation', 'مصروفیت؛ مشغلہ')
    b.lexicon['owner']['meanings'] = b.bilingual('companion', 'ساتھی')
    b.lexicon['paradise']['meanings'] = b.bilingual('garden; orchard', 'باغ')

INFLECTIONS = {
    'worship': 'عبدوا',
    'convey-iv': 'أبلغت', 'think': 'تظنون ظنوا', 'take': 'أخذت', 'obey': 'أطعتم تطيعون تطيعونني',
    'admire': 'أعجبت', 'wealthy': 'أغنياء أغنيائ', 'give': 'أوتوا', 'deity': 'إلها',
    'counsellor': 'ناصحين', 'love': 'تحبون', 'soil': 'ترابا', 'want': 'تريدون',
    'cease': 'تزالون يزل', 'live': 'تسكنون', 'be': 'تكونوا كنا كنتم', 'birth': 'تلد ولدت',
    'die': 'تموتون متم', 'cut-carve': 'تنحتون نحتوا', 'promise-v': 'توعدون',
    'empty': 'خالية', 'submit': 'خضعوا', 'go': 'ذهبت', 'hope': 'رجاؤ',
    'wise': 'رشيدا', 'throw-r': 'رما', 'ask': 'سألتم', 'way': 'سبيلا', 'succeed': 'ينجحون',
    'oppress': 'ظلموا', 'amazement': 'عجبا', 'great': 'عظيمة', 'drown': 'غرقت',
    'fear': 'خافوا', 'make-v': 'يصنعون', 'big': 'كبار كبارا', 'falsehood': 'كذبا',
    'needy': 'مسكينة', 'kill': 'نقتل', 'perish': 'هلكوا', 'refuse': 'أبوا',
    'strange': 'غريبة', 'flee': 'فرت', 'water': 'ماؤ', 'advise': 'نصحت',
    'corrupt': 'يفسدون', 'find': 'يجدوا', 'come-out': 'يخرجون', 'disobey': 'يعصي',
    'wait': 'ينتظران',
}


def choose(ids, vocal):
    keys = set(ids)
    if {'convey', 'convey-iv'} <= keys:
        return 'convey-iv' if 'أَبْلَغ' in vocal else 'convey'
    for ident in ('secure', 'whenever', 'to-what'):
        if ident in keys:
            return ident
    if 'crop-z' in keys and 'زَرْع' in vocal:
        return 'crop-z'
    for ident in ('err', 'be-soft', 'be-perplexed', 'migrate', 'recompense', 'standing', 'joy-delight', 'below'):
        if ident in keys:
            return ident
    if {'stone', 'room'} <= keys:
        return 'stone' if 'حَجَر' in vocal else 'room'
    if {'wealth', 'incline'} <= keys:
        return 'wealth' if 'مَالِ' in vocal else 'incline'
    if {'think', 'thought-n'} <= keys:
        return 'thought-n' if 'ظَنُّنَا' in vocal else 'think'
    if {'honour', 'ennoble'} <= keys:
        return 'ennoble' if 'شَرَّف' in vocal else 'honour'
    if {'more-lowly', 'abase'} <= keys:
        return 'abase' if 'أَذَلَّ' in vocal else 'more-lowly'
    if {'warn-caution', 'be-wary'} <= keys:
        return 'warn-caution' if 'يُحَذِّر' in vocal else 'be-wary'
    if {'count', 'promise-v'} <= keys:
        return 'promise-v' if 'يَعِد' in vocal else 'count'
    if 'salih' in keys:
        return 'salih'
    plain = vocal.replace('ّ', '')
    if 'come-out' in keys:
        return 'come-out'
    if {'injustice', 'oppress'} <= keys and 'ظُلْم' in plain:
        return 'injustice'
    for ident, pattern in [('blessing', 'نِعَم'), ('eating-n', 'أَكْل'), ('drinking-n', 'شُرْب'), ('sickness', 'مَرَض'), ('saying-n', 'قَوْل'), ('friend', 'صَدِيق')]:
        if ident in keys and pattern in plain:
            return ident
    if 'oppress' in keys and 'يَظْلِم' in vocal:
        return 'oppress'
    for ident in ('aad', 'water-spring', 'permission', 'bone', 'honoured'):
        if ident in keys:
            return ident
    if 'birth' in keys and vocal == 'وُلِدَ':
        return 'birth'
    if 'joy' in keys and 'فَرَحًا' in vocal:
        return 'joy'
    if 'play-n' in keys and 'لَعِب' in vocal.replace('ّ', ''):
        return 'play-n'
    if {'wonder', 'marvel'} <= keys:
        return 'wonder' if 'تَعَجَّب' in vocal else 'marvel'
    return h.choose(ids, vocal)

def resolve(vocal):
    if vocal == 'لِيُخْرِجَهُمْ':
        return 'bring-out', [{'surfaceBare': 'ل', 'vocabularyId': 'for-to', 'role': 'prefix'},
                             {'surfaceBare': 'يخرج', 'vocabularyId': 'bring-out', 'role': 'stem'},
                             {'surfaceBare': 'هم', 'vocabularyId': 'them', 'role': 'suffix'}]
    if b.bare(vocal) == 'ولئن':
        return 'if', [{'surfaceBare': 'و', 'vocabularyId': 'and', 'role': 'prefix'}, {'surfaceBare': 'ل', 'vocabularyId': 'emphasis', 'role': 'prefix'}, {'surfaceBare': 'ئن', 'underlying': 'إِنْ', 'vocabularyId': 'if', 'role': 'stem'}]
    return h.resolve(vocal)

def light(vocal):
    ident, _ = resolve(vocal)
    if vocal in PASSIVE:
        return PASSIVE[vocal][0]
    if vocal == 'وُلِدَ':
        return 'وُلِد'
    if vocal == 'يُقَالُ':
        return 'يُقال'
    if ident == 'knowledge':
        return b.bare(vocal).replace('علم', 'عِلْم')
    if ident == 'mention-n':
        return b.bare(vocal).replace('ذكر', 'ذِكْر')
    if ident == 'angel':
        return b.bare(vocal).replace('ملك', 'مَلَك')
    if ident == 'king':
        return b.bare(vocal).replace('ملوك', 'مُلوك')
    if ident == 'secure':
        return b.bare(vocal).replace('آمن', 'آمِن')
    if ident == 'age':
        return b.bare(vocal).replace('سن', 'سِنّ')
    for lexeme, bare_stem, marked in [('aad', 'عاد', 'عَاد'), ('friend', 'صديق', 'صَديق'),
                                     ('blessing', 'نعم', 'نِعَم'), ('drinking-n', 'شرب', 'شُرْب'),
                                     ('sickness', 'مرض', 'مَرَض'), ('bone', 'عظم', 'عَظْم'),
                                     ('saying-n', 'قول', 'قَوْل')]:
        if ident == lexeme:
            return b.bare(vocal).replace(bare_stem, marked)
    return ''.join(c for c in vocal if not b.MARKS.fullmatch(c) or c == '\u0651')

PASSIVE = {'وُلِدَ': ('وُلِد', 'was born', 'پیدا ہوا'),
           'أُوتُوا': ('أُوتوا', 'were given', 'دیے گئے'),
           'تُوعَدُونَ': ('تُوعَدون', 'you are promised', 'تم سے وعدہ کیا جاتا ہے'),
           'نُحِرَتْ': ('نُحِرَت', 'was slaughtered', 'ذبح کی گئی'),
           'وَدُهِشُوا': ('ودُهِشوا', 'were astonished', 'حیران ہو گئے')}


def make_line(vocal, ident, pages):
    result = b.make_line(vocal, ident, pages)
    for token in result['tokens']:
        if token['vocalized'] in PASSIVE:
            _, en, ur = PASSIVE[token['vocalized']]
            token['usage'] = b.bilingual(en + '; passive', ur + '؛ مجہول')
        if token['vocalized'] in ('وُلِدَ', 'يُقَالُ'):
            token['usage'] = b.bilingual('was born; passive' if token['vocalized'] == 'وُلِدَ' else 'is called; passive', 'پیدا ہوا؛ مجہول' if token['vocalized'] == 'وُلِدَ' else 'کہا جاتا ہے؛ مجہول')
        if token['vocalized'] == 'إِنْ' and ('إِنْ أَجْرِيَ إِلَّا' in vocal or '﴿إِنْ هِيَ إِلَّا' in vocal or '﴿إِنْ هُوَ إِلَّا' in vocal):
            token['vocabularyId'] = 'negation-in'
            token['parts'][-1]['vocabularyId'] = 'negation-in'
        if token['vocabularyId'] == 'what' and any(x in vocal for x in ('مَا لَكُمْ', 'مَا أَعْجَبَتْهُمْ', 'مَا عِنْدَهُ', 'مَا لَهُ', 'مَا هَذَا إِلَّا', 'مَا نَحْنُ', 'مَا نَالَ', 'مَا أَسْأَلُكُمْ', 'مَا أَنْتَ إِلَّا', 'مَا عِنْدَنَا')):
            token['vocabularyId'] = 'negation-ma'
            next(p for p in token['parts'] if p['role'] == 'stem')['vocabularyId'] = 'negation-ma'
        if token['vocalized'] in ('مِسْكِينٌ', 'مِسْكِينَةٌ'):
            token['usage'] = b.bilingual('poor fellow; a pitying or mocking description in the opponents’ speech', 'بیچارہ؛ مخالفین کے کلام میں ترحم یا طنز کا اظہار')
        if token['vocalized'] == 'وَسَلَّمَ':
            token['usage'] = b.bilingual('grant peace (in the blessing on the Prophet)', 'سلامتی عطا فرمائے؛ نبی پر درود کے الفاظ میں')
    return result

def main():
    load_lexicon()
    b.choose, b.resolve, b.light = choose, resolve, light
    b.lexicon['negation-in'] = {'id': 'negation-in', 'partOfSpeech': 'particle', 'lemma': 'إِنْ', 'root': None, 'meanings': b.bilingual('not (with إلا)', 'نہیں؛ الا کے ساتھ نفی'), 'rootNote': b.bilingual('Function word.', 'حرف۔')}
    text = (ROOT / 'data/stories/05-salih.vocalized.txt').read_text(encoding='utf-8')
    refs = [(10,44),(7,73),(23,33),(23,34),(23,35),(23,36),(23,37),(23,38),(26,145),(26,153),(26,154),(11,64),(11,65),(7,79),(11,68)]
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
            sections.append({'id': sid, 'number': int(number), 'sourceSectionNumber': int(number) + 11, 'title': heading['text'], 'titleVocalized': title,
                             'titleEnglish': english, 'titleTokens': heading['tokens'], 'lines': []})
        elif raw.startswith('@'):
            pages = [int(p) for p in raw[1:].split(',')]
        elif raw:
            section = sections[-1]
            section['lines'].append(make_line(raw, f"{section['id']}-l{len(section['lines'])+1:03d}", pages.copy()))
    template = json.loads((ROOT / 'data/stories/03-nooh.json').read_text(encoding='utf-8'))
    source = ROOT / 'books/Qisas Story 5 Sayyiduna Salih (AS).pdf'
    checksum = hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else json.loads(DEST.read_text(encoding='utf-8'))['source']['sha256']
    editorial = template['editorial'].copy()
    editorial.update({'method': 'Manual transcription checked against all 12 rendered PDF pages; editorial grammatical vocalization and bilingual vocabulary.',
        'corrections': [],
        'notes': ['Printed pages 78–88 correspond to PDF pages 2–12; the cover is printed page 77. sourcePages uses one-based PDF pages.',
                  'The PDF continues its previous chapter numbering (12–24); sections are numbered 1–13 in this standalone story, with sourceSectionNumber retained.',
                  'Reading units are sentences or short connected passages rather than physical PDF lines; deliberate repetition is retained.',
                  'The source uses Quran 23:33–38 in the opponents’ speech; the Quran passage does not name that people. The source narrative and actual verse links are retained.',
                  'The final hadith is retained as printed, including the explanatory من after حذرا; a parallel text is recorded in referenceSources (Sahih Muslim 2980b).',
                  'The ﷺ symbol is expanded to صلى الله عليه وسلم for clickable word-by-word reading.',
                  'Added vocalization and morphology are editorial preparation, not a certified edition.'],
        'referenceSources': [{'label': 'Source story PDF', 'path': 'books/' + source.name}, {'label': 'Quran references', 'url': 'https://quran.com'}, {'label': 'Quranic Arabic Corpus', 'url': 'https://corpus.quran.com'}, {'label': 'Sahih Muslim 2980b: visiting the dwellings of Thamud', 'url': 'https://sunnah.com/muslim:2980b'}]})
    story = {k: template[k] for k in ('schemaVersion', 'language', 'direction', 'meaningLanguages')}
    story.update({'id': '05-salih', 'number': 5, 'titleEnglish': 'The She-Camel of Thamud', 'titleUrdu': 'قوم ثمود کی اونٹنی',
        'description': b.bilingual('Read about Salih’s call to Thamud and the she-camel, in 13 sections.', 'حضرت صالح کی قوم ثمود کو دعوت اور اونٹنی کی کہانی؛ ۱۳ حصے۔'),
        'source': {'file': 'books/' + source.name, 'sha256': checksum, 'pdfPages': 12, 'coverPage': 1, 'printedPageRange': [78,88]},
        'editorial': editorial, 'sections': sections})
    for key, vocal in [('title', 'نَاقَةُ ثَمُودَ'), ('subtitle', 'قِصَّةُ سَيِّدِنَا صَالِحٍ')]:
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
