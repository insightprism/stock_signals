"""Interpolation utilities for converting weekly data to daily (e.g., COT reports)."""

import pandas as pd


def interpolate_weekly_to_daily(weekly_df: pd.DataFrame,
                                 value_col: str = "value",
                                 date_col: str = "date",
                                 method: str = "linear") -> pd.DataFrame:
    """Interpolate weekly data to daily frequency.

    Args:
        weekly_df: DataFrame with date and value columns
        value_col: Name of the value column
        date_col: Name of the date column
        method: Interpolation method ('linear', 'ffill', 'cubic')

    Returns:
        DataFrame with daily frequency
    """
    df = weekly_df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col).sort_index()

    # Create daily date range
    daily_idx = pd.date_range(start=df.index.min(), end=df.index.max(), freq="D")
    df = df.reindex(daily_idx)

    if method == "ffill":
        df[value_col] = df[value_col].ffill()
    else:
        df[value_col] = df[value_col].interpolate(method=method)

    df.index.name = date_col
    return df.reset_index()
