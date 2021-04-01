import logging.config

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, MetaData
from sqlalchemy.orm import sessionmaker
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger(__name__)
logger.setLevel("INFO")

Base = declarative_base()


class Tracks(Base):
    """Create a data model for the database to be set up for capturing songs

    """

    __tablename__ = 'tracks'

    id = Column(Integer, primary_key=True)
    title = Column(String(100), unique=False, nullable=False)
    artist = Column(String(100), unique=False, nullable=False)
    album = Column(String(100), unique=False, nullable=True)

    def __repr__(self):
        return '<Track %r>' % self.title


def create_db(engine_string: str) -> None:
    """Create database from provided engine string

    Args:
        engine_string: str - Engine string

    Returns: None

    """
    engine = sqlalchemy.create_engine(engine_string)

    Base.metadata.create_all(engine)
    logger.info("Database created.")


class TrackManager:

    def __init__(self, app=None, engine_string=None):
        """
        Args:
            app: Flask - Flask app
            engine_string: str - Engine string
        """
        if app:
            self.db = SQLAlchemy(app)
            self.session = self.db.session
        elif engine_string:
            engine = sqlalchemy.create_engine(engine_string)
            Session = sessionmaker(bind=engine)
            self.session = Session()
        else:
            raise ValueError("Need either an engine string or a Flask app to initialize")

    def close(self) -> None:
        """Closes session

        Returns: None

        """
        self.session.close()

    def add_track(self, title: str, artist: str, album: str) -> None:
        """Seeds an existing database with additional songs.

        Args:
            title: str - Title of song
            artist: str - Artist
            album: str - Album title

        Returns:None

        """

        session = self.session
        track = Tracks(artist=artist, album=album, title=title)
        session.add(track)
        session.commit()
        logger.info("%s by %s from album, %s, added to database", title, artist, album)
