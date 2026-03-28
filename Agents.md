# Agents.md — AI Delegation Documentation

## Overview

This document records how AI tools were used during development of the style guide copy editor, what was delegated vs. authored directly, and what was verified.

## AI Usage in the Pipeline

### Rule Index Generation (`build_index.py`)
- **Delegated to AI:** Generating match terms and regex patterns for each style rule. GPT-4.1 reads each rule's title and text and produces a structured match configuration (terms for phrase matching, patterns for regex).
- **Why:** Manually writing match configs for 50 rules is feasible but error-prone — easy to miss variant spellings or alternate forms. At 12k rules it would be impractical. The LLM reliably generates both correct and incorrect forms of each term.
- **Verification:** Reviewed generated match configs against example input/output pairs. Checked that each rule's terms cover the forms that appear in the test paragraphs. Spot-checked regex patterns compile correctly.
- **What the system constrains:** Match configs are generated once and cached as a static JSON file. They are human-reviewable and editable. The LLM is not called at retrieval time.

### Style Editing (`editor.py`)
- **Delegated to AI:** Determining which candidate rules are actually violated and producing corrected text with minimum edits.
- **Why:** Rule application requires contextual judgment — noun vs. verb usage, casing conventions, whether a term appears in a quote, whether a change would alter meaning. This is the core editorial task the LLM is suited for.
- **What the system constrains:** The LLM only sees rules surfaced by the percolator — it cannot invent corrections from external style guides. The prompt enforces minimum-edit constraints. Structured JSON output is required. Post-processing validates that cited rule IDs exist in the candidate set.

## AI Usage in Development

TODO: Fill in after completing the project.
- What tools were used (Claude, Copilot, ChatGPT, etc.)
- What was accepted vs. rejected from AI suggestions
- How AI-generated code was verified
