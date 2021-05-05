# p4k.ai

Developer: Brian Rice

Quality Assurance: Cheng Hao Ke

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Project charter](#project-charter)
  - [Background](#background)
  - [Vision](#vision)
  - [Mission](#mission)
  - [Data source](#data-source)
  - [Success criteria](#success-criteria)
- [Directory structure](#directory-structure)
- [Running the app](#running-the-app)
  - [1. Download the dataset](#1-download-the-dataset)
    - [Configure S3 credentials](#configure-s3-credentials)
    - [Usage](#usage)
      - [Download the dataset from source](#download-the-dataset-from-source)
      - [Upload to S3](#upload-to-s3)
      - [Download from S3](#download-from-s3)
      - [Download (custom S3 source, custom local destination)](#download-custom-s3-source-custom-local-destination)
  - [2. Initialize the database](#2-initialize-the-database)
    - [Create the database](#create-the-database)
    - [Adding albums](#adding-albums)
    - [Defining your engine string](#defining-your-engine-string)
      - [Local SQLite database](#local-sqlite-database)
  - [2. Configure Flask app](#2-configure-flask-app)
  - [3. Run the Flask app](#3-run-the-flask-app)
- [Running the app in Docker](#running-the-app-in-docker)
  - [1. Build the image](#1-build-the-image)
  - [2. Run the container](#2-run-the-container)
  - [3. Kill the container](#3-kill-the-container)
  - [Example using `python3` as an entry point](#example-using-python3-as-an-entry-point)
- [Testing](#testing)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Project charter

### Background

Pitchfork is a music publication company which offers spotlights, ratings, and detailed reviews for new albums, tracks, and reissues. With over 1.5 million unique visitors per month, it carries incredible influence in the music community and can significantly impact the trajectory of musicians' careers. The ratings it gives are particularly competitive, with just twelve albums having achieved a perfect 10.0 rating in the site's history. Of course there's more to music than one critic's rating, but an honor such as Best New Album or a 9+ rating can launch a musician's career to the next level and provide new access to endorsements, royalties, labels, and gigs. However, complaints are made that the site is biased and pretentious&mdash;there is little insight into how scores are developed and then reviews are presented matter-of-factly, failing to acknowledge that music is evaluated differently by different people.

### Vision

How do music characteristics affect an album's rating on Pitchfork? This app promotes transparency in the Pitchfork review process and helps readers understand and musicians create what makes "good" music in Pitchfork's eyes.

### Mission

The app predicts Pitchfork's rating given Spotify's information about an album (artist, genre, energy, tempo, etc.). Users can examine the predicted rating for the album of their choice, or tweak album qualities and study the rating's sensitivity to different inputs. 

For Pitchfork readers, having a better understanding of the site's review process can allow them to make better judgments for themselves about the quality of a particular album, accounting for potential biases for or against certain artists or styles of music. Musicians can also consult with the app during their own creation process to explore any tweaks to their music that might bump up their rating and catch the eye of a famous producer or resonate with a larger audience. 

### Data source

Pinter, A. T., J. M. Paul, J. Smith, and J. R. Brubaker. “P4KxSpotify: A Dataset of Pitchfork Music Reviews and Spotify Musical Features”. Proceedings of the International AAAI Conference on Web and Social Media, vol. 14, no. 1, May 2020, pp. 895-02, https://ojs.aaai.org/index.php/ICWSM/article/view/7355. ([paper](https://cmci.colorado.edu/idlab/assets/bibliography/pdf/Pinter2020-icwsm.pdf), [dataset](https://zenodo.org/record/3603330#.YGpIzC1h3RX))

The dataset is released under the [Creative Commons Attribution 4.0 International license](https://creativecommons.org/licenses/by/4.0/legalcode) (summary [here](https://creativecommons.org/licenses/by/4.0/)) by Anthony T. Pinter, Jacob M. Paul, Jessie Smith, and Jed R. Brubaker, and used without modification except for routine data cleaning/preparation.

### Success criteria

1. Model performance metric

  - Target RMSE of 1.0. The predicted rating should be, on average, within 1.0 of the actual rating so that users have a somewhat accurate estimate of the Pitchfork rating. It's important for readers and musicians to have some confidence in the output, so they can better contextualize Pitchfork's rating or create music (respectively). Given that lyrics are a key part of a musical composition but are not included in this dataset, this may need to be negotiated later on.

1. Business metrics

  - Average change in Pitchfork reader sentiment. A random selection of Pitchfork readers will be surveyed on their feeling of understanding the Pitchfork review process, exposed to the app, and then surveyed again. Given sufficiently quick turnaround between the first and second surveys, the impact of other variables besides the app should be negligible.

## Directory structure

```bash
├── README.md                         <- You are here
├── app
│   ├── static/                       <- CSS, JS files that remain static
│   ├── templates/                    <- HTML (or other code) that is templated and changes based on a set of inputs
│   ├── boot.sh                       <- Start up script for launching app in Docker container
│   ├── Dockerfile                    <- Dockerfile for building image to run app  
│
├── config                            <- Configuration files 
│   ├── local/                        <- Directory for keeping environment variables and other local configurations that *do not sync** to Github 
│   ├── logging/                      <- Configuration of python loggers
│   ├── flaskconfig.py                <- Configurations for Flask API 
│
├── data                              <- Data files used for analysis or by the app itself
│   ├── cleaned/                      <- Processed data
│   ├── raw/                          <- Raw datafile
│
├── deliverables/                     <- Any white papers, presentations, final work products that are presented or delivered to a stakeholder 
│
├── docs/                             <- Sphinx documentation based on Python docstrings
│
├── figures/                          <- Generated graphics and figures to be used in reporting, documentation, etc
│
├── models/                           <- Trained model objects (TMOs), model predictions, and/or model summaries
│
├── notebooks/
│   ├── archive/                      <- Develop notebooks no longer being used
│   ├── deliver/                      <- Notebooks shared with others / in final state
│   ├── develop/                      <- Current notebooks being used in development
│   ├── template.ipynb                <- Template notebook for analysis with useful imports, helper functions, and SQLAlchemy setup. 
│
├── references/                       <- Any reference material relevant to the project
│
├── src/                              <- Source data for the project 
│
├── test/                             <- Files necessary for running model tests (see documentation below) 
│
├── app.py                            <- Flask wrapper for running the model 
├── run.py                            <- Simplifies the execution of one or more of the src scripts  
├── requirements.txt                  <- Python package dependencies 
```

## Running the app

### 1. Load data into S3

#### Configure S3 credentials

Interacting with S3 requires your credentials to be loaded as environment variables:

```bash
export AWS_ACCESS_KEY_ID="MY_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="MY_SECRET_ACCESS_KEY"
```

#### Build the Docker image

```bash
docker build -t pitchfork .
```

#### Load to S3

```bash
docker run -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY pitchfork src/load_data.py
```

By default, this will load the raw data from `data/raw/P4KxSpotify.csv` into the S3 bucket `s3://2021-msia423-rice-brian/raw/P4KxSpotify.csv`. Alternative paths can be configured with `--local_path` or `--s3path`. Instead of uploading to S3, you may download from S3 by including the flag `--download`. Finally, `pandas` may be used to read the data by including `--pandas` (and optionally `--sep <VALUE>`).

### 2. Initialize the database

#### Create the database

To create the database in the location configured in `config.py` run:

`python run.py create_db --engine_string=<engine_string>`

By default, `python run.py create_db` creates a database at `sqlite:///data/albums.db`.

#### Adding albums

To add albums manually to the database:

```bash
python run.py ingest \
  --engine_string=<engine_string> \
  --album=<ALBUM> \
  --artist=<ARTIST> \
  --reviewauthor=<REVIEWAUTHOR> \
  --score=<SCORE> \
  --releaseyear=<RELEASEYEAR> \
  --reviewdate=<REVIEWDATE> \
  --recordlabel=<RECORDLABEL> \
  --genre=<GENRE> \
  --danceability=<DANCEABILITY> \
  --energy=<ENERGY> \
  --key=<KEY> \
  --loudness=<LOUDNESS> \
  --speechiness=<SPEECHINESS> \
  --acousticness=<ACOUSTICNESS> \
  --instrumentalness=<INSTRUMENTALNESS> \
  --liveness=<LIVENESS> \
  --valence=<VALENCE> \
  --tempo=<TEMPO>
```

By default, `python run.py ingest` adds *Run the Jewels 2* by Run the Jewels to the SQLite database located in `sqlite:///data/albums.db`.

#### Defining your engine string

A SQLAlchemy database connection is defined by a string with the following format:

`dialect+driver://username:password@host:port/database`

The `+dialect` is optional and if not provided, a default is used. For a more detailed description of what `dialect` and `driver` are and how a connection is made, you can see the documentation [here](https://docs.sqlalchemy.org/en/13/core/engines.html).

##### Local SQLite database

A local SQLite database can be created for development and local testing. It does not require a username or password and replaces the host and port with the path to the database file:

```python
engine_string = 'sqlite:///data/albums.db'
```

The three `///` denote that it is a relative path to where the code is being run (which is from the root of this directory).

You can also define the absolute path with four `////`, for example:

```python
engine_string = 'sqlite://///Users/brianrice/dev/2021-msia423-rice-brian-project/data/albums.db'
```

### 2. Configure Flask app

`config/flaskconfig.py` holds the configurations for the Flask app. It includes the following configurations:

```python
DEBUG = True  # Keep True for debugging, change to False when moving to production 
LOGGING_CONFIG = 'config/logging/local.conf'  # Path to file that configures Python logger
HOST = '0.0.0.0' # the host that is running the app. 0.0.0.0 when running locally 
PORT = 5000  # What port to expose app on. Must be the same as the port exposed in app/Dockerfile 
SQLALCHEMY_DATABASE_URI = 'sqlite:///data/albums.db'  # URI (engine string) for database that contains albums
APP_NAME = 'pitchfork'
SQLALCHEMY_TRACK_MODIFICATIONS = True 
SQLALCHEMY_ECHO = False  # If true, SQL for queries made will be printed
MAX_ROWS_SHOW = 100 # Limits the number of rows returned from the database 
```

### 3. Run the Flask app

To run the Flask app, run:

```bash
python app.py
```

You should now be able to access the app at http://0.0.0.0:5000/ in your browser.

## Running the app in Docker

### 1. Build the image

The Dockerfile for running the flask app is in the `app/` folder. To build the image, run from this directory (the root of the repo):

```bash
 docker build -f app/Dockerfile -t pitchfork .
```

This command builds the Docker image, with the tag `pitchfork`, based on the instructions in `app/Dockerfile` and the files existing in this directory.

### 2. Run the container

To run the app, run from this directory:

```bash
docker run -p 5000:5000 --name test pitchfork
```

You should now be able to access the app at http://0.0.0.0:5000/ in your browser.

This command runs the `pitchfork` image as a container named `test` and forwards the port 5000 from container to your laptop so that you can access the Flask app exposed through that port.

If `PORT` in `config/flaskconfig.py` is changed, this port should be changed accordingly (as should the `EXPOSE 5000` line in `app/Dockerfile`)

### 3. Kill the container

Once finished with the app, you will need to kill the container. To do so:

```bash
docker kill test 
```

where `test` is the name given in the `docker run` command.

### Example using `python3` as an entry point

We have included another example of a Dockerfile, `app/Dockerfile_python`, that has `python3` as the entry point such that when you run the image as a container, the command `python3` is run followed by the arguments given in the `docker run` command after the image name.

To build this image:

```bash
 docker build -f app/Dockerfile_python -t pitchfork .
```

then run the `docker run` command:

```bash
docker run -p 5000:5000 --name test pitchfork app.py
```

The new image defines the entry point command as `python3`. Building the sample pitchfork image this way will require initializing the database prior to building the image so that it is copied over, rather than created when the container is run. Therefore, please **do the step [Create the database](#create-the-database) above before building the image**.

## Testing

From within the Docker container, the following command should work to run unit tests when run from the root of the repository:

```bash
python -m pytest
```

Using Docker, run the following if the image has not been built yet:

```bash
 docker build -f app/Dockerfile_python -t pitchfork .
```

To run the tests, run:

```bash
 docker run pitchfork -m pytest
```
