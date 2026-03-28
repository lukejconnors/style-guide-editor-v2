# Style Rule Copy Editor

A pipeline that applies POLITICO style guide rules to editorial copy, producing corrected text with citations to the rules applied.

## Architecture

The system uses a **percolator pattern** for rule retrieval: each rule stores its own matching logic (terms + regex patterns), and input text is tested against all rules to find which ones are relevant. This mirrors the [Elasticsearch percolator](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-percolate-query.html), where stored queries are matched against incoming documents — the inverse of traditional search.

```
Input paragraph
    │
    ▼
┌──────────────────────────┐
│  spaCy NLP Processing    │  sentence split, POS tags, NER
└──────────────────────────┘
    │
    ▼
┌──────────────────────────┐
│  In-Memory Percolator    │  each rule's matcher (terms + regex) is tested
│                          │  against the input text → relevant rules
└──────────────────────────┘
    │
    ▼ (candidate rules for whole paragraph)
┌──────────────────────────┐
│  LLM Edit (GPT-4.1)      │  full paragraph + candidate rules → corrected text
└──────────────────────────┘
    │
    ▼
Output JSON (corrected text + cited rule IDs)
```

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download spaCy English model
python -m spacy download en_core_web_sm

# 3. Set OpenAI API key
export OPENAI_API_KEY=your-key-here

# 4. Build the rule index (one-time)
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
│   ├── DB.json             ← Style rules database (DO NOT MODIFY)
│   ├── rule_index.json     ← Generated percolator index (from build_index.py)
│   ├── input.json          ← Input paragraphs
│   └── output.json         ← Pipeline output
├── src/
│   ├── main.py             ← Pipeline orchestrator
│   ├── build_index.py      ← One-time: LLM generates match terms/patterns per rule
│   ├── nlp.py              ← spaCy NLP processing
│   ├── retrieval.py        ← In-memory percolator (with ES migration comments)
│   ├── editor.py           ← LLM editing with GPT-4.1
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
| 2 | `nlp.py` | spaCy: sentence segmentation, POS tags, NER |
| 3 | `retrieval.py` | Percolate: test input text against all rule matchers |
| 4 | `editor.py` | GPT-4.1 applies candidate rules → corrected text + citations |
| 5 | `main.py` | Write output JSON |

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
