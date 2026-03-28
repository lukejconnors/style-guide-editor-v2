"""Rule retrieval using an in-memory percolator pattern.

Each rule stores its own matching logic (terms + regex patterns).
Input text is tested against all rules to find which ones are relevant.

This mirrors the Elasticsearch percolator concept:
- In ES, each rule would be stored as a percolator query document
- At query time, ES runs input text against all stored queries
- Results are rules whose queries match the input

The in-memory implementation here uses the same model:
rule carries its matcher → input is tested against all matchers.

To migrate to Elasticsearch:

    # Index mapping
    PUT style_rules
    {
      "mappings": {
        "properties": {
          "title":   { "type": "text" },
          "text":    { "type": "text" },
          "content": { "type": "text" },
          "query":   { "type": "percolator" }
        }
      }
    }

    # Index a rule as a percolator query
    PUT style_rules/_doc/{rule_id}
    {
      "title": "adviser",
      "text": "Use adviser instead of advisor...",
      "query": {
        "bool": {
          "should": [
            { "match_phrase": { "content": "adviser" } },
            { "match_phrase": { "content": "advisor" } }
          ],
          "minimum_should_match": 1
        }
      }
    }

    # Query: which rules match this text?
    GET style_rules/_search
    {
      "query": {
        "percolate": {
          "field": "query",
          "document": { "content": "A senior advisor working the phones..." }
        }
      }
    }
"""

import re

from models import IndexedRule, RuleIndex


class RuleMatcher:
    """A compiled matcher for a single rule.

    Encapsulates the matching logic (terms + regex) so the percolator
    can test input text against it.

    In Elasticsearch, this would be a stored percolator query with
    match_phrase and regexp clauses in a bool/should.
    """

    def __init__(self, rule_id: str, terms: list[str], patterns: list[str]):
        self.rule_id = rule_id

        # Pre-compute lowercased terms for case-insensitive matching
        # ES equivalent: match_phrase clauses (case-insensitive by default)
        self.terms = [t.lower() for t in terms]

        # Compile regex patterns once
        # ES equivalent: regexp clauses in the percolator query
        self.compiled_patterns: list[re.Pattern] = []
        for pattern in patterns:
            try:
                self.compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error:
                print(f"  Warning: invalid regex for rule {rule_id}: {pattern}")

    def matches(self, text: str) -> bool:
        """Test if input text matches this rule's criteria.

        Returns True if any term or pattern matches.
        ES equivalent: the percolate query returns this rule in hits.
        """
        lowered = text.lower()

        # Check terms (phrase match)
        for term in self.terms:
            if term in lowered:
                return True

        # Check regex patterns
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                return True

        return False


class InMemoryPercolator:
    """In-memory implementation of the percolator pattern.

    Stores compiled matchers for all rules. At query time, runs input
    text against every matcher and returns the rules that match.

    At scale (12k+ rules), migrate to Elasticsearch percolator which
    builds an inverted index over stored queries for faster matching.
    """

    def __init__(self, index: RuleIndex):
        self.rules_by_id: dict[str, IndexedRule] = {}
        self.matchers: list[RuleMatcher] = []

        for rule in index.rules:
            self.rules_by_id[rule.id] = rule
            self.matchers.append(
                RuleMatcher(
                    rule_id=rule.id,
                    terms=rule.terms,
                    patterns=rule.patterns,
                )
            )

    def percolate(self, text: str) -> set[str]:
        """Find all rules that match the given text.

        Tests input text against every rule's matcher.
        Returns set of matching rule IDs.

        ES equivalent:
            POST style_rules/_search
            { "query": { "percolate": { "field": "query",
              "document": { "content": text } } } }
        """
        return {
            matcher.rule_id
            for matcher in self.matchers
            if matcher.matches(text)
        }

    def find_relevant_rules(self, text: str) -> list[IndexedRule]:
        """Find all rules relevant to the input text.

        Runs percolation, then returns full rule objects for matched IDs.
        """
        matched_ids = self.percolate(text)
        return [self.rules_by_id[rid] for rid in matched_ids]
