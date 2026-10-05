"""Check data integrity, bilingual coverage, and browser-rendering round trips."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKS = re.compile('[\u064b-\u0652\u0670]')


def check(item):
    path = ROOT / 'data' / item['file']
    assert path.resolve().is_relative_to((ROOT / 'data/stories').resolve()), item
    story = json.loads(path.read_text(encoding='utf-8'))
    assert item['id'] == story['id']
    assert item['counts'] == story['counts']
    if story.get('wordLookup') == 'google':
        check_text_only(story)
        return
    vocabulary = story['vocabulary']
    seen = set()
    used = set()
    lines = [line for section in story['sections'] for line in section['lines']]
    headings = [dict(id=section['id'] + '-title', text=section['title'],
                     vocalized=section['titleVocalized'], leading='',
                     tokens=section['titleTokens']) for section in story['sections']]
    headings += [dict(id='title', text=story['title'], vocalized=story['titleVocalized'],
                      leading='', tokens=story['titleTokens'])]
    headings += [dict(id='subtitle', text=story['subtitle'], vocalized=story['subtitleVocalized'],
                      leading='', tokens=story['subtitleTokens'])]
    for line in lines + headings:
        assert line['id'] not in seen, line['id']
        seen.add(line['id'])
        for field in ('text', 'vocalized'):
            reconstructed = line['leading'] + ''.join(t[field] + t['after'] for t in line['tokens'])
            assert reconstructed == line[field], (line['id'], field, reconstructed)
        assert MARKS.sub('', line['text']) == MARKS.sub('', line['vocalized']), line['id']
        if 'textBare' in line:
            assert line['textBare'] == MARKS.sub('', line['vocalized'])
            assert line['sourcePages'] and all(2 <= page <= story['source']['pdfPages'] for page in line['sourcePages'])
        for token in line['tokens']:
            assert token['id'] not in seen, token['id']
            seen.add(token['id'])
            assert token['vocabularyId'] in vocabulary, token
            assert ''.join(p['surfaceBare'] for p in token['parts']) == token['textBare'], token
            assert any(p['role'] == 'stem' and p['vocabularyId'] == token['vocabularyId'] for p in token['parts']), token
            assert MARKS.search(token['vocalized']) or vocabulary[token['vocabularyId']]['partOfSpeech'] == 'abbreviation', token
            for part in token['parts']:
                assert part['vocabularyId'] in vocabulary, part
                used.add(part['vocabularyId'])
    for key, entry in vocabulary.items():
        assert entry['id'] == key
        assert all(isinstance(entry['meanings'][lang], str) and entry['meanings'][lang].strip() for lang in ('en', 'ur')), key
        if entry['root']:
            assert re.fullmatch('[\u0621-\u064a]( [\u0621-\u064a]){2,3}', entry['root']), entry
        if entry['partOfSpeech'] == 'verb':
            assert set(entry['verb']) == {'madi', 'mudari', 'masdar'}, key
            assert isinstance(entry['verb']['masdar'], list)
        elif entry['partOfSpeech'] in ('noun', 'adjective'):
            assert entry['noun']['singular'] and isinstance(entry['noun']['plural'], list), key
    assert story['counts']['sections'] == len(story['sections'])
    assert story['counts']['lines'] == len(lines)
    assert story['counts']['wordOccurrences'] == sum(len(l['tokens']) for l in lines)
    assert story['counts']['vocabularyEntries'] == len(vocabulary)
    body_pages = set(range(1, story['source']['pdfPages'] + 1)) - set(story['source'].get('frontMatterPages', [story['source']['coverPage']]))
    assert {page for line in lines for page in line['sourcePages']} == body_pages
    assert [s['number'] for s in story['sections']] == list(range(1, len(story['sections']) + 1))
    for line in lines:
        excerpts = re.findall('﴿(.*?)﴾', line['vocalized'])
        assert excerpts == [r['excerptVocalized'] for r in line['references']], line['id']
        assert all(1 <= r['surah'] <= 114 and r['ayah'] > 0 and r['url'] == f"https://quran.com/{r['surah']}/{r['ayah']}" for r in line['references'])
    assert re.fullmatch('[0-9a-f]{64}', story['source']['sha256'])
    source_path = ROOT / story['source']['file']
    if source_path.is_file():
        source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
        assert story['source']['sha256'] == source_hash
    # Critical contextual distinctions must survive dictionary lookup.
    tokens = [token for line in lines for token in line['tokens']]
    expected = {'إِنْ': 'if', 'أَنْ': 'to-verb', 'مَنْ': 'who', 'مِنْ': 'from',
                'إِذًا': 'therefore', 'إِذَا': 'when-if', 'بِالذَّبْحِ': 'slaughter-n',
                'يُحْيِي': 'give-life', 'تُمِيتُ': 'cause-death'}
    if story['id'] == '01-ibrahim':
        assert len(story['sections']) == 16 and len(lines) == 183
    elif story['id'] == '02-yusuf':
        assert len(story['sections']) == 25 and len(lines) == 286
        expected = {'مَلَكٌ': 'angel', 'الْمَلِكُ': 'king', 'الْمُلْكُ': 'sovereignty',
                    'عِلْمٌ': 'knowledge', 'عَلَّمَنِي': 'teach', 'عَلِمَ': 'know-learn',
                    'أَبِي': 'father', 'أَبِيًّا': 'proud', 'سُجَّدًا': 'prostrating',
                    'سَالِمًا': 'safe', 'لَأَجِدُ': 'find', 'السِّرُّ': 'secret',
                    'أَحَبُّ': 'dearer', 'وَأَحَبَّ': 'love', 'أَلَّا': 'so-that-not'}
        for word in ('مَلَكٌ', 'الْمَلِكُ', 'الْمُلْكُ'):
            assert all(MARKS.search(t['text']) for t in tokens if t['vocalized'] == word)
        for word in ('يُرْسَلَ', 'وُجِدَ', 'وَصُلِبَ', 'وَيُحْشَرَ'):
            assert all(t.get('usage', {}).get('en', '').endswith('; passive') for t in tokens if t['vocalized'] == word)
    elif story['id'] == '03-nooh':
        assert len(story['sections']) == 22 and len(lines) == 193
        expected = {'مَلَكٌ': 'angel', 'مَلِكٍ': 'king', 'الْمُلُوكَ': 'king',
                    'ذِكْرًا': 'mention-n', 'ذَكَرًا': 'male', 'وَذَكَرَ': 'remember',
                    'وَلِي': 'for-to', 'وَقَلَّ': 'decrease', 'قِيلَ': 'say',
                    'أَمَاتَ': 'die', 'آمَنَ': 'believe-faith', 'بُنَيَّ': 'little-son',
                    'بَنِي': 'son', 'لَمَا': 'negation-ma'}
        for word in ('مَلَكٌ', 'مَلِكٍ', 'ذِكْرًا', 'ذَكَرًا', 'تُعْبَدُ'):
            matching = [t for t in tokens if t['vocalized'] == word]
            assert matching and all(MARKS.search(t['text']) for t in matching), word
        for word in ('قِيلَ', 'وَأُعْجِبَ', 'تُعْبَدُ', 'يُؤَخَّرُ'):
            matching = [t for t in tokens if t['vocalized'] == word]
            assert matching and all(t.get('usage', {}).get('en', '').endswith('; passive') for t in matching), word
        assert sum(r['surah'] == 37 and r['ayah'] == 79 for l in lines for r in l['references']) == 2
    elif story['id'] == '04-hud':
        assert len(story['sections']) == 11 and len(lines) == 110
        expected = {'وُلِدَ': 'birth', 'عَادٌ': 'aad', 'الْعِلْمُ': 'knowledge',
                    'النِّعَمِ': 'blessing', 'وَصَدِيقُكُمْ': 'friend',
                    'يَظْلِمُ': 'oppress', 'وَأَظْلَمَتِ': 'become-dark',
                    'وَالشُّرْبِ': 'drinking-n', 'مَرَضٌ': 'sickness',
                    'لِقَوْلِكَ': 'saying-n', 'وَعُيُونٌ': 'water-spring'}
        born = [t for t in tokens if t['vocalized'] == 'وُلِدَ']
        assert born and all(t['text'] == 'وُلِد' and t['usage']['en'].endswith('; passive') for t in born)
        reward = next(l for l in lines if 'إِنْ أَجْرِيَ إِلَّا' in l['vocalized'])
        assert next(t for t in reward['tokens'] if t['vocalized'] == 'إِنْ')['vocabularyId'] == 'negation-in'
        quote = next(l for l in lines if 'وَإِنَّمَا أَنَا نَذِيرٌ' in l['vocalized'])
        assert [(r['surah'], r['ayah']) for r in quote['references']] == [(67, 26)]
        assert sum(len(l['references']) for l in lines) == 12
    elif story['id'] == '05-salih':
        assert len(story['sections']) == 13 and len(lines) == 109
        assert [s['sourceSectionNumber'] for s in story['sections']] == list(range(12, 25))
        expected = {'صَالِحٌ': 'salih', 'مَلَكُ': 'angel', 'مُلُوكَ': 'king',
                    'آمِنٍ': 'secure', 'عِلْمٌ': 'knowledge', 'سِنِّكَ': 'age',
                    'نُحِرَتْ': 'slaughter-camel', 'وَنَحَرَهَا': 'slaughter-camel',
                    'تُوعَدُونَ': 'promise-v', 'لِيُخْرِجَهُمْ': 'bring-out',
                    'وَأُبَلِّغُكُمْ': 'convey', 'أَبْلَغْتُكُمْ': 'convey-iv',
                    'لِمَا': 'to-what', 'كُلَّمَا': 'whenever', 'وَهَاجَرَ': 'migrate'}
        for word in ('وُلِدَ', 'أُوتُوا', 'تُوعَدُونَ', 'نُحِرَتْ', 'وَدُهِشُوا'):
            matching = [t for t in tokens if t['vocalized'] == word]
            assert matching and all(t['usage']['en'].endswith('; passive') and MARKS.search(t['text']) for t in matching), word
        for opening in ('﴿إِنْ هِيَ إِلَّا', '﴿إِنْ هُوَ إِلَّا'):
            line = next(l for l in lines if l['vocalized'].startswith(opening))
            assert line['tokens'][0]['vocabularyId'] == 'negation-in'
        assert sum(len(l['references']) for l in lines) == 15
        assert any(r.get('url') == 'https://sunnah.com/muslim:2980b' for r in story['editorial']['referenceSources'])
    elif story['id'] == '06-musa':
        assert len(story['sections']) == 46 and len(lines) == 759
        assert story['source']['pdfPages'] == 83 and story['source']['frontMatterPages'] == [1,41]
        assert [s['sourceSectionNumber'] for s in story['sections']] == list(range(1,27))+list(range(1,21))
        assert [s['sourcePart'] for s in story['sections']] == ['A']*26+['B']*20
        assert sum(len(l['references']) for l in lines) == 226
        expected = {'أَنَا':'i', 'أَنْ':'to-verb', 'رَبَّنَا':'lord', 'لَنَا':'for-to',
                    'الْمَنُّ':'manna', 'لَمَّا':'until-when', 'عُلِّمْتَ':'teach',
                    'لِفَتَاهُ':'lad-assistant', 'سَنُقَتِّلُ':'kill-intensive',
                    'عَبَّدْتَ':'enslave-ii', 'وَأُشْرِبُوا':'make-drink',
                    'أَعْلَمُ':'more-knowledgeable', 'قُلْتُمْ':'say', 'فَأَبَوْا':'refuse',
                    'الْغَرَقُ':'drowning-n', 'لَوْنُهَا':'colour', 'أُوذِينَا':'hurt-iv'}
        for word in ('أُوذِينَا','عُلِّمْتَ','وَأُلْقِيَ','وَأُشْرِبُوا','قُتِلَ'):
            matching=[t for t in tokens if t['vocalized']==word]
            assert matching and all(t['usage']['en'].endswith('; passive') and MARKS.search(t['text']) for t in matching),word
    elif story['id'] == '07-shuaib':
        assert len(story['sections']) == 14 and len(lines) == 39
        assert story['source']['pdfPages'] == 9
        assert sum(len(l['references']) for l in lines) == 20
        expected={'شُعَيْبٌ':'shuaib','الْيَمَنِ':'sh-yemen','وَالْيَقِينِ':'sh-certainty-n',
                  'الْمِكْيَالَ':'sh-measure','وَالْمِيزَانَ':'sh-balance',
                  'الْكَيْلَ':'sh-measuring','تُوعِدُونَ':'sh-threaten-iv',
                  'أَثْرَوْا':'sh-become-rich','حَيَاتِكُمْ':'life-n',
                  'بَيَانًا':'sh-eloquence-n','عُدْنَا':'come-back',
                  'فَسُرِقَ':'steal','نُهِبَ':'sh-plunder','لَنُخْرِجَنَّكَ':'bring-out'}
        for word in ('أُنْفِقَ','فَسُرِقَ','نُهِبَ','سُلِّطَ','يُفْتَرَى'):
            matching=[t for t in tokens if t['vocalized']==word]
            assert matching and all(t['usage']['en'].endswith('; passive') and MARKS.search(t['text']) for t in matching), word
        reform=next(l for l in lines if 'إِنْ أُرِيدُ إِلَّا' in l['vocalized'])
        assert [t['vocabularyId'] for t in reform['tokens'] if t['vocalized']=='إِنْ']==['if','negation-in']
        assert all(t['vocabularyId']=='sh-emphatic-in' for t in tokens if t['vocalized']=='وَإِنْ')
    elif story['id'] == '08-dawood-sulaiman':
        assert len(story['sections']) == 15 and len(lines) == 84
        assert story['source']['pdfPages'] == 12
        assert sum(len(l['references']) for l in lines) == 41
        expected={'دَاوُدُ':'ds-dawood','سُلَيْمَانُ':'ds-sulaiman',
                  'الْمُلْكِ':'sovereignty','مَلِكٌ':'king','مَلِكَةِ':'queen',
                  'الْكَرْمِ':'ds-vineyard','كَالْجَوَابِ':'ds-reservoir',
                  'سَاقَيْهَا':'ds-leg','قُصُورِ':'ds-weakness',
                  'بِجِوَارِ':'ds-neighbourhood','بِمَالٍ':'wealth',
                  'وَيَحْيَى':'ds-yahya','أَوِّبِي':'ds-echo',
                  'نِعْمَ':'ds-excellent','آتِيكَ':'bring-come',
                  'فَهُمْ':'they','وَأَسْلَمْتُ':'ds-surrender',
                  'فَفَهَّمْنَاهَا':'ds-make-understand','عُلِّمْنَا':'teach',
                  'وَعَيْنَهُ':'eye','عَيْنَ':'water-spring','لَهُوَ':'he'}
        for word in ('بُعِثُوا','عُلِّمْنَا','وَأُوتِينَا','وَأُوتِيَتْ','رُفِعَتْ','أُلْقِيَ','قِيلَ'):
            matching=[t for t in tokens if t['vocalized']==word]
            assert matching and all(t['usage']['en'].endswith('; passive') and MARKS.search(t['text']) for t in matching),word
        for word in ('الْمُلْكِ','مَلِكٌ','مَلِكَةِ'):
            matching=[t for t in tokens if t['vocalized']==word]
            assert matching and all(MARKS.search(t['text']) for t in matching),word
        quran=story['sections'][13]
        assert [(r['surah'],r['ayah']) for l in quran['lines'] for r in l['references']]==[(27,a) for a in range(20,45)]
        assert next(t for t in tokens if t['vocalized']=='لَهُوَ')['parts'][0]['vocabularyId']=='emphasis'
        assert next(t for t in tokens if t['vocalized']=='أَتُمِدُّونَنِ')['parts'][-1]['vocabularyId']=='me'
        assert any(t['vocabularyId']=='negation-ma' for t in story['sections'][14]['lines'][1]['tokens'])
    elif story['id'] == '09-ayyub-yunus':
        assert len(story['sections']) == 7 and len(lines) == 21
        assert story['source']['pdfPages'] == 6
        assert [s['sourceSectionNumber'] for s in story['sections']] == list(range(16,23))
        assert [(r['surah'],r['ayah']) for l in lines for r in l['references']]==[(21,83),(21,84),(10,98),(37,141),(21,87),(21,88)]
        expected={'أَيُّوبَ':'ds-ayyub','يُونُسَ':'ds-yunus','عَافَهُ':'ay-loathe',
                  'وَعَافَاهُ':'ay-heal','مَالَهُ':'wealth','سَلْوَى':'ay-solace',
                  'سَلِيمًا':'ay-sound','الْحَالِكُ':'ay-dark','الْأَسَدِ':'ay-lion',
                  'وَسِخَالُهَا':'ay-lamb','فَلَا':'not','أَنِّي':'anna',
                  'أَظْهُرِهِمْ':'ay-back','النُّونِ':'ay-fish',
                  'وَنَجَّيْنَاهُ':'ay-rescue','نُنْجِي':'ay-rescue-iv','نَقْدِرَ':'ay-restrict'}
        for word in ('فَابْتُلِيَ','ابْتُلِيَ','وَأُفْرِدَ','وَتُسَدُّ'):
            matching=[t for t in tokens if t['vocalized']==word]
            assert matching and all(t['usage']['en'].endswith('; passive') and MARKS.search(t['text']) for t in matching),word
        footnotes=[l for l in lines if 'الْعِبَارَةُ لِابْنِ كَثِيرٍ' in l['vocalized']]
        assert len(footnotes)==2 and [l['sourcePages'] for l in footnotes]==[[2],[5]]
        assert all(next(t for t in l['tokens'] if t['vocalized']=='كَثِيرٍ')['vocabularyId']=='ay-kathir' for l in footnotes)
        exclamations=[t for l in story['sections'][6]['lines'] for t in l['tokens'] if t['vocalized'] in ('فَمَا','وَمَا')]
        assert len(exclamations)==2 and all(t['vocabularyId']=='ay-ma-exclamation' for t in exclamations)
        assert next(t for t in story['sections'][3]['titleTokens'] if t['vocalized']=='وَحِكْمَتُهَا')['vocabularyId']=='wisdom'
    elif story['id'] == '10-zakariyya':
        assert len(story['sections']) == 8 and len(lines) == 27
        assert story['source']['pdfPages'] == 6
        assert [s['sourceSectionNumber'] for s in story['sections']] == list(range(1,9))
        assert [(r['surah'],r['ayah']) for l in lines for r in l['references']] == [(3,35),(3,36),(3,37),(3,38),(3,41),(21,89),(21,90),(19,12),(19,13),(19,14),(19,15)]
        expected={'زَكَرِيَّا':'ds-zakariya','يَحْيَى':'ds-yahya','مَرْيَمَ':'zk-maryam',
                  'صَالِحٍ':'righteous','كَثِيرٍ':'many','بَكَّرَ':'zk-early',
                  'الذَّكَرُ':'male','أُمًّا':'mother','بِدُعَاءٍ':'supplication',
                  'هَبْ':'ds-bestow','فَتَقَبَّلَهَا':'accept','وَكَفَّلَهَا':'zk-foster-ii',
                  'عَصِيًّا':'zk-rebellious','وَطَوْرًا':'zk-turn','عَيْنٍ':'eye',
                  'قَدَّرَ':'consider-august','قُدْرَتِهِ':'power-ability',
                  'وَقُرْبِ':'zk-proximity','وَلِينِ':'zk-gentleness',
                  'وَزَكَاةً':'zk-purity','يُودِعَ':'zk-deposit','وُلِدَ':'birth'}
        for word in ('وَخُصَّ','يُولَدَ','وَيُولَدُ','وَخُلِقَ','وَوُلِدَ','وُلِدَ','يُبْعَثُ','يُشَارُ'):
            matching=[t for t in tokens if t['vocalized']==word]
            assert matching and all(t['usage']['en'].endswith('; passive') and MARKS.search(t['text']) for t in matching),word
        assert story['sections'][4]['lines'][0]['sourcePages']==[4,5]
        assert 'يُشَارُ فِي ذَلِكَ إِلَيْهِ بِالْبَنَانِ' in story['sections'][7]['lines'][0]['vocalized']
    elif story['id'] == '11-isa':
        assert len(story['sections']) == 42 and len(lines) == 175
        assert story['source']['pdfPages'] == 25
        assert [s['sourceSectionNumber'] for s in story['sections']] == list(range(1,43))
        assert sum(len(l['references']) for l in lines) == 59
        expected = {'عِيسَى':'is-isa', 'مَرْيَمَ':'zk-maryam',
                    'السَّبْتِ':'is-sabbath', 'وَحَيَاتُهُ':'life-n',
                    'وَكَهْلًا':'is-mature', 'وَأَيَّدَهُ':'strengthen-support',
                    'نَبِيُّنَا':'prophet', 'وَالْمُثُلِ':'is-ideal'}
        assert any('كُلُّهُمْ إِلَهٌ' in l['vocalized'] for l in lines)
        assert any('وَقَدْ صَوَّرَ الْقُرْآنُ' in l['vocalized'] for l in lines)
        assert any('تَتَجَلَّى فِيهِ' in l['vocalized'] for l in lines)
        for word in ('شُبِّهَ', 'فَوُلِدَ'):
            matching = [t for t in tokens if t['vocalized'] == word]
            assert matching and all(t['usage']['en'].endswith('; passive') and MARKS.search(t['text']) for t in matching), word
    for word, lexeme in expected.items():
        matching = [t for t in tokens if t['vocalized'] == word]
        assert matching and all(t['vocabularyId'] == lexeme for t in matching), word
    print(f"PASS {story['id']}: {len(lines)} lines, {len(tokens)} word occurrences, {len(vocabulary)} bilingual entries, {len(used)} entries used including headings/clitics.")


def check_text_only(story):
    assert story['schemaVersion'] == '2.0.0'
    assert 'vocabulary' not in story
    assert story['source']['storyStartPage'] == 8
    lines = [line for section in story['sections'] for line in section['lines']]
    start, end = story['publication']['reviewedPdfPages']
    assert start == 8 and end < story['source']['pdfPages']
    assert story['publication']['nextPdfPage'] in (end, end + 1)
    if story['publication']['nextPdfPage'] == end:
        assert story['publication']['nextHeading']
    assert {p for line in lines for p in line['sourcePages']} == set(range(start, end + 1))
    assert len({l['id'] for l in lines}) == len(lines)
    assert story['counts']['sections'] == len(story['sections'])
    assert story['counts']['lines'] == len(lines)
    assert story['counts']['wordOccurrences'] == sum(len(re.findall(r'[\u0621-\u064a][\u0621-\u064a\u064b-\u0652\u0670]*', l['vocalized'])) for l in lines)
    assert all(MARKS.search(l['vocalized']) and l['sourcePages'] for l in lines)
    assert all('text' not in l and 'tokens' not in l for l in lines)
    assert sum(l['kind'] == 'footnote' for l in lines) == 20
    assert [(r['surah'], r['ayah']) for l in lines for r in l['references']] == [(30, 41), (3, 96), (2, 127), (2, 128), (2, 129)] + [(105, a) for a in range(1, 6)]
    assert [s['id'] for s in story['sections']] == ['s01', 's02']
    assert any('وَقَدْ أَصَابَ لَهُ أَبْرَهَةُ مِائَتَيْ بَعِيرٍ' in l['vocalized'] for l in lines)
    source = ROOT / story['source']['file']
    assert re.fullmatch('[0-9a-f]{64}', story['source']['sha256'])
    if source.exists(): assert hashlib.sha256(source.read_bytes()).hexdigest() == story['source']['sha256']
    print(f"PASS {story['id']}: {len(lines)} text-only reading units, PDF pages {start}–{end}, no vocabulary dictionary.")


if __name__ == '__main__':
    index = json.loads((ROOT / 'data/stories.json').read_text(encoding='utf-8'))
    assert len({s['id'] for s in index['stories']}) == len(index['stories'])
    assert len({s['file'] for s in index['stories']}) == len(index['stories'])
    for item in index['stories']:
        check(item)
