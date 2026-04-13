"""Tests for the WordBank module."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.wordbank import WordBank, _seed_shuffle, SEEDS


class TestWordBank:
    """Test word bank construction and properties."""

    def setup_method(self):
        self.bank = WordBank()

    def test_all_categories_have_256_words(self):
        for cat in self.bank.CATEGORIES:
            words = self.bank.words_for_category(cat)
            assert len(words) == 256, f"{cat} has {len(words)} words, expected 256"

    def test_categories_are_disjoint(self):
        """Words must not appear in multiple categories (critical for error detection)."""
        all_words = {}
        for cat in self.bank.CATEGORIES:
            for word in self.bank.words_for_category(cat):
                if word in all_words:
                    pytest.fail(
                        f"Word '{word}' appears in both '{all_words[word]}' and '{cat}'"
                    )
                all_words[word] = cat

    def test_no_duplicates_within_category(self):
        for cat in self.bank.CATEGORIES:
            words = self.bank.words_for_category(cat)
            assert len(set(words)) == len(words), f"Duplicates in {cat}"

    def test_encode_byte_range(self):
        for cat in self.bank.CATEGORIES:
            for i in range(256):
                word = self.bank.encode_byte(cat, i)
                assert isinstance(word, str)
                assert len(word) > 0

    def test_decode_word_round_trip(self):
        for cat in self.bank.CATEGORIES:
            for i in range(256):
                word = self.bank.encode_byte(cat, i)
                byte_val = self.bank.decode_word(cat, word)
                assert byte_val == i, f"{cat}[{i}] -> '{word}' -> {byte_val}"

    def test_decode_unknown_word(self):
        result = self.bank.decode_word("adjective", "xyzzyplugh")
        assert result == -1

    def test_identify_category(self):
        for cat in self.bank.CATEGORIES:
            word = self.bank.encode_byte(cat, 42)
            assert self.bank.identify_category(word) == cat

    def test_identify_unknown_word(self):
        assert self.bank.identify_category("xyzzyplugh") is None

    def test_encode_byte_out_of_range(self):
        with pytest.raises(ValueError):
            self.bank.encode_byte("adjective", 256)
        with pytest.raises(ValueError):
            self.bank.encode_byte("adjective", -1)

    def test_encode_byte_bad_category(self):
        with pytest.raises(ValueError):
            self.bank.encode_byte("pronoun", 0)

    def test_all_words_lowercase(self):
        for cat in self.bank.CATEGORIES:
            for word in self.bank.words_for_category(cat):
                assert word == word.lower(), f"Word '{word}' in {cat} is not lowercase"

    def test_deterministic_shuffle(self):
        """Shuffle must be deterministic across runs."""
        words = ["alpha", "beta", "gamma", "delta", "epsilon"]
        result1 = _seed_shuffle(words, "test")
        result2 = _seed_shuffle(words, "test")
        assert result1 == result2

    def test_different_salt_different_shuffle(self):
        words = ["alpha", "beta", "gamma", "delta", "epsilon"]
        result1 = _seed_shuffle(words, "salt_a")
        result2 = _seed_shuffle(words, "salt_b")
        assert result1 != result2


class TestWordBankConsistency:
    """Ensure word bank is identical across multiple instantiations."""

    def test_multiple_instances_identical(self):
        bank1 = WordBank()
        bank2 = WordBank()
        for cat in bank1.CATEGORIES:
            words1 = bank1.words_for_category(cat)
            words2 = bank2.words_for_category(cat)
            assert words1 == words2, f"Category {cat} differs between instances"
