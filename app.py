"""
Run the single-page web application with Flask.
"""
import argparse
import logging.config
import os
import traceback
from time import time

import pkg_resources
import yaml
from flask import Flask, redirect, render_template, request, send_from_directory, url_for

from src import model
from src import serialize
from src.albums_database import Albums, AlbumManager

# Initialize the Flask application
# By default, Flask looks for templates/ and static/ in the current
# directory, so we need to tell it to look inside app/
app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
app.config.from_pyfile("config/flaskconfig.py")

# Define LOGGING_CONFIG in flask_config.py as the path to config file
# Using `pkg_resources` here allows Sphinx to find the logging config
# file when building the documentation HTML pages (only necessary for
# root-level scripts)
logging.config.fileConfig(
    pkg_resources.resource_filename(__name__, app.config["LOGGING_CONFIG"]),
    disable_existing_loggers=False
)
logger = logging.getLogger(app.config["APP_NAME"])
logger.debug("Web app log")

# App loads the serialized fitted model for live inference
with open(pkg_resources.resource_filename(__name__, app.config["PIPELINE_CONFIG"]), "r") as config_file:
    pipeline_config = yaml.load(config_file, Loader=yaml.FullLoader)

# Initialize the database session
album_manager = AlbumManager(app)


@app.route("/")
def index():
    """
    Main view that lists songs in the database.

    Creates view into index page that uses data queried from Albums database and
    inserts it into the app/templates/index.html template.

    Returns:
        Rendered HTML template for the SPA
    """
    try:
        # Default view shows the first MAX_ROWS_SHOW albums in the database
        albums = album_manager.session.query(Albums).limit(app.config["MAX_ROWS_SHOW"]).all()
        logger.debug("Index page accessed")
        return render_template("index.html", albums=albums)
    except:
        traceback.print_exc()
        logger.warning("Not able to display albums. Error page returned.")
        return render_template("error.html")


@app.route("/search")
def search():
    """
    Search for songs in the database.

    Returns:
        Rendered HTML template of SPA with songs filtered
    """
    # Available search fields from HTML
    album_name = request.args.get("album")
    artist_name = request.args.get("artist")
    score = request.args.get("score")

    # Filter all songs based on user input
    # TO DO: Validate user input before querying database
    albums = album_manager.session.query(Albums)
    if album_name:
        albums = albums.filter(Albums.album.like("%" + album_name + "%"))
    if artist_name:
        albums = albums.filter(Albums.artist.like("%" + artist_name + "%"))
    if score:
        albums = albums.filter(Albums.score == score)
    logger.debug(
        "Found %s albums like \"%s\" by \"%s\" (max displayed: %s)",
        len(albums.all()),
        album_name,
        artist_name,
        app.config["MAX_ROWS_SHOW"]
    )
    albums = albums.limit(app.config["MAX_ROWS_SHOW"]).all()

    return render_template("index.html", albums=albums)


@app.route("/add", methods=["POST"])
def add_entry():
    """
    View that processes a POST request with new album input.

    Returns:
        Redirect to index page if successful, else error page
    """
    try:
        # Parse user request
        form_data = request.form.to_dict()

        # Populate required fields if not provided
        form_data["album"] = form_data.get("album", "Not provided")
        form_data["reviewauthor"] = form_data.get("reviewauthor", "Not provided")
        form_data["score"] = form_data.get("score", 0)

        # Add to database
        album_manager.add_album(**form_data)
        logger.info("New album added: %s by %s", form_data["album"], form_data["artist"])
        return redirect(url_for("index"))
    except:
        traceback.print_exc()
        logger.warning("Failed to add new album. Error page returned.")
        return render_template("error.html")


@app.route("/predict", methods=["POST"])
def predict_rating():
    """
    Predict the rating for an input album given a POST form of input data.

    Returns:
        Redirect to index page
    """
    start_time = time()

    # Convert request form to the model's required `pandas.DataFrame` format
    input_data = request.form.to_dict()
    input_df = model.parse_dict_to_dataframe(input_data)

    # Ensure all columns (& order) match the original training data
    validated_df = model.validate_dataframe(input_df)
    logger.debug("Parsed input data to DataFrame format")

    try:
        score = round(pipeline.predict(validated_df)[0], 2)

        # Clip predicted score between 0 and 10
        score = min(10, max(0, score))

        logger.debug(
            """Prediction: %0.2f.
            Total time for loading model, parsing input, and performing inference: %0.4fs""",
            score,
            time() - start_time
        )
        return str(score)
    except:
        traceback.print_exc()
        logger.warning("Failed to predict rating for new album. Error page returned.")
        return render_template("error.html")


@app.route("/favicon.ico")
def favicon():
    """Show pitchfork favicon in browser."""
    return send_from_directory(
        os.path.join(app.root_path, "app", "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon"
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run web application")
    parser.add_argument("--model", "-m", help="Path to trained model object")
    args = parser.parse_args()

    # Preload the trained model for extremely fast inference
    pipeline = serialize.load_pipeline(args.model)
    logger.debug("Loaded saved model pipeline")

    app.run(debug=app.config["DEBUG"], port=app.config["PORT"], host=app.config["HOST"])
