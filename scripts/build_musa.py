"""Build the reviewed Musa story into a self-contained static payload."""
import hashlib
import json
import re
import sys
import build_story as b
import build_salih as h
ROOT = b.ROOT
DEST = ROOT / 'data/stories/06-musa.json'

def load_lexicon():
    h.load_lexicon()
    for raw in (ROOT / 'data/stories/06-musa.lexicon.tsv').read_text(encoding='utf-8').splitlines():
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
    b.lexicon["you-f-plural"]={"id":"you-f-plural","partOfSpeech":"pronoun","lemma":"كُنَّ","root":None,"meanings":b.bilingual("you; your (feminine plural)","تم سب؛ تمہارا؛ مؤنث جمع")}
    if ("كن","you-f-plural") not in b.SUFFIX: b.SUFFIX.insert(0,("كن","you-f-plural"))
    add_forms()
    for target, aliases in {'hurt-iv':'أوذي أوذين', 'eat':'كلوا', 'request-n':'طلب'}.items():
        for form in aliases.split(): b.forms.setdefault(form, []).append(target)
    for target, aliases in {'to-verb': 'أن', 'if': 'إن', 'possessor': 'أولو أولي', 'son': 'بنو', 'word': 'كلمات', 'journey-n': 'سفر', 'want': 'أردت أردنا', 'say': 'قلتم', 'plot-n': 'كيد', 'colour': 'لون', 'not-be': 'لست'}.items():
        for form in aliases.split(): b.forms.setdefault(form, []).append(target)


INFLECTIONS = {
 'afflict':'تصب يصب', 'hurt-iv':'آذيتمو آذوا يؤذي تؤذي يؤذون تؤذون',
 'secure':'آمنين', 'safe':'سالمين', 'righteous':'صالحات صالحة', 'last-adj':'أخير',
 'sea':'بحرين', 'honoured':'كرام', 'messenger':'مرسلين', 'escape':'نجوت',
 'boy':'غلامين', 'occasion':'مرتين', 'stand':'قم', 'make':'اجعلوا',
 'be-patient':'اصبروا', 'ten':'عشرة عشرات', 'guide-seek':'مهتدون',
 'promise-v':'وعدنا', 'support-care':'كفلت', 'call-out':'نودي',
 'live-life':'يحيى', 'towards':'نحو',
 'all-mighty':'قهار', 'm-hunger':'جوع',
 'wealthy':'غنية', 'wizard':'ساحران', 'two':'اثني', 'can':'قدرتمو تقدر',
 'give':'آت آتا آتوا آتي آتين يؤت أوتي', 'bring-come':'ائت أت أتيا',
 'come':'جئت جئتم جئتنا جئ جاؤ تجيئ جيء', 'take':'أخذو آخُذ',
 'go':'اذهب اذهبي اذهبا', 'follow':'اتبع اتبعوا اتبعون اتبعوني تتبعني',
 'choose-take':'اتخذ يتخذ نتخذ تتخذ', 'sit':'اجلس', 'carry-v':'احمل حملو يحملو',
 'choose':'اخترت', 'appoint-successor':'استخلف', 'call':'ادع', 'call':'ادع',
 'remember':'اذكروا', 'return':'ارجع', 'silence':'اسكت', 'strike':'اضرب',
 'forgive':'اغفر', 'stay':'امكثوا', 'kill':'قتلو يقتلو تقتلو', 'protect':'تقي',
 'command':'تؤمرون', 'birth':'يولد تولد', 'see':'را ترا', 'obey':'تطع',
 'fear':'خفت', 'put':'ضع ضعا', 'cease':'زلتم', 'want':'شئت شئتم',
 'know':'عرفتمو', 'enter':'دخلتمو', 'teach':'علمك علمني', 'abandon':'اتركو',
 'come-out':'اخرج', 'uncover-remove':'اخلع', 'enter':'ادخل دخلتمو',
 'attentive-listen':'استمع', 'buy':'اشترو', 'do':'افعلوا', 'return-object':'رددنا',
 'flee':'فررت', 'speak':'كلمو', 'ask':'سئل', 'reveal':'يوحى', 'find':'يوجد',
 'be':'كن يكن يك', 'not-be':'ليسوا ليست', 'lie':'يكذب', 'cut-v':'يقطع',
 'suffice':'كف', 'tent':'خيم', 'take-in-death':'توفي',
 'forget':'نسيت', 'plot':'مكرتمو', 'notables':'ملإ ملئ', 'water':'ماؤ',
 'enemy':'أعدائ', 'minister':'وزراؤ', 'cucumber':'قثائ', 'blood':'دمائ',
 'other':'آخرين', 'month':'أشهر', 'pharaoh':'فراعنة', 'eight':'ثماني',
 'emigration':'هجرة', 'woman':'امرأتين', 'poet':'شعراء',
}


def add_forms():
    for key, ids in list(b.forms.items()):
        if key.startswith("ال"):
            b.forms.setdefault(key[2:], []).extend(ids)
    for key, ids in list(b.forms.items()):
        if not key.endswith('ا'):
            b.forms.setdefault(key + 'ا', []).extend(ids)
    for ident, entry in b.lexicon.items():
        if entry['partOfSpeech'] in ('noun','adjective'):
            for f in [entry['noun']['singular'], *entry['noun']['plural']]:
                stem=b.bare(f)
                if stem.endswith('ة'):
                    for ending in ('ت','ات'):
                        b.forms.setdefault(stem[:-1]+ending,[]).append(ident)
        if entry['partOfSpeech'] != 'verb': continue
        madi=b.bare(entry['verb']['madi']); mudari=b.bare(entry['verb']['mudari'] or '')
        if not mudari: continue
        stem=madi[:-1] if madi.endswith('ى') else madi
        for end in ('ت','نا','تم','تما','تن','تا','وا','ن','ا'):
            b.forms.setdefault(stem+end,[]).append(ident)
        if madi.endswith('ى'):
            for stem in (madi[:-1]+'ي',madi[:-1]+'ا'):
                for end in ('ت','نا','تم','وا','ا'):
                    b.forms.setdefault(stem+end,[]).append(ident)
        for prefix in ('ي','ت','أ','ن'):
            base=prefix+mudari[1:]
            for end in ('','ون','وا','ان','ا','ين','ن'):
                b.forms.setdefault(base+end,[]).append(ident)
            if base.endswith(('ي','و','ى')):
                for end in ('','وا','ون'):
                    b.forms.setdefault(base[:-1]+end,[]).append(ident)
    for key, ids in list(b.forms.items()):
        if key.endswith("وا"):
            b.forms.setdefault(key[:-1],[]).extend(ids)
    for ident, words in INFLECTIONS.items():
        assert ident in b.lexicon, ident
        for word in words.split():
            b.forms.setdefault(word,[]).append(ident)
    b.lexicon['owner']['meanings']=b.bilingual('owner; companion; spouse according to context','مالک؛ ساتھی؛ سیاق کے مطابق شریک حیات')
    b.lexicon['spouse']['meanings']=b.bilingual('spouse; husband or wife','شریک حیات؛ شوہر یا بیوی')


def choose(ids,vocal):
    ids=list(dict.fromkeys(ids)); keys=set(ids)
    if len(ids)==1: return ids[0]
    if 'magic' in keys and 'سِحْر' in vocal.replace('ّ',''): return 'magic'
    if 'back-behind' in keys and 'خَلْف' in vocal: return 'back-behind'
    if {'killer','fight-iii'}<=keys: return 'fight-iii' if any(x in vocal for x in ('قَاتِلَا','قَاتِلْ','يُقَاتِل')) else 'killer'
    if {'leave-behind','succeed-in-place'}<=keys: return 'leave-behind' if 'خَلَّف' in vocal else 'succeed-in-place'

    defaults = {
        frozenset(['bring-come', 'give']): 'give',
        frozenset(['father', 'refuse']): 'father',
        frozenset(['never', 'eternity']): 'never',
        frozenset(['reward', 'fee', 'hire-fee', 'serve-wage', 'drag']): 'fee',
        frozenset(['reward', 'fee', 'hire-fee', 'serve-wage', 'run', 'drag']): 'fee',
        frozenset(['everyone', 'combine']): 'everyone',
        frozenset(['treat-well', 'sense']): 'treat-well',
        frozenset(['more-merciful', 'have-mercy']): 'more-merciful',
        frozenset(['earth', 'be-content']): 'earth',
        frozenset(['regret-n', 'sorrowful']): 'sorrowful',
        frozenset(['make-hasten', 'm-hurry']): 'make-hasten',
        frozenset(['corrupt', 'be-corrupt']): 'corrupt',
        frozenset(['multiply', 'increase-object']): 'increase-object',
        frozenset(['throw', 'meet']): 'throw',
        frozenset(['trustworthiness', 'trust-n']): 'trust-n',
        frozenset(['yesterday', 'touch']): 'yesterday',
        frozenset(['lodge', 'stop']): 'lodge',
        frozenset(['deny-disapprove', 'deny']): 'deny-disapprove',
        frozenset(['command', 'pass-by']): 'command',
        frozenset(['strive', 'exert']): 'exert',
        frozenset(['return-revert', 'revert']): 'return-revert',
        frozenset(['calling-n', 'call-out']): 'calling-n',
        frozenset(['second', 'second-fem']): 'second',
        frozenset(['man', 'person-man']): 'man',
        frozenset(['river', 'growl']): 'river',
        frozenset(['noble', 'noble-honourable']): 'noble-honourable',
        frozenset(['higher', 'upper']): 'upper',
        frozenset(['trustworthy', 'mother']): 'trustworthy',
        frozenset(['first', 'turn-v']): 'first',
        frozenset(['land', 'land-dry']): 'land-dry',
        frozenset(['ignorant-n', 'ignorant']): 'ignorant',
        frozenset(['snake', 'life-n']): 'snake',
        frozenset(['back-behind', 'leave-behind']): 'back-behind',
        frozenset(['staff', 'disobey']): 'staff',
        frozenset(['corruption', 'ruin-n']): 'corruption',
        frozenset(['case', 'ruling-case']): 'case',
        frozenset(['son-child', 'birth']): 'son-child',
        frozenset(['despair', 'grieve-for']): 'despair',
        frozenset(['lineage', 'curse-abuse']): 'lineage',
        frozenset(['daughter', 'build']): 'daughter',
        frozenset(['means-trick', 'trick']): 'means-trick',
        frozenset(['mercy', 'have-mercy']): 'mercy',
        frozenset(['promise-date', 'appointed-time']): 'promise-date',
        frozenset(['build', 'son']): 'build',
        frozenset(['fear', 'hide']): 'fear',
        frozenset(['remember', 'recall-self']): 'remember',
        frozenset(['watch-await', 'watch-observe']): 'watch-observe',
        frozenset(['arrive', 'pray']): 'arrive',
        frozenset(['speak', 'ask-mutual', 'talk-to']): 'speak',
        frozenset(['plant-grow', 'grow-plant']): 'grow-plant',
        frozenset(['madness', 'jinn']): 'madness',
        frozenset(['very', 'grandfather']): 'very',
        frozenset(['trick', 'means-trick']): 'means-trick',
        frozenset(['fear-v', 'fear-reverence']): 'fear-v',
        frozenset(['fear-n', 'scare']): 'fear-n',
        frozenset(['good', 'best-choice']): 'good',
        frozenset(['that-dha', 'possessor']): 'that-dha',
        frozenset(['have-mercy', 'mercy-rhum']): 'mercy-rhum',
        frozenset(['prostrating', 'prostrate']): 'prostrating',
        frozenset(['harm-n', 'harm']): 'harm-n',
        frozenset(['m-rebellion', 'recklessness']): 'recklessness',
        frozenset(['enemy', 'count']): 'enemy',
        frozenset(['hurry-v', 'm-hurry', 'make-hasten']): 'hurry-v',
        frozenset(['act-immorally', 'make-spring']): 'make-spring',
        frozenset(['miss', 'lose-v']): 'lose-v',
        frozenset(['say', 'saying-n']): 'say',
        frozenset(['occasion', 'pass-by']): 'pass-by',
        frozenset(['draw-out', 'pluck']): 'pluck',
        frozenset(['peck', 'be-content-eye', 'settle-standing']): 'peck',
        frozenset(['speak', 'ask-mutual']): 'speak',
        frozenset(['case', 'ruling-case', 'fulfil-spend']): 'fulfil-spend',
        frozenset(['story', 'recount']): 'story',
        frozenset(['plot', 'be-about']): 'be-about',
        frozenset(['no-indeed', 'each']): 'no-indeed',
        frozenset(['we', 'feel-longing']): 'we',
        frozenset(['employee', 'protect-give']): 'employee',
        frozenset(['benefit-n', 'm-benefit']): 'benefit-n',
        frozenset(['reduce', 'recount']): 'reduce',
        frozenset(['boat-fare', 'turn-v']): 'boat-fare',
        frozenset(['nooh', 'reveal']): 'nooh',
        frozenset(['far-fetched', 'impossible-far']): 'impossible-far',
        frozenset(['they-two', 'they']): 'they-two',
        frozenset(['here', 'them-f']): 'here',
        frozenset(['change-self', 'change']): 'change-self',
        frozenset(['advance', 'present-offer']): 'advance',
        frozenset(['receive-v', 'meet']): 'receive-v',
        frozenset(['green', 'khadir', 'vegetables']): 'vegetables',
        frozenset(['rare', 'know-aware']): 'rare',
        frozenset(['m-seek-help', 'rescue-seek']): 'rescue-seek',
        frozenset(['m-mock', 'mock-laugh']): 'mock-laugh',
        frozenset(['constrict', 'be-narrow']): 'constrict',
        frozenset(['admire', 'marvel']): 'marvel',
        frozenset(['honour', 'honour-v']): 'honour-v',
        frozenset(['make-easy', 'be-light-easy']): 'make-easy',
    }
    for ident, pattern in [('ward-custody','أَسْر'),('calf','عِجْل'),('hair','شَعْر'),('longing','شَوْق'),('stunned','صَعِق'),('guest','ضَيْف'),('sufficient','كَافِيَة'),('m-lower','أَدْنَى'),('easier','أَهْوَن'),('dream-n','حُلُم'),('falsehood','كَذِب'),('more','أَكْثَر'),('first','أَوَّل'),('fear','خِفْت')]:
        if ident in keys and pattern in vocal: return ident
    fixed = {'allow-v':'آذَن', 'more-ignorant':'أَجْهَل','magic':'سِحْر','hair':'شَّعْر','longing':'شَّوْق','ignorance':'جَهْل','love-affection':'وُدّ','plot-n':'مَكْر'}
    for ident,pattern in fixed.items():
        if ident in keys and pattern in vocal: return ident
    for group,target in [(('wave','m-wave'),'wave'),(('shadow','shade-tree'),'shadow'),(('attendant','serve'),'attendant'),(('subduer','all-mighty'),'subduer'),(('holy','m-holy'),'m-holy'),(('regret','be-sorry'),'be-sorry'),(('rebellion','recklessness'),'recklessness'),(('benefit-n','benefit'),'benefit-n'),(('mock','mock-laugh'),'mock-laugh'),(('shout','cry-out'),'cry-out'),(('trial-temptation','seduce-trial'),'seduce-trial'),(('seek-help','rescue-seek'),'rescue-seek'),(('point','lower'),'point')]:
        if set(group)<=keys: return target
    if 'toil' in keys: return 'toil' if 'تَعَبًا' in vocal else 'be-tired'
    if 'or' in keys: return 'or'
    if 'coming' in keys: return 'give' if 'آتَا' in vocal else 'coming'
    if 'settlement' in keys: return 'settlement'
    if 'live-life' in keys: return 'live-life'
    if 'possessor' in keys and 'ذِي' in vocal: return 'possessor'
    if 'm-toil' in keys: return 'm-toil' if 'تَعَبًا' in vocal else 'be-tired'
    if 'mislead' in keys: return 'mislead' if 'أَضَلَّ' in vocal or 'يُضِل' in vocal else 'stray'
    if 'can' in keys and 'consider-august' in keys: return 'can'
    if 'oppress' in keys and 'أَظْلَمُ' in vocal: return 'more-unjust'
    if 'harder' in keys and 'أَشُقَّ' in vocal: return 'harder'
    if 'then' in keys: return 'here-place' if 'ثَمَّ' in vocal else 'then'
    if 'crime' in keys: return 'indeed-jaram' if 'جَرَمَ' in vocal else 'crime'
    if {'talk-to','speak'} <= keys: return 'talk-to' if 'كَلَّم' in vocal else 'speak'
    if {'spoil-perish','turn-redirect'} <= keys: return 'spoil-perish' if 'تَلِفَ' in vocal else 'turn-redirect'
    if 'take-in-death' in keys: return 'take-in-death'
    if {'pleasant','be-soft-good'} <= keys: return 'be-soft-good'
    if {'force-unwilling','loathe-v'} <= keys: return 'loathe-v' if 'يَكْرَه' in vocal else 'force-unwilling'
    if frozenset(keys) in defaults: return defaults[frozenset(keys)]
    if {'when-if','therefore'} <= keys: return 'therefore' if 'ً' in vocal else 'when-if'
    if {'perish','destroy'} <= keys: return 'destroy' if any(x in vocal for x in ('أَهْلَ','تُهْلِ','يُهْلِ')) else 'perish'
    if {'escape','save'} <= keys: return 'save' if 'أَنْجَ' in vocal else 'escape'
    if {'man','leg'} <= keys: return 'leg' if 'رِجْل' in vocal else 'man'
    if {'young-man','grow-grey'} <= keys: return 'young-man' if 'شَابّ' in vocal else 'grow-grey'
    if {'nurse-feed','suckle'} <= keys: return 'nurse-feed' if 'رْضِع' in vocal else 'suckle'
    if {'first-fem','more-deserving'} <= keys: return 'first-fem' if 'أُولَى' in vocal else 'more-deserving'
    if {'m-dream','restraint'} <= keys: return 'restraint' if 'حِلْم' in vocal else 'm-dream'
    if {'flash','dazzle'} <= keys: return 'dazzle' if 'بَرِق' in vocal else 'flash'
    if {'come-close','bring-close'} <= keys:
        return 'come-nearer' if 'تَقَرَّب' in vocal else ('bring-close' if 'قَرَّب' in vocal else ('closer' if 'أَقْرَب' in vocal else 'come-close'))
    if {'anger','anger-iv'} <= keys: return 'anger-iv' if 'أَغْضَب' in vocal or 'يُغْضِب' in vocal else 'anger'
    if {'separate-ii','separate-i'} <= keys: return 'separate-ii' if 'فَرَّق' in vocal or 'فَرِّق' in vocal or 'يُفَرَّق' in vocal else 'separate-i'
    if {'coolness','quench-cool'} <= keys: return 'coolness' if 'بَرْد' in vocal else 'quench-cool'
    if {'muslim','unblemished'} <= keys: return 'unblemished' if 'مُسَلَّم' in vocal else 'muslim'
    if {'repent','repent-v'} <= keys: return 'repent-v'
    if {'yes','blessing'} <= keys: return 'yes' if 'نَعَمْ' in vocal else 'blessing'
    if 'salih' in keys: return 'righteous' if 'righteous' in keys else 'salih'
    if {'thirst','thirst-n'} <= keys: return 'thirst' if 'عَطِش' in vocal else 'thirst-n'
    if {'amazement','marvel'} <= keys: return 'marvel' if 'عَجِب' in vocal else 'amazement'
    if {'do','act'} <= keys: return 'act' if 'فَعْلَ' in vocal else 'do'
    if {'be-content-eye','settle-standing'} <= keys: return 'be-content-eye' if 'قَرَّ' in vocal or 'قُرَّ' in vocal else 'settle-standing'
    if {'rebuke-n','chide'} <= keys: return 'rebuke-n' if 'زَجْر' in vocal else 'chide'
    if 'longing' in keys and 'شَوْق' in vocal: return 'longing'
    if 'hair' in keys and 'شَعْر' in vocal: return 'hair'
    if 'injustice' in keys: return 'injustice' if 'ظُلْم' in vocal else 'oppress'
    if 'rate-estimation' in keys:
        return 'consider-august' if 'قَدَّر' in vocal else ('destiny' if 'قَدَر' in vocal else 'rate-estimation')
    for primary, secondary, pattern in [('kill','kill-intensive','قَتِّ'),('slaughter','slaughter-intensive','ذَبِّ'),('worship','enslave-ii','عَبَّ'),('cut-v','cut-intensive','قَطِّ'),('appear','appear-iv','ُظْهِ')]:
        if {primary,secondary} <= keys: return secondary if pattern in vocal else primary
    for group,target in [(('youth','lad-assistant'),'lad-assistant'),(('stay','put-upright'),'put-upright'),(('drink','make-drink'),'drink')]:
        if set(group)<=keys: return target
    if {'be-shy','spare-life'}<=keys: return 'spare-life'
    if {'bounty','award-prefer'}<=keys: return 'award-prefer' if 'ضَّ' in vocal else 'bounty'
    if {'get-weaker','strength-n'}<=keys: return 'strength-n' if 'ضَعْف' in vocal else 'get-weaker'
    if {'attend','urban-life'}<=keys: return 'urban-life' if 'حَضَرِ' in vocal else 'attend'
    if {'be-unable','incapacity'}<=keys: return 'incapacity' if 'عَجْز' in vocal else 'be-unable'
    if 'slaughter-n' in keys and 'ذَبْح' in vocal: return 'slaughter-n'
    if {'seek','request-n'} <= keys: return 'request-n' if 'طَلَبُ' in vocal else 'seek'
    if {'wiser','understand-v'} <= keys: return 'wiser' if 'أَعْقَلَ' in vocal else 'understand-v'
    if {'food-sustenance','power'} <= keys: return 'power' if 'قُوَّ' in vocal else 'food-sustenance'
    if {'argument','year-hijja'} <= keys: return 'year-hijja' if 'حِجَج' in vocal else 'argument'
    return h.choose(ids,vocal)



BASE_RESOLVE = b.resolve

FORCED = {'أَنْ': 'to-verb', 'وَأَنْ': 'to-verb', 'إِنْ': 'if', 'وَإِنْ': 'if', 'أَنَا': 'i', 'وَأَنَا': 'i', 'لَمَّا': 'until-when', 'فَلَمَّا': 'until-when', 'وَلَمَّا': 'until-when', 'أَمَّا': 'when-surprise', 'وَهُمْ': 'they', 'بَنُو': 'son', 'وَبَنُو': 'son', 'لِبَنِي': 'son', 'رَبَّنَا': 'lord', 'رَبُّنَا': 'lord', 'رَبِّنَا': 'lord', 'بِرَبِّنَا': 'lord', 'رَبِّي': 'lord', 'رَبِّيَ': 'lord', 'الْمَنَّ': 'manna', 'الْمَنُّ': 'manna', 'بِكَلِمَاتِهِ': 'word', 'وَحْيِ': 'revelation-n', 'بِوَحْيِ': 'revelation-n', 'أَلْهَمَ': 'inspire', 'وَأَلْهَمَهَا': 'inspire', 'وَيُصَلُّونَ': 'pray', 'أَفْضَلَ': 'better', 'فَضَّلَكُمْ': 'award-prefer', 'فَضَّلَهُمْ': 'award-prefer', 'وَفَضَّلَكُمْ': 'award-prefer', 'أُمِرَ': 'command', 'أَزَالُ': 'cease', 'أَغَيْرَ': 'other-than', 'وَيَضِيقُ': 'be-narrow', 'قُلْتُمْ': 'say', 'وَأُشْرِبُوا': 'make-drink', 'لِتُغْرِقَ': 'drown-v', 'وَأَغْرَقَ': 'drown-v', 'وَدَعَا': 'call', 'فَأَبَوْا': 'refuse', 'وَعِيدُ': 'warning-threat', 'الْمَلَأَ': 'notables', 'سَفَرِنَا': 'journey-n', 'أَنَّهُ': 'anna', 'وَأَنَّهُ': 'anna', 'لَوْنُهَا': 'colour', 'لَوْنِهَا': 'colour', 'نِسْيَانًا': 'sleep-forgot', 'حَرَّ': 'heat', 'ضَعْفَ': 'strength-n', 'ضَعْفَهُ': 'strength-n', 'وَالضَّعْفِ': 'strength-n', 'الشَّابَّ': 'young-man', 'الشَّابُّ': 'young-man', 'الشَّابِّ': 'young-man', 'كَيْدُ': 'plot-n', 'وَلِيدًا': 'infant-walid', 'لِكَرَمِهِ': 'be-generous', 'وَكَرَمَهُ': 'be-generous', 'كَبِدِهَا': 'liver', 'بِحِكْمَتِهِ': 'wisdom', 'الْخُضَرَ': 'vegetables', 'الْخُضَرِ': 'vegetables', 'سَنُقَتِّلُ': 'kill-intensive', 'أَعْلَمُ': 'more-knowledgeable', 'أَعْلَمُهُ': 'more-knowledgeable', 'أَعْلَمِ': 'more-knowledgeable', 'عُلِّمْتَ': 'teach', 'أَتَعْلَمُ': 'know-learn', 'الظُّلْمَ': 'injustice', 'لِلظُّلْمِ': 'injustice', 'الْمُرِّ': 'bitterness', 'وَعَدُوُّ': 'enemy', 'تَقِيهِمْ': 'protection-wqy', 'فَوَقَاهُ': 'protection-wqy', 'كِتَابًا': 'book', 'كِتَابٍ': 'book', 'كَتَبَ': 'write', 'أَلَسْتَ': 'not-be', 'يُذَبِّحُ': 'slaughter-intensive', 'يُذَبِّحُونَ': 'slaughter-intensive', 'عَبَّدْتَ': 'enslave-ii', 'عَمَلَ': 'deed', 'عَمَلَهُ': 'deed', 'عَمَلِ': 'deed', 'وَعَمَلِهِ': 'deed', 'الْعَمَلِ': 'deed', 'لِتُخْرِجُوا': 'bring-out', 'آمَنَ': 'believe-faith', 'آمَنَّا': 'believe-faith', 'أَحَبِّ': 'dearer', 'قَوْلًا': 'saying-n', 'قَوْلِي': 'saying-n', 'لِفَتَاهُ': 'lad-assistant', 'فَتَاهُ': 'lad-assistant', 'وَفَتَاهُ': 'lad-assistant', 'أُولُو': 'possessor', 'أُولِي': 'possessor', 'وَأُولُو': 'possessor', 'فَأَرَدْتُ': 'want', 'فَأَرَدْنَا': 'want'}

FORCED.update({'قِبَلَ': 'on-behalf', 'وَأَقْبَلَ': 'turn-towards', 'وَأَصْلَهُ': 'origin-n', 'وَأَزَالَ': 'remove-iv', 'يَبْلُغَا': 'reach-maturity', 'عَدْنٍ': 'eden', 'وَخُلُقَهُمُ': 'manners-nature', 'يُؤَثِّرْ': 'affect-ii', 'وَسَلَكَ': 'follow-path', 'الْأَمْنِ': 'safety-n', 'الْجِدَّ': 'seriousness', 'يَسْرِيَ': 'night-travel', 'أَنْشَأَ': 'bring-into-being', 'هُدًى': 'guidance-n', 'وَهُدًى': 'guidance-n', 'يُحَدِّثُونَ': 'tell-ii', 'وَبَطَلَ': 'be-invalid', 'وَبَذَلَ': 'give-freely', 'وَبَاءً': 'epidemic-n', 'جُنَّ': 'be-mad', 'وَجُنَّ': 'be-mad', 'قَتْلَنَا': 'killing-n', 'لَيِّنًا': 'gentle-adj', 'يُكَذِّبُونِ': 'deny-ii', 'كَرْهًا': 'reluctance-n', 'نَظَرُهُ': 'gaze-n', 'أَشُدَّهُمَا': 'full-strength', 'الْعُلَى': 'higher-plural', 'سَأَمَ': 'boredom-n', 'غَلَبُ': 'victory-n', 'غَلَبَ': 'victory-n', 'بِجُنَّةِ': 'shield-n', 'وَلِيَ': 'govern-v', 'مَسًّا': 'touch-n', 'حَقَّ': 'be-deserved', 'وَحَقَّ': 'be-deserved', 'بُنَيَّتِي': 'little-daughter', 'بُنَيَّتَيَّ': 'little-daughter', 'كَيْ': 'so-that-ky', 'يَنْعَمُ': 'enjoy-nym', 'يُبَدِّلَ': 'replace-ii', 'لَا': 'not', 'وَلَا': 'not'})

FORCED.update({'أَثَرِي': 'trace', 'أَحَقَّ': 'establish-right', 'أَنْعَمَ': 'bestow', 'أَوَلَوْ': 'if-hypothetical', 'وَلَوْ': 'if-hypothetical', 'الْجَنَّةِ': 'paradise', 'بِاللِّينِ': 'kind-sweet-words', 'تَسُرُّ': 'gladden', 'لِتَسُرَّ': 'gladden', 'جَنَّاتٍ': 'paradise', 'جَنَّاتُ': 'paradise', 'جِدًّا': 'very', 'حَدَثَ': 'happen', 'سَيُبْطِلُهُ': 'nullify', 'عَلَى': 'on', 'وَعَلَى': 'on', 'غُلِبَ': 'overcome', 'كَرِهَ': 'loathe-v', 'لِيَنْعَمَ': 'enjoy-nym', 'وَيَنْعَمُونَ': 'enjoy-nym', 'نَجِّنِي': 'save', 'وَنَجِّنَا': 'save', 'وَنَجِّنِي': 'save', 'وَيُحِقُّ': 'establish-right', 'يَكْذِبْ': 'lie', 'يُبْدِلَهُمَا': 'replace-iv', 'الْغَرَقُ': 'drowning-n', 'غَرَقًا': 'drowning-n', 'غَرَقُ': 'drowning-n', 'وَغَرِقَ': 'drown', 'الْحَقَّ': 'truth', 'الْحَقُّ': 'truth', 'الْحَقِّ': 'truth', 'حَقٌّ': 'truth', 'حَقٍّ': 'truth', 'لِلْحَقِّ': 'truth'})

FORCED.update({'وَأَمَّا': 'when-surprise', 'أَسِحْرٌ': 'magic', 'وَأَحَبِّ': 'dearer', 'أُوذِينَا': 'hurt-iv', 'الطَّلَبُ': 'request-n', 'فَكُلُوا': 'eat', 'قَتْلٍ': 'killing-n', 'قَتْلَ': 'killing-n', 'قَتْلِ': 'killing-n', 'بِقَتْلِ': 'killing-n', 'بُنَيَّتِي': 'little-daughter'})

FORCED.update({'رَفَعَ': 'raise-up', 'يَرْفَعُهُ': 'raise-up', 'تَعْقِلُونَ': 'understand-v', 'عَقَلَهُ': 'understand-v', 'جَزَاءَ': 'recompense-n', 'جَزَاءُ': 'recompense-n', 'وَجَزَاءً': 'recompense-n', 'مُسْتَمِعُونَ': 'listener', 'قُوتَ': 'food-sustenance', 'قُرَّتُ': 'comfort-eye-n', 'حِجَجٍ': 'year-hijja', 'وَعَادَ': 'come-back', 'خَبْطَ': 'beating-blind-n', 'وَخَبْطٌ': 'beating-blind-n', 'فَضْلَنَا': 'bounty', 'أَطَّلِعُ': 'ascend-observe', 'وَحَذَّرَهُمُ': 'warn-caution'})

def forced_resolve(vocal, target):
    original_forms, original_choose = b.forms, b.choose
    try:
        b.forms = {key: [target] for key, ids in original_forms.items() if target in ids}
        b.choose = lambda ids, word: target
        return BASE_RESOLVE(vocal)
    finally:
        b.forms, b.choose = original_forms, original_choose

def resolve(vocal):
    if vocal in FORCED:
        return forced_resolve(vocal, FORCED[vocal])
    key=b.bare(vocal)
    if key in ('له','لها','لهم','لهما','لكم','لي','لنا','بنا') or key[0:1] in ('و','ف') and key[1:] in ('له','لها','لهم','لهما','لكم','لي','لنا'):
        leading=[]
        if key[0] in 'وف': leading=[{'surfaceBare':key[0],'vocabularyId':'and' if key[0]=='و' else 'so','role':'prefix'}]; key=key[1:]
        suffix=dict(b.SUFFIX)[key[1:]]
        target='with-by' if key[0]=='ب' else 'for-to'
        return target,leading+[{'surfaceBare':key[0],'vocabularyId':target,'role':'stem'},{'surfaceBare':key[1:],'vocabularyId':suffix,'role':'suffix'}]
    if vocal == 'أَلَمْ':
        return 'negation-lam',[{'surfaceBare':'أ','vocabularyId':'question','role':'prefix'},{'surfaceBare':'لم','vocabularyId':'negation-lam','role':'stem'}]
    if vocal == 'أَذَلِكَ':
        return 'that',[{'surfaceBare':'أ','vocabularyId':'question','role':'prefix'},{'surfaceBare':'ذلك','vocabularyId':'that','role':'stem'}]

    if key in ('إحداهما','إحداكما'):
        return 'one-feminine', [{'surfaceBare':'إحدا','underlying':'إِحْدَى','vocabularyId':'one-feminine','role':'stem'}, {'surfaceBare':key[4:],'vocabularyId':'both' if key.endswith('هما') else 'you-two','role':'suffix'}]
    if key in ('لئن','أئن','لئلا','عما'):
        pre,stem,target = {'لئن':('ل','ئن','if'),'أئن':('أ','ئن','inna'),'لئلا':('ل','ئلا','so-that-not'),'عما':('ع','ما','what')}[key]
        pid={'لئن':'emphasis','أئن':'question','لئلا':'for-to','عما':'about'}[key]
        return target,[{'surfaceBare':pre,'vocabularyId':pid,'role':'prefix' if key!='عما' else 'stem','underlying':{'ع':'عَنْ'}.get(pre,pre)}, {'surfaceBare':stem,'vocabularyId':target,'role':'stem','underlying':b.lexicon[target]['lemma']}]
    if key.startswith('ل') and key[1:] in ('ساحران','مكر','وددنا'):
        target,parts=h.resolve(vocal[2:])
        return target,[{'surfaceBare':'ل','vocabularyId':'emphasis','role':'prefix'},*parts]
    return h.resolve(vocal)


def light(vocal):
    key = b.bare(vocal)
    ident, _ = resolve(vocal)
    if ident == 'king': return key.replace('ملك', 'مَلِك').replace('ملوك', 'مُلوك')
    if ident == 'sovereignty': return key.replace('ملك', 'مُلْك')
    if ident == 'angel': return key.replace('ملك', 'مَلَك')
    if key in b.SELECTIVE: return b.SELECTIVE[key]
    if vocal in PASSIVE:
        return re.sub(r'[ًٌٍ]$', '', vocal)
    return ''.join(c for c in vocal if not b.MARKS.fullmatch(c) or c == '\u0651')

PASSIVE = {w: (None, 'passive form: '+en, ur) for w,en,ur in [
    ('وُلِدَ','was born','پیدا ہوا'), ('يُقَالُ','is called','کہا جاتا ہے'), ('وَيُقَالُ','is called','کہا جاتا ہے'),
    ('قِيلَ','was said','کہا گیا'), ('فَقِيلَ','was said','کہا گیا'), ('وَقِيلَ','was said','کہا گیا'),
    ('أُرْسِلَ','was sent','بھیجا گیا'), ('أُعْطُوا','were given','دیے گئے'),
    ('أُمِرَ','was commanded','حکم دیا گیا'), ('أُمِرُوا','were commanded','حکم دیا گیا'),
    ('أُوذِينَا','we were harmed','ہمیں ستایا گیا'), ('عُلِّمْتَ','you were taught','تمہیں سکھایا گیا'),
    ('فَأُحْرِقَ','was burned','جلا دیا گیا'), ('قُتِلَ','was killed','قتل ہوا'),
    ('غُلِبَ','was defeated','مغلوب ہوا'), ('مُنِعُوا','were prevented','روکے گئے'),
    ('نُودِيَ','was called','پکارا گیا'), ('وَأُشْرِبُوا','were made to absorb','دل میں بٹھا دیا گیا'),
    ('وَأُلْقِيَ','were cast','ڈال دیے گئے'), ('وَمُنِحَ','was granted','عطا کیا گیا'),
    ('وَذُبِحَ','was slaughtered','ذبح ہوا'), ('تُذْبَحُ','is slaughtered','ذبح کی جاتی ہے'),
    ('فُتِنْتُمْ','you were tested','تم آزمائے گئے'), ('وَفُتِنَ','was tested','آزمایا گیا'),
    ('يُوحَى','is revealed','وحی کی جاتی ہے'), ('يُعْبَدَ','be worshipped','عبادت کی جائے'),
    ('تُؤْمَرُونَ','you are commanded','تمہیں حکم دیا جاتا ہے'), ('وَتُذْكَرُ','is mentioned','ذکر کی جاتی ہے'),
    ('يُفَرَّقَ','be separated','جدا کیا جائے'), ('يُقَصَّ','be narrated','بیان کیا جائے')
]}


def make_line(vocal, ident, pages):
    result = b.make_line(vocal, ident, pages)
    for token in result['tokens']:
        if token['vocalized'] in PASSIVE:
            _, en, ur = PASSIVE[token['vocalized']]
            token['usage'] = b.bilingual(en + '; passive', ur + '؛ مجہول')
        if token['vocalized'] in ('وُلِدَ', 'يُقَالُ'):
            token['usage'] = b.bilingual('was born; passive' if token['vocalized'] == 'وُلِدَ' else 'is called; passive', 'پیدا ہوا؛ مجہول' if token['vocalized'] == 'وُلِدَ' else 'کہا جاتا ہے؛ مجہول')
        if token['vocalized'] == 'إِنْ' and ('إِنْ تُرِيدُ إِلَّا' in vocal or 'إِنْ يَتَّبِعُونَ إِلَّا' in vocal or 'إِنْ هِيَ إِلَّا' in vocal):
            token['vocabularyId'] = 'negation-in'
            next(p for p in token['parts'] if p['role']=='stem')['vocabularyId']='negation-in'
        if token['vocabularyId']=='water-spring' and not any(x in vocal for x in ('اثْنَتَا','عُيُونٍ','عُيُونًا','وَعُيُونُ','عُيُونُ الْأَرْضِ')):
            token['vocabularyId']='eye'
            next(p for p in token['parts'] if p['role']=='stem')['vocabularyId']='eye'
        if token['vocabularyId']=='spare-life' and 'تَعِيشُ فِيهَا' in vocal:
            token['usage']=b.bilingual('survive; remain alive', 'زندہ رہنا')
    return result

def main():
    load_lexicon()
    b.choose, b.resolve, b.light = choose, resolve, light
    b.lexicon['adoption-n']['root']='أ خ ذ'
    b.lexicon['paradise']['meanings']=b.bilingual('garden; orchard; Paradise (according to context)', 'باغ؛ جنت؛ سیاق کے مطابق')
    b.lexicon['negation-in'] = {'id': 'negation-in', 'partOfSpeech': 'particle', 'lemma': 'إِنْ', 'root': None, 'meanings': b.bilingual('not (with إلا)', 'نہیں؛ الا کے ساتھ نفی'), 'rootNote': b.bilingual('Function word.', 'حرف۔')}
    text = (ROOT / 'data/stories/06-musa.vocalized.txt').read_text(encoding='utf-8')
    refs = [(79, 24), (43, 51), (28, 4), (28, 7), (28, 9), (28, 8), (28, 13), (28, 15), (28, 17), (28, 18), (28, 19), (28, 20), (28, 21), (28, 22), (28, 23), (28, 24), (28, 25), (28, 25), (28, 26), (28, 27), (28, 27), (28, 28), (28, 28), (20, 10), (20, 11), (20, 12), (20, 13), (20, 14), (20, 15), (20, 17), (20, 18), (20, 18), (20, 19), (20, 20), (20, 21), (20, 22), (28, 32), (28, 33), (26, 10), (26, 11), (26, 12), (26, 13), (26, 14), (26, 15), (26, 16), (26, 17), (20, 44), (26, 18), (26, 19), (26, 20), (26, 21), (26, 22), (26, 23), (26, 24), (26, 25), (26, 26), (26, 27), (26, 28), (20, 51), (20, 52), (20, 53), (26, 29), (26, 30), (26, 31), (26, 32), (26, 33), (26, 34), (20, 63), (10, 77), (10, 78), (26, 35), (26, 39), (26, 40), (26, 41), (26, 42), (26, 43), (26, 44), (20, 66), (20, 68), (20, 69), (10, 81), (10, 82), (26, 45), (7, 118), (20, 70), (7, 120), (7, 121), (7, 122), (7, 123), (26, 49), (7, 123), (7, 124), (26, 50), (26, 51), (20, 73), (20, 74), (20, 75), (20, 76), (7, 127), (7, 127), (43, 51), (43, 52), (28, 38), (28, 38), (20, 4), (20, 6), (43, 84), (40, 26), (40, 28), (40, 28), (40, 28), (40, 29), (40, 29), (40, 30), (40, 31), (80, 34), (80, 35), (80, 36), (80, 37), (43, 67), (23, 101), (40, 16), (40, 32), (40, 33), (40, 34), (40, 38), (40, 39), (40, 41), (40, 42), (53, 23), (40, 43), (40, 44), (40, 45), (29, 8), (66, 11), (7, 128), (7, 129), (7, 129), (10, 84), (10, 85), (10, 86), (10, 87), (7, 132), (7, 133), (26, 62), (44, 24), (10, 90), (4, 18), (6, 158), (10, 91), (10, 92), (44, 25), (44, 26), (44, 27), (44, 28), (44, 29), (2, 60), (2, 61), (2, 61), (2, 61), (2, 58), (2, 59), (2, 67), (2, 68), (2, 69), (2, 70), (2, 71), (2, 70), (2, 71), (53, 28), (24, 40), (7, 142), (20, 83), (20, 84), (7, 143), (6, 103), (59, 21), (7, 143), (7, 144), (2, 55), (7, 155), (7, 146), (7, 138), (7, 140), (20, 88), (20, 89), (7, 148), (20, 90), (20, 91), (20, 92), (20, 93), (20, 94), (7, 150), (7, 151), (20, 95), (20, 96), (20, 97), (2, 54), (7, 152), (5, 20), (5, 21), (5, 21), (5, 22), (5, 22), (5, 23), (5, 24), (5, 25), (5, 26), (18, 61), (18, 62), (18, 63), (18, 64), (18, 66), (18, 69), (18, 72), (18, 73), (18, 74), (18, 75), (18, 77), (18, 77), (18, 78), (18, 80), (18, 81), (18, 82), (12, 76), (3, 117)]
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
            sections.append({'id': sid, 'number': int(number), 'sourceSectionNumber': int(number) if int(number)<=26 else int(number)-26, 'sourcePart': 'A' if int(number)<=26 else 'B', 'title': heading['text'], 'titleVocalized': title,
                             'titleEnglish': english, 'titleTokens': heading['tokens'], 'lines': []})
        elif raw.startswith('@'):
            pages = [int(p) for p in raw[1:].split(',')]
        elif raw:
            section = sections[-1]
            section['lines'].append(make_line(raw, f"{section['id']}-l{len(section['lines'])+1:03d}", pages.copy()))
    template = json.loads((ROOT / 'data/stories/03-nooh.json').read_text(encoding='utf-8'))
    source = ROOT / 'books/Qisas Story 6 Sayyiduna Musa (AS).pdf'
    checksum = hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else json.loads(DEST.read_text(encoding='utf-8'))['source']['sha256']
    editorial = template['editorial'].copy()
    editorial.update({'method': 'Manual transcription checked against all 83 rendered PDF pages; editorial grammatical vocalization and bilingual vocabulary.',
        'corrections': [
            {'pdfPage': 9, 'note': 'Corrected demonstrative agreement: لعل هذه هي السادسة.'},
            {'pdfPage': 40, 'note': 'Restored the verb خلق in the Quran 20:4 excerpt.'},
            {'pdfPage': 53, 'note': 'Corrected يشكرون to يشكون in the complaint about scarce water.'},
            {'pdfPage': 54, 'note': 'Corrected the damaged verb before القمل to يلعنون.'},
            {'pdfPage': 82, 'note': 'Restored سبوه دعا in the description of responding to insults.'},
            {'note': 'Standardized Quran 20:63 to the Hafs vocalization إن هذان; corrected the order of names in the Quran 20:70 excerpt.'},
            {'note': 'Corrected active agreement in يعاملون بني إسرائيل and the expression وطار نومه.'}],
        'notes': ['PDF pages 1 and 41 are covers (printed 89 and 129); narrative pages are PDF 2–40 and 42–83 (printed 90–128 and 130–171).',
                  'The source contains two parts. Sections are numbered continuously 1–46; sourcePart and sourceSectionNumber preserve the printed numbering.',
                  'Reading units are sentences or connected passages; source repetition is retained.',
                  'Quran excerpts use modern imlai spelling. Verse links are checked against Quran.com; excerpts are not expanded to full verses.',
                  'The ﷺ symbol is expanded for word-by-word reading.',
                  'Added vocalization, morphology and bilingual glosses are editorial preparation.'],
        'referenceSources': [{'label': 'Source story PDF', 'path': 'books/' + source.name}, {'label': 'Quran references and Arabic text', 'url': 'https://quran.com'}, {'label': 'Quranic Arabic Corpus', 'url': 'https://corpus.quran.com'}]})
    story = {k: template[k] for k in ('schemaVersion', 'language', 'direction', 'meaningLanguages')}
    story.update({'id': '06-musa', 'number': 6, 'titleEnglish': 'Musa (Moses)', 'titleUrdu': 'حضرت موسیٰ علیہ السلام',
        'description': b.bilingual('Read the story of Musa, from his birth in Egypt to his journey with Khadir, in 46 chapters.', 'حضرت موسیٰ کی پیدائش، فرعون سے مقابلہ اور خضر کے ساتھ سفر کی کہانی؛ ۴۶ ابواب۔'),
        'source': {'file': 'books/' + source.name, 'sha256': checksum, 'pdfPages': 83, 'coverPage': 1, 'frontMatterPages': [1,41], 'printedPageRange': [90,171]},
        'editorial': editorial, 'sections': sections})
    for key, vocal in [('title', 'مُوسَى'), ('subtitle', 'قِصَّةُ سَيِّدِنَا مُوسَى')]:
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
