import datetime
from copy import deepcopy

import pandas as pd
import pytest
from numpy import NaN

from src import clean

COLUMNS = ["artist", "album", "reviewauthor", "score", "releaseyear", "reviewdate", "recordlabel", "genre"]
RAW_DATA = [
    ["Run the Jewels ", "Run the Jewels 2", "Ian Cohen", 9.0, 2014.0,
     "October 29 2014", NaN, "Rap"],
    ["Vampire Weekend ", "Modern Vampires of the City", "Ryan Dombal", 9.3, NaN,
     "May 13 2013", NaN, "Rock"],
    ["Metallica ", "Metallica", "Zoe Camp", 7.7, 1991.0,
     "July 9 2017", NaN, "Metal"]
]
MISSING_RECORD_LABELS = ["Mass Appeal", "XL", "Elektra"]

# Same as `RAW_DATA`, but with `reviewdate` in `datetime.datetime` format
# (mostly for convenience)
RAW_DATA_DATETIME = [
    ["Run the Jewels ", "Run the Jewels 2", "Ian Cohen", 9.0, 2014.0,
     datetime.datetime(2014, 10, 29), NaN, "Rap"],
    ["Vampire Weekend ", "Modern Vampires of the City", "Ryan Dombal", 9.3, NaN,
     datetime.datetime(2013, 5, 13), NaN, "Rock"],
    ["Metallica ", "Metallica", "Zoe Camp", 7.7, 1991.0,
     datetime.datetime(2017, 7, 9), NaN, "Metal"]
]


@pytest.fixture()
def dummy_df():
    return pd.DataFrame(data=RAW_DATA, columns=COLUMNS)


@pytest.fixture
def dummy_df_datetime():
    return pd.DataFrame(data=RAW_DATA_DATETIME, columns=COLUMNS)


def test_fill_na_with_str(dummy_df):
    """Fill NaN values with a specified string."""
    actual = clean.fill_na_with_str(dummy_df, colname="recordlabel", fill_string="Missing")

    expected = deepcopy(dummy_df)
    expected["recordlabel"] = "Missing"

    pd.testing.assert_frame_equal(actual, expected)


def test_fill_na_with_str_no_missing_values(dummy_df):
    """Columns with no missing values should remain unchanged."""
    actual = clean.fill_na_with_str(dummy_df, colname="album", fill_string="Missing")
    expected = dummy_df
    pd.testing.assert_frame_equal(actual, expected)


def test_fill_na_with_str_invalid_column(dummy_df):
    """Gracefully handle when column is not present."""
    expected = dummy_df

    actual = clean.fill_na_with_str(dummy_df, colname="", fill_string="Missing")
    pd.testing.assert_frame_equal(actual, expected)

    actual = clean.fill_na_with_str(dummy_df, colname="notarealcolumn", fill_string="Missing")
    pd.testing.assert_frame_equal(actual, expected)

    actual = clean.fill_na_with_str(dummy_df, colname=None, fill_string="Missing")
    pd.testing.assert_frame_equal(actual, expected)


def test_convert_str_to_datetime(dummy_df, dummy_df_datetime):
    """Parse strings to datetime format."""
    actual = clean.convert_str_to_datetime(dummy_df, colname="reviewdate", datetime_format="%B %d %Y")

    expected = deepcopy(dummy_df_datetime)

    # Preserve original dtypes
    expected["reviewdate"] = expected["reviewdate"].astype("datetime64")
    expected["recordlabel"] = expected["recordlabel"].astype("float64")

    pd.testing.assert_frame_equal(actual, expected)


def test_convert_str_to_datetime_bad_format(dummy_df):
    """Inappropriate datetime format."""
    with pytest.raises(ValueError):
        clean.convert_str_to_datetime(dummy_df, colname="reviewdate", datetime_format="%Y-%m-%d")


def test_convert_str_to_datetime_invalid_column_type(dummy_df):
    """Column to parse is not of type `str`."""
    clean.convert_str_to_datetime(dummy_df, colname="releaseyear", datetime_format="%Y")


def test_onvert_datetime_to_date(dummy_df_datetime):
    """Removes time components of datetime column."""
    actual = clean.convert_datetime_to_date(dummy_df_datetime, colname="reviewdate")

    expected_data = [
        ["Run the Jewels ", "Run the Jewels 2", "Ian Cohen", 9.0, 2014.0,
         datetime.date(2014, 10, 29), NaN, "Rap"],
        ["Vampire Weekend ", "Modern Vampires of the City", "Ryan Dombal", 9.3, NaN,
         datetime.date(2013, 5, 13), NaN, "Rock"],
        ["Metallica ", "Metallica", "Zoe Camp", 7.7, 1991.0,
         datetime.date(2017, 7, 9), NaN, "Metal"]
    ]
    expected = pd.DataFrame(data=expected_data, columns=COLUMNS)

    pd.testing.assert_frame_equal(actual, expected)


def test_convert_datetime_to_date_invalid_column_type(dummy_df_datetime):
    """Column not datetime format."""
    with pytest.raises(AttributeError):
        clean.convert_datetime_to_date(dummy_df_datetime, colname="genre")


def test_approximate_missing_year(dummy_df_datetime):
    actual = clean.approximate_missing_year(
        dummy_df_datetime,
        fill_column="releaseyear",
        approximate_with="reviewdate"
    )

    expected_data = [
        ["Run the Jewels ", "Run the Jewels 2", "Ian Cohen", 9.0, 2014.0,
         datetime.date(2014, 10, 29), NaN, "Rap"],
        ["Vampire Weekend ", "Modern Vampires of the City", "Ryan Dombal", 9.3, 2013,  # <-- Filled NaN here
         datetime.date(2013, 5, 13), NaN, "Rock"],
        ["Metallica ", "Metallica", "Zoe Camp", 7.7, 1991.0,
         datetime.date(2017, 7, 9), NaN, "Metal"]
    ]
    expected = pd.DataFrame(data=expected_data, columns=COLUMNS)

    # Preserve original dtypes
    expected["releaseyear"] = expected["releaseyear"].astype("float64")
    expected["reviewdate"] = expected["reviewdate"].astype("datetime64[ns]")

    pd.testing.assert_frame_equal(actual, expected)


def test_approximate_missing_year_reference_invalid_column_type(dummy_df_datetime):
    """Reference column is not in `datetime` format."""
    with pytest.raises(AttributeError):
        clean.approximate_missing_year(
            dummy_df_datetime,
            fill_column="releaseyear",
            approximate_with="album"
        )

    with pytest.raises(AttributeError):
        clean.approximate_missing_year(
            dummy_df_datetime,
            fill_column="releaseyear",
            approximate_with="score"
        )


def test_fill_missing_manually(dummy_df):
    """Replace missing values in a column with curated replacements."""
    actual = clean.fill_missing_manually(
        dummy_df,
        colname="recordlabel",
        fill_with=MISSING_RECORD_LABELS
    )

    expected_data = [
        ["Run the Jewels ", "Run the Jewels 2", "Ian Cohen", 9.0, 2014.0,
         "October 29 2014", "Mass Appeal", "Rap"],
        ["Vampire Weekend ", "Modern Vampires of the City", "Ryan Dombal", 9.3, NaN,
         "May 13 2013", "XL", "Rock"],
        ["Metallica ", "Metallica", "Zoe Camp", 7.7, 1991.0,
         "July 9 2017", "Elektra", "Metal"]
    ]
    expected = pd.DataFrame(data=expected_data, columns=COLUMNS)

    pd.testing.assert_frame_equal(actual, expected)


def test_fill_missing_manually_replacements_bad_length(dummy_df):
    """Differing number of missing values and fill values."""
    with pytest.raises(ValueError):
        # Replacement values too long
        clean.fill_missing_manually(
            dummy_df,
            colname="recordlabel",
            fill_with=MISSING_RECORD_LABELS + ["Rice Records"]
        )

    with pytest.raises(ValueError):
        # Replacement values too short
        clean.fill_missing_manually(
            dummy_df,
            colname="recordlabel",
            fill_with=MISSING_RECORD_LABELS[:-1]
        )


def test_strip_whitespace(dummy_df):
    """Remove extra whitespace in a `str` column."""
    actual = clean.strip_whitespace(dummy_df, colname="artist")

    # Remove extra whitespace from artist names
    expected_data = [
        ["Run the Jewels", "Run the Jewels 2", "Ian Cohen", 9.0, 2014.0,
         "October 29 2014", NaN, "Rap"],
        ["Vampire Weekend", "Modern Vampires of the City", "Ryan Dombal", 9.3, NaN,
         "May 13 2013", NaN, "Rock"],
        ["Metallica", "Metallica", "Zoe Camp", 7.7, 1991.0,
         "July 9 2017", NaN, "Metal"]
    ]
    expected = pd.DataFrame(data=expected_data, columns=COLUMNS)

    pd.testing.assert_frame_equal(actual, expected)


def test_strip_whitespace_invalid_column(dummy_df):
    """Gracefully handle when column is not present."""
    actual = clean.strip_whitespace(dummy_df, colname="")
    expected = dummy_df
    pd.testing.assert_frame_equal(actual, expected)

    actual = clean.strip_whitespace(dummy_df, colname="notarealcolumn")
    expected = dummy_df
    pd.testing.assert_frame_equal(actual, expected)

    actual = clean.strip_whitespace(dummy_df, colname=None)
    expected = dummy_df
    pd.testing.assert_frame_equal(actual, expected)


def test_strip_whitespace_invalid_column_type(dummy_df, dummy_df_datetime):
    """Apply strip to invalid column type."""
    with pytest.raises(TypeError):
        clean.strip_whitespace(dummy_df, colname="releaseyear")

    with pytest.raises(TypeError):
        clean.strip_whitespace(dummy_df_datetime, colname="reviewdate")


def test_bucket_values_together(dummy_df):
    actual = clean.bucket_values_together(
        dummy_df,
        colname="album",
        values=["Run the Jewels 2", "Modern Vampires of the City", "Metallica"],
        replace_with="Best of Brian Rice"
    )

    expected = deepcopy(dummy_df)
    expected["album"] = "Best of Brian Rice"

    pd.testing.assert_frame_equal(actual, expected)


def test_bucket_values_together_invalid_column(dummy_df):
    """Gracefully handle when column is not present."""
    expected = dummy_df

    actual = clean.bucket_values_together(
        dummy_df,
        colname="",
        values=["Run the Jewels 2", "Modern Vampires of the City", "Metallica"],
        replace_with="Best of Brian Rice"
    )
    pd.testing.assert_frame_equal(actual, expected)

    actual = clean.bucket_values_together(
        dummy_df,
        colname="notarealcolumn",
        values=["Run the Jewels 2", "Modern Vampires of the City", "Metallica"],
        replace_with="Best of Brian Rice"
    )
    pd.testing.assert_frame_equal(actual, expected)

    actual = clean.bucket_values_together(
        dummy_df,
        colname=None,
        values=["Run the Jewels 2", "Modern Vampires of the City", "Metallica"],
        replace_with="Best of Brian Rice"
    )
    pd.testing.assert_frame_equal(actual, expected)


def test_bucket_values_together_none_replacement(dummy_df):
    """`None` passed as replacement value yields `numpy.NaN`."""
    actual = clean.bucket_values_together(
        dummy_df,
        colname="album",
        values=["Run the Jewels 2", "Modern Vampires of the City", "Metallica"],
        replace_with=None
    )

    expected = deepcopy(dummy_df)
    expected["album"] = NaN

    # Filling with `None` makes the column of type `object`
    expected["album"] = expected["album"].astype("object")

    pd.testing.assert_frame_equal(actual, expected)


def test_bucket_values_together_none_values(dummy_df):
    """`None` passed as values to bucket."""
    actual = clean.bucket_values_together(
        dummy_df,
        colname="album",
        values=[None],
        replace_with="None"
    )
    expected = dummy_df
    pd.testing.assert_frame_equal(actual, expected)


def test_bucket_values_together_scalar_values(dummy_df):
    """Single scalar value, not an iterable, passed as values to bucket."""
    with pytest.raises(TypeError):
        clean.bucket_values_together(
            dummy_df,
            colname="album",
            values="Run the Jewels 2",
            replace_with="RTJ2"
        )
