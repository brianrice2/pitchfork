"""
Generate new values given a trained model and some new input.
"""
import logging
from copy import deepcopy
from time import time

import pandas as pd
import sklearn.pipeline

from src import model

logger = logging.getLogger(__name__)


def get_predictions(trained_model: sklearn.pipeline.Pipeline, input_data: pd.DataFrame) -> list:
    """
    Get predicted values for input data.

    Args:
        trained_model (:obj:`sklearn.pipeline.Pipeline`): Trained model pipeline
        input_data (:obj:`pandas.DataFrame`): Input data to predict on

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
    data = model.validate_dataframe(input_data)

    start_time = time()
    preds = trained_model.predict(data)
    logger.debug(
        "Predictions made on input data. Time taken to predict: %0.4f seconds",
        time() - start_time
    )

    return preds


def append_predictions(
        trained_model: sklearn.pipeline.Pipeline,
        input_data: pd.DataFrame,
        output_col: str = "preds"
) -> pd.DataFrame:
    """
    Append predictions to an existing input DataFrame.

    Args:
        trained_model (:obj:`sklearn.pipeline.Pipeline`): Trained model pipeline
        input_data (:obj:`pandas.DataFrame`): Input data to predict on
        output_col (str, optional): Name of column to place predicted
            values in. Defaults to "preds".

    Returns:
        Input `pandas.DataFrame` with predictions appended as a new column
    """
    data = deepcopy(input_data)
    predictions = get_predictions(trained_model, input_data)

    # Overwrites column named `output_col` if it exists already (in this case,
    # it may not actually be the last column). New columns always placed at end.
    data[output_col] = predictions
    logger.info("Predictions appended to original data")

    return data
