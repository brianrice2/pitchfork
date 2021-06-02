import os

DEBUG = True
LOGGING_CONFIG = "config/logging/local.conf"
PIPELINE_CONFIG = "config/pipeline.yaml"
PORT = 5000
APP_NAME = "pitchfork"
SQLALCHEMY_TRACK_MODIFICATIONS = True
HOST = "0.0.0.0"
SQLALCHEMY_ECHO = False  # If True, SQL queries will be echoed/printed
MAX_ROWS_SHOW = 1000
DEFAULT_LOCAL_DATABASE = "sqlite:///data/msia423_db.db"

# Connection string
DB_HOST = os.environ.get("MYSQL_HOST")
DB_PORT = os.environ.get("MYSQL_PORT")
DB_USER = os.environ.get("MYSQL_USER")
DB_PW = os.environ.get("MYSQL_PASSWORD")
DATABASE = os.environ.get("MYSQL_DATABASE")
DB_DIALECT = "mysql+pymysql"
SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
if SQLALCHEMY_DATABASE_URI is not None:
    pass
elif DB_HOST is None:
    SQLALCHEMY_DATABASE_URI = DEFAULT_LOCAL_DATABASE
else:
    SQLALCHEMY_DATABASE_URI = "{dialect}://{user}:{pw}@{host}:{port}/{db}".format(
        dialect=DB_DIALECT,
        user=DB_USER,
        pw=DB_PW,
        host=DB_HOST,
        port=DB_PORT,
        db=DATABASE,
    )
