#!/usr/bin/env bash

S3_BUCKET="s3://2021-msia423-rice-brian"
PIPELINE_CONFIG="config/pipeline.yaml"

python3 run.py pipeline clean \
  --input "${S3_BUCKET}/data/raw/P4KxSpotify.csv" \
  --config "${PIPELINE_CONFIG}" \
  --output "${S3_BUCKET}/data/cleaned/P4KxSpotify.csv"

python3 run.py pipeline model \
  --input "${S3_BUCKET}/data/cleaned/P4KxSpotify.csv" \
  --config "${PIPELINE_CONFIG}" \
  --output "${S3_BUCKET}/models/gbt_pipeline.joblib"

python3 run.py pipeline predict \
  --input "${S3_BUCKET}/data/cleaned/P4KxSpotify.csv" \
  --model "${S3_BUCKET}/models/gbt_pipeline.joblib" \
  --config "${PIPELINE_CONFIG}" \
  --output "${S3_BUCKET}/models/cleaned_with_predictions.csv"
