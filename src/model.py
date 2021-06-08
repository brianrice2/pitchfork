"""
Build, fit, and evaluate predictive models.
"""
import logging
from time import time

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


def split_predictors_response(data, target_col="score"):
    """Separate predictor variables from response variable."""
    features = data.drop(target_col, axis=1)
    target = data[target_col]
    logger.info(
        """Split predictors and response variable.
        Shapes: features=%s, target=%s""",
        features.shape,
        target.shape
    )

    return features, target


def split_train_val_test(features, target, train_val_test_ratio, **kwargs):
    """
    Partition dataset into training, validation, and testing splits.

    Args:

        features (:obj:`pandas.DataFrame`): DataFrame of input features
        target (array-like): Values of response variable to predict
        train_val_test_ratio (str): Relative proportion of data for each of
            train, val, and test sets, in the form "X:Y:Z" (e.g., "6:2:2").
        **kwargs: Additional settings to pass on to `train_test_split()`
            (for example, random seed)

    Returns:
        (X_train, X_val, X_test, y_train, y_val, y_test), each as DataFrames.
            X_val and y_val are omitted if the desired ratio does not specify
            the size of a validation set.
    """
    # Compute sizes and split according to ratio
    train_size, val_size, test_size = _parse_ratio(train_val_test_ratio)
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        features, target, test_size=test_size, **kwargs
    )

    # If no validation set is provided, additional splitting will throw an error
    if val_size > 0:
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_val, y_train_val, test_size=(val_size / (val_size + train_size)), **kwargs
        )
        logger.debug(
            """Data split into train/test sets.
            Shapes: X_train=%s, X_val=%s, X_test=%s, y_train=%s, y_val=%s, y_test=%s""",
            X_train.shape,
            X_val.shape,
            X_test.shape,
            y_train.shape,
            y_val.shape,
            y_test.shape
        )

        return X_train, X_val, X_test, y_train, y_val, y_test

    # Otherwise just return train and test sets
    X_train, y_train = X_train_val, y_train_val
    logger.debug(
        """Data split into train/test sets.
        Shapes: X_train=%s, X_test=%s, y_train=%s, y_test=%s""",
        X_train.shape,
        X_test.shape,
        y_train.shape,
        y_test.shape
    )

    return X_train, X_test, y_train, y_test


def _parse_ratio(ratio):
    """Convert a train-val-test ratio from X:Y:Z to list of proportions in [0,1]."""
    sizes = [float(n) for n in ratio.split(":")]

    # If only 2 pieces are given, keep train and test
    sizes = [sizes[0], 0., sizes[1]] if len(sizes) == 2 else sizes

    # Scale to [0,1]
    _sum = sum(sizes)
    proportions = list(size / _sum for size in sizes)
    logger.debug("Successfuly parsed ratio %s to %s", ratio, "/".join(map(str, proportions)))

    return proportions


def train_pipeline(X_train, y_train, preprocessor, model):
    """
    Create and fit a preprocessing --> modeling pipeline.

    Args:
        X_train (:obj:`pandas.DataFrame`): Training features
        y_train (array-like): Training targets
        preprocessor (obj:`sklearn.compose.ColumnTransformer`): ColumnTransformer
            defining the processing to perform for input data
        model (:obj:`sklearn.base.BaseEstimator`): An untrained `sklearn`
            regression model

    Returns:
        A fitted :obj:`sklearn.pipeline.Pipeline`
    """
    # Assemble pipeline and train
    pipe = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("predictor", model)
    ])
    logger.info("Pipeline created successfully. Beginning training.")

    start_time = time()
    pipe.fit(X_train, y_train)
    logger.info("Pipeline training complete. Time taken: %0.4f seconds", time() - start_time)

    return pipe


def make_preprocessor(numeric_features, categorical_features, handle_unknown):
    """
    Define preprocessing steps for input features.

    Performs standard scaling for numeric features and one-hot encoding for categorical
    features. All features specified for this function are processed, and _only_ these
    features are used when modeling. In other words, this preprocessor determines the
    exact input columns (and order) when training and performing inference.

    Args:
        numeric_features (list(str)): Names of numeric features to scale
        categorical_features (list(str)): Names of categorical features to one-hot encode
        handle_unknown (str): Policy for unknown categories in `OneHotEncoder`
            (either "handle_unknown" or "error")

    Returns:
        A :obj:`sklearn.compose.ColumnTransformer` with the desired transformation steps
    """
    # Scale numbers to mean 0 & stdev 1; one-hot encode categorical variables
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
    # Don't think there's anything else to say for this really
    model = GradientBoostingRegressor(**kwargs)
    return model


def parse_dict_to_dataframe(form_dict):
    """
    Parse a dictionary to `pandas.DataFrame` format.

    Flask forms supply data via POST requests in MultiDict format, but the
    model pipeline requires an input DataFrame.

    Args:
        form_dict (dict): Flask form response as a flat dictionary

    Returns:
        :obj:`pandas.DataFrame` with keys as column names and values as the
            associated values for each key
    """
    logger.debug("Converting dictionary to pandas DataFrame")

    # This structure is intuitive for a single record and scalar values,
    # but may behavior weird if, for example, lists or other multi-value
    # data structures are stored in a key's value
    data = pd.DataFrame([form_dict.values()], columns=form_dict.keys())

    return data


def validate_dataframe(data, output_cols=PREDICTION_COLUMNS):
    """
    Align a DataFrame with model pipeline's required order and names.

    The model pipeline requires an input DataFrame with exactly the same
    columns as seen during training, and in the same order.
    Creates the columns that don't exist (filling with NA).

    Args:
        data (:obj:`pandas.DataFrame`): Input DataFrame to validate/align
        output_cols (list(str), optional): Required columns for output
            DataFrame. Defaults to those seen during training. If not
            provided (`None`), no adjustment to the DataFrame's columns is made.

    Returns:
        Validated :obj:`pandas.DataFrame`
    """
    if output_cols:
        # Create columns if they don't exist already
        for colname in output_cols:
            if colname not in data.columns:
                logger.debug("Column %s not found. Creating and filling with NA.", colname)
                data[colname] = NaN

        # Column order must match exactly
        logger.debug("Reordering input columns")
        data = data[output_cols]

    return data
