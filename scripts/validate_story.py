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
            assert MARKS.search(token['vocalized']), token
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
    assert {page for line in lines for page in line['sourcePages']} == set(range(2, story['source']['pdfPages'] + 1))
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
    for word, lexeme in expected.items():
        matching = [t for t in tokens if t['vocalized'] == word]
        assert matching and all(t['vocabularyId'] == lexeme for t in matching), word
    print(f"PASS {story['id']}: {len(lines)} lines, {len(tokens)} word occurrences, {len(vocabulary)} bilingual entries, {len(used)} entries used including headings/clitics.")


if __name__ == '__main__':
    index = json.loads((ROOT / 'data/stories.json').read_text(encoding='utf-8'))
    assert len({s['id'] for s in index['stories']}) == len(index['stories'])
    assert len({s['file'] for s in index['stories']}) == len(index['stories'])
    for item in index['stories']:
        check(item)
