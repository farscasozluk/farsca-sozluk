# Evernote → Google E-Tablolar aktarımı (tek seferlik)

    python3 extract.py yedek.zip ham/            # zip içindeki .enex dosyalarını doğru adlarla çıkarır
    python3 parse.py ham/ notlar.json            # notları sözlük maddelerine ve haber çevirilerine ayırır
    python3 build_xlsx.py notlar.json Farsca_Sozluk.xlsx Haric_tutulan_notlar.xlsx

Haber defterleri (flaş, titr, alt yazı, infografik) tabloya alınmaz. Kalıp ifadeler içindeki tam haber cümleleri `newslike.py` kurallarıyla "Yayınlanmayanlar" sekmesine ayrılır.

Hangi defterin hangi bölüme gittiği `parse_lib.py` içindeki `DICT_BOOKS`, `NEWS_BOOKS` ve `SKIP_BOOKS` listelerinde.
