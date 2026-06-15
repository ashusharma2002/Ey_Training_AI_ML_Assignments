import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.graphics.tsaplots import (
    plot_acf,
    plot_pacf
)


def generate_time_series_plot(df):

    df["timestamp"] = pd.to_datetime(
        df["timestamp_ms"],
        unit="ms"
    )

    plt.figure(figsize=(12, 6))

    plt.plot(
        df["timestamp"],
        df["red_corrected"]
    )

    plt.title(
        "PPG Signal Over Time"
    )

    plt.xlabel("Time")

    plt.ylabel(
        "Red Corrected Signal"
    )

    plt.tight_layout()

    plt.savefig(
        "artifacts/time_series_plot.png"
    )

    plt.close()

def generate_trend_plot(df):

    df["trend"] = (
        df["red_corrected"]
        .rolling(window=50)
        .mean()
    )

    plt.figure(figsize=(12, 6))

    plt.plot(
        df["red_corrected"],
        label="Original Signal"
    )

    plt.plot(
        df["trend"],
        linewidth=3,
        label="Trend"
    )

    plt.title(
        "Trend Analysis"
    )

    plt.xlabel(
        "Observation"
    )

    plt.ylabel(
        "Red Corrected Signal"
    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        "artifacts/trend_plot.png"
    )

    plt.close()

import seaborn as sns


def generate_boxplot(df):

    plt.figure(figsize=(8, 6))

    sns.boxplot(
        y=df["red_corrected"]
    )

    plt.title(
        "PPG Signal Boxplot"
    )

    plt.ylabel(
        "Red Corrected Signal"
    )

    plt.tight_layout()

    plt.savefig(
        "artifacts/boxplot.png"
    )

    plt.close()

def generate_decomposition_plot(df):

    signal = df["red_corrected"]

    decomposition = seasonal_decompose(
        signal,
        model="additive",
        period=50
    )

    fig = decomposition.plot()

    fig.set_size_inches(12, 8)

    plt.tight_layout()

    plt.savefig(
        "artifacts/decomposition_plot.png"
    )

    plt.close()

def generate_acf_plot(df):

    plt.figure(figsize=(10, 5))

    plot_acf(
        df["red_corrected"],
        lags=50
    )

    plt.tight_layout()

    plt.savefig(
        "artifacts/acf_plot.png"
    )

    plt.close()

def generate_pacf_plot(df):

    plt.figure(figsize=(10, 5))

    plot_pacf(
        df["red_corrected"],
        lags=50
    )

    plt.tight_layout()

    plt.savefig(
        "artifacts/pacf_plot.png"
    )

    plt.close()