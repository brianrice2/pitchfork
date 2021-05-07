import numpy as np
import pytest


@pytest.fixture
def global_vars():
	# Manually-checked characteristics of raw dataset
	pytest.RAW_DATA_NROWS = 18403
	pytest.RAW_DATA_NCOLS = 18
	pytest.RAW_DATA_COLNAMES = [
		"artist",
		"album",
		"reviewauthor",
		"score",
		"releaseyear",
		"reviewdate",
		"recordlabel",
		"genre",
		"danceability",
		"energy",
		"key",
		"loudness",
		"speechiness",
		"acousticness",
		"instrumentalness",
		"liveness",
		"valence",
		"tempo",
	]
	pytest.RAW_DATA_DTYPES = [
		np.dtype("O"),
		np.dtype("O"),
		np.dtype("O"),
		np.dtype("float64"),
		np.dtype("float64"),
		np.dtype("O"),
		np.dtype("O"),
		np.dtype("O"),
		np.dtype("float64"),
		np.dtype("float64"),
		np.dtype("float64"),
		np.dtype("float64"),
		np.dtype("float64"),
		np.dtype("float64"),
		np.dtype("float64"),
		np.dtype("float64"),
		np.dtype("float64"),
		np.dtype("float64")
	]
