#!/usr/bin/env bash

python3 run.py create_db
python3 run.py ingest_dataset
python3 app.py
