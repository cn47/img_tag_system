#!/bin/bash
set -e

# 現在のスクリプトのパスから、プロジェクトルートを推定
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

MODEL_DIR="$PROJECT_ROOT/data/model"
METADATA_URL="https://huggingface.co/cn47/camie-tagger-v2/resolve/main/camie-tagger-v2-metadata.json"
ONNX_URL="https://huggingface.co/cn47/camie-tagger-v2/resolve/main/camie-tagger-v2.onnx"

# modelディレクトリがなければ作成
mkdir -p "$MODEL_DIR"

# メタデータ
if [ ! -f "$MODEL_DIR/camie-tagger-v2-metadata.json" ]; then
  echo "Downloading metadata..."
  curl -L -o "$MODEL_DIR/camie-tagger-v2-metadata.json" "$METADATA_URL"
else
  echo "Metadata already exists. Skipping."
fi

# ONNXモデル
if [ ! -f "$MODEL_DIR/camie-tagger-v2.onnx" ]; then
  echo "Downloading ONNX model..."
  curl -L -o "$MODEL_DIR/camie-tagger-v2.onnx" "$ONNX_URL"
else
  echo "ONNX model already exists. Skipping."
fi

echo "✅ Setup complete."
