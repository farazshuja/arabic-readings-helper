"""Build the reviewed Hud story into a self-contained static payload."""
import hashlib
import json
import re
import sys
import build_story as b
import build_nooh as n
ROOT = b.ROOT
DEST = ROOT / 'data/stories/04-hud.json'

def load_lexicon():
    n.load_lexicon()
    for raw in (ROOT / 'data/stories/04-hud.lexicon.tsv').read_text(encoding='utf-8').splitlines():
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

INFLECTIONS = {
    'believe-faith': 'أؤمن تؤمن يؤمنون', 'see': 'رأيتم يرون', 'corrupt': 'أفسدو',
    'abandon': 'نترك', 'some': 'بعضا', 'bring-come': 'تأتي', 'fear': 'تخافون تخافونني نخاف',
    'associate': 'تشركون', 'fill': 'تملأ يملؤون', 'possess': 'تملك تملكون',
    'look': 'تنظر', 'beautiful': 'جميلة', 'stone': 'حجرا', 'animal': 'حيوانا',
    'come-out': 'خرجت', 'man': 'رجالا', 'be-content': 'رضوا', 'hear': 'سمعو نسمع',
    'severe': 'شديدة', 'evil': 'شرا', 'rejoice': 'فرحوا', 'palace': 'قصرا قصورا',
    'disbelieve': 'كفروا', 'dog': 'كلبا', 'think': 'نظن', 'wealth': 'مالا', 'place': 'مكانا',
    'understand': 'نفهم', 'wait': 'ننتظر ينتظرون', 'carry-v': 'تحمل',
    'forget': 'نسوا نسيت', 'perish': 'هلكت', 'build': 'يبنون', 'answer-v': 'يجيبون',
    'live': 'يسكنون', 'thank': 'يشكروا', 'reason': 'يعقلون',
    'friend': 'صديق', 'blessing': 'نعم', 'saying-n': 'قول',
    'overcome': 'يغلبون', 'high': 'عالية', 'afflict': 'أصاب', 'oppress': 'يظلم يظلمون',
}

def choose(ids, vocal):
    keys = set(ids)
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
    return n.choose(ids, vocal)

def resolve(vocal):
    return n.resolve(vocal)

def light(vocal):
    ident, _ = resolve(vocal)
    if vocal == 'وُلِدَ':
        return 'وُلِد'
    if vocal == 'يُقَالُ':
        return 'يُقال'
    if ident == 'knowledge':
        return b.bare(vocal).replace('علم', 'عِلْم')
    if ident == 'mention-n':
        return b.bare(vocal).replace('ذكر', 'ذِكْر')
    for lexeme, bare_stem, marked in [('aad', 'عاد', 'عَاد'), ('friend', 'صديق', 'صَديق'),
                                     ('blessing', 'نعم', 'نِعَم'), ('drinking-n', 'شرب', 'شُرْب'),
                                     ('sickness', 'مرض', 'مَرَض'), ('bone', 'عظم', 'عَظْم'),
                                     ('saying-n', 'قول', 'قَوْل')]:
        if ident == lexeme:
            return b.bare(vocal).replace(bare_stem, marked)
    return ''.join(c for c in vocal if not b.MARKS.fullmatch(c) or c == '\u0651')

def make_line(vocal, ident, pages):
    result = b.make_line(vocal, ident, pages)
    for token in result['tokens']:
        if token['vocalized'] in ('وُلِدَ', 'يُقَالُ'):
            token['usage'] = b.bilingual('was born; passive' if token['vocalized'] == 'وُلِدَ' else 'is called; passive', 'پیدا ہوا؛ مجہول' if token['vocalized'] == 'وُلِدَ' else 'کہا جاتا ہے؛ مجہول')
        if token['vocalized'] == 'إِنْ' and 'إِنْ أَجْرِيَ إِلَّا' in vocal:
            token['vocabularyId'] = 'negation-in'
            token['parts'][-1]['vocabularyId'] = 'negation-in'
        if token['vocabularyId'] == 'what' and any(x in vocal for x in ('مَا عَلِمُوا', 'مَا رَأَى', 'مَا سَمِعَ', 'مَا عِنْدَكَ', 'مَا لَكُمْ', 'مَا زَالَ')):
            token['vocabularyId'] = 'negation-ma'
            next(p for p in token['parts'] if p['role'] == 'stem')['vocabularyId'] = 'negation-ma'
    return result

def main():
    load_lexicon()
    b.choose, b.resolve, b.light = choose, resolve, light
    b.lexicon['negation-in'] = {'id': 'negation-in', 'partOfSpeech': 'particle', 'lemma': 'إِنْ', 'root': None, 'meanings': b.bilingual('not (with إلا)', 'نہیں؛ الا کے ساتھ نفی'), 'rootNote': b.bilingual('Function word.', 'حرف۔')}
    text = (ROOT / 'data/stories/04-hud.vocalized.txt').read_text(encoding='utf-8')
    refs = [(7,65),(7,66),(7,67),(7,68),(11,29),(7,69),(11,54),(11,55),(11,56),(67,26),(11,43),(11,60)]
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
            sections.append({'id': sid, 'number': int(number), 'title': heading['text'], 'titleVocalized': title,
                             'titleEnglish': english, 'titleTokens': heading['tokens'], 'lines': []})
        elif raw.startswith('@'):
            pages = [int(p) for p in raw[1:].split(',')]
        elif raw:
            section = sections[-1]
            section['lines'].append(make_line(raw, f"{section['id']}-l{len(section['lines'])+1:03d}", pages.copy()))
    template = json.loads((ROOT / 'data/stories/03-nooh.json').read_text(encoding='utf-8'))
    source = ROOT / 'books/Qisas Story 4 Sayyiduna Hud (AS).pdf'
    checksum = hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else json.loads(DEST.read_text(encoding='utf-8'))['source']['sha256']
    editorial = template['editorial'].copy()
    editorial.update({'method': 'Manual transcription checked against all 11 rendered PDF pages; editorial grammatical vocalization and bilingual vocabulary.',
        'corrections': [
            {'sourcePages': [2], 'source': 'وكانت أولاد عاد تملأ البيوت', 'edited': 'وكان أولاد عاد يملؤون البيوت', 'reason': 'Masculine plural agreement for human children.'},
            {'sourcePages': [6], 'source': 'الذي ترمونه إليه بعظم', 'edited': 'الذي ترمون إليه بعظم', 'reason': 'Removed the redundant object pronoun; the intended sense is throwing a bone to the dog.'}],
        'notes': ['Printed pages 68–77 correspond to PDF pages 2–11; the cover is printed page 67. sourcePages uses one-based PDF pages.',
                  'Reading units are sentences or short connected passages rather than physical PDF lines; deliberate repetition is retained.',
                  'The source places Quran 11:29 (words of Nuh) and 67:26 (an address to Muhammad) in Hud’s dialogue. These narrative borrowings are retained and linked to their actual verses, rather than being reassigned to Hud verses.',
                  'Added vocalization and morphology are editorial preparation, not a certified edition.'],
        'referenceSources': [{'label': 'Source story PDF', 'path': 'books/' + source.name}, {'label': 'Quran references', 'url': 'https://quran.com'}, {'label': 'Quranic Arabic Corpus', 'url': 'https://corpus.quran.com'}]})
    story = {k: template[k] for k in ('schemaVersion', 'language', 'direction', 'meaningLanguages')}
    story.update({'id': '04-hud', 'number': 4, 'titleEnglish': 'The Storm', 'titleUrdu': 'حضرت ہود اور آندھی',
        'description': b.bilingual('Read about Hud’s call to Ad and the storm, in 11 sections.', 'حضرت ہود کی قوم عاد کو دعوت اور آندھی کی کہانی؛ ۱۱ حصے۔'),
        'source': {'file': 'books/' + source.name, 'sha256': checksum, 'pdfPages': 11, 'coverPage': 1, 'printedPageRange': [68,77]},
        'editorial': editorial, 'sections': sections})
    for key, vocal in [('title', 'الْعَاصِفَةُ'), ('subtitle', 'قِصَّةُ سَيِّدِنَا هُودٍ')]:
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
