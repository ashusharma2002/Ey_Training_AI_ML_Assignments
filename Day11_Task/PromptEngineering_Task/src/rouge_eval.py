import pandas as pd

from rouge_score import rouge_scorer


def calculate_rouge(results):

    scorer = rouge_scorer.RougeScorer(
        ["rougeL"],
        use_stemmer=True
    )

    rouge_results = []

    for item in results:

        reference = item["reference_summary"]

        zero_score = scorer.score(
            reference,
            item["zero_shot_summary"]
        )["rougeL"].fmeasure

        few_score = scorer.score(
            reference,
            item["few_shot_summary"]
        )["rougeL"].fmeasure

        rouge_results.append(
            {
                "call_id": item["id"],
                "zero_shot_rougeL": round(
                    zero_score,
                    4
                ),
                "few_shot_rougeL": round(
                    few_score,
                    4
                )
            }
        )

    return rouge_results


def save_rouge_results(
    rouge_results,
    output_path
):

    df = pd.DataFrame(
        rouge_results
    )

    df.to_csv(
        output_path,
        index=False
    )

    print(
        f"ROUGE-L scores saved to: {output_path}"
    )