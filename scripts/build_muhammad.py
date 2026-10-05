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
            if 'أَتَقْتُلُونَ رَجُلًا أَنْ يَقُولَ' in vocal: references = [{'surah': 40, 'ayah': 28}]
            if vocal.startswith('﴿ظَهَرَ'): references = [{'surah': 30, 'ayah': 41}]
            if vocal.startswith('﴿إِنَّ أَوَّلَ'): references = [{'surah': 3, 'ayah': 96}]
            quran = {
                'وَإِذْ يَرْفَعُ': (2, 127), 'رَبَّنَا وَاجْعَلْنَا': (2, 128), 'رَبَّنَا وَابْعَثْ': (2, 129),
                'أَلَمْ تَرَ': (105, 1), 'أَلَمْ يَجْعَلْ': (105, 2), 'وَأَرْسَلَ عَلَيْهِمْ': (105, 3),
                'تَرْمِيهِمْ': (105, 4), 'فَجَعَلَهُمْ': (105, 5),
                'وَمَا كُنْتَ تَتْلُو': (29, 48), 'الَّذِينَ يَتَّبِعُونَ': (7, 157),
                'اقْرَأْ بِاسْمِ': (96, 1), 'خَلَقَ الْإِنْسَانَ': (96, 2),
                'اقْرَأْ وَرَبُّكَ': (96, 3), 'الَّذِي عَلَّمَ': (96, 4), 'عَلَّمَ الْإِنْسَانَ': (96, 5),
                'فَاصْدَعْ بِمَا': (15, 94), 'وَأَنْذِرْ عَشِيرَتَكَ': (26, 214),
                'وَاخْفِضْ جَنَاحَكَ': (26, 215), 'إِنِّي أَنَا النَّذِيرُ': (15, 89),
                'يَا أَيُّهَا الْمُدَّثِّرُ': (74, 1), 'قُمْ فَأَنْذِرْ': (74, 2),
                'مَا زَاغَ الْبَصَرُ': (53, 17), 'لَقَدْ رَأَى مِنْ': (53, 18)}
            for beginning, (surah, ayah) in quran.items():
                if vocal.startswith('﴿' + beginning): references = [{'surah': surah, 'ayah': ayah}]
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
             'publication': {'status': 'partial', 'reviewedPdfPages': [8, 109], 'nextPdfPage': 109,
                             'nextHeading': 'تَآمُرُ قُرَيْشٍ عَلَى رَسُولِ اللَّهِ الْأَخِيرُ وَخَيْبَتُهُمْ فِيمَا أَرَادُوا',
                             'label': 'Reviewed through the Aqabah pledges and early migration · PDF pages 8–109 of 353 (page 109 opening passage only). More chapters to follow.'},
             'source': {'file': 'books/' + source.name, 'sha256': sha, 'pdfPages': 353, 'storyStartPage': 8, 'printedPageRange': [7, 108]},
             'editorial': {'method': 'Manual transcription reviewed against each rendered page; full editorial grammatical vocalization.',
                           'notes': ['Front matter on PDF pages 1–7 is excluded.', 'Original narrative, subheadings and all explanatory footnotes in the reviewed batches are retained.',
                                     'The Before the Prophethood chapter is split into two reader sections; the second navigation title adds Birth and Upbringing for clarity. Original printed subheadings are retained.',
                                     'Reader section 4 adds Revelation and Early Believers to the original After the Prophethood heading for navigation clarity.',
                                     'Reader section 5 groups the public call and early persecution; its navigation title is editorial and printed subheadings are retained.',
                                     'Reader section 6 begins at the original heading محاربة قريش رسول الله وتفننهم في الإيذاء.',
                                     'Reader section 7 covers the migration to Abyssinia and retains Ja‘far’s speech and the explanatory footnotes. Its passage ends on page 82 at وخرجا من عنده مقبوحين.',
                                     'Reader section 8 extends the original إسلام عمر بن الخطاب heading with والمقاطعة for navigation; printed subheadings are retained. Its passage ends on page 93 with the deaths of Abu Talib and Khadijah.',
                                     'Reader section 9 has an editorial navigation title grouping the Quran’s effect, Ta’if and the Night Journey; all original printed subheadings are retained. Its passages cover pages 93–100.',
                                     'Reader section 10 has an editorial navigation title grouping the call to the tribes, both Aqabah pledges and early migration. All printed subheadings and footnotes are retained. Page 109 is reviewed only through the migration passage ending رضي الله عنهما; resume at تآمر قريش على رسول الله الأخير وخيبتهم فيما أرادوا.',
                                     'Historical and theological statements remain those of the supplied author.', 'Only vocalized text is stored; browser text variants and tokens are derived locally.'],
                           'corrections': [{'sourcePages': [41], 'source': 'أن رسول الله أميا', 'edited': 'أن رسول الله أمي',
                                            'reason': 'The predicate of أن is nominative: أُمِّيٌّ. Honorific remains in the text.'},
                                           {'sourcePages': [43], 'source': 'فيمكث فيها', 'edited': 'فيمكث فيه',
                                            'reason': 'Pronoun refers to the masculine noun غار.'},
                                           {'sourcePages': [44], 'source': 'فغطني حتى الثانية بلغ مني الجهد', 'edited': 'فغطني الثانية حتى بلغ مني الجهد',
                                            'reason': 'Correct misplaced الثانية in the printed quotation while retaining all words.'}]}, 'sections': sections}
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
