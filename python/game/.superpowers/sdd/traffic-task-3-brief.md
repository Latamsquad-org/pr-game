### Task 3: Wire Nginx includes + deny data + seed confs

**Files:**
- Modify: `C:/nginx/conf/nginx.conf`
- Modify: `C:/nginx/conf/latamsquad-locations.conf`
- Create initial: `C:/nginx/conf/latam-traffic-zones.conf`, `latam-traffic-limits.conf` (via PHP defaults apply or hand seed)
- Mirror conf templates

- [ ] **Step 1: Add zones include inside `http { }` in `nginx.conf`**

After the `types { ... }` block (before `include latamsquad.conf`):

```nginx
    include latam-traffic-zones.conf;
```

- [ ] **Step 2: Seed zone/limit files with defaults (enabled)**

Run once:

```powershell
php -r "require 'C:/nginx/html/admin/lib/traffic_settings.php'; file_put_contents('C:/nginx/conf/latam-traffic-zones.conf', traffic_generate_zones_conf(traffic_settings_defaults())); file_put_contents('C:/nginx/conf/latam-traffic-limits.conf', traffic_generate_limits_conf(traffic_settings_defaults()));"
```

- [ ] **Step 3: Add `include latam-traffic-limits.conf;` to each demos2d/demos3d location**

Inside every `location /pr/demos2d/...` and `/pr/demos3d/...` block, after `autoindex on;`:

```nginx
        include latam-traffic-limits.conf;
```

(8 locations: demos2d root+sv2-4, demos3d sv1-4)

- [ ] **Step 4: Deny `/admin/data/`**

Add near admin locations:

```nginx
    location ^~ /admin/data/ {
        deny all;
        return 404;
    }
```

- [ ] **Step 5: nginx -t && reload**

```powershell
cd C:\nginx; .\nginx.exe -t; if ($LASTEXITCODE -eq 0) { .\nginx.exe -s reload }
```

Expected: test successful.

- [ ] **Step 6: Mirror + commit**

Copy `nginx.conf`, `latamsquad-locations.conf`, both generated confs (as samples) into `docs/nginx-templates/`, commit:

```
git commit -m "Conecta includes de limites de trafico en Nginx."
```

---

