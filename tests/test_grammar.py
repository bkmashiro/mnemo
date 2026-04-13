"""Tests for the grammar module."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.grammar import Grammar, GrammarError, Sentence, PATTERNS
from src.wordbank import WordBank


class TestGrammar:
    """Test grammar pattern properties."""

    def test_all_patterns_valid(self):
        for name in PATTERNS:
            g = Grammar(name)
            assert g.words_per_sentence > 0
            assert g.bytes_per_sentence > 0

    def test_invalid_pattern(self):
        with pytest.raises(ValueError):
            Grammar("nonexistent")

    def test_clause_structure(self):
        g = Grammar("clause")
        assert g.slots == ["adjective", "noun", "verb", "adjective", "noun"]
        assert g.bytes_per_sentence == 5
        assert g.words_per_sentence == 5

    def test_phrase_structure(self):
        g = Grammar("phrase")
        assert g.slots == ["determiner", "adjective", "noun", "verb",
                           "determiner", "adjective", "noun"]
        assert g.bytes_per_sentence == 5
        assert g.words_per_sentence == 7

    def test_mini_structure(self):
        g = Grammar("mini")
        assert g.slots == ["adjective", "noun", "verb"]
        assert g.bytes_per_sentence == 3
        assert g.words_per_sentence == 3

    def test_data_slot_indices_clause(self):
        g = Grammar("clause")
        assert g.data_slot_indices() == [0, 1, 2, 3, 4]

    def test_data_slot_indices_phrase(self):
        g = Grammar("phrase")
        assert g.data_slot_indices() == [1, 2, 3, 5, 6]

    def test_determiner_slot_indices_phrase(self):
        g = Grammar("phrase")
        assert g.determiner_slot_indices() == [0, 4]

    def test_determiner_slot_indices_clause(self):
        g = Grammar("clause")
        assert g.determiner_slot_indices() == []


class TestSentence:
    """Test Sentence data class."""

    def test_str(self):
        s = Sentence(pattern="test", words=["brave", "fox", "chase"], slots=["a", "n", "v"])
        assert str(s) == "brave fox chase"

    def test_display(self):
        s = Sentence(pattern="test", words=["brave", "fox", "chase"], slots=["a", "n", "v"])
        assert s.to_display() == "Brave fox chase."

    def test_empty(self):
        s = Sentence(pattern="test", words=[], slots=[])
        assert s.to_display() == ""


class TestValidation:
    """Test grammar validation."""

    def setup_method(self):
        self.bank = WordBank()
        self.grammar = Grammar("clause")

    def test_valid_sentence(self):
        # Get actual words from the bank
        words = [
            self.bank.encode_byte("adjective", 0),
            self.bank.encode_byte("noun", 0),
            self.bank.encode_byte("verb", 0),
            self.bank.encode_byte("adjective", 1),
            self.bank.encode_byte("noun", 1),
        ]
        errors = self.grammar.validate_structure(words, self.bank)
        assert errors == []

    def test_wrong_word_count(self):
        errors = self.grammar.validate_structure(["a", "b", "c"], self.bank)
        assert len(errors) > 0

    def test_word_in_wrong_category(self):
        # Put a noun where an adjective should be
        words = [
            self.bank.encode_byte("noun", 0),     # wrong! should be adjective
            self.bank.encode_byte("noun", 1),
            self.bank.encode_byte("verb", 0),
            self.bank.encode_byte("adjective", 1),
            self.bank.encode_byte("noun", 2),
        ]
        errors = self.grammar.validate_structure(words, self.bank)
        assert any("expected adjective" in e for e in errors)


class TestChecksums:
    """Test determiner checksum computation."""

    def test_deterministic(self):
        g = Grammar("phrase")
        d1 = g.compute_determiners([1, 2, 3, 4, 5])
        d2 = g.compute_determiners([1, 2, 3, 4, 5])
        assert d1 == d2

    def test_different_data_different_checksums(self):
        g = Grammar("phrase")
        d1 = g.compute_determiners([1, 2, 3, 4, 5])
        d2 = g.compute_determiners([5, 4, 3, 2, 1])
        assert d1 != d2

    def test_checksum_range(self):
        g = Grammar("phrase")
        d1, d2 = g.compute_determiners([0, 0, 0, 0, 0])
        assert 0 <= d1 <= 255
        assert 0 <= d2 <= 255
