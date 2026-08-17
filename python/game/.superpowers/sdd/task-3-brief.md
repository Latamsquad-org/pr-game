### Task 3: Hub link on `/pr.php`

**Files:**
- Modify: `C:/nginx/html/pr.php` (`.pr-links` list)
- Mirror: `docs/nginx-templates/pr.php`

**Interfaces:**
- Consumes: working `/pr/logs/` from Task 2
- Produces: discoverable hub entry

- [ ] **Step 1: Add list item**

In the `<ul class="pr-links">` block, add:

```html
      <li><a href="/pr/logs/">Visor de logs</a></li>
```

Keep ASCII (`Visor de logs`). Suggested order: after Extras or before Extras â€” either is fine; prefer after tracker/demos, before or after Extras consistently in live + mirror.

- [ ] **Step 2: Verify hub HTML**

```powershell
curl.exe -sk "https://127.0.0.1/pr.php" -H "Host: latamsquad.dev" | findstr /C:"/pr/logs/"
# Expect: href="/pr/logs/"
```

- [ ] **Step 3: Mirror `pr.php` to `docs/nginx-templates/pr.php`**

---

