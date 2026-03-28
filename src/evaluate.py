"""Evaluation harness for the style guide copy editor.

Compares pipeline output against a golden dataset on three axes:
1. Text accuracy: exact match + word-level diff
2. Citation precision: of the rules you cited, how many were correct?
3. Citation recall: of the rules that should have been cited, how many did you find?

Usage:
    python src/evaluate.py --output data/output.json --expected data/expected.json
"""

import argparse
import difflib
import json

from models import OutputFile


def compute_citation_metrics(
    predicted: list[str], expected: list[str]
) -> dict:
    """Compute precision, recall, F1 for citation lists."""
    pred_set = set(predicted)
    exp_set = set(expected)

    if not exp_set and not pred_set:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "tp": 0, "fp": 0, "fn": 0}

    tp = len(pred_set & exp_set)
    fp = len(pred_set - exp_set)
    fn = len(exp_set - pred_set)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def evaluate(output_path: str, expected_path: str):
    """Run evaluation and print report."""
    with open(output_path, "r") as f:
        output = OutputFile(**json.load(f))

    with open(expected_path, "r") as f:
        expected = OutputFile(**json.load(f))

    output_map = {p.id: p for p in output.output}
    expected_map = {p.id: p for p in expected.output}

    all_ids = sorted(set(output_map.keys()) | set(expected_map.keys()))

    print("=" * 70)
    print("STYLE GUIDE EDITOR — EVALUATION REPORT")
    print("=" * 70)

    total_metrics = {"precision": [], "recall": [], "f1": [], "text_match": []}

    for para_id in all_ids:
        pred = output_map.get(para_id)
        exp = expected_map.get(para_id)

        print(f"\n--- {para_id} ---")

        if pred is None:
            print("  MISSING from pipeline output")
            total_metrics["precision"].append(0)
            total_metrics["recall"].append(0)
            total_metrics["f1"].append(0)
            total_metrics["text_match"].append(0)
            continue

        if exp is None:
            print("  No expected output to compare against (skipping)")
            continue

        # Text comparison
        text_match = pred.edit.strip() == exp.edit.strip()
        total_metrics["text_match"].append(1.0 if text_match else 0.0)

        if text_match:
            print("  Text: EXACT MATCH")
        else:
            print("  Text: DIFFERS")
            diff = list(
                difflib.unified_diff(
                    exp.edit.split(),
                    pred.edit.split(),
                    fromfile="expected",
                    tofile="predicted",
                    lineterm="",
                    n=2,
                )
            )
            for line in diff[:20]:
                print(f"    {line}")

        # Citation comparison
        metrics = compute_citation_metrics(pred.citations, exp.citations)
        total_metrics["precision"].append(metrics["precision"])
        total_metrics["recall"].append(metrics["recall"])
        total_metrics["f1"].append(metrics["f1"])

        print(
            f"  Citations: P={metrics['precision']:.1%}  "
            f"R={metrics['recall']:.1%}  F1={metrics['f1']:.1%}  "
            f"(TP={metrics['tp']} FP={metrics['fp']} FN={metrics['fn']})"
        )

        if metrics["fp"] > 0:
            false_pos = set(pred.citations) - set(exp.citations)
            print(f"    False positives: {false_pos}")
        if metrics["fn"] > 0:
            false_neg = set(exp.citations) - set(pred.citations)
            print(f"    Missed rules:    {false_neg}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    n = len(total_metrics["f1"])
    if n > 0:
        avg = lambda vals: sum(vals) / len(vals) if vals else 0
        print(f"  Paragraphs evaluated:   {n}")
        print(f"  Exact text match rate:  {avg(total_metrics['text_match']):.1%}")
        print(f"  Avg citation precision: {avg(total_metrics['precision']):.1%}")
        print(f"  Avg citation recall:    {avg(total_metrics['recall']):.1%}")
        print(f"  Avg citation F1:        {avg(total_metrics['f1']):.1%}")
    else:
        print("  No paragraphs evaluated.")

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Evaluate style editor output")
    parser.add_argument("--output", required=True, help="Pipeline output JSON")
    parser.add_argument("--expected", required=True, help="Golden expected output JSON")
    args = parser.parse_args()

    evaluate(args.output, args.expected)


if __name__ == "__main__":
    main()
