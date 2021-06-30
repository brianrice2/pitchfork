"""
Clean the dataset before modeling.
"""
import logging
from time import time

import pandas as pd

logger = logging.getLogger(__name__)

# Some albums lack a record label in the dataset, even though
# they have one in reality. Correct these ones manually.
FILL_MISSING_RECORDLABEL_DATA = (
    "Fool's Gold",          # Run the Jewels
    "Vapor",                # 808s and Dark Grapes III
    "101 Distribution",     # Dedication 2
    "Jet Life",             # The Drive In Theatre
    "Espo",                 # Animals
    "Cinematic",            # 1999
    "Def Jam",              # Rich Forever
    "LM Dupli-Cation",      # Cervantine
    "Glory Boyz",           # Back From the Dead
    "Epic",                 # Drilluminati
    "Self-released",        # Community Service 2!
    "Cash Money",           # Sorry 4 the Wait
    "Grand Hustle",         # Fuck a Mixtape
    "Vice",                 # Blue Chips
    "Free Bandz",           # 56 Nights
    "Six Shooter Records",  # Retribution
    "Self-released",        # Acid Rap
    "Maybach",              # Dreamchasers
    "Self-released",        # White Mystery
    "Top Dawg",             # Cilvia Demo
    "Triple X",             # Winter Hill
    "1017",                 # 1017 Thug
    "Rostrum",              # Kush and Orange Juice
    "BasedWorld",           # God's Father
    "10.Deep",              # The Mixtape About Nothing
    "Self-released"         # Coloring Book
)


def clean_dataset(data: pd.DataFrame, config) -> pd.DataFrame:
    """
    Perform full data processing pipeline.

    Args:
        data (:obj:`pandas.DataFrame`): Raw data
        config (dict): Config file as read in by PyYAML

    Returns:
        :obj:`pandas.DataFrame` of cleaned data
    """
    start_time = time()

    # Perform cleaning steps specified in config file
    if "fill_na_with_str" in config:
        data = fill_na_with_str(data, **config["fill_na_with_str"]["iteration1"])
        data = fill_na_with_str(data, **config["fill_na_with_str"]["iteration2"])

    if "convert_str_to_datetime" in config:
        data = convert_str_to_datetime(data, **config["convert_str_to_datetime"])

    if "approximate_missing_year" in config:
        data = approximate_missing_year(data, **config["approximate_missing_year"])

    if "convert_datetime_to_date" in config:
        data = convert_datetime_to_date(data, **config["convert_datetime_to_date"])

    if "fill_missing_manually" in config:
        data = fill_missing_manually(data, **config["fill_missing_manually"])

    if "strip_whitespace" in config:
        data = strip_whitespace(data, **config["strip_whitespace"])

    if "bucket_values_together" in config:
        data = bucket_values_together(data, **config["bucket_values_together"]["iteration1"])
        data = bucket_values_together(data, **config["bucket_values_together"]["iteration2"])

    logger.info("Completed data cleaning process. Time taken: %0.4fs", time() - start_time)
    return data


def convert_str_to_datetime(
    data: pd.DataFrame,
    colname: str = "reviewdate",
    datetime_format: str = "%B %d %Y"
) -> pd.DataFrame:
    """
    Parse a string column to datetime format.

    Args:
        data (:obj:`pandas.DataFrame`): DataFrame to clean
        colname (str, optional): Name of column to apply transformation to.
            Defaults to "reviewdate".
        datetime_format (str, optional): Datetime format of column. Defaults to
            "%B %d %Y". For more info on these codes:
            https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes.

    Returns:
        Cleaned :obj:`pandas.DataFrame`
    """
    # Do nothing if the specified column is not present
    if colname not in data.columns:
        logger.warning("%s not found in columns. Returning original data.", colname)
        return data

    # Convert to datetime
    data[colname] = pd.to_datetime(data[colname], format=datetime_format)
    logger.debug("Converted column %s to datetime format", colname)

    return data


def convert_datetime_to_date(data: pd.DataFrame, colname: str = "reviewdate") -> pd.DataFrame:
    """
    Remove the time component of a datetime column.

    Args:
        data (:obj:`pandas.DataFrame`): DataFrame to clean
        colname (str, optional): Name of column to apply transformation to.
            Defaults to "reviewdate".

    Returns:
        Cleaned :obj:`pandas.DataFrame`
    """
    # Do nothing if the specified column is not present
    if colname not in data.columns:
        logger.warning("%s not found in columns. Returning original data.", colname)
        return data

    # Extract date component
    data[colname] = data[colname].dt.date
    logger.debug("Converted column %s to date format", colname)

    return data


def approximate_missing_year(
        data: pd.DataFrame,
        fill_column: str = "releaseyear",
        approximate_with: str = "reviewdate"
) -> pd.DataFrame:
    """
    Fill missing values in one column with the year of another datetime column.

    Args:
        data (:obj:`pandas.DataFrame`): DataFrame to clean
        fill_column (str): Name of column to fill values in
        approximate_with (str): Name of `datetime` column to pull year from

    Returns:
        Cleaned :obj:`pandas.DataFrame`
    """
    # Do nothing if either of the specified columns is not present
    if fill_column not in data.columns:
        logger.warning("%s not found in columns. Returning original data.", fill_column)
        return data

    if approximate_with not in data.columns:
        logger.warning("%s not found in columns. Returning original data.", approximate_with)
        return data

    nrows_affected = len(data.loc[pd.isna(data[fill_column])].index)

    # Fill values with year component of datetime column
    data.loc[pd.isna(data[fill_column]), fill_column] = \
        data[pd.isna(data[fill_column])].loc[:, approximate_with].dt.year

    logger.debug("Filled missing values in %s with year from %s", fill_column, approximate_with)
    logger.debug("Number of rows affected: %d", nrows_affected)

    return data


def fill_missing_manually(
        data: pd.DataFrame,
        colname: str = "recordlabel",
        fill_with: tuple = FILL_MISSING_RECORDLABEL_DATA
) -> pd.DataFrame:
    """
    Manually fill missing values.

    Args:
        data (:obj:`pandas.DataFrame`): DataFrame to clean
        colname (str, optional): Name of column to apply transformation to.
            Defaults to "recordlabel".
        fill_with (iterable): Corrected values to replace missing values with.
            Data type depends on the column being filled.

    Returns:
        Cleaned :obj:`pandas.DataFrame`
    """
    # Do nothing if the specified column is not present
    if colname not in data.columns:
        logger.warning("%s not found in columns. Returning original data.", colname)
        return data

    # Drop in corrected values
    fill_missing = pd.Series(data=fill_with, index=data[pd.isna(data[colname])].index)
    data.loc[pd.isna(data[colname]), colname] = fill_missing
    logger.debug(
        "Manually filled in missing values for %d missing rows in column %s",
        len(fill_missing.index),
        colname
    )

    return data


def strip_whitespace(data: pd.DataFrame, colname: str = "recordlabel") -> pd.DataFrame:
    """
    Trim extra whitespace from values in a column.

    Args:
        data (:obj:`pandas.DataFrame`): DataFrame to clean
        colname (str, optional): Name of column to apply transformation to.
            Defaults to "recordlabel".

    Returns:
        Cleaned :obj:`pandas.DataFrame`
    """
    # Do nothing if the specified column is not present
    if colname not in data.columns:
        logger.warning("%s not found in columns. Returning original data.", colname)
        return data

    data[colname] = data[colname].apply(str.strip)
    logger.debug("Trimmed extra whitespace in column %s", colname)
    return data


def bucket_values_together(data: pd.DataFrame, colname: str, values: list, replace_with: list) -> pd.DataFrame:
    """
    Replace one or more values with a single value.

    Args:
        data (:obj:`pandas.DataFrame`): DataFrame to clean
        colname (str): Name of column to apply transformation to
        values (iterable): Iterable of values to replace.
        replace_with: Value to replace with.

    Returns:
        Cleaned :obj:`pandas.DataFrame`

    Raises:
        `TypeError` if a single `str` object is passed to `values`. Since a `str` in
            Python is simply a list of characters, this doesn't immediately register
            as bad input, and logically doesn't really make sense for this method.
    """
    # Do nothing if the specified column is not present
    if colname not in data.columns:
        logger.warning("%s not found in columns. Returning original data.", colname)
        return data

    if isinstance(values, str):
        logger.error("""Error: Received a single string "%s" instead of an iterable
            of values to bucket together.""", values)
        raise TypeError("`bucket_values_together` requires an iterable of values, not a str")

    nrows_affected = 0
    # For every old value to replace, swap out for the new value
    for value in values:
        nrows_affected += len(data.loc[data[colname] == value, colname].index)
        data.loc[data[colname] == value, colname] = replace_with

    logger.debug(
        "Replaced values (%s) with %s in column %s",
        ", ".join(map(str, values)),
        replace_with,
        colname
    )
    logger.debug("Number of rows affected: %d", nrows_affected)

    return data


def fill_na_with_str(data: pd.DataFrame, colname: str= "genre", fill_string: str = "Missing") -> pd.DataFrame:
    """
    Fill NA values with a string value.

    Args:
        data (:obj:`pandas.DataFrame`): DataFrame to clean
        colname (str, optional): Name of column to apply transformation to.
            Defaults to "genre".
        fill_string (str, optional): String to replace missing values with.
            Defaults to "Missing".

    Returns:
        Cleaned :obj:`pandas.DataFrame`
    """
    # Do nothing if the specified column is not present
    if colname not in data.columns:
        logger.warning("%s not found in columns. Returning original data.", colname)
        return data

    nrows_affected = len(data.loc[pd.isna(data[colname])].index)
    data[colname] = data[colname].fillna(fill_string)

    logger.debug("Replaced missing values in %s with %s", colname, fill_string)
    logger.debug("Number of rows affected: %d", nrows_affected)

    return data
