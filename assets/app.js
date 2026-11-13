(function () {
  'use strict';
  var MODE = window.SITE_MODE || 'site';
  var $ = function (s) { return document.querySelector(s); };
  var esc = function (s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  };
  var reEsc = function (s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); };
  var fmt = function (n) { return n.toLocaleString('tr-TR'); };

  /* ---------- metin normalleştirme (build.py ile aynı kurallar) ---------- */
  var INVIS = /[‎‏‪-‮⁦-⁩﻿­]/g;
  var HARAKAT = /[ً-ٰٟۖ-ۭـ]/g;
  function faBase(s) {
    return String(s || '').replace(INVIS, '').replace(/[يى]/g, 'ی').replace(/ك/g, 'ک')
      .replace(HARAKAT, '').replace(/[أإٱآ]/g, 'ا').replace(/ؤ/g, 'و').replace(/[ۀة]/g, 'ه').replace(/ئ/g, 'ی').replace(/ء/g, '');
  }
  function faKey(s) { return faBase(s).replace(/[‌\s\-–—_\/.,،؛:!?؟«»"'()\[\]]+/g, ''); }
  function faWords(s) {
    return faBase(s).replace(/‌/g, ' ').split(/[\s\-–—\/.,،؛:!?؟«»"'()\[\]0-9۰-۹]+/).map(faKey).filter(Boolean);
  }
  var FOLD = { 'â': 'a', 'î': 'i', 'û': 'u', 'ı': 'i', 'ş': 's', 'ç': 'c', 'ğ': 'g', 'ö': 'o', 'ü': 'u', 'é': 'e', 'ê': 'e', 'ô': 'o', 'á': 'a', 'í': 'i', 'ú': 'u', 'ā': 'a', 'ī': 'i', 'ū': 'u' };
  function trKey(s) {
    s = String(s || '').replace(INVIS, '').replace(/I/g, 'ı').replace(/İ/g, 'i').toLowerCase();
    s = s.replace(/[âîûışçğöüéêôáíúāīū]/g, function (c) { return FOLD[c]; });
    s = s.normalize('NFKD').replace(/[̀-ͯ]/g, '');
    return s.replace(/[^\p{L}\p{N}\s]/gu, ' ').replace(/\s+/g, ' ').trim();
  }
  var AR = /[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]/g, LA = /[A-Za-zÀ-ɏ]/g;
  function isFa(s) { var a = (s.match(AR) || []).length, l = (s.match(LA) || []).length; return a > 0 && a >= l; }

  /* ---------- veri ---------- */
  var S = null, E = [], BYKEY = {}, TURLER = [], GROUPS = [];
  var LETTERS = 'ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی'.split('');
  var GROUP_DEF = [
    { id: 'kelimeler', name: 'Kelimeler', names: ['Kelime'] },
    { id: 'kalip', name: 'Kalıp ifadeler', names: ['Kalıp ifade'] },
    { id: 'deyim', name: 'Deyimler ve atasözleri', names: ['Deyim / ifade', 'Deyim / atasözü', 'İkileme', 'Argo', 'Günlük konuşma'] },
    { id: 'edat', name: 'Edatlar ve bağlaçlar', names: ['Edat / bağlaç'] },
    { id: 'ozel', name: 'Özel isimler', names: ['Özel isim: kişi', 'Özel isim: yer', 'Özel isim: kurum', 'Özel isim: gün / olay'] }
  ];

  function prep(j) {
    S = j; TURLER = j.turler;
    E = j.e.map(function (r, i) {
      var e = { i: i, f: r[0], o: r[1], a: r[2], x: r[3], s: r[4], z: r[5], n: r[6], t: r[7], e: r[8], d: r[9], u: r[10] };
      e.fk = faKey(e.f);
      e.ok = trKey(e.o).replace(/\s/g, '');
      e.ak = e.a.map(trKey);
      e.ap = [];
      e.ak.forEach(function (m) { m.split(/\s*(?:,|;| veya | ya da )\s*/).forEach(function (p) { if (p) e.ap.push(p.trim()); }); });
      e.sk = e.s.map(faKey);
      BYKEY[e.fk] = e;
      return e;
    });
    var used = {};
    GROUPS = GROUP_DEF.map(function (g) {
      var t = g.names.map(function (n) { return TURLER.indexOf(n); }).filter(function (x) { return x >= 0; });
      t.forEach(function (x) { used[x] = 1; });
      return { id: g.id, name: g.name, t: t };
    });
    var rest = TURLER.map(function (_, i) { return i; }).filter(function (i) { return !used[i]; });
    if (rest.length) GROUPS.push({ id: 'diger', name: 'Diğer', t: rest });
    GROUPS.forEach(function (g) {
      g.items = E.filter(function (e) { return e.t.some(function (t) { return g.t.indexOf(t) >= 0; }); });
    });
  }

  /* ---------- arama ---------- */
  function search(q) {
    q = (q || '').trim();
    if (!q) return [];
    var out = [];
    if (isFa(q)) {
      var k = faKey(q);
      if (!k) return [];
      E.forEach(function (e) {
        var sc = 0;
        if (e.fk === k) sc = 100;
        else if (e.fk.indexOf(k) === 0) sc = 80 - Math.min(20, (e.fk.length - k.length) * 0.5);
        else if (e.sk.indexOf(k) >= 0) sc = 70;
        else if (k.length >= 2 && e.fk.indexOf(k) > 0) sc = 45 - Math.min(15, (e.fk.length - k.length) * 0.2);
        if (sc) out.push([sc, e]);
      });
    } else {
      var t = trKey(q), tn = t.replace(/\s/g, '');
      if (!t) return [];
      E.forEach(function (e) {
        var sc = 0;
        if (e.ok && e.ok === tn) sc = 95;
        else if (e.ap.indexOf(t) >= 0) sc = 90;
        else if (e.ok && tn.length >= 3 && e.ok.indexOf(tn) === 0) sc = 72;
        if (sc < 85) {
          for (var j = 0; j < e.ak.length; j++) {
            var m = e.ak[j];
            if (m.indexOf(t + ' ') === 0) { sc = Math.max(sc, 70); break; }
            if ((' ' + m + ' ').indexOf(' ' + t + ' ') >= 0) sc = Math.max(sc, 60);
            else if (t.length >= 3 && (' ' + m).indexOf(' ' + t) >= 0) sc = Math.max(sc, 40);
            else if (t.length >= 4 && m.indexOf(t) >= 0) sc = Math.max(sc, 25);
          }
        }
        if (sc) out.push([sc, e]);
      });
    }
    out.sort(function (a, b) {
      return b[0] - a[0] || (a[1].t[0] || 0) - (b[1].t[0] || 0) || a[1].f.length - b[1].f.length || a[1].i - b[1].i;
    });
    return out.map(function (x) { return x[1]; });
  }

  /* ---------- parçalar ---------- */
  function entryHref(e) { return MODE === 'preview' ? '#k-' + e.i : 'k/' + encodeURIComponent(e.u) + '/'; }
  function trunc(s, n) { return s.length > n ? s.slice(0, n - 1) + '…' : s; }
  function turChip(e) {
    var names = e.t.map(function (t) { return TURLER[t]; }).filter(function (n) { return n !== 'Kelime'; });
    return names.length ? '<span class="chip small">' + esc(names[0]) + '</span>' : '';
  }
  function rowHTML(e) {
    return '<li><a class="row" href="' + entryHref(e) + '"><div class="row-fa" lang="fa" dir="rtl">' + esc(e.f) +
      '</div><div class="row-tr">' + turChip(e) + (e.o ? '<span class="translit">' + esc(e.o) + '</span>' : '') +
      '<span class="mean">' + esc(trunc(e.a.join(' · '), 170)) + '</span></div></a></li>';
  }
  function listWithMore(items, step, emptyMsg) {
    var id = 'L' + Math.random().toString(36).slice(2, 8);
    if (!items.length) return '<div class="empty">' + emptyMsg + '</div>';
    setTimeout(function () {
      var ul = document.getElementById(id), btn = document.getElementById(id + 'm'), shown = 0;
      if (!ul) return;
      function more() {
        ul.insertAdjacentHTML('beforeend', items.slice(shown, shown + step).map(rowHTML).join(''));
        shown += step;
        if (shown >= items.length) btn.hidden = true; else btn.textContent = 'Daha fazla göster (' + fmt(items.length - shown) + ' madde daha)';
      }
      btn.addEventListener('click', more); more();
    });
    return '<ul class="list" id="' + id + '"></ul><button class="more" id="' + id + 'm" type="button">Daha fazla göster</button>';
  }
  function setHome(on) {
    document.body.classList.toggle('is-home', on);
    $('#hero').hidden = !on;
  }
  function view(html) { $('#view').innerHTML = html; }

  /* ---------- görünümler ---------- */
  var query = '';
  function showHome() {
    setHome(true);
    document.title = 'Farsça–Türkçe Sözlük';
    if ($('#q').value !== query) $('#q').value = query;
    if (query) return showResults(query);
    var kel = (GROUPS[0] && GROUPS[0].items) || E;
    var pool = kel.filter(function (e) { return e.o && e.f.length < 18 && e.a.length >= 2; });
    var day = new Date().toISOString().slice(0, 10), h = 0;
    for (var c = 0; c < day.length; c++) h = (h * 31 + day.charCodeAt(c)) >>> 0;
    var w = pool[h % pool.length] || E[0];
    var recent = E.filter(function (e) { return e.d; }).sort(function (a, b) { return a.d < b.d ? 1 : a.d > b.d ? -1 : 0; }).slice(0, 8);
    var tiles = GROUPS.map(function (g) {
      return '<a class="tile" href="#bolum-' + g.id + '"><b>' + fmt(g.items.length) + '</b><span>' + esc(g.name) + '</span></a>';
    }).join('');
    var letters = LETTERS.map(function (l, i) { return '<a href="#harf-' + i + '" lang="fa">' + l + '</a>'; }).join('');
    view(
      '<div class="grid2"><div>' +
      '<h2 class="sec">Bölümler</h2><div class="tiles">' + tiles + '</div>' +
      '<h2 class="sec" style="margin-top:28px">Harf harf</h2><nav class="letters" aria-label="Farsça harfler">' + letters + '</nav>' +
      '</div><div>' +
      '<h2 class="sec">Günün kelimesi</h2><a class="wotd" href="' + entryHref(w) + '" style="color:inherit;text-decoration:none">' +
      '<div class="hw" lang="fa" dir="rtl">' + esc(w.f) + '</div>' + (w.o ? '<p class="translit">' + esc(w.o) + '</p>' : '') +
      '<ol>' + w.a.slice(0, 4).map(function (a) { return '<li>' + esc(a) + '</li>'; }).join('') + '</ol></a>' +
      '<h2 class="sec" style="margin-top:28px">Son eklenenler</h2><ul class="list stack">' + recent.map(rowHTML).join('') + '</ul>' +
      '</div></div>'
    );
  }

  function showResults(q) {
    var res = search(q);
    var hint = isFa(q) ? 'Farsça başlıklarda' : 'Türkçe anlamlarda ve okunuşlarda';
    view('<p class="count">“' + esc(q) + '” için ' + hint + ' ' + fmt(res.length) + ' sonuç</p>' +
      listWithMore(res, 60, 'Bu aramayla eşleşen madde yok. Yazımı kontrol edin ya da kelimenin kökünü deneyin; Farsça kelimeleri Arapça klavyeyle (ي ، ك) yazsanız da bulunur.'));
  }

  function highlightFa(text, f) {
    var first = f.split(/[\s\-–]+/)[0];
    var cands = [f, f.replace(/ (کردن|شدن|دادن|زدن|گرفتن|داشتن|آمدن|نمودن|گشتن|بودن|یافتن|کشیدن|افتادن)$/, ''), first.length >= 3 ? first : ''];
    var t = esc(text);
    for (var i = 0; i < cands.length; i++) {
      var c = esc(cands[i]);
      if (c.length >= 2 && t.indexOf(c) >= 0) return t.split(c).join('<mark>' + c + '</mark>');
    }
    return t;
  }

  function showEntry(i) {
    var e = E[i];
    if (!e) return showHome();
    setHome(false);
    document.title = e.f + ' — Türkçe anlamı | Farsça–Türkçe Sözlük';
    var chips = e.t.map(function (t) { return '<span class="chip">' + esc(TURLER[t]) + '</span>'; }).join('') +
      e.e.map(function (x) { return '<span class="chip ghost" lang="fa">' + esc(x) + '</span>'; }).join('');
    var rel = '';
    [['s', 'Eş anlamlılar'], ['z', 'Zıt anlamlılar']].forEach(function (p) {
      if (!e[p[0]].length) return;
      rel += '<div class="rel"><h3>' + p[1] + '</h3><div class="terms">' + e[p[0]].map(function (v) {
        var tgt = BYKEY[faKey(v)];
        return tgt ? '<a class="term" lang="fa" href="' + entryHref(tgt) + '">' + esc(v) + '</a>'
          : '<a class="term" lang="fa" href="#" data-q="' + esc(v) + '">' + esc(v) + '</a>';
      }).join('') + '</div></div>';
    });
    var exs = e.x.length ? '<section class="block"><h2>Örnek cümleler</h2><ol class="examples">' + e.x.map(function (x) {
      return '<li>' + (x[0] ? '<p class="fa-s" lang="fa" dir="rtl">' + highlightFa(x[0], e.f) + '</p>' : '') +
        (x[1] ? '<p class="tr-s">' + esc(x[1]) + '</p>' : '') + '</li>';
    }).join('') + '</ol></section>' : '';
    view('<a class="back" href="#" id="back">← Geri</a><article class="entry">' +
      '<div class="entry-head"><h1 class="hw" lang="fa" dir="rtl">' + esc(e.f) + '</h1>' +
      (e.o ? '<p class="translit">' + esc(e.o) + '</p>' : '') + '<div class="chips">' + chips + '</div></div>' +
      '<section class="block"><h2>Anlamları</h2><ol class="means">' + e.a.map(function (a) { return '<li>' + esc(a) + '</li>'; }).join('') + '</ol>' +
      (e.n ? '<p class="note">' + esc(e.n) + '</p>' : '') + '</section>' + rel + exs +
      '</article>');
    $('#back').addEventListener('click', function (ev) { ev.preventDefault(); if (history.length > 1) history.back(); else location.hash = ''; });
  }

  function showSection(id, sub) {
    var g = GROUPS.filter(function (x) { return x.id === id; })[0];
    if (!g) return showHome();
    setHome(false);
    document.title = g.name + ' | Farsça–Türkçe Sözlük';
    var subs = g.t.length > 1 ? '<div class="filters">' + ['<button class="chip" type="button" data-sub="" aria-pressed="true">Tümü</button>']
      .concat(g.t.map(function (t) {
        var n = g.items.filter(function (e) { return e.t.indexOf(t) >= 0; }).length;
        return '<button class="chip" type="button" data-sub="' + t + '" aria-pressed="false">' + esc(TURLER[t].replace('Özel isim: ', '')) + ' · ' + fmt(n) + '</button>';
      })).join('') + '</div>' : '';
    view('<div class="pagehead"><h1>' + esc(g.name) + '</h1><p class="muted">' + fmt(g.items.length) + ' madde, Farsça alfabe sırasıyla</p></div>' +
      '<label class="sr" for="sf">Bu bölümde ara</label><input class="inline-search" id="sf" type="search" placeholder="Bu bölümde ara (Farsça ya da Türkçe)">' +
      subs + '<div id="slist"></div>');
    var cur = '';
    function draw() {
      var f = $('#sf').value.trim(), items = g.items;
      if (cur !== '') items = items.filter(function (e) { return e.t.indexOf(+cur) >= 0; });
      if (f) {
        var ids = {}; search(f).forEach(function (e) { ids[e.i] = 1; });
        items = items.filter(function (e) { return ids[e.i]; });
      }
      $('#slist').innerHTML = (f ? '<p class="count">' + fmt(items.length) + ' sonuç</p>' : '') + listWithMore(items, 150, 'Bu bölümde eşleşen madde yok.');
    }
    var tmr; $('#sf').addEventListener('input', function () { clearTimeout(tmr); tmr = setTimeout(draw, 150); });
    Array.prototype.forEach.call(document.querySelectorAll('[data-sub]'), function (b) {
      b.addEventListener('click', function () {
        cur = b.getAttribute('data-sub');
        Array.prototype.forEach.call(document.querySelectorAll('[data-sub]'), function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
        draw();
      });
    });
    draw();
  }

  function showLetter(n) {
    var l = LETTERS[n];
    if (!l) return showHome();
    setHome(false);
    var items = E.filter(function (e) { return e.fk.charAt(0) === l; });
    document.title = l + ' harfi | Farsça–Türkçe Sözlük';
    var letters = LETTERS.map(function (x, i) { return '<a href="#harf-' + i + '" lang="fa"' + (i === n ? ' aria-current="page"' : '') + '>' + x + '</a>'; }).join('');
    view('<div class="pagehead"><h1><span class="fa-t" lang="fa">' + l + '</span> harfiyle başlayanlar</h1><p class="muted">' + fmt(items.length) + ' madde</p></div>' +
      '<nav class="letters" aria-label="Farsça harfler" style="margin:6px 0 18px">' + letters + '</nav>' + listWithMore(items, 150, 'Bu harfle başlayan madde yok.'));
  }

  /* ---------- yönlendirme ---------- */
  function route() {
    var h = location.hash.slice(1);
    if (/^k-\d+$/.test(h)) return showEntry(+h.slice(2));
    if (h.indexOf('bolum-') === 0) return showSection(h.slice(6));
    if (/^harf-\d+$/.test(h)) return showLetter(+h.slice(5));
    showHome();
  }
  function setQuery(q, goHome) {
    query = q;
    if (MODE === 'site') {
      var u = new URL(location.href);
      if (q) u.searchParams.set('q', q); else u.searchParams.delete('q');
      if (goHome) u.hash = '';
      history.replaceState(null, '', u.pathname + u.search + u.hash);
    }
    if (goHome && location.hash) { location.hash = ''; return; }
    showHome();
  }

  document.addEventListener('click', function (ev) {
    var a = ev.target.closest('[data-q],#brand');
    if (!a) return;
    if (a.id === 'brand') { ev.preventDefault(); $('#q').value = ''; setQuery('', true); window.scrollTo(0, 0); return; }
    ev.preventDefault(); $('#q').value = a.getAttribute('data-q'); setQuery(a.getAttribute('data-q'), true); window.scrollTo(0, 0);
  });

  function init(j) {
    prep(j);
    var nTotal = E.length;
    $('#stats').textContent = fmt(nTotal) + ' madde: kelimeler, okunuşlar, örnek cümleler, kalıp ifadeler, deyimler ve özel isimler.';
    $('#foot').textContent = 'Son güncelleme: ' + S.built + (MODE === 'preview' ? ' · Önizleme' : '') + ' · Veriler Google E-Tablolar\'dan alınır.';
    var tries = ['تقدیر کردن', 'afiyet olsun', 'nüfuz', 'دست', 'Cumhurbaşkanı'].filter(function (q) { return search(q).length; }).slice(0, 4);
    $('#tries').insertAdjacentHTML('beforeend', tries.map(function (q) {
      return '<button class="chip ghost" type="button" data-q="' + esc(q) + '"' + (isFa(q) ? ' lang="fa"' : '') + '>' + esc(q) + '</button>';
    }).join(''));
    var tmr;
    $('#q').addEventListener('input', function () {
      clearTimeout(tmr); var v = this.value;
      tmr = setTimeout(function () { setQuery(v.trim(), false); }, 140);
    });
    $('#bigform').addEventListener('submit', function (ev) { ev.preventDefault(); setQuery($('#q').value.trim(), false); });
    $('#topform').addEventListener('submit', function (ev) {
      ev.preventDefault(); var v = $('#tq').value.trim(); $('#tq').value = ''; $('#q').value = v; setQuery(v, true); window.scrollTo(0, 0);
    });
    if (MODE === 'site') { var p = new URLSearchParams(location.search).get('q'); if (p) { query = p; } }
    window.addEventListener('hashchange', function () { route(); window.scrollTo(0, 0); });
    route();
  }

  fetch('data/sozluk.json').then(function (r) {
    if (!r.ok) throw new Error(r.status);
    return r.json();
  }).then(init).catch(function () {
    view('<div class="empty">Sözlük verisi yüklenemedi. Sayfayı yenileyin; sorun sürerse internet bağlantınızı kontrol edin.</div>');
  });
})();
