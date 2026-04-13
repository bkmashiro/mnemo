"""Analysis utilities for mnemonic encodings.

Provides tools to analyze memorability, uniqueness, and error
detection properties of encoded mnemonics.
"""

from __future__ import annotations
from typing import Dict, List, Tuple
import hashlib

from .wordbank import WordBank
from .grammar import Grammar, PATTERNS


def word_frequency_profile(text: str) -> Dict[str, int]:
    """Count word frequencies in encoded text."""
    words = []
    for sent in text.split("."):
        words.extend(w.lower().strip() for w in sent.split() if w.strip())
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    return dict(sorted(freq.items(), key=lambda x: -x[1]))


def uniqueness_score(text: str) -> float:
    """Ratio of unique words to total words (1.0 = all unique)."""
    words = []
    for sent in text.split("."):
        words.extend(w.lower().strip() for w in sent.split() if w.strip())
    if not words:
        return 0.0
    return len(set(words)) / len(words)


def error_detection_capability(pattern: str) -> Dict[str, any]:
    """Describe the error detection properties of a pattern."""
    grammar = Grammar(pattern)
    total_slots = grammar.words_per_sentence
    data_slots = len(grammar.data_slot_indices())
    det_slots = len(grammar.determiner_slot_indices())

    # Each word must belong to its expected POS category.
    # If a word is swapped into the wrong slot, it'll be in the wrong category.
    # With 4 categories and 256 words each, the chance of a random word
    # passing the category check for a wrong slot is:
    # (words in target category that also appear in source category) / 256
    # Since categories are disjoint by construction, this is 0.

    # For within-category corruption (wrong word, right slot):
    # phrase pattern catches this via checksum determiners
    # clause/mini patterns don't catch within-category errors

    return {
        "pattern": pattern,
        "total_slots": total_slots,
        "data_slots": data_slots,
        "checksum_slots": det_slots,
        "slot_swap_detection": "100% (categories are disjoint)",
        "wrong_word_same_slot": (
            "detected via checksum" if det_slots > 0
            else "not detected (use 'phrase' pattern for checksums)"
        ),
        "missing_word_detection": "100% (word count mismatch)",
        "extra_word_detection": "100% (word count mismatch)",
        "category_confusion_rate": "0% (disjoint word sets)",
    }


def hamming_distance_words(text1: str, text2: str) -> int:
    """Count how many word positions differ between two encodings."""
    words1 = [w.lower().strip() for s in text1.split(".") for w in s.split() if w.strip()]
    words2 = [w.lower().strip() for s in text2.split(".") for w in s.split() if w.strip()]

    max_len = max(len(words1), len(words2))
    distance = abs(len(words1) - len(words2))

    for i in range(min(len(words1), len(words2))):
        if words1[i] != words2[i]:
            distance += 1

    return distance


def diff_encodings(text1: str, text2: str) -> List[Tuple[int, str, str]]:
    """Show word-by-word differences between two encodings.

    Returns list of (position, word1, word2) for differing positions.
    """
    words1 = [w.lower().strip() for s in text1.split(".") for w in s.split() if w.strip()]
    words2 = [w.lower().strip() for s in text2.split(".") for w in s.split() if w.strip()]

    diffs = []
    max_len = max(len(words1), len(words2))
    for i in range(max_len):
        w1 = words1[i] if i < len(words1) else "<missing>"
        w2 = words2[i] if i < len(words2) else "<missing>"
        if w1 != w2:
            diffs.append((i, w1, w2))

    return diffs


def encoding_entropy(text: str) -> float:
    """Estimate the bits of entropy per word in an encoding.

    For a perfectly random encoding with 256 words per category,
    each word carries 8 bits (log2(256)) of entropy.
    """
    import math
    words = [w.lower().strip() for s in text.split(".") for w in s.split() if w.strip()]
    if not words:
        return 0.0

    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1

    total = len(words)
    entropy = 0.0
    for count in freq.values():
        p = count / total
        entropy -= p * math.log2(p)

    return entropy
