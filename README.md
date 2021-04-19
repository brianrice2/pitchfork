# p4k.ai

Developer: Brian Rice

Quality Assurance: Cheng Hao Ke

---

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
    - [1. Initialize the database](#1-initialize-the-database)
      - [Create the database](#create-the-database)
      - [Adding songs](#adding-songs)
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
    + Target RMSE of 1.0. The predicted rating should be, on average, within 1.0 of the actual rating so that users have a somewhat accurate estimate of the Pitchfork rating. It's important for readers and musicians to have some confidence in the output, so they can better contextualize Pitchfork's rating or create music (respectively). Given that lyrics are a key part of a musical composition but are not included in this dataset, this may need to be negotiated later on.
2. Business metrics
    + Average actual Pitchfork rating. Results will be compared via (randomized) A/B testing between musicians who did use the app versus those who did not. 
    + Average change in Pitchfork reader sentiment. A random selection of Pitchfork readers will be surveyed on their feeling of understanding the Pitchfork review process, exposed to the app, and then surveyed again. Given sufficiently quick turnaround between the first and second surveys, the impact of other variables besides the app should be negligible.

## Directory structure 

```
├── README.md                         <- You are here
├── app
│   ├── static/                       <- CSS, JS files that remain static
│   ├── templates/                    <- HTML (or other code) that is templated and changes based on a set of inputs
│   ├── boot.sh                       <- Start up script for launching app in Docker container.
│   ├── Dockerfile                    <- Dockerfile for building image to run app  
│
├── config                            <- Directory for configuration files 
│   ├── local/                        <- Directory for keeping environment variables and other local configurations that *do not sync** to Github 
│   ├── logging/                      <- Configuration of python loggers
│   ├── flaskconfig.py                <- Configurations for Flask API 
│
├── data                              <- Folder that contains data used or generated. Only the external/ and sample/ subdirectories are tracked by git. 
│   ├── external/                     <- External data sources, usually reference data,  will be synced with git
│   ├── sample/                       <- Sample data used for code development and testing, will be synced with git
│
├── deliverables/                     <- Any white papers, presentations, final work products that are presented or delivered to a stakeholder 
│
├── docs/                             <- Sphinx documentation based on Python docstrings. Optional for this project. 
│
├── figures/                          <- Generated graphics and figures to be used in reporting, documentation, etc
│
├── models/                           <- Trained model objects (TMOs), model predictions, and/or model summaries
│
├── notebooks/
│   ├── archive/                      <- Develop notebooks no longer being used.
│   ├── deliver/                      <- Notebooks shared with others / in final state
│   ├── develop/                      <- Current notebooks being used in development.
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

### 1. Initialize the database

#### Create the database

To create the database in the location configured in `config.py` run: 

`python run.py create_db --engine_string=<engine_string>`

By default, `python run.py create_db` creates a database at `sqlite:///data/tracks.db`.

#### Adding songs

To add songs to the database:

`python run.py ingest --engine_string=<engine_string> --artist=<ARTIST> --title=<TITLE> --album=<ALBUM>`

By default, `python run.py ingest` adds *Minor Cause* by Emancipator to the SQLite database located in `sqlite:///data/tracks.db`.

#### Defining your engine string

A SQLAlchemy database connection is defined by a string with the following format:

`dialect+driver://username:password@host:port/database`

The `+dialect` is optional and if not provided, a default is used. For a more detailed description of what `dialect` and `driver` are and how a connection is made, you can see the documentation [here](https://docs.sqlalchemy.org/en/13/core/engines.html). We will cover SQLAlchemy and connection strings in the SQLAlchemy lab session on 

##### Local SQLite database 

A local SQLite database can be created for development and local testing. It does not require a username or password and replaces the host and port with the path to the database file: 

```python
engine_string = 'sqlite:///data/tracks.db'
```

The three `///` denote that it is a relative path to where the code is being run (which is from the root of this directory).

You can also define the absolute path with four `////`, for example:

```python
engine_string = 'sqlite://///Users/cmawer/Repos/2020-MSIA423-template-repository/data/tracks.db'
```


### 2. Configure Flask app 

`config/flaskconfig.py` holds the configurations for the Flask app. It includes the following configurations:

```python
DEBUG = True  # Keep True for debugging, change to False when moving to production 
LOGGING_CONFIG = 'config/logging/local.conf'  # Path to file that configures Python logger
HOST = '0.0.0.0' # the host that is running the app. 0.0.0.0 when running locally 
PORT = 5000  # What port to expose app on. Must be the same as the port exposed in app/Dockerfile 
SQLALCHEMY_DATABASE_URI = 'sqlite:///data/tracks.db'  # URI (engine string) for database that contains tracks
APP_NAME = 'penny-lane'
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
 docker build -f app/Dockerfile -t pennylane .
```

This command builds the Docker image, with the tag `pennylane`, based on the instructions in `app/Dockerfile` and the files existing in this directory.
 
### 2. Run the container 

To run the app, run from this directory: 

```bash
docker run -p 5000:5000 --name test pennylane
```
You should now be able to access the app at http://0.0.0.0:5000/ in your browser.

This command runs the `pennylane` image as a container named `test` and forwards the port 5000 from container to your laptop so that you can access the flask app exposed through that port. 

If `PORT` in `config/flaskconfig.py` is changed, this port should be changed accordingly (as should the `EXPOSE 5000` line in `app/Dockerfile`)

### 3. Kill the container 

Once finished with the app, you will need to kill the container. To do so: 

```bash
docker kill test 
```

where `test` is the name given in the `docker run` command.

### Example using `python3` as an entry point

We have included another example of a Dockerfile, `app/Dockerfile_python` that has `python3` as the entry point such that when you run the image as a container, the command `python3` is run, followed by the arguments given in the `docker run` command after the image name. 

To build this image: 

```bash
 docker build -f app/Dockerfile_python -t pennylane .
```

then run the `docker run` command: 

```bash
docker run -p 5000:5000 --name test pennylane app.py
```

The new image defines the entry point command as `python3`. Building the sample PennyLane image this way will require initializing the database prior to building the image so that it is copied over, rather than created when the container is run. Therefore, please **do the step [Create the database](#create-the-database) above before building the image**.

# Testing

From within the Docker container, the following command should work to run unit tests when run from the root of the repository: 

```bash
python -m pytest
``` 

Using Docker, run the following, if the image has not been built yet:

```bash
 docker build -f app/Dockerfile_python -t pennylane .
```

To run the tests, run: 

```bash
 docker run penny -m pytest
```
 
