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
  - [1. Load data into S3](#1-load-data-into-s3)
    - [Configure S3 credentials](#configure-s3-credentials)
    - [Build the Docker image](#build-the-docker-image)
    - [Download raw data and upload to S3](#download-raw-data-and-upload-to-s3)
  - [2. Initialize the database](#2-initialize-the-database)
    - [Configure environment variables](#configure-environment-variables)
    - [Create the database](#create-the-database)
      - [Local SQLite database](#local-sqlite-database)
      - [RDS instance](#rds-instance)
    - [Ingest the data](#ingest-the-data)
  - [3. Train a machine learning model](#3-train-a-machine-learning-model)
  - [4. Running the web application](#4-running-the-web-application)
    - [Custom connection string](#custom-connection-string)
    - [The verbose way](#the-verbose-way)
  - [5. Deployment to AWS ECS](#5-deployment-to-aws-ecs)
  - [0. Testing](#0-testing)
    - [Unit tests](#unit-tests)
    - [Reproducibility tests](#reproducibility-tests)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Project charter

### Background

Pitchfork is a music publication company which offers spotlights, ratings, and detailed reviews for new albums, tracks, and reissues. With over 1.5 million unique visitors per month, it carries incredible influence in the music community and can significantly impact the trajectory of musicians' careers. The ratings it gives are particularly competitive, with just twelve albums having achieved a perfect 10.0 rating on their initial release in the site's history. Of course there's more to music than one critic's rating, but an honor such as Best New Album or a 9+ rating can launch a musician's career to the next level and provide new access to endorsements, royalties, labels, and gigs. However, complaints are made that the site is biased and pretentious&mdash;there is little insight into how scores are developed and then reviews are presented matter-of-factly, failing to acknowledge that music is evaluated differently by different people.

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

2. Business metrics

  - Average change in Pitchfork reader sentiment. A random selection of Pitchfork readers will be surveyed on their feeling of understanding the Pitchfork review process, exposed to the app, and then surveyed again. Given sufficiently quick turnaround between the first and second surveys, the impact of other variables besides the app should be negligible.

## Directory structure

```
├── README.md                         <- You are here!
|
├── app/                              <- Configuration files 
│   ├── static/                       <- Static CSS, JS, etc. files
│   ├── templates/                    <- HTML (or other code) that is templated and changes
|   |                                      based on a set of inputs
│   └── Dockerfile                    <- Defines the Docker image for running the web app
│
├── config/                           <- Configuration files 
│   ├── local/                        <- Private configuration files and environment variable
|   |                                      settings (not tracked)
│   ├── logging/                      <- Configuration of Python loggers
│   ├── flaskconfig.py                <- Configurations for Flask API
│   └── pipeline.yaml                 <- Parameter values passed to functions. Tracked
|                                           for reproducibility.
│
├── copilot/                          <- Deployment configuration for AWS Copilot
|
├── data/                             <- Data files used for analysis or by the app itself
│   ├── cleaned/                      <- Processed data
│   └── raw/                          <- Raw data
|
├── deliverables/                     <- Final presentations, white papers, etc. for
|                                          stakeholders
│
├── docs/                             <- Sphinx documentation based on Python docstrings
│
├── notebooks/
│   ├── archive/                      <- Develop notebooks no longer being used
│   ├── deliver/                      <- Notebooks shared with others / in final state
│   └── develop/                      <- Current notebooks being used in development
│
├── src/                              <- Source data for the project 
│
├── tests/                            <- Pytest unit tests
│
├── app.py                            <- Flask wrapper for running the model
├── Dockerfile_pipeline               <- Defines the Docker image for the data cleaning and
|                                          modeling pipeline
├── Dockerfile_python                 <- Defines the Docker image for ingesting data & creating
|                                          the database
├── Makefile                          <- Defines handy shortcuts for executing app functionality:
|                                          ingesting data, training a model, running the web
|                                          app, unit tests, and more
├── requirements.txt                  <- Python package dependencies
└── run.py                            <- Orchestration function to simplify the execution of
                                           one or more of the src scripts
```

## Running the app

### 1. Load data into S3

#### Configure S3 credentials

Interacting with S3 requires your credentials to be loaded as environment variables. You may find it convenient to put a file with the following information in `config/local/` (where it will not sync with git) and then `source` this file to set these fields.

```bash
export AWS_ACCESS_KEY_ID="MY_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="MY_SECRET_ACCESS_KEY"
```

#### Build the Docker image

```bash
docker build -f Dockerfile_python -t pitchfork-setup .
````

#### Download raw data and upload to S3

```bash
docker run -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY pitchfork-setup run.py load_data
```

By default, this will download the original data to `data/raw/P4KxSpotify.csv` and then upload into the S3 bucket `s3://2021-msia423-rice-brian/data/raw/P4KxSpotify.csv`.

Optional arguments:

- `--local_path` and `--s3path` for configuring alternative paths
- `--download` flag for downloading instead of uploading
- `--pandas` flag for uploading or downloading using `pandas`
  - `--sep` for specifying a different separator (default "," as the dataset is CSV-formatted)

### 2. Initialize the database

#### Configure environment variables

The database can be created and configured differently depending on the values of a few environment variables. Again, I recommend sourcing from a secret config file in `config/local/`.

```bash
export MYSQL_USER="MY_USERNAME"
export MYSQL_PASSWORD="MY_PASSWORD"
export MYSQL_HOST="MY_HOST"
export MYSQL_PORT="MY_PORT"
export MYSQL_DATABASE="MY_DATABASE"
```

These variables are interpreted to create a SQLAlchemy database URI (an "engine string"). So instead of specifying all these variables, you can also pass this engine string directly as a command-line argument (see below).

#### Create the database

To create the database according to your `MYSQL_*` environment variables (either locally or in RDS), run:

```bash
docker run \
  -e MYSQL_HOST \
  -e MYSQL_PORT \
  -e MYSQL_USER \
  -e MYSQL_PASSWORD \
  -e MYSQL_DATABASE \
  pitchfork-setup run.py create_db
```

By default, `run.py create_db` creates a local SQLite database at `sqlite:///data/msia423_db.db`.

If you know the engine string already, you can simply run:

```bash
docker run pitchfork-setup run.py create_db --engine_string <MY_ENGINE_STRING>
```

##### Local SQLite database

A local SQLite database can be created for development and local testing. It does not require a username or password and replaces the host and port with the path to the database file:

`engine_string = 'sqlite:///data/msia423_db.db'`

Keep in mind that if the local database is created inside of Docker, it will remain in the writable layer unless a persistent storage drive is mounted. Assuming the current working directory is the root level of this repository:

```bash
docker run -v "$(pwd)"/data/:/app/data/ pitchfork-setup run.py create_db
```

##### RDS instance

Specify your environment variables according to your own RDS instance username and password, host (endpoint), port, and database name, then run the same command.

You can inspect the database from a MySQL client via Docker:

```bash
docker run -it --rm \
  mysql:5.7.33 \
  mysql \
  -h$MYSQL_HOST \
  -u$MYSQL_USER \
  -p$MYSQL_PASSWORD
```

And then inside MySQL:

```MySQL
SHOW DATABASES;
USE msia423_db;
SHOW TABLES;
SELECT * FROM albums LIMIT 5;
```

#### Ingest the data

To load a sample album into the database after it has been created, use:

```bash
docker run \
  -e MYSQL_HOST \
  -e MYSQL_PORT \
  -e MYSQL_USER \
  -e MYSQL_PASSWORD \
  -e MYSQL_DATABASE \
  pitchfork-setup run.py ingest_album
```

To instead load the contents of a CSV file (again after the table has been created), use:

```bash
docker run \
  -e MYSQL_HOST \
  -e MYSQL_PORT \
  -e MYSQL_USER \
  -e MYSQL_PASSWORD \
  -e MYSQL_DATABASE \
  pitchfork-setup run.py ingest_dataset --file "path/to/my/file.csv"
```

### 3. Train a machine learning model

Once the raw data has been downloaded to S3 through the process above, we can train a model to predict the Pitchfork rating for an album! `Dockerfile_pipeline` defines an image to:

1. Load the existing raw data file
1. Clean and process it
1. Train a gradient-boosted tree model
1. Score the model
1. Evaluate its performance

```bash
docker build -f Dockerfile_pipeline -t pitchfork-pipeline .
docker run \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  pitchfork-pipeline pipeline
```

Artifacts are saved locally and to S3 for future use (again, beware the writable layer). If you prefer to retain the local copies you may mount a local volume, for example through `docker run -v "$(pwd)"/:/app/ ...`. Since artifacts are produced in both `data/` and `models/`, you must mount the root directory and not only the `data/` folder as was done earlier.

### 4. Running the web application

Sure, creating and moving data into databases is fun, but eventually we should run the web app. To do so, first ensure the database is not already created or populated and run the command below most closely suited to your situation (it will still work, but the records will be added again, resulting in duplicate entries). You may either use a local SQLite database (default behavior if `MYSQL_*` or `SQLALCHEMY_DATABASE_URI` are not set) or a MySQL database running on RDS.

Please note that, apart from the database specification, S3 credentials are required for the app to function as it pulls raw data and other artifacts during the pipeline from S3. Since the app creates and populates the database that it displays and interacts with, you must also have the appropriate database permissions for creating and inserting into tables!

You have two options: specifying the `SQLALCHEMY_DATABASE_URI` connection string directly, or providing all the necessary `MYSQL_*` information.

#### Custom connection string

```bash
docker build -f app/Dockerfile -t pitchfork-app .
docker run \
  -p 5000:5000 \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  -e SQLALCHEMY_DATABASE_URI \
  pitchfork-app
```

#### The verbose way

```bash
docker build -f app/Dockerfile -t pitchfork-app .
docker run \
  -p 5000:5000 \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  -e MYSQL_HOST \
  -e MYSQL_PORT \
  -e MYSQL_USER \
  -e MYSQL_PASSWORD \
  -e MYSQL_DATABASE \
  pitchfork-app
```

### 5. Deployment to AWS ECS

If you wish to deploy the application onto ECS, view the [copilot manifest](/copilot/app/manifest.yml) for an example configuration. As personal information like a username and password is required, you'll need to use secrets to securely store this information ([tutorial here](https://ecsworkshop.com/secrets/05-inject-params/)).

Your deployment to ECS is outside the scope and responsibility of this application, but the manifest is included for reference purposes to give an idea of what's required. 

### 0. Testing

#### Unit tests

To run the unit tests in a Docker container (from the `pitchfork-pipeline` image, specifically), run:

```bash
docker run pitchfork-pipeline unit_tests
```

#### Reproducibility tests

In addition, there are some tests to ensure that the pipeline is executed in a reproducible manner.:

With Docker (using the same `Dockerfile_pipeline` as the unit tests):

```bash
docker run -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY pitchfork-pipeline reproducibility_tests
```

Please note S3 credentials are required as the reproducibility pipeline begins by pulling raw data from S3.
