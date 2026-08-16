# Algoritmo Evolutivo de Polígonos

## Descripción

Este proyecto implementa un algoritmo de reconstrucción de imágenes mediante polígonos semitransparentes, utilizando la estrategia de optimización (1+1) hill-climbing. El sistema toma una imagen de referencia y genera una representación aproximada compuesta por triángulos o cuadriláteros, cuyos atributos (posición, color, opacidad) se ajustan iterativamente para minimizar el error cuadrático medio (MSE) respecto a la imagen original.

El proyecto está diseñado para ejecutarse en Windows, Linux y macOS, y cuenta con un sistema de checkpointing que permite interrumpir y reanudar la ejecución sin pérdida de progreso.

## Características

- Reconstrucción de imágenes mediante polígonos.
- Algoritmo de optimización (1+1) hill-climbing con mutación local.
- Renderizado local por región afectada para mejorar el rendimiento.
- Sistema de checkpointing automático para reanudar ejecuciones interrumpidas.

