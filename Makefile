.PHONY: raw_data cleaned_data model pipeline predictions empty_database ingest_dataset app cleanup

PIPELINE_CONFIG="config/pipeline.yaml"
S3_BUCKET="s3://2021-msia423-rice-brian"
RAW_DATA_PATH="data/raw/P4KxSpotify.csv"
CLEANED_DATA_PATH="data/cleaned/P4KxSpotify.csv"
SAVED_MODEL_PATH="models/gbt_pipeline.joblib"
SAVED_MODEL_PREDICTIONS_PATH="models/cleaned_with_predictions.csv"

raw_data:
	python3 run.py load_data \
		--local_path "${RAW_DATA_PATH}" \
		--s3path "${S3_BUCKET}/${RAW_DATA_PATH}"

cleaned_data:
	python3 run.py pipeline clean \
		--input "${S3_BUCKET}/${RAW_DATA_PATH}" \
		--config "${PIPELINE_CONFIG}" \
		--output "${S3_BUCKET}/${CLEANED_DATA_PATH}"

model:
	python3 run.py pipeline model \
		--input "${S3_BUCKET}/${CLEANED_DATA_PATH}" \
		--config "${PIPELINE_CONFIG}" \
		--output "${S3_BUCKET}/${SAVED_MODEL_PATH}"

pipeline: cleaned_data model

predictions:
	python3 run.py pipeline predict \
		--input "${S3_BUCKET}/${CLEANED_DATA_PATH}" \
		--model "${S3_BUCKET}/${SAVED_MODEL_PATH}" \
		--config "${PIPELINE_CONFIG}" \
		--output "${S3_BUCKET}/${SAVED_MODEL_PREDICTIONS_PATH}"

empty_database:
	python3 run.py create_db

ingest_dataset:
	python3 run.py ingest_dataset -f "${S3_BUCKET}/${CLEANED_DATA_PATH}"

app:
	python3 app.py

cleanup:
	find ./data -mindepth 1 ! -name '.gitkeep' -delete
	find ./models -mindepth 1 ! -name '.gitkeep' -delete
	echo 'Cleaned up artifacts in data/ and models/'
