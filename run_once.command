#!/bin/bash
# === CHAY 1 LAN CHO CA LOAT ANH (macOS) ===
# Nhan dup de chen logo cho tat ca anh dang co trong input/.
cd "$(dirname "$0")"

PY=""
for c in python3 python; do
  if command -v $c >/dev/null 2>&1; then PY=$c; break; fi
done
if [ -z "$PY" ]; then
  echo "❌ Chua co Python 3. Cai tai: https://www.python.org/downloads/"
  read -p "Nhan Enter de thoat..."; exit 1
fi

if ! $PY -c "import PIL" >/dev/null 2>&1; then
  echo "⏳ Lan dau chay — dang cai thu vien xu ly anh (can mang)..."
  $PY -m pip install --user --quiet Pillow || $PY -m pip install --quiet Pillow
fi

$PY add_logo.py
read -p "Xong. Nhan Enter de dong cua so..."
