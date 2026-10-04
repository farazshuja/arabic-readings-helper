"""Build the reviewed Dawood and Sulaiman story into a self-contained static payload."""
import hashlib
import json
import re
import sys
import build_story as b
import build_shuaib as h
import build_musa as m
ROOT = b.ROOT
DEST = ROOT / 'data/stories/08-dawood-sulaiman.json'

def load_lexicon():
    h.load_lexicon()
    for raw in (ROOT / 'data/stories/08-dawood-sulaiman.lexicon.tsv').read_text(encoding='utf-8').splitlines():
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
    b.lexicon['ds-excellent']['formNote'] = b.bilingual('Fixed verb of praise; no ordinary present tense or verbal noun.', 'فعل مدح؛ عام مضارع اور مصدر نہیں۔')

    for ident, words in INFLECTIONS.items():
        assert ident in b.lexicon, ident
        for word in words.split(): b.forms.setdefault(word, []).append(ident)

INFLECTIONS = {'work-v':'اعمل', 'ds-horse':'خيول', 'ds-devil':'شياطين', 'strong':'قوية', 'name':'سم', 'ds-news':'نبإ', 'surround':'تحط', 'wise-knowing':'حكيمة', 'ds-shrewdness':'دهائ', 'chief':'رؤسائ', 'eye':'عيني', 'rule':'احكم', 'give':'أوتيت', 'sh-read':'اقرؤوا', 'judge':'حكام حاكمة', 'swerve':'يزغ', 'bring-come':'آتي', 'ds-eloquent':'أبلغ', 'surround':'تحط أحطت', 'ds-soften':'أل', 'ds-bestow':'وهبنا', 'ds-excellent':'نعم', 'ds-make-understand':'فهمنا', 'he':'هو'}
FORCED = {'أَحْيَانًا':'sometimes', 'أَكْبَرُ':'greater', 'إِلَى':'to', 'وَإِلَى':'to', 'التِّيهُ':'sh-pride-tiih', 'الْجِنِّ':'jinn', 'وَالْجِنِّ':'jinn', 'الْخَطَأَ':'ds-error', 'الْكُتُبِ':'book', 'الْكَرْمُ':'ds-vineyard','الْكَرْمَ':'ds-vineyard','الْكَرْمِ':'ds-vineyard','كَرْمٌ':'ds-vineyard', 'الْمُرْسَلُونَ':'ds-envoy','مُرْسَلٍ':'ds-envoy', 'بَسْطٍ':'ds-expansion','بِهَدِيَّتِكُمْ':'ds-gift', 'تَجْرِي':'run','تَحَدَّثَ':'ds-talk','يَتَحَدَّثُ':'ds-talk','تَطَّلِعْ':'ascend-observe','جِدٌّ':'seriousness','جُلَسَاءِ':'meeting-companion','جَهِلَهُ':'ignorant-v','ذَاتَ':'possessor','طَرْفُكَ':'ds-glance','ظَلَمْتُ':'oppress','غَنِيٌّ':'wealthy','فَأَنْكَرَ':'deny-disapprove','فَضَّلَنَا':'award-prefer','فَكَتَبَ':'write','فَمَرَّ':'pass-by','مَرَّ':'pass-by','مَلِكَتِهَا':'queen','وَمَلِكَتِهِمْ':'queen','نَظَرِهَا':'gaze-n','نِعْمَتِهِ':'blessing','وَأَجْرَوْا':'ds-cause-flow','وَأَلْفِ':'thousand','وَبَعَثَتْ':'raise','وَتَوَعَّدَهُ':'sh-threaten','وَتَوَعَّدَهُمْ':'sh-threaten','وَحُسْنَ':'goodness','وَطُرَفٍ':'ds-rarity','وَغَيْرَتَهُ':'ds-jealousy','وَوَسَّعَ':'widen','يُرِيَهَا':'show-v','يَقِينٍ':'sh-certainty-n', 'آلَاءِ':'ds-favours','آلَ':'family','آتِيكَ':'ds-coming'}

FORCED.update({'فَيُصِيبُ':'ds-benefit','لَهُوَ':'he','كَالْجَوَابِ':'ds-reservoir',
 'يُحْضِرَ':'ds-bring','وَأَبْعَدَ':'ds-farther','وَأَلَانَ':'ds-soften','وَأَلَنَّا':'ds-soften',
 'صِدْقٍ':'ds-truthfulness','حَذَّرَتْهُمْ':'warn-caution','نِعْمَ':'ds-excellent',
 'وَوَهَبْنَا':'ds-bestow','وَقَدِّرْ':'ds-apportion','وَقُدْرَتُهُ':'power-ability',
 'وَأَسَلْنَا':'ds-melt-flow','أَمْرِنَا':'command-n','أَبْلَغَ':'ds-eloquent',
 'وَزَحْفِهِ':'ds-march','يَزْحَفَ':'ds-march-v','سَاقَيْهَا':'ds-leg','فَنَسَبُوا':'ds-ascribe',
 'الظَّاهِرِ':'ds-apparent','أَصَدَقْتَ':'be-truthful','أَعْظَمِ':'ds-greatest',
 'وَهَمِّهَا':'ds-feeling','وَدَعَاهَا':'call','سِلْكِ':'ds-chain','بِأَنَّهُ':'anna',
 'وَأَسْلَمْتُ':'ds-surrender','وَحِكْمَتَهُ':'wisdom','عُلِّمْنَا':'teach','وَيَحْيَى':'ds-yahya',
 'نَسَبَ':'ds-ascribe','وَتَفَقَّدَ':'ds-inspect','أَدَلَّ':'ds-more-indicative',
 'يُدِلُّونَ':'ds-boast','بِجِوَارِ':'ds-neighbourhood','سَخَّرَ':'ds-subjugate',
 'وَسَخَّرَ':'ds-subjugate','وَسَخَّرْنَا':'ds-subjugate','وَجِفَانٍ':'ds-bowl',
 'وَكُلًّا':'each','فَأَمَّا':'when-surprise','قُصُورَ':'ds-weakness','قُصُورِ':'ds-weakness',
 'أَحَطْتُ':'surround','وَقْتٍ':'ds-time','وَذَكَّرَتْهُمْ':'ds-remind','فَأَطْلَعَتْ':'ds-inform',
 'فَبَرَّأَهُ':'ds-clear-blame','الْفَاتِحِينَ':'ds-conqueror','بِفِقْهٍ':'ds-understanding',
 'وَفِقْهَهُ':'ds-understanding','أَعْرَضَ':'ds-turn-away','فَفَهَّمْنَاهَا':'ds-make-understand',
 'فَهُمْ':'they','وَعَيْنَهُ':'eye','لِلْعَمَلِ':'deed','عَالِمِينَ':'ds-knowledgable',
 'الْعَبْدُ':'servant','عَبْدًا':'servant','آتِيكَ':'bring-come','قِبَلَ':'ds-capacity','الْعَالَمِينَ':'world','بِقَصْدِهِ':'ds-intend','فِقْهٌ':'ds-understanding','يَسِيلُ':'flow','فَفَهِمَ':'understand','وَأَسْرَعِ':'ds-faster','بِمَالٍ':'wealth','يَسِيرًا':'ds-easy','شِرْكِكُمْ':'ds-polytheism','لِلشِّرْكِ':'ds-polytheism','تَبْلُغْهَا':'ds-reach-v','بِقَتْلِهِمْ':'killing-n','الشَّيْطَانُ':'ds-devil','أَوِّبِي':'ds-echo','تَوَلَّ':'ds-turn-v','رَاسِيَاتٍ':'ds-fixed','عَاصِفَةً':'ds-stormy'})

def choose(ids, vocal):
    if {'sh-diminution','sh-withhold'} <= set(ids): return 'sh-diminution' if 'بَخْس' in vocal else 'sh-withhold'
    return h.choose(ids, vocal)

def resolve(vocal):
    if vocal == 'لَهُوَ':
        return 'he', [{'surfaceBare':'ل','vocabularyId':'emphasis','role':'prefix'}, {'surfaceBare':'هو','vocabularyId':'he','role':'stem'}]
    if vocal == 'أَتُمِدُّونَنِ':
        return 'ds-supply', [{'surfaceBare':'أ','vocabularyId':'question','role':'prefix'}, {'surfaceBare':'تمدون','vocabularyId':'ds-supply','role':'stem'}, {'surfaceBare':'ن','underlying':'نِي','vocabularyId':'me','role':'suffix','note':'The final ya of the object pronoun is omitted in this Quranic spelling.'}]
    if vocal in FORCED: return m.forced_resolve(vocal, FORCED[vocal])
    return h.resolve(vocal)

PASSIVE = {'بُعِثُوا':('were sent','بھیجے گئے'), 'عُلِّمْنَا':('we were taught','ہمیں سکھایا گیا'), 'أُوتِينَا':('we were given','ہمیں دیا گیا'), 'وَأُوتِينَا':('we were given','ہمیں دیا گیا'), 'وَأُوتِيَتْ':('she was given','اسے دیا گیا'), 'رُفِعَتْ':('was submitted','پیش کی گئی'), 'أُلْقِيَ':('was delivered','پہنچایا گیا'), 'قِيلَ':('it was said','کہا گیا')}

def light(vocal):
    if vocal in PASSIVE: return re.sub(r'[ًٌٍ]$', '', vocal)
    ident,_=resolve(vocal)
    key=b.bare(vocal)
    if ident == 'sovereignty': return key.replace('ملك','مُلك')
    if ident in ('king','queen'): return key.replace('ملك','مَلِك').replace('ملوك','مُلوك')
    if ident == 'ds-chain': return key.replace('سلك','سِلك')
    if ident == 'ds-polytheism': return key.replace('شرك','شِرك')
    if key in b.SELECTIVE: return b.SELECTIVE[key]
    if ident in ('sh-virtue','sh-thought-n'):
        return b.bare(vocal).replace('بر','بِرّ').replace('ظن','ظَنّ')
    return ''.join(c for c in vocal if not b.MARKS.fullmatch(c) or c=='\u0651')

def make_line(vocal, ident, pages):
    result=b.make_line(vocal, ident, pages)
    for index, token in enumerate(result['tokens']):
        if token['vocalized'] in PASSIVE:
            en, ur = PASSIVE[token['vocalized']]
            token['usage']=b.bilingual(en+'; passive', ur+'؛ مجہول')
        usage = {'وَعَيْنَهُ': ('his scout; literally his eye', 'اس کا جاسوس؛ لفظی معنی اس کی آنکھ'),
                 'أَحَطْتُ': ('I have learned; encompassed in knowledge', 'میں نے معلوم کر لیا؛ علم میں احاطہ کیا'),
                 'تُحِطْ': ('know fully; encompass in knowledge', 'پوری طرح جاننا؛ علم میں احاطہ کرنا'),
                 'اطَّلَعْتُ': ('I learned; became aware', 'میں نے معلوم کیا'),
                 'تَطَّلِعْ': ('become aware; learn', 'معلوم کرنا؛ آگاہ ہونا'),
                 'تَدْفَعُ': ('you hand over; deliver', 'تم حوالے کرتے ہو'),
                 'وَتَدْفَعُ': ('and you hand over', 'اور تم حوالے کرتے ہو'),
                 'دَفَعْتَ': ('you handed over', 'تم نے حوالے کیا'),
                 'وَدَفَعْتَ': ('and you handed over', 'اور تم نے حوالے کیا'),
                 'بُعِثُوا': ('were sent; passive', 'بھیجے گئے؛ مجہول'),
                 'وَبَعَثَتْ': ('she sent', 'اس نے بھیجا'),
                 'كَسَائِرِ': ('like other; like the rest of', 'دوسرے کی طرح'),
                 'رَاسِيَاتٍ': ('firmly fixed (large cooking pots)', 'جمی ہوئی بڑی دیگیں')}
        if token['vocalized'] in usage:
            token['usage'] = b.bilingual(*usage[token['vocalized']])
        rest=b.bare(''.join(t['vocalized']+t['after'] for t in result['tokens'][index+1:])).lstrip()
        if token['vocabularyId']=='what' and rest.startswith(('لي لا أرى','كنت قاطعة','كفر سليمان')):
            token['vocabularyId']='negation-ma' if not rest.startswith('لي لا أرى') else 'what-question'
            next(p for p in token['parts'] if p['role']=='stem')['vocabularyId']=token['vocabularyId']
    return result

def main():
    load_lexicon()
    b.choose, b.resolve, b.light = choose, resolve, light
    b.lexicon['negation-in'] = {'id': 'negation-in', 'partOfSpeech': 'particle', 'lemma': 'إِنْ', 'root': None, 'meanings': b.bilingual('not (with إلا)', 'نہیں؛ الا کے ساتھ نفی'), 'rootNote': b.bilingual('Function word.', 'حرف۔')}
    text = (ROOT / 'data/stories/08-dawood-sulaiman.vocalized.txt').read_text(encoding='utf-8')
    refs = [(27,15),(27,16),(34,10),(34,11),(21,79),(21,80),(38,26),(21,81),(34,12),(34,13),(21,78),(21,79),(27,44)] + [(27,a) for a in range(20,45)] + [(2,102),(38,30),(38,40)]
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
    source = ROOT / 'books/Qisas Story 8 Sayyiduna Dawood and Sulaiman (AS).pdf'
    checksum = hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else json.loads(DEST.read_text(encoding='utf-8'))['source']['sha256']
    editorial = template['editorial'].copy()
    editorial.update({'method': 'Manual transcription checked against all twelve rendered PDF pages; editorial grammatical vocalization and bilingual vocabulary.',
        'corrections': [{'sourcePages': [7], 'source': 'ودعاها فيها', 'edited': 'ودعاها فيه', 'reason': 'Pronoun refers to the masculine noun كتاب.'}, {'sourcePages': [8], 'source': 'تسير إليها', 'edited': 'تسير إليه', 'reason': 'Pronoun refers to Sulaiman.'}],
        'notes': ['PDF page 1 is the cover (printed page 183); narrative PDF pages 2–12 correspond to printed pages 184–194.',
                  'All 15 printed chapters and deliberate repetitions are retained. Reading units are sentences or connected passages rather than physical PDF lines.',
                  'The Quran excerpts use modern imlai spelling and verified verse links. The source spelling داود is retained; Quran.com imlai text uses داوود.',
                  'Added vocalization, morphology and bilingual glosses are editorial preparation.'],
        'referenceSources': [{'label': 'Source story PDF', 'path': 'books/' + source.name}, {'label': 'Quran references', 'url': 'https://quran.com'}, {'label': 'Quranic Arabic Corpus', 'url': 'https://corpus.quran.com'}]})
    story = {k: template[k] for k in ('schemaVersion', 'language', 'direction', 'meaningLanguages')}
    story.update({'id': '08-dawood-sulaiman', 'number': 8, 'titleEnglish': 'Dawood and Sulaiman', 'titleUrdu': 'حضرت داؤد اور سلیمان',
        'description': b.bilingual('Read about Dawood and Sulaiman, their wisdom, gratitude, and the Queen of Saba, in 15 chapters.', 'حضرت داؤد اور سلیمان کی حکمت، شکر گزاری اور ملکہ سبا کا قصہ؛ ۱۵ ابواب۔'),
        'source': {'file': 'books/' + source.name, 'sha256': checksum, 'pdfPages': 12, 'coverPage': 1, 'printedPageRange': [184,194]},
        'editorial': editorial, 'sections': sections})
    for key, vocal in [('title', 'دَاوُدُ وَسُلَيْمَانُ'), ('subtitle', 'قِصَّةُ سَيِّدِنَا دَاوُدَ وَسَيِّدِنَا سُلَيْمَانَ')]:
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
