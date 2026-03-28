"""Data models for the style guide editor pipeline."""

from pydantic import BaseModel


# --- Input/Output schemas ---

class InputParagraph(BaseModel):
    id: str
    text: str


class InputFile(BaseModel):
    input: list[InputParagraph]


class OutputParagraph(BaseModel):
    id: str
    edit: str
    citations: list[str]


class OutputFile(BaseModel):
    output: list[OutputParagraph]


# --- Rule database schemas ---

class Rule(BaseModel):
    id: str
    title: str
    text: str


class RuleDB(BaseModel):
    rules: list[Rule]


# --- Rule index schemas ---
# Structured to map directly to Elasticsearch percolator queries:
#   terms    → match_phrase clauses in a bool/should query
#   patterns → regexp clauses in a bool/should query

class IndexedRule(BaseModel):
    id: str
    title: str
    text: str
    terms: list[str]        # lowercased phrases for exact matching
    patterns: list[str]     # regex patterns for structural rules


class RuleIndex(BaseModel):
    rules: list[IndexedRule]
