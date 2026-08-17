# Task 3 review package
Base: 2ae9d0c49e56add06fb982796fc902c04c59a43b
Head: 226de34fc682820cae64f702b003c63a59336fd2

## Commits
226de34 hub: link Visor de logs to /pr/logs/

## Stat
 docs/nginx-templates/pr.php | 7 ++++---  1 file changed, 4 insertions(+), 3 deletions(-)

## Diff
```diff
diff --git a/docs/nginx-templates/pr.php b/docs/nginx-templates/pr.php index b2970a6..f24db59 100644 --- a/docs/nginx-templates/pr.php +++ b/docs/nginx-templates/pr.php @@ -68,30 +68,31 @@ $jsonLdEncoded = json_encode(            alt="LATAMFILES - logo LATAMSQUAD"            width="625"            height="91"          >        </a>        <div class="latam-site-header__auth">          <?php if ($id === null): ?>            <a class="latam-site-header__admins" href="/admin/">ADMINS</a>          <?php else: ?>            <span><?= htmlspecialchars((string) $name, ENT_QUOTES, 'UTF-8') ?></span> -          ┬╖ <a href="/admin/">Panel</a> -          ┬╖ <a href="/auth/logout.php">Salir</a> +          ├é┬╖ <a href="/admin/">Panel</a> +          ├é┬╖ <a href="/auth/logout.php">Salir</a>          <?php endif; ?>        </div>      </div>    </header>      <main class="latam-main"> -    <a class="pr-back" href="/">ΓåÉ Juegos</a> +    <a class="pr-back" href="/">├óΓÇá┬É Juegos</a>      <h1>Project Reality - Archivos</h1>      <p>Tracker, demos y archivos del servidor Project Reality de LATAMSQUAD.</p>      <ul class="pr-links">        <li><a href="/pr/tracker/?srv=1">Listado de Partidas</a></li>        <li><a href="/pr/demos2d/">.PRdemos (2D)</a></li>        <li><a href="/pr/demos3d/sv1/">.BF2demos (3D)</a></li> +      <li><a href="/pr/logs/">Visor de logs</a></li>        <li><a href="/pr/extras/">Extras</a></li>      </ul>    </main>  </body>  </html>
```