"""Build the reviewed Isa story into a self-contained static payload."""
import hashlib
import json
import re
import sys
import build_story as b
import build_zakariyya as h
import build_musa as m
ROOT = b.ROOT
DEST = ROOT / 'data/stories/11-isa.json'

def load_lexicon():
    h.load_lexicon()
    for raw in (ROOT / 'data/stories/11-isa.lexicon.tsv').read_text(encoding='utf-8').splitlines():
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

INFLECTIONS = {'prophet':'أنبيائ', 'deity':'إلهين', 'guide':'اهدنا', 'mother':'والدتي',
 'tell':'تحكى', 'is-study':'تدرسون', 'write':'اكتبنا', 'provide':'ارزقنا',
 'witness':'اشهد', 'touch':'يمسس', 'is-flatter':'أطرو', 'is-adopt':'تبنا',
 'is-helper':'أنصار أنصاري أنصار ناصرين', 'is-delude':'يؤفكون',
 'is-poor':'فقرائ', 'is-false-adj':'باطلة', 'is-stay':'دمت', 'is-gospel':'إنجيل',
 'is-weep':'تدمع', 'recite':'نتلو', 'is-taker':'متوفي', 'oppose-enemy':'عادو',
 'strengthen-support':'أيد', 'is-engender':'ولد', 'is-assimilate':'شبه', 'is-allow':'أحل',
 'be':'كونوا', 'leave-v':'دعوا'}
FORCED = {'عِيسَى': 'is-isa', 'آخِرُ': 'ay-last', 'مُحَمَّدٍ': 'muhammad', 'يَحُولُ': 'is-change', 'وَالطَّبِيعَةِ': 'is-nature', 'وَجَهِلَ': 'ignorant-v', 'الْبَارِئُ': 'is-originator', 'مَثَلَ': 'like-n', 'كَمَثَلِ': 'like-n', 'بَلَغَتْ': 'reach', 'عَصْرِهِمْ': 'sh-era', 'تَفْسِيرًا': 'is-explanation', 'لِحَادِثٍ': 'is-occurrence', 'عِلَاجًا': 'is-treatment', 'الضَّيِّقِ': 'is-narrow', 'الْعَصْرِ': 'sh-era', 'وَالتَّمَسُّكِ': 'is-attachment', 'وَالتَّشَبُّثِ': 'is-clinging', 'طَبَائِعُهُمْ': 'is-nature', 'يَجْرِي': 'run', 'الْإِسْرَائِيلِيُّ': 'is-israelite', 'الذُّلِّ': 'humiliation', 'وَالدَّهَاءَ': 'is-cunning', 'وَالتَّعَامُلَ': 'is-transaction', 'بِالرِّبَا': 'is-usury', 'الدِّينِيَّةِ': 'is-religious', 'الْإِنْسَانِيَّةِ': 'is-humanity', 'وَتَجَرَّدَتْ': 'is-detach', 'أَصْلُهُ': 'origin-n', 'وَالْكَرَمِ': 'is-generosity', 'يُؤْمِنُونَ': 'believe-faith', 'وَالْحَقِّ': 'truth', 'وَإِصْلَاحِ': 'is-reform', 'الْبُهْتِ': 'is-slander', 'نِعْمَتِيَ': 'blessing', 'فَضَّلْتُكُمْ': 'award-prefer', 'تَسَرَّبَتْ': 'is-leak', 'الْوَثَنِيَّةِ': 'is-idolatry', 'وَبِطُولِ': 'length', 'وَبَلَغَتْ': 'reach', 'الْوَقَاحَةُ': 'is-impudence', 'وَالْوَثَنِيَّةِ': 'is-idolatry', 'بِالنَّسَبِ': 'lineage', 'الِاعْتِمَادِ': 'is-dependence', 'وَالْأَحْلَامِ': 'dream-n', 'وَالْمُثُلِ': 'is-ideal', 'الْعُلْيَا': 'higher-plural', 'يُؤْمِنُ': 'believe-faith', 'فَقِيرَةٍ': 'is-poor', 'وَيَحْنُو': 'ay-affection', 'وَغَنِيٍّ': 'wealthy', 'الْقُدُسِ': 'is-holy', 'وَيُبْرِئُ': 'is-cure', 'الْمَوْتَى': 'zk-dead', 'وَيُنَبِّئُ': 'is-inform', 'الْإِلَهِيَّةِ': 'is-divine', 'وَيُكَذِّبُ': 'deny-ii', 'يُنْكِرُونَ': 'deny-disapprove', 'وَأَصْلِهِ': 'origin-n', 'بِالتُّهَمِ': 'is-charge-n', 'بِالْقَذْفِ': 'is-slander-n', 'وَسَدُّوا': 'block', 'وَرَفَعَهُ': 'raise-up', 'وَكَرَّمَهُ': 'honour-v', 'وَأُبْرِئُ': 'is-cure', 'وَمَكَرَ': 'plot-scheme', 'وَمُطَهِّرُكَ': 'is-purifier', 'أُجُورَهُمْ': 'reward', 'شَقِيًّا': 'unfortunate', 'التَّنَازُلُ': 'is-concession', 'وَفُقَرَائِهِمْ': 'is-poor', 'حَوْلٍ': 'is-power-n', 'وَطَوْلٍ': 'is-influence', 'وَعَرَقِ': 'is-sweat', 'بِنَسَبٍ': 'lineage', 'حَوْلَهُ': 'around', 'يَسُدُّ': 'block', 'وَالْجَلَدِ': 'is-endurance', 'وَأَصَابَهُمْ': 'afflict', 'يُعْجِبْ': 'admire', 'وَكَرِهَ': 'loathe-v', 'بِالْغَيْبِ': 'is-unseen', 'ظُهُورِهَا': 'zk-manifestation', 'أَعْلَى': 'zk-exalted', 'وَأَجَلُّ': 'ay-exalted', 'وَذَكَرُوا': 'remember', 'لِلْأَجْيَالِ': 'is-generation', 'وَعِيلَ': 'is-exhaust', 'قَضِيَّتَهُ': 'is-case', 'وَدَهَاءٌ': 'is-cunning', 'وَالدَّهَاءِ': 'is-cunning', 'مَصْبُوغًا': 'is-coloured', 'الدِّينِيَّ': 'is-religious', 'يُهَيِّجُهُمْ': 'is-provoke', 'سِيَاسَتِهِمْ': 'is-politics', 'بِالسِّيَاسَةِ': 'is-politics', 'الْقَضِيَّةِ': 'is-case', 'وَكَفٍّ': 'is-cessation', 'يَصْدُرَ': 'is-emit', 'بِالْقَضِيَّةِ': 'is-case', 'وَالْوَقْتُ': 'ds-time', 'فَأَصْدَرَ': 'is-issue', 'صَلْبًا': 'is-crucifixion', 'بِالشَّنْقِ': 'is-hanging', 'الْجَمْعُ': 'combine', 'الشُّرْطَةِ': 'is-police', 'الْإِسْرَائِيلِيُّونَ': 'is-israelite', 'يَلْتَبِسُ': 'is-confuse', 'نَظَرِ': 'gaze-n', 'الْوَقْتُ': 'ds-time', 'وَإِهَانَتَهُ': 'is-insult', 'وَطُولُ': 'length', 'وَتَحَمُّلُ': 'is-bearing', 'إِلَهِيٌّ': 'is-divine', 'إِسْرَائِيلِيًّا': 'is-israelite', 'حَمَاسَةً': 'is-enthusiasm', 'وَأَكْبَرَهُمْ': 'greater', 'سَفَاهَةً': 'is-foolishness', 'إِيذَاءِ': 'is-harm', 'الْمَوْكِبُ': 'is-procession', 'شُرْطَةُ': 'is-police', 'وَتَسَلَّمُوا': 'is-receive', 'فَأَخَذَ': 'take', 'بِالصَّلْبِ': 'is-crucifixion', 'وَشُرْطَةُ': 'is-police', 'يَفْهَمُونَ': 'understand', 'مُجْرِمٍ': 'is-criminal', 'وَنَفَّذُوا': 'is-implement', 'رَفْعُ': 'ay-raising', 'مُطَهَّرًا': 'is-purified', 'رَّفَعَهُ': 'raise-up', 'وَأَفْرَطُوا': 'is-exceed', 'أَحْمَدُ': 'is-ahmad', 'وَتَأْوِيلٍ': 'is-interpretation', 'وَالنَّذْرِ': 'zk-vow', 'مُنْكِرًا': 'is-disapproving', 'مَتَّى': 'is-matthew', 'الْجَنَّةَ': 'paradise', 'يَتَذَوَّقُهُ': 'is-taste', 'عَرَفَ': 'know', 'وَلِيًّا': 'protector', 'يُبَرِّئُ': 'ds-clear-blame', 'تَقَوَّلَهُ': 'is-claim', 'هُمُ': 'they', 'إِجْلَالَ': 'is-awe', 'بِحَقٍّ': 'truth', 'الرَّقِيبَ': 'is-watchful', 'يَنفَعُ': 'ay-benefit', 'جَنَّاتٌ': 'paradise', 'رَّضِيَ': 'be-content', 'وَثَنِيَّةٍ': 'is-idolatry', 'الْوَثَنِيَّةُ': 'is-idolatry', 'وَجَرَتْ': 'run', 'وَتَنَصَّرَ': 'is-christianise', 'الْكَثِيرَ': 'many', 'النَّبَوِيَّةَ': 'is-prophetic', 'وَبَسَاطَتَهَا': 'is-simple', 'وَالْوَثَنِيَّةُ': 'is-idolatry', 'سَلَكَ': 'follow-path', 'قَصْدٍ': 'ds-intend', 'سَيْرَهُ': 'is-course', 'الضَّالِّينَ': 'is-errant', 'لِلْإِنْسَانِيَّةِ': 'is-humanity', 'وَالضِّيقُ': 'straitness', 'أَحْلَامَنَا': 'is-intelligence', 'وَأَيْسَرُ': 'is-easier', 'الْيُسْرُ': 'is-ease'}

FORCED.update({'إِيذَاءَهُ':'is-harm','الْبَاطِلِ':'is-false-adj','التَّخَلُّصَ':'is-releasing',
 'وَالتَّخَلُّصَ':'is-releasing','الصَّحِيحِ':'is-sound','الْفُقَرَاءَ':'is-poor',
 'الْفُقَرَاءِ':'is-poor','الْفَقِيرِ':'is-poor','فَقِيرٍ':'is-poor','لِلْفُقَرَاءِ':'is-poor',
 'الْمُشْرِكُونَ':'polytheist','تَتِمُّ':'complete-v','تَفْقِدُ':'lose-v',
 'دَامَ':'is-stay','دُعَاةُ':'zk-caller','زَهْوٌ':'is-pride','سَرِيعًا':'quick',
 'صِرَاعٌ':'is-conflict','صَرَّحَ':'is-state','كَثُرَ':'multiply','كَثُرَتْ':'multiply',
 'وَكَثُرَ':'multiply','مَرِّ':'pass-by','نَسَبُوا':'ds-ascribe','نَقَلَ':'carry',
 'وَآخِرِنَا':'ay-last','وَالزَّكَاةِ':'is-charity','وَحَمَاسَتَهَا':'is-enthusiasm',
 'وَشَاهَدَ':'is-observe'})
FORCED.update({'أَقْبَلَ':'turn-towards','بُعْدٍ':'is-distance-n','الْجَهْدُ':'is-effort',
 'صِدْقُهُمْ':'is-truthfulness','صِدْقِ':'is-truthfulness','وَصِدْقٍ':'is-truthfulness',
 'وَحَذَّرَهُمْ':'warn-caution','نَصِيرًا':'is-helper-sing','وَلَّدَتْ':'is-engender',
 'وَوَلَّدَ':'is-engender','أَشْبَاهًا':'is-alikeness','شُبِّهَ':'is-assimilate',
 'وَتَدْنُو':'is-near','بِحَمْلِ':'carrying','حَمْلَ':'carrying','حَمْلَهُ':'carrying',
 'الْجَمْعُ':'crowd','عَادَوْهُ':'oppose-enemy','أَمْرَنَا':'command-n',
 'يَشُكُّ':'is-doubt-v','السَّبْتِ':'is-sabbath','بِالسَّبِّ':'is-insult-n',
 'وَصْفَهُ':'is-description','وَكُلُّ':'each','كُونُوا':'be','وَأَنِّي':'anna',
 'وَدَعَاهُمْ':'call','وَدَعُوا':'leave-v','سِرُّ':'is-secret','نُزُولُ':'is-sending-down',
 'نَبِيُّنَا':'prophet','نَبِيِّنَا':'prophet','خَطَرٌ':'is-danger','وَالْعَبَثَ':'is-tampering',
 'وَوَرَدَتْ':'come-to','قَوْلُ':'saying-n','قَوْلُهُ':'saying-n','قَوْلِهِ':'saying-n',
 'وَالْقَوْلِ':'saying-n','وَقَوْلُهُ':'saying-n','وَقَوْلِهِمْ':'saying-n',
 'أَحَلَّهُ':'is-allow','وَأَحَلُّوا':'is-allow','وَلِأُحِلَّ':'is-allow',
 'تَوَفَّيْتَنِي':'take-in-death','الظَّنِّ':'thought-n','عَبْدُ':'servant',
 'بِالطَّعْنِ':'is-persecution','وَالطَّعْنِ':'is-persecution',
 'بِبِعْثَةِ':'is-sending','مُنَزِّلُهَا':'is-downsender','دَوْرُ':'is-turn-n',
 'الْحِرَفِ':'is-craft','وَأَيَّدَهُ':'strengthen-support','وَأَيَّدَهُمْ':'strengthen-support',
 'فَأَحْكُمُ':'is-ruling-v','صَوَّرَ':'depict','السَّهْلِ':'easy',
 'حَامِلِ':'is-carrier','فِيمَا':'what','وَآمَنَ':'believe-faith',
 'وَحَيَاتُهُ':'life-n','فَوُلِدَ':'birth','مَعَانِيَ':'is-meaning',
 'الْعُيُونُ':'eye','وَالدِّينِ':'faith','وَهُنَا':'here', 'وَأَجَلُّ':'is-majestic',
 'تَرَدُّدُهُمْ':'is-delay','بِوَالِدَتِي':'is-mother',
 'الْكِتَابَ':'book','الْكِتَابُ':'book','الْكِتَابِ':'book','الْمَسِيحِيَّةِ':'is-christian',
 'تَصَوَّرُوا':'is-imagine','شَكٍّ':'doubt','وَصَفَ':'describe','وَصَفَهُمُ':'describe',
 'وَصُوَرٌ':'picture','وَلَدٌ':'son-child','وُلِدتُّ':'birth','يُولَدْ':'birth',
 'يُكَفَّ':'is-limit','هَوَاهُمْ':'is-inclination','وَكَهْلًا':'is-mature'})

def choose(ids, vocal):
    if 'what' in ids and 'ay-ma-exclamation' in ids: return 'what'
    if {'sh-diminution','sh-withhold'} <= set(ids): return 'sh-diminution' if 'بَخْس' in vocal else 'sh-withhold'
    return h.choose(ids, vocal)

def resolve(vocal):
    if b.bare(vocal)=='فيما':
        return 'what', [{'surfaceBare':'في','vocabularyId':'in','role':'prefix'},
                        {'surfaceBare':'ما','vocabularyId':'what','role':'stem'}]
    if vocal in FORCED: return m.forced_resolve(vocal, FORCED[vocal])
    return h.resolve(vocal)

PASSIVE = {
 'وَنُسِخَتْ':('were superseded','منسوخ کر دیے گئے'), 'فَوُلِدَ':('was born','پیدا ہوا'),
 'وُلِدتُّ':('I was born','میں پیدا ہوا'), 'وُلِدْتُ':('I was born','میں پیدا ہوا'),
 'أُبْعَثُ':('I am raised again','میں دوبارہ اٹھایا جاتا ہوں'),
 'يُولَدْ':('be born','پیدا ہونا'), 'يُصْلَبُ':('is crucified','صلیب پر چڑھایا جاتا ہے'),
 'يُكَفَّ':('be restrained','روک دیا جائے'), 'يُسَلَّى':('are entertained','دل بہلایا جاتا ہے'),
 'وَيُلْهَى':('are amused','دل بہلایا جاتا ہے'), 'يُمْهَلُونَ':('are granted respite','مہلت دی جاتی ہے'),
 'تُحْكَى':('is recounted','بیان کی جاتی ہے'), 'وَتُرْوَى':('is narrated','روایت کی جاتی ہے'),
 'كُلِّفَ':('was assigned','ذمہ داری دی گئی'), 'شُبِّهَ':('was made to appear so','ایسا دکھایا گیا'),
 'وَعِيلَ':('was exhausted','ختم ہو گیا'), 'وَدُوِّنَتْ':('were recorded','لکھی گئیں'),
 'طُبِعُوا':('were endowed by nature','فطرت میں رکھا گیا'),
 'أُرْسِلَ':('was sent','بھیجا گیا'), 'أُرْسِلْتُم':('you were sent','تم بھیجے گئے'),
 'يُؤْفَكُونَ':('are turned away from truth','حق سے پھیرے جاتے ہیں'),
 'حُرِّمَ':('was forbidden','حرام کیا گیا')}

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
            token['usage']=b.bilingual(PASSIVE[token['vocalized']][0]+'; passive',PASSIVE[token['vocalized']][1]+'؛ مجہول')
        if token['vocalized']=='الْمَسِيحِيَّةِ' and index and result['tokens'][index-1]['vocabularyId']=='zk-caller':
            token['vocabularyId']='is-theology'
            next(p for p in token['parts'] if p['role']=='stem')['vocabularyId']='is-theology'
        rest=b.bare(''.join(t['vocalized']+t['after'] for t in result['tokens'][index+1:])).lstrip()
        if token['vocabularyId']=='what' and rest.startswith(('قتلوه','صلبوه','قتلنا','قلت لهم','كنا','لهم به','نحن','أرسلنا')):
            token['vocabularyId']='negation-ma'
            next(p for p in token['parts'] if p['role']=='stem')['vocabularyId']='negation-ma'
        if token['vocalized'] in ('وَإِن','وَإِنْ') and rest.startswith('من أهل الكتاب'):
            token['vocabularyId']='negation-in'
            next(p for p in token['parts'] if p['role']=='stem')['vocabularyId']='negation-in'
        usage={
          'تَوَفَّيْتَنِي':('You took me away; You took me fully','تو نے مجھے لے لیا؛ پوری طرح لے لیا'),
          'وَأَنْبَتَهَا':('caused her to grow well','اس کی اچھی پرورش کی'),
          'مُتَوَفِّيكَ':('taking you fully; taking you away','تمہیں پوری طرح لینے والا؛ لے جانے والا'),
          'جَنَّاتٌ':('gardens of Paradise here','یہاں جنت کے باغ'),
          'الْجَنَّةَ':('Paradise here','یہاں جنت'),
          'تَرَدُّدُهُمْ':('their repeated visits and demands','ان کا بار بار آنا اور مطالبہ کرنا'),
          'بِالْقَذْفِ':('with slanderous accusations','بہتان اور تہمت لگا کر'),
          'وَأَنِّي':('and that I; the Messiah speaks here','اور یہ کہ میں؛ یہاں حضرت عیسیٰ کہہ رہے ہیں'),
          'تَدَبِيرٌ':('intervention; arrangement','تدبیر؛ انتظام')}
        if token['vocalized'] in usage: token['usage']=b.bilingual(*usage[token['vocalized']])
    return result


def main():
    load_lexicon()
    b.choose, b.resolve, b.light = choose, resolve, light
    b.lexicon['negation-in'] = {'id': 'negation-in', 'partOfSpeech': 'particle', 'lemma': 'إِنْ', 'root': None, 'meanings': b.bilingual('not (with إلا)', 'نہیں؛ الا کے ساتھ نفی'), 'rootNote': b.bilingual('Function word.', 'حرف۔')}
    text = (ROOT / 'data/stories/11-isa.vocalized.txt').read_text(encoding='utf-8')
    refs = [(36, 82), (59, 24), (3, 59), (2, 122), (5, 18), (2, 80), (3, 45), (3, 46), (3, 47), (3, 48), (3, 49), (3, 50), (3, 51), (3, 52), (3, 53), (3, 54), (3, 55), (3, 56), (3, 57), (3, 58), (3, 59), (3, 60), (19, 30), (19, 31), (19, 32), (19, 33), (34, 34), (34, 35), (3, 52), (3, 52), (3, 53), (5, 112), (5, 112), (5, 113), (5, 114), (5, 115), (4, 156), (4, 157), (4, 158), (4, 159), (61, 6), (9, 30), (18, 4), (5, 72), (5, 75), (5, 76), (3, 79), (3, 80), (5, 72), (4, 172), (4, 173), (5, 116), (5, 117), (5, 118), (5, 119), (5, 120), (1, 6), (1, 7), (30, 4)]
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
    source = ROOT / 'books/Qisas Story 11 Sayyiduna Isa (AS).pdf'
    checksum = hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else json.loads(DEST.read_text(encoding='utf-8'))['source']['sha256']
    editorial = template['editorial'].copy()
    editorial.update({'method': 'Manual transcription checked against all 25 rendered PDF pages; editorial grammatical vocalization and bilingual vocabulary.',
        'corrections': [{'sourcePages': [25], 'source': 'تتجلى فيها', 'edited': 'تتجلى فيه', 'reason': 'Pronoun refers to the masculine noun دين.'}],
        'notes': ['PDF page 1 is the cover (printed page 207); narrative PDF pages 2–25 correspond to printed pages 208–231.',
                  'All 42 printed chapters and both footnotes are retained.',
                  'Quran passages are split at verse boundaries and use modern imlai spelling with verified verse links.',
                  'Historical and theological assertions, including the account of the trial and later religious history, are the supplied author’s narrative.',
                  'Added vocalization, morphology and bilingual glosses are editorial preparation.'],
        'referenceSources': [{'label': 'Source story PDF', 'path': 'books/' + source.name}, {'label': 'Quran references', 'url': 'https://quran.com'}, {'label': 'Quranic Arabic Corpus', 'url': 'https://corpus.quran.com'}]})
    story = {k: template[k] for k in ('schemaVersion', 'language', 'direction', 'meaningLanguages')}
    story.update({'id': '11-isa', 'number': 11, 'titleEnglish': 'Isa ibn Maryam', 'titleUrdu': 'حضرت عیسیٰ ابن مریم',
        'description': b.bilingual('Read about Isa ibn Maryam’s birth, miracles and message, in 42 chapters.', 'حضرت عیسیٰ ابن مریم کی ولادت، معجزات اور دعوت کا قصہ؛ ۴۲ ابواب۔'),
        'source': {'file': 'books/' + source.name, 'sha256': checksum, 'pdfPages': 25, 'coverPage': 1, 'printedPageRange': [208,231]},
        'editorial': editorial, 'sections': sections})
    for key, vocal in [('title', 'عِيسَى ابْنُ مَرْيَمَ'), ('subtitle', 'قِصَّةُ سَيِّدِنَا عِيسَى ابْنِ مَرْيَمَ')]:
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
