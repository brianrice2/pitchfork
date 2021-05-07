import os

import botocore
import pytest
import pandas as pd

from src import load_data


# Manually-checked characteristics of raw dataset
RAW_DATA_NROWS = 18403
RAW_DATA_NCOLS = 18
RAW_DATA_COLNAMES = [
    "artist",
    "album",
    "reviewauthor",
    "score",
    "releaseyear",
    "reviewdate",
    "recordlabel",
    "genre",
    "danceability",
    "energy",
    "key",
    "loudness",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
]


@pytest.fixture
def raw_data_as_df(local_destination=load_data.DEFAULT_RAW_DATA_PATH):
    """Download raw data and return as a `pandas.DataFrame`."""
    load_data.download_raw_data(local_destination)
    assert os.path.isfile(local_destination)

    df = pd.read_csv(local_destination)

    return df


def test_raw_data_dimensions(raw_data_as_df):
    """Raw data has the expected dimensions."""
    assert raw_data_as_df.shape == (RAW_DATA_NROWS, RAW_DATA_NCOLS)


def test_raw_data_columns(raw_data_as_df):
    """Raw data has the expected columns."""
    assert raw_data_as_df.columns.to_list() == RAW_DATA_COLNAMES


def test_parse_s3():
    """`parse_s3()` correctly splits bucket and path."""
    bucket, path = load_data.parse_s3("s3://my-bucket/my-path")
    assert bucket == "my-bucket"
    assert path == "my-path"


def test_parse_s3_long_path():
    """`parse_s3()` correctly splits bucket at the first "/"."""
    bucket, path = load_data.parse_s3("s3://my-bucket/my/super/long/path")
    assert bucket == "my-bucket"
    assert path == "my/super/long/path"


def test_parse_s3_missing_path():
    """Missing S3 path (only bucket provided)."""
    with pytest.raises(AttributeError):
        bucket, path = load_data.parse_s3("s3://my-bucket/")


def test_upload_file_to_s3_idempotent(
    raw_data_as_df,
    local_source=load_data.DEFAULT_RAW_DATA_PATH,
    s3_destination=load_data.DEFAULT_S3_LOCATION,
):
    """Uploading to S3 should not change the data."""
    load_data.upload_file_to_s3(local_source, s3_destination)
    df_actual = pd.read_csv(s3_destination)

    pd.testing.assert_frame_equal(raw_data_as_df, df_actual)


def test_upload_file_to_s3_missing_local_source():
    """Try to upload a local file that does not exist."""
    with pytest.raises(FileNotFoundError):
        load_data.upload_file_to_s3(
            "this-path-does-not-exist.csv",
            load_data.DEFAULT_S3_LOCATION
        )


def test_upload_to_s3_pandas_idempotent(
    raw_data_as_df,
    local_source=load_data.DEFAULT_RAW_DATA_PATH,
    s3_destination=load_data.DEFAULT_S3_LOCATION,
):
    """Uploading to S3 via `pandas` should not change the data."""
    load_data.upload_to_s3_pandas(local_source, s3_destination)
    df_actual = pd.read_csv(s3_destination)

    pd.testing.assert_frame_equal(raw_data_as_df, df_actual)


def test_upload_to_s3_pandas_missing_local_source():
    """Try to upload a local file that does not exist."""
    with pytest.raises(FileNotFoundError):
        load_data.upload_to_s3_pandas(
            "this-path-does-not-exist.csv",
            load_data.DEFAULT_S3_LOCATION
        )


def test_upload_to_s3_pandas_wrong_separator(
    raw_data_as_df,
    local_source=load_data.DEFAULT_RAW_DATA_PATH,
    s3_destination=load_data.DEFAULT_S3_LOCATION,
):
    """Pass an incorrect value separator to `pandas.read_csv()`."""
    with pytest.raises(pd.errors.ParserError):
        load_data.upload_to_s3_pandas(local_source, s3_destination, sep=";")


def test_s3_upload_download_idempotent(
    raw_data_as_df,
    local_path=load_data.DEFAULT_RAW_DATA_PATH,
    s3path=load_data.DEFAULT_S3_LOCATION,
):
    """Uploading to and then downloading from S3 should not change the data."""
    load_data.upload_file_to_s3(local_path, s3path)
    load_data.download_file_from_s3(local_path, s3path)
    df_actual = pd.read_csv(local_path)

    pd.testing.assert_frame_equal(raw_data_as_df, df_actual)


def test_s3_pandas_upload_download_idempotent(
    raw_data_as_df,
    local_path=load_data.DEFAULT_RAW_DATA_PATH,
    s3path=load_data.DEFAULT_S3_LOCATION,
):
    """Uploading and downloading from S3 via `pandas` should not change the data."""
    load_data.upload_to_s3_pandas(local_path, s3path)
    load_data.download_from_s3_pandas(s3path, local_path)
    df_actual = pd.read_csv(local_path)

    pd.testing.assert_frame_equal(raw_data_as_df, df_actual)


def test_download_file_from_s3_no_path(local_destination=load_data.DEFAULT_RAW_DATA_PATH):
    """Missing S3 path (only bucket provided)."""
    with pytest.raises(AttributeError):
        load_data.download_file_from_s3(local_destination, "s3://my-bucket")


def test_download_missing_file_from_s3(local_destination=load_data.DEFAULT_RAW_DATA_PATH):
    """Attempt to download a file from S3 that does not exist."""
    with pytest.raises(botocore.exceptions.ClientError):
        load_data.download_file_from_s3(local_destination, "s3://this-path/does-not-exist")


def test_download_from_s3_pandas_no_path(local_destination=load_data.DEFAULT_RAW_DATA_PATH):
    """
    Missing S3 path (only bucket provided).

    Since `pandas` reads directly from S3, this error should be different than
    the error from no_such_bucket.
    """
    with pytest.raises(ValueError):
        load_data.download_from_s3_pandas(local_destination, "s3://my-bucket/")


def test_download_from_s3_pandas_no_such_bucket(local_destination=load_data.DEFAULT_RAW_DATA_PATH):
    """Attempt to download a file from S3 bucket that does not exist."""
    with pytest.raises(FileNotFoundError):
        load_data.download_from_s3_pandas(local_destination, "s3://this-bucket/does-not-exist")