/* ── Слой правок и комментариев ────────────────────────────
   Подключается к любой странице сайта одной строкой:
       <script src="review.js" defer></script>

   Три режима:
     Просмотр       — страница как есть
     Комментарии    — клик по блоку оставляет заметку
     Правка текста  — текст правится прямо на странице,
                      сохраняется «было → стало»

   Всё лежит в localStorage браузера. Общего сервера нет:
   каждый комментирует у себя и жмёт «Собрать всё», чтобы
   выгрузить свои правки одним файлом.
──────────────────────────────────────────────────────────── */
(function () {
  'use strict';

  var STORE = 'pv_review_v1';
  var TYPES = [
    ['text',   'Текст'],
    ['photo',  'Фото и видео'],
    ['struct', 'Структура'],
    ['other',  'Другое']
  ];
  var TYPE_NAME = {};
  TYPES.forEach(function (t) { TYPE_NAME[t[0]] = t[1]; });

  var db = load();
  var mode = 'view';
  var blocks = [];

  /* ───────────── хранилище ───────────── */
  function load() {
    try {
      var raw = JSON.parse(localStorage.getItem(STORE) || 'null');
      if (raw && raw.comments) return raw;
    } catch (e) {}
    return { author: '', comments: [], edits: [] };
  }
  function save() {
    try { localStorage.setItem(STORE, JSON.stringify(db)); } catch (e) {}
    paint();
  }
  function uid() { return Math.random().toString(36).slice(2, 9); }

  /* ───────────── разметка блоков ───────────── */
  function nameOf(el, i) {
    var k = el.querySelector('.kicker, .lbl, .hd .t, .rh .t');
    var h = el.querySelector('h1, h2, .dm, .mark');
    var parts = [];
    if (k) parts.push(txt(k));
    if (h) parts.push(txt(h));
    var n = parts.join(' · ').replace(/\s+/g, ' ').trim();
    if (!n && el.classList.contains('tick')) n = 'Бегущая строка';
    if (!n && el.classList.contains('strip')) n = 'Полоса фотографий';
    if (!n && el.tagName === 'NAV') n = 'Верхнее меню';
    if (!n && el.tagName === 'FOOTER') n = 'Подвал';
    if (!n && el.tagName === 'HEADER') n = 'Первый экран';
    if (!n) n = 'Блок ' + (i + 1);
    return n.length > 64 ? n.slice(0, 62) + '…' : n;
  }
  function txt(el) { return (el.textContent || '').replace(/\s+/g, ' ').trim(); }

  function collect() {
    var sel = 'body > header, body > section, body > nav, body > footer, body > .tick, body > .strip';
    blocks = [].slice.call(document.querySelectorAll(sel));
    blocks.forEach(function (el, i) {
      el.dataset.rvId = el.id || ('b' + (i + 1));
      el.dataset.rvName = nameOf(el, i);
      el.classList.add('rv-block');
    });
  }

  /* ───────────── правка текста ───────────── */
  var INLINE = { SPAN: 1, EM: 1, B: 1, I: 1, STRONG: 1, CODE: 1, S: 1, SMALL: 1, BR: 1, A: 1 };
  function isLeaf(el) {
    if (!txt(el)) return false;
    for (var i = 0; i < el.children.length; i++) {
      if (!INLINE[el.children[i].tagName]) return false;
    }
    return true;
  }
  function pathOf(block, el) {
    var p = [], cur = el;
    while (cur && cur !== block) {
      var t = cur.tagName.toLowerCase(), n = 1, sib = cur;
      while ((sib = sib.previousElementSibling)) if (sib.tagName === cur.tagName) n++;
      p.unshift(t + ':nth-of-type(' + n + ')');
      cur = cur.parentElement;
    }
    return p.join('>');
  }
  function editables() {
    var out = [];
    blocks.forEach(function (b) {
      if (b.tagName === 'NAV' || b.classList.contains('tick')) return;
      [].slice.call(b.querySelectorAll('h1,h2,h3,p,li,summary,div,span,a'))
        .forEach(function (el) {
          if (el.closest('#rv-bar, #rv-panel, #rv-list, #pvgate, .tick')) return;
          if (isLeaf(el) && txt(el).length > 1) out.push({ b: b, el: el });
        });
    });
    return out;
  }
  function armEdit(on) {
    editables().forEach(function (o) {
      var el = o.el;
      if (on) {
        if (el.dataset.rvOrig === undefined) el.dataset.rvOrig = el.innerHTML;
        el.contentEditable = 'true';
        el.classList.add('rv-edit');
        if (!el.dataset.rvBound) {
          el.dataset.rvBound = '1';
          el.addEventListener('blur', function () { commitEdit(o.b, el); });
        }
      } else {
        el.contentEditable = 'false';
        el.classList.remove('rv-edit');
      }
    });
  }
  function clean(html) {
    var d = document.createElement('div');
    d.innerHTML = html;
    return (d.textContent || '').replace(/\s+/g, ' ').trim();
  }
  function commitEdit(block, el) {
    var before = clean(el.dataset.rvOrig || ''), after = clean(el.innerHTML);
    var path = pathOf(block, el);
    var idx = db.edits.findIndex(function (e) { return e.block === block.dataset.rvId && e.path === path; });
    if (before === after) {
      if (idx > -1) db.edits.splice(idx, 1);
    } else {
      var rec = {
        id: idx > -1 ? db.edits[idx].id : uid(),
        block: block.dataset.rvId, blockName: block.dataset.rvName,
        path: path, before: before, after: after,
        author: db.author, ts: Date.now()
      };
      if (idx > -1) db.edits[idx] = rec; else db.edits.push(rec);
    }
    save();
  }

  /* ───────────── интерфейс ───────────── */
  function css() {
    var s = document.createElement('style');
    s.textContent = [
      '#rv-bar,#rv-panel,#rv-list,.rv-pin,.rv-badge{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;box-sizing:border-box}',
      '#rv-bar{position:fixed;left:50%;transform:translateX(-50%);bottom:18px;z-index:9000;',
        'background:rgba(23,19,19,.97);backdrop-filter:blur(12px);border-radius:999px;',
        'display:flex;align-items:center;gap:6px;padding:6px;box-shadow:0 10px 34px rgba(0,0,0,.4)}',
      '#rv-bar button{border:0;background:transparent;color:rgba(242,234,217,.66);font-size:12.5px;',
        'font-weight:600;padding:9px 15px;border-radius:999px;cursor:pointer;white-space:nowrap;transition:.18s}',
      '#rv-bar button:hover{color:#fff;background:rgba(242,234,217,.1)}',
      '#rv-bar button.on{background:#F5C63A;color:#1A1717}',
      '#rv-bar .sep{width:1px;height:20px;background:rgba(242,234,217,.2);margin:0 3px}',
      '#rv-bar .cnt{color:#F5C63A;font-size:12px;font-weight:700;padding:0 8px;white-space:nowrap}',
      '#rv-bar .go{background:#6B2138;color:#fff}',
      '#rv-bar .go:hover{background:#8C2C49;color:#fff}',

      'body.rv-comment .rv-block{cursor:pointer}',
      'body.rv-comment .rv-block:hover{outline:2px dashed #F5C63A;outline-offset:-2px}',
      '.rv-edit:hover{outline:1px dashed rgba(107,33,56,.45);outline-offset:3px}',
      '.rv-edit:focus{outline:2px solid #F5C63A;outline-offset:3px;background:rgba(245,198,58,.12)}',
      '.rv-touched{box-shadow:inset 3px 0 0 #F5C63A}',

      '.rv-badge{position:absolute;top:10px;right:10px;z-index:60;background:#F5C63A;color:#1A1717;',
        'min-width:26px;height:26px;border-radius:999px;display:flex;align-items:center;justify-content:center;',
        'font-size:12.5px;font-weight:700;cursor:pointer;box-shadow:0 3px 10px rgba(0,0,0,.28);padding:0 8px}',
      '.rv-block{position:relative}',

      '#rv-panel,#rv-list{position:fixed;top:0;right:0;height:100%;width:380px;max-width:92vw;z-index:9500;',
        'background:#FBF7F0;box-shadow:-8px 0 40px rgba(0,0,0,.24);display:flex;flex-direction:column;',
        'transform:translateX(105%);transition:transform .28s cubic-bezier(.22,.61,.36,1)}',
      '#rv-panel.on,#rv-list.on{transform:none}',
      '#rv-panel .h,#rv-list .h{background:#22314A;color:#EFEAE0;padding:16px 18px;flex:none}',
      '#rv-panel .h .t,#rv-list .h .t{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:#F5C63A;margin-bottom:5px}',
      '#rv-panel .h .n,#rv-list .h .n{font-size:16px;font-weight:600;line-height:1.3;color:#fff}',
      '#rv-panel .h .x,#rv-list .h .x{position:absolute;top:12px;right:14px;background:none;border:0;',
        'color:rgba(239,234,224,.7);font-size:22px;cursor:pointer;line-height:1;padding:4px}',
      '#rv-panel .bd,#rv-list .bd{flex:1;overflow-y:auto;padding:18px}',
      '#rv-panel label{display:block;font-size:11px;letter-spacing:.13em;text-transform:uppercase;',
        'color:#837A72;font-weight:600;margin:0 0 8px}',
      '#rv-panel .tp{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:18px}',
      '#rv-panel .tp button{border:1px solid rgba(26,23,23,.16);background:#fff;color:#4C4643;',
        'font-size:12.5px;padding:7px 13px;border-radius:999px;cursor:pointer;transition:.15s}',
      '#rv-panel .tp button.on{background:#22314A;color:#fff;border-color:#22314A}',
      '#rv-panel textarea,#rv-panel input{width:100%;border:1px solid rgba(26,23,23,.16);border-radius:4px;',
        'padding:11px 13px;font-size:15px;font-family:inherit;background:#fff;outline:none;resize:vertical}',
      '#rv-panel textarea:focus,#rv-panel input:focus{border-color:#6B2138}',
      '#rv-panel textarea{min-height:132px;margin-bottom:16px}',
      '#rv-panel input{margin-bottom:18px}',
      '#rv-panel .ft{padding:14px 18px;border-top:1px solid rgba(26,23,23,.1);flex:none;display:flex;gap:8px}',
      '#rv-panel .ft button{flex:1;border:0;border-radius:4px;padding:13px;font-size:13.5px;font-weight:600;cursor:pointer}',
      '#rv-panel .ft .add{background:#6B2138;color:#fff}',
      '#rv-panel .ft .add:hover{background:#8C2C49}',

      '.rv-item{background:#fff;border-left:3px solid #F5C63A;padding:13px 15px;margin-bottom:9px;border-radius:3px;',
        'box-shadow:0 1px 6px rgba(26,23,23,.07)}',
      '.rv-item .m{display:flex;justify-content:space-between;gap:10px;font-size:10.5px;letter-spacing:.1em;',
        'text-transform:uppercase;color:#837A72;font-weight:600;margin-bottom:6px}',
      '.rv-item p{font-size:14.5px;line-height:1.5;color:#1A1717;margin:0}',
      '.rv-item .del{background:none;border:0;color:#B33A3A;font-size:11.5px;cursor:pointer;padding:6px 0 0;font-weight:600}',
      '.rv-item.ed{border-left-color:#6B2138}',
      '.rv-item .was{font-size:13px;color:#B33A3A;text-decoration:line-through;margin-bottom:4px;line-height:1.45}',
      '.rv-item .now{font-size:14px;color:#2E7D5B;font-weight:500;line-height:1.45}',
      '#rv-list .g{font-size:11px;letter-spacing:.13em;text-transform:uppercase;color:#6B2138;',
        'font-weight:700;margin:20px 0 9px}',
      '#rv-list .g:first-child{margin-top:0}',
      '#rv-list .empty{color:#837A72;font-size:14.5px;line-height:1.55;text-align:center;padding:40px 10px}',
      '#rv-list .ft{padding:14px 18px;border-top:1px solid rgba(26,23,23,.1);flex:none;display:flex;gap:8px}',
      '#rv-list .ft button{flex:1;border:0;border-radius:4px;padding:13px;font-size:13px;font-weight:600;cursor:pointer}',
      '#rv-list .ft .cp{background:#6B2138;color:#fff}',
      '#rv-list .ft .dl{background:#22314A;color:#fff}',
      '#rv-list .ft .rs{background:rgba(26,23,23,.08);color:#B33A3A;flex:0 0 auto;padding:13px 15px}',
      '#rv-toast{position:fixed;left:50%;transform:translateX(-50%);bottom:80px;z-index:9999;',
        'background:#2E7D5B;color:#fff;padding:12px 22px;border-radius:999px;font-size:13.5px;font-weight:600;',
        'opacity:0;transition:opacity .25s;pointer-events:none}',
      '#rv-toast.on{opacity:1}',
      '@media(max-width:640px){#rv-bar{bottom:10px;padding:5px;gap:3px}',
        '#rv-bar button{padding:9px 11px;font-size:12px}#rv-bar .cnt{padding:0 5px}}'
    ].join('');
    document.head.appendChild(s);
  }

  var bar, panel, list, toast, cur = null, curType = 'text';

  function ui() {
    bar = document.createElement('div');
    bar.id = 'rv-bar';
    bar.innerHTML =
      '<button data-m="view">Просмотр</button>' +
      '<button data-m="comment">Комментарии</button>' +
      '<button data-m="edit">Правка текста</button>' +
      '<span class="sep"></span><span class="cnt" id="rv-cnt">0</span>' +
      '<button class="go" id="rv-open">Собрать всё</button>';
    document.body.appendChild(bar);

    panel = document.createElement('div');
    panel.id = 'rv-panel';
    panel.innerHTML =
      '<div class="h"><div class="t">Комментарий к блоку</div><div class="n" id="rv-bn"></div>' +
        '<button class="x" data-close>&times;</button></div>' +
      '<div class="bd">' +
        '<label>О чём правка</label><div class="tp" id="rv-tp"></div>' +
        '<label>Что поменять</label>' +
        '<textarea id="rv-tx" placeholder="Например: заголовок слишком длинный, оставить первую строку"></textarea>' +
        '<label>Кто пишет</label><input id="rv-au" placeholder="Имя">' +
        '<div id="rv-ex"></div>' +
      '</div>' +
      '<div class="ft"><button class="add" id="rv-add">Добавить</button></div>';
    document.body.appendChild(panel);

    list = document.createElement('div');
    list.id = 'rv-list';
    list.innerHTML =
      '<div class="h"><div class="t">Все правки</div><div class="n" id="rv-ln">0 записей</div>' +
        '<button class="x" data-close>&times;</button></div>' +
      '<div class="bd" id="rv-lb"></div>' +
      '<div class="ft"><button class="cp" id="rv-cp">Скопировать</button>' +
        '<button class="dl" id="rv-dl">Скачать</button>' +
        '<button class="rs" id="rv-rs">Очистить</button></div>';
    document.body.appendChild(list);

    toast = document.createElement('div');
    toast.id = 'rv-toast';
    document.body.appendChild(toast);

    var tp = document.getElementById('rv-tp');
    TYPES.forEach(function (t) {
      var b = document.createElement('button');
      b.textContent = t[1];
      b.dataset.t = t[0];
      b.addEventListener('click', function () {
        curType = t[0];
        [].forEach.call(tp.children, function (c) { c.classList.toggle('on', c.dataset.t === curType); });
      });
      tp.appendChild(b);
    });

    bar.addEventListener('click', function (e) {
      var b = e.target.closest('button[data-m]');
      if (b) setMode(b.dataset.m);
    });
    document.getElementById('rv-open').addEventListener('click', openList);
    document.addEventListener('click', function (e) {
      if (e.target.closest('[data-close]')) { panel.classList.remove('on'); list.classList.remove('on'); }
    });
    document.getElementById('rv-add').addEventListener('click', addComment);
    document.getElementById('rv-cp').addEventListener('click', function () {
      var t = report();
      if (navigator.clipboard) navigator.clipboard.writeText(t).then(function () { say('Скопировано'); });
      else { prompt('Скопируйте текст:', t); }
    });
    document.getElementById('rv-dl').addEventListener('click', download);
    document.getElementById('rv-rs').addEventListener('click', function () {
      if (!confirm('Удалить все свои правки и комментарии?')) return;
      db.comments = []; db.edits = [];
      document.querySelectorAll('[data-rv-orig]').forEach(function (el) {
        el.innerHTML = el.dataset.rvOrig;
      });
      save(); openList();
    });

    document.addEventListener('click', function (e) {
      if (mode !== 'comment') return;
      if (e.target.closest('#rv-bar, #rv-panel, #rv-list')) return;
      var badge = e.target.closest('.rv-badge');
      var b = e.target.closest('.rv-block');
      if (!b) return;
      e.preventDefault();
      openPanel(b, !!badge);
    }, true);

    setMode('comment');
  }

  function setMode(m) {
    mode = m;
    document.body.classList.toggle('rv-comment', m === 'comment');
    [].forEach.call(bar.querySelectorAll('button[data-m]'), function (b) {
      b.classList.toggle('on', b.dataset.m === m);
    });
    armEdit(m === 'edit');
    if (m !== 'comment') panel.classList.remove('on');
  }

  function openPanel(b, scroll) {
    cur = b;
    document.getElementById('rv-bn').textContent = b.dataset.rvName;
    document.getElementById('rv-tx').value = '';
    document.getElementById('rv-au').value = db.author || '';
    var mine = db.comments.filter(function (c) { return c.block === b.dataset.rvId; });
    document.getElementById('rv-ex').innerHTML = mine.length
      ? '<label style="margin-top:4px">Уже отмечено</label>' + mine.map(item).join('')
      : '';
    panel.classList.add('on');
    if (!scroll) setTimeout(function () { document.getElementById('rv-tx').focus(); }, 240);
  }

  function addComment() {
    var tx = document.getElementById('rv-tx').value.trim();
    if (!tx) { document.getElementById('rv-tx').focus(); return; }
    db.author = document.getElementById('rv-au').value.trim() || db.author;
    db.comments.push({
      id: uid(), block: cur.dataset.rvId, blockName: cur.dataset.rvName,
      type: curType, text: tx, author: db.author, ts: Date.now()
    });
    save();
    say('Записано');
    openPanel(cur, true);
  }

  function item(c) {
    return '<div class="rv-item"><div class="m"><span>' + esc(TYPE_NAME[c.type] || '') + '</span>' +
      '<span>' + esc(c.author || '') + '</span></div><p>' + esc(c.text) + '</p>' +
      '<button class="del" data-del="' + c.id + '">Удалить</button></div>';
  }
  function itemEdit(e) {
    return '<div class="rv-item ed"><div class="m"><span>Текст</span><span>' + esc(e.author || '') + '</span></div>' +
      '<div class="was">' + esc(e.before) + '</div><div class="now">' + esc(e.after) + '</div>' +
      '<button class="del" data-del="' + e.id + '">Отменить</button></div>';
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (m) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[m];
    });
  }

  function openList() {
    var bd = document.getElementById('rv-lb');
    var n = db.comments.length + db.edits.length;
    document.getElementById('rv-ln').textContent =
      n + ' ' + (n % 10 === 1 && n % 100 !== 11 ? 'запись' : (n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20) ? 'записи' : 'записей'));
    if (!n) {
      bd.innerHTML = '<div class="empty">Пока пусто.<br>Включите «Комментарии» и нажмите на любой блок, ' +
        'или «Правка текста» и перепишите текст прямо на странице.</div>';
    } else {
      var by = {};
      db.comments.forEach(function (c) { (by[c.blockName] = by[c.blockName] || []).push(item(c)); });
      db.edits.forEach(function (e) { (by[e.blockName] = by[e.blockName] || []).push(itemEdit(e)); });
      bd.innerHTML = Object.keys(by).map(function (k) {
        return '<div class="g">' + esc(k) + '</div>' + by[k].join('');
      }).join('');
    }
    list.classList.add('on');
    panel.classList.remove('on');
  }

  document.addEventListener('click', function (e) {
    var d = e.target.closest('[data-del]');
    if (!d) return;
    var id = d.dataset.del;
    var ed = db.edits.find(function (x) { return x.id === id; });
    if (ed) {
      var blk = document.querySelector('[data-rv-id="' + ed.block + '"]');
      var el = blk && ed.path ? blk.querySelector(ed.path) : null;
      if (el && el.dataset.rvOrig !== undefined) el.innerHTML = el.dataset.rvOrig;
      db.edits = db.edits.filter(function (x) { return x.id !== id; });
    } else {
      db.comments = db.comments.filter(function (x) { return x.id !== id; });
    }
    save();
    if (list.classList.contains('on')) openList();
    else if (cur) openPanel(cur, true);
  });

  function paint() {
    document.getElementById('rv-cnt').textContent = db.comments.length + db.edits.length;
    document.querySelectorAll('.rv-badge').forEach(function (b) { b.remove(); });
    document.querySelectorAll('.rv-touched').forEach(function (b) { b.classList.remove('rv-touched'); });
    var cnt = {};
    db.comments.forEach(function (c) { cnt[c.block] = (cnt[c.block] || 0) + 1; });
    db.edits.forEach(function (e) { cnt[e.block] = (cnt[e.block] || 0) + 1; });
    blocks.forEach(function (b) {
      var n = cnt[b.dataset.rvId];
      if (!n) return;
      b.classList.add('rv-touched');
      var el = document.createElement('div');
      el.className = 'rv-badge';
      el.textContent = n;
      el.title = 'Правок в блоке: ' + n;
      b.appendChild(el);
    });
  }

  /* ───────────── выгрузка ───────────── */
  function report() {
    var d = new Date();
    var out = ['# Правки · страница «Продвижение»', ''];
    out.push('Автор: ' + (db.author || 'не указан'));
    out.push('Дата: ' + d.toLocaleDateString('ru-RU') + ' ' + d.toLocaleTimeString('ru-RU').slice(0, 5));
    out.push('Комментариев: ' + db.comments.length + ' · правок текста: ' + db.edits.length);
    out.push('');

    if (db.edits.length) {
      out.push('## Правки текста', '');
      group(db.edits).forEach(function (g) {
        out.push('### ' + g.name, '');
        g.items.forEach(function (e) {
          out.push('- Было:  ' + e.before);
          out.push('  Стало: ' + e.after);
        });
        out.push('');
      });
    }
    if (db.comments.length) {
      out.push('## Комментарии', '');
      group(db.comments).forEach(function (g) {
        out.push('### ' + g.name, '');
        g.items.forEach(function (c) {
          out.push('- [' + (TYPE_NAME[c.type] || '') + '] ' + c.text);
        });
        out.push('');
      });
    }
    if (!db.edits.length && !db.comments.length) out.push('_Правок нет._');
    return out.join('\n');
  }
  function group(arr) {
    var by = {}, order = [];
    arr.forEach(function (x) {
      if (!by[x.blockName]) { by[x.blockName] = []; order.push(x.blockName); }
      by[x.blockName].push(x);
    });
    return order.map(function (n) { return { name: n, items: by[n] }; });
  }
  function download() {
    var blob = new Blob([report()], { type: 'text/markdown;charset=utf-8' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'pravki-prodvizhenie-' + (db.author || 'bez-imeni').replace(/\s+/g, '-').toLowerCase() + '.md';
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 2000);
    say('Файл скачан');
  }
  function say(t) {
    toast.textContent = t;
    toast.classList.add('on');
    clearTimeout(say._t);
    say._t = setTimeout(function () { toast.classList.remove('on'); }, 1800);
  }

  /* ───────────── старт ───────────── */
  function boot() {
    if (document.getElementById('rv-bar')) return;
    collect();
    css();
    ui();
    paint();
  }
  function ready() {
    if (document.documentElement.classList.contains('gated')) {
      window.addEventListener('pv:unlocked', boot, { once: true });
    } else boot();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready);
  else ready();
})();
