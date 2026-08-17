/* LATAMFILES autoindex - inyectado via sub_filter */
(function () {
  var CSS = [
    ':root{--ai-bg:#0a0e0b;--ai-row-a:#152019;--ai-row-b:#0f1612;--ai-row-hover:#1e3224;--ai-border:#2a332f;--ai-text:#e8ece9;--ai-muted:#9aa8a0;--ai-accent:#6b8f3c;--ai-accent-soft:#7fa648;--ai-head:#1a2e1f;--ai-header-h:3.5rem;--ai-max:1120px;}',
    'html{margin:0;min-height:100%;background-color:var(--ai-bg);}',
    /* Fondo militar oscuro (mismo criterio que site.css) */
    'body{margin:0;min-height:100vh;display:flex;flex-direction:column;color:var(--ai-text)!important;font-family:"Rajdhani","Segoe UI",Tahoma,sans-serif!important;font-weight:500;background-color:var(--ai-bg)!important;background-image:radial-gradient(ellipse 120% 80% at 50% -10%,rgba(55,72,40,.35),transparent 55%),radial-gradient(ellipse 90% 60% at 100% 100%,rgba(28,36,22,.55),transparent 50%),radial-gradient(ellipse 70% 50% at 0% 80%,rgba(20,28,18,.5),transparent 45%),repeating-linear-gradient(125deg,transparent 0,transparent 11px,rgba(0,0,0,.07) 11px,rgba(0,0,0,.07) 12px),repeating-linear-gradient(35deg,transparent 0,transparent 17px,rgba(107,143,60,.03) 17px,rgba(107,143,60,.03) 18px),linear-gradient(180deg,#0d120e 0%,#080b09 45%,#0a0f0c 100%)!important;background-attachment:fixed;background-size:cover;}',
    /* Cabecera igual que site.css (LATAMFILES) */
    '.latam-site-header{position:sticky;top:0;z-index:40;background:rgba(11,15,12,.35);border-bottom:1px solid var(--ai-border);backdrop-filter:blur(8px);}',
    '.latam-site-header__inner{display:flex;align-items:center;justify-content:space-between;gap:1rem;max-width:var(--ai-max);margin:0 auto;padding:0 1rem;min-height:var(--ai-header-h);}',
    '.latam-site-brand{display:inline-flex;align-items:center;color:var(--ai-text);text-decoration:none;}',
    '.latam-site-brand:hover,.latam-site-brand:focus-visible{color:var(--ai-text);}',
    '.latam-site-brand__logo{display:block;height:1.8rem;width:auto;object-fit:contain;}',
    '.latam-site-header__auth{display:flex;flex-wrap:wrap;align-items:center;justify-content:flex-end;gap:.65rem .95rem;font-size:.95rem;color:var(--ai-muted);}',
    '.latam-site-header__auth a{font-weight:600;text-decoration:none;}',
    '.latam-ext-nav{display:inline-flex;flex-wrap:wrap;align-items:center;gap:.35rem .85rem;}',
    '.latam-ext-nav__link{color:#f5f2ed;font-size:.95rem;font-weight:600;letter-spacing:.04em;text-transform:uppercase;text-decoration:none;padding:.35rem 0;border-bottom:2px solid transparent;white-space:nowrap;}',
    '.latam-ext-nav__link:hover,.latam-ext-nav__link:focus-visible{color:#fff;text-decoration:none;}',
    '.latam-ext-nav__link--external::after{content:" \\2197";font-size:.75em;opacity:.75;}',
    '.latam-ext-nav__latam{color:#f5f2ed;}',
    '.latam-ext-nav__squad{color:#ff8000;}',
    '.latam-ext-nav__link--latamsquad:hover .latam-ext-nav__squad,.latam-ext-nav__link--latamsquad:focus-visible .latam-ext-nav__squad{color:#ff9933;}',
    '.latam-ext-nav__stats{color:#ff8000;}',
    '.latam-ext-nav__link--latamstats:hover .latam-ext-nav__stats,.latam-ext-nav__link--latamstats:focus-visible .latam-ext-nav__stats{color:#ff9933;}',
    '.latam-ext-nav__torneos{color:#e53935;}',
    '.latam-ext-nav__link--latamtorneos:hover .latam-ext-nav__torneos,.latam-ext-nav__link--latamtorneos:focus-visible .latam-ext-nav__torneos{color:#ef5350;}',
    '.latam-ext-nav__link--discord{color:#5865f2;}',
    '.latam-ext-nav__link--discord:hover,.latam-ext-nav__link--discord:focus-visible{color:#7289da;}',
    '.latam-site-header__admins{color:#ffffff;font-weight:700;letter-spacing:.06em;text-decoration:none;white-space:nowrap;}',
    '.latam-site-header__admins:hover,.latam-site-header__admins:focus-visible{color:#ffffff;opacity:.85;}',
    '.latam-site-header__user{display:inline-flex;align-items:center;gap:.45rem;color:#f5f2ed;font-weight:600;text-decoration:none;max-width:14rem;}',
    'a.latam-site-header__user:hover,a.latam-site-header__user:focus-visible{color:#fff;opacity:.9;text-decoration:none;}',
    '.latam-site-header__avatar{width:1.75rem;height:1.75rem;border-radius:50%;object-fit:cover;flex-shrink:0;background:#2b2d31;border:1px solid rgba(255,255,255,.18);}',
    '.latam-site-header__user-name{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}',
    '.site-footer{margin-top:auto;border-top:1px solid var(--ai-border);background:rgba(11,15,12,.95);}',
    '.site-footer__inner{max-width:var(--ai-max);margin:0 auto;padding:1.25rem 1rem 1.75rem;color:var(--ai-muted);font-size:.9rem;text-align:center;}',
    '.site-footer__copy,.site-footer__links{margin:.35rem 0;}',
    '.site-footer__links a{color:var(--ai-muted);text-decoration:none;}',
    '.site-footer__links a:hover,.site-footer__links a:focus-visible{color:var(--ai-accent);}',
    'body>h1{margin:1.25rem 1rem .75rem;font-size:1.55rem;font-weight:700;letter-spacing:.04em;color:var(--ai-text);}',
    'body>hr{display:none;}',
    'body>pre{display:none!important;}',
    /* Barra demos: pestanas 2D/3D + servidores 1-4 */
    '.latam-ai-servers{max-width:960px;margin:1.25rem auto .85rem;padding:0 1rem;}',
    '.latam-ai-servers__inner{display:flex;flex-direction:column;gap:.85rem;}',
    '.latam-ai-servers__tabs{display:flex;flex-wrap:wrap;align-items:center;gap:.5rem .75rem;border-bottom:1px solid var(--ai-border);padding-bottom:.65rem;}',
    '.latam-ai-servers__tabs-links{display:flex;flex-wrap:wrap;align-items:center;gap:.5rem;flex:0 0 auto;}',
    '.latam-ai-servers__tab{display:inline-flex;align-items:center;justify-content:center;padding:.55rem 1rem;border:1px solid transparent;border-bottom:2px solid transparent;margin-bottom:-1px;background:transparent;color:var(--ai-muted);font-weight:700;font-size:1.05rem;letter-spacing:.04em;text-decoration:none;}',
    '.latam-ai-servers__tab:hover,.latam-ai-servers__tab:focus-visible{color:var(--ai-text);border-color:rgba(107,143,60,.35);}',
    '.latam-ai-servers__tab.is-active{color:#fff;border-color:var(--ai-border);border-bottom-color:var(--ai-accent);background:rgba(107,143,60,.18);}',
    /* Buscador: misma fila que pestanas 2D/3D */
    '.latam-ai-servers__search{display:block;flex:1 1 12rem;min-width:10rem;max-width:22rem;margin-left:auto;}',
    '.latam-ai-servers__search-input{display:block;width:100%;box-sizing:border-box;padding:.55rem .85rem;border:1px solid var(--ai-border);border-radius:4px;background:rgba(15,22,18,.9);color:var(--ai-text);font-family:inherit;font-size:1rem;font-weight:600;letter-spacing:.02em;}',
    '.latam-ai-servers__search-input::placeholder{color:var(--ai-muted);font-weight:500;}',
    '.latam-ai-servers__search-input:focus{outline:none;border-color:var(--ai-accent);box-shadow:0 0 0 2px rgba(107,143,60,.25);}',
    '.latam-ai-servers__row{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:.75rem 1rem;}',
    /* Nombre real del servidor actual (sin uppercase: nombres largos) */
    '.latam-ai-servers__hint{font-size:.9rem;font-weight:600;letter-spacing:.02em;color:var(--ai-muted);max-width:min(100%,36rem);line-height:1.35;}',
    '.latam-ai-servers__btns{display:flex;flex-wrap:wrap;gap:.5rem;}',
    '.latam-ai-servers__btn{display:inline-flex;align-items:center;justify-content:center;min-width:2.6rem;padding:.5rem .9rem;border:1px solid var(--ai-border);background:rgba(15,22,18,.85);color:var(--ai-text);font-weight:700;font-size:1rem;letter-spacing:.06em;text-decoration:none;}',
    '.latam-ai-servers__btn:hover,.latam-ai-servers__btn:focus-visible{border-color:var(--ai-accent);color:#fff;}',
    '.latam-ai-servers__btn.is-active{border-color:var(--ai-accent);background:rgba(107,143,60,.3);color:#fff;pointer-events:none;}',
    '.latam-ai-wrap{max-width:960px;margin:0 auto;padding:0 1rem;flex:1 1 auto;width:100%;box-sizing:border-box;}',
    '.latam-ai-table{width:100%;border-collapse:collapse;border:1px solid var(--ai-border);border-radius:6px;overflow:hidden;background:var(--ai-row-b);box-shadow:0 8px 24px rgba(0,0,0,.35);}',
    '.latam-ai-table thead th{background:var(--ai-head);color:var(--ai-accent-soft);text-align:left;font-size:.85rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:.7rem 1rem;border-bottom:1px solid var(--ai-border);}',
    '.latam-ai-table thead th.latam-ai-sortable{cursor:pointer;user-select:none;-webkit-user-select:none;}',
    '.latam-ai-table thead th.latam-ai-sortable:hover,.latam-ai-table thead th.latam-ai-sortable:focus-visible{color:#fff;}',
    '.latam-ai-table thead th.latam-ai-sortable .latam-ai-sort-ind{display:inline-block;margin-left:.35rem;opacity:.45;font-size:.75em;}',
    '.latam-ai-table thead th.latam-ai-sortable.is-active{color:#fff;}',
    '.latam-ai-table thead th.latam-ai-sortable.is-active .latam-ai-sort-ind{opacity:1;color:var(--ai-accent-soft);}',
    '.latam-ai-table tbody td{padding:.65rem 1rem;border-bottom:1px solid rgba(42,51,47,.65);vertical-align:middle;}',
    '.latam-ai-table tbody tr:nth-child(odd){background:var(--ai-row-a);}',
    '.latam-ai-table tbody tr:nth-child(even){background:var(--ai-row-b);}',
    '.latam-ai-table tbody tr:hover{background:var(--ai-row-hover);}',
    '.latam-ai-table a{color:var(--ai-accent);text-decoration:none;font-weight:600;}',
    '.latam-ai-table a:hover,.latam-ai-table a:focus-visible{color:var(--ai-accent-soft);text-decoration:underline;}',
    '.latam-ai-col-name{width:56%;word-break:break-all;}',
    '.latam-ai-col-date{width:26%;color:var(--ai-muted);white-space:nowrap;}',
    '.latam-ai-col-size{width:18%;color:var(--ai-muted);text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums;}',
    '.latam-ai-table thead th.latam-ai-col-size{text-align:right;}',
    '.latam-ai-parent a{color:var(--ai-accent-soft);}',
    '.latam-ai-empty{color:var(--ai-muted);padding:1rem;}',
    '.latam-ai-filter-empty{display:none;color:var(--ai-muted);padding:1rem 0 0;font-weight:600;}',
    '.latam-ai-filter-empty.is-visible{display:block;}',
    /* Overlay de carga (logo LATAMFILES) */
    '#latam-ai-loader{position:fixed;inset:0;z-index:9999;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1rem;margin:0;padding:1rem;background:#0a0e0b;color:#e8ece9;font-family:"Rajdhani","Segoe UI",Tahoma,sans-serif;}',
    '#latam-ai-loader img{display:block;height:2.4rem;width:auto;object-fit:contain;animation:latamAiPulse 1.2s ease-in-out infinite;}',
    '#latam-ai-loader p{margin:0;font-size:.95rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#9aa8a0;}',
    '@keyframes latamAiPulse{0%,100%{opacity:.55;transform:scale(.96);}50%{opacity:1;transform:scale(1);}}',
    /* Responsive header (mismo patron que stats / site.css) */
    '@media (max-width:1100px){.latam-ext-nav{gap:.25rem .45rem;}.latam-ext-nav__link--discord{display:none;}.latam-site-header__user-name{display:none;}.latam-site-header__user{max-width:none;flex-shrink:0;}.latam-ext-nav__latam{display:none;}}',
    '@media (max-width:640px){.latam-site-header__inner{flex-direction:column;align-items:stretch;flex-wrap:wrap;padding-top:.75rem;padding-bottom:.75rem;}.latam-site-header__auth{justify-content:flex-start;margin-left:0;width:100%;gap:.35rem .75rem;}.latam-ext-nav{display:contents;}.latam-ext-nav__link--discord{display:inline;}.latam-site-header__user-name{display:inline;}.latam-ext-nav__latam{display:inline;}}'
  ].join('');

  /* HTML inyectado al abrir <body> (nginx sub_filter); estilos inline por si el JS llega tarde */
  var LOADER_BOOT_STYLE =
    'body>pre,body>hr{visibility:hidden!important}' +
    '#latam-ai-loader{position:fixed;inset:0;z-index:9999;display:flex;flex-direction:column;' +
    'align-items:center;justify-content:center;gap:1rem;margin:0;padding:1rem;background:#0a0e0b;' +
    'color:#e8ece9;font-family:Segoe UI,Tahoma,sans-serif}' +
    '#latam-ai-loader img{display:block;height:2.4rem;width:auto;object-fit:contain;' +
    'animation:latamAiPulse 1.2s ease-in-out infinite}' +
    '#latam-ai-loader p{margin:0;font-size:.95rem;font-weight:600;letter-spacing:.1em;' +
    'text-transform:uppercase;color:#9aa8a0}' +
    '@keyframes latamAiPulse{0%,100%{opacity:.55;transform:scale(.96)}50%{opacity:1;transform:scale(1)}}';

  function ensureFonts() {
    if (document.getElementById('latam-ai-fonts')) return;
    var pre = document.createElement('link');
    pre.id = 'latam-ai-fonts';
    pre.rel = 'preconnect';
    pre.href = 'https://fonts.googleapis.com';
    document.head.appendChild(pre);
    var link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&display=swap';
    document.head.appendChild(link);
  }

  function ensureFavicon() {
    if (document.querySelector('link[rel="icon"]')) return;
    var icon = document.createElement('link');
    icon.rel = 'icon';
    icon.type = 'image/png';
    icon.href = '/assets/img/favicon.png';
    document.head.appendChild(icon);
  }

  /* Si nginx no inyecto el overlay, lo crea el JS (fallback). */
  function ensureLoader() {
    if (document.getElementById('latam-ai-loader')) return;
    var loader = document.createElement('div');
    loader.id = 'latam-ai-loader';
    loader.setAttribute('role', 'status');
    loader.setAttribute('aria-live', 'polite');
    loader.innerHTML =
      '<style id="latam-ai-loader-boot">' + LOADER_BOOT_STYLE + '</style>' +
      '<img src="/assets/img/latamfiles-logo.png" alt="LATAMFILES" width="180" height="36">' +
      '<p>Cargando listado...</p>';
    var body = document.body;
    if (body.firstChild) {
      body.insertBefore(loader, body.firstChild);
    } else {
      body.appendChild(loader);
    }
  }

  function removeLoader() {
    var loader = document.getElementById('latam-ai-loader');
    if (loader && loader.parentNode) {
      loader.parentNode.removeChild(loader);
    }
    var boot = document.getElementById('latam-ai-loader-boot');
    if (boot && boot.parentNode) {
      boot.parentNode.removeChild(boot);
    }
  }

  /* Cabecera LATAMFILES (logo + login); cuenta via /auth/me.php */
  function escapeHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function renderAuthSlot(data) {
    if (!data || !data.logged_in) {
      return '<a class="latam-site-header__admins" href="/admin/">ADMINS</a>';
    }
    var name = escapeHtml(data.name || 'Usuario');
    var img = data.avatar_url
      ? '<img class="latam-site-header__avatar" src="' + escapeHtml(data.avatar_url) + '" alt="" width="28" height="28" decoding="async" referrerpolicy="no-referrer">'
      : '';
    var inner = img + '<span class="latam-site-header__user-name">' + name + '</span>';
    var chip = data.is_staff
      ? '<a class="latam-site-header__user" href="/admin/" title="Panel de administracion">' + inner + '</a>'
      : '<span class="latam-site-header__user">' + inner + '</span>';
    return chip + ' &middot; <a href="/auth/logout.php">Salir</a>';
  }

  function injectHeader() {
    if (document.getElementById('latam-ai-header')) return;
    var header = document.createElement('header');
    header.id = 'latam-ai-header';
    header.className = 'latam-site-header';
    header.setAttribute('role', 'banner');
    header.innerHTML =
      '<div class="latam-site-header__inner">' +
        '<a class="latam-site-brand" href="/" aria-label="LATAMFILES - Inicio">' +
          '<img class="latam-site-brand__logo" src="/assets/img/latamfiles-logo.png" alt="LATAMFILES" width="625" height="91">' +
        '</a>' +
        '<div class="latam-site-header__auth">' +
          '<nav class="latam-ext-nav" aria-label="Enlaces comunidad">' +
            '<a class="latam-ext-nav__link latam-ext-nav__link--external latam-ext-nav__link--latamsquad" href="https://latamsquad.org" target="_blank" rel="noopener noreferrer"><span class="latam-ext-nav__latam">LATAM</span><span class="latam-ext-nav__squad">SQUAD</span></a>' +
            '<a class="latam-ext-nav__link latam-ext-nav__link--external latam-ext-nav__link--latamstats" href="https://stats.latamsquad.org/" target="_blank" rel="noopener noreferrer"><span class="latam-ext-nav__latam">LATAM</span><span class="latam-ext-nav__stats">STATS</span></a>' +
            '<a class="latam-ext-nav__link latam-ext-nav__link--external latam-ext-nav__link--latamtorneos" href="https://torneos.latamsquad.org/" target="_blank" rel="noopener noreferrer"><span class="latam-ext-nav__latam">LATAM</span><span class="latam-ext-nav__torneos">TORNEOS</span></a>' +
            '<a class="latam-ext-nav__link latam-ext-nav__link--external latam-ext-nav__link--discord" href="https://discord.gg/latamsquad" target="_blank" rel="noopener noreferrer">Discord</a>' +
          '</nav>' +
          '<span id="latam-ai-auth-slot"><a class="latam-site-header__admins" href="/admin/">ADMINS</a></span>' +
        '</div>' +
      '</div>';
    var body = document.body;
    body.insertBefore(header, body.firstChild);

    // Completa avatar + nombre si hay sesion Discord
    fetch('/auth/me.php', { credentials: 'same-origin', cache: 'no-store' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        var slot = document.getElementById('latam-ai-auth-slot');
        if (slot) {
          slot.innerHTML = renderAuthSlot(data);
        }
      })
      .catch(function () { /* dejar ADMINS */ });
  }

  /* Pie igual a stats / LATAMFILES PHP (latam_render_footer) */
  function injectFooter() {
    if (document.getElementById('latam-ai-footer')) return;
    var year = new Date().getFullYear();
    var footer = document.createElement('footer');
    footer.id = 'latam-ai-footer';
    footer.className = 'site-footer';
    footer.innerHTML =
      '<div class="site-footer__inner">' +
        '<p class="site-footer__copy">' +
          '&copy; 2021 - ' + year +
          ' <a href="https://latamsquad.org" target="_blank" rel="noopener noreferrer">LATAMSQUAD</a>' +
        '</p>' +
        '<p class="site-footer__links">' +
          '<a href="/">Juegos</a>' +
          ' <span aria-hidden="true">&middot;</span> ' +
          '<a href="/pr.php">Inicio</a>' +
          ' <span aria-hidden="true">&middot;</span> ' +
          '<a href="/pr/tracker/?srv=1">Tracker</a>' +
          ' <span aria-hidden="true">&middot;</span> ' +
          '<a href="/pr/logs/">Logs</a>' +
          ' <span aria-hidden="true">&middot;</span> ' +
          '<a href="https://discord.gg/latamsquad" target="_blank" rel="noopener noreferrer">Discord</a>' +
        '</p>' +
      '</div>';
    document.body.appendChild(footer);
  }

  /* demos2d / demos3d: ambos usan /pr/demosXd/svN/ */
  function getDemoContext() {
    var p = location.pathname || '';
    if (/^\/pr\/demos2d(\/|$)/i.test(p)) {
      var m2 = p.match(/^\/pr\/demos2d\/sv([1-4])(?:\/|$)/i);
      if (!m2) return null;
      return { kind: '2d', srv: parseInt(m2[1], 10) };
    }
    if (/^\/pr\/demos3d(\/|$)/i.test(p)) {
      var m3 = p.match(/^\/pr\/demos3d\/sv([1-4])(?:\/|$)/i);
      if (!m3) return null;
      return { kind: '3d', srv: parseInt(m3[1], 10) };
    }
    return null;
  }

  function demoServerHref(kind, n) {
    if (kind === '2d') {
      return '/pr/demos2d/sv' + n + '/';
    }
    return '/pr/demos3d/sv' + n + '/';
  }

  var DEMOS_DEFAULTS = {
    servers_visible: [1, 2, 3, 4],
    sort: 'newest',
    tab_2d: 'PRdemos 2D',
    tab_3d: 'BF2demos 3D',
    server_label: 'Servidor',
    server_names: {
      1: '[LATAMSQUAD] #1 Mapas Mixtos - latamsquad.org',
      2: '[LATAMSQUAD] #2 Ranking - EnemyVOIP - Tesoros - latamsquad.org',
      3: '[LATAMSQUAD] #3 Cooperativo - latamsquad.org',
      4: '[LATAMSQUAD] #4 Eventos - latamsquad.org'
    }
  };

  function copyServerNames(src) {
    var out = {};
    for (var i = 1; i <= 4; i++) {
      out[i] = src[i] || src[String(i)] || DEMOS_DEFAULTS.server_names[i];
    }
    return out;
  }

  function normalizeDemosSettings(raw) {
    var out = {
      servers_visible: DEMOS_DEFAULTS.servers_visible.slice(),
      sort: DEMOS_DEFAULTS.sort,
      tab_2d: DEMOS_DEFAULTS.tab_2d,
      tab_3d: DEMOS_DEFAULTS.tab_3d,
      server_label: DEMOS_DEFAULTS.server_label,
      server_names: copyServerNames(DEMOS_DEFAULTS.server_names)
    };
    if (!raw || typeof raw !== 'object') return out;
    var servers = [];
    var list = raw.servers_visible;
    if (list && list.length) {
      for (var i = 0; i < list.length; i++) {
        var n = parseInt(list[i], 10);
        if (n >= 1 && n <= 4 && servers.indexOf(n) < 0) servers.push(n);
      }
      servers.sort(function (a, b) { return a - b; });
      if (servers.length) out.servers_visible = servers;
    }
    if (raw.sort === 'newest' || raw.sort === 'name') out.sort = raw.sort;
    if (typeof raw.tab_2d === 'string') {
      var t2 = raw.tab_2d.replace(/^\s+|\s+$/g, '');
      if (t2 && t2.length <= 40) out.tab_2d = t2;
    }
    if (typeof raw.tab_3d === 'string') {
      var t3 = raw.tab_3d.replace(/^\s+|\s+$/g, '');
      if (t3 && t3.length <= 40) out.tab_3d = t3;
    }
    if (typeof raw.server_label === 'string') {
      var lb = raw.server_label.replace(/^\s+|\s+$/g, '');
      if (lb && lb.length <= 24) out.server_label = lb;
    }
    if (raw.server_names && typeof raw.server_names === 'object') {
      for (var si = 1; si <= 4; si++) {
        var sn = raw.server_names[si] || raw.server_names[String(si)];
        if (typeof sn === 'string') {
          var trimmed = sn.replace(/^\s+|\s+$/g, '');
          if (trimmed && trimmed.length <= 80) out.server_names[si] = trimmed;
        }
      }
    }
    return out;
  }

  /* Nombre a mostrar junto a los botones 1-4 (servidor de la URL actual) */
  function currentServerDisplayName(settings, srv) {
    var names = (settings && settings.server_names) || DEMOS_DEFAULTS.server_names;
    var name = names[srv] || names[String(srv)];
    if (typeof name === 'string' && name.replace(/^\s+|\s+$/g, '')) return name;
    return DEMOS_DEFAULTS.server_names[srv] || ('Servidor ' + srv);
  }

  function fetchDemosSettings(cb) {
    if (typeof fetch !== 'function') {
      cb(DEMOS_DEFAULTS);
      return;
    }
    fetch('/assets/demos-settings.json', { cache: 'no-store' })
      .then(function (res) {
        if (!res.ok) throw new Error('http ' + res.status);
        return res.json();
      })
      .then(function (data) {
        cb(normalizeDemosSettings(data));
      })
      .catch(function () {
        cb(DEMOS_DEFAULTS);
      });
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  /* Reemplaza el h1 "Index of ..." por pestanas 2D/3D + botones de servidor */
  function injectServerNav(settings) {
    if (document.getElementById('latam-ai-servers')) return;
    var ctx = getDemoContext();
    if (!ctx) return;
    settings = settings || DEMOS_DEFAULTS;

    var visible = settings.servers_visible || DEMOS_DEFAULTS.servers_visible;
    if (visible.indexOf(ctx.srv) < 0) {
      location.replace(demoServerHref(ctx.kind, visible[0]));
      return;
    }

    var nav = document.createElement('nav');
    nav.id = 'latam-ai-servers';
    nav.className = 'latam-ai-servers';
    nav.setAttribute('aria-label', 'Demos y servidores');

    var tab2d = ctx.kind === '2d';
    var tab3d = ctx.kind === '3d';
    var tab2Text = escapeHtml(settings.tab_2d || DEMOS_DEFAULTS.tab_2d);
    var tab3Text = escapeHtml(settings.tab_3d || DEMOS_DEFAULTS.tab_3d);
    var srvLabel = escapeHtml(currentServerDisplayName(settings, ctx.srv));
    var parts = [
      '<div class="latam-ai-servers__inner">',
      '<div class="latam-ai-servers__tabs">',
      '<div class="latam-ai-servers__tabs-links" role="tablist" aria-label="Tipo de demo">',
      '<a class="latam-ai-servers__tab' + (tab2d ? ' is-active' : '') + '"' +
        ' role="tab" href="' + demoServerHref('2d', ctx.srv) + '"' +
        (tab2d ? ' aria-selected="true" aria-current="page"' : ' aria-selected="false"') +
        '>' + tab2Text + '</a>',
      '<a class="latam-ai-servers__tab' + (tab3d ? ' is-active' : '') + '"' +
        ' role="tab" href="' + demoServerHref('3d', ctx.srv) + '"' +
        (tab3d ? ' aria-selected="true" aria-current="page"' : ' aria-selected="false"') +
        '>' + tab3Text + '</a>',
      '</div>',
      '<div class="latam-ai-servers__search">',
      '<label class="latam-ai-servers__search-label" for="latam-ai-search" style="position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);border:0;">Buscar demos</label>',
      '<input id="latam-ai-search" class="latam-ai-servers__search-input" type="search" name="q" placeholder="Buscar..." autocomplete="off" spellcheck="false">',
      '</div>',
      '</div>',
      '<div class="latam-ai-servers__row">',
      '<span class="latam-ai-servers__hint">' + srvLabel + '</span>',
      '<div class="latam-ai-servers__btns" role="group" aria-label="Elegir servidor">'
    ];
    for (var vi = 0; vi < visible.length; vi++) {
      var i = visible[vi];
      var active = i === ctx.srv;
      parts.push(
        '<a class="latam-ai-servers__btn' + (active ? ' is-active' : '') + '"' +
          ' href="' + demoServerHref(ctx.kind, i) + '"' +
          (active ? ' aria-current="page"' : '') +
          '>' + i + '</a>'
      );
    }
    parts.push('</div></div></div>');
    nav.innerHTML = parts.join('');

    var h1 = document.querySelector('body > h1');
    if (h1 && h1.parentNode) {
      h1.parentNode.replaceChild(nav, h1);
      return;
    }
    var header = document.getElementById('latam-ai-header');
    if (header && header.nextSibling) {
      header.parentNode.insertBefore(nav, header.nextSibling);
    } else {
      document.body.appendChild(nav);
    }
  }

  function fmtSize(raw) {
    if (raw == null || raw === '' || raw === '-') return '-';
    var n = parseInt(raw, 10);
    if (isNaN(n)) return String(raw);
    if (n < 1024) return n + ' B';
    var units = ['KB', 'MB', 'GB', 'TB'];
    var x = n;
    var i = -1;
    do {
      x = x / 1024;
      i += 1;
    } while (x >= 1024 && i < units.length - 1);
    return x.toFixed(x >= 10 || i === 0 ? 0 : 1) + ' ' + units[i];
  }

  function parseLine(line) {
    var m = line.match(/^<a href="([^"]*)">([^<]*)<\/a>\s+(\S+\s+\S+)\s+(\S+)\s*$/);
    if (m) {
      return { href: m[1], name: m[2], date: m[3], size: m[4] };
    }
    m = line.match(/^<a href="([^"]*)">([^<]*)<\/a>\s*$/);
    if (m) {
      return { href: m[1], name: m[2], date: '', size: '-' };
    }
    return null;
  }

  /* Fecha nginx autoindex: "20-Oct-2025 01:48" */
  var NGX_MONTHS = {
    Jan: 0, Feb: 1, Mar: 2, Apr: 3, May: 4, Jun: 5,
    Jul: 6, Aug: 7, Sep: 8, Oct: 9, Nov: 10, Dec: 11
  };

  function parseNginxDate(dateStr) {
    if (!dateStr) return 0;
    var m = String(dateStr).match(
      /^(\d{1,2})-([A-Za-z]{3})-(\d{4})\s+(\d{1,2}):(\d{2})(?::(\d{2}))?$/
    );
    if (!m) return 0;
    var mon = NGX_MONTHS[m[2]];
    if (mon == null) return 0;
    var sec = m[6] ? parseInt(m[6], 10) : 0;
    return Date.UTC(
      parseInt(m[3], 10),
      mon,
      parseInt(m[1], 10),
      parseInt(m[4], 10),
      parseInt(m[5], 10),
      sec
    );
  }

  function parseSizeBytes(raw) {
    if (raw == null || raw === '' || raw === '-') return -1;
    var n = parseInt(raw, 10);
    return isNaN(n) ? -1 : n;
  }

  /* key: name|date|size ; dir: 1 asc, -1 desc */
  function sortRowsBy(rows, key, dir) {
    var d = dir < 0 ? -1 : 1;
    rows.sort(function (a, b) {
      var cmp = 0;
      if (key === 'date') {
        cmp = (a.dateMs || 0) - (b.dateMs || 0);
      } else if (key === 'size') {
        cmp = (a.sizeBytes || 0) - (b.sizeBytes || 0);
      } else {
        cmp = String(a.name || '').localeCompare(String(b.name || ''), undefined, {
          sensitivity: 'base',
          numeric: true
        });
      }
      if (cmp === 0 && key !== 'name') {
        cmp = String(a.name || '').localeCompare(String(b.name || ''), undefined, {
          sensitivity: 'base',
          numeric: true
        });
      }
      return cmp * d;
    });
  }

  /* Mas nuevos primero (default) */
  function sortRowsNewestFirst(rows) {
    sortRowsBy(rows, 'date', -1);
  }

  function sortRowsByName(rows) {
    sortRowsBy(rows, 'name', 1);
  }

  function renderTableBody(tbody, rows) {
    var html = [];
    for (var r = 0; r < rows.length; r++) {
      var it = rows[r];
      html.push(
        '<tr>' +
        '<td class="latam-ai-col-name"><a href="' + it.href + '">' + it.name + '</a></td>' +
        '<td class="latam-ai-col-date">' + (it.date || '-') + '</td>' +
        '<td class="latam-ai-col-size">' + fmtSize(it.size) + '</td>' +
        '</tr>'
      );
    }
    tbody.innerHTML = html.join('');
  }

  function updateSortIndicators(table, key, dir) {
    var heads = table.querySelectorAll('thead th.latam-ai-sortable');
    for (var i = 0; i < heads.length; i++) {
      var th = heads[i];
      var ind = th.querySelector('.latam-ai-sort-ind');
      var k = th.getAttribute('data-sort');
      if (k === key) {
        th.className = th.className.replace(/\bis-active\b/g, '') + ' is-active';
        th.setAttribute('aria-sort', dir < 0 ? 'descending' : 'ascending');
        if (ind) ind.textContent = dir < 0 ? '\u25BC' : '\u25B2';
      } else {
        th.className = th.className.replace(/\bis-active\b/g, '').replace(/\s+/g, ' ').replace(/^\s+|\s+$/g, '');
        th.removeAttribute('aria-sort');
        if (ind) ind.textContent = '\u2195';
      }
    }
  }

  /* Click en encabezados: ordenar por nombre / fecha / tamano */
  function bindTableSort(wrap, rows, initialKey, initialDir) {
    var table = wrap.querySelector('.latam-ai-table');
    if (!table || !rows || !rows.length) return;
    var tbody = table.querySelector('tbody');
    if (!tbody) return;

    var state = {
      key: initialKey || 'date',
      dir: initialDir != null ? initialDir : -1
    };
    wrap._latamRows = rows;
    wrap._latamSort = state;

    function resort() {
      sortRowsBy(rows, state.key, state.dir);
      renderTableBody(tbody, rows);
      updateSortIndicators(table, state.key, state.dir);
      if (typeof wrap._latamApplyFilter === 'function') {
        wrap._latamApplyFilter();
      }
    }

    var heads = table.querySelectorAll('thead th.latam-ai-sortable');
    for (var i = 0; i < heads.length; i++) {
      (function (th) {
        th.setAttribute('tabindex', '0');
        th.setAttribute('role', 'columnheader');
        th.addEventListener('click', function () {
          var key = th.getAttribute('data-sort') || 'name';
          if (state.key === key) {
            state.dir = -state.dir;
          } else {
            state.key = key;
            state.dir = (key === 'name') ? 1 : -1;
          }
          resort();
        });
        th.addEventListener('keydown', function (ev) {
          if (ev.key === 'Enter' || ev.key === ' ') {
            ev.preventDefault();
            th.click();
          }
        });
      })(heads[i]);
    }

    updateSortIndicators(table, state.key, state.dir);
  }

  /* Filtra filas de la tabla por nombre (solo listado del servidor actual). */
  function bindDemoSearch(wrap) {
    var input = document.getElementById('latam-ai-search');
    if (!input || !wrap) return;
    var table = wrap.querySelector('.latam-ai-table');
    if (!table) return;
    var tbody = table.querySelector('tbody');
    if (!tbody) return;

    var empty = document.createElement('p');
    empty.className = 'latam-ai-filter-empty';
    empty.setAttribute('role', 'status');
    empty.textContent = 'No hay resultados para esa busqueda.';
    wrap.appendChild(empty);

    function applyFilter() {
      tbody = table.querySelector('tbody');
      if (!tbody) return;
      var q = String(input.value || '').replace(/^\s+|\s+$/g, '').toLowerCase();
      var rows = tbody.querySelectorAll('tr');
      var visible = 0;
      for (var i = 0; i < rows.length; i++) {
        var row = rows[i];
        if (row.className.indexOf('latam-ai-parent') >= 0) {
          row.style.display = '';
          continue;
        }
        var nameCell = row.querySelector('.latam-ai-col-name');
        var name = nameCell ? String(nameCell.textContent || '').toLowerCase() : '';
        var show = !q || name.indexOf(q) >= 0;
        row.style.display = show ? '' : 'none';
        if (show) visible += 1;
      }
      if (q && visible === 0) {
        empty.className = 'latam-ai-filter-empty is-visible';
        table.style.display = 'none';
      } else {
        empty.className = 'latam-ai-filter-empty';
        table.style.display = '';
      }
    }

    wrap._latamApplyFilter = applyFilter;
    input.addEventListener('input', applyFilter);
    input.addEventListener('search', applyFilter);
  }

  function finishBuild(settings) {
    if (document.getElementById('latam-ai-style')) {
      removeLoader();
      return;
    }
    ensureLoader();
    ensureFonts();
    ensureFavicon();
    var style = document.createElement('style');
    style.id = 'latam-ai-style';
    style.appendChild(document.createTextNode(CSS));
    document.head.appendChild(style);

    injectHeader();
    injectServerNav(settings);
    injectFooter();

    var pre = document.querySelector('body > pre');
    if (!pre) {
      removeLoader();
      return;
    }
    var raw = pre.innerHTML.replace(/\r/g, '');
    var lines = raw.split('\n');
    var rows = [];
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i].replace(/^\s+|\s+$/g, '');
      if (!line) continue;
      var item = parseLine(line);
      if (!item) continue;
      /* No mostrar enlace al directorio padre ../ */
      if (item.href === '../' || item.name === '../') continue;
      item.dateMs = parseNginxDate(item.date);
      item.sizeBytes = parseSizeBytes(item.size);
      rows.push(item);
    }
    var initialKey = 'date';
    var initialDir = -1;
    if (settings && settings.sort === 'name') {
      initialKey = 'name';
      initialDir = 1;
      sortRowsByName(rows);
    } else {
      sortRowsNewestFirst(rows);
    }

    var wrap = document.createElement('div');
    wrap.className = 'latam-ai-wrap';
    if (!rows.length) {
      wrap.innerHTML = '<p class="latam-ai-empty">No hay archivos en esta carpeta.</p>';
    } else {
      var html = [
        '<table class="latam-ai-table" role="table">',
        '<thead><tr>',
        '<th class="latam-ai-col-name latam-ai-sortable" data-sort="name" title="Ordenar por nombre">Nombre<span class="latam-ai-sort-ind" aria-hidden="true">\u2195</span></th>',
        '<th class="latam-ai-col-date latam-ai-sortable" data-sort="date" title="Ordenar por fecha">Fecha<span class="latam-ai-sort-ind" aria-hidden="true">\u2195</span></th>',
        '<th class="latam-ai-col-size latam-ai-sortable" data-sort="size" title="Ordenar por tamano">Tama\u00f1o<span class="latam-ai-sort-ind" aria-hidden="true">\u2195</span></th>',
        '</tr></thead><tbody>'
      ];
      for (var r = 0; r < rows.length; r++) {
        var it = rows[r];
        html.push(
          '<tr>' +
          '<td class="latam-ai-col-name"><a href="' + it.href + '">' + it.name + '</a></td>' +
          '<td class="latam-ai-col-date">' + (it.date || '-') + '</td>' +
          '<td class="latam-ai-col-size">' + fmtSize(it.size) + '</td>' +
          '</tr>'
        );
      }
      html.push('</tbody></table>');
      wrap.innerHTML = html.join('');
    }
    pre.parentNode.insertBefore(wrap, pre);
    if (rows.length) {
      bindTableSort(wrap, rows, initialKey, initialDir);
    }
    if (getDemoContext()) {
      bindDemoSearch(wrap);
    }
    removeLoader();
  }

  function build() {
    if (document.getElementById('latam-ai-style')) {
      removeLoader();
      return;
    }
    if (getDemoContext()) {
      fetchDemosSettings(function (settings) {
        finishBuild(settings);
      });
      return;
    }
    finishBuild(null);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', build);
  } else {
    build();
  }
})();
