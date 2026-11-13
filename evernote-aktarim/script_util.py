import re, unicodedata
AR = re.compile(r'[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]')
LA = re.compile(r'[A-Za-zÀ-ɏḀ-ỿ]')
def script(s):
    a = len(AR.findall(s)); l = len(LA.findall(s))
    if a == 0 and l == 0: return 'N' if s.strip() else 'E'
    if a >= l: return 'P'
    return 'L'
