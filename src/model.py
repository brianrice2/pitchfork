"""
Build, fit, and evaluate predictive models.
"""
import logging
import math
from time import time

import pandas as pd
from numpy import NaN
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import max_error, mean_squared_error, median_absolute_error, r2_score
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


def split_predictors_response(df, target_col="score"):
    """Separate predictor variables from response variable."""
    features = df.drop(target_col, axis=1)
    target = df[target_col]
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
        (X_train, X_val, X_test, y_train, y_val, y_test), each as DataFrames
    """
    # Compute sizes and split according to ratio
    train_size, val_size, test_size = parse_ratio(train_val_test_ratio)
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        features, target, test_size=test_size, **kwargs
    )
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


def parse_ratio(ratio):
    """Convert a train-val-test ratio from X:Y:Z to list of proportions in [0,1]."""
    sizes = [float(n) for n in ratio.split(":")]
    sizes = [sizes[0], 0., sizes[1]] if len(sizes) == 2 else sizes
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
    Get feature importance measures from a trained model.

    Args:
        trained_pipeline (:obj:`sklearn.pipeline.Pipeline`): Fitted model pipeline
        numeric_features (list(str)): Names of numeric features

    Returns:
        :obj:`pandas.Series` containing each feature and its importance
    """
    categorical_features = list(trained_pipeline["preprocessor"]
        .transformers_[1][1]
        .get_feature_names())
    features = numeric_features + categorical_features

    importances = trained_pipeline["predictor"].feature_importances_

    return pd.Series(data=importances, index=features)


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
    df = pd.DataFrame([form_dict.values()], columns=form_dict.keys())

    return df


def validate_dataframe(df, output_cols=PREDICTION_COLUMNS):
    """
    Align a DataFrame with model pipeline's required order and names.

    The model pipeline requires an input DataFrame with exactly the same
    columns as seen during training, and in the same order.
    Creates the columns that don't exist (filling with NA).

    Args:
        df (:obj:`pandas.DataFrame`): Input DataFrame to validate/align
        output_cols (list(str), optional): Required columns for output
            DataFrame. Defaults to those seen during training. If not
            provided (`None`), no adjustment to the DataFrame's columns is made.

    Returns:
        Validated :obj:`pandas.DataFrame`
    """
    if output_cols:
        # Create columns if they don't exist already
        for colname in output_cols:
            if colname not in df.columns:
                logger.debug("Column %s not found. Creating and filling with NA.", colname)
                df[colname] = NaN

        # Column order must match exactly
        logger.debug("Reordering input columns")
        df = df[output_cols]

    return df


def evaluate_model(y_true, y_pred, save_metrics_path):
    """
    Evaluate performance against a variety of regression metrics.

    Args:
        y_true (array-like): True values
        y_pred (array-like): Predicted values
        save_metrics_path (str): Location to save performance metrics

    Returns:
        None (logs and saves results).
    """
    logger.debug("Evaluating model performance")

    # Calculate metrics
    mse = mean_squared_error(y_true, y_pred)
    rmse = math.sqrt(mse)
    mad = median_absolute_error(y_true, y_pred)
    r_squared = r2_score(y_true, y_pred)
    max_err = max_error(y_true, y_pred)

    # Log results
    logger.info("""
        MSE:\t\t%0.4f
        RMSE:\t%0.4f
        MAD:\t\t%0.4f
        R-squared:\t%0.4f
        Max error:\t%0.4f""",
        mse, rmse, mad, r_squared, max_err
    )

    # Also save a copy of metrics to disk
    metric_data = pd.DataFrame(
        data=[mse, rmse, mad, r_squared, max_err],
        index=["mse", "rmse", "mad", "r_squared", "max_err"],
        columns=["performance"]
    )
    metric_data.to_csv(save_metrics_path)


def append_predictions(model, input_data, output_col="preds"):
    """
    Append predictions to an existing input DataFrame.

    Args:
        model (:obj:`sklearn.pipeline.Pipeline`): Trained model pipeline
        input_data (:obj:`pandas.DataFrame`): Input data to predict on
        output_col (str, optional): Name of column to place predicted
            values in. Defaults to "preds".

    Returns:
        array-like of predicted values
    """
    logger.debug(
        "Input data has %s columns: %s",
        len(input_data.columns),
        ", ".join(input_data.columns)
    )

    # Validate input and make predictions
    logger.debug("Validating input before predicting")
    df = validate_dataframe(input_data)

    start_time = time()
    preds = model.predict(df)
    logger.debug(
        "Predictions made on input data. Time taken to predict: %0.4f seconds",
        time() - start_time
    )

    # Store results in original DataFrame -- new columns always placed at end
    # Overwrites column named `output_col` if it exists already (in this case,
    # it may not actually be the last column)
    df[output_col] = preds
    logger.info("Predictions appended to original data")

    return df
