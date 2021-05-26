import logging.config
import os
import traceback

from flask import Flask, redirect, render_template, request, send_from_directory, url_for

from src import model
from src import serialize
from src.add_albums import Albums, AlbumManager

# Initialize the Flask application
app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
app.config.from_pyfile("config/flaskconfig.py")

# Define LOGGING_CONFIG in flask_config.py: path to config file
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
        Redirect to index page if successful; else error page
    """
    try:
        form_data = request.form.to_dict()
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
    pipeline = serialize.load_pipeline(app.config["SAVED_MODEL_PATH"])
    logger.info("Loaded saved model pipeline")

    input_data = request.form.to_dict()
    df = model.parse_dict_to_dataframe(input_data)
    logger.debug("Parsed input data to DataFrame format")

    try:
        score = round(pipeline.predict(df)[0], 2)
        logger.info("Prediction: %s", score)
        return str(score)
    except:
        traceback.print_exc()
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
