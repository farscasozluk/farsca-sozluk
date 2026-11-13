#!/usr/bin/env python3
"""Farsça–Türkçe Sözlük: Google E-Tablolar'daki veriden statik site üretir.

Kullanım:
  python build.py --xlsx Farsca_Sozluk.xlsx --out _site
  python build.py --sozluk-csv <URL> --out _site --base-url https://ornek.github.io/sozluk/
  python build.py --xlsx Farsca_Sozluk.xlsx --out preview --preview     (tek sayfalık önizleme)
"""
import argparse, csv, io, json, os, re, shutil, sys, html, hashlib, datetime, urllib.request, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_util import script
from textnorm import clean_display, fa_key, tr_key
from fa_sort import fa_sort_key

HERE = os.path.dirname(os.path.abspath(__file__))
TURLER = ['Kelime', 'Kalıp ifade', 'Deyim / ifade', 'Deyim / atasözü', 'Edat / bağlaç', 'İkileme', 'Argo',
          'Günlük konuşma', 'Özel isim: kişi', 'Özel isim: yer', 'Özel isim: kurum', 'Özel isim: gün / olay']
SOZLUK_COLS = ['Farsça', 'Okunuş', 'Türkçe anlamlar', 'Örnek cümleler', 'Eş anlamlılar', 'Zıt anlamlılar',
               'Not', 'Tür', 'Etiket', 'Yayında', 'Kontrol', 'Kaynak defter', 'Eklenme tarihi']


# ---------- veri okuma ----------
def read_csv_source(src):
    if re.match(r'https?://', src):
        req = urllib.request.Request(src, headers={'User-Agent': 'sozluk-build'})
        raw = urllib.request.urlopen(req, timeout=120).read().decode('utf-8-sig')
    else:
        raw = open(src, encoding='utf-8-sig').read()
    return list(csv.DictReader(io.StringIO(raw)))


def read_xlsx(path):
    from openpyxl import load_workbook
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb['Sözlük']
    rows = ws.iter_rows(values_only=True)
    head = [str(h).strip() if h else '' for h in next(rows)]
    return [{head[i]: ('' if v is None else str(v)) for i, v in enumerate(r) if i < len(head)} for r in rows]


def lines(s):
    return [clean_display(x) for x in str(s or '').replace('\r', '').split('\n') if clean_display(x)]


def is_yes(v):
    return tr_key(v or 'evet') not in ('hayir', 'h', 'no', 'false', '0', 'yok')


def parse_examples(text):
    ex, cur = [], None
    for ln in lines(text):
        if script(ln) == 'P':
            cur = [ln, '']; ex.append(cur)
        elif cur is not None and not cur[1]:
            cur[1] = ln
        elif cur is not None:
            cur[1] += ' ' + ln
        else:
            ex.append(['', ln])
    return ex


def split_terms(s):
    out = []
    for ln in lines(s):
        out.extend(x.strip() for x in re.split(r'[،,;؛]', ln) if x.strip())
    return out


def load_entries(rows):
    ents = []
    for r in rows:
        fa = clean_display(r.get('Farsça', ''))
        mean = lines(r.get('Türkçe anlamlar', ''))
        if not fa or not mean or not is_yes(r.get('Yayında', '')):
            continue
        tur = clean_display(r.get('Tür', '')) or 'Kelime'
        if tur not in TURLER:
            TURLER.append(tur)
        ents.append({
            'f': fa, 'o': clean_display(r.get('Okunuş', '')), 'a': mean,
            'x': parse_examples(r.get('Örnek cümleler', '')),
            's': split_terms(r.get('Eş anlamlılar', '')), 'z': split_terms(r.get('Zıt anlamlılar', '')),
            'n': clean_display(r.get('Not', '')), 't': TURLER.index(tur),
            'e': clean_display(r.get('Etiket', '')), 'd': clean_display(r.get('Eklenme tarihi', ''))[:10],
        })
    return ents


# ---------- gruplama ve adresler ----------
def slugify(fa, used):
    s = re.sub(r'[\s‌]+', '-', fa.strip())
    s = re.sub(r'[/\\?#%&"\'<>:*|.,،؛;!؟()\[\]{}«»]+', '', s).strip('-')
    words = s.split('-')
    if len(words) > 7 or len(s) > 70:
        s = '-'.join(words[:6])[:60].strip('-') + '-' + hashlib.md5(fa.encode()).hexdigest()[:5]
    base, k = s or 'madde', 2
    while s in used:
        s = f'{base}-{k}'; k += 1
    used.add(s)
    return s


def group_entries(ents):
    groups = collections.OrderedDict()
    for e in sorted(ents, key=lambda e: fa_sort_key(e['f'])):
        groups.setdefault(fa_key(e['f']) or e['f'], []).append(e)
    used, out = set(), []
    for key, es in groups.items():
        g = {'f': es[0]['f'], 'o': '', 'a': [], 'x': [], 's': [], 'z': [], 'n': [], 't': [], 'e': [], 'd': ''}
        seen_a, seen_x = set(), set()
        for e in es:
            g['o'] = g['o'] or e['o']
            for a in e['a']:
                if tr_key(a) not in seen_a:
                    seen_a.add(tr_key(a)); g['a'].append(a)
            for x in e['x']:
                k = fa_key(x[0]) + '|' + tr_key(x[1])
                if k not in seen_x:
                    seen_x.add(k); g['x'].append(x)
            for f in ('s', 'z'):
                for v in e[f]:
                    if v not in g[f]: g[f].append(v)
            if e['n'] and e['n'] not in g['n']: g['n'].append(e['n'])
            if e['t'] not in g['t']: g['t'].append(e['t'])
            if e['e'] and e['e'] not in g['e']: g['e'].append(e['e'])
            g['d'] = max(g['d'], e['d'])
        g['n'] = ' '.join(g['n'])
        g['u'] = slugify(g['f'], used)
        out.append(g)
    return out


# ---------- çıktı ----------
def esc(s):
    return html.escape(s or '', quote=True)


def read_asset(name):
    return open(os.path.join(HERE, 'assets', name), encoding='utf-8').read()


def page_shell(title, desc, body, root, canonical='', extra_head=''):
    return f'''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{f'<link rel="canonical" href="{esc(canonical)}">' if canonical else ''}
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='30' height='64' rx='10' fill='%23233f99'/%3E%3Crect x='20' width='44' height='64' rx='10' fill='%230b7f84'/%3E%3Crect x='20' width='12' height='64' fill='%23233f99'/%3E%3Ctext x='17' y='44' font-family='Georgia,serif' font-size='30' font-weight='700' fill='white' text-anchor='middle'%3ET%3C/text%3E%3Ctext x='46' y='44' font-family='Tahoma,sans-serif' font-size='34' font-weight='700' fill='white' text-anchor='middle'%3E%D9%81%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,600;1,7..72,400&family=Markazi+Text:wght@500;700&family=Vazirmatn:wght@400;500;700&display=swap">
<link rel="stylesheet" href="{root}assets/style.css">
{extra_head}
</head>
<body>
{body}
</body>
</html>'''


def header_html(root, q=''):
    return f'''<header class="top">
  <div class="top-in">
    <a class="brand" href="{root}index.html"><span class="logo" aria-hidden="true"><span class="lt">T</span><span class="lf">ف</span></span><span>Farsça–Türkçe Sözlük</span></a>
    <form class="topsearch" action="{root}index.html" method="get" role="search">
      <label class="sr" for="tq">Sözlükte ara</label>
      <input id="tq" name="q" type="search" value="{esc(q)}" placeholder="Farsça, Türkçe ya da okunuşla ara" autocomplete="off">
    </form>
  </div>
</header>'''


def entry_html(g, root, link):
    turs = ''.join(f'<span class="chip">{esc(TURLER[t])}</span>' for t in g['t'])
    tags = ''.join(f'<span class="chip ghost">{esc(e)}</span>' for e in g['e'])
    means = ''.join(f'<li>{esc(a)}</li>' for a in g['a'])
    rel = ''
    for key, label in (('s', 'Eş anlamlılar'), ('z', 'Zıt anlamlılar')):
        if g[key]:
            items = ''.join(f'<a class="term fa" lang="fa" dir="rtl" href="{link(v)}">{esc(v)}</a>' for v in g[key])
            rel += f'<div class="rel"><h3>{label}</h3><div class="terms">{items}</div></div>'
    exs = ''
    if g['x']:
        rows = ''.join(
            f'<li>{f"<p class=fa-s lang=fa dir=rtl>{esc(x[0])}</p>" if x[0] else ""}{f"<p class=tr-s>{esc(x[1])}</p>" if x[1] else ""}</li>'
            for x in g['x'])
        exs = f'<section class="block"><h2>Örnek cümleler</h2><ol class="examples">{rows}</ol></section>'
    note = f'<p class="note">{esc(g["n"])}</p>' if g['n'] else ''
    return f'''<article class="entry">
  <div class="entry-head">
    <h1 class="hw" lang="fa" dir="rtl">{esc(g['f'])}</h1>
    {f'<p class="translit">{esc(g["o"])}</p>' if g['o'] else ''}
    <div class="chips">{turs}{tags}</div>
  </div>
  <section class="block"><h2>Anlamları</h2><ol class="means">{means}</ol>{note}</section>
  {rel}
  {exs}
</article>'''


def build(args):
    srows = read_xlsx(args.xlsx) if args.xlsx else read_csv_source(args.sozluk_csv)
    ents = load_entries(srows)
    if len(ents) < args.min_entries:
        sys.exit(f'HATA: tabloda yalnızca {len(ents)} yayınlanabilir satır bulundu (en az {args.min_entries} bekleniyordu). '
                 'Tablo bağlantısını ve sütun başlıklarını kontrol edin; site değiştirilmedi.')
    groups = group_entries(ents)
    built = datetime.date.today().isoformat()
    print(f'{len(ents)} satır → {len(groups)} madde')

    out = args.out
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(os.path.join(out, 'data'))
    sozluk = {'v': 1, 'built': built, 'turler': TURLER,
              'e': [[g['f'], g['o'], g['a'], g['x'], g['s'], g['z'], g['n'], g['t'], g['e'], g['d'], g['u']] for g in groups]}
    json.dump(sozluk, open(os.path.join(out, 'data', 'sozluk.json'), 'w'), ensure_ascii=False, separators=(',', ':'))

    css, js = read_asset('style.css'), read_asset('app.js')
    app_body = read_asset('app.html')
    if args.preview:
        page = page_shell('Farsça–Türkçe Sözlük', 'Farsça–Türkçe sözlük: kelimeler, okunuşlar, örnek cümleler, kalıp ifadeler ve özel isimler.',
                          app_body.replace('{{ROOT}}', ''), '')
        page = page.replace('<link rel="stylesheet" href="assets/style.css">', f'<style>\n{css}\n</style>')
        page = page.replace('</body>', f'<script>window.SITE_MODE="preview";\n{js}\n</script>\n</body>')
        open(os.path.join(out, 'index.html'), 'w').write(page)
        return

    base = (args.base_url or '').rstrip('/') + '/' if args.base_url else ''
    os.makedirs(os.path.join(out, 'assets'))
    open(os.path.join(out, 'assets', 'style.css'), 'w').write(css)
    open(os.path.join(out, 'assets', 'app.js'), 'w').write(js)
    home = page_shell('Farsça–Türkçe Sözlük', 'Farsça–Türkçe sözlük: kelimeler, okunuşları, örnek cümleler, kalıp ifadeler ve özel isimler.',
                      app_body.replace('{{ROOT}}', ''), '', canonical=base,
                      extra_head='<script>window.SITE_MODE="site";</script>')
    home = home.replace('</body>', '<script src="assets/app.js"></script>\n</body>')
    open(os.path.join(out, 'index.html'), 'w').write(home)

    by_key = {fa_key(g['f']): g for g in groups}
    def link_from_entry(v):
        g = by_key.get(fa_key(v))
        return f'../{g["u"]}/' if g else f'../../index.html?q={urllib.parse.quote(v)}'
    import urllib.parse
    kdir = os.path.join(out, 'k')
    os.makedirs(kdir)
    urls = [base]
    for gi, g in enumerate(groups):
        d = os.path.join(kdir, g['u'])
        os.makedirs(d)
        title = f'{g["f"]} — Türkçe anlamı | Farsça–Türkçe Sözlük'
        desc = f'{g["f"]}' + (f' ({g["o"]})' if g['o'] else '') + ': ' + '; '.join(g['a'])[:150]
        body = header_html('../../') + '<main class="wrap">' + entry_html(g, '../../', link_from_entry) + '</main>' + footer_html(built)
        canon = f'{base}k/{urllib.parse.quote(g["u"])}/' if base else ''
        open(os.path.join(d, 'index.html'), 'w').write(page_shell(title, desc, body, '../../', canonical=canon))
        if base: urls.append(canon)
    if base:
        with open(os.path.join(out, 'sitemap.xml'), 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            for u in urls:
                f.write(f'<url><loc>{esc(u)}</loc></url>\n')
            f.write('</urlset>\n')
        open(os.path.join(out, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\nSitemap: {base}sitemap.xml\n')
    open(os.path.join(out, '404.html'), 'w').write(page_shell('Sayfa bulunamadı', '', header_html('') + '<main class="wrap"><h1>Bu sayfa bulunamadı</h1><p><a href="index.html">Sözlüğün ana sayfasına dönün</a> ve kelimeyi arama kutusuna yazın.</p></main>', ''))
    open(os.path.join(out, '.nojekyll'), 'w').write('')


def footer_html(built):
    return f'<footer class="foot"><div class="wrap">Son güncelleme: {built}</div></footer>'


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--xlsx')
    ap.add_argument('--sozluk-csv')
    ap.add_argument('--out', default='_site')
    ap.add_argument('--base-url', default='')
    ap.add_argument('--preview', action='store_true')
    ap.add_argument('--min-entries', type=int, default=100)
    a = ap.parse_args()
    if not a.xlsx and not a.sozluk_csv:
        ap.error('--xlsx ya da --sozluk-csv gerekli')
    build(a)
