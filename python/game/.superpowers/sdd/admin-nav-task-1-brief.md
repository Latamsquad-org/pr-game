### Task 1: Sidebar sections + CSS (live) + smoke

**Files:**
- Modify: `C:/nginx/html/admin/_layout.php`
- Modify: `C:/nginx/html/assets/css/site.css` (after `.latam-admin__nav` block ~488)

**Interfaces:**
- Consumes: `admin_render_start(string $activeNav, string $title, string $heading): void` signature unchanged
- Produces: HTML with Config + Atajos; CSS classes `latam-admin__nav-section`, `latam-admin__nav-label`

- [ ] **Step 1: Replace nav rendering in `_layout.php`**

Keep the `$nav` config array for active-state Config links. After opening `<nav class="latam-admin__nav">`, render:

```php
    $shortcuts = [
        ['href' => '/pr/logs/', 'label' => 'Visor de logs'],
        ['href' => '/pr/admins/logs/sv1/', 'label' => 'Logs crudos'],
        ['href' => '/pr/tracker/?srv=1', 'label' => 'Tracker'],
        ['href' => '/pr/demos2d/', 'label' => 'Demos 2D'],
        ['href' => '/pr/demos3d/sv1/', 'label' => 'Demos 3D'],
    ];
```

Render structure (ASCII labels):

```php
    echo '      <nav class="latam-admin__nav">' . "\n";
    echo '        <div class="latam-admin__nav-section">' . "\n";
    echo '          <p class="latam-admin__nav-label">Config</p>' . "\n";
    foreach ($nav as $key => $item) {
        $cls = 'latam-admin__nav-link' . ($key === $activeNav ? ' is-active' : '');
        $cur = $key === $activeNav ? ' aria-current="page"' : '';
        echo '          <a class="' . admin_h($cls) . '" href="' . admin_h($item['href']) . '"' . $cur . '>' . admin_h($item['label']) . '</a>' . "\n";
    }
    echo '        </div>' . "\n";
    echo '        <div class="latam-admin__nav-section">' . "\n";
    echo '          <p class="latam-admin__nav-label">Atajos</p>' . "\n";
    foreach ($shortcuts as $item) {
        echo '          <a class="latam-admin__nav-link" href="' . admin_h($item['href']) . '">' . admin_h($item['label']) . '</a>' . "\n";
    }
    echo '        </div>' . "\n";
    echo '      </nav>' . "\n";
```

Do not add `is-active` on shortcuts. Keep `@param 'home'|'traffic'|'demos'|'auth' $activeNav`.

- [ ] **Step 2: Add CSS after `.latam-admin__nav { ... }`**

```css
.latam-admin__nav-section {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.latam-admin__nav-section + .latam-admin__nav-section {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--latam-border);
}

.latam-admin__nav-label {
  margin: 0 0 0.15rem;
  padding: 0 0.75rem;
  color: var(--latam-text-muted);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
```

Optionally set `.latam-admin__nav { gap: 0; }` so spacing comes from sections (or leave gap and rely on section margin â€” prefer `gap: 0` on nav when using sections).

- [ ] **Step 3: PHP lint**

Run: `php -l C:/nginx/html/admin/_layout.php`  
Expected: No syntax errors

- [ ] **Step 4: Smoke (staff session cookie if required; else grep HTML after login path)**

If unauthenticated redirects to Discord, use an existing staff session or verify via reading rendered structure offline. Prefer:

```powershell
# If you have staff cookie jar:
curl.exe -sk "https://127.0.0.1/admin/" -H "Host: latamsquad.dev" -b cookies.txt | findstr /C:"Config" /C:"Atajos" /C:"/pr/logs/" /C:"/pr/admins/logs/sv1/" /C:"/pr/tracker/?srv=1" /C:"/pr/demos2d/" /C:"/pr/demos3d/sv1/"
```

Also open Trafico and confirm `is-active` still only on Trafico Config link.

Alternatively without cookie: `php -r` include bootstrap is heavy; minimum bar is file content asserts:

```powershell
Select-String -Path C:/nginx/html/admin/_layout.php -Pattern "Atajos|/pr/logs/|Demos 2D|Demos 3D|Logs crudos"
```

- [ ] **Step 5: Commit not required until Task 2 mirrors** (live-only until mirror synced)

---

