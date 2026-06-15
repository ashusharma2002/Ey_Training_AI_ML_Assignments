import pandas as pd
from statsmodels.tsa.stattools import adfuller


def load_dataset(file_path):

    df = pd.read_csv(file_path)

    return df


def generate_dataset_summary(df):

    rows = df.shape[0]

    columns = df.shape[1]

    report = f"""
# Dataset Summary

## Overview

- Rows : {rows}

- Columns : {columns}

## Column Names

"""

    for column in df.columns:

        report += f"- {column}\n"

    return report

def missing_value_analysis(df):

    report = """
# Missing Value Report

| Column | Missing Count | Missing Percentage |
|---------|--------------|-------------------|
"""

    missing = df.isnull().sum()

    total_rows = len(df)

    for column, count in missing.items():

        percentage = (
            count / total_rows
        ) * 100

        report += (
            f"| {column} | {count} | {percentage:.2f}% |\n"
        )

    return report

def continuity_analysis(df):

    df["timestamp"] = pd.to_datetime(
        df["timestamp_ms"],
        unit="ms"
    )

    time_diff = (
        df["timestamp"]
        .diff()
        .dt.total_seconds()
        * 1000
    )

    report = f"""
# Time Continuity Report

## Timestamp Gap Analysis

- Mean Gap (ms): {time_diff.mean():.2f}

- Maximum Gap (ms): {time_diff.max():.2f}

- Minimum Gap (ms): {time_diff.min():.2f}
"""

    return report

def statistics_analysis(df):

    signal = df["red_corrected"]

    report = f"""
# Statistics Report

## Signal Statistics

- Mean : {signal.mean():.2f}

- Standard Deviation : {signal.std():.2f}

- Mode : {signal.mode()[0]:.2f}

- Minimum : {signal.min():.2f}

- Maximum : {signal.max():.2f}
"""

    return report

def adf_test_report(df):

    signal = df["red_corrected"]

    result = adfuller(signal)

    adf_statistic = result[0]

    p_value = result[1]

    stationarity = (
        "Stationary"
        if p_value < 0.05
        else "Non-Stationary"
    )

    report = f"""
# ADF Stationarity Test Report

## Results

- ADF Statistic: {adf_statistic:.4f}

- P Value: {p_value:.6f}

- Conclusion: {stationarity}
"""

    return report

def feature_engineering_report(df):

    report = """
# Feature Engineering Report

## Recommended Features

1. Lag Features
   - lag_1
   - lag_5
   - lag_10
   - lag_50

2. Rolling Statistics
   - rolling_mean_10
   - rolling_mean_50
   - rolling_std_10
   - rolling_std_50

3. Time Based Features
   - timestamp
   - elapsed_time

4. Differencing Feature
   - signal_difference

## Rationale

Lag features capture temporal dependency.

Rolling statistics capture local trends and variability.

Differencing helps transform a non-stationary series into a stationary one.

Time-based features preserve temporal information.
"""
    return report

def final_report():

    report = """
# Final Time Series EDA Report

## Key Findings

1. Dataset Length
   - 7423 observations

2. Missing Values
   - No significant missing values detected.

3. Time Continuity
   - Mean sampling interval approximately 20 ms.
   - Timestamp anomaly detected.

4. Trend
   - Multiple upward and downward trends observed.

5. Seasonality
   - Repeating seasonal component detected.

6. Outliers
   - Significant outliers identified through boxplot analysis.

7. Stationarity
   - ADF Test Conclusion: Non-Stationary.

8. Autocorrelation
   - Strong autocorrelation observed across multiple lags.

## Conclusion

The PPG signal exhibits trend, seasonality, strong autocorrelation, and non-stationary behavior. The dataset is suitable for further preprocessing and forecasting model development.
"""
    return report