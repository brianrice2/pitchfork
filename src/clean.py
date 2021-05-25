import pandas as pd


def convert_nan_to_str(data, colname="artist"):
    data[colname] = data[colname].where(data[colname].notna(), other="NA")
    return data


def convert_str_to_datetime(data, colname, format="%B %d %Y"):
    data[colname] = pd.to_datetime(data[colname], format=format)
    return data


def convert_datetime_to_date(data, colname):
    data[colname] = data[colname].dt.date
    return data


def approximate_missing_year(data, fill_column="releaseyear", approximate_with="reviewdate"):
    data.loc[pd.isna(data[fill_column]), fill_column] = \
        data[pd.isna(data[fill_column])].loc[:, approximate_with].dt.year
    return data


def fill_missing_manually(data, colname):
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

    return data


def strip_whitespace(data, colname):
    data[colname] = data[colname].apply(str.strip)
    return data


def bucket_values_together(data, colname, values, replace_with):
    for value in values:
        data.loc[data[colname] == value, colname] = replace_with
    return data


def fill_na_with_str_missing(data, colname, fill_string="Missing"):
    data[colname] = data[colname].fillna(fill_string)
    return data
