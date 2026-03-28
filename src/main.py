"""Main pipeline entry point.

Orchestrates: load → NLP → percolate → LLM edit → write output.

Usage:
    python src/main.py --input data/input.json --output data/output.json
"""

import argparse
import json
import os
import sys

from openai import OpenAI

from models import InputFile, OutputFile, OutputParagraph, RuleIndex
from nlp import process_paragraph
from retrieval import InMemoryPercolator
from editor import edit_paragraph


def load_rule_index(index_path: str) -> RuleIndex:
    """Load the pre-built rule index."""
    with open(index_path, "r") as f:
        return RuleIndex(**json.load(f))


def run_pipeline(input_path: str, output_path: str, index_path: str):
    """Run the full style editing pipeline."""
    client = OpenAI()  # uses OPENAI_API_KEY env var

    # Step 1: Load inputs and rule index
    print("Step 1: Loading inputs and rule index...")
    with open(input_path, "r") as f:
        input_data = InputFile(**json.load(f))
    print(f"  {len(input_data.input)} paragraphs loaded")

    rule_index = load_rule_index(index_path)
    percolator = InMemoryPercolator(rule_index)
    total_terms = sum(len(r.terms) for r in rule_index.rules)
    total_patterns = sum(len(r.patterns) for r in rule_index.rules)
    print(f"  {len(rule_index.rules)} rules loaded ({total_terms} terms, {total_patterns} patterns)")

    results: list[OutputParagraph] = []

    for para in input_data.input:
        print(f"\nProcessing {para.id}...")

        # Step 2: NLP processing
        processed = process_paragraph(para.text)
        print(f"  Step 2 (NLP): {len(processed.sentences)} sentences")

        # Step 3: Percolate — find rules whose matchers fire on this text
        candidate_rules = percolator.find_relevant_rules(para.text)
        print(
            f"  Step 3 (Percolate): {len(candidate_rules)} candidate rules"
        )
        for rule in candidate_rules:
            print(f"    → {rule.title}")

        # Step 4: LLM editing — apply candidate rules to full paragraph
        result = edit_paragraph(client, processed, candidate_rules, para.id)
        print(f"  Step 4 (Edit): {len(result.citations)} rules applied")
        for cid in result.citations:
            rule = percolator.rules_by_id.get(cid)
            if rule:
                print(f"    ✓ {rule.title}")

        results.append(result)

    # Step 5: Write output
    output = OutputFile(output=results)
    with open(output_path, "w") as f:
        json.dump(output.model_dump(), f, indent=2)

    print(f"\nOutput written to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Style Guide Copy Editor Pipeline")
    parser.add_argument("--input", required=True, help="Path to input JSON file")
    parser.add_argument("--output", required=True, help="Path to write output JSON file")
    parser.add_argument(
        "--index",
        default=None,
        help="Path to rule index JSON (default: data/rule_index.json)",
    )
    args = parser.parse_args()

    # Default index path relative to project root
    if args.index is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(script_dir)
        args.index = os.path.join(project_dir, "data", "rule_index.json")

    if not os.path.exists(args.index):
        print(
            f"ERROR: Rule index not found at {args.index}\n"
            f"Run 'python src/build_index.py' first to generate it.",
            file=sys.stderr,
        )
        sys.exit(1)

    run_pipeline(args.input, args.output, args.index)


if __name__ == "__main__":
    main()
