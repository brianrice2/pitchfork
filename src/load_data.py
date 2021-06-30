"""
Move data between a local filesystem and S3 bucket.

Copyright 2020, Chloe Mawer
"""
import logging.config
import re
import typing

import boto3
import botocore
import pandas as pd
import requests

logger = logging.getLogger(__name__)

# Limit unnecessary logs from dependencies
logging.getLogger("aiobotocore").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("boto3").setLevel(logging.ERROR)
logging.getLogger("botocore").setLevel(logging.ERROR)
logging.getLogger("fsspec").setLevel(logging.ERROR)
logging.getLogger("s3fs").setLevel(logging.ERROR)
logging.getLogger("s3transfer").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

MISSING_AWS_CREDENTIALS_MSG = """Please provide AWS credentials via AWS_ACCESS_KEY_ID
and AWS_SECRET_ACCESS_KEY environment variables."""
RAW_DATA_SOURCE_URL = "https://zenodo.org/record/3603330/files/output-data.csv?download=1"


def parse_s3(s3path: str) -> typing.Tuple[str, str]:
    """
    Split an S3 filepath into the bucket name and subsequent path.

    Args:
        s3path (str): File path in S3 (including "s3://" prefix)

    Returns:
        tuple(str, str): Tuple containing S3 bucket name and S3 path

    Raises:
        `ValueError` if `s3path` not in the format "s3://bucket/path"
    """
    # Search string for bucket and path names
    pattern = r"s3://([\w._-]+)/([\w./_-]+)"
    matches = re.match(pattern, s3path)

    if matches:
        s3bucket = matches.group(1)
        s3path = matches.group(2)

        return s3bucket, s3path

    # If no matches were found, the user entered bad input
    raise ValueError(
        """The provided S3 location could not be parsed.
        Please confirm your path follows the structure "s3://bucket/path".
    """)


def upload_file_to_s3(local_path: str, s3path: str) -> None:
    """
    Upload a local file to S3.

    Args:
        local_path (str): File name or path to local file to upload.
        s3path (str): Destination path in S3.

    Returns:
        None
    """
    # Separate bucket from path for boto3
    s3bucket, s3_just_path = parse_s3(s3path)
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(s3bucket)

    try:
        bucket.upload_file(local_path, s3_just_path)
    except botocore.exceptions.NoCredentialsError:
        logger.warning(MISSING_AWS_CREDENTIALS_MSG)
        logger.warning("Data not uploaded")
    except boto3.exceptions.S3UploadFailedError:
        logger.warning("Don't have appropriate permissions to upload. Skipped upload.")
    else:
        logger.info("Data uploaded from %s to %s", local_path, s3path)


def upload_to_s3_pandas(local_path: str, s3path: str, sep: str = ",") -> None:
    """
    Upload a `pandas.DataFrame` to S3.

    Args:
        local_path (str): File name or path to local file to upload.
        s3path (str): Destination path in S3.
        sep (str, optional): Field separator. Defaults to ",".

    Returns:
        None
    """
    # Assumes that input is already in a compatible format
    data = pd.read_csv(local_path, sep=sep)

    try:
        data.to_csv(s3path, sep=sep, index=False)
    except botocore.exceptions.NoCredentialsError:
        logger.warning(MISSING_AWS_CREDENTIALS_MSG)
        logger.warning("Data not uploaded")
    except boto3.exceptions.S3UploadFailedError:
        logger.warning("Don't have appropriate permissions to upload. Skipped upload.")
    else:
        logger.info("Data uploaded from %s to %s", local_path, s3path)


def download_file_from_s3(local_path: str, s3path: str) -> None:
    """
    Download a file from S3.

    Args:
        local_path (str): Destination file or path on local machine
        s3path (str): File or path to download from S3

    Returns:
        None
    """
    # Separate bucket from path for boto3
    s3bucket, s3_just_path = parse_s3(s3path)
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(s3bucket)

    try:
        bucket.download_file(s3_just_path, local_path)
    except botocore.exceptions.NoCredentialsError:
        logger.error(MISSING_AWS_CREDENTIALS_MSG)
        logger.error("Data not downloaded")
    else:
        logger.info("Data downloaded from %s to %s", s3path, local_path)


def download_from_s3_pandas(local_path: str, s3path: str, sep: str = ",") -> None:
    """
    Download a `pandas.DataFrame` from S3.

    Args:
        local_path (str): Destination file or path on local machine
        s3path (str): File or path to download from S3
        sep (str, optional): Field separator in S3 file. Defaults to ",".

    Returns:
        None
    """
    try:
        # Assumes that file is already in a compatible format
        data = pd.read_csv(s3path, sep=sep)
    except botocore.exceptions.NoCredentialsError:
        logger.error(MISSING_AWS_CREDENTIALS_MSG)
        logger.error("Data not downloaded")
    else:
        data.to_csv(local_path, sep=sep, index=False)
        logger.info("Data downloaded from %s to %s", s3path, local_path)


def download_raw_data(local_destination: str) -> None:
    """
    Download the original dataset from source.

    Args:
        local_destination (str): Destination file or path on local machine

    Returns:
        None
    """
    # Download raw data from the internet
    response = requests.get(RAW_DATA_SOURCE_URL)

    if response.ok:
        with open(local_destination, "wb") as file:
            for chunk in response:
                file.write(chunk)
        logger.info("Downloaded raw data to %s", local_destination)
    else:
        logger.warning(
            "Unsuccesful status code received when trying to download raw datafile"
        )
