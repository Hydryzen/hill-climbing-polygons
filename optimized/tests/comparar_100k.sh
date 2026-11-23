
#!/bin/bash

set -e
set -o pipefail

# Directorios absolutos basados en la ubicación de este script
TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPTIMIZED_DIR="$(dirname "$TESTS_DIR")"
PROJECT_DIR="$(dirname "$OPTIMIZED_DIR")"

BASE="$TESTS_DIR/comparacion_100k"

mkdir -p "$BASE/original"
mkdir -p "$BASE/evolutivoC"

echo "=========================================="
echo "  COMPARACIÓN: 100000 ITERACIONES"
echo "=========================================="

echo ""
echo "1. EJECUTANDO ALGORITMO ORIGINAL"
echo ""

 /usr/bin/time -f 'Tiempo real: %e s' \
    -o "$BASE/original/tiempo.txt" \
    python3 "$OPTIMIZED_DIR/algoritmoevolutivo.py" \
        --attempts 100000 \
        --n 600 \
        --seed 42 \
        --out "$BASE/original/resultados" \
    2>&1 | tee "$BASE/original/log.txt"

echo ""
echo "2. EJECUTANDO ALGORITMO EVOLUTIVO C"
echo ""

 /usr/bin/time -f 'Tiempo real: %e s' \
    -o "$BASE/evolutivoC/tiempo.txt" \
    python3 "$OPTIMIZED_DIR/algoritmoevolutivoC.py" \
        --renderer c \
        --attempts 100000 \
        --n 600 \
        --seed 42 \
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
