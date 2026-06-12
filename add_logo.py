#!/usr/bin/env python3
"""
Chèn logo (watermark) hàng loạt cho ảnh.

Cách dùng:
    1. Bỏ logo của bạn vào thư mục này, đặt tên: logo.png (nên là PNG nền trong suốt)
    2. Bỏ tất cả ảnh cần chèn vào thư mục:  input/
    3. Chạy:  python3 add_logo.py
    4. Ảnh đã chèn logo nằm trong:  output/

Tuỳ chỉnh nhanh ở phần CẤU HÌNH bên dưới.
"""

from pathlib import Path
from PIL import Image

# ============== CẤU HÌNH ==============
LOGO_PATH   = "logo.png"     # file logo
INPUT_DIR   = "input"        # thư mục ảnh gốc
OUTPUT_DIR  = "output"       # thư mục ảnh kết quả

POSITION    = "top-left"     # top-left | top-right | bottom-left | bottom-right | center
LOGO_RATIO  = 0.10           # logo rộng = 10% chiều rộng ảnh
OPACITY     = 1.0            # 1.0 = đậm rõ nét, 0.4 = mờ
MARGIN      = 0.03           # lề cách mép = 3% chiều rộng ảnh
# ======================================

VALID_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


def apply_opacity(logo: Image.Image, opacity: float) -> Image.Image:
    """Giảm độ mờ của logo (giữ vùng trong suốt sẵn có)."""
    logo = logo.convert("RGBA")
    if opacity >= 1.0:
        return logo
    alpha = logo.getchannel("A").point(lambda a: int(a * opacity))
    logo.putalpha(alpha)
    return logo


def position_xy(pos: str, img_w: int, img_h: int, logo_w: int, logo_h: int, margin: int):
    if pos == "center":
        return (img_w - logo_w) // 2, (img_h - logo_h) // 2
    left   = margin
    right  = img_w - logo_w - margin
    top    = margin
    bottom = img_h - logo_h - margin
    return {
        "top-left":     (left,  top),
        "top-right":    (right, top),
        "bottom-left":  (left,  bottom),
        "bottom-right": (right, bottom),
    }.get(pos, (right, top))


def main():
    base = Path(__file__).parent
    logo_file = base / LOGO_PATH
    in_dir    = base / INPUT_DIR
    out_dir   = base / OUTPUT_DIR
    in_dir.mkdir(exist_ok=True)
    out_dir.mkdir(exist_ok=True)

    if not logo_file.exists():
        print(f"❌ Không tìm thấy logo: {logo_file}\n   → Hãy bỏ file logo.png vào thư mục này.")
        return

    logo_master = Image.open(logo_file).convert("RGBA")

    images = [p for p in sorted(in_dir.glob("*")) if p.suffix.lower() in VALID_EXT]
    if not images:
        print(f"⚠️  Không có ảnh nào trong {in_dir}/ → hãy bỏ ảnh vào đó.")
        return

    print(f"🔧 Bắt đầu xử lý {len(images)} ảnh...\n")
    ok = 0
    for p in images:
        try:
            img = Image.open(p).convert("RGBA")
            iw, ih = img.size

            # Resize logo theo tỉ lệ chiều rộng ảnh
            lw = max(1, int(iw * LOGO_RATIO))
            lh = max(1, int(logo_master.height * lw / logo_master.width))
            logo = logo_master.resize((lw, lh), Image.LANCZOS)
            logo = apply_opacity(logo, OPACITY)

            margin_px = int(iw * MARGIN)
            x, y = position_xy(POSITION, iw, ih, lw, lh, margin_px)

            img.paste(logo, (x, y), logo)

            # Lưu: JPG thì ghép nền trắng (bỏ alpha), còn lại giữ PNG
            out_path = out_dir / p.name
            if p.suffix.lower() in {".jpg", ".jpeg"}:
                bg = Image.new("RGB", img.size, (255, 255, 255))
                bg.paste(img, mask=img.getchannel("A"))
                bg.save(out_path, quality=95)
            else:
                img.save(out_path)

            ok += 1
            print(f"  ✅ {p.name}")
        except Exception as e:
            print(f"  ❌ {p.name}: {e}")

    print(f"\n🎉 Xong! {ok}/{len(images)} ảnh đã lưu vào {out_dir}/")


if __name__ == "__main__":
    main()
