import sys, os, re, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_lib import *
SRC = sys.argv[1]; OUT = sys.argv[2]
entries, news, excluded = [], [], []
for fn in sorted(os.listdir(SRC)):
    book = fn[:-5]
    path = os.path.join(SRC, fn)
    if book in SKIP_BOOKS:
        excluded.append({'kaynak': book, 'baslik': '(tüm defter)', 'neden': SKIP_BOOKS[book]}); continue
    for n in read_enex(path):
        if book in DICT_BOOKS:
            if not SENSITIVE.search(n['title'] + '\n' + n['content']):
                parts = split_pairs(n, book)
                if parts:
                    entries.extend(parts); continue
            e, why = entry_from_note(n, book)
            if e and len(e['ornekler']) > 20:
                e['yayinda'] = 'HAYIR'
                e['kontrol'] = (f"liste notu ({len(e['ornekler'])} satır): sitede gösterilmiyor, maddelere bölünmeli; " + e['kontrol']).strip('; ')
            (entries.append(e) if e else excluded.append({'kaynak': book, 'baslik': n['title'], 'neden': why, 'icerik': ' / '.join(l['text'] for l in enml_lines(n['content']))[:500]}))
        elif book in NEWS_BOOKS:
            e, why = news_from_note(n, book)
            (news.append(e) if e else excluded.append({'kaynak': book, 'baslik': n['title'], 'neden': why, 'icerik': ' / '.join(l['text'] for l in enml_lines(n['content']))[:500]}))
        else:
            excluded.append({'kaynak': book, 'baslik': n['title'], 'neden': 'tanımsız defter'})

# bağlantıları temizle, yayınlanmayacakları ayır
from newslike import news_reason
URL = re.compile(r'https?://\S+|www\.\S+')
for e in entries:
    e['anlamlar'] = [a for a in (URL.sub('', x).strip(' /;,') for x in e['anlamlar']) if a]
    e['not'] = URL.sub('', e['not']).strip()
    e['ornekler'] = [o for o in ({'fa': URL.sub('', x['fa']).strip(), 'tr': URL.sub('', x['tr']).strip()} for x in e['ornekler']) if o['fa'] or o['tr']]
    e['kontrol'] = e['kontrol'].replace('bağlantı (link) içeriyor', '').strip('; ')
    reason = ''
    if e['baslik'].startswith('Has sisteminde'):
        reason = 'iş yeri sistemi (Has) arayüz terimi'
    elif e.get('yayinda') == 'HAYIR':
        reason = 'Türkçesi olmayan liste notu'
    else:
        r = news_reason(e)
        if r: reason = 'haber cümlesi (' + r + ')'
    e['gizli'] = reason
    if reason:
        e['kontrol'] = (reason + '; ' + e['kontrol']).strip('; ')

# yinelenenler
groups = collections.defaultdict(list)
for idx, e in enumerate(entries):
    if e['farsca']: groups[fa_key(e['farsca'])].append(idx)
for k, idxs in groups.items():
    if len(idxs) > 1:
        for j in idxs:
            others = ', '.join(entries[o]['kaynak'] for o in idxs if o != j)
            f = f'aynı kelime başka notta da var ({len(idxs)} not)'
            entries[j]['kontrol'] = (entries[j]['kontrol'] + '; ' + f).strip('; ')

print('yayınlanmayan:', collections.Counter(e['gizli'].split(' (')[0] for e in entries if e['gizli']))
json.dump({'entries': entries, 'news': news, 'excluded': excluded}, open(OUT, 'w'), ensure_ascii=False, indent=0)
print('sözlük maddesi:', len(entries), '| haber çevirisi:', len(news), '| hariç:', len(excluded))
c = collections.Counter(e['tur'] for e in entries); print(c)
fc = collections.Counter()
for e in entries:
    for f in filter(None, e['kontrol'].split('; ')): fc[re.sub(r'\(\d+ not\)', '', f)] += 1
print('kontrol bayrakları:', fc)
print('hariç nedenleri:', collections.Counter(x['neden'] for x in excluded))
