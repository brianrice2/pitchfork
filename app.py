import logging.config
import os
import traceback

from flask import Flask
from flask import redirect, render_template, request, send_from_directory, url_for

from src.add_albums import Albums, AlbumManager

# Initialize the Flask application
app = Flask(__name__, template_folder="app/templates", static_folder="app/static")

# Configure flask app from flask_config.py
app.config.from_pyfile("config/flaskconfig.py")

# Define LOGGING_CONFIG in flask_config.py - path to config file for setting
# up the logger (e.g. config/logging/local.conf)
logging.config.fileConfig(app.config["LOGGING_CONFIG"])
logger = logging.getLogger(app.config["APP_NAME"])
logger.debug("Web app log")

# Initialize the database session
album_manager = AlbumManager(app)


@app.route("/")
def index():
    """
    Main view that lists songs in the database.

    Creates view into index page that uses data queried from Albums database and
    inserts it into the app/templates/index.html template.

    Returns:
        Rendered HTML template
    """
    try:
        albums = album_manager.session.query(Albums).limit(app.config["MAX_ROWS_SHOW"]).all()
        logger.debug("Index page accessed")
        return render_template("index.html", albums=albums)
    except:
        traceback.print_exc()
        logger.warning("Not able to display albums. Error page returned.")
        return render_template("error.html")


@app.route("/add", methods=["POST"])
def add_entry():
    """
    View that processes a POST request with new album input.

    Returns:
        Redirect to index page
    """
    try:
        album_manager.add_album(
            artist=request.form["artist"],
            album=request.form["album"],
            reviewauthor=request.form["reviewauthor"],
            score=request.form["score"],
            releaseyear=request.form["releaseyear"],
            reviewdate=request.form["reviewdate"],
            recordlabel=request.form["recordlabel"],
            genre=request.form["genre"],
            danceability=request.form["danceability"],
            energy=request.form["energy"],
            key=request.form["key"],
            loudness=request.form["loudness"],
            speechiness=request.form["speechiness"],
            acousticness=request.form["acousticness"],
            instrumentalness=request.form["instrumentalness"],
            liveness=request.form["liveness"],
            valence=request.form["valence"],
            tempo=request.form["tempo"]
        )
        logger.info("New album added: %s by %s", request.form["album"], request.form["artist"])
        return redirect(url_for("index"))
    except:
        logger.warning("Failed to add new album. Error page returned.")
        return render_template("error.html")


@app.route("/predict", methods=["POST"])
def predict_rating():
    """
    View that processes a POST request to predict rating for an input album.

    Returns:
        Redirect to index page
    """
    try:
        model.predict(
            artist=request.form["artist"],
            album=request.form["album"],
            reviewauthor=request.form["reviewauthor"],
            score=request.form["score"],
            releaseyear=request.form["releaseyear"],
            reviewdate=request.form["reviewdate"],
            recordlabel=request.form["recordlabel"],
            genre=request.form["genre"],
            danceability=request.form["danceability"],
            energy=request.form["energy"],
            key=request.form["key"],
            loudness=request.form["loudness"],
            speechiness=request.form["speechiness"],
            acousticness=request.form["acousticness"],
            instrumentalness=request.form["instrumentalness"],
            liveness=request.form["liveness"],
            valence=request.form["valence"],
            tempo=request.form["tempo"]
        )
        logger.info("Making prediction for %s by %s", request.form["album"], request.form["artist"])
        return redirect(url_for("index"))
    except:
        logger.warning("Failed to predict rating for new album. Error page returned.")
        return render_template("error.html")


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "app", "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon"
    )


if __name__ == '__main__':
    app.run(debug=app.config["DEBUG"], port=app.config["PORT"], host=app.config["HOST"])
