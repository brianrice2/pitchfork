"""
Analyze a trained model.
"""
import logging
import typing

import pandas as pd
import sklearn.pipeline

logger = logging.getLogger(__name__)


def get_feature_importance(
        trained_pipeline: sklearn.pipeline.Pipeline,
        numeric_features: typing.List[str]
) -> pd.Series:
    """
    Get feature importance measures from a trained model.

    Args:
        trained_pipeline (:obj:`sklearn.pipeline.Pipeline`): Fitted model pipeline
        numeric_features (list(str)): Names of numeric features

    Returns:
        :obj:`pandas.Series` containing each feature and its importance
    """
    # Retrieve categorical features from the one-hot encoder
    # (numeric features need to be passed in manually)
    categorical_features = list(trained_pipeline["preprocessor"]
        .transformers_[1][1]
        .get_feature_names())
    features = numeric_features + categorical_features

    # Fetch importance values (without labels) from the model itself
    importances = trained_pipeline["predictor"].feature_importances_

    return pd.Series(data=importances, index=features)
