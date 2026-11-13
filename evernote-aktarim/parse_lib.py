"""Evernote ENEX defterlerini sözlük maddelerine ve haber çevirisi çiftlerine dönüştürür."""
import sys, os, re, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from enml import read_enex, enml_lines
from script_util import script, AR
from textnorm import clean_display, fa_key, tr_key, translit_score


DICT_BOOKS = {
    'FARSÇA KELİMELER': ('Kelime', ''),
    'Edatlar, Bağlaçlar ve Kısaltmalar': ('Edat / bağlaç', ''),
    'سر': ('Deyim / ifade', 'سر'),
    'کار': ('Deyim / ifade', 'کار'),
    'eş anlamlı ya da birlikte kullanılan ifadeler': ('İkileme', ''),
    'Argo Terimler Farsça': ('Argo', ''),
    'Deyim ve Atasözleri': ('Deyim / atasözü', ''),
    'diyalog cümleleri': ('Günlük konuşma', ''),
    'kalıp ifadeler': ('Kalıp ifade', ''),
    'Tanınmış Kişiler': ('Özel isim: kişi', ''),
    'Yer Adları': ('Özel isim: yer', ''),
    'siyasi grup - oluşum - örgüt - parti - kurum - şirket - spor kulübü adları': ('Özel isim: kurum', ''),
    'önemli gün - program - olaylar': ('Özel isim: gün / olay', ''),
}
NEWS_BOOKS = {
    'Flaş': 'Flaş', 'Hazır flaşlar': 'Flaş', 'Titr': 'Titr',
    'Foto ve Video alt yazıları': 'Foto / video alt yazısı', 'örnek alt yazılar': 'Alt yazı',
    'İnfografikler': 'İnfografik', 'Haber Geçmişi - سابقه خبر': 'Haber geçmişi',
}
SKIP_BOOKS = {'haber akademisi 4 ders notları': 'kişisel ders notu (telefon/şifre içeriyor)',
              'takip edilecek kişiler': 'kişisel liste', 'medya farsçası notları': 'serbest yazım notu'}

SENSITIVE = re.compile(r'(\b0?5\d{2}[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}\b|\+90[\s\d]{9,}|\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b|\bTR\d{2}[\s]?\d{4}[\s]?\d{4}|^\s*(şifre|parola|password|kullanıcı( adı)?|username)\s*[:=]\s*\S+)', re.I | re.M)
MARKER = re.compile(r'^\s*(örnek(ler)?\s*(cümle(ler)?|cumle(ler)?)?|ör\.?|misal(ler)?|example|kullanım(ı)?|مثال)\s*[:：\-]?\s*', re.I)
BULLET = re.compile(r'^\s*(\d+\s*[-.):]|[•\-–—*·▪◦]|[a-zçğıöşü]\))\s*', re.I)

def date(s):
    return f"{s[0:4]}-{s[4:6]}-{s[6:8]}" if len(s) >= 8 else ''

def strip_bullet(s):
    return BULLET.sub('', s, count=1).strip()

LABEL = re.compile(r'^[\sً-ٟ]*(?P<k>eş\s*anlaml[ıi](s[ıi])?|eş\s*anlam[ıi]|eşanlamlılar[ıi]?|zıt\s*anlaml[ıi](s[ıi])?|karş[ıi]t\s*anlam[ıi]?l?[ıi]?(s[ıi])?|not|örnek(ler)?\s*(cümle(ler)?|cumle(ler)?)?|örmek\s*cümle|ör\.?|misal(ler)?|مثال)\s*[:：\-]\s*|^[\sً-ٟ]*(?P<k2>örnek\s*(cümle(ler)?|cumle(ler)?)?|örnekler|örmek\s*cümle|misal(ler)?)\s*$', re.I)
def label(t):
    m = LABEL.match(t)
    if not m: return None, t
    k = tr_key(m.group('k') or m.group('k2') or '')
    rest = t[m.end():].strip()
    if k.startswith('es'): return 'syn', rest
    if k.startswith('zit') or k.startswith('karsit'): return 'ant', rest
    if k == 'not': return 'note', rest
    return 'ex', rest

def tidy(s):
    s = strip_bullet(s)
    return re.sub(r'[\s,;،]+$', '', s).strip()

def split_list(s):
    return [x.strip() for x in re.split(r'[,،;؛/]| و ', s) if x.strip()]

def entry_from_note(n, book):
    tur, etiket = DICT_BOOKS[book]
    title = clean_display(n['title'])
    if title.lower() in ('untitled note', 'adsız not', 'başlıksız not', 'isimsiz'): title = ''
    raw = enml_lines(n['content'])
    content = []
    for l in raw:
        t = clean_display(l['text'])
        if not t: continue
        content.append({'t': t, 's': script(t), 'it': l['italic'] > 0.8 and script(t) == 'L', 'li': l['li']})
    flags = []
    alltext = title + '\n' + '\n'.join(l['t'] for l in content)
    if SENSITIVE.search(alltext):
        return None, 'hassas bilgi olabilir (telefon/e-posta/şifre)'
    if len(AR.findall(alltext)) < 2:
        return None, 'Farsça metin yok'
    ts = script(title) if title else 'E'
    farsca, okunus, anlamlar, ornekler, syn, ant, notes = '', '', [], [], [], [], []
    i = 0
    turkce_title = ''
    if ts == 'P':
        farsca = title
        while i < len(content) and content[i]['s'] == 'P' and label(content[i]['t'])[0] is None:
            a, b = fa_key(content[i]['t']), fa_key(title)
            if a == b: i += 1; continue
            if i == 0 and b and (b in a or a in b) and len(content[i]['t']) < 80:
                if len(a) > len(b): farsca = content[i]['t']
                i += 1; continue
            break
    else:
        turkce_title = title
        pre = []
        while i < len(content) and content[i]['s'] != 'P':
            pre.append(content[i]); i += 1
        if i < len(content):
            farsca = content[i]['t']; i += 1
            while i < len(content) and content[i]['s'] == 'P' and fa_key(content[i]['t']) == fa_key(farsca): i += 1
        for p in pre:
            if p['it'] and not okunus: okunus = p['t']; continue
            if tr_key(p['t']) != tr_key(title): anlamlar.append(tidy(p['t']))
    # okunuş
    if i < len(content) and content[i]['s'] == 'L' and not okunus and label(content[i]['t'])[0] is None:
        c = content[i]; sc = translit_score(farsca, c['t'])
        if c['it'] or (sc >= 0.6 and not c['li']) or sc >= 0.75:
            okunus = c['t']; i += 1
    if turkce_title:
        anlamlar.insert(0, turkce_title)
    mode = 'mean'      # mean -> ex ; syn/ant: sonraki Farsça satırlar eş/zıt anlamlıdır
    cur = None
    while i < len(content):
        c = content[i]; t = c['t']; i += 1
        kind, rest = label(t)
        if kind in ('syn', 'ant'):
            target = syn if kind == 'syn' else ant
            if rest: target.extend(split_list(rest)); mode = 'mean' if mode == 'mean' else 'ex'
            else: mode = kind
            continue
        if kind == 'note':
            notes.append(rest); continue
        if kind == 'ex':
            mode = 'ex'
            if not rest: continue
            t = rest
        s = script(t)
        if mode in ('syn', 'ant'):
            if s == 'P':
                (syn if mode == 'syn' else ant).extend(split_list(t)); continue
            mode = 'mean' if not ornekler else 'ex'
        if mode == 'mean':
            if s == 'P':
                mode = 'ex'
            else:
                if c['it'] and not okunus and not anlamlar:
                    okunus = t; continue
                tt = tidy(t)
                if tt and (not turkce_title or tr_key(tt) != tr_key(turkce_title)):
                    anlamlar.append(tt)
                continue
        # örnekler
        if s == 'P':
            tt = strip_bullet(t)
            if cur is not None and not cur['tr'] and len(cur['fa']) >= 40 and not re.search(r'([.!?؟:»"\)]|د|است)$', cur['fa']):
                cur['fa'] = cur['fa'] + ' ' + tt          # satır sonunda bölünmüş cümle
            else:
                cur = {'fa': tt, 'tr': ''}; ornekler.append(cur)
        else:
            if cur is not None:
                cur['tr'] = (cur['tr'] + ' ' + strip_bullet(t)).strip()
            else:
                anlamlar.append(tidy(t))
    if okunus and translit_score(farsca, okunus) < 0.35 and not anlamlar:
        anlamlar.append(tidy(okunus)); okunus = ''
    if not farsca: flags.append('Farsça başlık bulunamadı')
    if not anlamlar: flags.append('Türkçe anlam yok')
    if okunus and translit_score(farsca, okunus) < 0.35: flags.append('okunuş kelimeyle uyuşmuyor olabilir')
    if not okunus and tur in ('Kelime', 'Edat / bağlaç', 'Deyim / ifade', 'İkileme', 'Argo'): flags.append('okunuş yok')
    if re.search(r'https?://', alltext): flags.append('bağlantı (link) içeriyor')
    return {
        'farsca': farsca, 'okunus': okunus,
        'anlamlar': [a for a in anlamlar if a],
        'ornekler': ornekler, 'esanlamli': syn, 'zitanlamli': ant, 'not': ' '.join(notes),
        'tur': tur, 'etiket': etiket, 'kontrol': '; '.join(flags),
        'kaynak': book, 'tarih': date(n['created']), 'baslik': clean_display(n['title']),
    }, None

def translit_score_ok(content, i, title):
    # ilk satır Farsça ve başlığı içeriyor/benziyor mu
    a, b = fa_key(content[i]['t']), fa_key(title)
    return bool(a) and bool(b) and (a in b or b in a)

def news_from_note(n, book):
    title = clean_display(n['title'])
    lines = [clean_display(l['text']) for l in enml_lines(n['content'])]
    lines = [l for l in lines if l]
    alltext = title + '\n' + '\n'.join(lines)
    if SENSITIVE.search(alltext):
        return None, 'hassas bilgi olabilir (telefon/e-posta/şifre)'
    tr, fa = [], []
    if script(title) == 'L': tr.append(title)
    elif script(title) == 'P': fa.append(title)
    for l in lines:
        s = script(l)
        if s == 'P':
            if not fa or fa_key(fa[-1]) != fa_key(l): fa.append(l)
        elif s == 'L':
            if not tr or tr_key(tr[-1]) != tr_key(l): tr.append(l)
        elif s == 'N' and tr: tr.append(l)
    if not fa:
        return None, 'Farsça metin yok'
    return {'turkce': '\n'.join(tr), 'farsca': '\n'.join(fa), 'tur': NEWS_BOOKS[book],
            'tarih': date(n['created']), 'kaynak': book,
            'kontrol': '' if tr else 'Türkçe metin yok'}, None



def split_pairs(n, book):
    """Türkçe satır + Farsça karşılığı şeklinde art arda yazılmış liste notlarını ayrı maddelere böler."""
    tur, etiket = DICT_BOOKS[book]
    ls = [clean_display(l['text']) for l in enml_lines(n['content'])]
    ls = [l for l in ls if l]
    if len(ls) < 20: return None
    pairs, cur = [], None
    for l in ls:
        s = script(l)
        if s == 'L':
            if cur and cur['fa']: pairs.append(cur)
            cur = {'tr': l, 'fa': []}
        elif s == 'P' and cur is not None:
            cur['fa'].append(l)
    if cur and cur['fa']: pairs.append(cur)
    nl = sum(1 for l in ls if script(l) == 'L')
    if len(pairs) < 8 or len(pairs) < 0.6 * nl:
        return None
    out = []
    for c in pairs:
        fa = re.sub(r'^\s*(ترجمه|مترادف فارسی|معادل فارسی)\s*[:：]\s*', '', c['fa'][0]).strip('«»" .').strip()
        syn, ex = [], []
        for x in c['fa'][1:]:
            k, rest = label(x if not x.startswith('مترادف') else 'eş anlamlı: ' + x.split(':', 1)[-1])
            if k == 'syn' or x.startswith('مترادف'):
                syn.append(rest.strip('«»" ').strip())
            else:
                ex.append({'fa': x.strip('«»" *').strip(), 'tr': ''})
        out.append({'farsca': fa, 'okunus': '', 'anlamlar': [tidy(c['tr'])], 'ornekler': ex, 'esanlamli': syn,
                    'zitanlamli': [], 'not': '', 'tur': tur, 'etiket': etiket,
                    'kontrol': 'liste notundan ayrıldı: ' + clean_display(n['title'])[:50],
                    'kaynak': book, 'tarih': date(n['created']), 'baslik': clean_display(n['title']), 'yayinda': 'EVET'})
    return out
