#!/usr/bin/env bash
set -e

# wait for Postgres
if [ -n "$DATABASE_URL" ]; then
  echo "Waiting for Postgres at $(echo $DATABASE_URL | sed -E 's|.*://([^@]+@)?([^:/]+):?([0-9]*)/.*|\2 \3|') ..."
fi

until python - <<'PY'
import os, time
from urllib.parse import urlparse
url=os.environ.get("DATABASE_URL","")
if not url:
    raise SystemExit(0)
p=urlparse(url)
import socket
s=socket.socket()
try:
    s.settimeout(1.0)
    s.connect((p.hostname, int(p.port or 5432)))
    print("DB reachable")
except Exception as e:
    print("DB not ready:", e); raise SystemExit(1)
finally:
    s.close()
PY
do
  sleep 1
done

python manage.py migrate --noinput
python manage.py collectstatic --noinput || true

exec "$@"
