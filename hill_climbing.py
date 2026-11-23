#!/usr/bin/env python3
"""
Reconstrucción de imagen con polígonos — (1+1) hill-climbing con
re-renderizado LOCAL (solo el bounding box afectado).

  - Checkpoint real: guarda el genoma (lista de polígonos) cada N
    intentos en un .pkl y puede reanudar si el proceso muere.
  - Guarda al recibir Ctrl+C / SIGTERM, no solo cada N intentos.
"""
import argparse
import os
import pickle
import random
import signal
import sys
import time
import numpy as np
from PIL import Image, ImageDraw


class Poly:
    __slots__ = ("pts", "color", "alpha", "kind")

    def __init__(self, pts, color, alpha, kind):
        self.pts = pts
        self.color = color
        self.alpha = alpha
        self.kind = kind

    def bbox(self, w, h, pad=0):
        xs = [p[0] for p in self.pts]
        ys = [p[1] for p in self.pts]
        x0 = max(0, min(xs) - pad)
        y0 = max(0, min(ys) - pad)
        x1 = min(w, max(xs) + pad + 1)
        y1 = min(h, max(ys) + pad + 1)
        return x0, y0, x1, y1

    def clone(self):
        return Poly(list(self.pts), self.color, self.alpha, self.kind)


def random_poly(w, h, target_arr, kind="triangle"):
    n_pts = {"triangle": 3, "quad": 4}.get(kind, 3)
    cx, cy = random.randint(0, w - 1), random.randint(0, h - 1)
    size = random.randint(max(4, w // 25), max(8, w // 8))
    pts = [
        (
            min(w - 1, max(0, cx + random.randint(-size, size))),
            min(h - 1, max(0, cy + random.randint(-size, size))),
        )
        for _ in range(n_pts)
    ]
    color = tuple(int(c) for c in target_arr[cy, cx])
    alpha = random.randint(40, 180)
    return Poly(pts, color, alpha, kind)


class Canvas:
    def __init__(self, w, h, bg, target_arr, polys=None):
        self.w, self.h = w, h
        self.bg = np.array(bg, dtype=np.float32)
        self.target = target_arr.astype(np.float32)
        self.polys = polys or []
        # Renderiza el estado inicial completo UNA sola vez (barato:
        # pasa una vez al arrancar o al reanudar, nunca más).
        self.canvas = self._render_region(0, 0, w, h, self.polys)
        diff = self.canvas - self.target
        self.total_sq_err = float(np.sum(diff * diff))

    def _render_region(self, x0, y0, x1, y1, polys):
        rw, rh = x1 - x0, y1 - y0
        if rw <= 0 or rh <= 0:
            return None
        region = np.tile(self.bg, (rh, rw, 1)).astype(np.float32)
        for p in polys:
            pb0x, pb0y, pb1x, pb1y = p.bbox(self.w, self.h)
            if pb1x <= x0 or pb0x >= x1 or pb1y <= y0 or pb0y >= y1:
                continue
            layer = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
            d = ImageDraw.Draw(layer)
            shifted = [(px - x0, py - y0) for px, py in p.pts]
            d.polygon(shifted, fill=(*p.color, p.alpha))
            larr = np.array(layer, dtype=np.float32)
            a = larr[:, :, 3:4] / 255.0
            region = larr[:, :, :3] * a + region * (1 - a)
        return region

    def try_mutation(self, mutate_fn):
        new_polys, (x0, y0, x1, y1) = mutate_fn(self.polys)
        old_region = self.canvas[y0:y1, x0:x1, :]
        target_region = self.target[y0:y1, x0:x1, :]
        old_err = float(np.sum((old_region - target_region) ** 2))

        new_region = self._render_region(x0, y0, x1, y1, new_polys)
        new_err = float(np.sum((new_region - target_region) ** 2))

        delta = new_err - old_err
        return delta, new_region, (x0, y0, x1, y1), new_polys

    def apply(self, new_region, bbox, new_polys, delta):
        x0, y0, x1, y1 = bbox
        self.canvas[y0:y1, x0:x1, :] = new_region
        self.polys = new_polys
        self.total_sq_err += delta

    def to_image(self):
        return Image.fromarray(np.clip(self.canvas, 0, 255).astype(np.uint8))


def mse(canvas):
    return canvas.total_sq_err / (canvas.w * canvas.h * 3)


def save_checkpoint(path, polys, attempt, seed, bg, w, h):
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        pickle.dump({
            "polys": polys, "attempt": attempt, "seed": seed,
            "bg": bg, "w": w, "h": h,
        }, f)
    os.replace(tmp, path)  # escritura atómica: no corrompe si se corta la luz/proceso


def load_checkpoint(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Checkpoint corrupto, se ignora ({e})")
        return None


def run(target_path, out_dir, n_polys=600, attempts=200000, shape="triangle",
        seed=42, snapshot_every=5000, checkpoint_every=1000,
        checkpoint_path=None):
    os.makedirs(out_dir, exist_ok=True)
    checkpoint_path = checkpoint_path or os.path.join(out_dir, "checkpoint.pkl")

    target_img = Image.open(target_path).convert("RGB")
    w, h = target_img.size
    target_arr = np.array(target_img)

    ckpt = load_checkpoint(checkpoint_path)
    if ckpt and ckpt["w"] == w and ckpt["h"] == h:
        random.seed(ckpt["seed"])
        np.random.seed(ckpt["seed"])
        bg = ckpt["bg"]
        canvas = Canvas(w, h, bg, target_arr, polys=ckpt["polys"])
        start_attempt = ckpt["attempt"]
        print(f"Reanudando desde intento {start_attempt} "
              f"({len(canvas.polys)} polígonos ya aceptados)")
    else:
        random.seed(seed)
        np.random.seed(seed)
        bg = tuple(int(c) for c in target_arr.reshape(-1, 3).mean(axis=0))
        canvas = Canvas(w, h, bg, target_arr)
        start_attempt = 0
        print(f"Empezando desde cero. Imagen: {w}x{h}")

    # Guardar checkpoint si llega Ctrl+C o el sistema manda SIGTERM
    # (esto último es justo lo que hace Android/Termux al matar el proceso)
    def handle_signal(signum, frame):
        print(f"\nSeñal {signum} recibida — guardando checkpoint antes de salir...")
        save_checkpoint(checkpoint_path, canvas.polys, attempt, seed, bg, w, h)
        canvas.to_image().save(f"{out_dir}/final_interrumpido.png")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    t0 = time.time()
    accepted = 0
    poly_budget = n_polys
    attempt = start_attempt

    while attempt < attempts:
        attempt += 1
        polys = canvas.polys
        r = random.random()

        if len(polys) < poly_budget and r < 0.5:
            def mut(plist, _shape=shape):
                np_ = random_poly(w, h, target_arr, _shape)
                bbox = np_.bbox(w, h)
                return plist + [np_], bbox
        elif polys and r < 0.85:
            idx = random.randrange(len(polys))

            def mut(plist, _idx=idx):
                old = plist[_idx]
                new = old.clone()
                choice = random.random()
                if choice < 0.5:
                    new.pts = [
                        (min(w - 1, max(0, x + random.randint(-4, 4))),
                         min(h - 1, max(0, y + random.randint(-4, 4))))
                        for x, y in new.pts
                    ]
                elif choice < 0.8:
                    r_, g_, b_ = new.color
                    new.color = (
                        min(255, max(0, r_ + random.randint(-15, 15))),
                        min(255, max(0, g_ + random.randint(-15, 15))),
                        min(255, max(0, b_ + random.randint(-15, 15))),
                    )
                else:
                    new.alpha = min(255, max(15, new.alpha + random.randint(-20, 20)))
                ob0 = old.bbox(w, h)
                nb0 = new.bbox(w, h)
                bbox = (min(ob0[0], nb0[0]), min(ob0[1], nb0[1]),
                        max(ob0[2], nb0[2]), max(ob0[3], nb0[3]))
                new_list = list(plist)
                new_list[_idx] = new
                return new_list, bbox
        elif polys:
            idx = random.randrange(len(polys))

            def mut(plist, _idx=idx):
                new_list = list(plist)
                p = new_list.pop(_idx)
                new_pos = random.randrange(len(new_list) + 1)
                new_list.insert(new_pos, p)
                bbox = p.bbox(w, h)
                return new_list, bbox
        else:
            continue

        delta, new_region, bbox, new_polys = canvas.try_mutation(mut)
        if delta < 0:
            canvas.apply(new_region, bbox, new_polys, delta)
            accepted += 1

        if attempt % checkpoint_every == 0:
            save_checkpoint(checkpoint_path, canvas.polys, attempt, seed, bg, w, h)

        if attempt % snapshot_every == 0:
            elapsed = time.time() - t0
            cur_mse = mse(canvas)
            print(f"intento {attempt:6d}/{attempts} | polígonos {len(canvas.polys):3d} "
                  f"| MSE {cur_mse:8.3f} | aceptados {accepted:5d} "
                  f"({100*accepted/(attempt-start_attempt+1):.1f}%) | {elapsed:.1f}s")
            canvas.to_image().save(f"{out_dir}/snap_{attempt:06d}.png")

    save_checkpoint(checkpoint_path, canvas.polys, attempt, seed, bg, w, h)
    canvas.to_image().save(f"{out_dir}/final.png")
    print(f"\nCompletado en {time.time()-t0:.1f}s. MSE final: {mse(canvas):.3f}, "
          f"polígonos: {len(canvas.polys)}")
    return canvas


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("target", default="C:/Users/user/Desktop/python/algoritmo evolutivo/ruka_referencia.png", nargs="?")
    ap.add_argument("--out", default="resultados_ruka")
    ap.add_argument("--n", type=int, default=600, help="máximo de polígonos")
    ap.add_argument("--attempts", type=int, default=2000000)
    ap.add_argument("--shape", default="triangle", choices=["triangle", "quad"])
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--checkpoint-every", type=int, default=1000)
    args = ap.parse_args()
    run(args.target, args.out, args.n, args.attempts, args.shape, args.seed,
        checkpoint_every=args.checkpoint_every)

