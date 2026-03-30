"""Build the rule index: generate match configurations via LLM.

Run once during development, not per-pipeline-execution:
    python src/build_index.py

Reads:  data/DB.json
Writes: data/rule_index.json
"""

import json
import os
import time

from openai import OpenAI
from models import Rule, RuleDB, IndexedRule, RuleIndex
from prompts import TRIGGER_GENERATION_SYSTEM, TRIGGER_GENERATION_USER


def generate_match_config(client: OpenAI, rule: Rule) -> dict:
    """Use GPT to generate match terms and patterns for a single rule.

    Returns dict with "terms" and "patterns" keys.
    """
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": TRIGGER_GENERATION_SYSTEM},
            {
                "role": "user",
                "content": TRIGGER_GENERATION_USER.format(
                    title=rule.title, text=rule.text
                ),
            },
        ],
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content.strip()
    config = json.loads(raw)

    # Normalize terms: lowercase, strip whitespace, deduplicate
    terms = list(set(
        t.lower().strip()
        for t in config.get("terms", [])
        if isinstance(t, str) and t.strip()
    ))

    # Patterns: keep as-is (regex strings)
    patterns = [
        p for p in config.get("patterns", [])
        if isinstance(p, str) and p.strip()
    ]

    return {"terms": terms, "patterns": patterns}


def build_index(db_path: str, output_path: str):
    """Build the full rule index."""
    client = OpenAI()  # uses OPENAI_API_KEY env var

    # Load rules
    with open(db_path, "r") as f:
        db = RuleDB(**json.load(f))

    print(f"Processing {len(db.rules)} rules...")

    indexed_rules = []
    for i, rule in enumerate(db.rules):
        print(f"  [{i + 1}/{len(db.rules)}] {rule.title}")
        config = generate_match_config(client, rule)
        print(f"    terms:    {config['terms']}")
        if config["patterns"]:
            print(f"    patterns: {config['patterns']}")

        indexed_rules.append(
            IndexedRule(
                id=rule.id,
                title=rule.title,
                text=rule.text,
                terms=config["terms"],
                patterns=config["patterns"],
            )
        )
        time.sleep(0.2)  # light rate limiting

    # Write index
    index = RuleIndex(rules=indexed_rules)
    with open(output_path, "w") as f:
        json.dump(index.model_dump(), f, indent=2)

    print(f"\nRule index written to {output_path}")
    print(f"  {len(indexed_rules)} rules indexed")
    print(f"  {sum(len(r.terms) for r in indexed_rules)} total terms")
    print(f"  {sum(len(r.patterns) for r in indexed_rules)} total patterns")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    db_path = os.path.join(project_dir, "data", "DB.json")
    output_path = os.path.join(project_dir, "data", "rule_index.json")

    build_index(db_path, output_path)
