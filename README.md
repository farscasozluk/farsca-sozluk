# Farsça–Türkçe Sözlük

Google E-Tablolar'daki sözlük tablosundan her gün otomatik olarak üretilen, herkese açık sözlük sitesi.

- **Kaynak:** Google E-Tablolar'daki `Sözlük` sekmesi (yalnızca bu sekme yayınlanır)
- **Site:** GitHub Pages (ücretsiz), her gün 06:17'de ve bu depoya her değişiklik gönderildiğinde yeniden üretilir
- **Her kelimenin kendi sayfası var** (`/k/<kelime>/`). Google bu sayfaları tek tek dizine ekler.

## Bir kerelik kurulum

### 1. Tabloyu Google E-Tablolar'a taşıyın
1. `Farsca_Sozluk.xlsx` dosyasını Google Drive'a yükleyin.
2. Dosyayı açın ve **Dosya → Google E-Tablolar olarak kaydet** deyin. Bundan sonra yalnızca bu Google E-Tablolar kopyasında çalışın.

### 2. Yalnızca "Sözlük" sekmesini web'de yayınlayın
1. **Dosya → Paylaş → Web'de yayınla**.
2. Soldaki listeden **yalnızca Sözlük** sekmesini, sağdakinden **Virgülle ayrılmış değerler (.csv)** seçin → **Yayınla** → bağlantıyı kopyalayın.
3. "Değişiklik yapıldığında otomatik olarak yeniden yayınla" seçeneği açık kalsın.
4. Dosyanın paylaşım ayarını "Kısıtlanmış" bırakın. Böylece **Yayınlanmayanlar** sekmesi dışarıdan görünmez.

> Not: Yayınlanan *Sözlük* sekmesinin tamamı (Kontrol sütunu dahil) bağlantıyı bilen herkes tarafından okunabilir. Kişisel ya da gizli bir şeyi bu sekmeye yazmayın; yayınlamak istemediğiniz maddeleri **Yayınlanmayanlar** sekmesine taşıyın.

### 3. GitHub deposunu açın
1. GitHub'da yeni ve **herkese açık (Public)** bir depo açın, ör. `farsca-sozluk`.
2. Bu klasördeki dosyaların hepsini depoya yükleyin. `.github` klasörü de yüklenmeli.
3. **Settings → Pages → Build and deployment → Source: GitHub Actions** seçin.
4. **Settings → Secrets and variables → Actions → Variables → New repository variable** ile iki değişken ekleyin:

| Ad | Değer |
|---|---|
| `SOZLUK_CSV_URL` | 2. adımda kopyaladığınız *Sözlük* bağlantısı |
| `SITE_URL` | `https://<github-kullanıcı-adınız>.github.io/farsca-sozluk/` |

5. **Actions → Sözlüğü güncelle ve yayınla → Run workflow**. Birkaç dakika sonra site `SITE_URL` adresinde açılır.

### 4. (İsteğe bağlı) Kendi alan adınız
Bir alan adı alırsanız (ör. `farscasozluk.com`), **Settings → Pages → Custom domain** bölümüne yazın ve `SITE_URL` değişkenini yeni adresle güncelleyin.

## Günlük kullanım
- Yeni kelimeyi Google E-Tablolar'da `Sözlük` sekmesinin en altına ekleyin. Kurallar tablonun **Nasıl kullanılır** sekmesinde.
- Bir maddeyi siteden kaldırmak için satırını **Yayınlanmayanlar** sekmesine taşıyın; geri almak için tersini yapın.
- Site her sabah kendiliğinden güncellenir. Hemen görmek isterseniz **Actions → Run workflow** deyin.
- Güvenlik önlemi: Tablo okunamazsa ya da 100'den az madde içerirse güncelleme durur ve mevcut site olduğu gibi kalır.

## Dosyalar
- `build.py`: tabloyu okur, siteyi `_site/` klasörüne üretir
- `assets/`: sayfa tasarımı (`style.css`), arama ve gezinme (`app.js`), ana sayfa iskeleti (`app.html`)
- `textnorm.py`: Farsça ve Türkçe arama için harf birleştirme (ي/ی, ك/ک, harekeler, yarım boşluk, â/î/û)
- `evernote-aktarim/`: Evernote yedeklerini tabloya çeviren tek seferlik araç

Bilgisayarınızda denemek için: `python3 build.py --xlsx Farsca_Sozluk.xlsx --out _site`, ardından `_site` klasöründe `python3 -m http.server` çalıştırıp tarayıcıda `http://localhost:8000` adresini açın.
