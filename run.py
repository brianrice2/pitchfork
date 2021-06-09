"""
Receives command-line arguments from the user and delegates
instructions to the appropriate module in `src/`. It handles:

- Database interaction (creation, deletion, ingestion)
- Data downloading from source, uploading to S3, and downloading from S3
- Data processing and model training pipeline
- Making predictions on new data
"""
import argparse
import logging.config
import pkg_resources

import botocore
import pandas as pd
import yaml

from config.flaskconfig import SQLALCHEMY_DATABASE_URI
from src import (
    albums_database,
    clean,
    evaluate_performance,
    load_data,
    model,
    post_process,
    score_model,
    serialize
)

# Using `pkg_resources` here allows Sphinx to find the logging config
# file when building the documentation HTML pages (only necessary for
# root-level scripts)
logging.config.fileConfig(
    pkg_resources.resource_filename(__name__, "config/logging/local.conf"),
    disable_existing_loggers=False
)
logger = logging.getLogger("pitchfork-pipeline")

DEFAULT_RAW_DATA_PATH = "data/raw/P4KxSpotify.csv"
DEFAULT_S3_BUCKET = "s3://2021-msia423-rice-brian/"
DEFAULT_S3_PATH = "raw/P4KxSpotify.csv"
DEFAULT_S3_LOCATION = DEFAULT_S3_BUCKET + DEFAULT_S3_PATH


if __name__ == "__main__":
    # Add parsers for both managing database, cleaning data, and modeling
    parser = argparse.ArgumentParser(description="Create/update database, clean data, and model")
    subparsers = parser.add_subparsers(dest="subparser_name")

    # Sub-parser for creating a database
    sp_create = subparsers.add_parser("create_db", description="Create database")
    sp_create.add_argument(
        "--engine_string",
        default=SQLALCHEMY_DATABASE_URI,
        help="SQLAlchemy connection URI for database",
    )

    # Sub-parser for deleting a database
    sp_delete = subparsers.add_parser("delete_db", description="Delete database")
    sp_delete.add_argument(
        "--engine_string",
        default=SQLALCHEMY_DATABASE_URI,
        help="SQLAlchemy connection URI for database",
    )

    # Sub-parser for ingesting new data
    sp_ingest_album = subparsers.add_parser("ingest_album", description="Add data to database")
    sp_ingest_album.add_argument(
        "--engine_string",
        default=SQLALCHEMY_DATABASE_URI,
        help="SQLAlchemy connection URI for database",
    )
    sp_ingest_album.add_argument("--album", default="Run the Jewels 2", help="Album title")
    sp_ingest_album.add_argument("--artist", default="Run the Jewels", help="Artist of album")
    sp_ingest_album.add_argument(
        "--reviewauthor", default="Ian Cohen", help="Album reviewer's name"
    )
    sp_ingest_album.add_argument("--score", default="9", help="Pitchfork rating")
    sp_ingest_album.add_argument("--releaseyear", default=2014, help="Album release year")
    sp_ingest_album.add_argument(
        "--reviewdate", default="October 29 2014", help="Pitchfork review date"
    )
    sp_ingest_album.add_argument(
        "--recordlabel", default="Mass Appeal", help="Album record label"
    )
    sp_ingest_album.add_argument("--genre", default="Rap", help="Album genre")
    sp_ingest_album.add_argument(
        "--danceability", default="0.639833333", help="Album's Spotify danceability score"
    )
    sp_ingest_album.add_argument(
        "--energy", default="0.65425", help="Album's Spotify energy score"
    )
    sp_ingest_album.add_argument(
        "--key", default="4.916666667", help="Album's Spotify key score"
    )
    sp_ingest_album.add_argument(
        "--loudness", default="-7.842166667", help="Album's Spotify loudness score"
    )
    sp_ingest_album.add_argument(
        "--speechiness", default="0.236491667", help="Album's Spotify speechiness score"
    )
    sp_ingest_album.add_argument(
        "--acousticness", default="0.0945741669999999", help="Album's Spotify acousticness score"
    )
    sp_ingest_album.add_argument(
        "--instrumentalness",
        default="0.0470013809999999",
        help="Album's Spotify instrumentalness score"
    )
    sp_ingest_album.add_argument(
        "--liveness", default="0.271858333", help="Album's Spotify liveness score"
    )
    sp_ingest_album.add_argument(
        "--valence", default="0.361166667", help="Album's Spotify valence score"
    )
    sp_ingest_album.add_argument(
        "--tempo", default="123.1539167", help="Album's Spotify tempo score"
    )

    # Sub-parser for ingesting a dataset
    sp_ingest_dataset = subparsers.add_parser(
        "ingest_dataset", description="Ingest dataset into database"
    )
    sp_ingest_dataset.add_argument(
        "--engine_string",
        default=SQLALCHEMY_DATABASE_URI,
        help="SQLAlchemy connection URI for database",
    )
    sp_ingest_dataset.add_argument(
        "-f",
        "--file",
        default="data/raw/P4KxSpotify.csv",
        help="Filename or path to file containing CSV dataset of albums to load",
    )

    # Sub-parser for downloading dataset and moving between S3
    sp_load_data = subparsers.add_parser(
        "load_data", description="Download data and move between S3"
    )
    sp_load_data.add_argument("--sep", default=",", help="CSV separator if using pandas")
    sp_load_data.add_argument(
        "-p",
        "--pandas",
        default=False,
        action="store_true",
        help="If used, will load data via pandas",
    )
    sp_load_data.add_argument(
        "-d",
        "--download",
        default=False,
        action="store_true",
        help="If used, will download from the source instead of uploading",
    )
    sp_load_data.add_argument(
        "-s",
        "--s3path",
        default=DEFAULT_S3_LOCATION,
        help="Location in S3 for source/destination file",
    )
    sp_load_data.add_argument(
        "-l",
        "--local_path",
        default=DEFAULT_RAW_DATA_PATH,
        help="Location in local filesystem for source/destination file",
    )
    sp_load_data.add_argument(
        "-r",
        "--raw_data",
        default=False,
        action="store_true",
        help="If used, will download the raw dataset from the internet",
    )

    # Sub-parser for data processing and model training pipeline
    sp_pipeline = subparsers.add_parser(
        "pipeline", description="Data cleaning and model training pipeline"
    )
    sp_pipeline.add_argument(
        "step",
        help="Which step to run",
        choices=["clean", "model", "predict", "evaluate"]
    )
    sp_pipeline.add_argument(
        "--input", "-i",
        default=None,
        help="Path to input_data df (optional, default=None)"
    )
    sp_pipeline.add_argument(
        "--config", "-c",
        default="config/pipeline.yaml",
        help="Path to configuration file"
    )
    sp_pipeline.add_argument(
        "--output", "-o",
        default=None,
        help="Path to save output CSV (optional, default=None)"
    )
    sp_pipeline.add_argument(
        "--model", "-m",
        default=None,
        help="Path to load trained model object. Only used for `predict`."
    )
    sp_pipeline.add_argument(
        "--local_copy",
        default=None,
        help="Local path to save output CSV (optional, default=None)"
    )

    # Interpret and execute commands
    args = parser.parse_args()
    sp_used = args.subparser_name
    if sp_used == "create_db":
        albums_database.create_db(args.engine_string)
    elif sp_used == "delete_db":
        albums_database.delete_db(args.engine_string)
    elif sp_used == "ingest_album":
        album_manager = albums_database.AlbumManager(engine_string=args.engine_string)
        album_manager.add_album(
            args.album,
            args.artist,
            args.reviewauthor,
            args.score,
            args.releaseyear,
            args.reviewdate,
            args.recordlabel,
            args.genre,
            args.danceability,
            args.energy,
            args.key,
            args.loudness,
            args.speechiness,
            args.acousticness,
            args.instrumentalness,
            args.liveness,
            args.valence,
            args.tempo,
        )
        album_manager.close()
    elif sp_used == "ingest_dataset":
        album_manager = albums_database.AlbumManager(engine_string=args.engine_string)
        album_manager.ingest_dataset(args.file)
        album_manager.close()
    elif sp_used == "load_data":
        # Assume data exists already in S3
        if args.download:
            if args.pandas:
                load_data.download_from_s3_pandas(args.local_path, args.s3path, args.sep)
            else:
                load_data.download_file_from_s3(args.local_path, args.s3path)
        # Assume data does _not_ exist already in S3
        else:
            # Download data from internet
            load_data.download_raw_data(args.local_path)

            # Upload to S3
            if args.pandas:
                load_data.upload_to_s3_pandas(args.local_path, args.s3path, args.sep)
            else:
                load_data.upload_file_to_s3(args.local_path, args.s3path)
    elif sp_used == "pipeline":
        # Load configuration file for parameters and trained model object path
        # In PyYAML 5.1+, using `yaml.load` _without the `Loader` param_ has
        # been deprecated (for security reasons), so specify `FullLoader`.
        # This loads the full YAML language, but avoids arbitrary code execution.
        with open(args.config, "r") as config_file:
            config = yaml.load(config_file, Loader=yaml.FullLoader)
        logger.debug("Configuration file loaded from %s", args.config)

        if args.input:
            input_data = pd.read_csv(args.input)
            logger.debug("Input df loaded from %s", args.input)

        if args.step == "clean":
            logger.debug("Beginning `clean`")
            output = clean.clean_dataset(input_data, config["clean"])
        elif args.step == "model":
            logger.debug("Beginning `model`")

            # Train on full dataset for deployment
            X, y = model.split_predictors_response(
                input_data,
                **config["model"]["split_predictors_response"]
            )

            # Model building and training
            preprocessor = model.make_preprocessor(**config["model"]["make_preprocessor"])
            model_pipeline = model.make_model(**config["model"]["make_model"])
            fitted_pipeline = model.train_pipeline(X, y, preprocessor, model_pipeline)

            feature_importances = post_process.get_feature_importance(
                fitted_pipeline,
                **config["post_process"]["get_feature_importance"]
            )
            logger.info("Feature importances from training:\n%s", feature_importances)
        elif args.step == "predict":
            logger.debug("Beginning `predict`")
            fitted_pipeline = serialize.load_pipeline(args.model)
            output = score_model.append_predictions(
                fitted_pipeline,
                input_data,
                **config["score_model"]["append_predictions"]
            )
        elif args.step == "evaluate":
            logger.debug("Beginning `evaluate`")
            output = evaluate_performance.evaluate_model(
                input_data,
                **config["evaluate_performance"]["evaluate_model"]
            )

        # Only the output from `model` cannot be saved in CSV format (returns a TMO)
        if args.output:
            if args.step != "model":
                try:
                    output.to_csv(args.output, index=False)
                except botocore.exceptions.ClientError:
                    logger.warning("Failed to upload to S3 (ad permissions). Skipped.")
                else:
                    logger.info("Output saved to %s", args.output)

                if args.local_copy:
                    output.to_csv(args.local_copy, index=False)
                    logger.info("Local copy saved to %s", args.local_copy)
            else:
                serialize.save_pipeline(fitted_pipeline, args.output)
                logger.info("Trained model object saved to %s", args.output)
    else:
        parser.print_help()
