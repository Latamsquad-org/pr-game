# Task 3 Report: Hub link on /pr.php

## Status
Complete.

## Commit
226de34fc682820cae64f702b003c63a59336fd2 - hub: link Visor de logs to /pr/logs/

## Changes
- Live: C:/nginx/html/pr.php - added Visor de logs before Extras in `.pr-links`.
- Mirror: docs/nginx-templates/pr.php - same link; UTF-8 BOM removed (Set-Content had broken PHP strict_types).

## Test
`curl.exe -sk "https://127.0.0.1/pr.php" -H "Host: latamsquad.dev" | findstr /C:"/pr/logs/"` -> `href="/pr/logs/"` OK after BOM fix on live file.

## Concerns
Initial edit used UTF-8 BOM on live pr.php (HTTP 500); fixed in place, not in game repo. Mirror amended without BOM.

## Report path
C:/prbf2_1/mods/pr/python/game/.superpowers/sdd/task-3-report.md
