import argparse

import logging.config

logging.config.fileConfig("config/logging/local.conf")
logger = logging.getLogger("pitchfork-pipeline")

from src.add_albums import AlbumManager, create_db
from config.flaskconfig import SQLALCHEMY_DATABASE_URI

if __name__ == "__main__":
    # Add parsers for both creating a database and adding albums to it
    parser = argparse.ArgumentParser(description="Create and/or add data to database")
    subparsers = parser.add_subparsers(dest="subparser_name")

    # Sub-parser for creating a database
    sb_create = subparsers.add_parser("create_db", description="Create database")
    sb_create.add_argument(
        "--engine_string",
        default=SQLALCHEMY_DATABASE_URI,
        help="SQLAlchemy connection URI for database",
    )

    # Sub-parser for ingesting new data
    sb_ingest = subparsers.add_parser("ingest", description="Add data to database")
    sb_ingest.add_argument(
        "--engine_string",
        default="sqlite:///data/albums.db",
        help="SQLAlchemy connection URI for database",
    )
    sb_ingest.add_argument("--album", default="Run the Jewels 2", help="Album title")
    sb_ingest.add_argument("--artist", default="Run the Jewels", help="Artist of album")
    sb_ingest.add_argument(
        "--reviewauthor", default="Ian Cohen", help="Album reviewer's name"
    )
    sb_ingest.add_argument("--score", default="9", help="Pitchfork rating")
    sb_ingest.add_argument("--releaseyear", default="2014", help="Album release year")
    sb_ingest.add_argument(
        "--reviewdate", default="October 29 2014", help="Pitchfork review date"
    )
    sb_ingest.add_argument(
        "--recordlabel", default="Mass Appeal", help="Album record label"
    )
    sb_ingest.add_argument("--genre", default="Rap", help="Album genre")
    sb_ingest.add_argument(
        "--danceability",
        default="0.639833333",
        help="Album's Spotify danceability score",
    )
    sb_ingest.add_argument(
        "--energy", default="0.65425", help="Album's Spotify energy score"
    )
    sb_ingest.add_argument(
        "--key", default="4.916666667", help="Album's Spotify key score"
    )
    sb_ingest.add_argument(
        "--loudness", default="-7.842166667", help="Album's Spotify loudness score"
    )
    sb_ingest.add_argument(
        "--speechiness", default="0.236491667", help="Album's Spotify speechiness score"
    )
    sb_ingest.add_argument(
        "--acousticness",
        default="0.0945741669999999",
        help="Album's Spotify acousticness score",
    )
    sb_ingest.add_argument(
        "--instrumentalness",
        default="0.0470013809999999",
        help="Album's Spotify instrumentalness score",
    )
    sb_ingest.add_argument(
        "--liveness", default="0.271858333", help="Album's Spotify liveness score"
    )
    sb_ingest.add_argument(
        "--valence", default="0.361166667", help="Album's Spotify valence score"
    )
    sb_ingest.add_argument(
        "--tempo", default="123.1539167", help="Album's Spotify tempo score"
    )

    args = parser.parse_args()
    sp_used = args.subparser_name
    if sp_used == "create_db":
        create_db(args.engine_string)
    elif sp_used == "ingest":
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
    else:
        parser.print_help()
