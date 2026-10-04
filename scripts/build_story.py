"""Build the reviewed story into a self-contained UTF-8 browser payload.

Run with Python 3; no third-party dependencies or network required.
Unknown words fail the build rather than receiving guessed dictionary cards.
"""
import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'data/stories/01-ibrahim.json'
MARKS = re.compile('[\u064b-\u0652\u0670]')
WORDS = re.compile('[\u0621-\u063a\u0641-\u0652\u0670]+')


def bare(text):
    return MARKS.sub('', unicodedata.normalize('NFC', text)).replace('ـ', '')


def bilingual(en, ur):
    return {'en': en, 'ur': ur}


lexicon = {}
forms = {}
for raw in (ROOT / 'data/stories/01-ibrahim.lexicon.tsv').read_text(encoding='utf-8').splitlines():
    if not raw or raw.startswith('#'):
        continue
    ident, pos, root, first, second, masdar, en, ur, extra = raw.split('|')
    entry = {'id': ident, 'partOfSpeech': pos, 'lemma': first,
             'root': None if root == '-' else root, 'meanings': bilingual(en, ur)}
    if pos == 'verb':
        entry['verb'] = {'madi': first, 'mudari': None if second == '-' else second,
                         'masdar': [] if masdar == '-' else masdar.split('، ')}
        if second == '-':
            entry['formNote'] = bilingual('Defective verb: no regular present tense or verbal noun.',
                                         'فعل ناقص: عام مضارع اور مصدر استعمال نہیں ہوتے۔')
    elif pos in ('noun', 'adjective'):
        entry['noun'] = {'singular': first, 'plural': [] if second == '-' else second.split('، ')}
        if second == '-':
            entry['formNote'] = bilingual('No plural supplied for this sense: abstract, collective, or fixed expression.',
                                         'اس معنی میں جمع نہیں دی گئی: مجرد معنی، اسم جمع یا مقررہ ترکیب۔')
    if entry['root'] is None:
        entry['rootNote'] = bilingual('No Arabic derivational root assigned (proper name or function word).',
                                     'عربی اشتقاقی مادہ مقرر نہیں کیا گیا؛ اسم خاص یا حرف وغیرہ۔')
    lexicon[ident] = entry
    for form in [first, *([] if second == '-' else second.split('، ')), *extra.split()]:
        forms.setdefault(bare(form), []).append(ident)

# Function words and clitics are dictionary entries too, so every word is clickable.
for ident, lemma, pos, en, ur in [
    ('and', 'وَ', 'particle', 'and', 'اور'),
    ('so', 'فَ', 'particle', 'so; then', 'پس؛ پھر'),
    ('with-by', 'بِ', 'particle', 'with; by; in', 'سے؛ کے ساتھ؛ میں'),
    ('for-to', 'لِ', 'particle', 'for; to', 'کے لیے؛ کو'),
    ('as-like', 'كَ', 'particle', 'like; as', 'کی طرح'),
    ('question', 'أَ', 'particle', 'question marker', 'کیا؛ سوالیہ حرف'),
    ('future', 'سَ', 'particle', 'will (future marker)', 'عنقریب؛ مستقبل کی علامت'),
    ('article', 'الْ', 'particle', 'the (definite article)', 'حرف تعریف؛ مخصوص چیز کی علامت'),
    ('if', 'إِنْ', 'particle', 'if', 'اگر'),
    ('to-verb', 'أَنْ', 'particle', 'to; that (before a verb)', 'کہ؛ فعل کو مصدر کے معنی میں لانے والا حرف'),
    ('not-question', 'أَلَا', 'particle', 'do you not?; will you not?', 'کیا نہیں؟'),
    ('negation-ma', 'مَا', 'particle', 'not (past-tense negation here)', 'نہیں؛ ماضی کی نفی'),
    ('when-past', 'إِذْ', 'particle', 'when', 'جب'),
    ('him-it', 'هُ', 'pronoun', 'him; his; it; its', 'اسے؛ اس کا؛ مذکر'),
    ('her-it', 'هَا', 'pronoun', 'her; hers; it; its', 'اسے؛ اس کا؛ مؤنث'),
    ('them', 'هُمْ', 'pronoun', 'them; their', 'انہیں؛ ان کا'),
    ('both', 'هُمَا', 'pronoun', 'both of them; their (dual)', 'ان دونوں کو؛ ان دونوں کا'),
    ('you-attached', 'كَ', 'pronoun', 'you; your (masculine singular)', 'تمہیں؛ تمہارا؛ مذکر واحد'),
    ('you-plural', 'كُمْ', 'pronoun', 'you; your (plural)', 'تم سب کو؛ تم سب کا'),
    ('us', 'نَا', 'pronoun', 'us; our', 'ہمیں؛ ہمارا'),
    ('me', 'نِي', 'pronoun', 'me', 'مجھے'),
    ('my', 'ي', 'pronoun', 'my; me (after a preposition)', 'میرا؛ حرف جر کے بعد مجھے'),
]:
    lexicon[ident] = {'id': ident, 'partOfSpeech': pos, 'lemma': lemma,
                      'root': None, 'meanings': bilingual(en, ur),
                      'rootNote': bilingual('Function word or attached pronoun; no derivational root.',
                                            'حرف یا متصل ضمیر؛ اشتقاقی مادہ نہیں۔')}
    if ident in ('when-past', 'not-question', 'for-to', 'with-by', 'as-like'):
        forms[bare(lemma)] = [ident]

# Reviewed irregular/inflected stems; these are exact mappings, not a stemmer.
extra_forms = {
    'أب': 'father', 'أبو': 'father', 'آباء': 'father', 'أبت': 'father',
    'أخ': 'brother', 'أخو': 'brother', 'عالمين': 'world',
    'مسلمين': 'muslim', 'مسلمون': 'muslim', 'صابرين': 'patient',
    'أكسر': 'break', 'يسمعون': 'hear', 'يسجدوا': 'prostrate',
    'يهدين': 'guide', 'يسقين': 'give-water', 'يشفين': 'heal', 'يحيين': 'give-life',
    'تتركن': 'abandon', 'اترك': 'abandon', 'ستجد': 'find', 'تجد': 'find',
    'آت': 'bring-come', 'أت': 'bring-come', 'إذ': 'when-past',
    'ألا': 'not-question',
    'اسألو': 'ask', 'حرقو': 'burn', 'بنا': 'build',
}
for key, value in extra_forms.items():
    forms[key] = [value]

for attached in ('ربي', 'ربنا', 'أبي', 'أبوه', 'أخوه', 'آباءنا', 'سيدي',
                 'تتركني', 'اتركني', 'ستجدني'):
    forms.pop(attached, None)

PREFIX = [('و', 'and'), ('ف', 'so'), ('أ', 'question'), ('س', 'future'),
          ('ب', 'with-by'), ('ل', 'for-to'), ('ك', 'as-like')]
SUFFIX = [('هما', 'both'), ('هم', 'them'), ('ها', 'her-it'), ('كم', 'you-plural'),
          ('نا', 'us'), ('ني', 'me'), ('ه', 'him-it'), ('ك', 'you-attached'), ('ي', 'my')]


def choose(ids, vocal):
    ids = list(dict.fromkeys(ids))
    if set(ids) == {'who', 'from'}:
        return 'who' if 'مَ' in vocal else 'from'
    if set(ids) == {'when-if', 'therefore'}:
        return 'therefore' if '\u064b' in vocal else 'when-if'
    if set(ids) == {'slaughter-n', 'slaughter'}:
        return 'slaughter-n' if 'بْ' in vocal else 'slaughter'
    if 'inna' in ids:
        return 'inna' if '\u0651' in vocal else 'if'
    if 'anna' in ids:
        return 'anna' if '\u0651' in vocal else 'to-verb'
    if len(ids) != 1:
        raise ValueError(f'Ambiguous lexeme: {vocal} => {ids}')
    return ids[0]


def resolve(vocal):
    """Find exact reviewed forms with transparent proclitic/enclitic decomposition."""
    key = bare(vocal)
    if key == 'لله':
        return 'allah', [
            {'surfaceBare': 'ل', 'vocabularyId': 'for-to', 'role': 'prefix'},
            {'surfaceBare': 'له', 'underlying': 'اللَّه', 'vocabularyId': 'allah', 'role': 'stem',
             'note': 'Contracted spelling of لِ + اللَّه.'}]
    if key == 'منا':
        return 'from', [
            {'surfaceBare': 'م', 'underlying': 'مِنْ', 'vocabularyId': 'from', 'role': 'stem'},
            {'surfaceBare': 'نا', 'underlying': 'نَا', 'vocabularyId': 'us', 'role': 'suffix',
             'note': 'The two nuns merge into the shadda in مِنَّا.'}]
    # Named words retain their lexical shape; grammatical endings are in vocalized.
    candidates = []

    def stem_match(stem, leading, trailing, cost):
        variants = [(stem, leading)]
        if stem.startswith('ال'):
            variants.append((stem[2:], leading + [('ال', 'article')]))
        if stem.startswith('لل'):
            variants.append((stem[2:], leading + [('ل', 'for-to'), ('ل', 'article')]))
        for body, pre in variants:
            if body in forms:
                candidates.append((cost, pre, body, forms[body], trailing))
            if trailing and body.endswith('ت') and body[:-1] + 'ة' in forms:
                candidates.append((cost + 1, pre, body, forms[body[:-1] + 'ة'], trailing))

    def visit(stem, leading, depth):
        stem_match(stem, leading, [], depth * 3)
        for suffix, ident in SUFFIX:
            if stem.endswith(suffix) and len(stem) > len(suffix):
                stem_match(stem[:-len(suffix)], leading, [(suffix, ident)], depth * 3 + 2)
        if depth < 3:
            for prefix, ident in PREFIX:
                if stem.startswith(prefix) and len(stem) > len(prefix) + 1:
                    visit(stem[len(prefix):], leading + [(prefix, ident)], depth + 1)
    visit(key, [], 0)
    if not candidates:
        raise ValueError(f'Unmapped word: {vocal} ({key})')
    candidates.sort(key=lambda x: x[0])
    _, pre, stem, ids, post = candidates[0]
    ident = choose(ids, vocal)
    parts = [{'surfaceBare': s, 'vocabularyId': i, 'role': 'prefix'} for s, i in pre]
    parts += [{'surfaceBare': stem, 'vocabularyId': ident, 'role': 'stem'}]
    parts += [{'surfaceBare': s, 'vocabularyId': i, 'role': 'suffix'} for s, i in post]
    return ident, parts


# Retain shadda generally; retain selected vowels where a lexical/passive reading
# would otherwise be ambiguous. The completely stripped text is provided too.
SELECTIVE = {
    'ملك': 'مَلِك', 'الملك': 'المَلِك', 'للملك': 'للمَلِك',
    'والملك': 'والمَلِك', 'ملوك': 'مُلوك',
    'يقال': 'يُقال', 'تؤمر': 'تُؤمَر', 'يغني': 'يُغني',
    'يحيي': 'يُحيي', 'أحيي': 'أُحيي', 'تحيي': 'تُحيي',
    'يميت': 'يُميت', 'أميت': 'أُميت', 'تميت': 'تُميت',
}


def light(vocal):
    key = bare(vocal)
    if key in SELECTIVE:
        return SELECTIVE[key]
    # Prefixes/suffixes are covered by testing the reviewed stem in resolve.
    ident, parts = resolve(vocal)
    if ident == 'king':
        return key.replace('ملك', 'مَلِك').replace('ملوك', 'مُلوك')
    if ident in ('give-life', 'cause-death', 'avail'):
        # Preserve the initial stem vowel only (active form IV vs other readings).
        chars = list(vocal)
        stem_start = sum(len(p['surfaceBare']) for p in parts if p['role'] == 'prefix')
        base_count = 0
        out = ''
        for c in chars:
            if not MARKS.fullmatch(c):
                out += c
                base_count += 1
            elif c == '\u0651' or base_count == stem_start + 1:
                out += c
        return out
    return ''.join(c for c in vocal if not MARKS.fullmatch(c) or c == '\u0651')


QUOTES = [
    ('ما لكم لا تنطقون', 37, 92),
    ('قالوا من فعل هذا بآلهتنا', 21, 59),
    ('قالوا سمعنا فتى يذكرهم يقال له إبراهيم', 21, 60),
    ('قالوا أأنت فعلت هذا بآلهتنا يا إبراهيم', 21, 62),
    ('قال بل فعله كبيرهم هذا فاسألوهم إن كانوا ينطقون', 21, 63),
    ('قالوا حرقوه وانصروا آلهتكم', 21, 68),
    ('يا نار كوني بردا وسلاما على إبراهيم', 21, 69),
    ('هذا ربي هذا أكبر', 6, 78),
    ('قالوا نعبد أصناما', 26, 71),
    ('هل يسمعونكم إذ تدعون', 26, 72),
    ('أو ينفعونكم أو يضرون', 26, 73),
    ('قالوا بل وجدنا آباءنا كذلك يفعلون', 26, 74),
    ('الذي خلقني فهو يهدين', 26, 78),
    ('والذي هو يطعمني ويسقين', 26, 79),
    ('وإذا مرضت فهو يشفين', 26, 80),
    ('والذي يميتني ثم يحيين', 26, 81),
    ('الذي يحيي ويميت', 2, 258),
    ('قال أنا أحيي وأميت', 2, 258),
    ('فإن الله يأتي بالشمس من المشرق فأت بها من المغرب', 2, 258),
    ('يا أبت لم تعبد ما لا يسمع ولا يبصر ولا يغني عنك شيئا', 19, 42),
    ('يا أبت لا تعبد الشيطان', 19, 44),
    ('سلام عليك', 19, 47),
    ('إني أرى في المنام أني أذبحك فانظر ماذا ترى', 37, 102),
    ('قال يا أبت افعل ما تؤمر ستجدني إن شاء الله من الصابرين', 37, 102),
    ('ربنا تقبل منا إنك أنت السميع العليم', 2, 127),
]


def make_line(vocal, line_id, pages):
    tokens = []
    hits = list(WORDS.finditer(vocal))
    text = vocal[:hits[0].start()] if hits else vocal
    for i, match in enumerate(hits):
        word = match.group()
        ident, parts = resolve(word)
        gap = vocal[match.end():hits[i+1].start() if i+1 < len(hits) else len(vocal)]
        reading = light(word)
        token = {'id': f'{line_id}-w{i+1:02d}', 'text': reading,
                 'textBare': bare(word), 'vocalized': word,
                 'vocabularyId': ident, 'parts': parts, 'after': gap}
        # Store occurrence-specific grammatical information where it affects meaning.
        if ident == 'say' and bare(word).lstrip('وف') == 'يقال':
            token['usage'] = bilingual('is called; passive', 'کہلاتا ہے؛ مجہول')
        if ident == 'command' and bare(word) == 'تؤمر':
            token['usage'] = bilingual('you are commanded; passive', 'تمہیں حکم دیا جاتا ہے؛ مجہول')
        if ident == 'therefore' and bare(word) == 'إذا':
            token['usage'] = bilingual('then; in that case (إذًا, not إذا)', 'تب؛ اس صورت میں؛ اذًا')
        if ident == 'what' and parts[-1]['surfaceBare'] == 'ما':
            # Explicitly mark the two narrative past-tense negations.
            rest = bare(vocal[match.end():]).lstrip()
            if rest.startswith(('نطقت', 'وجد', 'كان بيت')):
                token['vocabularyId'] = 'negation-ma'
                token['parts'][-1]['vocabularyId'] = 'negation-ma'
        tokens.append(token)
        text += reading + gap
    citations = []
    for quote in re.findall('﴿(.*?)﴾', vocal):
        qbare = bare(quote)
        found = [(s, a) for t, s, a in QUOTES if t == qbare]
        if not found:
            raise ValueError(f'Unreferenced Quran excerpt: {qbare}')
        s, a = found[0]
        citations.append({'type': 'quran', 'surah': s, 'ayah': a,
                          'excerptVocalized': quote,
                          'url': f'https://quran.com/{s}/{a}'})
    return {'id': line_id, 'sourcePages': pages, 'text': text, 'textBare': bare(vocal),
            'vocalized': vocal, 'leading': vocal[:hits[0].start()] if hits else vocal,
            'tokens': tokens, 'references': citations}


def main():
    sections = []
    pages = []
    for raw in (ROOT / 'data/stories/01-ibrahim.vocalized.txt').read_text(encoding='utf-8').splitlines():
        if raw.startswith('# '):
            number, title, en = raw[2:].split('|')
            sections.append({'id': f's{int(number):02d}', 'number': int(number),
                             'title': bare(title), 'titleVocalized': title,
                             'titleEnglish': en, 'lines': []})
        elif raw.startswith('@'):
            pages = [int(p) for p in raw[1:].split(',')]
        elif raw:
            section = sections[-1]
            line_id = f"{section['id']}-l{len(section['lines'])+1:03d}"
            section['lines'].append(make_line(raw, line_id, pages.copy()))
    source = ROOT / 'books/Qisas Story 1 Sayyiduna Ibrahim (AS).pdf'
    if source.is_file():
        source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    elif DEST.is_file():
        source_sha256 = json.loads(DEST.read_text(encoding='utf-8'))['source']['sha256']
    else:
        raise FileNotFoundError('Rebuilding requires either the source PDF or existing story JSON with its source checksum.')
    for section in sections:
        title_line = make_line(section['titleVocalized'], section['id'] + '-title', [])
        section['title'] = title_line['text']
        section['titleTokens'] = title_line['tokens']
    story = {
        'schemaVersion': '1.0.0', 'id': '01-ibrahim', 'number': 1,
        'language': 'ar', 'direction': 'rtl', 'meaningLanguages': ['en', 'ur'],
        'title': 'من كسر الأصنام', 'titleVocalized': 'مَنْ كَسَرَ الْأَصْنَامَ',
        'subtitle': 'قصة سيدنا إبراهيم', 'titleEnglish': 'Who broke the idols?',
        'titleUrdu': 'بت کس نے توڑے؟',
        'description': bilingual('A beginner reading story about Ibrahim, in 16 sections.',
                                 'حضرت ابراہیم کی کہانی؛ ابتدائی قارئین کے لیے ۱۶ حصے۔'),
        'source': {'file': 'books/' + source.name, 'sha256': source_sha256,
                   'pdfPages': 15, 'coverPage': 1, 'printedPageRange': [3, 17]},
        'editorial': {
            'status': 'prepared; specialist review recommended before publication',
            'method': 'Manual reconstruction checked against all 15 rendered PDF pages; editorial grammatical vocalization.',
            'readingTextPolicy': 'text retains shadda and selected disambiguating vowels; textBare removes all harakat. Hamza, alif madda and alif maqsura are letters and are preserved.',
            'vocalizationPolicy': 'Connected-reading grammatical endings are supplied, including case endings and sandhi vowels. At a pause the reader may omit the final short vowel. This is tashkil, not a syntactic i\u02bfrab analysis.',
            'quranPolicy': 'Only excerpts printed in the story are included. Standard modern imlai spelling is used, not a facsimile of Uthmani orthography or Quran recitation notation; references identify the verse.',
            'vocabularyPolicy': 'Meaning strings give the sense used in this story. Verbs use third-person masculine singular dictionary forms; masdar and plural arrays may list alternatives. Null roots and empty form arrays are intentional, with explanatory notes.',
            'contentPolicy': 'The source narrative is preserved; this is a reading resource, not independent historical or theological verification.',
            'corrections': [
                {'sourcePages': [3], 'source': 'ولأي شيء تضع لها الطعام والشراب.', 'edited': 'ولأي شيء تضع لها الطعام والشراب؟', 'reason': 'Question punctuation.'},
                {'sourcePages': [11], 'source': 'ووصل إبراهيم إلى مكة ونزل فيه.', 'edited': 'ووصل إبراهيم إلى مكة ونزل فيها.', 'reason': 'Feminine pronoun agrees with مكة.'},
                {'sourcePages': [11], 'source': 'إذا لا يضيعنا.', 'edited': 'إذًا لا يضيعنا.', 'reason': 'Consequence particle إذًا, not conditional إذا.'},
            ],
            'notes': [
                'Repeated words such as كثيرة كثيرة and مشهور مشهور are intentional beginner-story repetition, and are retained.',
                'Reading units follow sentences or short connected passages rather than PDF physical line wrapping.',
                'Foreign personal names have no fabricated Arabic triliteral roots. Traditional roots are supplied for Arabic vocabulary; etymological analyses of الله / اسم / نبي can vary.',
                'Review Arabic vowels, English/Urdu senses and morphology with a qualified Arabic editor before public release.',
            ],
            'referenceSources': [{'label': 'Source story PDF', 'path': 'books/' + source.name},
                                 {'label': 'Quran verse text and references', 'url': 'https://quran.com'},
                                 {'label': 'Quranic Arabic Corpus', 'url': 'https://corpus.quran.com'}]
        },
        'sections': sections, 'vocabulary': lexicon,
    }
    story['titleTokens'] = make_line(story['titleVocalized'], 'title', [1])['tokens']
    story['subtitleVocalized'] = 'قِصَّةُ سَيِّدِنَا إِبْرَاهِيمَ'
    subtitle_line = make_line(story['subtitleVocalized'], 'subtitle', [1])
    story['subtitleTokens'] = subtitle_line['tokens']
    story['subtitle'] = subtitle_line['text']
    lines = [line for s in sections for line in s['lines']]
    story['counts'] = {'sections': len(sections), 'lines': len(lines),
                       'wordOccurrences': sum(len(l['tokens']) for l in lines),
                       'vocabularyEntries': len(lexicon)}
    DEST.write_text(json.dumps(story, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    update_catalog(story, DEST.name)
    print(json.dumps(story['counts']))


def update_catalog(story, filename):
    path = ROOT / 'data/stories.json'
    index = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {'schemaVersion': '1.0.0', 'stories': []}
    item = {k: story[k] for k in ('id', 'number', 'title', 'titleVocalized', 'subtitle',
                                'titleEnglish', 'titleUrdu', 'description', 'counts')}
    item['file'] = 'stories/' + filename
    index['stories'] = sorted([s for s in index['stories'] if s['id'] != story['id']] + [item], key=lambda s: s['number'])
    path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
