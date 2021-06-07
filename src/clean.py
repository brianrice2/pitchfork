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


def clean_dataset(data, config):
    """
    Perform full data processing pipeline.

    Args:
        data (:obj:`pandas.DataFrame`): Raw data
        config (dict): Config file as read in by PyYAML

    Returns:
        :obj:`pandas.DataFrame` of cleaned data
    """
    start_time = time()

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


def convert_nan_to_str(df, colname="artist"):
    """
    Convert an NA/missing value to the literal string "NA".

    Args:
        df (:obj:`pandas.DataFrame`): DataFrame to clean
        colname (str, optional): Name of column to apply transformation to.
            Defaults to "artist".

    Returns:
        Cleaned :obj:`pandas.DataFrame`
    """
    if colname not in df.columns:
        logger.warning("%s not found in columns. Returning original data.", colname)
        return df

    nrows_affected = len(df.loc[pd.isna(df[colname])].index)
    df[colname] = df[colname].where(df[colname].notna(), other="NA")
    logger.info("Replaced missing values in %s with \"NA\"", colname)
    logger.info("Number of rows affected: %d", nrows_affected)
    return df


def convert_str_to_datetime(df, colname="reviewdate", datetime_format="%B %d %Y"):
    """
    Parse a string column to datetime format.

    Args:
        df (:obj:`pandas.DataFrame`): DataFrame to clean
        colname (str, optional): Name of column to apply transformation to.
            Defaults to "reviewdate".
        datetime_format (str, optional): Datetime format of column. Defaults to
            "%B %d %Y". For more info on these codes:
            https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes.

    Returns:
        Cleaned :obj:`pandas.DataFrame`
    """
    if colname not in df.columns:
        logger.warning("%s not found in columns. Returning original data.", colname)
        return df

    df[colname] = pd.to_datetime(df[colname], format=datetime_format)
    logger.info("Converted column %s to datetime format", colname)
    return df


def convert_datetime_to_date(df, colname="reviewdate"):
    """
    Remove the time component of a datetime column.

    Args:
        df (:obj:`pandas.DataFrame`): DataFrame to clean
        colname (str, optional): Name of column to apply transformation to.
            Defaults to "reviewdate".

    Returns:
        Cleaned :obj:`pandas.DataFrame`
    """
    if colname not in df.columns:
        logger.warning("%s not found in columns. Returning original data.", colname)
        return df

    df[colname] = df[colname].dt.date
    logger.info("Converted column %s to date format", colname)
    return df


def approximate_missing_year(df, fill_column="releaseyear", approximate_with="reviewdate"):
    """
    Fill missing values in one column with the year of another datetime column.

    Args:
        df (:obj:`pandas.DataFrame`): DataFrame to clean
        fill_column (str): Name of column to fill values in
        approximate_with (str): Name of `datetime` column to pull year from

    Returns:
        Cleaned :obj:`pandas.DataFrame`
    """
    if fill_column not in df.columns:
        logger.warning("%s not found in columns. Returning original data.", fill_column)
        return df

    if approximate_with not in df.columns:
        logger.warning("%s not found in columns. Returning original data.", approximate_with)
        return df

    nrows_affected = len(df.loc[pd.isna(df[fill_column])].index)
    df.loc[pd.isna(df[fill_column]), fill_column] = \
        df[pd.isna(df[fill_column])].loc[:, approximate_with].dt.year
    logger.info("Filled missing values in %s with year from %s", fill_column, approximate_with)
    logger.info("Number of rows affected: %d", nrows_affected)
    return df


def fill_missing_manually(df, colname="recordlabel", fill_with=FILL_MISSING_RECORDLABEL_DATA):
    """
    Manually fill missing values.

    Args:
        df (:obj:`pandas.DataFrame`): DataFrame to clean
        colname (str, optional): Name of column to apply transformation to.
            Defaults to "recordlabel".
        fill_with (iterable): Corrected values to replace missing values with.
            Data type depends on the column being filled.

    Returns:
        Cleaned :obj:`pandas.DataFrame`
    """
    if colname not in df.columns:
        logger.warning("%s not found in columns. Returning original data.", colname)
        return df

    fill_missing = pd.Series(data=fill_with, index=df[pd.isna(df[colname])].index)
    df.loc[pd.isna(df[colname]), colname] = fill_missing
    logger.info(
        "Manually filled in missing values for %d missing rows in column %s",
        len(fill_missing.index),
        colname
    )

    return df


def strip_whitespace(df, colname="recordlabel"):
    """
    Trim extra whitespace from values in a column.

    Args:
        df (:obj:`pandas.DataFrame`): DataFrame to clean
        colname (str, optional): Name of column to apply transformation to.
            Defaults to "recordlabel".

    Returns:
        Cleaned :obj:`pandas.DataFrame`
    """
    if colname not in df.columns:
        logger.warning("%s not found in columns. Returning original data.", colname)
        return df

    df[colname] = df[colname].apply(str.strip)
    logger.info("Trimmed extra whitespace in column %s", colname)
    return df


def bucket_values_together(df, colname, values, replace_with):
    """
    Replace one or more values with a single value.

    Args:
        df (:obj:`pandas.DataFrame`): DataFrame to clean
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
    if colname not in df.columns:
        logger.warning("%s not found in columns. Returning original data.", colname)
        return df

    if isinstance(values, str):
        logger.error("""Error: Received a single string "%s" instead of an iterable
            of values to bucket together.""", values)
        raise TypeError("`bucket_values_together` requires an iterable of values, not a str")

    nrows_affected = 0
    for value in values:
        nrows_affected += len(df.loc[df[colname] == value, colname].index)
        df.loc[df[colname] == value, colname] = replace_with

    logger.info(
        "Replaced values (%s) with %s in column %s",
        ", ".join(map(str, values)),
        replace_with,
        colname
    )
    logger.info("Number of rows affected: %d", nrows_affected)

    return df


def fill_na_with_str(df, colname="genre", fill_string="Missing"):
    """
    Fill NA values with a string value.

    Args:
        df (:obj:`pandas.DataFrame`): DataFrame to clean
        colname (str, optional): Name of column to apply transformation to.
            Defaults to "genre".
        fill_string (str, optional): String to replace missing values with.
            Defaults to "Missing".

    Returns:
        Cleaned :obj:`pandas.DataFrame`
    """
    if colname not in df.columns:
        logger.warning("%s not found in columns. Returning original data.", colname)
        return df

    nrows_affected = len(df.loc[pd.isna(df[colname])].index)
    df[colname] = df[colname].fillna(fill_string)
    logger.info("Replaced missing values in %s with %s", colname, fill_string)
    logger.info("Number of rows affected: %d", nrows_affected)

    return df
