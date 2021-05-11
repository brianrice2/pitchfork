"""
Receives command-line arguments from the user and delegates
instructions to the appropriate script in `src/`. It handles:

- Database interaction (creation, deletion, ingestion)
- Data downloading from source, uploading to S3, and downloading from S3
"""
import argparse
import logging.config
import pkg_resources

from src.add_albums import AlbumManager, create_db, delete_db
from src.load_data import (
    download_raw_data,
    download_file_from_s3,
    download_from_s3_pandas,
    upload_file_to_s3,
    upload_to_s3_pandas
)
from config.flaskconfig import SQLALCHEMY_DATABASE_URI

# Using `pkg_resources` here allows Sphinx to find the logging config
# file when building the documentation HTML pages
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
    # Add parsers for both creating a database and adding albums to it
    parser = argparse.ArgumentParser(description="Create and/or add data to database")
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
    sp_ingest_album.add_argument("--releaseyear", default="2014", help="Album release year")
    sp_ingest_album.add_argument(
        "--reviewdate", default="October 29 2014", help="Pitchfork review date"
    )
    sp_ingest_album.add_argument(
        "--recordlabel", default="Mass Appeal", help="Album record label"
    )
    sp_ingest_album.add_argument("--genre", default="Rap", help="Album genre")
    sp_ingest_album.add_argument(
        "--danceability",
        default="0.639833333",
        help="Album's Spotify danceability score",
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
        "--acousticness",
        default="0.0945741669999999",
        help="Album's Spotify acousticness score",
    )
    sp_ingest_album.add_argument(
        "--instrumentalness",
        default="0.0470013809999999",
        help="Album's Spotify instrumentalness score",
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
        default="sqlite:///data/msia423_db.db",
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
    parser.add_argument("--sep", default=",", help="CSV separator if using pandas")
    parser.add_argument(
        "-p",
        "--pandas",
        default=False,
        action="store_true",
        help="If used, will load data via pandas",
    )
    parser.add_argument(
        "-d",
        "--download",
        default=False,
        action="store_true",
        help="If used, will download from the source instead of uploading",
    )
    parser.add_argument(
        "-s",
        "--s3path",
        default=DEFAULT_S3_LOCATION,
        help="Location in S3 for source/destination file",
    )
    parser.add_argument(
        "-l",
        "--local_path",
        default=DEFAULT_RAW_DATA_PATH,
        help="Location in local filesystem for source/destination file",
    )
    parser.add_argument(
        "-r",
        "--raw_data",
        default=False,
        action="store_true",
        help="If used, will download the raw dataset from the internet",
    )

    # Interpret and execute commands
    args = parser.parse_args()
    sp_used = args.subparser_name
    if sp_used == "create_db":
        create_db(args.engine_string)
    elif sp_used == "delete_db":
        delete_db(args.engine_string)
    elif sp_used == "ingest_album":
        album_manager = AlbumManager(engine_string=args.engine_string)
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
        album_manager = AlbumManager(engine_string=args.engine_string)
        album_manager.ingest_dataset(args.file)
        album_manager.close()
    elif sp_used == "load_data":
        # Assume data exists already in S3
        if args.download:
            if args.pandas:
                download_from_s3_pandas(args.local_path, args.s3path, args.sep)
            else:
                download_file_from_s3(args.local_path, args.s3path)
        # Assume data does _not_ exist already in S3
        else:
            # Download data from internet
            download_raw_data(args.local_path)

            # Upload to S3
            if args.pandas:
                upload_to_s3_pandas(args.local_path, args.s3path, args.sep)
            else:
                upload_file_to_s3(args.local_path, args.s3path)
    else:
        parser.print_help()
