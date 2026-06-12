#!/bin/bash
# === MO APP CHEN LOGO (macOS) — nhan dup de mo ===
cd "$(dirname "$0")"

PY=""
for c in python3 python; do
  if command -v $c >/dev/null 2>&1; then PY=$c; break; fi
done
if [ -z "$PY" ]; then
  echo "❌ Chua co Python 3. Cai tai: https://www.python.org/downloads/"
  read -p "Nhan Enter de thoat..."; exit 1
fi

# Lan dau: tu cai thu vien (can mang)
$PY -c "import PIL" >/dev/null 2>&1 || { echo "⏳ Dang cai Pillow..."; $PY -m pip install --user --quiet Pillow || $PY -m pip install --quiet Pillow; }
$PY -c "import tkinterdnd2" >/dev/null 2>&1 || { echo "⏳ Dang cai keo-tha (tkinterdnd2)..."; $PY -m pip install --user --quiet tkinterdnd2 || $PY -m pip install --quiet tkinterdnd2; }

$PY app.py
