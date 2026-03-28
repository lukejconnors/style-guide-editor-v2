"""LLM-based style editing: sends paragraph + candidate rules to GPT for correction."""

import json

from openai import OpenAI

from models import IndexedRule, OutputParagraph
from nlp import ProcessedParagraph
from prompts import EDITOR_SYSTEM, EDITOR_USER


def format_rules_for_prompt(rules: list[IndexedRule]) -> str:
    """Format candidate rules as a readable block for the LLM prompt."""
    parts = []
    for rule in rules:
        parts.append(f"Rule ID: {rule.id}\nTitle: {rule.title}\nRule: {rule.text}")
    return "\n---\n".join(parts)


def edit_paragraph(
    client: OpenAI,
    paragraph: ProcessedParagraph,
    candidate_rules: list[IndexedRule],
    paragraph_id: str,
) -> OutputParagraph:
    """Apply style rules to a paragraph via LLM.

    Args:
        client: OpenAI client
        paragraph: NLP-processed paragraph
        candidate_rules: rules identified as potentially relevant by percolator
        paragraph_id: ID from input file

    Returns:
        OutputParagraph with corrected text and cited rule IDs
    """
    # If no candidate rules matched, return original text unchanged
    if not candidate_rules:
        return OutputParagraph(
            id=paragraph_id,
            edit=paragraph.text,
            citations=[],
        )

    # Build prompt
    rules_block = format_rules_for_prompt(candidate_rules)
    pos_context = paragraph.pos_tags_str()

    user_prompt = EDITOR_USER.format(
        paragraph=paragraph.text,
        pos_tags=pos_context,
        rules=rules_block,
    )

    response = client.chat.completions.create(
        model="gpt-4.1",
        temperature=0,
        messages=[
            {"role": "system", "content": EDITOR_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()
    result = json.loads(raw)

    # Validate: only allow citations for rules we actually sent
    valid_rule_ids = {r.id for r in candidate_rules}
    citations = [cid for cid in result.get("citations", []) if cid in valid_rule_ids]

    return OutputParagraph(
        id=paragraph_id,
        edit=result.get("edit", paragraph.text),
        citations=citations,
    )
