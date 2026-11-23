
import ctypes
import os
import time
import random
import statistics

import numpy as np
from PIL import Image, ImageDraw


# --------------------------------------------------
# Configuración
# --------------------------------------------------

WIDTH = 256
HEIGHT = 256
POLYGON_COUNT = 100
RUNS = 30
WARMUP = 3

BACKGROUND = np.array([255, 255, 255], dtype=np.float32)


# --------------------------------------------------
# Cargar renderer C
# --------------------------------------------------

lib = ctypes.CDLL(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "renderer.so"))

FloatPtr = ctypes.POINTER(ctypes.c_float)
IntPtr = ctypes.POINTER(ctypes.c_int)
BytePtr = ctypes.POINTER(ctypes.c_uint8)

lib.render_region.argtypes = [
    FloatPtr,
    FloatPtr,
    IntPtr,
    IntPtr,
    BytePtr,
    BytePtr,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int
]

lib.render_region.restype = None


# --------------------------------------------------
# Generar escena reproducible
# --------------------------------------------------

rng = random.Random(42)

polygons = []
colors = []
alphas = []

for _ in range(POLYGON_COUNT):
    cx = rng.randint(20, WIDTH - 20)
    cy = rng.randint(20, HEIGHT - 20)

    radius = rng.randint(10, 45)
    count = rng.randint(3, 8)

    angles = sorted(
        rng.uniform(0, 2 * np.pi)
        for _ in range(count)
    )

    polygon = []

    for angle in angles:
        r = radius * rng.uniform(0.55, 1.0)

        x = int(cx + r * np.cos(angle))
        y = int(cy + r * np.sin(angle))

        x = max(0, min(WIDTH - 1, x))
        y = max(0, min(HEIGHT - 1, y))

        polygon.append((x, y))

    polygons.append(polygon)

    colors.append((
        rng.randint(0, 255),
        rng.randint(0, 255),
        rng.randint(0, 255)
    ))

    alphas.append(rng.randint(40, 220))


# --------------------------------------------------
# Preparar datos para C
# --------------------------------------------------

vertices_list = []
offsets_list = [0]

for polygon in polygons:
    for x, y in polygon:
        vertices_list.extend([x, y])

    offsets_list.append(
        offsets_list[-1] + len(polygon)
    )

vertices = np.ascontiguousarray(
    vertices_list, dtype=np.int32
)

offsets = np.ascontiguousarray(
    offsets_list, dtype=np.int32
)

colors_array = np.ascontiguousarray(
    np.array(colors).flatten(), dtype=np.uint8
)

alphas_array = np.ascontiguousarray(
    alphas, dtype=np.uint8
)

background = np.ascontiguousarray(
    BACKGROUND, dtype=np.float32
)


# --------------------------------------------------
# Render C
# --------------------------------------------------

def render_c():
    output = np.empty(
        (HEIGHT, WIDTH, 3),
        dtype=np.float32
    )

    lib.render_region(
        output.ctypes.data_as(FloatPtr),
        background.ctypes.data_as(FloatPtr),
        vertices.ctypes.data_as(IntPtr),
        offsets.ctypes.data_as(IntPtr),
        colors_array.ctypes.data_as(BytePtr),
        alphas_array.ctypes.data_as(BytePtr),
        POLYGON_COUNT,
        WIDTH,
        HEIGHT
    )

    return np.rint(output).astype(np.uint8)


# --------------------------------------------------
# Render Pillow
# --------------------------------------------------

def render_pillow():
    region = np.empty(
        (HEIGHT, WIDTH, 3),
        dtype=np.float32
    )

    region[:] = BACKGROUND

    for polygon, color, alpha in zip(
        polygons, colors, alphas
    ):
        layer = Image.new(
            "RGBA",
            (WIDTH, HEIGHT),
            (0, 0, 0, 0)
        )

        draw = ImageDraw.Draw(layer)

        draw.polygon(
            polygon,
            fill=(*color, alpha)
        )

        layer_array = np.asarray(
            layer,
            dtype=np.float32
        )

        a = layer_array[:, :, 3:4] / 255.0

        region = (
            layer_array[:, :, :3] * a
            + region * (1.0 - a)
        )

    return np.rint(region).astype(np.uint8)


# --------------------------------------------------
# Verificar equivalencia antes del benchmark
# --------------------------------------------------

print("\n========== BENCHMARK RENDERER ==========\n")

print("Resolución:", WIDTH, "x", HEIGHT)
print("Polígonos:", POLYGON_COUNT)
print("Ejecuciones:", RUNS)

print("\nComprobando equivalencia...")

image_c = render_c()
image_pillow = render_pillow()

different = np.any(image_c != image_pillow, axis=2)

different_count = np.count_nonzero(different)

print("Píxeles diferentes:", different_count)

if different_count != 0:
    print("ERROR: Los renderizadores no producen el mismo resultado.")
    raise SystemExit(1)

print("Equivalencia exacta confirmada.")


# --------------------------------------------------
# Calentamiento
# --------------------------------------------------

print("\nCalentando...")

for _ in range(WARMUP):
    render_c()
    render_pillow()


# --------------------------------------------------
# Medición
# --------------------------------------------------

times_c = []
times_pillow = []

print("\nMidiendo...")

for i in range(RUNS):
    start = time.perf_counter()
    render_c()
    end = time.perf_counter()

    times_c.append(end - start)

    start = time.perf_counter()
    render_pillow()
    end = time.perf_counter()

    times_pillow.append(end - start)

    print(f"Ejecución {i + 1}/{RUNS}")


# --------------------------------------------------
# Resultados
# --------------------------------------------------

median_c = statistics.median(times_c)
median_pillow = statistics.median(times_pillow)

speedup = median_pillow / median_c

print("\n========== RESULTADOS ==========\n")

print(f"C:")
print(f"  Mediana: {median_c * 1000:.3f} ms")
print(f"  Media:   {statistics.mean(times_c) * 1000:.3f} ms")

print(f"\nPillow:")
print(f"  Mediana: {median_pillow * 1000:.3f} ms")
print(f"  Media:   {statistics.mean(times_pillow) * 1000:.3f} ms")

print(f"\nSpeedup: {speedup:.2f}x")

print(
    f"\nReducción de tiempo: "
    f"{(1 - median_c / median_pillow) * 100:.2f}%"
)

print("\nBenchmark finalizado.")
