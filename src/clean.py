import logging

import pandas as pd

logger = logging.getLogger(__name__)


def clean_dataset(df, config):
    """
    Perform full data processing pipeline.

    Args:
        df (:obj:`pandas.DataFrame`): Raw data
        config (dict): Config file as read in by PyYAML

    Returns:
        :obj:`pandas.DataFrame` of cleaned data
    """
    if "convert_nan_to_str" in config:
        df = convert_nan_to_str(df, **config["convert_nan_to_str"])

    if "convert_str_to_datetime" in config:
        df = convert_str_to_datetime(df, **config["convert_str_to_datetime"])

    if "approximate_missing_year" in config:
        df = approximate_missing_year(df, **config["approximate_missing_year"])

    if "convert_datetime_to_date" in config:
        df = convert_datetime_to_date(df, **config["convert_datetime_to_date"])

    if "fill_missing_manually" in config:
        df = fill_missing_manually(df, **config["fill_missing_manually"])

    if "strip_whitespace" in config:
        df = strip_whitespace(df, **config["strip_whitespace"])

    if "bucket_values_together" in config:
        df = bucket_values_together(df, **config["bucket_values_together"]["iteration1"])
        df = bucket_values_together(df, **config["bucket_values_together"]["iteration2"])

    if "fill_na_with_str_missing" in config:
        df = fill_na_with_str_missing(df, **config["fill_na_with_str_missing"])

    return df


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
    nrows_affected = len(df.loc[pd.isna(df[colname])].index)
    df[colname] = df[colname].where(df[colname].notna(), other="NA")
    logger.info("Replaced missing values in %s with \"NA\"", colname)
    logger.info("Number of rows affected: %d", nrows_affected)
    return df


def convert_str_to_datetime(df, colname="reviewdate", format="%B %d %Y"):
    """
    Parse a string column to datetime format.

    Args:
        df (:obj:`pandas.DataFrame`): DataFrame to clean
        colname (str, optional): Name of column to apply transformation to.
            Defaults to "reviewdate".
        format (str, optional): Datetime format of column. Defaults to "%B %d %Y".
            For more info on these codes:
            https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes.

    Returns:
        Cleaned :obj:`pandas.DataFrame`
    """
    df[colname] = pd.to_datetime(df[colname], format=format)
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
    df[colname] = df[colname].dt.date
    logger.info("Converted column %s to date format", colname)
    return df


def approximate_missing_year(df, fill_column="releaseyear", approximate_with="reviewdate"):
    """
    Fill missing values in one column with the year of another datetime column.

    Args:
        df (:obj:`pandas.DataFrame`): DataFrame to clean
        fill_column:
        approximate_with:

    Returns:
        Cleaned :obj:`pandas.DataFrame`
    """
    nrows_affected = len(df.loc[pd.isna(df[fill_column])].index)
    df.loc[pd.isna(df[fill_column]), fill_column] = \
        df[pd.isna(df[fill_column])].loc[:, approximate_with].dt.year
    logger.info("Filled missing values in %s with year from %s", fill_column, approximate_with)
    logger.info("Number of rows affected: %d", nrows_affected)
    return df


def fill_missing_manually(df, colname="recordlabel"):
    """
    Manually fill missing values.

    Args:
        df (:obj:`pandas.DataFrame`): DataFrame to clean
        colname (str, optional): Name of column to apply transformation to.
            Defaults to "recordlabel".

    Returns:
        Cleaned :obj:`pandas.DataFrame`
    """
    fill_missing = pd.Series(
        data=[
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
        ],
        index=df[pd.isna(df[colname])].index
    )
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
    """
    nrows_affected = 0
    for value in values:
        nrows_affected += len(df.loc[df[colname] == value, colname].index)
        df.loc[df[colname] == value, colname] = replace_with

    logger.info(
        "Replaced values (%s) with %s in column %s",
        ", ".join(values),
        replace_with,
        colname
    )
    logger.info("Number of rows affected: %d", nrows_affected)

    return df


def fill_na_with_str_missing(df, colname="genre", fill_string="Missing"):
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
    nrows_affected = len(df.loc[pd.isna(df[colname])].index)
    df[colname] = df[colname].fillna(fill_string)
    logger.info("Replaced missing values in %s with %s", colname, fill_string)
    logger.info("Number of rows affected: %d", nrows_affected)
    
    return df
