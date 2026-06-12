#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APP KÉO-THẢ CHÈN LOGO
=====================
Mở app lên → kéo ảnh thả vào cửa sổ (hoặc bấm "Chọn ảnh") → bấm "Chèn logo".
Ảnh kết quả nằm trong thư mục  output/  (ảnh gốc KHÔNG bị thay đổi).

Chạy:  python3 app.py     — hoặc nhấn đúp  mo_app.command (Mac) / mo_app_WINDOWS.bat (Windows)
"""

import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image

# --- Kéo-thả thật (nếu có thư viện tkinterdnd2) ---
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_OK = True
except Exception:
    DND_OK = False

# Khi đóng gói thành .exe (PyInstaller), dùng thư mục chứa file .exe;
# còn khi chạy bằng python thì dùng thư mục chứa file app.py.
if getattr(sys, "frozen", False):
    BASE = Path(sys.executable).parent
else:
    BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
VALID_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
POSITIONS = ["top-left", "top-right", "bottom-left", "bottom-right", "center"]


# ---------- Xử lý ảnh ----------
def apply_opacity(logo, opacity):
    logo = logo.convert("RGBA")
    if opacity >= 1.0:
        return logo
    alpha = logo.getchannel("A").point(lambda a: int(a * opacity))
    logo.putalpha(alpha)
    return logo


def position_xy(pos, iw, ih, lw, lh, m):
    if pos == "center":
        return (iw - lw) // 2, (ih - lh) // 2
    left, right, top, bottom = m, iw - lw - m, m, ih - lh - m
    return {
        "top-left": (left, top), "top-right": (right, top),
        "bottom-left": (left, bottom), "bottom-right": (right, bottom),
    }.get(pos, (right, top))


def process_one(img_path, logo_master, pos, ratio, opacity, margin, out_dir):
    img = Image.open(img_path).convert("RGBA")
    iw, ih = img.size
    lw = max(1, int(iw * ratio))
    lh = max(1, int(logo_master.height * lw / logo_master.width))
    logo = apply_opacity(logo_master.resize((lw, lh), Image.LANCZOS), opacity)
    mx = int(iw * margin)
    x, y = position_xy(pos, iw, ih, lw, lh, mx)
    img.paste(logo, (x, y), logo)
    out_path = out_dir / img_path.name
    if img_path.suffix.lower() in {".jpg", ".jpeg"}:
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.getchannel("A"))
        bg.save(out_path, quality=95)
    else:
        img.save(out_path)
    return out_path


# ---------- Giao diện ----------
class App:
    def __init__(self, root):
        self.root = root
        self.images = []          # danh sách Path ảnh đã thêm
        self.logo_path = tk.StringVar()
        # tự nhận logo.png nếu có sẵn
        default_logo = BASE / "logo.png"
        if default_logo.exists():
            self.logo_path.set(str(default_logo))

        root.title("Chèn Logo — Kéo Thả")
        root.geometry("560x620")
        root.minsize(520, 560)

        pad = {"padx": 12, "pady": 6}

        # --- Logo ---
        f_logo = ttk.LabelFrame(root, text="1. Logo (PNG nền trong suốt là đẹp nhất)")
        f_logo.pack(fill="x", **pad)
        self.lbl_logo = ttk.Label(f_logo, text=self._logo_text(), foreground="#444")
        self.lbl_logo.pack(side="left", padx=8, pady=8)
        ttk.Button(f_logo, text="Chọn logo…", command=self.pick_logo).pack(side="right", padx=8, pady=8)

        # --- Vùng kéo thả ---
        f_drop = ttk.LabelFrame(root, text="2. Ảnh cần chèn")
        f_drop.pack(fill="both", expand=True, **pad)
        drop_hint = ("⬇  KÉO ẢNH THẢ VÀO ĐÂY  ⬇\n(hoặc bấm để chọn ảnh)"
                     if DND_OK else "BẤM VÀO ĐÂY ĐỂ CHỌN ẢNH")
        self.drop = tk.Label(f_drop, text=drop_hint, relief="ridge", bd=2,
                             bg="#f3f6fb", fg="#3366aa", height=4, cursor="hand2",
                             font=("Helvetica", 13, "bold"))
        self.drop.pack(fill="x", padx=8, pady=8)
        self.drop.bind("<Button-1>", lambda e: self.pick_images())
        if DND_OK:
            self.drop.drop_target_register(DND_FILES)
            self.drop.dnd_bind("<<Drop>>", self.on_drop)

        self.listbox = tk.Listbox(f_drop, height=7)
        self.listbox.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        row = ttk.Frame(f_drop); row.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(row, text="Thêm ảnh…", command=self.pick_images).pack(side="left")
        ttk.Button(row, text="Xoá danh sách", command=self.clear_images).pack(side="left", padx=6)
        self.lbl_count = ttk.Label(row, text="0 ảnh"); self.lbl_count.pack(side="right")

        # --- Tuỳ chỉnh ---
        f_set = ttk.LabelFrame(root, text="3. Tuỳ chỉnh logo")
        f_set.pack(fill="x", **pad)
        g = ttk.Frame(f_set); g.pack(fill="x", padx=8, pady=8)

        ttk.Label(g, text="Vị trí:").grid(row=0, column=0, sticky="w")
        self.pos = tk.StringVar(value="top-left")
        ttk.Combobox(g, textvariable=self.pos, values=POSITIONS, width=14,
                     state="readonly").grid(row=0, column=1, sticky="w", padx=6)

        ttk.Label(g, text="Cỡ logo:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.size = tk.IntVar(value=10)
        ttk.Scale(g, from_=3, to=40, variable=self.size, orient="horizontal",
                  length=200, command=lambda v: self._refresh_labels()
                  ).grid(row=1, column=1, sticky="w", padx=6, pady=(8, 0))
        self.lbl_size = ttk.Label(g, text="10% bề ngang ảnh")
        self.lbl_size.grid(row=1, column=2, sticky="w")

        ttk.Label(g, text="Độ đậm:").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.op = tk.IntVar(value=100)
        ttk.Scale(g, from_=10, to=100, variable=self.op, orient="horizontal",
                  length=200, command=lambda v: self._refresh_labels()
                  ).grid(row=2, column=1, sticky="w", padx=6, pady=(8, 0))
        self.lbl_op = ttk.Label(g, text="100%")
        self.lbl_op.grid(row=2, column=2, sticky="w")

        # --- Hành động ---
        f_act = ttk.Frame(root); f_act.pack(fill="x", **pad)
        self.btn_run = tk.Button(f_act, text="▶  CHÈN LOGO", command=self.run,
                                 bg="#2e7d32", fg="white", font=("Helvetica", 13, "bold"),
                                 height=2, relief="raised")
        self.btn_run.pack(fill="x")
        self.status = ttk.Label(root, text="Sẵn sàng.", foreground="#555")
        self.status.pack(fill="x", padx=12)
        ttk.Button(root, text="📂  Mở thư mục kết quả (output)",
                   command=self.open_output).pack(fill="x", padx=12, pady=(0, 12))

    # ---- helpers ----
    def _logo_text(self):
        p = self.logo_path.get()
        return f"✅ {Path(p).name}" if p else "⚠️ Chưa chọn logo"

    def _refresh_labels(self):
        self.lbl_size.config(text=f"{self.size.get()}% bề ngang ảnh")
        self.lbl_op.config(text=f"{self.op.get()}%")

    def _update_list(self):
        self.listbox.delete(0, "end")
        for p in self.images:
            self.listbox.insert("end", p.name)
        self.lbl_count.config(text=f"{len(self.images)} ảnh")

    # ---- actions ----
    def pick_logo(self):
        f = filedialog.askopenfilename(title="Chọn file logo",
                                       filetypes=[("Ảnh", "*.png *.jpg *.jpeg *.webp *.bmp")])
        if f:
            self.logo_path.set(f)
            self.lbl_logo.config(text=self._logo_text())

    def _add_paths(self, paths):
        added = 0
        for s in paths:
            p = Path(s)
            if p.suffix.lower() in VALID_EXT and p not in self.images and p.is_file():
                self.images.append(p); added += 1
        self._update_list()
        if added:
            self.status.config(text=f"Đã thêm {added} ảnh.")

    def pick_images(self):
        fs = filedialog.askopenfilenames(
            title="Chọn ảnh",
            filetypes=[("Ảnh", "*.jpg *.jpeg *.png *.webp *.bmp *.tiff")])
        if fs:
            self._add_paths(fs)

    def on_drop(self, event):
        # event.data có thể là "{đường dẫn có dấu cách} /khac/abc.jpg"
        self._add_paths(self.root.tk.splitlist(event.data))

    def clear_images(self):
        self.images.clear(); self._update_list()
        self.status.config(text="Đã xoá danh sách.")

    def open_output(self):
        OUTPUT_DIR.mkdir(exist_ok=True)
        import subprocess, sys
        if sys.platform == "darwin":
            subprocess.run(["open", str(OUTPUT_DIR)])
        elif sys.platform.startswith("win"):
            subprocess.run(["explorer", str(OUTPUT_DIR)])
        else:
            subprocess.run(["xdg-open", str(OUTPUT_DIR)])

    def run(self):
        logo = self.logo_path.get()
        if not logo or not Path(logo).exists():
            messagebox.showwarning("Thiếu logo", "Hãy chọn file logo trước.")
            return
        if not self.images:
            messagebox.showwarning("Chưa có ảnh", "Hãy kéo thả hoặc chọn ảnh cần chèn logo.")
            return

        OUTPUT_DIR.mkdir(exist_ok=True)
        logo_master = Image.open(logo).convert("RGBA")
        pos = self.pos.get()
        ratio = self.size.get() / 100.0
        opacity = self.op.get() / 100.0

        self.btn_run.config(state="disabled", text="Đang xử lý…")
        self.root.update()
        ok, fail = 0, 0
        for i, p in enumerate(list(self.images), 1):
            try:
                process_one(p, logo_master, pos, ratio, opacity, 0.03, OUTPUT_DIR)
                ok += 1
            except Exception as e:
                fail += 1
                print(f"Lỗi {p.name}: {e}")
            self.status.config(text=f"Đang xử lý {i}/{len(self.images)}…")
            self.root.update()

        self.btn_run.config(state="normal", text="▶  CHÈN LOGO")
        self.status.config(text=f"🎉 Xong! {ok} ảnh đã lưu vào output/" + (f" ({fail} lỗi)" if fail else ""))
        if messagebox.askyesno("Hoàn tất",
                               f"Đã chèn logo {ok} ảnh.\nMở thư mục kết quả?"):
            self.open_output()


def main():
    root = TkinterDnD.Tk() if DND_OK else tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
