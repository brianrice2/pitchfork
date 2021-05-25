import pandas as pd
import pytest

from src import model


@pytest.fixture
def dummy_df():
    dummy_df = pd.DataFrame(data={'col1': list(range(100)), 'target': list(range(100))})
    return dummy_df


def test_parse_ratio():
    """Parses ratio as expected."""
    ratio = '6:2:2'
    sizes = model.parse_ratio(ratio)
    assert sizes == [0.6, 0.2, 0.2]


def test_parse_ratio_missing_component():
    """Ratio only provides two ratios."""
    ratio = '6:4'
    sizes = model.parse_ratio(ratio)
    assert sizes == [0.6, 0., 0.4]


def test_parse_ratio_invalid_ratio():
    """Ratio uses incorrect separator."""
    ratio = '6;2;2'
    with pytest.raises(ValueError):
        model.parse_ratio(ratio)


def test_split_train_val_test(dummy_df):
    """Splits into train/val/test with dimensions as expected."""
    X_train, X_val, X_test, y_train, y_val, y_test = model.split_train_val_test(dummy_df, 'target', '6:2:2')

    assert X_train.shape == (60, 1)
    assert X_val.shape == (20, 1)
    assert X_test.shape == (20, 1)
    assert y_train.shape == (60, )
    assert y_val.shape == (20, )
    assert y_test.shape == (20, )


def test_split_train_val_test_invalid_target_col(dummy_df):
    """Specified target column does not exist in DataFrame."""
    with pytest.raises(KeyError):
        model.split_train_val_test(dummy_df, 'class_dne', '6:2:2')


def test_split_train_val_test_bad_ratio(dummy_df):
    """Ratio results in an empty train, validation, or test set."""
    with pytest.raises(ValueError):
        model.split_train_val_test(dummy_df, 'target', '10:0:0')
    with pytest.raises(ValueError):
        model.split_train_val_test(dummy_df, 'target', '0:10:0')
    with pytest.raises(ValueError):
        model.split_train_val_test(dummy_df, 'target', '0:0:10')
    with pytest.raises(ValueError):
        model.split_train_val_test(dummy_df, 'target', '6:4')
