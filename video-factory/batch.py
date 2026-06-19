"""
Engine san xuat hang loat.
2 che do:
  - "pool"  : moi video = K clip ngau nhien tu kho bodies (xao thu tu)
  - "funnel": moi video = 1 Hook + K Body + 1 CTA  (tron bien the phieu mua hang)
Kem: gan TEXT tu danh sach, chen LOGO, tron NHAC, encode CPU/GPU.
Chuan hoa truoc 1 lan -> san xuat song song cuc nhanh.
"""
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import core

ROOT = core.ROOT


def _read_texts(texts):
    """texts co the la list cau, hoac duong dan file .txt (moi dong 1 cau)."""
    if not texts:
        return []
    if isinstance(texts, (str, Path)) and Path(texts).is_file():
        return [ln.strip() for ln in Path(texts).read_text(encoding="utf-8").splitlines()
                if ln.strip()]
    if isinstance(texts, str):
        return [texts]
    return list(texts)


def produce_batch(pool_dir, out_dir, music_dir=None, count=20,
                  clips_per_video=3, per_clip_seconds=None,
                  music_volume=0.8, keep_original=True, workers=4,
                  seed=None, progress=None,
                  mode="pool", hook_dir=None, cta_dir=None,
                  texts=None, text_pos="bottom", text_size=64, text_color="white",
                  logo=None, gpu=False, bitrate="6M", random_segment=False,
                  transition="none", trans_dur=0.5):
    """San xuat `count` video.

    mode             : "pool" (tron tu bodies) | "funnel" (Hook+Body+CTA)
    hook_dir, cta_dir: thu muc hook/cta (che do funnel)
    texts            : list cau hoac file .txt -> gan moi video 1 cau
    text_pos         : top | center | bottom
    logo             : duong dan logo .png
    gpu              : True = encode bang GPU videotoolbox (nhanh)
    random_segment   : True = moi lan dung clip lay 1 DOAN NGAU NHIEN khac nhau
                       (chi co tac dung khi per_clip_seconds > 0)
    """
    rnd = random.Random(seed)
    bodies = core.list_media(pool_dir)
    musics = core.list_media(music_dir, "audio") if music_dir else []
    hooks = core.list_media(hook_dir) if hook_dir else []
    ctas = core.list_media(cta_dir) if cta_dir else []
    text_list = _read_texts(texts)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if mode == "funnel" and not (hooks or ctas):
        mode = "pool"  # khong co hook/cta -> ve che do pool
    if not bodies and not hooks:
        raise RuntimeError(f"Khong tim thay clip nao trong: {pool_dir}")

    def emit(d, t, m):
        if progress:
            progress(d, t, m)

    # Cat ngau nhien chi co y nghia khi co cat (per_clip_seconds > 0)
    rseg = bool(random_segment and per_clip_seconds)
    # B1: chuan hoa truoc moi clip nguon (tuan tu, dien cache)
    # Neu cat ngau nhien: chuan hoa NGUYEN clip (de con cat doan bat ky sau do)
    norm_cut = None if rseg else per_clip_seconds
    all_src = list(dict.fromkeys(bodies + hooks + ctas))
    dur_cache = {}
    emit(0, count, f"Dang chuan hoa {len(all_src)} clip goc...")
    for i, c in enumerate(all_src, 1):
        full = core.normalize(c, norm_cut, gpu=gpu)
        if rseg:
            dur_cache[str(c)] = core.probe(full)[0]
        emit(0, count, f"Chuan hoa {i}/{len(all_src)}")

    # B2: len kich ban tung video
    k = min(clips_per_video, len(bodies)) if bodies else 0
    texts_shuffled = text_list[:]
    rnd.shuffle(texts_shuffled)
    jobs = []
    for i in range(count):
        if mode == "funnel":
            picks = []
            if hooks:
                picks.append(rnd.choice(hooks))
            if bodies:
                picks += rnd.sample(bodies, k) if len(bodies) >= k else bodies[:]
            if ctas:
                picks.append(rnd.choice(ctas))
        else:
            picks = rnd.sample(bodies, k) if len(bodies) >= k else bodies[:]
            rnd.shuffle(picks)
        music = rnd.choice(musics) if musics else None
        txt = texts_shuffled[i % len(texts_shuffled)] if texts_shuffled else None
        out = out_dir / f"video_{i + 1:03d}.mp4"
        # diem bat dau ngau nhien cho tung clip (neu cat ngau nhien)
        if rseg:
            starts = [round(rnd.uniform(0, max(0.0, dur_cache.get(str(c), 0) -
                                                per_clip_seconds)), 2) for c in picks]
        else:
            starts = [None] * len(picks)
        jobs.append((picks, starts, music, txt, out))

    # B3: san xuat song song
    done = 0

    def make(job):
        picks, starts, music, txt, out = job
        norm = []
        for c, start in zip(picks, starts):
            if start is None:
                norm.append(core.normalize(c, per_clip_seconds, gpu=gpu))
            else:
                full = core.normalize(c, None, gpu=gpu)
                norm.append(core.make_segment(full, start, per_clip_seconds, gpu=gpu))
        tlist = [{"text": txt, "pos": text_pos, "size": text_size,
                  "color": text_color}] if txt else None
        core.assemble(norm, out, music=music, music_volume=music_volume,
                      keep_original=keep_original, logo=logo, texts=tlist,
                      gpu=gpu, bitrate=bitrate,
                      transition=transition, trans_dur=trans_dur)
        return out

    results = []
    emit(0, count, "Bat dau san xuat...")
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(make, j): j for j in jobs}
        for fut in as_completed(futs):
            done += 1
            try:
                results.append(str(fut.result()))
                emit(done, count, f"Xong {done}/{count}")
            except Exception as e:
                emit(done, count, f"Loi 1 video: {str(e)[:200]}")
    emit(count, count, f"HOAN TAT: {len(results)} video tai {out_dir}")
    return results


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="San xuat video hang loat")
    ap.add_argument("--pool", default=str(ROOT / "input" / "bodies"))
    ap.add_argument("--music", default=str(ROOT / "input" / "music"))
    ap.add_argument("--out", default=str(ROOT / "output" / "batch"))
    ap.add_argument("--count", type=int, default=20)
    ap.add_argument("--clips", type=int, default=3)
    ap.add_argument("--cut", type=float, default=None)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--mode", default="pool", choices=["pool", "funnel"])
    ap.add_argument("--hooks", default=str(ROOT / "input" / "hooks"))
    ap.add_argument("--ctas", default=str(ROOT / "input" / "ctas"))
    ap.add_argument("--texts", default=str(ROOT / "input" / "texts.txt"))
    ap.add_argument("--logo", default=None)
    ap.add_argument("--gpu", action="store_true")
    ap.add_argument("--random-seg", action="store_true", help="cat doan ngau nhien khac nhau")
    ap.add_argument("--transition", default="none", help="hieu ung chuyen canh: none/fade/dissolve/slideleft/random...")
    ap.add_argument("--trans-dur", type=float, default=0.5, help="do dai chuyen canh (giay)")
    ap.add_argument("--no-music", action="store_true")
    a = ap.parse_args()
    produce_batch(
        a.pool, a.out, music_dir=None if a.no_music else a.music,
        count=a.count, clips_per_video=a.clips, per_clip_seconds=a.cut,
        workers=a.workers, mode=a.mode, hook_dir=a.hooks, cta_dir=a.ctas,
        texts=a.texts if Path(a.texts).is_file() else None,
        logo=a.logo, gpu=a.gpu, random_segment=a.random_seg,
        transition=a.transition, trans_dur=a.trans_dur,
        progress=lambda d, t, m: print(f"[{d}/{t}] {m}"),
    )
