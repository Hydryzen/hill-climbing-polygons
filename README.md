# Polygon Evolution Algorithm

## Description

This project implements an image reconstruction algorithm using semi-transparent polygons, with a (1+1) hill-climbing optimization strategy. The system takes a reference image and generates an approximate representation composed of triangles or quadrilaterals, whose attributes (position, color, opacity) are iteratively adjusted to minimize the Mean Squared Error (MSE) relative to the original image.

The project is designed to run on Windows, Linux and macOS, and includes a checkpointing system that allows interrupting and resuming execution without losing progress.

## Features

- Image reconstruction using polygons.
- (1+1) hill-climbing optimization algorithm with local mutation.
- Local region rendering to improve performance.
- Automatic checkpointing system to resume interrupted executions.

## Dependencies

The project requires the following Python libraries:

- `numpy >= 1.24.0`
- `Pillow >= 10.0.0`

## Results

Evolution of the algorithm over iterations:

Attempt number 5000:
<img width="425" height="686" alt="snap_005000" src="https://github.com/user-attachments/assets/c8caee4f-605b-43de-a635-ba24ade53564" />

Attempt number 2000000:
<img width="425" height="686" alt="snap_2000000" src="https://github.com/user-attachments/assets/0633f889-f62d-4e1c-9ff0-bf9afee54509" />

Evolution:
<img width="425" height="686" alt="evolucion" src="https://github.com/user-attachments/assets/f9ade39e-fbb0-426a-a5e2-7881c9077855" />
