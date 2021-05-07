"""
Move data between a local filesystem and S3 bucket.

Default behavior uploads the raw dataset from the local filesystem to my
(Brian's) S3 bucket. Additional options allow configuration for downloading
instead or using different source/destination filepaths.

Copyright 2020, Chloe Mawer
"""
import argparse
import logging
import re
import requests

import boto3
import botocore
import pandas as pd

logging.basicConfig(
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s", level=logging.DEBUG
)

# Limit unnecessary logs from dependencies
logging.getLogger("aiobotocore").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("boto3").setLevel(logging.ERROR)
logging.getLogger("botocore").setLevel(logging.ERROR)
logging.getLogger("fsspec").setLevel(logging.ERROR)
logging.getLogger("s3fs").setLevel(logging.ERROR)
logging.getLogger("s3transfer").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

logger = logging.getLogger("s3")

MISSING_AWS_CREDENTIALS_MSG = "Please provide AWS credentials via AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables."
RAW_DATA_SOURCE_URL = (
    "https://zenodo.org/record/3603330/files/output-data.csv?download=1"
)


def parse_s3(s3path):
    """
    Split an S3 filepath into the primary bucket and subsequent path.

    Args:
        s3path (str): File path in S3

    Returns:
        tuple(str, str): Tuple containing S3 bucket name and S3 path.
    """
    regex = r"s3://([\w._-]+)/([\w./_-]+)"

    m = re.match(regex, s3path)
    try:
        s3bucket = m.group(1)
        s3path = m.group(2)
    except AttributeError:
        # If no match is found, `m` is None
        logger.error(
            "The provided S3 location could not be parsed. Please confirm your" +
            "path follows the structure \"s3://bucket/path\""
        )
        raise
    else:
        return s3bucket, s3path


def upload_file_to_s3(local_path, s3path):
    """
    Upload a local file to S3.

    Args:
        local_path (str): File name or path to local file to upload.
        s3path (str): Destination path in S3.
    """
    s3bucket, s3_just_path = parse_s3(s3path)

    s3 = boto3.resource("s3")
    bucket = s3.Bucket(s3bucket)

    try:
        bucket.upload_file(local_path, s3_just_path)
    except botocore.exceptions.NoCredentialsError:
        logger.error(MISSING_AWS_CREDENTIALS_MSG)
    else:
        logger.info("Data uploaded from %s to %s", local_path, s3path)


def upload_to_s3_pandas(local_path, s3path, sep=","):
    """
    Upload a pandas.DataFrame to S3.

    Args:
        local_path ([type]): [description]
        s3path ([type]): [description]
        sep (str, optional): [description]. Defaults to ",".
    """
    df = pd.read_csv(local_path, sep=sep)

    try:
        df.to_csv(s3path, sep=sep, index=False)
    except botocore.exceptions.NoCredentialsError:
        logger.error(MISSING_AWS_CREDENTIALS_MSG)
    else:
        logger.info("Data uploaded from %s to %s", local_path, s3path)


def download_file_from_s3(local_path, s3path):
    """
    Download a file from S3.

    Args:
        local_path (str): Destination file or path on local machine
        s3path (str): File or path to download from S3
    """
    s3bucket, s3_just_path = parse_s3(s3path)

    s3 = boto3.resource("s3")
    bucket = s3.Bucket(s3bucket)

    try:
        bucket.download_file(s3_just_path, local_path)
    except botocore.exceptions.NoCredentialsError:
        logger.error(MISSING_AWS_CREDENTIALS_MSG)
    else:
        logger.info("Data downloaded from %s to %s", s3path, local_path)


def download_from_s3_pandas(local_path, s3path, sep=","):
    """
    Download a pandas.DataFrame from S3.

    Args:
        local_path (str): Destination file or path on local machine
        s3path (str): File or path to download from S3
        sep (str, optional): Field separator in S3 file. Defaults to ",".
    """
    try:
        df = pd.read_csv(s3path, sep=sep)
    except botocore.exceptions.NoCredentialsError:
        logger.error(MISSING_AWS_CREDENTIALS_MSG)
    else:
        df.to_csv(local_path, sep=sep, index=False)
        logger.info("Data downloaded from %s to %s", s3path, local_path)


def download_raw_data(local_destination):
    """
    Download the original dataset from source.

    Args:
        local_destination (str): Destination file or path on local machine
    """
    response = requests.get(RAW_DATA_SOURCE_URL)
    if response.status_code == 200:
        with open(local_destination, "wb") as file:
            for chunk in response:
                file.write(chunk)
        logger.info("Downloaded raw data to %s", local_destination)
    elif response.status_code < 200:
        logger.warning("Request received but not immediately processed (unusual)")
    else:
        logger.warning(
            "Unsuccesful status code received when trying to download raw datafile"
        )
