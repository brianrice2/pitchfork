import logging.config

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, Float, Integer, String, MetaData
from sqlalchemy.orm import sessionmaker
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger(__name__)
logger.setLevel("INFO")

Base = declarative_base()


class Albums(Base):
    """Create a data model for the database to be set up for capturing albums."""

    __tablename__ = "albums"

    album = Column(String(100), primary_key=True)
    artist = Column(String(100))
    reviewauthor = Column(String(100))
    score = Column(Float(100))
    releaseyear = Column(Integer(100))
    reviewdate = Column(DateTime(100))
    recordlabel = Column(String(100))
    genre = Column(String(100))
    danceability = Column(Float(100))
    energy = Column(Float(100))
    key = Column(Float(100))
    loudness = Column(Float(100))
    speechiness = Column(Float(100))
    acousticness = Column(Float(100))
    instramentalness = Column(Float(100))
    liveness = Column(Float(100))
    valence = Column(Float(100))
    tempo = Column(Float(100))

    def __repr__(self):
        return "<Album %r>" % self.album


def create_db(engine_string: str) -> None:
    """
    Create database from provided engine string.

    Args:
        engine_string (str): Engine string
    """
    engine = sqlalchemy.create_engine(engine_string)

    Base.metadata.create_all(engine)
    logger.info("Database created.")


class AlbumManager:
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
                "Need either an engine string or a Flask app to initialize."
            )

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
            reviewdate (datetime): Album review date
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

        session = self.session
        album = Albums(
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
        session.add(album)
        session.commit()
        logger.info("%s by %s added to database", album, artist)
