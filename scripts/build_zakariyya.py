"""Build the reviewed Zakariyya story into a self-contained static payload."""
import hashlib
import json
import re
import sys
import build_story as b
import build_ayyub_yunus as h
import build_musa as m
ROOT = b.ROOT
DEST = ROOT / 'data/stories/10-zakariyya.json'

def load_lexicon():
    h.load_lexicon()
    for raw in (ROOT / 'data/stories/10-zakariyya.lexicon.tsv').read_text(encoding='utf-8').splitlines():
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

INFLECTIONS = {'zk-heir':'وارثين', 'hear':'اسمعوا', 'zk-presence':'لدنا',
 'mother':'أما', 'male':'ذكر', 'ds-bestow':'هب', 'birth':'ولد',
 'zk-foster-ii':'كفل', 'zk-deposit':'يودع', 'zk-weaken':'وهن',
 'bring-out':'يخرج', 'turn-towards':'يقبل', 'supplication':'دعاء'}
FORCED = {
 'الْأَذْكِيَاءِ':'clever', 'الْعُقَلَاءِ':'wise-minded', 'الْحَدَثِ':'zk-event',
 'الْحَيَّ':'zk-living', 'الْحَيِّ':'zk-living', 'حَيًّا':'zk-living',
 'الْمَيِّتِ':'zk-dead', 'الْمَيِّتَ':'zk-dead', 'الْخَالِصِ':'zk-sincere',
 'الرَّجِيمِ':'zk-accursed', 'الْكَفِّ':'zk-palm', 'النَّذْرِ':'zk-vow', 'نَذْرُ':'zk-vow',
 'نَذَرَتِ':'zk-vow-v', 'نَذَرْتُ':'zk-vow-v', 'الْهُدَى':'guidance-n',
 'بِالْحَنَانِ':'zk-compassion', 'وَالْحَنَانِ':'zk-compassion', 'وَحَنَانًا':'zk-compassion',
 'بَرٍّ':'zk-dutiful', 'وَبَرًّا':'zk-dutiful', 'وَالْبِرِّ':'zk-virtue',
 'بَكَّرَ':'zk-early', 'تَقِيٍّ':'zk-pious', 'تَقِيًّا':'zk-pious',
 'تَهَبُ':'ds-bestow', 'وَتَهَبُ':'ds-bestow', 'يَهَبَ':'ds-bestow',
 'حَسَنٍ':'sh-good', 'حَسَنًا':'sh-good', 'ظُنُونَ':'thought-n', 'عَجَلٍ':'m-hurry',
 'لِوَالِدِهِ':'zk-parent', 'بِوَالِدَيْهِ':'zk-parent', 'بِالْوَالِدَيْنِ':'zk-parent',
 'وَأَبْطَلَ':'nullify', 'وَأَثَّرَ':'affect-ii', 'وَأَعْلَى':'zk-exalted',
 'وَالتَّقْوَى':'zk-piety', 'وَالْقَوِيُّ':'strong', 'وَجَرَتِ':'run',
 'وَخَفْضِ':'zk-lowering', 'وَزَكَاةً':'zk-purity', 'وَكَذَّبَ':'deny-ii',
 'وَيَرِثُ':'inherit', 'يَرِثُهُ':'inherit', 'وَيَنْفَعَ':'ay-benefit',
 'كَثِيرٍ':'many', 'صَالِحٍ':'righteous', 'صَالِحَةً':'righteous',
 'الصَّالِحَةُ':'righteous', 'الصَّالِحَةِ':'righteous',
 'وَعَلَاهُ':'zk-rise', 'وَعَلَتْ':'zk-rise', 'تَدُلُّ':'zk-indicate',
 'يَحْيَى':'ds-yahya', 'الْعِلْمِ':'knowledge', 'وَالْعِلْمُ':'knowledge',
 'أَخْلَصَتْ':'zk-devote', 'وَأَخْلَصَتْ':'zk-devote', 'أَقْرَانِهِ':'zk-peer',
 'أَقْوَى':'zk-stronger', 'أَمَّنَتْ':'zk-amen', 'أُمًّا':'mother', 'الذَّكَرُ':'male',
 'أَبْكَمَ':'zk-mute', 'بِدُعَاءٍ':'supplication', 'رَضِيٍّ':'zk-pleasing',
 'طَيِّبَةً':'zk-good', 'ظُهُورِهِ':'zk-manifestation', 'عَصِيًّا':'zk-rebellious',
 'عَيْنٍ':'eye', 'عَيْنُهُ':'eye', 'فَتَقَبَّلَهَا':'accept', 'فَتَقَبَّلْ':'accept',
 'فَيُقْبِلُ':'turn-towards', 'قَدَّرَ':'consider-august', 'قُدْرَتِهِ':'power-ability',
 'هَبْ':'ds-bestow', 'وَطَوْرًا':'zk-turn', 'وَقُرْبِ':'zk-proximity',
 'وَتَقْدِيرًا':'zk-decree', 'وَكَفَّلَهَا':'zk-foster-ii', 'وَلِينِ':'zk-gentleness',
 'وَوَهَنَ':'zk-weaken', 'وَوُلِدَ':'birth', 'وُلِدَ':'birth',
 'وَيُخْرِجُ':'bring-out', 'يُخْرِجُ':'bring-out', 'يُودِعَ':'zk-deposit',
 'الْوَهَنُ':'zk-weakness',
}

def choose(ids, vocal):
    if 'what' in ids and 'ay-ma-exclamation' in ids: return 'what'
    if {'sh-diminution','sh-withhold'} <= set(ids): return 'sh-diminution' if 'بَخْس' in vocal else 'sh-withhold'
    return h.choose(ids, vocal)

def resolve(vocal):
    if vocal in FORCED: return m.forced_resolve(vocal, FORCED[vocal])
    return h.resolve(vocal)

PASSIVE = {'وَخُصَّ':('was specially endowed','خاص طور پر نوازا گیا'), 'يُولَدَ':('is born','پیدا ہوتا ہے'), 'وَيُولَدُ':('is born','پیدا ہوتا ہے'), 'وَخُلِقَ':('was created','پیدا کیا گیا'), 'وَوُلِدَ':('was born','پیدا ہوا'), 'وُلِدَ':('was born','پیدا ہوا'), 'يُبْعَثُ':('is raised again','دوبارہ اٹھایا جاتا ہے'), 'يُشَارُ':('is pointed to with admiration','تعریف کے ساتھ اس کی طرف اشارہ کیا جاتا ہے')}

def light(vocal):
    if vocal in PASSIVE: return re.sub(r'[ًٌٍ]$', '', vocal)
    ident,_=resolve(vocal)
    key=b.bare(vocal)
    if ident == 'sovereignty': return key.replace('ملك','مُلك')
    if ident in ('king','queen'): return key.replace('ملك','مَلِك').replace('ملوك','مُلوك')
    if ident == 'zk-virtue': return key.replace('بر','بِرّ')
    if ident == 'zk-dutiful': return key.replace('بر','بَرّ')
    if ident == 'male': return key.replace('ذكر','ذَكَر')
    if key in b.SELECTIVE: return b.SELECTIVE[key]
    return ''.join(c for c in vocal if not b.MARKS.fullmatch(c) or c=='\u0651')

def make_line(vocal, ident, pages):
    result=b.make_line(vocal, ident, pages)
    for index, token in enumerate(result['tokens']):
        if token['vocalized'] in PASSIVE:
            token['usage']=b.bilingual(PASSIVE[token['vocalized']][0]+'; passive', PASSIVE[token['vocalized']][1]+'؛ مجہول')
        usage = {
            'وَرَبَطَ': ('strengthened his heart; made him steadfast (ربط على قلب)', 'اس کے دل کو مضبوط کیا؛ اسے ثابت قدم رکھا'),
            'طَعَنَ': ('advanced in age (طعن في السن)', 'عمر رسیدہ ہوا'),
            'وَعَلَاهُ': ('grey hair spread over him', 'اس پر بڑھاپے کی سفیدی چھا گئی'),
            'وَجَرَتِ': ('it was customary (جرت العادة)', 'معمول تھا؛ دستور چلا آ رہا تھا'),
            'بِالْأَبَوَيْنِ': ('both parents', 'ماں باپ دونوں'),
            'لِأَبَوَيْهِ': ('for his two parents', 'اپنے ماں باپ دونوں کے لیے'),
            'بِوَالِدَيْهِ': ('towards his two parents', 'اپنے والدین کے ساتھ'),
            'بِالْوَالِدَيْنِ': ('towards both parents', 'والدین کے ساتھ'),
            'الْحُكْمَ': ('wisdom and sound judgment here', 'یہاں حکمت اور صحیح فیصلہ کرنے کی صلاحیت'),
            'وَأَنْبَتَهَا': ('caused her to grow up well', 'اس کی اچھی پرورش کی'),
            'نَبَاتًا': ('growth; upbringing here', 'یہاں نشوونما؛ پرورش'),
            'وَأَصْلَحْنَا': ('We made his wife fit to bear a child', 'ہم نے اس کی بیوی کو اولاد کے قابل بنا دیا'),
            'جَبَّارًا': ('arrogant; overbearing here', 'یہاں متکبر؛ سرکش'),
            'الْعَزِيزِ': ('the Almighty (Allah)', 'غالب؛ زبردست، اللہ تعالیٰ'),
            'وَلَوْنٌ': ('another kind of divine blessings here', 'یہاں الٰہی نعمتوں کی ایک اور قسم'),
        }
        if token['vocalized'] in usage: token['usage']=b.bilingual(*usage[token['vocalized']])
    return result

def main():
    load_lexicon()
    b.choose, b.resolve, b.light = choose, resolve, light
    b.lexicon['negation-in'] = {'id': 'negation-in', 'partOfSpeech': 'particle', 'lemma': 'إِنْ', 'root': None, 'meanings': b.bilingual('not (with إلا)', 'نہیں؛ الا کے ساتھ نفی'), 'rootNote': b.bilingual('Function word.', 'حرف۔')}
    text = (ROOT / 'data/stories/10-zakariyya.vocalized.txt').read_text(encoding='utf-8')
    refs = [(3,35),(3,36),(3,37),(3,38),(3,41),(21,89),(21,90),(19,12),(19,13),(19,14),(19,15)]
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
    source = ROOT / 'books/Qisas Story 10 Sayyiduna Zakariyya (AS).pdf'
    checksum = hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else json.loads(DEST.read_text(encoding='utf-8'))['source']['sha256']
    editorial = template['editorial'].copy()
    editorial.update({'method': 'Manual transcription checked against all six rendered PDF pages; editorial grammatical vocalization and bilingual vocabulary.',
        'corrections': [],
        'notes': ['PDF page 1 is the cover (printed page 201); narrative PDF pages 2–6 correspond to printed pages 202–206.',
                  'All eight printed chapters are retained, including Maryam’s care and Yahya’s upbringing.',
                  'Quran passages are split at verse boundaries and use modern imlai spelling with verified verse links.',
                  'Added vocalization, morphology and bilingual glosses are editorial preparation.'],
        'referenceSources': [{'label': 'Source story PDF', 'path': 'books/' + source.name}, {'label': 'Quran references', 'url': 'https://quran.com'}, {'label': 'Quranic Arabic Corpus', 'url': 'https://corpus.quran.com'}]})
    story = {k: template[k] for k in ('schemaVersion', 'language', 'direction', 'meaningLanguages')}
    story.update({'id': '10-zakariyya', 'number': 10, 'titleEnglish': 'Zakariyya', 'titleUrdu': 'حضرت زکریا',
        'description': b.bilingual('Read Zakariyya’s prayer, Maryam’s care and Yahya’s upbringing, in eight chapters.', 'حضرت زکریا کی دعا، حضرت مریم کی پرورش اور حضرت یحییٰ کی تربیت؛ آٹھ ابواب۔'),
        'source': {'file': 'books/' + source.name, 'sha256': checksum, 'pdfPages': 6, 'coverPage': 1, 'printedPageRange': [202,206]},
        'editorial': editorial, 'sections': sections})
    for key, vocal in [('title', 'زَكَرِيَّا'), ('subtitle', 'قِصَّةُ سَيِّدِنَا زَكَرِيَّا')]:
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
