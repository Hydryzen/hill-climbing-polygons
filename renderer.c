
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define ROUND_UP(f) \
    ((int)((f) >= 0.0 ? floor((f) + 0.5F) : -floor(fabs(f) + 0.5F)))

#define ROUND_DOWN(f) \
    ((int)((f) >= 0.0 ? ceil((f) - 0.5F) : -ceil(fabs(f) - 0.5F)))

typedef struct {
    int d;
    int x0, y0;
    int xmin, ymin, xmax, ymax;
    float dx;
} Edge;

static int x_compare(const void *a, const void *b)
{
    float diff = *(const float *)a - *(const float *)b;
    return (diff < 0.0f) ? -1 : (diff > 0.0f) ? 1 : 0;
}

static void add_edge(Edge *e, int x0, int y0, int x1, int y1)
{
    e->xmin = (x0 <= x1) ? x0 : x1;
    e->xmax = (x0 <= x1) ? x1 : x0;

    e->ymin = (y0 <= y1) ? y0 : y1;
    e->ymax = (y0 <= y1) ? y1 : y0;

    if (y0 == y1) {
        e->d = 0;
        e->dx = 0.0f;
    } else {
        e->dx = (float)(x1 - x0) / (float)(y1 - y0);
        e->d = (y0 == e->ymin) ? 1 : -1;
    }

    e->x0 = x0;
    e->y0 = y0;
}

static void mark_horizontal(
    uint8_t *mask,
    int width,
    int height,
    int x0,
    int y,
    int x1
)
{
    if (y < 0 || y >= height) return;

    if (x0 < 0) x0 = 0;
    if (x1 >= width) x1 = width - 1;

    if (x0 > x1) return;

    memset(mask + y * width + x0, 1, (size_t)(x1 - x0 + 1));
}

static void mark_interval(
    uint8_t *mask,
    int width,
    int height,
    int x0,
    int y,
    int x1
)
{
    if (y < 0 || y >= height) return;

    if (x0 < 0) x0 = 0;
    if (x1 >= width) x1 = width - 1;

    if (x0 > x1) return;

    memset(mask + y * width + x0, 1, (size_t)(x1 - x0 + 1));
}

static int rasterize_polygon(
    uint8_t *mask,
    int width,
    int height,
    const int *vertices,
    int count
)
{
    if (count < 3) return 0;

    Edge *edges = calloc((size_t)count, sizeof(Edge));
    if (!edges) return -1;

    int n = 0;

    // Construcción de aristas, incluyendo el cierre del polígono.
    for (int i = 0; i < count - 1; i++) {
        int x0 = vertices[i * 2];
        int y0 = vertices[i * 2 + 1];
        int x1 = vertices[i * 2 + 2];
        int y1 = vertices[i * 2 + 3];

        // Pillow une segmentos horizontales consecutivos
        // cuando avanzan en la misma dirección.
        if (y0 == y1 && i != 0 &&
            y0 == vertices[i * 2 - 1]) {

            Edge *last = &edges[n - 1];

            if (x1 > x0 && x0 > vertices[i * 2 - 2]) {
                last->xmax = x1;
                continue;
            }
            else if (x1 < x0 && x0 < vertices[i * 2 - 2]) {
                last->xmin = x1;
                continue;
            }
        }

        add_edge(&edges[n++], x0, y0, x1, y1);
    }

    int last = count - 1;

    if (vertices[last * 2] != vertices[0] ||
        vertices[last * 2 + 1] != vertices[1]) {

        add_edge(
            &edges[n++],
            vertices[last * 2],
            vertices[last * 2 + 1],
            vertices[0],
            vertices[1]
        );
    }

    int ymin = height - 1;
    int ymax = 0;

    // Pillow dibuja las aristas horizontales por separado.
    for (int i = 0; i < n; i++) {
        Edge *e = &edges[i];

        if (e->ymin < ymin) ymin = e->ymin;
        if (e->ymax > ymax) ymax = e->ymax;

        if (e->ymin == e->ymax) {
            mark_horizontal(
                mask, width, height,
                e->xmin, e->ymin, e->xmax
            );
        }
    }

    if (ymin < 0) ymin = 0;
    if (ymax >= height) ymax = height - 1;

    int edge_count = 0;

    for (int i = 0; i < n; i++) {
        if (edges[i].ymin != edges[i].ymax) {
            edge_count++;
        }
    }

    Edge **edge_table = calloc((size_t)edge_count, sizeof(Edge *));
    float *xx = calloc((size_t)edge_count * 2, sizeof(float));

    if (!edge_table || !xx) {
        free(edges);
        free(edge_table);
        free(xx);
        return -1;
    }

    int k = 0;

    for (int i = 0; i < n; i++) {
        if (edges[i].ymin != edges[i].ymax) {
            edge_table[k++] = &edges[i];
        }
    }

    // Rasterización scanline siguiendo polygon_generic de Pillow.
    for (int y = ymin; y <= ymax; y++) {
        int j = 0;

        for (int i = 0; i < edge_count; i++) {
            Edge *current = edge_table[i];

            if (y >= current->ymin && y <= current->ymax) {
                xx[j++] =
                    (y - current->y0) * current->dx + current->x0;

                if (y == current->ymax && y < ymax) {
                    xx[j] = xx[j - 1];
                    j++;
                }
                else if ((y == current->ymin || y == current->ymax) &&
                         current->dx != 0.0f) {

                    for (int q = 0; q < i; q++) {
                        Edge *other = edge_table[q];

                        if ((y != other->ymin && y != other->ymax) ||
                            other->dx == 0.0f) {
                            continue;
                        }

                        if (roundf(xx[j - 1]) ==
                            roundf(
                                (y - other->y0) * other->dx + other->x0
                            )) {

                            int offset = (y == current->ymax) ? -1 : 1;

                            float adjacent =
                                (y + offset - current->y0) *
                                current->dx + current->x0;

                            if (y + offset >= other->ymin &&
                                y + offset <= other->ymax) {

                                float adjacent_other =
                                    (y + offset - other->y0) *
                                    other->dx + other->x0;

                                if (xx[j - 1] > adjacent + 1.0f &&
                                    xx[j - 1] > adjacent_other + 1.0f) {

                                    xx[j - 1] =
                                        roundf(fmaxf(
                                            adjacent,
                                            adjacent_other
                                        )) + 1.0f;
                                }
                                else if (xx[j - 1] < adjacent - 1.0f &&
                                         xx[j - 1] < adjacent_other - 1.0f) {

                                    xx[j - 1] =
                                        roundf(fminf(
                                            adjacent,
                                            adjacent_other
                                        )) - 1.0f;
                                }

                                break;
                            }
                        }
                    }
                }
            }
        }

        qsort(xx, (size_t)j, sizeof(float), x_compare);

        for (int i = 1; i < j; i += 2) {
            int x_start = ROUND_UP(xx[i - 1]);
            int x_end = ROUND_DOWN(xx[i]);

            mark_interval(
                mask, width, height,
                x_start, y, x_end
            );
        }
    }

    free(xx);
    free(edge_table);
    free(edges);

    return 0;
}

void render_region(
    float *output,
    const float *background,
    const int *vertices,
    const int *offsets,
    const uint8_t *colors,
    const uint8_t *alphas,
    int polygon_count,
    int width,
    int height
)
{
    if (!output || !background || !vertices || !offsets ||
        !colors || !alphas || width <= 0 || height <= 0 ||
        polygon_count < 0) {
        return;
    }

    int pixels = width * height;

    for (int i = 0; i < pixels; i++) {
        output[i * 3]     = background[0];
        output[i * 3 + 1] = background[1];
        output[i * 3 + 2] = background[2];
    }

    uint8_t *mask = calloc((size_t)pixels, sizeof(uint8_t));
    if (!mask) return;

    for (int p = 0; p < polygon_count; p++) {
        int start = offsets[p];
        int count = offsets[p + 1] - start;

        if (count < 3) continue;

        memset(mask, 0, (size_t)pixels);

        if (rasterize_polygon(
            mask,
            width,
            height,
            &vertices[start * 2],
            count
        ) != 0) {
            continue;
        }

        float r = (float)colors[p * 3];
        float g = (float)colors[p * 3 + 1];
        float b = (float)colors[p * 3 + 2];
        float alpha = (float)alphas[p] / 255.0f;
        float inverse_alpha = 1.0f - alpha;

        // Cada píxel cubierto se mezcla exactamente una vez.
        for (int i = 0; i < pixels; i++) {
            if (!mask[i]) continue;

            int index = i * 3;

            output[index] =
                r * alpha + output[index] * inverse_alpha;

            output[index + 1] =
                g * alpha + output[index + 1] * inverse_alpha;

            output[index + 2] =
                b * alpha + output[index + 2] * inverse_alpha;
        }
    }

    free(mask);
}
