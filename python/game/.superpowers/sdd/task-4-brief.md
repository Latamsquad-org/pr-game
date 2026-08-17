### Task 4: Repo mirror of vendor + end-to-end smoke

**Files:**
- Create: `docs/nginx-templates/pr/logs/**` (mirror of live vendor + LATAM config + VENDOR.md; may omit bulky identical upstream blobs if policy prefers â€” **default: full mirror of tree used in production**, exclude `public/logs/*` cache contents except empty `index.html`)
- Ensure `.gitignore` does not need to ignore cache: add `docs/nginx-templates/pr/logs/public/logs/*` keep `!docs/nginx-templates/pr/logs/public/logs/index.html` if committing cache empties; live cache stays on server only.

**Interfaces:**
- Consumes: Tasks 1-3 live state
- Produces: reproducible mirror + smoke evidence

- [ ] **Step 1: Sync vendor mirror**

```powershell
$src = "C:/nginx/html/pr/logs"
$dst = "C:/prbf2_1/mods/pr/python/game/docs/nginx-templates/pr/logs"
New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
robocopy $src $dst /E /XD logs
# Recreate empty logs placeholder
New-Item -ItemType Directory -Force -Path "$dst/public/logs" | Out-Null
if (Test-Path "$src/public/logs/index.html") {
  Copy-Item "$src/public/logs/index.html" "$dst/public/logs/index.html"
}
```

(`/XD logs` skips nested `public/logs` content during robocopy from `pr/logs` â€” if robocopy excludes wrong `logs`, copy manually excluding only `public/logs/*.txt` cache files.)

- [ ] **Step 2: Refresh cache via download.php (SV1) then query API**

```powershell
curl.exe -sk "https://127.0.0.1/pr/logs/public/download.php?server_id=1" -H "Host: latamsquad.dev"
# Expect JSON with success true (or clear error if source missing)
curl.exe -sk "https://127.0.0.1/pr/logs/public/get_timestamp.php?server_id=1" -H "Host: latamsquad.dev"
curl.exe -sk "https://127.0.0.1/pr/logs/public/get_log.php?server_id=1,&command=ALL" -H "Host: latamsquad.dev" -o "$env:TEMP/prlog_sv1.json"
# Spot SV2-SV4 download + timestamp similarly
```

- [ ] **Step 3: Prove cache is not HTTP-readable after refresh**

```powershell
# After a successful download, latam_sv1.txt should exist on disk:
Test-Path "C:/nginx/html/pr/logs/public/logs/latam_sv1.txt"
curl.exe -skI "https://127.0.0.1/pr/logs/public/logs/latam_sv1.txt" -H "Host: latamsquad.dev"
# Expect: 403 or 404 (NOT 200)
```

- [ ] **Step 4: Verify hide_ips on player API (if cdhash data exists)**

```powershell
curl.exe -sk "https://127.0.0.1/pr/logs/public/download.php?server_id=1" -H "Host: latamsquad.dev"
curl.exe -sk "https://127.0.0.1/pr/logs/public/get_player.php?server_id=1,&search=&group_by=nick&hide=" -H "Host: latamsquad.dev" -o "$env:TEMP/prlog_players.json"
# Inspect: IP fields should look like a.b.0.0 / masked per upstream, not full client IPs
```

If upstream leaves full IPs inside admin log `content`/`mess` strings, document as known limitation in smoke notes; only patch if trivial (YAGNI unless smoke shows clear unmasked IP columns in player view with `hide_ips` true â€” then fix get_player path).

- [ ] **Step 5: Session endpoint must not bounce public users**

```powershell
curl.exe -sk "https://127.0.0.1/pr/logs/public/get_session.php" -H "Host: latamsquad.dev"
# Expect JSON status true when require_login is false
```

- [ ] **Step 6: Staff autoindex still gated**

```powershell
curl.exe -skI "https://127.0.0.1/pr/admins/logs/sv1/" -H "Host: latamsquad.dev"
# Expect: 302 to Discord login (or 401 handled by error_page), not a public 200 listing
```

- [ ] **Step 7: Commit mirrors + spec already present**

```bash
git add docs/nginx-templates/pr/logs docs/nginx-templates/pr.php docs/nginx-templates/latamsquad-locations.conf docs/superpowers/specs/2026-07-25-latamfiles-pr-log-viewer-design.md docs/superpowers/plans/2026-07-25-latamfiles-pr-log-viewer.md
git commit -m "$(cat <<'EOF'
Add public PR LOG Viewer at /pr/logs for LATAMFILES.

Vendor gerbesf/PR-LOG-Viewer with local SV1-SV4 paths, hide IPs, deny cache HTTP, and hub link.
EOF
)"
```

(On Windows PowerShell without HEREDOC, use an equivalent `git commit -m` multi-line message.)

---

