# LATAMFILES Admin Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a staff-only `/admin/` shell (home + sidebar placeholders) using existing Discord OAuth, with ADMINS links pointing there.

**Architecture:** PHP pages under `C:/nginx/html/admin/` share `_bootstrap.php` (session + staff gate) and `_layout.php` (header/sidebar). Nginx FastCGI serves `/admin/*.php` like `/auth/`. Public headers and autoindex JS link ADMINS to `/admin/`. Repo mirrors live under `docs/nginx-templates/`.

**Tech Stack:** PHP 8.x, existing `auth/lib.php`, Nginx + FastCGI, `assets/css/site.css`, vanilla HTML.

## Global Constraints

- ASCII only in PHP comments/strings (no fancy dashes/quotes) - Project Reality / Py2 habit; keep PHP clean ASCII too.
- Do not expose Discord `client_secret` or full auth config in the panel.
- All admin responses must send `noindex` / `nofollow`.
- Validate staff on every admin request via `auth_is_staff()`.
- v1: no settings persistence, no Nginx reload, no fake setting forms.
- Live site root: `C:/nginx/html/`. Conf: `C:/nginx/conf/latamsquad-locations.conf`.
- After Nginx conf changes: `nginx.exe -t` then `nginx.exe -s reload` (needs host approval if gated).

---

## File map

| Path | Responsibility |
|------|----------------|
| `C:/nginx/html/admin/_bootstrap.php` | require auth lib, session, gate, helpers |
| `C:/nginx/html/admin/_layout.php` | `admin_render_start()` / `admin_render_end()` |
| `C:/nginx/html/admin/index.php` | Home |
| `C:/nginx/html/admin/traffic.php` | Placeholder Trafico |
| `C:/nginx/html/admin/demos.php` | Placeholder Demos |
| `C:/nginx/html/admin/auth-settings.php` | Placeholder Auth |
| `C:/nginx/html/assets/css/site.css` | `.latam-admin-*` styles |
| `C:/nginx/conf/latamsquad-locations.conf` | `/admin/` FastCGI location |
| `C:/nginx/html/auth/callback.php` | Honor `$_SESSION['auth_return']` after login |
| `C:/nginx/html/pr.php`, `index.php` | ADMINS href -> `/admin/` |
| `C:/nginx/html/assets/autoindex-enhance.js` | ADMINS href -> `/admin/` |
| `docs/nginx-templates/**` | Mirror of deployed HTML/conf for the repo |

---

### Task 1: Admin bootstrap (auth gate)

**Files:**
- Create: `C:/nginx/html/admin/_bootstrap.php`
- Modify: `C:/nginx/html/auth/callback.php` (post-login return)
- Mirror: `docs/nginx-templates/admin/_bootstrap.php`, `docs/nginx-templates/auth/callback.php`

**Interfaces:**
- Consumes: `auth_start_session()`, `auth_send_noindex()`, `auth_current_discord_id()`, `auth_is_staff()`, `auth_display_name()`, `auth_render_notice_page()` from `auth/lib.php`
- Produces: after include, caller may assume staff session; helpers `admin_h(string $s): string`, `admin_nav_key` not needed yet

- [ ] **Step 1: Create `C:/nginx/html/admin/_bootstrap.php`**

```php
<?php
declare(strict_types=1);

require_once dirname(__DIR__) . '/auth/lib.php';

/**
 * Escape HTML.
 */
function admin_h(string $s): string
{
    return htmlspecialchars($s, ENT_QUOTES, 'UTF-8');
}

/**
 * Safe internal return path only (same-site path).
 */
function admin_safe_return_path(?string $path): string
{
    if ($path === null || $path === '') {
        return '/admin/';
    }
    if ($path[0] !== '/' || str_starts_with($path, '//')) {
        return '/admin/';
    }
    if (str_starts_with($path, '/auth/')) {
        return '/admin/';
    }
    return $path;
}

auth_start_session();
auth_send_noindex();

$discordId = auth_current_discord_id();
if ($discordId === null) {
    $_SESSION['auth_return'] = admin_safe_return_path(
        isset($_SERVER['REQUEST_URI']) ? (string) $_SERVER['REQUEST_URI'] : '/admin/'
    );
    header('Location: /auth/discord.php', true, 302);
    exit;
}

if (!auth_is_staff()) {
    auth_render_notice_page(
        'Acceso solo para administradores',
        'Acceso restringido',
        'LATAMFILES es solo para el staff de LATAMSQUAD. Tu cuenta de Discord no tiene permisos de administrador en este sitio.',
        'Si eres jugador, tus estadisticas y tu perfil estan en latamstats.pro.',
        [
            ['href' => 'https://latamstats.pro/', 'label' => 'Ir a latamstats.pro', 'primary' => true],
            ['href' => '/', 'label' => 'Volver al inicio'],
        ],
        403
    );
}
```

- [ ] **Step 2: Update callback redirect to honor `auth_return`**

In `C:/nginx/html/auth/callback.php`, replace the final redirect:

```php
$return = '/';
if (isset($_SESSION['auth_return']) && is_string($_SESSION['auth_return'])) {
    $candidate = $_SESSION['auth_return'];
    unset($_SESSION['auth_return']);
    if ($candidate !== '' && $candidate[0] === '/' && !str_starts_with($candidate, '//')
        && !str_starts_with($candidate, '/auth/')) {
        $return = $candidate;
    }
}
header('Location: ' . $return, true, 302);
exit;
```

- [ ] **Step 3: Syntax check**

Run:

```powershell
php -l C:\nginx\html\admin\_bootstrap.php
php -l C:\nginx\html\auth\callback.php
```

Expected: `No syntax errors detected` for both.

- [ ] **Step 4: Mirror into repo and commit**

```powershell
New-Item -ItemType Directory -Force -Path C:\prbf2_1\mods\pr\python\game\docs\nginx-templates\admin | Out-Null
New-Item -ItemType Directory -Force -Path C:\prbf2_1\mods\pr\python\game\docs\nginx-templates\auth | Out-Null
Copy-Item -Force C:\nginx\html\admin\_bootstrap.php C:\prbf2_1\mods\pr\python\game\docs\nginx-templates\admin\_bootstrap.php
Copy-Item -Force C:\nginx\html\auth\callback.php C:\prbf2_1\mods\pr\python\game\docs\nginx-templates\auth\callback.php
cd C:\prbf2_1\mods\pr\python\game
git add docs/nginx-templates/admin/_bootstrap.php docs/nginx-templates/auth/callback.php
git commit -m "Agrega bootstrap del panel admin y retorno post-login."
```

---

### Task 2: Admin layout + CSS

**Files:**
- Create: `C:/nginx/html/admin/_layout.php`
- Modify: `C:/nginx/html/assets/css/site.css` (append `.latam-admin-*`)
- Mirror: `docs/nginx-templates/admin/_layout.php`, `docs/nginx-templates/assets/css/site.css`

**Interfaces:**
- Consumes: `admin_h()`, `auth_display_name()`, `auth_current_discord_id()` (bootstrap already loaded)
- Produces: `admin_render_start(string $activeNav, string $title, string $heading): void`, `admin_render_end(): void`
- `$activeNav` values: `home` | `traffic` | `demos` | `auth`

- [ ] **Step 1: Create `C:/nginx/html/admin/_layout.php`**

```php
<?php
declare(strict_types=1);

/**
 * Opens admin HTML shell (header + sidebar + main start).
 *
 * @param 'home'|'traffic'|'demos'|'auth' $activeNav
 */
function admin_render_start(string $activeNav, string $title, string $heading): void
{
    $cssV = (string) @filemtime(dirname(__DIR__) . '/assets/css/site.css');
    $logoV = (string) @filemtime(dirname(__DIR__) . '/assets/img/latamfiles-logo.png');
    $nav = [
        'home' => ['href' => '/admin/', 'label' => 'Inicio'],
        'traffic' => ['href' => '/admin/traffic.php', 'label' => 'Trafico'],
        'demos' => ['href' => '/admin/demos.php', 'label' => 'Demos'],
        'auth' => ['href' => '/admin/auth-settings.php', 'label' => 'Auth'],
    ];
    echo '<!DOCTYPE html>' . "\n";
    echo '<html lang="es">' . "\n";
    echo '<head>' . "\n";
    echo '  <meta charset="utf-8">' . "\n";
    echo '  <meta name="viewport" content="width=device-width, initial-scale=1">' . "\n";
    echo '  <meta name="robots" content="noindex,nofollow">' . "\n";
    echo '  <title>' . admin_h($title) . '</title>' . "\n";
    echo '  <link rel="icon" href="/assets/img/favicon.png" type="image/png">' . "\n";
    echo '  <link rel="preconnect" href="https://fonts.googleapis.com">' . "\n";
    echo '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>' . "\n";
    echo '  <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&display=swap" rel="stylesheet">' . "\n";
    echo '  <link rel="stylesheet" href="/assets/css/site.css?v=' . admin_h($cssV !== '' ? $cssV : '1') . '">' . "\n";
    echo '</head>' . "\n";
    echo '<body class="latam-admin-body">' . "\n";
    echo '  <header class="latam-site-header" role="banner">' . "\n";
    echo '    <div class="latam-site-header__inner">' . "\n";
    echo '      <a class="latam-site-brand" href="/" aria-label="LATAMFILES - Inicio">' . "\n";
    echo '        <img class="latam-site-brand__logo" src="/assets/img/latamfiles-logo.png?v=' . admin_h($logoV !== '' ? $logoV : '1') . '" alt="LATAMFILES" width="180" height="36">' . "\n";
    echo '      </a>' . "\n";
    echo '      <div class="latam-site-header__auth">' . "\n";
    echo '        <a class="latam-site-header__admins" href="/admin/">ADMINS</a>' . "\n";
    echo '      </div>' . "\n";
    echo '    </div>' . "\n";
    echo '  </header>' . "\n";
    echo '  <div class="latam-admin">' . "\n";
    echo '    <aside class="latam-admin__sidebar" aria-label="Menu admin">' . "\n";
    echo '      <nav class="latam-admin__nav">' . "\n";
    foreach ($nav as $key => $item) {
        $cls = 'latam-admin__nav-link' . ($key === $activeNav ? ' is-active' : '');
        $cur = $key === $activeNav ? ' aria-current="page"' : '';
        echo '        <a class="' . admin_h($cls) . '" href="' . admin_h($item['href']) . '"' . $cur . '>' . admin_h($item['label']) . '</a>' . "\n";
    }
    echo '      </nav>' . "\n";
    echo '    </aside>' . "\n";
    echo '    <main class="latam-admin__main">' . "\n";
    echo '      <h1 class="latam-admin__title">' . admin_h($heading) . '</h1>' . "\n";
}

function admin_render_end(): void
{
    echo '    </main>' . "\n";
    echo '  </div>' . "\n";
    echo '</body>' . "\n";
    echo '</html>';
}
```

- [ ] **Step 2: Append CSS to `C:/nginx/html/assets/css/site.css`**

```css
/* Panel admin LATAMFILES (/admin/) */
.latam-admin-body {
  margin: 0;
}

.latam-admin {
  display: grid;
  grid-template-columns: 14rem minmax(0, 1fr);
  gap: 0;
  max-width: 1120px;
  margin: 0 auto;
  min-height: calc(100vh - 3.5rem);
}

.latam-admin__sidebar {
  border-right: 1px solid var(--latam-border);
  background: rgba(11, 15, 12, 0.72);
  padding: 1.25rem 0.85rem;
}

.latam-admin__nav {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.latam-admin__nav-link {
  display: block;
  padding: 0.55rem 0.75rem;
  border: 1px solid transparent;
  color: var(--latam-text-muted);
  text-decoration: none;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.latam-admin__nav-link:hover,
.latam-admin__nav-link:focus-visible {
  color: #fff;
  border-color: var(--latam-border);
}

.latam-admin__nav-link.is-active {
  color: #fff;
  border-color: var(--latam-accent);
  background: rgba(107, 143, 60, 0.22);
}

.latam-admin__main {
  padding: 1.5rem 1.25rem 2.5rem;
}

.latam-admin__title {
  margin: 0 0 0.75rem;
  font-size: clamp(1.5rem, 3vw, 1.9rem);
  font-weight: 700;
  letter-spacing: 0.04em;
}

.latam-admin__lead {
  margin: 0 0 1.25rem;
  color: var(--latam-text-muted);
  line-height: 1.45;
}

.latam-admin__card {
  max-width: 28rem;
  padding: 1.25rem 1.1rem;
  border: 1px solid var(--latam-border);
  background: rgba(18, 24, 22, 0.92);
}

.latam-admin__card-label {
  margin: 0 0 0.35rem;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--latam-accent);
}

.latam-admin__card-name {
  margin: 0 0 0.35rem;
  font-size: 1.2rem;
  font-weight: 700;
}

.latam-admin__card-meta {
  margin: 0 0 1rem;
  color: var(--latam-text-muted);
  font-size: 0.95rem;
}

.latam-admin__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
}

.latam-admin__btn {
  display: inline-block;
  padding: 0.55rem 0.9rem;
  border: 1px solid var(--latam-border);
  color: var(--latam-text);
  text-decoration: none;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.latam-admin__btn:hover,
.latam-admin__btn:focus-visible {
  border-color: var(--latam-accent);
  color: #fff;
}

.latam-admin__btn--primary {
  border-color: var(--latam-accent);
  background: rgba(107, 143, 60, 0.22);
  color: #fff;
}

.latam-admin__soon {
  margin: 0;
  padding: 1rem 1.1rem;
  border: 1px dashed var(--latam-border);
  color: var(--latam-text-muted);
}

@media (max-width: 720px) {
  .latam-admin {
    grid-template-columns: 1fr;
  }

  .latam-admin__sidebar {
    border-right: none;
    border-bottom: 1px solid var(--latam-border);
  }

  .latam-admin__nav {
    flex-direction: row;
    flex-wrap: wrap;
  }
}
```

- [ ] **Step 3: Syntax check layout**

Run: `php -l C:\nginx\html\admin\_layout.php`  
Expected: `No syntax errors detected`

- [ ] **Step 4: Mirror and commit**

```powershell
Copy-Item -Force C:\nginx\html\admin\_layout.php C:\prbf2_1\mods\pr\python\game\docs\nginx-templates\admin\_layout.php
New-Item -ItemType Directory -Force -Path C:\prbf2_1\mods\pr\python\game\docs\nginx-templates\assets\css | Out-Null
Copy-Item -Force C:\nginx\html\assets\css\site.css C:\prbf2_1\mods\pr\python\game\docs\nginx-templates\assets\css\site.css
cd C:\prbf2_1\mods\pr\python\game
git add docs/nginx-templates/admin/_layout.php docs/nginx-templates/assets/css/site.css
git commit -m "Agrega layout y estilos del panel admin."
```

---

### Task 3: Admin pages (home + placeholders)

**Files:**
- Create: `C:/nginx/html/admin/index.php`
- Create: `C:/nginx/html/admin/traffic.php`
- Create: `C:/nginx/html/admin/demos.php`
- Create: `C:/nginx/html/admin/auth-settings.php`
- Mirror under `docs/nginx-templates/admin/`

**Interfaces:**
- Consumes: `_bootstrap.php`, `_layout.php` (`admin_render_start`, `admin_render_end`, `admin_h`, `auth_display_name`, `auth_current_discord_id`)

- [ ] **Step 1: Create home `index.php`**

```php
<?php
declare(strict_types=1);
require_once __DIR__ . '/_bootstrap.php';
require_once __DIR__ . '/_layout.php';

$name = auth_display_name() ?? 'Staff';
$id = (string) auth_current_discord_id();

admin_render_start('home', 'Panel de administracion | LATAMFILES', 'Panel de administracion');
?>
<p class="latam-admin__lead">Aqui van a aparecer los modulos de configuracion (trafico, demos, auth) a medida que los activemos.</p>
<section class="latam-admin__card" aria-label="Sesion actual">
  <p class="latam-admin__card-label">Staff</p>
  <p class="latam-admin__card-name"><?= admin_h($name) ?></p>
  <p class="latam-admin__card-meta">Discord ID: <?= admin_h($id) ?></p>
  <div class="latam-admin__actions">
    <a class="latam-admin__btn latam-admin__btn--primary" href="/pr.php">Volver al sitio</a>
    <a class="latam-admin__btn" href="/auth/logout.php">Cerrar sesion</a>
  </div>
</section>
<?php
admin_render_end();
```

- [ ] **Step 2: Create placeholder pages**

`traffic.php`:

```php
<?php
declare(strict_types=1);
require_once __DIR__ . '/_bootstrap.php';
require_once __DIR__ . '/_layout.php';
admin_render_start('traffic', 'Trafico | Admin LATAMFILES', 'Trafico');
echo '<p class="latam-admin__soon">Proximamente: limites de trafico y descargas en Nginx.</p>';
admin_render_end();
```

`demos.php`:

```php
<?php
declare(strict_types=1);
require_once __DIR__ . '/_bootstrap.php';
require_once __DIR__ . '/_layout.php';
admin_render_start('demos', 'Demos | Admin LATAMFILES', 'Demos');
echo '<p class="latam-admin__soon">Proximamente: opciones del listado de demos 2D/3D.</p>';
admin_render_end();
```

`auth-settings.php`:

```php
<?php
declare(strict_types=1);
require_once __DIR__ . '/_bootstrap.php';
require_once __DIR__ . '/_layout.php';
admin_render_start('auth', 'Auth | Admin LATAMFILES', 'Auth');
echo '<p class="latam-admin__soon">Proximamente: mensajes y opciones de acceso Discord.</p>';
admin_render_end();
```

- [ ] **Step 3: Lint all admin PHP**

```powershell
php -l C:\nginx\html\admin\index.php
php -l C:\nginx\html\admin\traffic.php
php -l C:\nginx\html\admin\demos.php
php -l C:\nginx\html\admin\auth-settings.php
```

Expected: no syntax errors on all four.

- [ ] **Step 4: Mirror and commit**

```powershell
Copy-Item -Force C:\nginx\html\admin\*.php C:\prbf2_1\mods\pr\python\game\docs\nginx-templates\admin\
cd C:\prbf2_1\mods\pr\python\game
git add docs/nginx-templates/admin/
git commit -m "Agrega paginas del panel admin (home y proximamente)."
```

---

### Task 4: Nginx location for `/admin/`

**Files:**
- Modify: `C:/nginx/conf/latamsquad-locations.conf`
- Mirror: `docs/nginx-templates/latamsquad-locations.conf`

**Interfaces:**
- Produces: FastCGI for `/admin/` index and `/admin/*.php`

- [ ] **Step 1: Insert locations before the `location = /auth/gate.php` block**

```nginx
    # Panel admin LATAMFILES (solo staff; gate en PHP)
    location = /admin {
        return 301 /admin/;
    }
    location = /admin/ {
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME C:/nginx/html/admin/index.php;
        fastcgi_param HTTPS $https if_not_empty;
        fastcgi_pass 127.0.0.1:9000;
    }
    location ~ ^/admin/(.+\.php)$ {
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME C:/nginx/html/admin/$1;
        fastcgi_param HTTPS $https if_not_empty;
        fastcgi_pass 127.0.0.1:9000;
    }
```

Write conf UTF-8 **without BOM**.

- [ ] **Step 2: Test and reload Nginx**

```powershell
cd C:\nginx
.\nginx.exe -t
.\nginx.exe -s reload
```

Expected: `syntax is ok` / `test is successful`, then reload succeeds (warn about duplicate `prdemo` MIME is pre-existing OK).

- [ ] **Step 3: Smoke HTTP (logged-out)**

```powershell
curl.exe -skI "https://127.0.0.1/admin/" -H "Host: latamsquad.dev"
```

Expected: `302` with `Location:` containing `/auth/discord.php` (or absolute Discord URL only after discord.php - first hop should be discord.php).

- [ ] **Step 4: Mirror and commit**

```powershell
Copy-Item -Force C:\nginx\conf\latamsquad-locations.conf C:\prbf2_1\mods\pr\python\game\docs\nginx-templates\latamsquad-locations.conf
cd C:\prbf2_1\mods\pr\python\game
git add docs/nginx-templates/latamsquad-locations.conf
git commit -m "Configura Nginx para servir /admin/."
```

---

### Task 5: Point ADMINS links to `/admin/`

**Files:**
- Modify: `C:/nginx/html/pr.php` (ADMINS href)
- Modify: `C:/nginx/html/index.php` (ADMINS href)
- Modify: `C:/nginx/html/assets/autoindex-enhance.js` (ADMINS href + cache bust in conf)
- Modify: `C:/nginx/conf/latamsquad-locations.conf` (bump `autoindex-enhance.js?v=...`)
- Mirror under `docs/nginx-templates/`

- [ ] **Step 1: Change ADMINS hrefs**

In `pr.php` and `index.php`, when showing the ADMINS link (guest), use:

```php
<a class="latam-site-header__admins" href="/admin/">ADMINS</a>
```

When logged in on `pr.php`/`index.php`, prefer linking the name or adding a panel link to `/admin/` (keep Salir). Minimal change for logged-in header:

```php
<span><?= htmlspecialchars((string) $name, ENT_QUOTES, 'UTF-8') ?></span>
· <a href="/admin/">Panel</a>
· <a href="/auth/logout.php">Salir</a>
```

- [ ] **Step 2: Autoindex JS**

In `autoindex-enhance.js` `injectHeader()`, change:

```javascript
'<a class="latam-site-header__admins" href="/admin/">ADMINS</a>' +
```

Bump all `autoindex-enhance.js?v=` query strings in `latamsquad-locations.conf` to a new value (e.g. `20260724w`). Reload Nginx after conf change.

- [ ] **Step 3: Smoke**

```powershell
curl.exe -sk "https://127.0.0.1/pr.php" -H "Host: latamsquad.dev" | Select-String "href=\"/admin/\""
curl.exe -skI "https://127.0.0.1/admin/traffic.php" -H "Host: latamsquad.dev" | Select-Object -First 8
```

Expected: `pr.php` contains `/admin/`; `traffic.php` without session returns `302` to Discord login.

- [ ] **Step 4: Mirror and commit**

```powershell
Copy-Item -Force C:\nginx\html\pr.php C:\prbf2_1\mods\pr\python\game\docs\nginx-templates\pr.php
Copy-Item -Force C:\nginx\html\index.php C:\prbf2_1\mods\pr\python\game\docs\nginx-templates\index.php
Copy-Item -Force C:\nginx\html\assets\autoindex-enhance.js C:\prbf2_1\mods\pr\python\game\docs\nginx-templates\assets\autoindex-enhance.js
Copy-Item -Force C:\nginx\conf\latamsquad-locations.conf C:\prbf2_1\mods\pr\python\game\docs\nginx-templates\latamsquad-locations.conf
cd C:\prbf2_1\mods\pr\python\game
git add docs/nginx-templates/
git commit -m "Apunta el boton ADMINS al panel /admin/."
```

---

### Task 6: Manual staff verification checklist

**Files:** none (verification only)

- [ ] **Step 1: Logged-out**
  - Open `/admin/` → redirects to Discord OAuth
- [ ] **Step 2: Non-staff Discord** (if available)
  - Completes OAuth → 403 notice page (no session)
- [ ] **Step 3: Staff Discord**
  - Lands on `/admin/` (via `auth_return`) with sidebar + user card
  - Open Trafico / Demos / Auth → "Proximamente"
  - Cerrar sesion works; ADMINS from demos list goes to `/admin/`
- [ ] **Step 4: Confirm no settings UI**
  - No forms that claim to save Nginx/demos/auth settings

If any step fails, fix in the owning task file and re-run smoke before closing.

---

## Spec coverage (self-review)

| Spec requirement | Task |
|------------------|------|
| `/admin/` staff-only | 1, 3, 4 |
| Reuse Discord OAuth + is_staff | 1 |
| Home + sidebar placeholders | 2, 3 |
| ADMINS → `/admin/` | 5 |
| LATAMFILES CSS | 2 |
| noindex | 1, 2 |
| Nginx PHP location | 4 |
| No settings persistence v1 | 3, 6 |
| Return path after login | 1 |

Placeholder scan: no TBD/TODO left in steps.  
Naming: `admin_render_start` / `admin_render_end` / `admin_h` / `auth_return` consistent across tasks.
