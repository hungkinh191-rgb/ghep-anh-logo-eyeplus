"""
App giao dien cho video-factory (chay local, KHONG can cai them thu vien).
Chay:  python3 app.py   -> tu mo http://127.0.0.1:8765

Tinh nang: tai clip/nhac/logo len truc tiep, sua cau chu, chon che do tron,
bat/tat text-logo-GPU, san xuat hang loat, xem tien do.
"""
import cgi
import json
import subprocess
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import batch
import core

ROOT = core.ROOT
IN = ROOT / "input"
DIRS = {"bodies": IN / "bodies", "hooks": IN / "hooks",
        "ctas": IN / "ctas", "music": IN / "music"}
LOGO = IN / "logo.png"
TEXTS = IN / "texts.txt"
OUT = ROOT / "output"
PORT = 8765

# Tao san cac thu muc can thiet (quan trong khi chay tu file .exe)
for _d in list(DIRS.values()) + [OUT, core.CACHE]:
    _d.mkdir(parents=True, exist_ok=True)

STATE = {"running": False, "done": 0, "total": 0, "msg": "San sang", "out": ""}


def open_folder(path):
    """Mo thu muc trong trinh quan ly file (Windows / Mac / Linux)."""
    path = str(path)
    if os.name == "nt":
        os.startfile(path)  # noqa: type-ignore (chi co tren Windows)
    elif sys.platform == "darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])


def run_batch(o):
    STATE.update(running=True, done=0, total=o["count"], msg="Bat dau...")
    out_dir = OUT / f"dot-{_tag()}"
    STATE["out"] = str(out_dir)
    results = []
    try:
        results = batch.produce_batch(
            DIRS["bodies"], out_dir,
            music_dir=DIRS["music"] if o["music"] else None,
            count=o["count"], clips_per_video=o["clips"],
            per_clip_seconds=o["cut"] or None,
            music_volume=o["volume"], keep_original=o["keep"],
            workers=o["workers"], mode=o["mode"],
            hook_dir=DIRS["hooks"], cta_dir=DIRS["ctas"],
            texts=str(TEXTS) if (o["text"] and TEXTS.is_file()) else None,
            text_pos=o["textpos"], text_size=o["textsize"],
            logo=str(LOGO) if (o["logo"] and LOGO.exists()) else None,
            gpu=o["gpu"], random_segment=o.get("randomseg", False),
            transition=o.get("transition", "none"), trans_dur=o.get("transdur", 0.5),
            progress=lambda d, t, m: STATE.update(done=d, total=t, msg=m),
        )
    except Exception as e:
        STATE.update(msg=f"LOI: {str(e)[:300]}")
    # CHI tu don nguon khi THUC SU co video ra (tranh xoa nham khi loi)
    if results and o.get("autoclear"):
        n = clear_inputs(include_logo=True)
        STATE["msg"] = STATE["msg"] + f" · Da don {n} file nguon + logo (ve 0)"
    STATE["running"] = False


def clear_inputs(include_logo=False):
    """Xoa cac clip/nhac trong thu muc nguon -> dem ve 0.
    Giu lai logo & texts.txt (la mau dung lai). File upload la ban copy,
    file goc cua Tung van con tren may."""
    n = 0
    for d in DIRS.values():
        if not d.exists():
            continue
        for f in d.iterdir():
            if f.is_file() and f.name != ".gitkeep":
                f.unlink()
                n += 1
    if include_logo and LOGO.exists():
        LOGO.unlink()
        n += 1
    return n


def _tag():
    existing = [p.name for p in OUT.glob("dot-*")] if OUT.exists() else []
    return f"{len(existing) + 1:03d}"


HTML = r"""<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Video Factory - EyePlus</title>
<style>
*{box-sizing:border-box;font-family:-apple-system,Segoe UI,Roboto,sans-serif}
body{margin:0;background:#0f172a;color:#e2e8f0;padding:24px}
.wrap{max-width:820px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px}.sub{color:#94a3b8;font-size:13px;margin-bottom:20px}
.card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:18px;margin-bottom:16px}
.hd{font-weight:700;margin-bottom:12px;color:#fff}
.row{display:flex;justify-content:space-between;align-items:center;margin:9px 0;gap:12px;flex-wrap:wrap}
label{font-size:14px}.hint{color:#94a3b8;font-size:12px}
input[type=number]{width:90px}input[type=range]{width:150px}
input,select,textarea{background:#0f172a;border:1px solid #475569;color:#e2e8f0;border-radius:8px;padding:7px 9px;font-size:14px}
textarea{width:100%;min-height:90px;resize:vertical;font-size:13px}
button{background:#3b82f6;color:#fff;border:0;border-radius:9px;padding:10px 16px;font-size:14px;cursor:pointer;font-weight:600}
button:hover{background:#2563eb}button.ghost{background:#334155}button.ghost:hover{background:#475569}
button:disabled{opacity:.5;cursor:not-allowed}
.btns{display:flex;gap:8px;flex-wrap:wrap}
.up{border:1.5px dashed #475569;border-radius:10px;padding:14px;text-align:center;cursor:pointer;font-size:13px;color:#94a3b8;transition:.15s}
.up:hover,.up.drag{border-color:#3b82f6;color:#cbd5e1;background:#0f172a}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.bar{height:12px;background:#0f172a;border-radius:6px;overflow:hidden;margin:10px 0}
.bar>div{height:100%;background:linear-gradient(90deg,#3b82f6,#22d3ee);width:0;transition:width .3s}
.stat{font-size:13px;color:#94a3b8}.ok{color:#4ade80}b{color:#fff}
.count{font-size:26px;font-weight:700;color:#22d3ee}
.tag{font-size:11px;background:#0f172a;border:1px solid #475569;border-radius:20px;padding:2px 9px;color:#cbd5e1}
.go{background:#22c55e;font-size:16px;padding:13px 26px}.go:hover{background:#16a34a}
</style></head><body><div class="wrap">
<h1>🎬 Video Factory</h1>
<div class="sub">Tải clip lên → bấm Sản xuất → ra hàng loạt video dọc 9:16 (logo · chữ · nhạc, tự cắt-ghép)</div>

<div class="card">
  <div class="hd">① Nguồn vào <span class="hint">(kéo-thả file vào ô, hoặc bấm chọn)</span></div>
  <div class="grid">
    <div class="up" data-dest="bodies">📹 <b>Clip nội dung</b> <span class="tag" id="t_bodies">0</span><br><span class="hint">kéo-thả hoặc bấm</span></div>
    <div class="up" data-dest="hooks">🎯 <b>Hook</b> (mở đầu) <span class="tag" id="t_hooks">0</span><br><span class="hint">cho chế độ phễu</span></div>
    <div class="up" data-dest="ctas">📣 <b>CTA</b> (kêu gọi) <span class="tag" id="t_ctas">0</span><br><span class="hint">cho chế độ phễu</span></div>
    <div class="up" data-dest="music">🎵 <b>Nhạc nền</b> <span class="tag" id="t_music">0</span><br><span class="hint">mp3, m4a...</span></div>
    <div class="up" data-dest="logo">🖼️ <b>Logo</b> <span class="tag" id="t_logo">—</span><br><span class="hint">png trong suốt</span></div>
    <div class="up" data-dest="bodies2" style="display:flex;align-items:center;justify-content:center" onclick="event.stopPropagation();openF('bodies')">📂 <span class="hint">Mở thư mục nguồn</span></div>
  </div>
  <input type="file" id="picker" multiple hidden>
  <div class="row" style="margin-top:10px"><span class="hint">Làm mới số đếm</span>
    <div class="btns"><button class="ghost" onclick="clearInputs()">🗑️ Xóa nguồn vào</button>
      <button class="ghost" onclick="refresh()">⟳ Cập nhật</button></div></div>
</div>

<div class="card">
  <div class="hd">② Câu chữ chèn lên video <span class="hint">(mỗi dòng = 1 câu, app gán lần lượt cho từng video)</span></div>
  <textarea id="texts" placeholder="Kính EyePlus chính hãng&#10;Giảm đến 50% hôm nay&#10;Bảo hành trọn đời — Mua ngay"></textarea>
  <div class="row"><span class="hint" id="txtSaved"></span><button class="ghost" onclick="saveTexts()">💾 Lưu câu chữ</button></div>
</div>

<div class="card">
  <div class="hd">③ Thông số sản xuất</div>
  <div class="row"><label>Chế độ ghép</label>
    <select id="mode">
      <option value="pool">Trộn ngẫu nhiên (từ Clip nội dung)</option>
      <option value="funnel">Phễu: Hook → Nội dung → CTA</option>
    </select></div>
  <div class="row"><label>Số video cần ra</label><input type="number" id="count" value="50" min="1" max="3000"></div>
  <div class="row"><label>Mỗi video ghép từ … clip nội dung</label><input type="number" id="clips" value="3" min="1" max="20"></div>
  <div class="row"><label>Cắt mỗi clip còn … giây <span class="hint">(0 = giữ nguyên)</span></label><input type="number" id="cut" value="0" min="0" max="60" step="0.5"></div>
  <div class="row"><label>🎲 Cắt ngẫu nhiên đoạn khác nhau <span class="hint">(mỗi video lấy 1 khúc khác trong clip)</span></label><input type="checkbox" id="randomseg" checked></div>
  <hr style="border-color:#334155;width:100%">
  <div class="row"><label>🎞️ Hiệu ứng chuyển cảnh giữa các đoạn</label>
    <select id="transition">
      <option value="none">Không (cắt thẳng — nhanh nhất)</option>
      <option value="fade">Mờ dần</option>
      <option value="fadeblack">Mờ qua đen (Black Fade)</option>
      <option value="fadewhite">Lóe sáng (Glow / Flash)</option>
      <option value="dissolve">Tan vào nhau</option>
      <option value="slideleft">Trượt ngang</option>
      <option value="slideup">Trượt lên</option>
      <option value="circleopen">Mở vòng tròn</option>
      <option value="wipeleft">Gạt ngang</option>
      <option value="pixelize">Vỡ hạt</option>
      <option value="zoomin">Phóng to (Zoom/Whoosh) — gần Warp</option>
      <option value="hblur">Nhoè mờ (Blur)</option>
      <option value="squeezeh">Bóp ngang</option>
      <option value="squeezev">Bóp dọc</option>
      <option value="random">🎲 Ngẫu nhiên (mỗi đoạn 1 kiểu)</option>
    </select></div>
  <div class="row"><label>Độ dài chuyển cảnh (giây)</label><input type="number" id="transdur" value="0.5" min="0.2" max="2" step="0.1"></div>
  <hr style="border-color:#334155;width:100%">
  <div class="row"><label>🎵 Thêm nhạc nền</label><input type="checkbox" id="music" checked></div>
  <div class="row"><label>Giữ tiếng gốc của clip</label><input type="checkbox" id="keep" checked></div>
  <div class="row"><label>Âm lượng nhạc <span class="hint" id="volLbl">80%</span></label><input type="range" id="volume" min="0" max="100" value="80" oninput="volLbl.textContent=this.value+'%'"></div>
  <hr style="border-color:#334155;width:100%">
  <div class="row"><label>✏️ Chèn câu chữ lên video</label><input type="checkbox" id="text" checked></div>
  <div class="row"><label>Vị trí chữ</label><select id="textpos"><option value="bottom">Dưới</option><option value="center">Giữa</option><option value="top">Trên</option></select></div>
  <div class="row"><label>Cỡ chữ</label><input type="number" id="textsize" value="64" min="24" max="160" step="4"></div>
  <div class="row"><label>🖼️ Chèn logo (góc trên-phải)</label><input type="checkbox" id="logo" checked></div>
  <hr style="border-color:#334155;width:100%">
  <div class="row"><label>⚡ Encode bằng GPU (nhanh hơn)</label><input type="checkbox" id="gpu" checked></div>
  <div class="row"><label>Số luồng song song</label><input type="number" id="workers" value="6" min="1" max="16"></div>
</div>

<div class="card">
  <div class="hd">④ Sản xuất</div>
  <div class="row"><label>🗑️ Tự xóa nguồn vào (clip + logo) sau khi sản xuất xong <span class="hint">(đếm về 0)</span></label><input type="checkbox" id="autoclear" checked></div>
  <div class="btns"><button class="go" id="go" onclick="produce()">🚀 Sản xuất</button>
    <button class="ghost" onclick="openF('out')">📂 Mở thư mục kết quả</button></div>
  <div class="bar"><div id="barFill"></div></div>
  <div class="row"><span class="stat" id="msg">Sẵn sàng</span><span class="count" id="prog"></span></div>
</div>
</div>
<script>
const $=id=>document.getElementById(id);
async function refresh(){let s=await(await fetch('/api/status')).json();
  for(const k of ['bodies','hooks','ctas','music'])$('t_'+k).textContent=s[k];
  $('t_logo').textContent=s.logo?'✓':'—';
  if(s.texts&&!$('texts').value)$('texts').value=s.texts;}
function openF(w){fetch('/api/open?w='+w);}
async function upload(dest,files){
  if(!files.length)return; let fd=new FormData();
  for(const f of files)fd.append('file',f);
  $('msg').textContent='Đang tải '+files.length+' file lên...';
  await fetch('/api/upload?dest='+dest,{method:'POST',body:fd});
  $('msg').textContent='Đã tải lên xong.'; refresh();}
let curDest='bodies';
document.querySelectorAll('.up[data-dest]').forEach(el=>{
  const d=el.dataset.dest; if(d==='bodies2')return;
  el.onclick=()=>{curDest=d;$('picker').click();};
  el.ondragover=e=>{e.preventDefault();el.classList.add('drag');};
  el.ondragleave=()=>el.classList.remove('drag');
  el.ondrop=e=>{e.preventDefault();el.classList.remove('drag');upload(d,e.dataTransfer.files);};
});
$('picker').onchange=e=>upload(curDest,e.target.files);
async function saveTexts(){await fetch('/api/texts',{method:'POST',body:$('texts').value});
  $('txtSaved').textContent='Đã lưu ✓';setTimeout(()=>$('txtSaved').textContent='',2000);}
async function clearInputs(){if(!confirm('Xóa hết clip/nhạc + logo trong nguồn vào? (file gốc trên máy bạn vẫn còn)'))return;
  await fetch('/api/clear?what=all',{method:'POST'});$('t_logo').textContent='—';refresh();}
async function produce(){let o={mode:$('mode').value,count:+$('count').value,clips:+$('clips').value,
  cut:+$('cut').value,randomseg:$('randomseg').checked,transition:$('transition').value,transdur:+$('transdur').value,
  music:$('music').checked,keep:$('keep').checked,volume:$('volume').value/100,
  text:$('text').checked,textpos:$('textpos').value,textsize:+$('textsize').value,
  logo:$('logo').checked,gpu:$('gpu').checked,workers:+$('workers').value,autoclear:$('autoclear').checked};
  $('go').disabled=true;await fetch('/api/produce',{method:'POST',body:JSON.stringify(o)});poll();}
async function poll(){let s=await(await fetch('/api/progress')).json();
  let pct=s.total?Math.round(s.done/s.total*100):0;$('barFill').style.width=pct+'%';
  $('msg').textContent=s.msg;$('msg').className='stat'+(s.running?'':' ok');
  $('prog').textContent=s.total?s.done+'/'+s.total:'';
  if(s.running)setTimeout(poll,500);else{$('go').disabled=false;refresh();}}
refresh();
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        b = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            return self._send(200, HTML, "text/html; charset=utf-8")
        if path == "/api/status":
            s = {k: len(core.list_media(d, "audio" if k == "music" else "video"))
                 for k, d in DIRS.items()}
            s["logo"] = LOGO.exists()
            s["texts"] = TEXTS.read_text(encoding="utf-8") if TEXTS.is_file() else ""
            return self._send(200, json.dumps(s))
        if path == "/api/progress":
            return self._send(200, json.dumps(STATE))
        if path == "/api/open":
            w = parse_qs(urlparse(self.path).query).get("w", ["out"])[0]
            open_folder(DIRS.get(w, OUT if w == "out" else IN))
            return self._send(200, json.dumps({"ok": True}))
        return self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/produce":
            if STATE["running"]:
                return self._send(409, json.dumps({"error": "dang chay"}))
            n = int(self.headers.get("Content-Length", 0))
            o = json.loads(self.rfile.read(n) or b"{}")
            threading.Thread(target=run_batch, args=(o,), daemon=True).start()
            return self._send(200, json.dumps({"ok": True}))
        if path == "/api/texts":
            n = int(self.headers.get("Content-Length", 0))
            TEXTS.write_text(self.rfile.read(n).decode("utf-8"), encoding="utf-8")
            return self._send(200, json.dumps({"ok": True}))
        if path == "/api/clear":
            what = parse_qs(urlparse(self.path).query).get("what", ["clips"])[0]
            n = clear_inputs(include_logo=(what == "all"))
            return self._send(200, json.dumps({"cleared": n}))
        if path == "/api/upload":
            dest = parse_qs(urlparse(self.path).query).get("dest", ["bodies"])[0]
            return self._upload(dest)
        return self._send(404, json.dumps({"error": "not found"}))

    def _upload(self, dest):
        form = cgi.FieldStorage(
            fp=self.rfile, headers=self.headers,
            environ={"REQUEST_METHOD": "POST",
                     "CONTENT_TYPE": self.headers["Content-Type"]})
        items = form["file"] if "file" in form else []
        if not isinstance(items, list):
            items = [items]
        saved = 0
        for it in items:
            if not getattr(it, "filename", None):
                continue
            name = Path(it.filename).name
            if dest == "logo":
                target = LOGO
            else:
                target = DIRS.get(dest, DIRS["bodies"]) / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "wb") as f:
                f.write(it.file.read())
            saved += 1
        return self._send(200, json.dumps({"saved": saved}))


def open_as_app(url):
    """Mo giao dien dang APP (cua so rieng, khong co thanh trinh duyet).
    Uu tien Edge/Chrome che do --app; neu khong co thi mo tab thuong."""
    if os.name == "nt":
        candidates = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
        for exe in candidates:
            if os.path.exists(exe):
                try:
                    subprocess.Popen([exe, f"--app={url}", "--window-size=900,1000"])
                    return
                except Exception:
                    pass
    elif sys.platform == "darwin":
        # Chrome che do app neu co; khong thi mo trinh duyet mac dinh
        chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if os.path.exists(chrome):
            try:
                subprocess.Popen([chrome, f"--app={url}"])
                return
            except Exception:
                pass
    webbrowser.open(url)


def main():
    url = f"http://127.0.0.1:{PORT}"
    # Chay web server o thread nen (giao dien la trang web noi bo)
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        # Cong dang ban -> co the app da mo san; chi mo cua so tro toi no
        server = None
    if server:
        threading.Thread(target=server.serve_forever, daemon=True).start()

    # Hien giao dien trong CUA SO APP RIENG (pywebview) - KHONG mo trinh duyet.
    # Tren Windows dung thanh phan WebView2 co san cua Windows (khong phai trinh duyet Edge).
    try:
        import webview
        webview.create_window("Video Factory - EyePlus", url, width=940, height=1020)
        webview.start()
        return  # dong cua so -> thoat app
    except Exception as e:
        print("Khong mo duoc cua so app rieng, chuyen sang trinh duyet:", e)

    # Du phong: mo bang trinh duyet + giu tien trinh song
    open_as_app(url)
    import time
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
