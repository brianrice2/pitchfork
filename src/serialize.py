import logging

import joblib

logger = logging.getLogger(__name__)


def save_pipeline(pipeline, save_path):
    """
    Serialize a fitted model pipeline.

    Args:
        pipeline (:obj:`sklearn.pipeline.Pipeline`): Fitted model pipeline
        save_path (str): Where to save the pipeline

    Returns:
        None
    """
    joblib.dump(pipeline, save_path)
    logger.info('Saved model to %s', save_path)


def load_pipeline(load_path):
    """
    Deserialize a fitted model pipeline.

    Args:
        load_path (str): Path to joblib-saved pipeline

    Returns:
        Fitted :obj:`sklearn.pipeline.Pipeline` object
    """
    pipeline = joblib.load(load_path)
    logger.info('Loaded model pipeline from %s', load_path)
    return pipeline
