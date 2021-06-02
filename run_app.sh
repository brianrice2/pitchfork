#!/usr/bin/env bash

S3_BUCKET="s3://2021-msia423-rice-brian"

# Create empty database
python3 run.py create_db

# Run data cleaning and modeling pipeline
./run_pipeline.sh

# Add cleaned data to database
python3 run.py ingest_dataset -f "${S3_BUCKET}/data/cleaned/P4KxSpotify.csv"

# Run Flask web app
python3 app.py
