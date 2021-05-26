"""
Build, fit, evaluate, and (de)serialize predictive models.
"""
import logging

import pandas as pd
from numpy import NaN
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder

logger = logging.getLogger(__name__)

# The exact same columns must be present, and in the exact same order, as the
# original training data for the pipeline to make predictions (even if the
# columns aren't used at all by the preprocessor or model)
PREDICTION_COLUMNS = [
    "artist", "album", "reviewauthor", "releaseyear", "reviewdate",
    "recordlabel", "genre", "danceability", "energy", "key", "loudness",
    "speechiness", "acousticness", "instrumentalness", "liveness", "valence", "tempo"
]


def split_train_val_test(df, target_col, train_val_test_ratio, **kwargs):
    """
    Partition dataset into training, validation, and testing splits.

    Args:
        df (:obj:`pandas.DataFrame`): DataFrame containing input features
            and response variable
        target_col (str): Name of column containing response variable
        train_val_test_ratio (str): Relative proportion of data for each of
            train, val, and test sets, in the form "X:Y:Z" (e.g., "6:2:2")
        **kwargs: Additional settings to pass on to `train_test_split()`
            (for example, random seed)

    Returns:
        (X_train, X_val, X_test, y_train, y_val, y_test), each as DataFrames
    """
    features = df.drop(target_col, axis=1)
    target = df[target_col]

    # Compute sizes and split according to ratio
    train_size, val_size, test_size = parse_ratio(train_val_test_ratio)
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        features, target, test_size=test_size, **kwargs
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=(val_size / (val_size + train_size)), **kwargs
    )

    logger.info(
        "Data split into train/test sets. " +
        "Shapes: X_train=%s, X_val=%s, X_test=%s, y_train=%s, y_val=%s, y_test=%s",
        (X_train.shape, ),
        (X_val.shape, ),
        (X_test.shape, ),
        (y_train.shape, ),
        (y_val.shape, ),
        (y_test.shape, )

    )

    return X_train, X_val, X_test, y_train, y_val, y_test


def parse_ratio(ratio):
    """Convert a train-val-test ratio from X:Y:Z to list of proportions in [0, 1]."""
    sizes = [float(n) for n in ratio.split(":")]
    sizes = [sizes[0], 0., sizes[1]] if len(sizes) == 2 else sizes
    _sum = sum(sizes)
    return list(size / _sum for size in sizes)


def train_pipeline(X_train, y_train):
    """
    Create and fit a preprocessing --> modeling pipeline.

    Args:
        X_train (:obj:`pandas.DataFrame`): Training features
        y_train (array-like): Training targets

    Returns:
        A fitted :obj:`sklearn.pipeline.Pipeline`
    """
    preprocessor = make_preprocessor()
    model = make_model()
    pipe = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("predictor", model)
    ])
    logger.info("Pipeline created successfully. Beginning training.")

    pipe.fit(X_train, y_train)
    logger.info("Pipeline training complete")
    return pipe


def make_preprocessor(numeric_features, categorical_features, handle_unknown):
    """
    Define preprocessing steps for input features.

    Performs standard scaling for numeric features and one-hot encoding for categorical
    features. All features specified for this function are processed, and _only_ these
    features are used when modeling.

    Args:
        numeric_features (list(str)): Names of numeric features to scale
        categorical_features (list(str)): Names of categorical features to one-hot encode
        handle_unknown (str): Policy for unknown categories in `OneHotEncoder`
            (either "handle_unknown" or "error")

    Returns:
        A :obj:`sklearn.compose.ColumnTransformer` with the desired transformation steps
    """
    numeric_transformer = StandardScaler()
    categorical_transformer = OneHotEncoder(handle_unknown=handle_unknown)

    preprocessor = ColumnTransformer(transformers=[
        ("numeric", numeric_transformer, numeric_features),
        ("categorical", categorical_transformer, categorical_features)
    ])
    return preprocessor


def make_model(**kwargs):
    """
    Create an untrained GBT model for use in a `sklearn.pipeline.Pipeline`.

    Args:
        **kwargs: Parameters to pass on to GBT constructor

    Returns:
        Untrained :obj:`sklearn.ensemble.GradientBoostingRegressor` object
    """
    model = GradientBoostingRegressor(**kwargs)
    return model


def get_feature_importances(trained_pipeline, numeric_features):
    """
    Get feature importance measures. Only applicable with tree-based models.

    Args:
        trained_pipeline (:obj:`sklearn.pipeline.Pipeline`): Fitted model pipeline
        numeric_features (list(str)): Names of numeric features

    Returns:
        :obj:`pandas.Series` containing each feature and its importance
    """
    features = numeric_features + list(trained_pipeline["preprocessor"].transformers_[1][1].get_feature_names())
    importances = trained_pipeline["predictor"].feature_importances_

    return pd.Series(data=importances, index=features)


def parse_dict_to_dataframe(form_dict, output_cols=PREDICTION_COLUMNS):
    """
    Parse a dictionary to `pandas.DataFrame`.

    Uses keys as column names, and creates the columns that don't exist (filling
    with NA). Reorders columns to match the original training data, per the
    pipeline's expectation.

    Flask forms supply data via POST requests in MultiDict format, but the
    model pipeline requires an input DataFrame with exactly the same columns
    as seen during training. The MultiDict can be converted to a flat dict
    using its `to_dict(flat=True)` method.

    Args:
        form_dict (dict): Flask form response as a flat
        output_cols (list(str), optional): Required columns for output
            DataFrame. Defaults to those seen during training. If not
            provided (`None`), no adjustment to the DataFrame's columns is made.

    Returns:
        :obj:`pandas.DataFrame`
    """
    logger.info("Converting dictionary to pandas DataFrame")
    df = pd.DataFrame([form_dict.values()], columns=form_dict.keys())

    if output_cols:
        # Create columns if they don't exist already
        for colname in output_cols:
            if colname not in df.columns:
                logger.info("Column %s not found. Creating and filling with NA.", colname)
                df[colname] = NaN

        # Column order must match exactly
        logger.info("Reordering input columns")
        df = df[output_cols]

    return df
