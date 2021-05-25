import logging

import pandas as pd

logger = logging.getLogger(__name__)


def convert_nan_to_str(data, colname="artist"):
    """
    Convert an NA/missing value to the literal string "NA".

    Args:
        data (:obj:`pandas.DataFrame`): DataFrame to clean
        colname (str, optional): Name of column to apply transformation to.
            Defaults to "artist".

    Returns:
        Cleaned :obj:`pandas.DataFrame`
    """
    nrows_affected = len(data.loc[pd.isna(data[colname])].index)
    data[colname] = data[colname].where(data[colname].notna(), other="NA")
    logger.info("Replaced missing values in %s with \"NA\"", colname)
    logger.info("Number of rows affected: %d", nrows_affected)
    return data


def convert_str_to_datetime(data, colname="releaseyear", format="%B %d %Y"):
    """
    Parse a string column to datetime format.

    Args:
        data (:obj:`pandas.DataFrame`): DataFrame to clean
        colname (str, optional): Name of column to apply transformation to.
            Defaults to "releaseyear".
        format (str, optional): Datetime format of column. Defaults to "%B %d %Y".
            For more info on these codes:
            https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes.

    Returns:
        Cleaned :obj:`pandas.DataFrame`
    """
    data[colname] = pd.to_datetime(data[colname], format=format)
    logger.info("Converted column %s to datetime format", colname)
    return data


def convert_datetime_to_date(data, colname="releaseyear"):
    """
    Remove the time component of a datetime column.

    Args:
        data (:obj:`pandas.DataFrame`): DataFrame to clean
        colname (str, optional): Name of column to apply transformation to.
            Defaults to "releaseyear".

    Returns:
        Cleaned :obj:`pandas.DataFrame`
    """
    data[colname] = data[colname].dt.date
    logger.info("Converted column %s to date format", colname)
    return data


def approximate_missing_year(data, fill_column="releaseyear", approximate_with="reviewdate"):
    """
    Fill missing values in one column with the year of another datetime column.

    Args:
        data (:obj:`pandas.DataFrame`): DataFrame to clean
        fill_column:
        approximate_with:

    Returns:
        Cleaned :obj:`pandas.DataFrame`
    """
    nrows_affected = len(data.loc[pd.isna(data[fill_column])].index)
    data.loc[pd.isna(data[fill_column]), fill_column] = \
        data[pd.isna(data[fill_column])].loc[:, approximate_with].dt.year
    logger.info("Filled missing values in %s with year from %s", fill_column, approximate_with)
    logger.info("Number of rows affected: %d", nrows_affected)
    return data


def fill_missing_manually(data, colname="recordlabel"):
    """
    Manually fill missing values.

    Args:
        data (:obj:`pandas.DataFrame`): DataFrame to clean
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
        index=data[pd.isna(data[colname])].index
    )
    data.loc[pd.isna(data[colname]), colname] = fill_missing
    logger.info(
        "Manually filled in missing values for %d missing rows in column %s",
        len(fill_missing.index),
        colname
    )

    return data


def strip_whitespace(data, colname="recordlabel"):
    """
    Trim extra whitespace from values in a column.

    Args:
        data (:obj:`pandas.DataFrame`): DataFrame to clean
        colname (str, optional): Name of column to apply transformation to.
            Defaults to "recordlabel".

    Returns:
        Cleaned :obj:`pandas.DataFrame`
    """
    data[colname] = data[colname].apply(str.strip)
    logger.info("Trimmed extra whitespace in column %s", colname)
    return data


def bucket_values_together(data, colname, values, replace_with):
    """
    Replace one or more values with a single value.

    Args:
        data (:obj:`pandas.DataFrame`): DataFrame to clean
        colname (str): Name of column to apply transformation to
        values (iterable): Iterable of values to replace.
        replace_with: Value to replace with.

    Returns:
        Cleaned :obj:`pandas.DataFrame`
    """
    nrows_affected = 0
    for value in values:
        nrows_affected += len(data.loc[data[colname] == value, colname].index)
        data.loc[data[colname] == value, colname] = replace_with

    logger.info(
        "Replaced values (%s) with %s in column %s",
        ", ".join(values),
        replace_with,
        colname
    )
    logger.info("Number of rows affected: %d", nrows_affected)

    return data


def fill_na_with_str_missing(data, colname="genre", fill_string="Missing"):
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
    nrows_affected = len(data.loc[pd.isna(data[colname])].index)
    data[colname] = data[colname].fillna(fill_string)
    logger.info("Replaced missing values in %s with %s", colname, fill_string)
    logger.info("Number of rows affected: %d", nrows_affected)
    
    return data
