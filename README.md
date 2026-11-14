# Polygon Evolution Algorithm

<img width="425" height="686" alt="evolucion" src="https://github.com/user-attachments/assets/f9ade39e-fbb0-426a-a5e2-7881c9077855" />

## Description

This project implements an image reconstruction algorithm using semi-transparent polygons, with a (1+1) hill-climbing optimization strategy. The system takes a reference image and generates an approximate representation composed of triangles or quadrilaterals, whose attributes (position, color, opacity) are iteratively adjusted to minimize the Mean Squared Error (MSE) relative to the original image.

## Design Decisions

* **Why (1+1) Hill-Climbing instead of a Genetic Algorithm?** To keep the implementation lightweight and reduce memory overhead, while still achieving excellent local optimization.
* **Why Local Region Rendering?** Calculating the MSE of the entire image for every single mutation is computationally expensive. I implemented a local region rendering approach, which only recalculates the MSE for the bounding box affected by the mutated polygon. This drastically improved the iterations-per-second rate.
* **Checkpointing:** Evolutionary algorithms take a long time. I built an automatic checkpointing system so long-running executions can be safely interrupted and resumed without losing progress.

## Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/Hydryzen/hill-climbing-polygons.git
cd hill-climbing-polygons
pip install -r requirements.txt
```

**Prerequisites:** Python 3.8+, `numpy >= 1.24.0`, and `Pillow >= 10.0.0`.

### Usage

Run the algorithm using the following command (update the script name and arguments if your implementation differs):

```bash
python algoritmoevolutivo.py --input reference_image.jpg --iterations 2000000
```

## Results

The following results were obtained using a custom reference image created by the author, showing the evolution of the algorithm over iterations.

| Original image | Attempt 5,000 | Attempt 2,000,000 |
| :---: | :---: | :---: |
| <img width="200" alt="ruka_referencia" src="https://github.com/user-attachments/assets/fe535532-81c7-4d38-b320-d0d65774b43b" /> | <img width="200" alt="snap_005000" src="https://github.com/user-attachments/assets/c8caee4f-605b-43de-a635-ba24ade53564" /> | <img width="200" alt="snap_2000000" src="https://github.com/user-attachments/assets/0633f889-f62d-4e1c-9ff0-bf9afee54509" /> |


