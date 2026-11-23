#!/bin/bash

set -e
set -o pipefail

# Directorios absolutos basados en la ubicación de este script
TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$TESTS_DIR")" # Subimos un nivel para encontrar hill_climbing.py

BASE="$TESTS_DIR/comparacion_100k"

mkdir -p "$BASE/original"
mkdir -p "$BASE/evolutivoC"

echo "=========================================="
echo "  COMPARACIÓN: 100000 ITERACIONES"
echo "=========================================="

# Imagen objetivo (asegúrate de que exista en PROJECT_DIR)
TARGET_IMAGE="$PROJECT_DIR/ruka_referencia.png"

echo ""
echo "1. EJECUTANDO ALGORITMO ORIGINAL (hill_climbing.py)"
echo ""

/usr/bin/time -f 'Tiempo real: %e s' \
    -o "$BASE/original/tiempo.txt" \
    python3 "$PROJECT_DIR/hill_climbing.py" \
        "$TARGET_IMAGE" \
        --attempts 100000 \
        --n 600 \
        --seed 42 \
        --shape triangle \
        --out "$BASE/original/resultados" \
    2>&1 | tee "$BASE/original/log.txt"

echo ""
echo "2. EJECUTANDO ALGORITMO EVOLUTIVO C (optimized/algoritmoevolutivoC.py)"
echo ""

/usr/bin/time -f 'Tiempo real: %e s' \
    -o "$BASE/evolutivoC/tiempo.txt" \
    python3 "$PROJECT_DIR/optimized/algoritmoevolutivoC.py" \
        "$TARGET_IMAGE" \
        --renderer c \
        --attempts 100000 \
        --n 600 \
        --seed 42 \
        --shape triangle \
        --out "$BASE/evolutivoC/resultados" \
    2>&1 | tee "$BASE/evolutivoC/log.txt"

echo ""
echo "=========================================="
echo "  COMPARACIÓN FINALIZADA"
echo "=========================================="

echo ""
echo "ORIGINAL:"
cat "$BASE/original/tiempo.txt"

echo ""
echo "EVOLUTIVO C:"
cat "$BASE/evolutivoC/tiempo.txt"

echo ""
echo "Archivos guardados en: $BASE/"
