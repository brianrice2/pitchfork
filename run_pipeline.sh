#!/usr/bin/env bash

PIPELINE_CONFIG="config/pipeline.yaml"
S3_BUCKET="s3://2021-msia423-rice-brian"
RAW_DATA_PATH="data/raw/P4KxSpotify.csv"
CLEANED_DATA_PATH="data/cleaned/P4KxSpotify.csv"
SAVED_MODEL_PATH="models/gbt_pipeline.joblib"
MODEL_PREDICTIONS_PATH="models/cleaned_with_predictions.csv"


python3 run.py pipeline clean \
  --input "${S3_BUCKET}/${RAW_DATA_PATH}" \
  --config "${PIPELINE_CONFIG}" \
  --output "${S3_BUCKET}/${CLEANED_DATA_PATH}"

python3 run.py pipeline model \
  --input "${S3_BUCKET}/${CLEANED_DATA_PATH}" \
  --config "${PIPELINE_CONFIG}" \
  --output "${S3_BUCKET}/${SAVED_MODEL_PATH}"

python3 run.py pipeline predict \
  --input "${S3_BUCKET}//${CLEANED_DATA_PATH}" \
  --model "${S3_BUCKET}/${SAVED_MODEL_PATH}" \
  --config "${PIPELINE_CONFIG}" \
  --output "${S3_BUCKET}/${MODEL_PREDICTIONS_PATH}"
