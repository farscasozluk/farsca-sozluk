import re, unicodedata
from difflib import SequenceMatcher
from script_util import script, AR, LA

INVIS = re.compile(r'[‎‏‪-‮⁦-⁩﻿­]')
def clean_display(s):
    s = INVIS.sub('', s)
    s = s.replace('\u064a', '\u06cc').replace('\u0649', '\u06cc').replace('\u0643', '\u06a9')  # ي ى ك -> ی ی ک
    s = s.replace('\u00a0', ' ')
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'\u200c+(?=\s)|(?<=\s)\u200c+', '', s)   # boşluğa yapışık gereksiz yarım boşluk
    s = re.sub(r'\u200c{2,}', '\u200c', s)
    s = s.strip().strip('\u200c').strip()
    return s

HARAKAT = re.compile(r'[ً-ٰٟۖ-ۭـ]')
def fa_key(s):
    s = clean_display(s)
    s = HARAKAT.sub('', s)
    for a, b in (('أ','ا'),('إ','ا'),('ٱ','ا'),('آ','ا'),('ؤ','و'),('ۀ','ه'),('ة','ه'),('ئ','ی'),('ء','')):
        s = s.replace(a, b)
    s = re.sub(r'[‌\s\-–—_/.,،؛:!?؟«»"\'()\[\]]+', '', s)
    return s

TR_FOLD = str.maketrans({'â':'a','î':'i','û':'u','ı':'i','ş':'s','ç':'c','ğ':'g','ö':'o','ü':'u','é':'e','ê':'e','ô':'o','á':'a','í':'i','ú':'u','ā':'a','ī':'i','ū':'u'})
def tr_lower(s):
    return s.replace('I','ı').replace('İ','i').lower()
def tr_key(s):
    s = tr_lower(clean_display(s)).translate(TR_FOLD)
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', s)).strip()

# consonant skeletons for transliteration detection
FA_SK = {'ب':'b','پ':'p','ت':'t','ط':'t','ث':'s','س':'s','ص':'s','ج':'c','چ':'ç','ح':'h','ه':'h','خ':'h','د':'d','ذ':'z','ز':'z','ض':'z','ظ':'z','ر':'r','ژ':'j','ش':'ş','غ':'k','ق':'k','ف':'f','ک':'k','گ':'k','ل':'l','م':'m','ن':'n'}
LA_SK = {'b':'b','p':'p','t':'t','s':'s','c':'c','ç':'ç','h':'h','x':'h','d':'d','z':'z','r':'r','j':'j','ş':'ş','g':'k','ğ':'k','k':'k','q':'k','f':'f','l':'l','m':'m','n':'n'}
def fa_skel(s):
    return ''.join(FA_SK.get(c, '') for c in clean_display(s))
def la_skel(s):
    return ''.join(LA_SK.get(c, '') for c in tr_lower(s))
def translit_score(fa, la):
    a, b = fa_skel(fa), la_skel(la)
    if not a or not b: return 0.0
    return SequenceMatcher(None, a, b).ratio()
