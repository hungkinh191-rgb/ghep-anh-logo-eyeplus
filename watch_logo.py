#!/usr/bin/env python3
"""
THEO DÕI THƯ MỤC — tự động chèn logo khi có ảnh mới.

Bật một lần, sau đó cứ thả ảnh vào input/ là tự động chèn logo,
kết quả xuất ra output/. Nhấn Ctrl+C để dừng.

Cách chạy:
    python3 watch_logo.py
Hoặc nhấn đúp file: start_watch.command

Cấu hình logo (vị trí, cỡ, độ mờ) lấy chung từ add_logo.py
"""

import time
from pathlib import Path
from PIL import Image

# Dùng chung cấu hình & hàm xử lý từ add_logo.py
from add_logo import (
    LOGO_PATH, INPUT_DIR, OUTPUT_DIR, POSITION, LOGO_RATIO,
    OPACITY, MARGIN, VALID_EXT, apply_opacity, position_xy,
)

CHECK_EVERY = 2  # giây — chu kỳ quét thư mục


def process_one(p: Path, logo_master: Image.Image, out_dir: Path) -> bool:
    img = Image.open(p).convert("RGBA")
    iw, ih = img.size

    lw = max(1, int(iw * LOGO_RATIO))
    lh = max(1, int(logo_master.height * lw / logo_master.width))
    logo = apply_opacity(logo_master.resize((lw, lh), Image.LANCZOS), OPACITY)

    margin_px = int(iw * MARGIN)
    x, y = position_xy(POSITION, iw, ih, lw, lh, margin_px)
    img.paste(logo, (x, y), logo)

    out_path = out_dir / p.name
    if p.suffix.lower() in {".jpg", ".jpeg"}:
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.getchannel("A"))
        bg.save(out_path, quality=95)
    else:
        img.save(out_path)
    return True


def is_stable(p: Path) -> bool:
    """Đảm bảo file copy xong (kích thước không đổi giữa 2 lần đọc)."""
    try:
        s1 = p.stat().st_size
        time.sleep(0.4)
        return s1 == p.stat().st_size and s1 > 0
    except OSError:
        return False


def main():
    base = Path(__file__).parent
    logo_file = base / LOGO_PATH
    in_dir = base / INPUT_DIR
    out_dir = base / OUTPUT_DIR
    in_dir.mkdir(exist_ok=True)
    out_dir.mkdir(exist_ok=True)

    if not logo_file.exists():
        print(f"❌ Chưa có logo: {logo_file}\n   → Bỏ file logo.png vào thư mục rồi chạy lại.")
        return

    logo_master = Image.open(logo_file).convert("RGBA")

    print("👀 ĐANG THEO DÕI thư mục input/ ...")
    print(f"   Vị trí={POSITION} | Cỡ={int(LOGO_RATIO*100)}% | Độ mờ={OPACITY}")
    print("   → Thả ảnh vào input/ để tự chèn logo. Nhấn Ctrl+C để dừng.\n")

    done = set()
    # Bỏ qua ảnh đã có sẵn trong output/ (đã xử lý trước đó)
    for f in out_dir.glob("*"):
        done.add(f.name)

    try:
        while True:
            for p in sorted(in_dir.glob("*")):
                if p.suffix.lower() not in VALID_EXT or p.name in done:
                    continue
                if not is_stable(p):
                    continue  # đợi vòng sau khi file copy xong
                try:
                    process_one(p, logo_master, out_dir)
                    done.add(p.name)
                    print(f"  ✅ {p.name}  →  output/{p.name}")
                except Exception as e:
                    print(f"  ❌ {p.name}: {e}")
            time.sleep(CHECK_EVERY)
    except KeyboardInterrupt:
        print("\n🛑 Đã dừng theo dõi.")


if __name__ == "__main__":
    main()
