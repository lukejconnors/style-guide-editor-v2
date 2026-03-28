#!/usr/bin/env bash
#
# run.sh — Entry point for the style-rule copy editor pipeline.
#
# Prerequisites:
#   1. pip install -r requirements.txt
#   2. python -m spacy download en_core_web_sm
#   3. export OPENAI_API_KEY=your-key-here
#   4. python src/build_index.py  (one-time, generates data/rule_index.json)
#
# Usage:
#   ./run.sh
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data"
SRC_DIR="$SCRIPT_DIR/src"

INPUT_FILE="$DATA_DIR/input.json"
OUTPUT_FILE="$DATA_DIR/output.json"

if [[ ! -f "$INPUT_FILE" ]]; then
  echo "ERROR: Input file not found at $INPUT_FILE" >&2
  exit 1
fi

if [[ ! -f "$DATA_DIR/rule_index.json" ]]; then
  echo "ERROR: Rule index not found. Run 'python src/build_index.py' first." >&2
  exit 1
fi

echo "=== Style Rule Copy Editor ==="
echo "Input:  $INPUT_FILE"
echo "Output: $OUTPUT_FILE"
echo ""

cd "$SCRIPT_DIR"
python "$SRC_DIR/main.py" --input "$INPUT_FILE" --output "$OUTPUT_FILE"
