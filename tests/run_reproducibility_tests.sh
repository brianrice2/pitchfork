#!/usr/bin/env bash

PIPELINE_CONFIG="config/pipeline.yaml"
REPR_ACTUAL_DIR="tests/reproducibility-actual"
S3_BUCKET="s3://2021-msia423-rice-brian"

RAW_DATA_PATH="${REPR_ACTUAL_DIR}/raw_data.csv"
CLEANED_DATA_PATH="${REPR_ACTUAL_DIR}/cleaned_data.csv"
SAVED_MODEL_PATH="${REPR_ACTUAL_DIR}/trained_model.joblib"
SAVED_MODEL_PREDICTIONS_PATH="${REPR_ACTUAL_DIR}/cleaned_with_predictions.csv"


# Acquire raw data
python3 run.py load_data \
  --local_path "${RAW_DATA_PATH}" \
  --s3path "${S3_BUCKET}/${RAW_DATA_PATH}"

# Clean data
python3 run.py pipeline clean \
  --input "${RAW_DATA_PATH}" \
  --config "${PIPELINE_CONFIG}" \
  --output "${CLEANED_DATA_PATH}"

# Train model
python3 run.py pipeline model \
  --input "${CLEANED_DATA_PATH}" \
  --config "${PIPELINE_CONFIG}" \
  --output "${SAVED_MODEL_PATH}"

# Make predictions
python3 run.py pipeline predict \
  --input "${CLEANED_DATA_PATH}" \
  --model "${SAVED_MODEL_PATH}" \
  --config "${PIPELINE_CONFIG}" \
  --output "${SAVED_MODEL_PREDICTIONS_PATH}"

# Exactly compare pipeline artifacts
echo 'Comparing actual and expected results:'
diff -ru -x '.gitkeep' tests/reproducibility-actual/ tests/reproducibility-expected/
echo 'All done!'
