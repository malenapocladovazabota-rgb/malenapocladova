/* ── Персональные коды VIP-участников ──────────────────────
   Ключ слева — код, который получает участник.
   Значение справа — имя, оно подставится в сертификат.

   Добавить нового: допишите строку в MEMBERS.
   Отозвать доступ: удалите строку.

   Это лёгкая защита от случайных переходов. Кто откроет
   исходный код страницы, увидит список. Для VIP-материалов
   этого достаточно, для чего-то серьёзного нужен Cloudflare Access.
──────────────────────────────────────────────────────────── */
(function () {
  var MEMBERS = {
    'reels-dqzn': 'Maryam Abdullaeva',
    'reels-xh8x': 'Mariia Bahnit',
    'reels-z8fy': 'Alina Civan',
    'reels-jcsn': 'Ecaterina Totomir',
    'reels-ct89': 'Aurica Darii',
    'reels-epvb': 'Svetlana Krupenina',
    'reels-8tce': 'Lesia Yaniuk',
    'reels-f7bf': 'Veronica Guzun',

    // служебные, для команды
    'malena-admin': 'Малена Покладова',
    'lev-admin': 'Лев Покладов'
  };

  var KEY = 'vip_member_v2';

  // уже входил раньше
  try {
    var saved = JSON.parse(localStorage.getItem(KEY) || 'null');
    if (saved && MEMBERS[saved.code] ) {
      window.VIP_MEMBER = { code: saved.code, name: MEMBERS[saved.code] };
      return;
    }
  } catch (e) {}

  // код можно передать ссылкой: /vip/?k=reels-xxxx
  var fromUrl = new URLSearchParams(location.search).get('k');
  if (fromUrl && MEMBERS[fromUrl.trim().toLowerCase()]) {
    var c = fromUrl.trim().toLowerCase();
    localStorage.setItem(KEY, JSON.stringify({ code: c }));
    window.VIP_MEMBER = { code: c, name: MEMBERS[c] };
    history.replaceState(null, '', location.pathname);
    return;
  }

  function build() {
    document.body.classList.add('locked');
    var g = document.createElement('div');
    g.id = 'gate';
    g.innerHTML =
      '<div class="box">' +
        '<div class="lock">✦</div>' +
        '<h1>Материалы<br>для VIP</h1>' +
        '<p>Введите личный код из вашего письма или из чата поддержки. Код у каждого свой.</p>' +
        '<input id="gp" type="text" placeholder="reels-xxxx" autocomplete="off" spellcheck="false" autocapitalize="off">' +
        '<button id="gb">Войти</button>' +
        '<div class="err" id="ge"></div>' +
      '</div>';
    document.body.appendChild(g);

    var inp = document.getElementById('gp');
    var err = document.getElementById('ge');

    function check() {
      var v = inp.value.trim().toLowerCase();
      if (MEMBERS[v]) {
        localStorage.setItem(KEY, JSON.stringify({ code: v }));
        window.VIP_MEMBER = { code: v, name: MEMBERS[v] };
        g.remove();
        document.body.classList.remove('locked');
        document.dispatchEvent(new CustomEvent('vip-ready'));
      } else {
        err.textContent = 'Код не подошёл';
        inp.value = '';
        inp.focus();
      }
    }
    document.getElementById('gb').addEventListener('click', check);
    inp.addEventListener('keydown', function (e) { if (e.key === 'Enter') check(); });
    setTimeout(function () { inp.focus(); }, 120);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', build);
  } else {
    build();
  }
})();
