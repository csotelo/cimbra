#!/bin/bash
set -e

# Auto-install requirements from Vigilo modules
for req in /app/apps/*/requirements.txt; do
    if [ -f "$req" ]; then
        echo "[entrypoint] Installing $req"
        pip install --quiet --cache-dir /pip-cache -r "$req"
    fi
done

echo "[entrypoint] Running migrations..."
python manage.py migrate --noinput

echo "[entrypoint] Starting server..."
exec "$@"
