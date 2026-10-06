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
                'مَا زَاغَ الْبَصَرُ': (53, 17), 'لَقَدْ رَأَى مِنْ': (53, 18),
                'فَأَغْشَيْنَاهُمْ': (36, 9), 'ثَانِيَ اثْنَيْنِ': (9, 40),
                'وَكَذَلِكَ جَعَلْنَاكُمْ': (2, 143), 'أُذِنَ لِلَّذِينَ': (22, 39),
                'يَا أَيُّهَا الَّذِينَ آمَنُوا كُتِبَ': (2, 183), 'شَهْرُ رَمَضَانَ': (2, 185),
                'إِنْ كُنْتُمْ آمَنْتُمْ': (8, 41), 'وَيُنَزِّلُ عَلَيْكُمْ': (8, 11), 'وَلَقَدْ نَصَرَكُمُ': (3, 123), 'وَلَقَدْ صَدَقَكُمُ': (3, 152), 'إِذْ جَاءُوكُمْ': (33, 10), 'هُنَالِكَ ابْتُلِيَ': (33, 11), 'يَا أَيُّهَا الَّذِينَ آمَنُوا اذْكُرُوا': (33, 9), 'وَرَدَّ اللَّهُ': (33, 25), 'لَقَدْ رَضِيَ اللَّهُ': (48, 18), 'وَمَغَانِمَ كَثِيرَةً': (48, 19), 'لَقَدْ صَدَقَ اللَّهُ': (48, 27), 'يَا أَيُّهَا النَّاسُ إِنَّا': (49, 13), 'إِذَا جَاءَ نَصْرُ': (110, 1), 'وَرَأَيْتَ النَّاسَ': (110, 2), 'لَقَدْ نَصَرَكُمُ': (9, 25), 'ثُمَّ أَنْزَلَ اللَّهُ': (9, 26), 'إِنَّا فَتَحْنَا': (48, 1), 'لِيَغْفِرَ لَكَ': (48, 2), 'وَيَنْصُرَكَ اللَّهُ': (48, 3), 'وَعَسَى أَنْ تَكْرَهُوا': (2, 216)}
            for beginning, (surah, ayah) in quran.items():
                if vocal.startswith('﴿' + beginning): references = [{'surah': surah, 'ayah': ayah}]
            if 'وَلِلَّهِ جُنُودُ السَّمَاوَاتِ وَالْأَرْضِ' in vocal:
                references = [{'surah': 48, 'ayah': 4}, {'surah': 48, 'ayah': 7}]
            if 'كُفُّوا أَيْدِيَكُمْ وَأَقِيمُوا الصَّلَاةَ' in vocal:
                references = [{'surah': 4, 'ayah': 77}]
            if '«سَمِعْنَا وَأَطَعْنَا»' in vocal:
                references = [{'surah': 2, 'ayah': 285}, {'surah': 4, 'ayah': 46}, {'surah': 5, 'ayah': 7}, {'surah': 3, 'ayah': 7}]
            if 'اذْهَبْ أَنْتَ وَرَبُّكَ فَقَاتِلَا' in vocal:
                references = [{'surah': 5, 'ayah': 24}]
            if 'وَمَا النَّصْرُ إِلَّا مِنْ عِنْدِ اللَّهِ' in vocal:
                references = [{'surah': 3, 'ayah': 126}, {'surah': 8, 'ayah': 10}]
            if vocal == 'هَذَانِ خَصْمَانِ اخْتَصَمُوا فِي رَبِّهِمْ':
                references = [{'surah': 22, 'ayah': 19}]
            if vocal == 'إِذْ جَاءُوكُمْ مِنْ فَوْقِكُمْ وَمِنْ أَسْفَلَ مِنْكُمْ': references = [{'surah': 33, 'ayah': 10}]
            if 'إِنَّ بُيُوتَنَا عَوْرَةٌ' in vocal: references = [{'surah': 33, 'ayah': 13}]
            if vocal == 'عَسَى أَنْ تَكْرَهُوا شَيْئًا وَهُوَ خَيْرٌ لَكُمْ': references = [{'surah': 2, 'ayah': 216}]
            if 'تَاللَّهِ لَقَدْ آثَرَكَ اللَّهُ عَلَيْنَا' in vocal: references = [{'surah': 12, 'ayah': 91}, {'surah': 12, 'ayah': 92}]
            if 'جَاءَ الْحَقُّ وَزَهَقَ الْبَاطِلُ' in vocal: references = [{'surah': 17, 'ayah': 81}, {'surah': 34, 'ayah': 49}]
            if '«لَا تَثْرِيبَ عَلَيْكُمُ الْيَوْمَ»' in vocal: references = [{'surah': 12, 'ayah': 92}]
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
             'publication': {'status': 'partial', 'reviewedPdfPages': [8, 299], 'nextPdfPage': 300,
                             'nextHeading': 'غَزْوَةُ تَبُوكَ',
                             'label': 'Reviewed through Ta’if, the captives and Thaqif’s conversion · PDF pages 8–299 of 353. More chapters to follow.'},
             'source': {'file': 'books/' + source.name, 'sha256': sha, 'pdfPages': 353, 'storyStartPage': 8, 'printedPageRange': [7, 298]},
             'editorial': {'method': 'Manual transcription reviewed against each rendered page; full editorial grammatical vocalization.',
                           'notes': ['Front matter on PDF pages 1–7 is excluded.', 'Original narrative, subheadings and all explanatory footnotes in the reviewed batches are retained.',
                                     'The Before the Prophethood chapter is split into two reader sections; the second navigation title adds Birth and Upbringing for clarity. Original printed subheadings are retained.',
                                     'Reader section 4 adds Revelation and Early Believers to the original After the Prophethood heading for navigation clarity.',
                                     'Reader section 5 groups the public call and early persecution; its navigation title is editorial and printed subheadings are retained.',
                                     'Reader section 6 begins at the original heading محاربة قريش رسول الله وتفننهم في الإيذاء.',
                                     'Reader section 7 covers the migration to Abyssinia and retains Ja‘far’s speech and the explanatory footnotes. Its passage ends on page 82 at وخرجا من عنده مقبوحين.',
                                     'Reader section 8 extends the original إسلام عمر بن الخطاب heading with والمقاطعة for navigation; printed subheadings are retained. Its passage ends on page 93 with the deaths of Abu Talib and Khadijah.',
                                     'Reader section 9 has an editorial navigation title grouping the Quran’s effect, Ta’if and the Night Journey; all original printed subheadings are retained. Its passages cover pages 93–100.',
                                     'Reader section 10 has an editorial navigation title grouping the call to the tribes, both Aqabah pledges and early migration. All printed subheadings and footnotes are retained. Its migration passage ends on page 109 at رضي الله عنهما.',
                                     'Reader section 11 groups Quraysh’s conspiracy, the departure from Mecca and the Cave of Thawr under an editorial navigation title; printed subheadings and footnotes are retained. Its passages cover pages 109–115.',
                                     'The phrase ولله جنود السماوات والأرض occurs in both 48:4 and 48:7; both references are recorded because the source does not specify one.',
                                     'Reader section 12 groups Suraqah’s pursuit, Umm Ma‘bad, arrival in Medina, Quba, Abu Ayyub’s hospitality and mosque construction under an editorial navigation title. Original printed headings, the welcome verses and all footnotes are retained. Its passages cover pages 116–125.',
                                     'Reader section 13 groups brotherhood, the agreement with the Jews, the adhan, the qiblah, early expeditions and prescribed fasting under an editorial navigation title. Printed subheadings and footnotes are retained. Its passages cover pages 126–134.',
                                     'The brief quotation سمعنا وأطعنا occurs in 2:285, 4:46 and 5:7; all three matches are recorded because the source does not specify one. The following آمنا به كل من عند ربنا is from 3:7.',
                                     'The Badr chapter is split into reviewed reader sections. Section 14 adds الاستعداد والدعاء to the printed معركة بدر الحاسمة title for navigation. Its preparation and supplication passage ends at the opening of page 145.',
                                     'The quotation وما النصر إلا من عند الله occurs in both 3:126 and 8:10; both matches are recorded because the source does not specify one.',
                                     'Reader section 15 completes the Badr chapter; its navigation title adds القتال والنصر to the printed title. Original subheadings, all five footnotes and the account of Banu Qaynuqa are retained. Pages 8–153 are complete; resume at غزوة أحد on page 154.',
                                     'Historical and theological statements remain those of the supplied author.', 'Only vocalized text is stored; browser text variants and tokens are derived locally.'],
                           'corrections': [{'sourcePages': [273], 'source': 'جاء الحق وما يبدئ وما يعيد', 'edited': 'جاء الحق وما يبدئ الباطل وما يعيد', 'reason': 'Restore the omitted الباطل in the quotation from 34:49.'}, {'sourcePages': [258], 'source': 'أن يدخل رسوله والمسلمون مكة', 'edited': 'أن يدخل رسوله والمسلمين مكة', 'reason': 'Correct coordinated object case after يدخل.'}, {'sourcePages': [258], 'source': 'فتكون مباركا', 'edited': 'فتكون مباركة', 'reason': 'Correct agreement with the feminine noun الكعبة.'}, {'sourcePages': [251], 'source': 'أراد يبعث بعثا', 'edited': 'أراد أن يبعث بعثا', 'reason': 'Restore the missing أن before the purpose verb.'}, {'sourcePages': [254], 'source': 'بضعة يسيرا', 'edited': 'بضعة يسيرة', 'reason': 'Correct adjective agreement with the feminine noun.'}, {'sourcePages': [174], 'source': 'وإن غطي رجلاه بدت رأسه', 'edited': 'وإن غطيت رجلاه بدا رأسه', 'reason': 'Agreement corrected for the dual legs and masculine head.'}, {'sourcePages': [174], 'source': 'حشيش ب الرائحة', 'edited': 'حشيش طيب الرائحة', 'reason': 'Restore the damaged printed adjective in the explanatory footnote.'}, {'sourcePages': [143], 'source': 'عريش يكون فيها', 'edited': 'عريش يكون فيه',
                                            'reason': 'Pronoun refers to the masculine noun عريش.'}, {'sourcePages': [41], 'source': 'أن رسول الله أميا', 'edited': 'أن رسول الله أمي',
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
