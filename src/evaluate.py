"""Evaluation harness for the style guide copy editor.

Scores pipeline output against a golden dataset on two axes:

1. Edit accuracy (50% of composite score)
   Extracts word-level diffs from original→predicted and original→expected,
   then computes precision/recall/F1 over the set of edits. This measures
   whether you made the right changes and only the right changes.

2. Citation accuracy (50% of composite score)
   Set comparison of cited rule IDs. Precision/recall/F1.

The composite score is the mean of edit F1 and citation F1 per paragraph,
averaged across all paragraphs. This gives a single trackable number
for benchmarking across iterations.

Usage:
    python src/evaluate.py \
        --input data/input.json \
        --output data/output.json \
        --expected data/golden_output.json
"""

import argparse
import difflib
import json

from models import InputFile, OutputFile


# --- Edit extraction ---

def extract_edits(original: str, edited: str) -> set[tuple[str, str]]:
    """Extract word-level edits between original and edited text.

    Uses difflib.SequenceMatcher to find changed spans.
    Returns a set of (original_span, edited_span) tuples.

    Example:
        original: "Her Press Secretary Alex Rivera"
        edited:   "Her press secretary Alex Rivera"
        returns:  {("Press Secretary", "press secretary")}
    """
    orig_words = original.split()
    edit_words = edited.split()

    matcher = difflib.SequenceMatcher(None, orig_words, edit_words)
    edits = set()

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        orig_span = " ".join(orig_words[i1:i2])
        edit_span = " ".join(edit_words[j1:j2])
        edits.add((orig_span, edit_span))

    return edits


def compute_edit_metrics(
    original: str, predicted: str, expected: str
) -> dict:
    """Compute precision, recall, F1 over edit operations.

    Compares the set of edits (original→predicted) against
    the set of edits (original→expected).

    - Precision: of the edits you made, how many were correct?
    - Recall: of the edits that should have been made, how many did you make?
    """
    pred_edits = extract_edits(original, predicted)
    exp_edits = extract_edits(original, expected)

    # No edits expected and none made = perfect
    if not exp_edits and not pred_edits:
        return {
            "precision": 1.0, "recall": 1.0, "f1": 1.0,
            "tp": 0, "fp": 0, "fn": 0,
            "pred_edits": pred_edits, "exp_edits": exp_edits,
        }

    tp = len(pred_edits & exp_edits)
    fp = len(pred_edits - exp_edits)
    fn = len(exp_edits - pred_edits)

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
        "pred_edits": pred_edits,
        "exp_edits": exp_edits,
    }


# --- Citation metrics ---

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


# --- Main evaluation ---

EDIT_WEIGHT = 0.5
CITATION_WEIGHT = 0.5


def evaluate(input_path: str, output_path: str, expected_path: str):
    """Run evaluation and print report."""
    with open(input_path, "r") as f:
        inputs = InputFile(**json.load(f))

    with open(output_path, "r") as f:
        output = OutputFile(**json.load(f))

    with open(expected_path, "r") as f:
        expected = OutputFile(**json.load(f))

    input_map = {p.id: p for p in inputs.input}
    output_map = {p.id: p for p in output.output}
    expected_map = {p.id: p for p in expected.output}

    all_ids = sorted(set(output_map.keys()) | set(expected_map.keys()))

    print("=" * 70)
    print("STYLE GUIDE EDITOR — EVALUATION REPORT")
    print("=" * 70)

    composite_scores = []
    all_edit_metrics = []
    all_citation_metrics = []

    for para_id in all_ids:
        original = input_map.get(para_id)
        pred = output_map.get(para_id)
        exp = expected_map.get(para_id)

        print(f"\n{'─' * 70}")
        print(f"  {para_id}")
        print(f"{'─' * 70}")

        if pred is None:
            print("  MISSING from pipeline output")
            composite_scores.append(0.0)
            all_edit_metrics.append({"f1": 0.0})
            all_citation_metrics.append({"f1": 0.0})
            continue

        if exp is None or original is None:
            print("  No expected output or original input (skipping)")
            continue

        # --- Edit accuracy ---
        edit_m = compute_edit_metrics(original.text, pred.edit, exp.edit)
        all_edit_metrics.append(edit_m)

        exact_match = pred.edit.strip() == exp.edit.strip()

        print(f"\n  EDITS {'(EXACT MATCH)' if exact_match else ''}")
        print(
            f"    P={edit_m['precision']:.1%}  "
            f"R={edit_m['recall']:.1%}  F1={edit_m['f1']:.1%}  "
            f"(correct={edit_m['tp']}  extra={edit_m['fp']}  missed={edit_m['fn']})"
        )

        # Show specific edit diffs
        if edit_m["fp"] > 0:
            wrong_edits = edit_m["pred_edits"] - edit_m["exp_edits"]
            for orig_span, edit_span in wrong_edits:
                label = "UNEXPECTED" if orig_span else "INSERTED"
                print(f'    {label}: "{orig_span}" → "{edit_span}"')

        if edit_m["fn"] > 0:
            missed_edits = edit_m["exp_edits"] - edit_m["pred_edits"]
            for orig_span, edit_span in missed_edits:
                print(f'    MISSED:     "{orig_span}" → "{edit_span}"')

        # --- Citation accuracy ---
        cite_m = compute_citation_metrics(pred.citations, exp.citations)
        all_citation_metrics.append(cite_m)

        print(f"\n  CITATIONS")
        print(
            f"    P={cite_m['precision']:.1%}  "
            f"R={cite_m['recall']:.1%}  F1={cite_m['f1']:.1%}  "
            f"(correct={cite_m['tp']}  extra={cite_m['fp']}  missed={cite_m['fn']})"
        )

        if cite_m["fp"] > 0:
            print(f"    Extra:  {set(pred.citations) - set(exp.citations)}")
        if cite_m["fn"] > 0:
            print(f"    Missed: {set(exp.citations) - set(pred.citations)}")

        # --- Composite ---
        composite = (edit_m["f1"] * EDIT_WEIGHT) + (cite_m["f1"] * CITATION_WEIGHT)
        composite_scores.append(composite)
        print(f"\n  COMPOSITE SCORE: {composite:.1%}")

    # === Summary ===
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")

    n = len(composite_scores)
    if n > 0:
        avg = lambda vals: sum(vals) / len(vals)

        avg_edit_f1 = avg([m["f1"] for m in all_edit_metrics])
        avg_cite_f1 = avg([m["f1"] for m in all_citation_metrics])
        avg_composite = avg(composite_scores)

        exact_matches = sum(1 for m in all_edit_metrics if m["f1"] == 1.0)

        print(f"  Paragraphs evaluated:     {n}")
        print(f"  Exact text matches:       {exact_matches}/{n}")
        print(f"")
        print(f"  Avg edit F1:              {avg_edit_f1:.1%}")
        print(f"  Avg citation F1:          {avg_cite_f1:.1%}")
        print(f"")
        print(f"  ┌─────────────────────────────────┐")
        print(f"  │  COMPOSITE SCORE:  {avg_composite:.1%}          │")
        print(f"  │  (edit F1 × {EDIT_WEIGHT} + citation F1 × {CITATION_WEIGHT})  │")
        print(f"  └─────────────────────────────────┘")
    else:
        print("  No paragraphs evaluated.")

    print(f"{'=' * 70}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate style editor output")
    parser.add_argument("--input", required=True, help="Original input JSON")
    parser.add_argument("--output", required=True, help="Pipeline output JSON")
    parser.add_argument("--expected", required=True, help="Golden expected output JSON")
    args = parser.parse_args()

    evaluate(args.input, args.output, args.expected)


if __name__ == "__main__":
    main()