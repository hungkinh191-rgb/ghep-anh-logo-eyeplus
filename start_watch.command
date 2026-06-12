#!/bin/bash
# === TU DONG THEO DOI THU MUC (macOS) ===
# Nhan dup file nay de bat. Lan dau se tu cai thu vien can thiet.
cd "$(dirname "$0")"

# Tim Python 3
PY=""
for c in python3 python; do
  if command -v $c >/dev/null 2>&1; then PY=$c; break; fi
done
if [ -z "$PY" ]; then
  echo "❌ Chua co Python 3. Cai tai: https://www.python.org/downloads/"
  read -p "Nhan Enter de thoat..."; exit 1
fi

# Cai Pillow neu chua co
if ! $PY -c "import PIL" >/dev/null 2>&1; then
  echo "⏳ Lan dau chay — dang cai thu vien xu ly anh (can mang)..."
  $PY -m pip install --user --quiet Pillow || $PY -m pip install --quiet Pillow
fi

$PY watch_logo.py
read -p "Da dung. Nhan Enter de dong cua so..."
