import pytest

from src import load_data


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
