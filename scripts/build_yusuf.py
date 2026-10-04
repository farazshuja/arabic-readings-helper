"""Build Story 2 from its reviewed transcription and bilingual lexical additions.

Uses the same browser schema and clitic resolver as Story 1. No PDF parser or
network is needed to rebuild when the existing JSON checksum is available.
"""
import hashlib
import json
import re
import sys
import build_story as b

ROOT = b.ROOT
DEST = ROOT / 'data/stories/02-yusuf.json'


def load_additions():
    for raw in (ROOT / 'data/stories/02-yusuf.lexicon.tsv').read_text(encoding='utf-8').splitlines():
        if not raw or raw.startswith('#'):
            continue
        ident, pos, root, first, second, masdar, en, ur, extra = raw.split('|')
        entry = {'id': ident, 'partOfSpeech': pos, 'lemma': first,
                 'root': None if root == '-' else root, 'meanings': b.bilingual(en, ur)}
        if pos == 'verb':
            entry['verb'] = {'madi': first, 'mudari': None if second == '-' else second,
                             'masdar': [] if masdar == '-' else masdar.split('، ')}
            if second == '-':
                entry['formNote'] = b.bilingual('Defective verb; no ordinary present or verbal noun supplied.', 'فعل ناقص؛ عام مضارع اور مصدر نہیں دیے گئے۔')
        elif pos in ('noun', 'adjective'):
            entry['noun'] = {'singular': first, 'plural': [] if second == '-' else second.split('، ')}
            if second == '-':
                entry['formNote'] = b.bilingual('Abstract, collective, or fixed use; no plural supplied for this sense.', 'مجرد معنی، اسم جمع یا مقررہ استعمال؛ اس معنی کی جمع نہیں دی گئی۔')
        if root == '-':
            entry['rootNote'] = b.bilingual('Proper name or function word; no derivational root assigned.', 'اسم خاص یا حرف وغیرہ؛ اشتقاقی مادہ مقرر نہیں کیا گیا۔')
        b.lexicon[ident] = entry
        for form in [first, *([] if second == '-' else second.split('، ')), *extra.split()]:
            b.forms.setdefault(b.bare(form), []).append(ident)
    # Inflected stems reviewed in the source, including case, dual, plural,
    # imperative and weak/jussive verb forms. Attached pronouns resolve separately.
    inflections = {
        'father': 'أبا آباء أباو', 'brother': 'أخا أخي', 'son': 'بني ابنين',
        'small': 'صغيران', 'weak': 'ضعيفان', 'strong': 'أقوياء',
        'man': 'رجلان رجلين', 'father-parent': 'والدنا',
        'be': 'يكونون أكون تكون كنت كنا',
        'prostrate': 'سجد', 'see': 'رأيت رأيتهم رأوا رأو رأ رأت نرى نرا',
        'know': 'عرفوا عرفو عرفت', 'love': 'يحبون يحبون أحبوا أحبو',
        'hear': 'سمعوا سمعا سمعتم', 'go': 'ذهبوا ذهبنا نذهب اذهبوا',
        'come': 'جاؤوا جئنا', 'gather': 'اجتمعوا', 'kill': 'اقتلوا',
        'throw': 'ألقو ألق ألقي ألقوا', 'take': 'يأخذ يأخذون أخذوا يأخذ نأخذ خذ',
        'send': 'أرسلوا ترسل يرسل أرسل', 'play': 'يلعبون نلعب',
        'fear': 'أخاف تخاف تخف', 'do': 'فعلوا فعلو فعلتم',
        'say': 'نقول قلت قولا قولوا قول قل يقولون يقل أقل',
        'eat': 'أكل تأكلون يأكلون', 'abandon': 'تركوا تركنا يتـرك يترك اتركوا',
        'put': 'وضعوا وضعتمو', 'return': 'رجعوا يرجعون ترجعون ارجعوا يرجعوا',
        'enter': 'دخل تدخلوا ادخلوا', 'remain': 'يبقى', 'arrive': 'وصلوا',
        'thirst': 'عطشوا', 'sell': 'باع', 'want': 'يريدون', 'ask': 'سألا',
        'know-learn': 'يعلم تعلمون يعلمون علموا علمتم علمنا أعلم',
        'worship': 'تعبدوا', 'call': 'يدعو يدع', 'sit': 'جلسا', 'find': 'وجدوا وجدو نجد يجد تجـد تجدون وجد',
        'create': 'خلقوا', 'look': 'انظروا', 'remember': 'اذكر تذكر',
        'bring-come': 'يأت ائتوا ائتو يأتوا تأتوا يأتين أتو',
        'give-water': 'يسقي', 'die': 'يموتون', 'not-be': 'أليس',
        'sleep': 'ناموا', 'inform': 'تخبر أخبر أخبرو',
        'honour': 'أكرمو', 'teach': 'علم علمت', 'give': 'آتيت',
        'protect': 'تحفظون حفظتم', 'overcome': 'تغلبوا',
        'miss': 'تفقدون نفقد', 'steal': 'يسرق', 'bereave': 'يفجعون',
        'join': 'ألحق', 'thank': 'شكر', 'peace': 'سلام',
        'relative-pl': 'الذين', 'all-n': 'جميعا', 'everyone': 'أجمعين',
        'cupbearer': 'ساقي ساقيا', 'year': 'سنين', 'proud': 'أبيا',
        'merciful-doer': 'راحمين', 'guardian': 'حافظين',
        'unjust': 'ظالمين', 'benefactor': 'محسنين', 'wrongdoer': 'خاطئين',
        'righteous': 'صالحين', 'prostrating': 'ساجدين', 'thief': 'سارقين',
    }
    for ident, values in inflections.items():
        for word in values.split():
            b.forms.setdefault(word.replace('ـ', ''), []).append(ident)
    more = {
        'father': 'آبائ آباؤ أبوي', 'son': 'أبنائ أبناؤ', 'see': 'أرا را رآ يرا',
        'lord': 'أربابا', 'earth': 'أرضا', 'want': 'أريد', 'throw': 'ألقا',
        'inna': 'إن', 'people': 'إنسانا', 'make': 'اجعل', 'well': 'بئرا',
        'go': 'تذهب يذهبون', 'travel': 'تسافر', 'know': 'تعرفان', 'say': 'تقولون',
        'recompense': 'جزاؤ', 'good': 'خيرا', 'merciful': 'رحيما', 'time': 'زمنا',
        'food': 'طعاما', 'enemy': 'عدوا', 'bereave': 'فجعو', 'rejoice': 'فرحا',
        'ram': 'كبشا', 'big': 'كبيرا', 'be': 'كنتم', 'muslim': 'مسلما',
        'dyed': 'مصبوغا', 'slaughter': 'ذبحو', 'ask': 'سألوا', 'seek': 'طلبوا',
        'anger': 'غضبت', 'fear': 'يخافون', 'hand': 'يدا', 'day': 'يوما', 'human': 'بشرا',
        'trust': 'أمنت',
        'safe': 'سالما', 'prostrating': 'سجدا', 'find': 'أجد',
    }
    for ident, words in more.items():
        for word in words.split():
            b.forms.setdefault(word, []).append(ident)
    for attached in ('رأيتهم', 'والدنا', 'أخبركما', 'أخبركم', 'أمنتكم', 'ألحقني'):
        b.forms.pop(attached, None)
    # Detached forms and contractions whose letters do not permit mechanical
    # segmentation, stored explicitly with the relevant lexical sense.
    b.forms.update({'إنما': ['only-indeed'], 'مما': ['from-what'], 'ألا': ['not-question', 'so-that-not'],
                    'ذلكما': ['that-two'], 'أنت': ['you'],
                    'إياه': ['him-only'], 'أيها': ['o-address'], 'تالله': ['allah']})
    b.SUFFIX.insert(0, ('كما', 'you-two'))
    # Do not let Story 1's why-lim interpretation capture past negation لَمْ.
    b.forms['لم'] = ['why-short', 'negation-lam']
    # Bare eleven has a different sense from Story 1's twelve label.
    b.lexicon['ten']['meanings'] = b.bilingual('ten; عشر in أحد عشر means eleven together with أحد', 'دس؛ احد عشر میں احد کے ساتھ گیارہ')
    b.lexicon['spouse']['meanings'] = b.bilingual('spouse; husband or wife according to context', 'زوج؛ سیاق کے مطابق شوہر یا بیوی')
    b.lexicon['us']['meanings'] = b.bilingual('we; us; our (according to grammatical role)', 'ہم؛ ہمیں؛ ہمارا؛ نحوی کردار کے مطابق')


original_choose = b.choose


def choose(ids, vocal):
    ids = list(dict.fromkeys(ids))
    keys = set(ids)
    if 'king' in keys and ('angel' in keys or 'sovereignty' in keys):
        return 'sovereignty' if 'مُلْك' in vocal else ('angel' if 'مَلَك' in vocal else 'king')
    if {'knowledge', 'know-learn', 'teach'} & keys and len(keys) > 1:
        if 'عِلْم' in vocal:
            return 'knowledge'
        if 'عَلَّم' in vocal or 'عَلِّم' in vocal:
            return 'teach'
        return 'know-learn'
    if {'associating', 'share'} <= keys:
        return 'associating' if 'ال' in b.bare(vocal) else 'share'
    if {'secret', 'gladden'} <= keys:
        return 'secret' if 'السر' in b.bare(vocal) else 'gladden'
    if {'permit', 'announce'} <= keys:
        return 'announce' if 'ذَّ' in vocal else 'permit'
    if {'bestow-favour', 'who', 'from'} & keys and len(keys) > 1:
        if 'مَنَّ' in vocal:
            return 'bestow-favour'
        return 'who' if 'مَ' in vocal else 'from'
    if {'negation-lam', 'why-short'} <= keys:
        return 'negation-lam' if 'لَمْ' in vocal else 'why-short'
    if {'not-question', 'so-that-not'} <= keys:
        return 'so-that-not' if 'لَّ' in vocal else 'not-question'
    if {'love', 'dearer'} <= keys:
        return 'dearer' if vocal.endswith('بُّ') else 'love'
    distinctions = [
        ('mother', 'or-question', 'أُمّ', 'mother', 'or-question'),
        ('command', 'command-n', 'أَمَر', 'command', 'command-n'),
        ('search-n', 'search-v', 'بَحَث', 'search-v', 'search-n'),
        ('grief', 'grieve-v', 'حَزِن', 'grieve-v', 'grief'),
        ('secret', 'gladden', 'سِرّ', 'secret', 'gladden'),
        ('reason', 'intellect', 'عَقْل', 'intellect', 'reason'),
        ('help', 'help-n', 'نَصْر', 'help-n', 'help'),
        ('human', 'give-tidings', 'بَشَّر', 'give-tidings', 'human'),
        ('after', 'be-distant', 'بَعْد', 'after', 'be-distant'),
        ('other-than', 'change', 'غَيْر', 'other-than', 'change'),
        ('jealousy', 'envy', 'حَسَدُ', 'jealousy', 'envy'),
        ('load', 'carry-v', 'حِمْل', 'load', 'carry-v'),
        ('ashamed', 'shame', 'خَجِل', 'ashamed', 'shame'),
        ('create', 'creation', 'خَلْق', 'creation', 'create'),
        ('cupbearer', 'drive', 'سَاقَ', 'drive', 'cupbearer'),
        ('associating', 'share', 'شِرْك', 'associating', 'share'),
        ('patience', 'be-patient', 'صَبْر', 'patience', 'be-patient'),
        ('world', 'scholar', 'عَالِم', 'scholar', 'world'),
        ('worship', 'servant', 'عَبْد', 'servant', 'worship'),
        ('anger', 'anger-n', 'غَضَب', 'anger-n', 'anger'),
        ('rejoice', 'happiness', 'فَرِح', 'rejoice', 'happiness'),
        ('kill', 'killing-n', 'قَتْل', 'killing-n', 'kill'),
        ('like', 'you-two', 'كَمَا', 'like', 'you-two'),
        ('for-to', 'emphasis', 'لِ', 'for-to', 'for-to'),
        ('praise', 'praise-v', 'حَمِد', 'praise-v', 'praise'),
        ('thanks', 'thank', 'شَكَر', 'thank', 'thanks'),
        ('leave', 'bring-out', 'يَخْرُج', 'leave', 'bring-out'),
        ('be-truthful', 'believe', 'صَدِّق', 'believe', 'be-truthful'),
        ('neglect', 'lose', 'يُضِيع', 'lose', 'neglect'),
        ('see', 'show', 'أُرِي', 'show', 'see'),
    ]
    if {'wisdom', 'judgement', 'rule'} & keys and len(keys) > 1:
        return 'rule' if 'حَكَم' in vocal else ('wisdom' if 'حِكَم' in vocal else 'judgement')
    for a, c, pattern, yes, no in distinctions:
        if {a, c} <= keys:
            match = pattern in vocal or ('\u0651' not in pattern and pattern in vocal.replace('\u0651', ''))
            return yes if match else no
    return original_choose(ids, vocal)


original_resolve = b.resolve


def resolve(vocal):
    key = b.bare(vocal)
    if key == 'فقد' and 'قَدْ' in vocal:
        return 'already', [{'surfaceBare': 'ف', 'vocabularyId': 'so', 'role': 'prefix'},
                           {'surfaceBare': 'قد', 'vocabularyId': 'already', 'role': 'stem'}]
    if key == 'أما' and 'مَّ' not in vocal:
        return 'what', [{'surfaceBare': 'أ', 'vocabularyId': 'question', 'role': 'prefix'},
                        {'surfaceBare': 'ما', 'vocabularyId': 'what', 'role': 'stem'}]
    if re.fullmatch('[ولفب]*أبي(?:ه|هم|كم|نا)?', key) and 'يّ' not in vocal:
        prefix = key[:key.index('أبي')]
        rest = key[len(prefix) + 3:]
        stem, suffix = ('أبي', rest) if rest else ('أب', 'ي')
        return 'father', ([{'surfaceBare': p, 'vocabularyId': dict(b.PREFIX)[p], 'role': 'prefix'} for p in prefix]
                          + [{'surfaceBare': stem, 'vocabularyId': 'father', 'role': 'stem'}]
                          + [{'surfaceBare': suffix, 'vocabularyId': dict(b.SUFFIX)[suffix], 'role': 'suffix'}])
    if key in ('إنا', 'وإنا'):
        pre = [{'surfaceBare': 'و', 'vocabularyId': 'and', 'role': 'prefix'}] if key.startswith('و') else []
        return 'inna', pre + [{'surfaceBare': 'إ', 'underlying': 'إِنَّ', 'vocabularyId': 'inna', 'role': 'stem'},
                             {'surfaceBare': 'نا', 'vocabularyId': 'us', 'role': 'suffix',
                              'note': 'Contracted إن + نا; pronoun is the subject: we.'}]
    if key == 'تالله':
        return 'allah', [{'surfaceBare': 'ت', 'vocabularyId': 'oath', 'role': 'prefix'},
                         {'surfaceBare': 'الله', 'vocabularyId': 'allah', 'role': 'stem'}]
    ident, parts = original_resolve(vocal)
    # Vocalized لَ is emphatic; لِ is the preposition. Retain that meaning in
    # attached forms such as لَحَافِظُونَ, لَأَنْتَ, لَظُلْمٌ and لَقَدْ.
    letters = re.findall('[^\u064b-\u0652\u0670][\u064b-\u0652\u0670]*', vocal)
    offset = 0
    for part in parts:
        if part['role'] == 'prefix' and part['vocabularyId'] == 'for-to' and letters[offset].startswith('لَ'):
            part['vocabularyId'] = 'emphasis'
        offset += len(part['surfaceBare'])
    return ident, parts


def light(vocal):
    ident, _ = resolve(vocal)
    if ident in ('king', 'angel', 'sovereignty'):
        word = b.bare(vocal)
        return word.replace('ملك', {'king': 'مَلِك', 'angel': 'مَلَك', 'sovereignty': 'مُلْك'}[ident]).replace('ملوك', 'مُلوك')
    if vocal in PASSIVE:
        return PASSIVE[vocal][0]
    if ident == 'knowledge':
        return b.bare(vocal).replace('علم', 'عِلْم')
    if ident in ('grief', 'goodness', 'share', 'associating', 'land', 'prison', 'servant', 'load'):
        core = {'grief': ('حزن', 'حُزن'), 'goodness': ('حسن', 'حُسن'), 'share': ('شرك', 'شِرك'),
                'associating': ('شرك', 'شِرك'), 'land': ('بر', 'بَرّ'), 'prison': ('سجن', 'سِجن'),
                'servant': ('عبد', 'عَبْد'), 'load': ('حمل', 'حِمل')}[ident]
        return b.bare(vocal).replace(*core)
    return ''.join(c for c in vocal if not b.MARKS.fullmatch(c) or c == '\u0651')


PASSIVE = {
    'وَعُرِفَ': ('وعُرِف', 'was known', 'معروف تھا'),
    'يُرْسَلَ': ('يُرسَل', 'be sent', 'بھیجا جائے'),
    'فَيُصْلَبُ': ('فيُصلَب', 'will be crucified', 'سولی دیا جائے گا'),
    'وَصُلِبَ': ('وصُلِب', 'was crucified', 'سولی دیا گیا'),
    'فَوُضِعَ': ('فوُضِع', 'was placed', 'رکھا گیا'),
    'تُغْلَبُوا': ('تُغلَبوا', 'be overpowered', 'مغلوب ہو جاؤ'),
    'وُجِدَ': ('وُجِد', 'was found', 'پایا گیا'),
    'فُجِعَ': ('فُجِع', 'was bereaved', 'صدمہ پہنچا'),
    'يُفْجَعُ': ('يُفجَع', 'is bereaved', 'صدمہ پہنچتا ہے'),
    'أَيُفْجَعُ': ('أيُفجَع', 'is he to be bereaved?', 'کیا اسے صدمہ پہنچے؟'),
    'وَيُحْشَرَ': ('ويُحشَر', 'be raised at resurrection', 'حشر میں اٹھایا جائے'),
}


def configure():
    load_additions()
    b.choose = choose
    b.resolve = resolve
    b.light = light
    # Each quotation is checked against an explicit reviewed verse reference.
    ayahs = [4, 12, 13, 16, 17, 18, 18, 19, 29, 31, 33, 36, 37, 37, 38, 38,
             39, 4, 11, 40, 40, 41, 42, 54, 55, 58, 59, 63, 64, 64, 66, 67,
             69, 70, 71, 72, 73, 74, 75, 77, 78, 79, 81, 83, 84, 86, 89,
             90, 90, 91, 92, 93, 94, 95, 96, 97, 98, 100, 101]
    text = (ROOT / 'data/stories/02-yusuf.vocalized.txt').read_text(encoding='utf-8')
    quotes = re.findall('﴿(.*?)﴾', text)
    assert len(quotes) == len(ayahs), (len(quotes), len(ayahs))
    b.QUOTES = [(b.bare(q), 46 if i == 17 else 31 if i == 18 else 12, a)
                for i, (q, a) in enumerate(zip(quotes, ayahs))]
    return text


def line(vocal, ident, pages):
    result = b.make_line(vocal, ident, pages)
    for token, hit in zip(result['tokens'], b.WORDS.finditer(vocal)):
        word = token['vocalized']
        if word in PASSIVE:
            _, en, ur = PASSIVE[word]
            token['usage'] = b.bilingual(en + '; passive', ur + '؛ مجہول')
        if word == 'إِنْ' and 'إِنْ هَذَا إِلَّا' in vocal:
            token['vocabularyId'] = 'negation-in'
            token['parts'][-1]['vocabularyId'] = 'negation-in'
        if word == 'وَإِنْ' and 'وَإِنْ كُنَّا لَخَاطِئِينَ' in vocal:
            token['vocabularyId'] = 'inna-light'
            token['parts'][-1]['vocabularyId'] = 'inna-light'
            token['usage'] = b.bilingual('indeed we were wrong; إن here is the lightened emphatic particle, not a condition', 'یقیناً ہم خطا کار تھے؛ یہاں ان مخففہ تاکید کے لیے ہے، شرط کے لیے نہیں')
        if word == 'كُنْتِ':
            token['usage'] = b.bilingual('you were (feminine singular)', 'تم تھیں؛ مؤنث واحد')
        if word == 'إِنَّكِ':
            for part in token['parts']:
                if part['vocabularyId'] == 'you-attached':
                    part['vocabularyId'] = 'you-attached-f'
        # Common occurrences of ما as past negation, rather than a relative
        # pronoun. The other uses retain the relative/interrogative card.
        tail = b.bare(vocal[hit.end():]).lstrip(' ،:!؟')
        if token['vocabularyId'] == 'what' and (tail.startswith(('فهم', 'نام', 'نسي', 'عرفوا', 'رضي', 'كان', 'جاء', 'جئنا', 'شهدنا', 'بقي', 'لامهم', 'هذا بشرا')) or word == 'أَمَا'):
            token['vocabularyId'] = 'negation-ma'
            for part in token['parts']:
                if part['role'] == 'stem':
                    part['vocabularyId'] = 'negation-ma'
        if token['vocabularyId'] == 'measuring-cup':
            token['usage'] = b.bilingual('The source glosses صواع as إناء, a vessel.', 'اصل متن میں صواع کی وضاحت إناء یعنی برتن سے کی گئی ہے۔')
        if word == 'يَسْرِقْ':
            token['usage'] = b.bilingual('Refers to Binyamin in the brothers’ allegation, not a statement of fact.', 'بھائیوں کے الزام میں بنیامین کی طرف اشارہ ہے؛ حقیقت کا بیان نہیں۔')
        if word == 'أَخٌ' and 'فَقَدْ سَرَقَ' in vocal:
            token['usage'] = b.bilingual('The brothers are referring to Yusuf in their allegation.', 'بھائی اپنے الزام میں یوسف کی طرف اشارہ کر رہے ہیں۔')
    return result


def main():
    text = configure()
    b.lexicon['negation-in'] = {'id': 'negation-in', 'lemma': 'إِنْ', 'partOfSpeech': 'particle',
                               'root': None, 'meanings': b.bilingual('not (restrictive negation with إلا)', 'نہیں؛ الا کے ساتھ حصر کے لیے نفی'),
                               'rootNote': b.bilingual('Function word.', 'حرف۔')}
    b.lexicon['you-attached-f'] = {'id': 'you-attached-f', 'lemma': 'كِ', 'partOfSpeech': 'pronoun',
                                  'root': None, 'meanings': b.bilingual('you; your (feminine singular)', 'تم؛ تمہارا؛ مؤنث واحد'),
                                  'rootNote': b.bilingual('Attached pronoun.', 'متصل ضمیر۔')}
    b.lexicon['inna-light'] = {'id': 'inna-light', 'lemma': 'إِنْ', 'partOfSpeech': 'particle', 'root': None,
                              'meanings': b.bilingual('indeed (lightened إنّ, confirmed by لَ)', 'بے شک؛ ان مخففہ، لام سے تاکید'),
                              'rootNote': b.bilingual('Function word.', 'حرف۔')}
    # Audit mode reports every unknown word before writing any payload.
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
            heading = line(title, sid + '-title', [])
            sections.append({'id': sid, 'number': int(number), 'title': heading['text'],
                             'titleVocalized': title, 'titleEnglish': english,
                             'titleTokens': heading['tokens'], 'lines': []})
        elif raw.startswith('@'):
            pages = [int(p) for p in raw[1:].split(',')]
        elif raw:
            section = sections[-1]
            section['lines'].append(line(raw, f"{section['id']}-l{len(section['lines'])+1:03d}", pages.copy()))
    source = ROOT / 'books/Qisas Story 2 Sayyiduna Yusuf  (AS).pdf'
    checksum = hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else json.loads(DEST.read_text(encoding='utf-8'))['source']['sha256']
    template = json.loads((ROOT / 'data/stories/01-ibrahim.json').read_text(encoding='utf-8'))
    editorial = template['editorial'].copy()
    editorial.update({
        'status': 'prepared; specialist review recommended',
        'method': 'Manual transcription checked against all 27 rendered source PDF pages; editorial grammatical vocalization and bilingual vocabulary.',
        'corrections': [
            {'sourcePages': [9], 'source': 'وقال أحدهما', 'edited': 'قال أحدهما', 'reason': 'Removed an extra conjunction from the quotation to match Quran 12:36.'},
            {'sourcePages': [12], 'source': 'لا تعبدوا إلا إياه', 'edited': 'ألا تعبدوا إلا إياه', 'reason': 'Restored the contracted أن + لا at the start of the excerpt from Quran 12:40.'},
            {'sourcePages': [19], 'source': 'ورجعوا إلى أبيهم وأخبره', 'edited': 'ورجعوا إلى أبيهم وأخبروه', 'reason': 'Plural subject agreement: the brothers informed him.'},
            {'sourcePages': [21], 'source': 'صواع (إناء) الملك؛ إن يسرق (بنيامين) فقد سرق أخ له (يوسف)', 'edited': 'صواع الملك؛ إن يسرق فقد سرق أخ له', 'reason': 'Source explanatory parentheses are moved into bilingual token usage notes outside Quran quotations.'},
            {'sourcePages': [23], 'source': 'في صدري قلب بشر', 'edited': 'في صدره قلب بشر', 'reason': 'Third-person pronoun agrees with the narration about Yaqub.'},
            {'sourcePages': [23], 'source': 'لا تزاك تذكر', 'edited': 'لا تزال تذكر', 'reason': 'Corrected an apparent printed typo in the verb تزال.'},
            {'sourcePages': [24], 'source': 'مصيتهم', 'edited': 'مصيبتهم', 'reason': 'Restored the missing ب in مصيبتهم.'},
        ],
        'notes': [
            'Printed pages 19–44 correspond to PDF pages 2–27; sourcePages always uses PDF page numbers.',
            'Sentence or short connected passage units replace physical PDF line wrapping; intentional repetitions are preserved.',
            'Light text retains shadda and disambiguating vowels, including مَلِك (king), مَلَك (angel), مُلْك (sovereignty), and passive forms.',
            'Source honorific glyphs are expanded into words. Quran quotations use imlai spelling and are linked to their verse.',
            'Source wording and narrative claims are preserved apart from the documented editorial corrections.',
            'Review Arabic vowels and bilingual morphology with a qualified Arabic editor; this is not a certified edition.',
        ],
        'referenceSources': [{'label': 'Source story PDF', 'path': 'books/' + source.name},
                             {'label': 'Quran verse references', 'url': 'https://quran.com/12'},
                             {'label': 'Quranic Arabic Corpus', 'url': 'https://corpus.quran.com'}],
    })
    story = {k: template[k] for k in ('schemaVersion', 'language', 'direction', 'meaningLanguages')}
    story.update({'id': '02-yusuf', 'number': 2, 'titleEnglish': 'The story of Yusuf',
                  'titleUrdu': 'حضرت یوسف کی کہانی',
                  'description': b.bilingual('Follow Yusuf’s story from his childhood dream to his reunion with his family, in 25 sections.', 'حضرت یوسف کے بچپن کے خواب سے خاندان کے ساتھ دوبارہ ملاقات تک کی کہانی؛ ۲۵ حصے۔'),
                  'source': {'file': 'books/' + source.name, 'sha256': checksum, 'pdfPages': 27, 'coverPage': 1, 'printedPageRange': [19, 44]},
                  'editorial': editorial, 'sections': sections})
    for key, vocal in [('title', 'قِصَّةُ يُوسُفَ'), ('subtitle', 'قِصَّةُ سَيِّدِنَا يُوسُفَ')]:
        heading = line(vocal, key, [1])
        story[key] = heading['text']
        story[key + 'Vocalized'] = vocal
        story[key + 'Tokens'] = heading['tokens']
    lines = [l for s in sections for l in s['lines']]
    headings = [s['titleTokens'] for s in sections] + [story['titleTokens'], story['subtitleTokens']]
    used = {p['vocabularyId'] for tokens in [l['tokens'] for l in lines] + headings for t in tokens for p in t['parts']}
    story['vocabulary'] = {k: v for k, v in b.lexicon.items() if k in used}
    story['counts'] = {'sections': len(sections), 'lines': len(lines), 'wordOccurrences': sum(len(l['tokens']) for l in lines),
                       'vocabularyEntries': len(story['vocabulary'])}
    DEST.write_text(json.dumps(story, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    b.update_catalog(story, DEST.name)
    print(json.dumps(story['counts']))


if __name__ == '__main__':
    main()
