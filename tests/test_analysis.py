"""Tests for the analysis module."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.codec import encode
from src.analysis import (
    word_frequency_profile,
    uniqueness_score,
    error_detection_capability,
    hamming_distance_words,
    diff_encodings,
    encoding_entropy,
)


class TestWordFrequency:
    def test_basic(self):
        text = "Brave fox chase. Brave owl guard."
        freq = word_frequency_profile(text)
        assert freq["brave"] == 2

    def test_empty(self):
        assert word_frequency_profile("") == {}


class TestUniqueness:
    def test_all_unique(self):
        text = "alpha beta gamma delta epsilon."
        score = uniqueness_score(text)
        assert score == 1.0

    def test_all_same(self):
        text = "word word word word."
        score = uniqueness_score(text)
        assert score == 0.25

    def test_empty(self):
        assert uniqueness_score("") == 0.0


class TestErrorDetection:
    def test_clause_properties(self):
        info = error_detection_capability("clause")
        assert info["data_slots"] == 5
        assert info["checksum_slots"] == 0
        assert "100%" in info["slot_swap_detection"]

    def test_phrase_properties(self):
        info = error_detection_capability("phrase")
        assert info["data_slots"] == 5
        assert info["checksum_slots"] == 2
        assert "checksum" in info["wrong_word_same_slot"]


class TestHammingDistance:
    def test_identical(self):
        text = "Brave fox chase calm owl."
        assert hamming_distance_words(text, text) == 0

    def test_one_diff(self):
        t1 = "Brave fox chase calm owl."
        t2 = "Brave fox guard calm owl."
        assert hamming_distance_words(t1, t2) == 1

    def test_different_lengths(self):
        t1 = "Brave fox chase."
        t2 = "Brave fox chase calm owl."
        assert hamming_distance_words(t1, t2) == 2


class TestDiffEncodings:
    def test_no_diff(self):
        text = "Brave fox chase calm owl."
        assert diff_encodings(text, text) == []

    def test_one_change(self):
        t1 = "Brave fox chase calm owl."
        t2 = "Brave fox guard calm owl."
        diffs = diff_encodings(t1, t2)
        assert len(diffs) == 1
        assert diffs[0] == (2, "chase", "guard")


class TestEntropy:
    def test_high_entropy(self):
        # Encode enough data to get many distinct words
        data = bytes(range(256))
        text = encode(data, "clause")
        ent = encoding_entropy(text)
        # With 256 different bytes, entropy should be relatively high
        assert ent > 3.0

    def test_low_entropy(self):
        data = b"\x00" * 50
        text = encode(data, "clause")
        ent = encoding_entropy(text)
        # Repeated data = lower entropy
        assert ent < 5.0

    def test_empty(self):
        assert encoding_entropy("") == 0.0
