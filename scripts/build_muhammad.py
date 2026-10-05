"""Build text-only reviewed batches; no dictionary or word mappings are stored."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'data/stories/12-muhammad.json'


def main():
    sections, pages = [], []
    rows = (ROOT / 'data/stories/12-muhammad.vocalized.txt').read_text(encoding='utf8').splitlines()
    for row_index, row in enumerate(rows):
        if row.startswith('# '):
            number, title, english = row[2:].split('|')
            sections.append({'id': f's{int(number):02d}', 'number': int(number), 'titleVocalized': title,
                             'titleEnglish': english, 'lines': []})
        elif row.startswith('@'):
            pages = [int(p) for p in row[1:].split(',')]
        elif row:
            kind = 'heading' if row.startswith('## ') else 'footnote' if row.startswith('! ') else 'text'
            vocal = row[3:] if kind == 'heading' else row[2:] if kind == 'footnote' else row
            references = []
            if vocal.startswith('﴿ظَهَرَ'): references = [{'surah': 30, 'ayah': 41}]
            if vocal.startswith('﴿إِنَّ أَوَّلَ'): references = [{'surah': 3, 'ayah': 96}]
            section = sections[-1]
            # Subheadings precede their page marker in the editable source.
            if kind == 'heading':
                assert rows[row_index + 1].startswith('@'), 'Subheading must be followed by its source pages'
                pages = [int(p) for p in rows[row_index + 1][1:].split(',')]
            section['lines'].append({'id': f"{section['id']}-l{len(section['lines'])+1:03d}",
                                    'vocalized': vocal, 'kind': kind, 'sourcePages': pages.copy(), 'references': references})
    source = ROOT / 'books/Qisas Story 12 Sayyinduna Muhammad (SAW).pdf'
    sha = hashlib.sha256(source.read_bytes()).hexdigest() if source.exists() else json.loads(DEST.read_text(encoding='utf8'))['source']['sha256']
    story = {'schemaVersion': '2.0.0', 'language': 'ar', 'direction': 'rtl', 'id': '12-muhammad', 'number': 12,
             'wordLookup': 'google', 'titleVocalized': 'مُحَمَّدٌ رَسُولُ اللَّهِ', 'subtitleVocalized': 'سِيرَةُ خَاتَمِ النَّبِيِّينَ',
             'titleEnglish': 'Muhammad, the Messenger of Allah', 'titleUrdu': 'حضرت محمد رسول اللہ',
             'description': {'en': 'The life of Muhammad; reviewed chapters are being published in batches.', 'ur': 'سیرتِ خاتم النبیین؛ نظرثانی شدہ ابواب مرحلہ وار شائع کیے جا رہے ہیں۔'},
             'publication': {'status': 'partial', 'reviewedPdfPages': [8, 15], 'nextPdfPage': 16,
                             'label': 'First reviewed chapter · PDF pages 8–15 of 353. More chapters to follow.'},
             'source': {'file': 'books/' + source.name, 'sha256': sha, 'pdfPages': 353, 'storyStartPage': 8, 'printedPageRange': [7, 14]},
             'editorial': {'method': 'Manual transcription reviewed against each rendered page; full editorial grammatical vocalization.',
                           'notes': ['Front matter on PDF pages 1–7 is excluded.', 'Original narrative, subheadings and all six explanatory footnotes in this batch are retained.',
                                     'Historical and theological statements remain those of the supplied author.', 'Only vocalized text is stored; browser text variants and tokens are derived locally.'],
                           'corrections': []}, 'sections': sections}
    import re
    word = re.compile(r'[\u0621-\u064a][\u0621-\u064a\u064b-\u0652\u0670]*')
    lines = [line for section in sections for line in section['lines']]
    story['counts'] = {'sections': len(sections), 'lines': len(lines), 'wordOccurrences': sum(len(word.findall(l['vocalized'])) for l in lines)}
    DEST.write_text(json.dumps(story, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    index_path = ROOT / 'data/stories.json'
    index = json.loads(index_path.read_text(encoding='utf8'))
    item = {k: story[k] for k in ('id', 'number', 'titleEnglish', 'titleUrdu', 'description', 'counts', 'wordLookup', 'publication')}
    item.update({'title': story['titleVocalized'], 'file': 'stories/' + DEST.name})
    index['stories'] = sorted([s for s in index['stories'] if s['id'] != story['id']] + [item], key=lambda s: s['number'])
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(story['counts'])


if __name__ == '__main__': main()
