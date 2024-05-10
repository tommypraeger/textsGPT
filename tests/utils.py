"""
Module that defines utility functions for tests.
"""

import pandas as pd


def assert_dataframes_equal(expected: pd.DataFrame, actual: pd.DataFrame):
    """
    Helper function for asserting that two DataFrames should be equals.
    Uses the pandas.testing.assert_frame_equal method.
    Ignores differences in index/dtype.
    """
    pd.testing.assert_frame_equal(
        expected.reset_index(drop=True),
        actual.reset_index(drop=True),
        check_dtype=False,
        check_index_type=False,
        check_column_type=False,
    )
