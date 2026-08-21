/* ── Пароль на страницу «Продвижение» ──────────────────────
   Пароль: prodvijenie2026
   Хранится хешем SHA-256, не открытым текстом.

   Прямая ссылка без ввода:  /prodvizhenie?p=prodvijenie2026
   Сбросить доступ:          /prodvizhenie?logout

   Это защита от случайных переходов и от индексации.
   Проверка происходит в браузере, поэтому подготовленный
   человек её обойдёт. Для черновика лендинга этого хватает.
   Если понадобится настоящая защита — Cloudflare Access.
──────────────────────────────────────────────────────────── */
(function () {
  var HASH = '1e5fc4ee16c8ac8bd57f86f6cbe8ef1aaf9b89e3fd1c45b4cfadd2618d14c00f';
  /* Запасной вариант на случай, когда браузер не даёт crypto.subtle:
     встроенные окна Telegram и Instagram, http без сертификата, старые версии.
     Без него человек с правильным паролем не смог бы войти вообще. */
  var PASS = 'prodvijenie2026';
  var KEY  = 'pv_gate_v1';
  var d = document;

  d.documentElement.classList.add('gated');
  var s = d.createElement('style');
  s.textContent =
    'html.gated body{overflow:hidden}' +
    'html.gated body>*:not(#pvgate){visibility:hidden!important}' +
    '#pvgate{position:fixed;inset:0;z-index:99999;background:#22314A;display:flex;' +
      'align-items:center;justify-content:center;padding:24px;' +
      'font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}' +
    '#pvgate .b{width:100%;max-width:380px;text-align:center;color:#EFEAE0}' +
    '#pvgate .m{font-size:34px;color:#F5C63A;margin-bottom:22px;line-height:1}' +
    '#pvgate h1{font-family:Georgia,serif;font-weight:400;font-size:29px;line-height:1.16;' +
      'margin:0 0 10px;color:#fff}' +
    '#pvgate p{font-size:14.5px;line-height:1.55;color:rgba(239,234,224,.7);margin:0 0 24px}' +
    '#pvgate input{width:100%;padding:15px 16px;border:1px solid rgba(239,234,224,.28);' +
      'background:rgba(239,234,224,.07);color:#fff;font-size:16px;border-radius:3px;' +
      'outline:none;text-align:center;letter-spacing:.04em;box-sizing:border-box;' +
      '-webkit-appearance:none}' +
    '#pvgate input:focus{border-color:#F5C63A;background:rgba(239,234,224,.12)}' +
    '#pvgate button{width:100%;margin-top:11px;padding:15px;border:0;border-radius:3px;' +
      'background:#F5C63A;color:#1A1717;font-size:14px;font-weight:600;letter-spacing:.1em;' +
      'text-transform:uppercase;cursor:pointer;transition:background .2s}' +
    '#pvgate button:hover{background:#FFDD6B}' +
    '#pvgate .e{min-height:20px;margin-top:12px;font-size:13.5px;color:#F09B8E}';
  (d.head || d.documentElement).appendChild(s);

  function open() {
    d.documentElement.classList.remove('gated');
    var g = d.getElementById('pvgate');
    if (g) g.remove();
    window.dispatchEvent(new Event('pv:unlocked'));
  }

  function sha256(txt) {
    if (!(window.crypto && crypto.subtle)) return Promise.resolve(null);
    return crypto.subtle.digest('SHA-256', new TextEncoder().encode(txt))
      .then(function (buf) {
        return Array.prototype.map.call(new Uint8Array(buf), function (b) {
          return b.toString(16).padStart(2, '0');
        }).join('');
      });
  }

  var q = new URLSearchParams(location.search);

  if (q.has('logout')) {
    try { localStorage.removeItem(KEY); } catch (e) {}
    history.replaceState(null, '', location.pathname);
  } else {
    try {
      if (localStorage.getItem(KEY) === HASH) { d.documentElement.classList.remove('gated'); return; }
    } catch (e) {}
  }

  function tryPass(txt, onFail) {
    var v = String(txt).trim();
    sha256(v).then(function (h) {
      var ok = h ? (h === HASH) : (v === PASS);
      if (ok) {
        try { localStorage.setItem(KEY, HASH); } catch (e) {}
        open();
      } else if (onFail) onFail();
    }).catch(function () {
      if (v === PASS) {
        try { localStorage.setItem(KEY, HASH); } catch (e) {}
        open();
      } else if (onFail) onFail();
    });
  }

  var fromUrl = q.get('p');

  function build() {
    var g = d.createElement('div');
    g.id = 'pvgate';
    g.innerHTML =
      '<div class="b">' +
        '<div class="m">&#9737;</div>' +
        '<h1>Черновик страницы</h1>' +
        '<p>Страница ещё не опубликована. Введите пароль, который прислала команда.</p>' +
        '<input id="pvi" type="password" placeholder="пароль" autocomplete="off" ' +
          'autocapitalize="off" spellcheck="false">' +
        '<button id="pvb">Открыть</button>' +
        '<div class="e" id="pve"></div>' +
      '</div>';
    d.body.appendChild(g);

    var inp = d.getElementById('pvi'),
        btn = d.getElementById('pvb'),
        err = d.getElementById('pve');

    function go() {
      err.textContent = '';
      tryPass(inp.value, function () {
        err.textContent = 'Пароль не подошёл';
        inp.value = '';
        inp.focus();
      });
    }
    btn.addEventListener('click', go);
    inp.addEventListener('keydown', function (e) { if (e.key === 'Enter') go(); });
    setTimeout(function () { inp.focus(); }, 60);
  }

  function start() {
    if (fromUrl) {
      history.replaceState(null, '', location.pathname);
      tryPass(fromUrl, build);
    } else {
      build();
    }
  }

  if (d.readyState === 'loading') d.addEventListener('DOMContentLoaded', start);
  else start();
})();
