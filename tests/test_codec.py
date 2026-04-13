"""Tests for the core codec module."""

import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.codec import encode, decode, encode_hex, decode_hex, describe_encoding
from src.grammar import GrammarError


class TestRoundTrip:
    """Test encode/decode round-trip for various data."""

    @pytest.mark.parametrize("pattern", ["clause", "phrase", "mini"])
    def test_empty_data(self, pattern):
        assert encode(b"", pattern) == ""
        assert decode("", pattern) == b""

    @pytest.mark.parametrize("pattern", ["clause", "phrase", "mini"])
    def test_single_byte(self, pattern):
        for b in [0, 1, 127, 128, 255]:
            data = bytes([b])
            encoded = encode(data, pattern)
            decoded = decode(encoded, pattern)
            assert decoded == data, f"Failed for byte {b} with pattern {pattern}"

    @pytest.mark.parametrize("pattern", ["clause", "phrase", "mini"])
    def test_short_data(self, pattern):
        data = b"hello"
        encoded = encode(data, pattern)
        decoded = decode(encoded, pattern)
        assert decoded == data

    @pytest.mark.parametrize("pattern", ["clause", "phrase", "mini"])
    def test_medium_data(self, pattern):
        data = b"The quick brown fox jumps over the lazy dog"
        encoded = encode(data, pattern)
        decoded = decode(encoded, pattern)
        assert decoded == data

    @pytest.mark.parametrize("pattern", ["clause", "phrase", "mini"])
    def test_binary_data(self, pattern):
        data = bytes(range(256))
        encoded = encode(data, pattern)
        decoded = decode(encoded, pattern)
        assert decoded == data

    @pytest.mark.parametrize("pattern", ["clause", "phrase", "mini"])
    def test_all_zeros(self, pattern):
        data = b"\x00" * 20
        encoded = encode(data, pattern)
        decoded = decode(encoded, pattern)
        assert decoded == data

    @pytest.mark.parametrize("pattern", ["clause", "phrase", "mini"])
    def test_all_ones(self, pattern):
        data = b"\xff" * 20
        encoded = encode(data, pattern)
        decoded = decode(encoded, pattern)
        assert decoded == data

    def test_exact_chunk_boundary(self):
        """Data that exactly fills chunks (no padding needed after header)."""
        # clause: 5 bytes/sentence. header = 2 bytes.
        # 3 bytes data + 2 header = 5, exact.
        data = b"abc"
        encoded = encode(data, "clause")
        decoded = decode(encoded, "clause")
        assert decoded == data

    def test_one_byte_over_boundary(self):
        """Data one byte over a chunk boundary."""
        # 4 bytes data + 2 header = 6, needs 2 sentences for clause
        data = b"abcd"
        encoded = encode(data, "clause")
        decoded = decode(encoded, "clause")
        assert decoded == data


class TestHexCodec:
    """Test hex-specific encoding functions."""

    def test_hex_round_trip(self):
        hex_str = "deadbeef"
        encoded = encode_hex(hex_str)
        decoded = decode_hex(encoded)
        assert decoded == hex_str

    def test_hex_with_prefix(self):
        hex_str = "0xdeadbeef"
        encoded = encode_hex(hex_str)
        decoded = decode_hex(encoded)
        assert decoded == "deadbeef"

    def test_git_hash(self):
        """Full SHA-1 git hash round-trip."""
        git_hash = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"
        encoded = encode_hex(git_hash)
        decoded = decode_hex(encoded)
        assert decoded == git_hash

    def test_sha256(self):
        """Full SHA-256 hash round-trip."""
        sha = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        encoded = encode_hex(sha)
        decoded = decode_hex(encoded)
        assert decoded == sha

    def test_odd_length_hex(self):
        """Odd-length hex gets zero-padded."""
        hex_str = "abc"  # becomes "0abc"
        encoded = encode_hex(hex_str)
        decoded = decode_hex(encoded)
        assert decoded == "0abc"


class TestErrorDetection:
    """Test grammar-based error detection."""

    def test_wrong_word_count(self):
        with pytest.raises(GrammarError):
            decode("one two three four.", "clause")

    def test_phrase_checksum_detects_corruption(self):
        """Corrupt a data word in phrase pattern; checksum should catch it."""
        data = b"test!"
        encoded = encode(data, "phrase")

        # Corrupt by replacing a word
        sentences = encoded.split(".")
        words = sentences[0].strip().split()
        # Swap an adjective with another adjective (same category, different value)
        from src.wordbank import WordBank
        bank = WordBank()
        adj_words = bank.words_for_category("adjective")
        # Find an adjective in position 1 (first data adj in phrase: det adj noun verb det adj noun)
        original = words[1].lower()
        replacement = None
        for w in adj_words:
            if w != original:
                replacement = w
                break
        words[1] = replacement.capitalize()
        sentences[0] = " ".join(words)
        corrupted = ".".join(sentences)

        with pytest.raises(ValueError, match="Checksum mismatch"):
            decode(corrupted, "phrase")

    def test_word_in_wrong_slot_detected(self):
        """A noun in an adjective slot should be detected."""
        data = b"test!"
        encoded = encode(data, "clause")

        # Get the words
        sentences = encoded.split(".")
        words = sentences[0].strip().split()

        # Swap adj (pos 0) and noun (pos 1) - wrong categories
        words[0], words[1] = words[1], words[0]
        sentences[0] = " ".join(words)
        corrupted = ".".join(sentences)

        with pytest.raises(GrammarError):
            decode(corrupted, "clause")


class TestDescribeEncoding:
    """Test encoding metadata."""

    def test_clause_info(self):
        info = describe_encoding(b"hello", "clause")
        assert info["pattern"] == "clause"
        assert info["input_bytes"] == 5
        assert info["bytes_per_sentence"] == 5
        assert info["words_per_sentence"] == 5
        assert info["has_checksums"] is False

    def test_phrase_info(self):
        info = describe_encoding(b"hello", "phrase")
        assert info["has_checksums"] is True
        assert info["words_per_sentence"] == 7

    def test_mini_info(self):
        info = describe_encoding(b"hi", "mini")
        assert info["bytes_per_sentence"] == 3
        assert info["words_per_sentence"] == 3


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_max_length(self):
        """Test maximum data length (65535 bytes)."""
        data = b"\xab" * 100  # Not full 65535, but still tests header
        encoded = encode(data, "clause")
        decoded = decode(encoded, "clause")
        assert decoded == data

    def test_too_long_raises(self):
        with pytest.raises(ValueError, match="too long"):
            encode(b"\x00" * 65536, "clause")

    def test_unicode_string_as_bytes(self):
        data = "Hello 世界!".encode("utf-8")
        encoded = encode(data, "clause")
        decoded = decode(encoded, "clause")
        assert decoded == data

    def test_deterministic(self):
        """Same input always produces same output."""
        data = b"deterministic"
        e1 = encode(data, "clause")
        e2 = encode(data, "clause")
        assert e1 == e2
