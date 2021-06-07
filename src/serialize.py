"""
Serialize and deserialize trained model pipelines.
"""
import logging
import os

import joblib

from src import load_data

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
    # Saving to S3 requires some extra care compared to a local directory,
    # so first save to a local directory and then upload in a separate step.
    # Put the local copy in the same place it would have gone inside S3.
    if save_path.startswith("s3://"):
        _, s3path = load_data.parse_s3(save_path)
        local_path = s3path
        joblib.dump(pipeline, local_path)
        logger.info("Saved a copy of the model to %s", local_path)
        load_data.upload_file_to_s3(local_path=local_path, s3path=save_path)
    else:
        joblib.dump(pipeline, save_path)

    logger.info("Saved model to %s", save_path)


def load_pipeline(load_path):
    """
    Deserialize a fitted model pipeline.

    Args:
        load_path (str): Path to joblib-saved pipeline

    Returns:
        Fitted :obj:`sklearn.pipeline.Pipeline` object
    """
    # Download from S3 if a local copy does not already exist
    # This helps improve inference speed by reducing unnecessary
    # I/O and network calls
    if load_path.startswith("s3://"):
        _, s3path = load_data.parse_s3(load_path)
        local_path = s3path
        if not os.path.exists(local_path):
            load_data.download_file_from_s3(local_path=local_path, s3path=load_path)
            logger.info("Downloaded a copy of the model to %s", local_path)
        else:
            logger.info("Using existing local copy of model at %s", local_path)
        pipeline = joblib.load(local_path)
    else:
        pipeline = joblib.load(load_path)

    logger.info("Loaded model pipeline from %s", load_path)
    return pipeline
