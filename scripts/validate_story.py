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
