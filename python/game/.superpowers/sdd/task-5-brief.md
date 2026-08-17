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

