"""NLP processing using spaCy: sentence splitting, tokenization, POS tagging."""

from dataclasses import dataclass, field

import spacy

# Load model once at module level
nlp = spacy.load("en_core_web_sm")


@dataclass
class ProcessedSentence:
    """NLP-processed sentence with extracted features."""

    text: str                           # original sentence text
    tokens: list[str]                   # individual word tokens
    pos_tags: list[tuple[str, str]]     # (token, POS) pairs
    entities: list[tuple[str, str]]     # (entity_text, entity_label) pairs


@dataclass
class ProcessedParagraph:
    """NLP-processed paragraph containing processed sentences."""

    text: str  # original paragraph text
    sentences: list[ProcessedSentence] = field(default_factory=list)

    def pos_tags_str(self) -> str:
        """Format POS tags as a readable string for LLM context."""
        parts = []
        for sent in self.sentences:
            tagged = [f"{token}/{pos}" for token, pos in sent.pos_tags]
            parts.append(" ".join(tagged))
        return " | ".join(parts)


def process_paragraph(text: str) -> ProcessedParagraph:
    """Run full NLP pipeline on a paragraph.

    Returns a ProcessedParagraph with sentence-level features.
    POS tags are used downstream by the LLM editor to disambiguate
    noun/verb usage (e.g., "startup" as noun vs. "start up" as verb).
    """
    doc = nlp(text)
    paragraph = ProcessedParagraph(text=text)

    for sent in doc.sents:
        tokens = [token.text for token in sent if not token.is_space]

        pos_tags = [(token.text, token.pos_) for token in sent if not token.is_space]

        entities = [(ent.text, ent.label_) for ent in sent.ents]

        paragraph.sentences.append(
            ProcessedSentence(
                text=sent.text.strip(),
                tokens=tokens,
                pos_tags=pos_tags,
                entities=entities,
            )
        )

    return paragraph
