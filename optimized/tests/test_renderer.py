
import ctypes
import os
import numpy as np
from PIL import Image, ImageDraw

# --------------------------------------------------
# Cargar biblioteca C
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

WIDTH = 100
HEIGHT = 100

BACKGROUND = np.array([255, 255, 255], dtype=np.float32)


# --------------------------------------------------
# Ejecutar renderer C
# --------------------------------------------------

def render_c(polygons, colors, alphas):
    vertices_list = []
    offsets = [0]

    for polygon in polygons:
        for x, y in polygon:
            vertices_list.extend([x, y])

        offsets.append(offsets[-1] + len(polygon))

    vertices = np.ascontiguousarray(vertices_list, dtype=np.int32)
    offsets = np.ascontiguousarray(offsets, dtype=np.int32)
    colors = np.ascontiguousarray(colors, dtype=np.uint8)
    alphas = np.ascontiguousarray(alphas, dtype=np.uint8)

    output = np.zeros((HEIGHT, WIDTH, 3), dtype=np.float32)

    lib.render_region(
        output.ctypes.data_as(FloatPtr),
        BACKGROUND.ctypes.data_as(FloatPtr),
        vertices.ctypes.data_as(IntPtr),
        offsets.ctypes.data_as(IntPtr),
        colors.ctypes.data_as(BytePtr),
        alphas.ctypes.data_as(BytePtr),
        len(polygons),
        WIDTH,
        HEIGHT
    )

    return np.rint(output).astype(np.uint8)


# --------------------------------------------------
# Referencia Python: comportamiento original
# --------------------------------------------------

def render_reference(polygons, colors, alphas):
    region = np.empty((HEIGHT, WIDTH, 3), dtype=np.float32)
    region[:] = BACKGROUND

    for polygon, color, alpha in zip(polygons, colors, alphas):
        layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)

        draw.polygon(
            polygon,
            fill=(*color, alpha)
        )

        layer_array = np.asarray(layer, dtype=np.float32)

        a = layer_array[:, :, 3:4] / 255.0

        region = (
            layer_array[:, :, :3] * a
            + region * (1.0 - a)
        )

    return np.rint(region).astype(np.uint8)


# --------------------------------------------------
# Casos de prueba
# --------------------------------------------------

tests = [
    {
        "name": "triangulo",
        "polygons": [
            [(10, 10), (90, 10), (50, 90)]
        ],
        "colors": [(255, 0, 0)],
        "alphas": [128]
    },

    {
        "name": "poligono_irregular",
        "polygons": [
            [
                (15, 10),
                (80, 15),
                (65, 40),
                (90, 65),
                (50, 85),
                (30, 60),
                (10, 45)
            ]
        ],
        "colors": [(30, 100, 230)],
        "alphas": [170]
    },

    {
        "name": "superposicion",
        "polygons": [
            [
                (10, 10),
                (75, 15),
                (50, 75)
            ],
            [
                (30, 25),
                (90, 30),
                (80, 90),
                (20, 80)
            ],
            [
                (15, 60),
                (45, 20),
                (85, 65),
                (55, 90)
            ]
        ],
        "colors": [
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255)
        ],
        "alphas": [128, 100, 180]
    }
]


# --------------------------------------------------
# Ejecutar comparaciones
# --------------------------------------------------

print("\n========== PRUEBAS DEL RENDERER ==========\n")

for test in tests:
    name = test["name"]
    polygons = test["polygons"]
    colors = test["colors"]
    alphas = test["alphas"]

    c_image = render_c(polygons, colors, alphas)

    reference = render_reference(
        polygons,
        colors,
        alphas
    )

    different = np.any(c_image != reference, axis=2)

    count = np.count_nonzero(different)
    percentage = count / (WIDTH * HEIGHT) * 100

    max_difference = np.max(
        np.abs(
            c_image.astype(np.int16)
            - reference.astype(np.int16)
        )
    )

    print(f"Prueba: {name}")
    print(f"Píxeles diferentes: {count}")
    print(f"Diferencia porcentual: {percentage:.4f}%")
    print(f"Diferencia máxima por canal: {max_difference}")

    if count == 0:
        print("RESULTADO: CORRECTO")
    else:
        print("RESULTADO: DIFERENCIAS")

        ys, xs = np.where(different)

        print("Primeras 10 diferencias:")

        for y, x in zip(ys[:10], xs[:10]):
            print(
                f"({x}, {y}) | "
                f"C: {c_image[y, x]} | "
                f"Pillow: {reference[y, x]}"
            )

    Image.fromarray(c_image).save(f"test_{name}_c.png")
    Image.fromarray(reference).save(f"test_{name}_pillow.png")

    print("-" * 40)

print("\nPruebas finalizadas.")
