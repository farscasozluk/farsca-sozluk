import re
EXEMPT = {'Deyim / atasözü', 'Günlük konuşma', 'İkileme', 'Argo', 'Edat / bağlaç', 'Deyim / ifade'}
QUOTE_TR = re.compile(r'^[A-ZÇĞİÖŞÜ][\wçğıöşü\.\s]{1,40}:\s*["“]')
QUOTE_FA = re.compile(r'^[؀-ۿ‌\s]{2,30}:\s')
def fa_words(s): return [w for w in re.split(r'[\s‌]+', s) if w]
def news_reason(e):
    if e['tur'] in EXEMPT: return ''
    fa = e['farsca']; tr = e['anlamlar'][0] if e['anlamlar'] else ''
    alltr = ' '.join(e['anlamlar'])
    if re.search(r'[A-ZÇĞİÖŞÜ]{3,}\s*\((AA|DHA|İHA)\)\s*[-–]', alltr + ' ' + ' '.join(o['fa'] + ' ' + o['tr'] for o in e['ornekler'])): return 'ajans metni'
    if len(fa_words(fa)) >= 12 and not e['tur'].startswith('Özel isim'): return 'uzun farsça cümle'
    if QUOTE_TR.search(tr) or QUOTE_FA.search(fa): return 'alıntı'
    if not e['tur'].startswith('Özel isim') and len(tr.split()) >= 10 and (re.search(r'\d', tr) or re.search(r"\s[A-ZÇĞİÖŞÜ][a-zçğıöşü]+", tr)): return 'uzun türkçe haber cümlesi'
    sp = [w for w in fa.strip(' .!؟/').split() if w]
    if (not e['tur'].startswith('Özel isim') and len(sp) >= 7 and re.search(r'(د|است)$', sp[-1])
            and (re.search(r'[0-9۰-۹]', fa + tr) or re.search(r"\s[A-ZÇĞİÖŞÜ][a-zçğıöşü]+", ' ' + ' '.join(tr.split()[1:])))):
        return 'haber başlığı'
    return ''
