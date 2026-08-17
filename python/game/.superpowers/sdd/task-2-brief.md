### Task 2: Nginx locations for `/pr/logs/` + deny cache

**Files:**
- Modify: `C:/nginx/conf/latamsquad-locations.conf` (insert before tracker block or after extras)
- Mirror: `docs/nginx-templates/latamsquad-locations.conf`

**Interfaces:**
- Consumes: files from Task 1 at `html/pr/logs/`
- Produces: public PHP app at `/pr/logs/`; HTTP 403/404 for `/pr/logs/public/logs/`

- [ ] **Step 1: Add locations (place BEFORE the generic tracker PHP regex is fine; deny must use `^~`)**

Insert into `latamsquad-locations.conf`:

```nginx
    # PR LOG Viewer (public UI; cache dir not web-readable)
    location ^~ /pr/logs/public/logs/ {
        deny all;
        return 404;
    }

    location = /pr/logs {
        return 301 /pr/logs/;
    }

    location /pr/logs/ {
        root html;
        index index.html index.php;
        try_files $uri $uri/ /pr/logs/index.html;
    }

    location ~ ^/pr/logs/(.+\.php)$ {
        root html;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root/pr/logs/$1;
        fastcgi_param HTTPS $https if_not_empty;
        fastcgi_pass 127.0.0.1:9000;
    }
```

Do **not** add `auth_request` here. Do **not** modify `/pr/admins/logs/sv1/`.

- [ ] **Step 2: Test and reload Nginx**

```powershell
C:/nginx/nginx.exe -t
# Expected: syntax is ok
C:/nginx/nginx.exe -s reload
```

- [ ] **Step 3: Smoke URL routing (no auth)**

```powershell
curl.exe -skI "https://127.0.0.1/pr/logs/" -H "Host: latamsquad.dev"
# Expect: 200 (or 302 to public/index.php then 200 on follow)
curl.exe -skI "https://127.0.0.1/pr/logs/public/index.php" -H "Host: latamsquad.dev"
# Expect: 200
curl.exe -skI "https://127.0.0.1/pr/logs/public/logs/" -H "Host: latamsquad.dev"
# Expect: 403 or 404
```

- [ ] **Step 4: Mirror conf into repo**

Copy updated `latamsquad-locations.conf` to `docs/nginx-templates/latamsquad-locations.conf`.

---

