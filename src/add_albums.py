import csv
import logging.config
from datetime import date, datetime

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Date, Float, Integer, String
from sqlalchemy.orm import sessionmaker
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger(__name__)

Base = declarative_base()


class Albums(Base):
    """Create a data model for the database to be set up for capturing albums."""

    __tablename__ = "albums"

    id = Column(Integer(), primary_key=True)
    album = Column(String(100), nullable=False)
    artist = Column(String(100))
    reviewauthor = Column(String(50), nullable=False)
    score = Column(Float(), nullable=False)
    releaseyear = Column(Integer())
    reviewdate = Column(Date())
    recordlabel = Column(String(100))
    genre = Column(String(50))
    danceability = Column(Float())
    energy = Column(Float())
    key = Column(Float())
    loudness = Column(Float())
    speechiness = Column(Float())
    acousticness = Column(Float())
    instrumentalness = Column(Float())
    liveness = Column(Float())
    valence = Column(Float())
    tempo = Column(Float())

    def __repr__(self):
        return "Album(%r, %r)" % album, artist


def create_db(engine_string: str) -> None:
    """
    Create database from provided engine string.

    Args:
        engine_string (str): Engine string
    """
    engine = sqlalchemy.create_engine(engine_string)

    Base.metadata.create_all(engine)
    logger.info("Database created")


def delete_db(engine_string: str) -> None:
    """
    Create database from provided engine string.

    Args:
        engine_string (str): Engine string
    """
    engine = sqlalchemy.create_engine(engine_string)

    Base.metadata.drop_all(engine)
    logger.info("Database deleted")


class AlbumManager:
    """Manages Flask <-> SQLAlchemy connection and adds data to database."""

    def __init__(self, app=None, engine_string=None):
        """
        Args:
            app (Flask, optional): Flask app. Defaults to None.
            engine_string (str, optional): Engine string. Defaults to None.

        Raises:
            ValueError: If neither an app nor an engine string is provided.
        """
        if app:
            self.db = SQLAlchemy(app)
            self.session = self.db.session
        elif engine_string:
            engine = sqlalchemy.create_engine(engine_string)
            Session = sessionmaker(bind=engine)
            self.session = Session()
        else:
            raise ValueError(
                "Need either an engine string or a Flask app to initialize"
            )

    def __repr__(self):
        return "AlbumManager({self.session!r})"

    def close(self) -> None:
        """
        Closes the current SQLAlchemy session.

        Returns:
            None
        """
        self.session.close()

    def add_album(
        self,
        album: str,
        artist: str,
        reviewauthor: str,
        score: float,
        releaseyear: int,
        reviewdate: datetime,
        recordlabel: str,
        genre: str,
        danceability: float,
        energy: float,
        key: float,
        loudness: float,
        speechiness: float,
        acousticness: float,
        instrumentalness: float,
        liveness: float,
        valence: float,
        tempo: float,
    ) -> None:
        """
        Seeds an existing database with additional albums.

        Args:
            album (str): Album title
            artist (str): Artist
            reviewauthor (str): Name of reviewing author
            score (float): Pitchfork rating
            releaseyear (int): Album release year
            reviewdate (str): Album review date (%B %d %Y)
            recordlabel (str): Album's record label(s)
            genre (str): Album genre
            danceability (float): Spotify danceability score
            energy (float): Spotify energy score
            key (float): Spotify key score
            loudness (float): Spotify loudness score
            speechiness (float): Spotify speechiness score
            acousticness (float): Spotify acousticness score
            instrumentalness (float): Spotify instrumentalness score
            liveness (float): Spotify liveness score
            valence (float): Spotify valence score
            tempo (float): Spotify tempo score

        Returns:
            None
        """
        try:
            # Parse datetime
            reviewdate = datetime.strptime(reviewdate, "%B %d %Y").date()
        except ValueError:
            logger.error("Failed to parse the given reviewdate %s. Aborting.", reviewdate)
        else:
            # Add to database
            session = self.session
            new_album = Albums(
                album=album,
                artist=artist,
                reviewauthor=reviewauthor,
                score=score,
                releaseyear=releaseyear,
                reviewdate=reviewdate,
                recordlabel=recordlabel,
                genre=genre,
                danceability=danceability,
                energy=energy,
                key=key,
                loudness=loudness,
                speechiness=speechiness,
                acousticness=acousticness,
                instrumentalness=instrumentalness,
                liveness=liveness,
                valence=valence,
                tempo=tempo,
            )
            session.add(new_album)
            try:
                session.commit()
            except sqlalchemy.exc.OperationalError:
                logger.error("Could not find table. One possible reason: are you connected to the Northwestern VPN?")
            else:
                logger.info("%s added to database", album)

    def ingest_dataset(self, file_or_path: str) -> None:
        """
        Seeds an existing database with entries from a CSV file.

        Args:
            file_or_path (str): Location of dataset to load into database

        Returns:
            None
        """
        session = self.session

        with open(file_or_path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                row["reviewdate"] = datetime.strptime(row["reviewdate"], "%B %d %Y").date()
                session.add(Albums(**row))

        try:
            session.commit()
        except sqlalchemy.exc.OperationalError:
            logger.error("Could not find table. One possible reason: are you connected to the Northwestern VPN?")
        else:
            logger.info("Contents of %s added to database", file_or_path)
