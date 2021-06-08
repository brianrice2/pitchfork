"""
Evaluate the performance of a model through its predictions.
"""
import math
import logging

import pandas as pd
from sklearn.metrics import max_error, mean_squared_error, median_absolute_error, r2_score

logger = logging.getLogger(__name__)


def evaluate_model(results_data, y_true_colname, y_pred_colname):
    """
    Evaluate performance against a variety of regression metrics.

    Args:
        results_data (:obj:`pandas.DataFrame`): DataFrame containing (at least)
            predicted and ground truth values
        y_true_colname (str): Name of column containing true values
        y_pred_colname (str): Name of column containing predicted values

    Returns:
        :obj:`pandas.DataFrame` containing metrics and values
    """
    logger.debug("Evaluating model performance")

    y_true = results_data[y_true_colname]
    y_pred = results_data[y_pred_colname]

    # Calculate metrics
    mse = mean_squared_error(y_true, y_pred)
    rmse = math.sqrt(mse)
    mad = median_absolute_error(y_true, y_pred)
    r_squared = r2_score(y_true, y_pred)
    max_err = max_error(y_true, y_pred)

    # Log results
    logger.info("""
        MSE:\t\t%0.4f
        RMSE:\t\t%0.4f
        MAD:\t\t%0.4f
        R-squared:\t%0.4f
        Max error:\t%0.4f""",
        mse, rmse, mad, r_squared, max_err
    )

    # Create a DataFrame of metrics and results
    metric_data = pd.DataFrame(
        data=[
            ["mse", mse],
            ["rmse", rmse],
            ["mad", mad],
            ["r_squared", r_squared],
            ["max_err", max_err]
        ],
        columns=["metric", "performance"]
    )
    return metric_data
