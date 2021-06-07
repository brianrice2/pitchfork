import numpy as np
import pandas as pd
import pytest

from src import model


@pytest.fixture
def dummy_df():
    dummy_df = pd.DataFrame(data={"col1": list(range(100)), "target": list(range(100))})
    return dummy_df


def test_parse_ratio():
    """Parses ratio as expected."""
    ratio = "6:2:2"
    sizes = model.parse_ratio(ratio)
    assert sizes == [0.6, 0.2, 0.2]


def test_parse_ratio_missing_component():
    """Ratio only provides two components."""
    ratio = "6:4"
    sizes = model.parse_ratio(ratio)
    assert sizes == [0.6, 0., 0.4]


def test_parse_ratio_invalid_ratio():
    """Ratio uses incorrect separator."""
    ratio = "6;2;2"
    with pytest.raises(ValueError):
        model.parse_ratio(ratio)


def test_split_predictors_response(dummy_df):
    """Separate predictor variables from response."""
    nrows, ncols = dummy_df.shape
    features, target = model.split_predictors_response(dummy_df, target_col="target")

    assert features.shape == (nrows, ncols - 1)
    assert target.shape == (nrows, )


def test_split_predictors_response_invalid_target_col(dummy_df):
    """Specified target column does not exist in DataFrame."""
    with pytest.raises(KeyError):
        model.split_predictors_response(dummy_df, "class_dne")


def test_split_predictors_response_only_one_column():
    """Splitting a 1-column DataFrame yields a 0-col DF and Series."""
    df = pd.DataFrame(data={"col1": list(range(100))})
    features, target = model.split_predictors_response(df, target_col="col1")

    pd.testing.assert_frame_equal(features, pd.DataFrame(index=list(range(100))))
    pd.testing.assert_series_equal(target, pd.Series(data=list(range(100)), name="col1"))


def test_split_train_val_test(dummy_df):
    """Splits into train/val/test with dimensions as expected."""
    target = dummy_df["target"]
    features = dummy_df.drop("target", axis=1)
    X_train, X_val, X_test, y_train, y_val, y_test = model.split_train_val_test(features, target, "6:2:2")

    assert X_train.shape == (60, 1)
    assert X_val.shape == (20, 1)
    assert X_test.shape == (20, 1)
    assert y_train.shape == (60, )
    assert y_val.shape == (20, )
    assert y_test.shape == (20, )


def test_split_train_val_test_bad_ratio(dummy_df):
    """Ratio results in an empty train, validation, or test set."""
    target = dummy_df["target"]
    features = dummy_df.drop("target", axis=1)

    with pytest.raises(ValueError):
        model.split_train_val_test(features, target, "10:0:0")

    with pytest.raises(ValueError):
        model.split_train_val_test(features, target, "0:10:0")

    with pytest.raises(ValueError):
        model.split_train_val_test(features, target, "0:0:10")

    with pytest.raises(ValueError):
        model.split_train_val_test(features, target, "6:4")


def test_parse_dict_to_dataframe():
    """Convert a dictionary to `pandas.DataFrame` format."""
    colnames = ["col1", "col2", "col3"]
    sample_data = [1.5, 3.0, 4.5]

    data_dict = dict(zip(colnames, sample_data))
    actual_df = model.parse_dict_to_dataframe(data_dict)
    expected_df = pd.DataFrame(data=[sample_data], columns=colnames)

    pd.testing.assert_frame_equal(actual_df, expected_df)


def test_parse_dict_to_dataframe_empty_dict():
    """An empty dict yields an empty DataFrame."""
    data_dict = dict()
    actual_df = model.parse_dict_to_dataframe(data_dict)
    # An empty `pandas.DataFrame` still has one index entry
    expected_df = pd.DataFrame(index=[0])

    pd.testing.assert_frame_equal(actual_df, expected_df)


def test_validate_dataframe():
    """Create and reorder columns for model pipeline."""
    expected_columns = model.PREDICTION_COLUMNS

    sample_data = list(range(len(expected_columns)))
    shuffled_columns = np.random.shuffle(expected_columns)
    sample_df = pd.DataFrame(sample_data, columns=shuffled_columns)

    actual = model.validate_dataframe(sample_df)

    assert len(actual.columns) == len(expected_columns)
    assert sorted(actual.columns) == sorted(expected_columns)


def test_validate_dataframe_empty_input():
    """An empty input DataFrame yields an empty output DataFrame."""
    actual = model.validate_dataframe(pd.DataFrame())

    expected_columns = model.PREDICTION_COLUMNS
    # `NaN` values make the dtype `float64`, not `object`, even though it's empty
    expected = pd.DataFrame(columns=expected_columns, dtype=np.float64)

    pd.testing.assert_frame_equal(actual, expected)
