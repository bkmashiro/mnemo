"""Grammar engine for mnemonic sentence construction.

Defines the sentence patterns used to encode bytes into grammatically
structured phrases. Each pattern specifies a sequence of parts-of-speech,
and the grammar engine handles serialization and parsing.

Sentence Patterns (bytes encoded per sentence):
  - CLAUSE:  adj noun verb adj noun           = 5 bytes
  - PHRASE:  det adj noun verb det adj noun    = 7 bytes  (with checksum determiners)
  - MINI:    adj noun verb                     = 3 bytes

The PHRASE pattern includes two determiner slots that serve as lightweight
checksums over their neighboring words, providing error detection.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import hashlib
import struct


class GrammarError(Exception):
    """Raised when a sentence doesn't conform to expected grammar."""
    pass


@dataclass
class Sentence:
    """A single encoded sentence with its word slots."""
    pattern: str
    words: List[str]
    slots: List[str]  # POS tags for each word

    def __str__(self) -> str:
        return " ".join(self.words)

    def to_display(self) -> str:
        """Format for human display with punctuation."""
        if not self.words:
            return ""
        text = " ".join(self.words)
        return text[0].upper() + text[1:] + "."


# Pattern definitions: each entry is (pattern_name, [pos_tags], data_byte_count)
PATTERNS = {
    "clause": (["adjective", "noun", "verb", "adjective", "noun"], 5),
    "phrase": (["determiner", "adjective", "noun", "verb", "determiner", "adjective", "noun"], 5),
    "mini":   (["adjective", "noun", "verb"], 3),
}

# Default pattern for encoding
DEFAULT_PATTERN = "clause"


class Grammar:
    """Handles sentence construction, parsing, and checksum validation."""

    def __init__(self, pattern: str = DEFAULT_PATTERN) -> None:
        if pattern not in PATTERNS:
            raise ValueError(f"Unknown pattern: {pattern}. Choose from: {list(PATTERNS.keys())}")
        self.pattern = pattern
        self.slots, self.data_bytes = PATTERNS[pattern]

    @property
    def words_per_sentence(self) -> int:
        return len(self.slots)

    @property
    def bytes_per_sentence(self) -> int:
        return self.data_bytes

    def compute_determiners(self, data_bytes_values: List[int]) -> Tuple[int, int]:
        """Compute checksum determiners for phrase pattern.

        Uses a simple hash of the data bytes to derive two check bytes,
        mapped to the determiner word list.
        """
        raw = bytes(data_bytes_values)
        h = hashlib.sha256(raw).digest()
        return h[0], h[1]

    def data_slot_indices(self) -> List[int]:
        """Return indices of slots that carry data (non-determiner slots)."""
        return [i for i, s in enumerate(self.slots) if s != "determiner"]

    def determiner_slot_indices(self) -> List[int]:
        """Return indices of determiner (checksum) slots."""
        return [i for i, s in enumerate(self.slots) if s == "determiner"]

    def build_sentence(self, data_words: List[Tuple[str, str]],
                       det_words: Optional[List[Tuple[str, str]]] = None) -> Sentence:
        """Build a Sentence from data words and optional determiner words.

        Args:
            data_words: List of (word, pos_tag) for data slots
            det_words: List of (word, pos_tag) for determiner slots (phrase pattern only)

        Returns:
            A Sentence object
        """
        words = [""] * self.words_per_sentence
        data_indices = self.data_slot_indices()
        det_indices = self.determiner_slot_indices()

        if len(data_words) != len(data_indices):
            raise GrammarError(
                f"Expected {len(data_indices)} data words, got {len(data_words)}"
            )

        for idx, (word, _) in zip(data_indices, data_words):
            words[idx] = word

        if det_indices:
            if det_words is None or len(det_words) != len(det_indices):
                raise GrammarError(
                    f"Expected {len(det_indices)} determiner words for pattern '{self.pattern}'"
                )
            for idx, (word, _) in zip(det_indices, det_words):
                words[idx] = word

        return Sentence(
            pattern=self.pattern,
            words=words,
            slots=list(self.slots),
        )

    def parse_sentence(self, words: List[str]) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]]]:
        """Parse a word list into (data_pairs, det_pairs).

        Returns:
            data_pairs: List of (pos_tag, slot_index) for data slots
            det_pairs: List of (pos_tag, slot_index) for determiner slots
        """
        if len(words) != self.words_per_sentence:
            raise GrammarError(
                f"Pattern '{self.pattern}' expects {self.words_per_sentence} words, "
                f"got {len(words)}"
            )

        data_pairs = []
        det_pairs = []

        for i, (word, slot) in enumerate(zip(words, self.slots)):
            if slot == "determiner":
                det_pairs.append((slot, i))
            else:
                data_pairs.append((slot, i))

        return data_pairs, det_pairs

    def validate_structure(self, words: List[str], word_bank) -> List[str]:
        """Validate that words appear in their expected POS categories.

        Returns a list of error messages (empty if valid).
        """
        errors = []
        if len(words) != self.words_per_sentence:
            errors.append(
                f"Wrong word count: expected {self.words_per_sentence}, got {len(words)}"
            )
            return errors

        for i, (word, expected_pos) in enumerate(zip(words, self.slots)):
            actual_pos = word_bank.identify_category(word.lower())
            if actual_pos is None:
                errors.append(f"Word '{word}' at position {i} not found in any category")
            elif actual_pos != expected_pos:
                errors.append(
                    f"Word '{word}' at position {i}: expected {expected_pos}, "
                    f"found in {actual_pos} (possible corruption)"
                )
        return errors
