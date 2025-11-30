#!/bin/bash

current_dir=$(cd $(dirname $0); pwd)

#BASE_DIR=/mnt/c/Users/integ/OneDrive/Desktop/ # デスクトップ
BASE_DIR=/mnt/e/__整理中/画像整理中 # 外付け
TARGET_DIR_NAME=プリキュア

uv run python3 \
    ${current_dir}/batch_move_by_tag.py \
    --input_dir=${BASE_DIR}/${TARGET_DIR_NAME}/ \
    --output_dir=${BASE_DIR}/TAGGING_RESULT_test \
    --mode=copy

