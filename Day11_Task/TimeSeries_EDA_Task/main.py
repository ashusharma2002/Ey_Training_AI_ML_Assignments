from src.data_processing import (
    load_dataset,
    generate_dataset_summary,
    missing_value_analysis,
    continuity_analysis,
    statistics_analysis,
    adf_test_report,
    feature_engineering_report,
    final_report
    
)

from src.report_generator import (
    save_markdown_report
)
from src.visualization import (
    generate_time_series_plot,
    generate_trend_plot,
    generate_boxplot,
    generate_decomposition_plot,
    generate_acf_plot,
    generate_pacf_plot

)

def main():

    df = load_dataset(
    "data/sakshi_ppg.csv"
    )
    print("Dataset Length:", len(df))

    save_markdown_report(
        "artifacts/dataset_summary.md",
        generate_dataset_summary(df)
    )

    save_markdown_report(
        "artifacts/missing_value_report.md",
        missing_value_analysis(df)
    )

    save_markdown_report(
    "artifacts/continuity_report.md",
    continuity_analysis(df)
    )

    save_markdown_report(
    "artifacts/statistics_report.md",
    statistics_analysis(df)
    )
    save_markdown_report(
    "artifacts/adf_report.md",
    adf_test_report(df)
    )
    save_markdown_report(
    "artifacts/feature_engineering_report.md",
    feature_engineering_report(df)
    )
    save_markdown_report(
    "artifacts/final_report.md",
    final_report()
    )

    generate_time_series_plot(df)
    generate_trend_plot(df)
    generate_boxplot(df)
    generate_decomposition_plot(df)
    generate_acf_plot(df)
    generate_pacf_plot(df)

    print(
        "Artifacts Generated Successfully"
    )


if __name__ == "__main__":

    main()