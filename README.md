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
├── docs/                             <- Sphinx documentation based on Python docstrings
│
├── notebooks/
│   ├── archive/                      <- Develop notebooks no longer being used
│   ├── deliver/                      <- Notebooks shared with others / in final state
│   ├── develop/                      <- Current notebooks being used in development
│   ├── template.ipynb                <- Template notebook for analysis with useful imports, helper functions, and SQLAlchemy setup. 
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

`docker build -t pitchfork .`

#### Download raw data and upload to S3

```bash
docker run -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY pitchfork src/load_data.py
```

By default, this will download the original data to `data/raw/P4KxSpotify.csv` and then upload into the S3 bucket `s3://2021-msia423-rice-brian/raw/P4KxSpotify.csv`. Alternative paths can be configured with `--local_path` or `--s3path`. Instead of uploading to S3, you may download from S3 by including the flag `--download`. Finally, `pandas` may be used to read the data by including `--pandas` (and optionally `--sep <VALUE>`).

### 2. Initialize the database

#### Configure environment variables

```bash
export MYSQL_USER="MY_USERNAME"
export MYSQL_PASSWORD="MY_PASSWORD"
export MYSQL_HOST="MY_HOST"
export MYSQL_PORT="MY_PORT"
export MYSQL_DATABASE="MY_DATABASE"
```

#### Create the database

To create the database in the location configured in `config.py` run:

`docker run -e MYSQL_HOST -e MYSQL_PORT -e MYSQL_USER -e MYSQL_PASSWORD -e MYSQL_DATABASE pitchfork run.py create_db`

By default, `python run.py create_db` creates a database at `sqlite:///data/msia423_db.db`.

##### Local SQLite database

A local SQLite database can be created for development and local testing. It does not require a username or password and replaces the host and port with the path to the database file:

`engine_string = 'sqlite:///data/msia423_db.db'`

##### RDS instance

Specify your environment variables according to your own RDS instance username and password, host (endpoint), port, and database name.
