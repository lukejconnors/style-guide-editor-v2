# Style Rule Copy Editor

A pipeline that applies POLITICO style guide rules to editorial copy, producing corrected text with citations to the rules applied.

## Architecture

The system uses a **percolator pattern** for rule retrieval: each rule stores its own matching logic (terms + regex patterns), and input text is tested against all rules to find which ones are relevant. This mirrors the [Elasticsearch percolator](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-percolate-query.html), where stored queries are matched against incoming documents — the inverse of traditional search.

### One-Time Setup: Rule Index Generation

```
DB.json (style rules)
    │
    ▼
┌──────────────────────────┐
│  LLM Index Builder       │  GPT-5 generates match terms + regex patterns
│  (build_index.py)        │  for each rule (e.g., "adviser" → ["adviser", "advisor"])
└──────────────────────────┘
    │
    ▼
rule_index.json (cached matchers)
```

### Runtime Pipeline

```
For each input paragraph
    │
    ▼
┌──────────────────────────┐
│  In-Memory Percolator    │  each rule's matcher (terms + regex) is tested against the input 
│                          │  text to find relevant rules in Elasticsearch percolator style
└──────────────────────────┘
    │
    ▼ (candidate rules for whole paragraph)
┌──────────────────────────┐
│  LLM Copy Editor         │  full paragraph + candidate rules → corrected text + citations
│  (GPT-5)                 │  
└──────────────────────────┘
    │
    ▼
Output JSON (corrected text + edits + cited rule IDs)
    │
    ▼ (optional, if golden output exists)
┌──────────────────────────┐
│  Evaluation              │  compares output vs golden, computes edit F1 + citation F1
│  (evaluate.py)           │  
└──────────────────────────┘
    │
    ▼
Benchmark Score (0-100%)
```

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set OpenAI API key
export OPENAI_API_KEY=your-key-here

# 3. Build the rule index (one-time)
python src/build_index.py
```

## Usage

```bash
# Run the pipeline
./run.sh

# Run with custom paths
python src/main.py --input data/input.json --output data/output.json

# Evaluate against expected output
python src/evaluate.py --output data/output.json --expected data/expected.json
```

## File Structure

```
├── run.sh                  ← Entry point
├── requirements.txt        ← Python dependencies
├── data/
│   ├── DB.json             ← Style rules database
│   ├── rule_index.json     ← Generated percolator index (from build_index.py on first run)
│   ├── input.json          ← Input paragraphs
│   └── output.json         ← Pipeline output
├── src/
│   ├── main.py             ← Pipeline orchestrator
│   ├── build_index.py      ← One-time: LLM generates match terms/patterns per rule
│   ├── retrieval.py        ← In-memory percolator (with ES migration comments)
│   ├── copy_editor.py      ← LLM copy editing with GPT-5
│   ├── prompts.py          ← Prompt templates
│   ├── evaluate.py         ← Evaluation harness
│   └── models.py           ← Pydantic data models
└── Agents.md               ← AI delegation documentation
```

## Pipeline Steps

| Step | Module | Description |
|------|--------|-------------|
| 0 (one-time) | `build_index.py` | LLM generates match terms + regex patterns per rule |
| 1 | `main.py` | Load input paragraphs and rule index |
| 2 | `retrieval.py` | Percolate: test input text against all rule matchers |
| 3 | `copy_editor.py` | GPT-5 applies candidate rules → corrected text + citations |
| 4 | `main.py` | Write output JSON |

## Scaling Path

The in-memory percolator works well at 50 rules. At 12k+ rules, the architecture migrates to Elasticsearch:

- **Rule matchers** → ES percolator queries (match_phrase + regexp in bool/should)
- **Percolation** → single ES percolate query replaces iterating all matchers
- **build_index.py** → writes percolator query documents to ES instead of JSON file

See comments in `retrieval.py` for the ES query equivalents.

## Evaluation

Measures three axes against a golden dataset:
- **Text accuracy**: exact match of corrected text
- **Citation precision**: of rules cited, how many were correct?
- **Citation recall**: of rules that should be cited, how many were found?
- **Citation F1**: harmonic mean of precision and recall

## Design Questions

### Should quoted text be edited?

The assignment states: "Quoted text is not automatically exempt from edits."

This creates ambiguity. Consider:
> "I spoke with the advisor yesterday," the senator said.

Applying the `adviser` rule ("use adviser instead of advisor"):
- **Option A**: Edit to "adviser" — the rule applies universally, and the constraint says quotes aren't exempt.
- **Option B**: Preserve "advisor" — altering a source's direct speech changes attribution, violating the "do not change meaning or attribution" constraint.

Some rules explicitly carve out exceptions (e.g., "Honorifics — Do not use honorifics outside of direct quotations"), but most rules don't specify. The current implementation leaves this decision to the LLM based on rule text, without encoding a blanket policy either way.

A production system would need editorial guidance on whether direct quotes should be altered to match house style or preserved as spoken.
