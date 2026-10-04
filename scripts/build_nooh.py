"""Build the reviewed Nuh story into a self-contained static browser payload."""
import hashlib
import json
import re
import sys
import build_story as b
import build_yusuf as y

ROOT = b.ROOT
DEST = ROOT / 'data/stories/03-nooh.json'


def load_lexicon():
    y.load_additions()
    for raw in (ROOT / 'data/stories/03-nooh.lexicon.tsv').read_text(encoding='utf-8').splitlines():
        if not raw or raw.startswith('#'):
            continue
        ident, pos, root, first, second, masdar, en, ur, extra = raw.split('|')
        entry = {'id': ident, 'partOfSpeech': pos, 'lemma': first,
                 'root': None if root == '-' else root, 'meanings': b.bilingual(en, ur)}
        if pos == 'verb':
            entry['verb'] = {'madi': first, 'mudari': None if second == '-' else second,
                             'masdar': [] if masdar == '-' else masdar.split('، ')}
        elif pos in ('noun', 'adjective'):
            entry['noun'] = {'singular': first, 'plural': [] if second == '-' else second.split('، ')}
            if second == '-':
                entry['formNote'] = b.bilingual('Abstract, collective, diminutive or fixed use; no plural supplied for this sense.', 'مجرد معنی، اسم جمع، تصغیر یا مقررہ استعمال؛ اس معنی کی جمع نہیں دی گئی۔')
        if root == '-':
            entry['rootNote'] = b.bilingual('Proper name or function word; no Arabic derivational root assigned.', 'اسم خاص یا حرف؛ عربی اشتقاقی مادہ مقرر نہیں کیا گیا۔')
        b.lexicon[ident] = entry
        for form in [first, *([] if second == '-' else second.split('، ')), *extra.split()]:
            b.forms.setdefault(b.bare(form), []).append(ident)
    inflections = {
        'many': 'كثيرون', 'house': 'بيوتا', 'build': 'بنو', 'father': 'آبائنا آبائنا آباءنا',
        'rejoice': 'فرح', 'be-content': 'يرضى', 'cease': 'يزال',
        'enter': 'يدخلوا فليدخلوا', 'prostrate': 'يسجد يسجدون',
        'worship': 'اعبدوا يعبدوا نعبد أنعبد', 'associate': 'يشركون أنشرك',
        'take': 'يأخذ', 'strike': 'ضربو', 'love': 'يحبون', 'exalt': 'يعظمون',
        'die': 'ماتوا تموت نموت أموت', 'call': 'دعوا دعو يدعون دعو يدعو',
        'see': 'رأو رأوها يرون يرون يرون يرا رأينا', 'look': 'تنظرون ينظر',
        'harm': 'تضر', 'benefit': 'تنفع', 'name-v': 'سمو', 'deity': 'آلهة',
        'walk': 'يمشون تمشي', 'slaughter': 'يذبحون', 'reason': 'عقلوا يعقلوا',
        'talk-to': 'يكلمون', 'understand': 'يفهمون يفهم', 'eat': 'نأكل آكل يأكلون',
        'drink': 'نشرب أشرب', 'thirst': 'تعطش نعطش أعطش',
        'hunger': 'تجوع نجوع أجوع', 'ill': 'تمرض نمرض أمرض',
        'remember': 'تذكرون نذكر أذكر', 'find': 'يجدون وجدوا', 'friend': 'أصدقاء',
        'first': 'أولين', 'know-learn': 'يعلم', 'hand': 'أيدي',
        'abandon': 'يتركوا تترك', 'occupy': 'شغلت', 'obey': 'يطيعوا أطيعون',
        'help': 'ينصر', 'good-pure': 'طيب', 'come': 'جاءت', 'bring-come': 'أتا فأت',
        'be-pious': 'اتقو', 'cease': 'زال', 'forgive': 'تغفر', 'have-mercy': 'رحم ترحم',
        'be': 'كنت تكن أكن تكون', 'sit': 'تجلس جلست',
        'carry-v': 'يحمل', 'say': 'قيل', 'escape': 'ينج', 'son': 'ابني',
        'surround': 'أحاط', 'perish': 'هلك', 'weep': 'بكت',
        'son-child': 'أولادي', 'peace': 'سلام', 'small': 'صغر',
        'give-water': 'يسقي', 'trustworthy': 'أمينا', 'righteous': 'صالحا',
        'prophet': 'نبيا', 'poor': 'فقيرا', 'messenger': 'رسولا', 'torment': 'عذاب',
        'but': 'ولكن', 'one-only': 'واحدا', 'human': 'بشر بشرا', 'angel': 'ملكا',
        'needy': 'مساكين', 'lowly': 'أرذلون', 'trust': 'أمن',
        'delay': 'يؤخر', 'separate': 'حال', 'prostrating': 'سجدا',
    }
    for ident, words in inflections.items():
        for word in words.split():
            b.forms.setdefault(word, []).append(ident)
    extra = {
        'night': 'ليلا', 'morning': 'صباح', 'truthful': 'صادقين', 'polytheist': 'مشركين',
        'door': 'بابا', 'ask': 'تسألن يسألون', 'know': 'تعرفون', 'make': 'جعلوا',
        'remember': 'ذكروا يذكرون', 'spouse': 'زوجا', 'hear': 'سمعت', 'anger-n': 'غضبا',
        'big': 'كبيرة', 'satan': 'شيطان', 'protector': 'أولياؤ', 'one-only': 'واحدة',
        'build': 'بنوا', 'journey': 'سارت', 'put': 'وضعو', 'cultivate': 'يزرعون',
        'reflect': 'يفكروا', 'look': 'ينظرون', 'before': 'قبل',
    }
    for ident, words in extra.items():
        for word in words.split():
            b.forms.setdefault(word, []).append(ident)
    b.SUFFIX.insert(0, ('هن', 'them-f'))
    b.lexicon['spouse']['meanings'] = b.bilingual('spouse; one of a pair; a pair here', 'زوج؛ جوڑے کا ایک فرد؛ یہاں جوڑا')
    b.lexicon['us']['meanings'] = b.bilingual('we; us; our (according to grammatical role)', 'ہم؛ ہمیں؛ ہمارا؛ نحوی کردار کے مطابق')
    # Common Story 1 vocabulary used here with ordinary, not divine-only senses.
    b.lexicon['friend']['lemma'] = 'صَدِيقٌ'
    b.lexicon['friend']['noun'] = {'singular': 'صَدِيقٌ', 'plural': ['أَصْدِقَاءُ']}
    b.lexicon['friend']['root'] = 'ص د ق'
    b.lexicon['friend']['meanings'] = b.bilingual('friend', 'دوست')
    b.lexicon['owner']['meanings'] = b.bilingual('companion; occupant (of the ark here)', 'ساتھی؛ یہاں کشتی میں سوار شخص')
    b.lexicon['lodge']['meanings'] = b.bilingual('bring down; send down', 'نازل کرنا؛ اتارنا')


def choose(ids, vocal):
    ids = list(dict.fromkeys(ids))
    keys = set(ids)
    plain = vocal.replace('\u0651', '')
    if {'before', 'kiss', 'accept-v'} & keys and len(keys) > 1:
        return 'before' if 'قَبْل' in plain else ('kiss' if 'قَبِّ' in vocal or 'قَبَّ' in vocal else 'accept-v')
    if {'son', 'little-son'} <= keys:
        return 'little-son' if 'بُنَيَّ' in vocal else 'son'
    if 'male' in keys and len(keys) > 1:
        if 'ذِكْر' in plain:
            return 'mention-n'
        return 'male' if 'ذَكَرًا' in vocal else 'remember'
    if {'drown-v', 'drown'} <= keys:
        return 'drown-v' if 'يُغْرِق' in vocal else 'drown'
    if {'occupy', 'occupation'} <= keys:
        return 'occupation' if 'شُغْل' in plain else 'occupy'
    pairs = [
        ('promise', 'promise-v', 'وَعْد', 'promise', 'promise-v'),
        ('idea', 'reflect', 'فِكْر', 'idea', 'reflect'),
        ('till', 'crop', 'حَرْث', 'crop', 'till'),
        ('live', 'needy', 'مَسَاكِين', 'needy', 'live'),
        ('work-v', 'deed', 'عَمَلٌ', 'deed', 'work-v'),
        ('provide', 'provision', 'رِزْق', 'provision', 'provide'),
        ('light-n', 'fire', 'نُور', 'light-n', 'fire'),
        ('head', 'chief', 'رُؤَسَاء', 'chief', 'head'),
        ('arm', 'hand', 'أَيْدِي', 'hand', 'arm'),
        ('delay', 'other', 'يُؤَخ', 'delay', 'other'),
        ('warner', 'warn', 'نَذِير', 'warner', 'warn'),
        ('promise-v', 'already', 'وَعَد', 'promise-v', 'already'),
        ('small', 'childhood', 'صِغَر', 'childhood', 'small'),
        ('year-am', 'general', 'عَامًا', 'year-am', 'general'),
        ('hold', 'needy', 'مَسَاكِين', 'needy', 'hold'),
        ('say', 'decrease', 'قَلَّ', 'decrease', 'say'),
        ('disbelieve', 'disbelief', 'كُفْر', 'disbelief', 'disbelieve'),
        ('grant', 'gift', 'أَعْطَى', 'grant', 'gift'),
        ('male', 'remember', 'ذَكَرًا', 'male', 'remember'),
        ('allah', 'allah-vocative', 'اللَّهُمَّ', 'allah-vocative', 'allah'),
        ('fill', 'notables', 'مَلَأَ', 'fill', 'notables'),
        ('dear', 'honour', 'شَرَف', 'honour', 'dear'),
        ('protect', 'preserver', 'حَفِيظ', 'preserver', 'protect'),
        ('state', 'separate', 'حَالَ', 'separate', 'state'),
    ]
    for a, c, pattern, yes, no in pairs:
        if {a, c} <= keys:
            matched = pattern in vocal or ('\u0651' not in pattern and pattern in plain)
            return yes if matched else no
    if {'trust', 'believe-faith'} <= keys:
        return 'believe-faith' if any(p in vocal for p in ('آمَن', 'آمَنْ', 'نُؤْمِن', 'يُؤْمِن')) else 'trust'
    if {'misguidance', 'error'} <= keys:
        return 'misguidance' if 'ضَلَالَة' in vocal else 'error'
    if {'angel', 'king', 'sovereignty'} & keys and 'مَلَائِكَة' in vocal:
        return 'angel'
    if 'jealousy' in keys and b.bare(vocal) == 'حسد':
        return 'jealousy'
    return y.choose(ids, vocal)


def resolve(vocal):
    key = b.bare(vocal)
    if key in ('إنا', 'وإنا', 'فإنا'):
        pre = [{'surfaceBare': key[0], 'vocabularyId': 'and' if key[0] == 'و' else 'so', 'role': 'prefix'}] if len(key) == 4 else []
        return 'inna', pre + [{'surfaceBare': 'إ', 'underlying': 'إِنَّ', 'vocabularyId': 'inna', 'role': 'stem'},
                             {'surfaceBare': 'نا', 'vocabularyId': 'us', 'role': 'suffix', 'note': 'Contracted إن + نا; we.'}]
    if vocal == 'لَمَا':
        return 'negation-ma', [{'surfaceBare': 'ل', 'vocabularyId': 'emphasis', 'role': 'prefix'},
                               {'surfaceBare': 'ما', 'vocabularyId': 'negation-ma', 'role': 'stem'}]
    if vocal == 'أَمَاتَ':
        return 'die', [{'surfaceBare': 'أ', 'vocabularyId': 'question', 'role': 'prefix'},
                       {'surfaceBare': 'مات', 'vocabularyId': 'die', 'role': 'stem'}]
    if vocal == 'وَلِي':
        return 'for-to', [{'surfaceBare': 'و', 'vocabularyId': 'and', 'role': 'prefix'},
                          {'surfaceBare': 'ل', 'vocabularyId': 'for-to', 'role': 'stem'},
                          {'surfaceBare': 'ي', 'vocabularyId': 'my', 'role': 'suffix'}]
    if key.startswith('لأنا'):
        return 'because', [{'surfaceBare': 'لأ', 'underlying': 'لِأَنَّ', 'vocabularyId': 'because', 'role': 'stem'},
                           {'surfaceBare': 'نا', 'vocabularyId': 'us', 'role': 'suffix', 'note': 'Contracted لأن + نا.'}]
    if key in ('أننا',):
        return 'anna', [{'surfaceBare': 'أن', 'vocabularyId': 'anna', 'role': 'stem'},
                        {'surfaceBare': 'نا', 'vocabularyId': 'us', 'role': 'suffix'}]
    return y.resolve(vocal)


PASSIVE = {'قِيلَ': ('قِيل', 'was said', 'کہا گیا'), 'وَقِيلَ': ('وقِيل', 'was said', 'کہا گیا'),
           'وَأُعْجِبَ': ('وأُعجِب', 'were impressed', 'متاثر ہوئے'),
           'تُعْبَدُ': ('تُعبَد', 'is worshipped', 'عبادت کی جاتی ہے'),
           'يُؤَخَّرُ': ('يُؤخَّر', 'is delayed', 'مؤخر کیا جاتا ہے')}


def light(vocal):
    ident, _ = resolve(vocal)
    if vocal in PASSIVE:
        return PASSIVE[vocal][0]
    if ident == 'male':
        return b.bare(vocal).replace('ذكر', 'ذَكَر')
    if ident == 'mention-n':
        return b.bare(vocal).replace('ذكر', 'ذِكْر')
    if ident == 'pride':
        return b.bare(vocal).replace('كبر', 'كِبْر')
    if ident == 'friend':
        return b.bare(vocal)
    if vocal in ('أَمَاتَ', 'لَمَا', 'فَإِنَّا', 'وَلِي'):
        return ''.join(c for c in vocal if not b.MARKS.fullmatch(c) or c == '\u0651')
    return y.light(vocal)


def make_line(vocal, ident, pages):
    result = b.make_line(vocal, ident, pages)
    for token, hit in zip(result['tokens'], b.WORDS.finditer(vocal)):
        word = token['vocalized']
        if word in PASSIVE:
            _, en, ur = PASSIVE[word]
            token['usage'] = b.bilingual(en + '; passive', ur + '؛ مجہول')
        tail = b.bare(vocal[hit.end():]).lstrip(' ،:!؟')
        if token['vocabularyId'] == 'what' and (tail.startswith(('عرف', 'عقلوا', 'تابوا', 'كان', 'آمن', 'سمع', 'يعبد', 'سبـق', 'سبق', 'سمعت', 'بكت', 'وعد', 'وجد', 'هذا إلا')) or word == 'أَمَا'):
            token['vocabularyId'] = 'negation-ma'
            next(p for p in token['parts'] if p['role'] == 'stem')['vocabularyId'] = 'negation-ma'
        if word == 'إِنْ' and 'إِنْ أَنَا إِلَّا' in vocal:
            token['vocabularyId'] = 'negation-in'
            token['parts'][-1]['vocabularyId'] = 'negation-in'
        if word == 'وَإِنْ' and 'وَإِنْ كَانَ ابْنَهُ' in vocal:
            token['usage'] = b.bilingual('even if he were his son; concessive condition', 'اگرچہ وہ اس کا بیٹا ہو؛ شرط میں رعایت')
        if token['vocabularyId'] == 'lowly':
            token['usage'] = b.bilingual('A contemptuous label used by Nuh’s opponents for poorer believers.', 'نوح کے مخالفین کا غریب اہل ایمان کے لیے تحقیر آمیز لفظ۔')
    return result


def main():
    load_lexicon()
    b.choose, b.resolve, b.light = choose, resolve, light
    b.lexicon['negation-in'] = {'id': 'negation-in', 'partOfSpeech': 'particle', 'lemma': 'إِنْ', 'root': None,
                               'meanings': b.bilingual('not (negation with إلا)', 'نہیں؛ الا کے ساتھ نفی'),
                               'rootNote': b.bilingual('Function word.', 'حرف۔')}
    text = (ROOT / 'data/stories/03-nooh.vocalized.txt').read_text(encoding='utf-8')
    refs = [(71,1),(11,25),(11,25),(23,24),(23,24),(7,59),(7,60),(7,61),(7,62),
            (26,111),(26,114),(26,115),(11,30),(46,11),(71,2),(71,3),(71,4),
            (11,36),(11,32),(11,38),(11,42),(11,43),(11,45),(11,46),(11,47),
            (11,44),(11,48),(37,79),(37,79)]
    quotes = re.findall('﴿(.*?)﴾', text)
    assert len(quotes) == len(refs), (len(quotes), len(refs))
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
    template = json.loads((ROOT / 'data/stories/02-yusuf.json').read_text(encoding='utf-8'))
    source = ROOT / 'books/Qisas Story 3 Sayyiduna Nooh (AS).pdf'
    checksum = hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else json.loads(DEST.read_text(encoding='utf-8'))['source']['sha256']
    editorial = template['editorial'].copy()
    editorial.update({'method': 'Manual transcription checked against all 19 rendered PDF pages; editorial grammatical vocalization and bilingual vocabulary.',
                      'corrections': [
                          {'sourcePages': [2], 'source': 'رجال كثير', 'edited': 'رجال كثيرون', 'reason': 'Regular plural adjective agreement for the beginner reading text.'},
                          {'sourcePages': [11], 'source': 'قوم اعبدوا الله', 'edited': 'يا قوم اعبدوا الله', 'reason': 'Expanded the vocative at the start of the quotation to the standard wording of Quran 7:59.'},
                          {'sourcePages': [11], 'source': 'قوم ليس بي ضلالة', 'edited': 'يا قوم ليس بي ضلالة', 'reason': 'Expanded the vocative to the standard wording of Quran 7:61.'},
                          {'sourcePages': [13], 'source': 'أن اعبدوا الله', 'edited': 'أنِ اعبدوا الله', 'reason': 'Connected-reading kasra to avoid consecutive sukuns, in Quran 71:3.'},
                      ],
                      'notes': ['Printed pages 46–63 correspond to PDF pages 2–19. sourcePages uses one-based PDF pages.',
                                'Intentional beginner-story repetition is retained, including the two final occurrences of Quran 37:79.',
                                'Reading units are sentences or short connected passages rather than physical PDF lines.',
                                'The opponents’ disparaging labels for poorer believers are explained in occurrence-specific bilingual notes.',
                                'The source narrative is preserved; added vocalization and morphology are editorial preparation, not a certified edition.'],
                      'referenceSources': [{'label': 'Source story PDF', 'path': 'books/' + source.name},
                                           {'label': 'Quran references', 'url': 'https://quran.com'},
                                           {'label': 'Quranic Arabic Corpus', 'url': 'https://corpus.quran.com'}]})
    story = {k: template[k] for k in ('schemaVersion', 'language', 'direction', 'meaningLanguages')}
    story.update({'id': '03-nooh', 'number': 3, 'titleEnglish': 'The Ark of Nuh', 'titleUrdu': 'حضرت نوح کی کشتی',
                  'description': b.bilingual('Read about Nuh’s call to his people, the ark, and the flood, in 22 sections.', 'حضرت نوح کی دعوت، کشتی اور طوفان کی کہانی؛ ۲۲ حصے۔'),
                  'source': {'file': 'books/' + source.name, 'sha256': checksum, 'pdfPages': 19, 'coverPage': 1, 'printedPageRange': [46,63]},
                  'editorial': editorial, 'sections': sections})
    for key, vocal in [('title', 'سَفِينَةُ نُوحٍ'), ('subtitle', 'قِصَّةُ سَيِّدِنَا نُوحٍ')]:
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
