# 🎬 Video Factory — Ghép video hàng loạt cho EyePlus

Tải clip lên → bấm 1 nút → ra **hàng loạt video dọc 9:16**: tự cắt-ghép, chèn **logo + chữ + nhạc**.

## Cách dùng (4 bước trong app)

1. **Mở app:** bấm-đúp file **`Khoi-dong.command`** (trình duyệt tự mở).
2. **Tải nguồn lên** (mục ①): kéo-thả file vào đúng ô — hoặc bấm để chọn:
   - 📹 **Clip nội dung** → dùng cho cả 2 chế độ
   - 🎯 **Hook** (mở đầu) · 📣 **CTA** (kêu gọi) → cho chế độ phễu
   - 🎵 **Nhạc** (mp3, m4a…) · 🖼️ **Logo** (png trong suốt)
3. **Câu chữ** (mục ②): gõ mỗi dòng 1 câu → bấm **💾 Lưu**. App gán lần lượt cho từng video.
4. **Chỉnh thông số** (mục ③) → bấm **🚀 Sản xuất** (mục ④) → xem tiến độ → **📂 Mở thư mục kết quả**.

Mỗi đợt lưu riêng: `output/dot-001`, `dot-002`, …

## ⚠️ Mẹo quan trọng về độ dài

**"Cắt mỗi clip còn … giây"** quyết định độ dài video:
- Để **0** = giữ NGUYÊN clip → nếu clip dài 40s thì video ra rất dài.
- Đặt **2–3 giây** = montage nhanh, mỗi clip lấy vài giây đầu → video ngắn gọn kiểu quảng cáo.

→ Muốn ra video ngắn để chạy ads, **nhớ đặt số giây cắt** (vd 2.5), đừng để 0.

## 2 chế độ ghép

| Chế độ | Cách ghép |
|---|---|
| **Trộn ngẫu nhiên** | Mỗi video = K clip ngẫu nhiên từ "Clip nội dung", xáo thứ tự |
| **Phễu Hook→Nội dung→CTA** | Mỗi video = 1 Hook + K clip nội dung + 1 CTA (ra nhiều biến thể để test ads) |

## Các thông số khác

| Thông số | Ý nghĩa |
|---|---|
| Số video cần ra | Vài chục → hàng trăm/đợt |
| Mỗi video ghép từ … clip | Số clip nội dung bốc vào mỗi video |
| Thêm nhạc / Giữ tiếng gốc / Âm lượng | Nhạc nền tự lặp-cắt vừa độ dài + fade cuối; trộn hoặc thay tiếng gốc |
| Chèn câu chữ + Vị trí + Cỡ chữ | Lấy từ mục ② (hỗ trợ tiếng Việt đầy đủ dấu) |
| Chèn logo | Logo png góc trên-phải (cần đã upload logo) |
| ⚡ Encode GPU | Dùng chip Mac (videotoolbox) — nhanh, nên bật |
| Số luồng song song | Máy 8 nhân để **6** |

## Tốc độ
Chuẩn hoá clip 1 lần (cache) + nối kiểu copy + chạy song song + GPU.
Video ngắn (cắt 2–3s): vài chục video chỉ trong ít giây. Clip dài/nhiều: vài phút/đợt.

## Chạy bằng lệnh (nâng cao)
```bash
# 100 video phễu, cắt mỗi clip 2.5s, logo + GPU
python3 batch.py --count 100 --mode funnel --clips 3 --cut 2.5 --logo input/logo.png --gpu --workers 6

# Ghép 1 video cụ thể
python3 core.py clipA.mp4 clipB.mp4 --music nhac.mp3 --logo logo.png --text "Chữ" --gpu
```

## Cấu trúc
```
video-factory/
├── Khoi-dong.command   ← bấm-đúp để mở app
├── app.py · batch.py · core.py
├── bin/ffmpeg · bin/font.ttf   ← engine + font tiếng Việt (đã có sẵn)
├── input/{bodies,hooks,ctas,music}/ · input/logo.png · input/texts.txt
├── cache/   ← clip đã chuẩn hoá (xoá được, tự sinh lại)
└── output/dot-NNN/   ← kết quả từng đợt
```
