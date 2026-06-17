"""
Loi xu ly video cua video-factory.
- Chuan hoa moi clip ve 9:16 (1080x1920, 30fps, H.264, AAC) -> de noi nhanh
- Noi cac clip thanh 1 video (concat copy = rat nhanh)
- Render cuoi: chen LOGO + TEXT/phu de + tron NHAC, encode CPU hoac GPU (videotoolbox)

Dung ffmpeg static trong thu muc bin/. Khong can cai dat he thong.
"""
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

# Phan biet chay tu ma nguon hay tu file .exe (PyInstaller).
if getattr(sys, "frozen", False):
    BUNDLE = Path(sys._MEIPASS)                       # tai nguyen kem theo (ffmpeg, font)
    ROOT = Path(sys.executable).resolve().parent      # du lieu (input/output/cache) ben canh .exe
else:
    BUNDLE = Path(__file__).resolve().parent
    ROOT = BUNDLE

_FF = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
FFMPEG = str(BUNDLE / "bin" / _FF)
FONT = str(BUNDLE / "bin" / "font.ttf")
CACHE = ROOT / "cache"
CACHE.mkdir(parents=True, exist_ok=True)

# Thong so chuan (video doc 9:16)
W, H, FPS = 1080, 1920, 30
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}
AUDIO_EXTS = {".mp3", ".m4a", ".aac", ".wav", ".flac", ".ogg"}
IMG_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def run(args, **kw):
    p = subprocess.run([FFMPEG, "-hide_banner", "-y", *args],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kw)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode("utf-8", "ignore")[-1500:])
    return p


def probe(path):
    """Doc duration (giay) va co audio hay khong."""
    p = subprocess.run([FFMPEG, "-hide_banner", "-i", str(path)],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    err = p.stderr.decode("utf-8", "ignore")
    dur = 0.0
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", err)
    if m:
        h, mi, s = m.groups()
        dur = int(h) * 3600 + int(mi) * 60 + float(s)
    has_audio = bool(re.search(r"Stream #\d+:\d+.*Audio:", err))
    return dur, has_audio


def venc(gpu=False, bitrate="6M", crf=20):
    """Tham so encode video. GPU videotoolbox CHI co tren Mac;
    tren Windows/Linux luon dung CPU (libx264) cho chac chan, khong phu thuoc card."""
    if gpu and sys.platform == "darwin":
        return ["-c:v", "h264_videotoolbox", "-b:v", bitrate, "-pix_fmt", "yuv420p"]
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), "-pix_fmt", "yuv420p"]


def normalize(src, per_clip_seconds=None, gpu=False):
    """Chuan hoa 1 clip ve 9:16 chuan, tra ve file da cache."""
    src = Path(src)
    key = f"{src.resolve()}|{src.stat().st_mtime}|{per_clip_seconds}|{W}x{H}@{FPS}|gpu={gpu}"
    h = hashlib.md5(key.encode()).hexdigest()[:16]
    dst = CACHE / f"{h}.mp4"
    if dst.exists():
        return dst

    _, has_audio = probe(src)
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
          f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,fps={FPS}")
    args = ["-i", str(src)]
    if not has_audio:
        args += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]
    if per_clip_seconds:
        args += ["-t", str(per_clip_seconds)]
    args += ["-vf", vf, "-r", str(FPS)]
    args += venc(gpu)
    args += ["-g", str(FPS * 2), "-video_track_timescale", "90000",
             "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "128k"]
    if not has_audio:
        args += ["-shortest", "-map", "0:v:0", "-map", "1:a:0"]
    args += [str(dst)]
    run(args)
    return dst


def concat(clips, dst):
    """Noi cac clip DA CHUAN HOA bang concat demuxer (copy = rat nhanh)."""
    lst = CACHE / f"concat_{hashlib.md5(str(clips).encode()).hexdigest()[:12]}.txt"
    lst.write_text("".join(f"file '{Path(c).resolve()}'\n" for c in clips))
    run(["-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(dst)])
    lst.unlink(missing_ok=True)
    return dst


# Vi tri chen (logo & text): bieu thuc x,y theo kich thuoc video
_POS = {
    "top": "h*0.08", "center": "(h-text_h)/2", "bottom": "h*0.82",
}
_LOGO_POS = {
    "top-left": "{m}:{m}", "top-right": "W-w-{m}:{m}",
    "bottom-left": "{m}:H-h-{m}", "bottom-right": "W-w-{m}:H-h-{m}",
    "center": "(W-w)/2:(H-h)/2",
}


def _esc_path(p):
    return str(p).replace("\\", "/").replace("'", "\\'")


def _drawtext(text, pos="bottom", size=64, color="white", box=True, idx=0):
    """Tao filter drawtext, ghi text ra file (tranh loi escape tieng Viet)."""
    tf = CACHE / f"txt_{hashlib.md5((text + str(idx) + pos).encode()).hexdigest()[:12]}.txt"
    tf.write_text(text, encoding="utf-8")
    y = _POS.get(pos, _POS["bottom"])
    expr = (f"drawtext=fontfile='{_esc_path(FONT)}':textfile='{_esc_path(tf)}'"
            f":expansion=none:fontcolor={color}:fontsize={size}:x=(w-text_w)/2:y={y}"
            f":line_spacing=12:borderw=3:bordercolor=black@0.8")
    if box:
        expr += ":box=1:boxcolor=black@0.45:boxborderw=24"
    return expr


def render(base_video, out, music=None, music_volume=0.8, keep_original=True,
           original_volume=1.0, fade=2.0, logo=None, logo_scale=0.18,
           logo_pos="top-right", logo_margin=40, texts=None, gpu=False, bitrate="6M"):
    """Render cuoi: overlay logo + text + tron nhac. Re-encode (CPU/GPU).
    texts: list dict {text, pos, size, color, box}."""
    texts = texts or []
    has_vfx = bool(logo) or bool(texts)
    vdur, _ = probe(base_video)

    # --- Truong hop khong co logo/text: dung duong nhanh ---
    if not has_vfx:
        if not music:
            run(["-i", str(base_video), "-c", "copy", str(out)])
            return out
        return _music_copy(base_video, music, out, music_volume, keep_original,
                           original_volume, fade, vdur)

    # --- Co logo/text: dung 1 lan re-encode bang filter_complex ---
    inputs = ["-i", str(base_video)]
    parts, vlabel = [], "0:v"
    logo_idx = music_idx = None
    nxt = 1
    if logo:
        inputs += ["-i", str(logo)]
        logo_idx = nxt; nxt += 1
    if music:
        inputs += ["-stream_loop", "-1", "-i", str(music)]
        music_idx = nxt; nxt += 1

    if logo:
        parts.append(f"[{logo_idx}:v]scale={int(W * logo_scale)}:-1[lg]")
        pos = _LOGO_POS.get(logo_pos, _LOGO_POS["top-right"]).format(m=logo_margin)
        parts.append(f"[{vlabel}][lg]overlay={pos}[vl]")
        vlabel = "vl"
    for i, t in enumerate(texts):
        dt = _drawtext(t.get("text", ""), t.get("pos", "bottom"),
                       t.get("size", 64), t.get("color", "white"),
                       t.get("box", True), idx=i)
        parts.append(f"[{vlabel}]{dt}[vt{i}]")
        vlabel = f"vt{i}"

    if music:
        fstart = max(0, vdur - fade)
        parts.append(f"[{music_idx}:a]atrim=0:{vdur},afade=t=out:st={fstart:.2f}:d={fade},"
                     f"volume={music_volume}[m]")
        if keep_original:
            parts.append(f"[0:a]volume={original_volume}[o];"
                         f"[o][m]amix=inputs=2:duration=first:dropout_transition=0[a]")
        else:
            parts[-1] = parts[-1].replace("[m]", "[a]")
        amap = "[a]"
    else:
        amap = "0:a"

    args = inputs + ["-filter_complex", ";".join(parts),
                     "-map", f"[{vlabel}]", "-map", amap]
    args += venc(gpu, bitrate)
    args += ["-c:a", "aac", "-b:a", "192k", "-shortest", str(out)]
    run(args)
    return out


def _music_copy(video, music, out, music_volume, keep_original, original_volume, fade, vdur):
    """Them nhac ma KHONG encode lai video (copy) -> nhanh."""
    fstart = max(0, vdur - fade)
    a_music = (f"[1:a]atrim=0:{vdur},afade=t=out:st={fstart:.2f}:d={fade},"
               f"volume={music_volume}[m]")
    if keep_original:
        fc = (f"{a_music};[0:a]volume={original_volume}[o];"
              f"[o][m]amix=inputs=2:duration=first:dropout_transition=0[a]")
    else:
        fc = a_music.replace("[m]", "[a]")
    run(["-i", str(video), "-stream_loop", "-1", "-i", str(music),
         "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)])
    return out


def make_segment(full_norm, start, dur, gpu=False):
    """Cat doan [start, start+dur] tu clip DA chuan hoa. Dung de lay cac
    DOAN KHAC NHAU cua cung 1 clip -> tao bien the da dang."""
    key = f"seg|{full_norm}|{start:.2f}|{dur}|gpu={gpu}"
    h = hashlib.md5(key.encode()).hexdigest()[:16]
    dst = CACHE / f"{h}.mp4"
    if dst.exists():
        return dst
    args = ["-ss", f"{start:.2f}", "-i", str(full_norm), "-t", str(dur)]
    args += venc(gpu) + ["-r", str(FPS), "-g", str(FPS * 2),
                         "-video_track_timescale", "90000",
                         "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "128k",
                         str(dst)]
    run(args)
    return dst


def assemble(norm_clips, out, music=None, music_volume=0.8, keep_original=True,
             logo=None, texts=None, gpu=False, **kw):
    """Noi cac clip DA chuan hoa -> render (logo/text/nhac)."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = CACHE / f"tmp_{out.stem}.mp4"
    concat(norm_clips, tmp)
    render(tmp, out, music=music, music_volume=music_volume,
           keep_original=keep_original, logo=logo, texts=texts, gpu=gpu,
           **{k: v for k, v in kw.items()
              if k in ("logo_scale", "logo_pos", "logo_margin", "fade",
                       "original_volume", "bitrate")})
    tmp.unlink(missing_ok=True)
    return out


def build_one(clips, out, music=None, per_clip_seconds=None, music_volume=0.8,
              keep_original=True, logo=None, texts=None, gpu=False, **kw):
    """Pipeline day du: chuan hoa -> noi -> render (logo/text/nhac)."""
    norm = [normalize(c, per_clip_seconds, gpu=gpu) for c in clips]
    return assemble(norm, out, music=music, music_volume=music_volume,
                    keep_original=keep_original, logo=logo, texts=texts,
                    gpu=gpu, **kw)


def list_media(folder, kind="video"):
    exts = {"video": VIDEO_EXTS, "audio": AUDIO_EXTS, "image": IMG_EXTS}[kind]
    p = Path(folder)
    if not p.exists():
        return []
    return sorted(f for f in p.iterdir() if f.suffix.lower() in exts)


if __name__ == "__main__":
    args = sys.argv[1:]
    opt = {}
    for flag, key in (("--music", "music"), ("--logo", "logo"), ("--text", "text")):
        if flag in args:
            i = args.index(flag)
            opt[key] = args[i + 1]
            args = args[:i] + args[i + 2:]
    gpu = "--gpu" in args
    args = [a for a in args if a != "--gpu"]
    if not args:
        print("Dung: python3 core.py <clip1> <clip2> ... "
              "[--music nhac.mp3] [--logo logo.png] [--text 'Chu'] [--gpu]")
        sys.exit(1)
    texts = [{"text": opt["text"], "pos": "bottom"}] if "text" in opt else None
    out = ROOT / "output" / "test.mp4"
    print("Dang dung video...")
    build_one(args, out, music=opt.get("music"), logo=opt.get("logo"),
              texts=texts, gpu=gpu)
    print(f"Xong: {out}")
