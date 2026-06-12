# Đưa "Ghép Ảnh Logo EyePlus" lên Railway

Tool web tĩnh trong thư mục `web/`, được phục vụ bởi `server.py` (Python thuần,
không cần thư viện ngoài). Railway sẽ chạy lệnh `python server.py` và tự cấp cổng
qua biến môi trường `PORT`.

## File phục vụ deploy
- `server.py` — server tĩnh, lắng nghe `0.0.0.0:$PORT`, phục vụ thư mục `web/`
- `Procfile`, `railway.json`, `nixpacks.toml` — cấu hình để Railway chạy đúng lệnh
- `requirements.txt` — rỗng, chỉ để Railway nhận diện app Python

---

## CÁCH 1 — Deploy bằng GitHub (khuyên dùng)

1. Tạo repo trên https://github.com rồi đẩy code lên:
   ```bash
   cd "/Users/tungteaz/AI EP"
   git init
   git add .
   git commit -m "Ghép Ảnh Logo EyePlus - web tool"
   git branch -M main
   git remote add origin https://github.com/<tài-khoản>/<repo>.git
   git push -u origin main
   ```
2. Vào https://railway.app → **New Project** → **Deploy from GitHub repo** → chọn repo.
3. Railway tự build & chạy. Khi xong, vào tab **Settings → Networking → Generate Domain**.
4. Đổi subdomain thành:  `ghep-anh-logo-eyeplus`
   → link sẽ là: **https://ghep-anh-logo-eyeplus.up.railway.app**

## CÁCH 2 — Deploy bằng Railway CLI (không cần GitHub)

```bash
# Cài CLI (cần Node, hoặc tải bản cài tại railway.app)
npm i -g @railway/cli      # hoặc: brew install railway

cd "/Users/tungteaz/AI EP"
railway login
railway init                # đặt tên project: ghep-anh-logo-eyeplus
railway up                  # build & deploy
railway domain              # tạo domain công khai
```

---

## Về tên miền
- Railway **không** cho phép dấu cách hay dấu tiếng Việt trong subdomain.
  Tên "Ghép Ảnh Logo EyePlus" được dùng làm **tiêu đề trang** (đã set sẵn).
- Subdomain hợp lệ gợi ý: `ghep-anh-logo-eyeplus`
  → `https://ghep-anh-logo-eyeplus.up.railway.app`
- Muốn domain riêng (vd: `logo.eyeplus.vn`): vào **Settings → Networking →
  Custom Domain**, thêm domain rồi trỏ bản ghi CNAME theo hướng dẫn của Railway.

## Kiểm tra tại máy trước khi deploy
```bash
cd "/Users/tungteaz/AI EP"
PORT=8099 python3 server.py
# mở http://localhost:8099
```
