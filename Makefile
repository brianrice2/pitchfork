.PHONY: help raw_data cleaned_data model pipeline predictions empty_database ingest_dataset app reproducibility_tests cleanup

PIPELINE_CONFIG="config/pipeline.yaml"
S3_BUCKET="s3://2021-msia423-rice-brian"
RAW_DATA_PATH="data/raw/P4KxSpotify.csv"
CLEANED_DATA_PATH="data/cleaned/P4KxSpotify.csv"
SAVED_MODEL_PATH="models/gbt_pipeline.joblib"
SAVED_MODEL_PREDICTIONS_PATH="models/predictions.csv"
SAVED_MODEL_PERFORMANCE_PATH="models/performance_report.csv"


.DEFAULT: help
help:
	@echo 'make raw_data'
	@echo '       Acquire raw data'
	@echo 'make cleaned_data'
	@echo '       Clean data for modeling'
	@echo 'make model'
	@echo '       Train a model pipeline'
	@echo 'make pipeline'
	@echo '       Clean data and train a model'
	@echo 'make predictions'
	@echo '       Make predictions on an input dataset'
	@echo 'make empty_database'
	@echo '       Create an empty MySQL/SQLite database'
	@echo 'make ingest_dataset'
	@echo '       Add albums from file into database'
	@echo 'make app'
	@echo '       Clean data, model, create and populate DB, and run web app'
	@echo 'make reproducibility_tests'
	@echo '       Run additional reproducibility tests'
	@echo 'make cleanup'
	@echo '       Remove artifacts from data/, models/, and tests/reproducibility-actual/'


# Dependencies don't work with S3, so these aren't included and directives are phony
data/raw/P4KxSpotify.csv:
	python3 run.py load_data \
		--local_path "${RAW_DATA_PATH}" \
		--s3path "${S3_BUCKET}/${RAW_DATA_PATH}" # A local copy is saved by default as an intermediate step before uploading to S3

raw_data: data/raw/P4KxSpotify.csv

data/cleaned/P4KxSpotify.csv: data/raw/P4KxSpotify.csv config/pipeline.yaml
	python3 run.py pipeline clean \
		--input "${S3_BUCKET}/${RAW_DATA_PATH}" \
		--config "${PIPELINE_CONFIG}" \
		--output "${S3_BUCKET}/${CLEANED_DATA_PATH}" \
		--local_copy "${CLEANED_DATA_PATH}"

cleaned_data: data/cleaned/P4KxSpotify.csv

models/gbt_pipeline.joblib: data/cleaned/P4KxSpotify.csv config/pipeline.yaml
	python3 run.py pipeline model \
		--input "${S3_BUCKET}/${CLEANED_DATA_PATH}" \
		--config "${PIPELINE_CONFIG}" \
		--output "${S3_BUCKET}/${SAVED_MODEL_PATH}" # A local copy is saved by default due to the joblib file format

model: models/gbt_pipeline.joblib config/pipeline.yaml

pipeline: cleaned_data model

models/predictions.csv: models/gbt_pipeline.joblib data/cleaned/P4KxSpotify.csv config/pipeline.yaml
	python3 run.py pipeline predict \
		--input "${S3_BUCKET}/${CLEANED_DATA_PATH}" \
		--model "${S3_BUCKET}/${SAVED_MODEL_PATH}" \
		--config "${PIPELINE_CONFIG}" \
		--output "${S3_BUCKET}/${SAVED_MODEL_PREDICTIONS_PATH}" \
		--local_copy "${SAVED_MODEL_PREDICTIONS_PATH}"

predictions: models/predictions.csv

models/performance_report.csv: models/predictions.csv
	python3 run.py pipeline evaluate \
		--input "${S3_BUCKET}/${SAVED_MODEL_PREDICTIONS_PATH}" \
		--config "${PIPELINE_CONFIG}" \
		--output "${S3_BUCKET}/${SAVED_MODEL_PERFORMANCE_PATH}" \
		--local_copy "${SAVED_MODEL_PERFORMANCE_PATH}"

evaluate: models/performance_report.csv

empty_database:
	python3 run.py create_db

ingest_dataset: data/cleaned/P4KxSpotify.csv
	python3 run.py ingest_dataset -f "${CLEANED_DATA_PATH}"

app: empty_database pipeline ingest_dataset
	python3 app.py --model "${S3_BUCKET}/${SAVED_MODEL_PATH}"

reproducibility_tests:
	./tests/run_reproducibility_tests.sh

cleanup:
	find ./data -mindepth 1 ! -name '.gitkeep' -delete
	find ./models -mindepth 1 ! -name '.gitkeep' -delete
	find ./tests/reproducibility-actual -mindepth 1 ! -name '.gitkeep' -delete
	@echo 'Cleaned up artifacts in data/, models/, and tests/reproducibility-actual/'
