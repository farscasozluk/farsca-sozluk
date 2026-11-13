import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fa_sort import fa_sort_key
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

data = json.load(open(sys.argv[1])); out = sys.argv[2]; out_excl = sys.argv[3]
F = 'Arial'
HEAD = Font(name=F, bold=True, color='FFFFFF', size=10)
HFILL = PatternFill('solid', start_color='1F4E5F')
BODY = Font(name=F, size=10)
FA_FONT = Font(name=F, size=12)
FLAG = Font(name=F, size=9, color='B45309')
RTL = Alignment(horizontal='right', vertical='top', wrap_text=True, readingOrder=2)
LTR = Alignment(horizontal='left', vertical='top', wrap_text=True)
TURLER = ['Kelime', 'Kalıp ifade', 'Deyim / ifade', 'Deyim / atasözü', 'Edat / bağlaç', 'İkileme', 'Argo', 'Günlük konuşma',
          'Özel isim: kişi', 'Özel isim: yer', 'Özel isim: kurum', 'Özel isim: gün / olay']
HABER_TURLER = ['Flaş', 'Titr', 'Foto / video alt yazısı', 'Alt yazı', 'İnfografik', 'Haber geçmişi']

def header(ws, cols):
    for j, (name, width, _) in enumerate(cols, 1):
        c = ws.cell(row=1, column=j, value=name); c.font = HEAD; c.fill = HFILL
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        ws.column_dimensions[get_column_letter(j)].width = width
    ws.freeze_panes = 'B2'; ws.row_dimensions[1].height = 30

wb = Workbook()
def entry_sheet(ws, entries):
    header(ws, cols)
    entries = sorted(entries, key=lambda e: (fa_sort_key(e['farsca']) if e['farsca'] else [9999]))
    for i, e in enumerate(entries, 2):
        ex_lines = []
        for o in e['ornekler']:
            if o['fa']: ex_lines.append(o['fa'])
            if o['tr']: ex_lines.append(o['tr'])
        vals = [e['farsca'], e['okunus'], '\n'.join(e['anlamlar']), '\n'.join(ex_lines),
                '\n'.join(e['esanlamli']), '\n'.join(e['zitanlamli']), e['not'], e['tur'], e['etiket'],
                e['kontrol'], e['kaynak'], e['tarih']]
        for j, v in enumerate(vals, 1):
            c = ws.cell(row=i, column=j, value=v if v != '' else None)
            kind = cols[j-1][2]
            if kind == 'fa': c.font = FA_FONT; c.alignment = RTL
            elif kind == 'mix': c.font = BODY; c.alignment = RTL
            elif kind == 'flag': c.font = FLAG; c.alignment = LTR
            else: c.font = BODY; c.alignment = LTR
    last = len(entries) + 1
    ws.auto_filter.ref = f'A1:{get_column_letter(len(cols))}{last}'
    dv = DataValidation(type='list', formula1='"' + ','.join(TURLER) + '"', allow_blank=True, showDropDown=False)
    ws.add_data_validation(dv); dv.add(f'H2:H{last + 5000}')
    return len(entries)

cols = [('Farsça', 28, 'fa'), ('Okunuş', 22, 'l'), ('Türkçe anlamlar', 42, 'l'), ('Örnek cümleler', 60, 'mix'),
        ('Eş anlamlılar', 20, 'fa'), ('Zıt anlamlılar', 16, 'fa'), ('Not', 24, 'l'), ('Tür', 16, 'l'), ('Etiket', 10, 'l'),
        ('Kontrol', 30, 'flag'), ('Kaynak defter', 18, 'l'), ('Eklenme tarihi', 13, 'l')]
wb = Workbook()
ws = wb.active; ws.title = 'Sözlük'
n_pub = entry_sheet(ws, [e for e in data['entries'] if not e.get('gizli')])
n_priv = entry_sheet(wb.create_sheet('Yayınlanmayanlar'), [e for e in data['entries'] if e.get('gizli')])

ws3 = wb.create_sheet('Nasıl kullanılır', 0)
ws3.column_dimensions['A'].width = 26; ws3.column_dimensions['B'].width = 95
rows = [
    ('FARSÇA–TÜRKÇE SÖZLÜK · VERİ TABLOSU', None),
    ('Bu tablo sözlük sitesinin tek kaynağıdır. Burada yaptığınız her değişiklik site bir sonraki güncellendiğinde yayına girer.', None),
    (None, None),
    ('YENİ KELİME EKLEMEK', None),
    ('1. Nereye?', '"Sözlük" sekmesinde en alttaki boş satıra yazın. Sıralama önemli değil; site kelimeleri kendisi alfabetik dizer.'),
    ('2. Zorunlu sütunlar', 'Farsça ve Türkçe anlamlar. Bu ikisi dolu olmayan satırlar sitede görünmez.'),
    ('3. Birden fazla anlam', 'Her anlamı ayrı satıra yazın (bilgisayarda Ctrl+Enter, Mac\'te ⌘+Enter; telefonda klavyedeki satır başı tuşu). Bir satırda virgülle ayrılmış anlamlar tek madde sayılır.'),
    ('4. Örnek cümleler', 'Evernote\'taki gibi: Farsça cümleyi bir satıra, varsa Türkçe çevirisini hemen alt satıra yazın. Site Farsça ve Türkçe satırları kendisi ayırt eder.'),
    ('5. Tür', 'Açılır listeden seçin (Kelime, Kalıp ifade, Deyim / atasözü, Özel isim: kişi …). Boş bırakırsanız "Kelime" sayılır.'),
    (None, None),
    ('ÖRNEK SATIR', None),
    ('Farsça', 'تقدیر کردن'),
    ('Okunuş', 'takdir kerden'),
    ('Türkçe anlamlar', 'takdir etmek\ndeğer biçmek'),
    ('Örnek cümleler', 'رئیس جمهور از تلاش بازیکنان تیم ملی تقدیر کرد\nCumhurbaşkanı milli takım oyuncularının çabasını takdir etti'),
    ('Tür', 'Kelime'),
    (None, None),
    ('İKİ SEKME', None),
    ('Sözlük', 'Sitede görünen maddeler. Yalnızca bu sekme "Web\'de yayınla" ile yayınlanır.'),
    ('Yayınlanmayanlar', f'Sitede görünmeyen ve dışarıdan erişilemeyen maddeler ({n_priv:,} satır): haber cümleleri, iş yeri sistemi (Has) terimleri, Türkçesi olmayan dilbilgisi listeleri. Neden ayrıldıkları "Kontrol" sütununda yazıyor. Bir maddeyi siteye çıkarmak için satırı kesip "Sözlük" sekmesine yapıştırın; siteden kaldırmak için tersini yapın.'.replace(',', '.')),
    ('Gizli kalması gerekenler', 'Kişisel ya da gizli bir şeyi "Sözlük" sekmesine yazmayın: yayınlanan sekmenin tamamı (Kontrol sütunu dahil) bağlantıyı bilen herkes tarafından okunabilir.'),
    (None, None),
    ('DİĞER SÜTUNLAR', None),
    ('Kontrol', 'Evernote\'tan aktarırken otomatik eklenen uyarılar (ör. "Türkçe anlam yok", "aynı kelime başka notta da var"). Düzelttikten sonra hücreyi silebilirsiniz. Sitede görünmez.'),
    ('Kaynak defter / tarih', 'Notun geldiği Evernote defteri ve oluşturulma tarihi. Yeni satırlarda boş bırakabilirsiniz.'),
    (None, None),
    ('LÜTFEN', 'Sekme adlarını ve sütun başlıklarını değiştirmeyin; site verileri bu başlıklarla okur. Yeni sütun eklemek isterseniz en sağa ekleyin.'),
]
for i, (a, b) in enumerate(rows, 1):
    ca = ws3.cell(row=i, column=1, value=a); cb = ws3.cell(row=i, column=2, value=b)
    ca.font = Font(name=F, size=10, bold=True); cb.font = Font(name=F, size=10)
    ca.alignment = Alignment(vertical='top', wrap_text=True); cb.alignment = Alignment(vertical='top', wrap_text=True)
    if a and b is None and a.isupper():
        ca.font = Font(name=F, size=11, bold=True, color='1F4E5F')
    if b and any('؀' <= ch <= 'ۿ' for ch in b):
        cb.alignment = Alignment(horizontal='right', vertical='top', wrap_text=True, readingOrder=2); cb.font = Font(name=F, size=12)
ws3['A1'].font = Font(name=F, size=14, bold=True, color='1F4E5F')
ws3.merge_cells('A2:B2'); ws3['A2'].font = Font(name=F, size=10, italic=True)
ws3.row_dimensions[2].height = 28
wb.active = 1
wb.save(out)

# hariç tutulanlar (özel dosya)
wb2 = Workbook(); w = wb2.active; w.title = 'Hariç tutulan notlar'
header(w, [('Kaynak defter', 34, ''), ('Not başlığı', 50, ''), ('Neden', 40, ''), ('İçerik (ilk 500 karakter)', 80, '')])
for i, x in enumerate(data['excluded'], 2):
    hassas = 'hassas' in x['neden'] or 'kişisel' in x['neden']
    vals = [x['kaynak'], x['baslik'], x['neden'], '' if hassas else x.get('icerik', '')]
    for j, v in enumerate(vals, 1):
        c = w.cell(row=i, column=j, value=v or None); c.font = BODY; c.alignment = LTR
wb2.save(out_excl)
print('Sözlük:', n_pub, '| Yayınlanmayanlar:', n_priv, '| hariç:', len(data['excluded']))
