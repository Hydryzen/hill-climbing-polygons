# Polygon Evolution Algorithm

<img width="425" height="686" alt="Evolution result" src="https://github.com/user-attachments/assets/f9ade39e-fbb0-426a-a5e2-7881c9077855" />

## Description

This project implements an image reconstruction algorithm using semi-transparent polygons and a **(1+1) Hill-Climbing optimization strategy**.

The algorithm takes a reference image and generates an approximate representation composed of triangles and quadrilaterals. Polygon attributes such as position, color, and opacity are iteratively modified to minimize the Mean Squared Error (MSE) between the generated image and the original.

The project includes two implementations:

- **Python:** Original implementation using Pillow for image rendering.
- **C Renderer:** Optimized implementation using a custom C rendering engine integrated with Python through `ctypes`.

## Results

The following results were obtained using a custom reference image created by the author.

| Original image | Attempt 5,000 | Attempt 2,000,000 |
| :---: | :---: | :---: |
| <img width="200" alt="Original image" src="https://github.com/user-attachments/assets/fe535532-81c7-4d38-b320-d0d65774b43b" /> | <img width="200" alt="Attempt 5000" src="https://github.com/user-attachments/assets/c8caee4f-605b-43de-a635-ba24ade53564" /> | <img width="200" alt="Attempt 2000000" src="https://github.com/user-attachments/assets/0633f889-f62d-4e1c-9ff0-bf9afee54509" /> |

## Technical Architecture

```text
hill-climbing-polygons/
│
├── hill_climbing.py.py
├── ruka_referencia.png
├── requirements.txt
├── README.md
│
└── optimized/
    ├── algoritmoevolutivo.py
    ├── algoritmoevolutivoC.py
    ├── renderer.c
    │
    └── tests/
        ├── test_renderer.py
        ├── benchmark_renderer.py
        └── comparar_100k.sh
```

The `optimized/` directory contains the optimized implementations and the custom C renderer.

The `tests/` directory contains rendering equivalence tests and performance benchmarks.

## Design Decisions

### Why (1+1) Hill-Climbing instead of a Genetic Algorithm?

The (1+1) Hill-Climbing strategy maintains a single candidate solution and iteratively accepts mutations that improve the objective function.

This keeps the implementation lightweight and reduces memory overhead while providing a straightforward optimization process.

### Local Region Rendering

Recalculating the MSE of the entire image after every mutation is computationally expensive.

To reduce this cost, I implemented a local region rendering approach: only the bounding box affected by a mutated polygon is recalculated.

This avoids unnecessary full-image rendering operations and significantly improves computational efficiency.

### C Renderer Integration

To further improve performance, I implemented a custom rendering engine in C and integrated it with Python using `ctypes`.

This allows the optimization logic to remain in Python while computationally intensive rendering operations are executed in compiled C code.

### Checkpointing

Long-running evolutionary processes need to preserve their progress.

The implementation includes an automatic checkpointing system that allows interrupted executions to resume without losing previously accumulated progress.

## Performance Benchmarks

Two different benchmarks were conducted to evaluate the optimization.

### 1. Complete Algorithm Comparison

Both implementations were evaluated using the same configuration:

- Attempts: 100,000
- Polygons: 600
- Random seed: 42

| Metric | Python | C Renderer |
| :--- | ---: | ---: |
| Execution time | 285.21 s | 116.40 s |
| Final MSE | 672.664 | 683.658 |
| Accepted mutations | 24,468 | 24,672 |

**Performance improvement:**

- 2.45× speedup.
- 59.2% reduction in execution time.
- Similar final reconstruction quality.

The implementations do not produce identical optimization trajectories, even with the same random seed. The final MSE difference is therefore reported rather than assuming identical behavior.

### 2. Isolated Renderer Benchmark

The rendering engines were also compared independently.

Configuration:

- Resolution: 256 × 256.
- Polygons: 100.
- Executions: 30.
- Exact pixel equivalence verified before timing.

| Metric | C | Pillow |
| :--- | ---: | ---: |
| Median execution time | 0.948 ms | 152.352 ms |
| Mean execution time | 0.915 ms | 142.690 ms |

**Results:**

- 160.64× speedup.
- 99.38% reduction in rendering time.
- Exact pixel equivalence in the tested configuration.

These results correspond to the isolated renderer benchmark, not the complete evolutionary algorithm.

## Installation

Clone the repository:

```bash
git clone https://github.com/Hydryzen/hill-climbing-polygons.git
cd hill-climbing-polygons
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

**Prerequisites:**

- Python 3.8+
- NumPy >= 1.24.0
- Pillow >= 10.0.0
- GCC (required for compiling the C renderer)

## Usage

### Python Implementation

Run the original Python implementation:

```bash
python3 optimized/algoritmoevolutivo.py \
    --attempts 100000 \
    --n 600 \
    --seed 42 \
    --out results/python
```

### C Renderer Implementation

Compile the C renderer:

```bash
gcc -O3 -shared -fPIC optimized/renderer.c \
    -o optimized/renderer.so -lm
```

Run the optimized implementation:

```bash
python3 optimized/algoritmoevolutivoC.py \
    --renderer c \
    --attempts 100000 \
    --n 600 \
    --seed 42 \
    --out results/c
```

The reference image defaults to `ruka_referencia.png` in the project root.

## Testing

Run the renderer equivalence tests:

```bash
python3 optimized/tests/test_renderer.py
```

Run the isolated renderer benchmark:

```bash
python3 optimized/tests/benchmark_renderer.py
```

Run the complete 100,000-attempt comparison:

```bash
bash optimized/tests/comparar_100k.sh
```

The C renderer tests compare the output against Pillow to verify pixel-level equivalence in the tested cases.

