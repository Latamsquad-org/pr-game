### Task 2: Mirror + commit

**Files:**
- Mirror: `docs/nginx-templates/admin/_layout.php` from live
- Mirror: `docs/nginx-templates/assets/css/site.css` from live (or patch same CSS hunk if live CSS has unrelated drift â€” copy only if intentional; prefer copy live â†’ mirror for these two files when they are the source of truth)
- Include: `docs/superpowers/specs/2026-07-25-latamfiles-admin-nav-shortcuts-design.md`
- Include: `docs/superpowers/plans/2026-07-25-latamfiles-admin-nav-shortcuts.md` (this plan)

**Interfaces:**
- Consumes: Task 1 live files
- Produces: repo mirror in sync

- [ ] **Step 1: Copy mirrors**

```powershell
Copy-Item C:/nginx/html/admin/_layout.php C:/prbf2_1/mods/pr/python/game/docs/nginx-templates/admin/_layout.php -Force
Copy-Item C:/nginx/html/assets/css/site.css C:/prbf2_1/mods/pr/python/game/docs/nginx-templates/assets/css/site.css -Force
```

- [ ] **Step 2: Diff sanity**

```powershell
Select-String -Path C:/prbf2_1/mods/pr/python/game/docs/nginx-templates/admin/_layout.php -Pattern "Atajos|Visor de logs"
Select-String -Path C:/prbf2_1/mods/pr/python/game/docs/nginx-templates/assets/css/site.css -Pattern "latam-admin__nav-label"
```

- [ ] **Step 3: Commit (only these paths)**

```bash
git add docs/nginx-templates/admin/_layout.php docs/nginx-templates/assets/css/site.css docs/superpowers/specs/2026-07-25-latamfiles-admin-nav-shortcuts-design.md docs/superpowers/plans/2026-07-25-latamfiles-admin-nav-shortcuts.md
git commit -m "$(cat <<'EOF'
Add admin sidebar Atajos to logs, tracker, and demos.

Group Config vs shortcuts so Demos settings stay distinct from listing links.
EOF
)"
```

---

