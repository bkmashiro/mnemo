"""Core codec: encode bytes to sentences, decode sentences to bytes.

Supports three encoding patterns:
  - clause: 5 bytes per sentence (adj noun verb adj noun)
  - phrase: 5 bytes + 2 checksum bytes per sentence (det adj noun verb det adj noun)
  - mini:   3 bytes per sentence (adj noun verb)

The codec handles padding, chunking, and round-trip fidelity.
"""

from __future__ import annotations
import math
from typing import List, Optional, Tuple

from .wordbank import WordBank
from .grammar import Grammar, GrammarError, Sentence, PATTERNS


# Singleton word bank (built once, reused)
_BANK: Optional[WordBank] = None


def _get_bank() -> WordBank:
    global _BANK
    if _BANK is None:
        _BANK = WordBank()
    return _BANK


def _chunk(data: bytes, size: int) -> List[bytes]:
    """Split data into chunks of `size` bytes, zero-padding the last chunk."""
    chunks = []
    for i in range(0, len(data), size):
        chunk = data[i:i + size]
        if len(chunk) < size:
            chunk = chunk + b"\x00" * (size - len(chunk))
        chunks.append(chunk)
    return chunks


def encode(data: bytes, pattern: str = "clause") -> str:
    """Encode binary data into mnemonic sentences.

    Args:
        data: Arbitrary bytes to encode.
        pattern: Sentence pattern ("clause", "phrase", or "mini").

    Returns:
        A string of period-separated sentences.

    Example:
        >>> encode(b'\\xde\\xad\\xbe\\xef\\x42', pattern='clause')
        'Dusty foxes chase coral moons.'
    """
    if not data:
        return ""

    bank = _get_bank()
    grammar = Grammar(pattern)

    # Prepend a length header (2 bytes, big-endian) so we can strip padding on decode
    length = len(data)
    if length > 65535:
        raise ValueError(f"Data too long: {length} bytes (max 65535)")
    header = length.to_bytes(2, "big")
    payload = header + data

    chunks = _chunk(payload, grammar.bytes_per_sentence)
    sentences = []

    for chunk in chunks:
        data_indices = grammar.data_slot_indices()
        det_indices = grammar.determiner_slot_indices()

        # Map data bytes to words
        data_words = []
        for j, idx in enumerate(data_indices):
            byte_val = chunk[j]
            pos = grammar.slots[idx]
            word = bank.encode_byte(pos, byte_val)
            data_words.append((word, pos))

        # Compute and map checksum determiners (for phrase pattern)
        det_words = None
        if det_indices:
            det_values = grammar.compute_determiners(list(chunk))
            det_words = []
            for k, idx in enumerate(det_indices):
                word = bank.encode_byte("determiner", det_values[k])
                det_words.append((word, "determiner"))

        sentence = grammar.build_sentence(data_words, det_words)
        sentences.append(sentence.to_display())

    return " ".join(sentences)


def decode(text: str, pattern: str = "clause") -> bytes:
    """Decode mnemonic sentences back to binary data.

    Args:
        text: Encoded mnemonic string (period-separated sentences).
        pattern: The pattern used during encoding.

    Returns:
        The original binary data.

    Raises:
        GrammarError: If sentences don't match expected structure.
        ValueError: If checksum validation fails (phrase pattern).
    """
    if not text or not text.strip():
        return b""

    bank = _get_bank()
    grammar = Grammar(pattern)

    # Split into sentences (by period)
    raw_sentences = [s.strip().rstrip(".").strip() for s in text.split(".") if s.strip()]

    recovered = bytearray()

    for sent_text in raw_sentences:
        words = sent_text.lower().split()

        if len(words) != grammar.words_per_sentence:
            raise GrammarError(
                f"Sentence '{sent_text}' has {len(words)} words, "
                f"expected {grammar.words_per_sentence}"
            )

        # Validate grammar structure
        errors = grammar.validate_structure(words, bank)
        if errors:
            raise GrammarError(
                f"Grammar validation failed for '{sent_text}': {'; '.join(errors)}"
            )

        # Extract data bytes
        data_indices = grammar.data_slot_indices()
        det_indices = grammar.determiner_slot_indices()

        chunk_bytes = []
        for idx in data_indices:
            word = words[idx]
            pos = grammar.slots[idx]
            byte_val = bank.decode_word(pos, word)
            if byte_val < 0:
                raise GrammarError(f"Word '{word}' not found in {pos} category")
            chunk_bytes.append(byte_val)

        # Validate checksum determiners (phrase pattern)
        if det_indices:
            expected_dets = grammar.compute_determiners(chunk_bytes)
            for k, idx in enumerate(det_indices):
                word = words[idx]
                actual_val = bank.decode_word("determiner", word)
                if actual_val < 0:
                    raise GrammarError(f"Determiner '{word}' not found in determiner category")
                if actual_val != expected_dets[k]:
                    raise ValueError(
                        f"Checksum mismatch in sentence '{sent_text}': "
                        f"determiner '{word}' (byte {actual_val}) != expected {expected_dets[k]}. "
                        f"Data may be corrupted."
                    )

        recovered.extend(chunk_bytes)

    # Strip length header and padding
    if len(recovered) < 2:
        raise GrammarError("Decoded data too short to contain length header")

    original_length = int.from_bytes(recovered[:2], "big")
    data = bytes(recovered[2:2 + original_length])

    if len(data) != original_length:
        raise GrammarError(
            f"Length mismatch: header says {original_length} bytes, "
            f"but only {len(data)} bytes recovered"
        )

    return data


def encode_hex(hex_string: str, pattern: str = "clause") -> str:
    """Encode a hex string (e.g., a git hash) into mnemonic sentences.

    Args:
        hex_string: Hex-encoded data (with or without '0x' prefix).
        pattern: Sentence pattern to use.

    Returns:
        Mnemonic sentence string.
    """
    hex_string = hex_string.strip().lower()
    if hex_string.startswith("0x"):
        hex_string = hex_string[2:]
    # Pad to even length
    if len(hex_string) % 2:
        hex_string = "0" + hex_string
    data = bytes.fromhex(hex_string)
    return encode(data, pattern)


def decode_hex(text: str, pattern: str = "clause") -> str:
    """Decode mnemonic sentences back to a hex string.

    Args:
        text: Encoded mnemonic string.
        pattern: The pattern used during encoding.

    Returns:
        Hex-encoded string (lowercase, no prefix).
    """
    data = decode(text, pattern)
    return data.hex()


def describe_encoding(data: bytes, pattern: str = "clause") -> dict:
    """Return metadata about how data would be encoded.

    Useful for understanding encoding efficiency and structure.
    """
    grammar = Grammar(pattern)
    payload_len = len(data) + 2  # +2 for length header
    num_sentences = math.ceil(payload_len / grammar.bytes_per_sentence)
    total_words = num_sentences * grammar.words_per_sentence
    padding_bytes = (num_sentences * grammar.bytes_per_sentence) - payload_len

    return {
        "pattern": pattern,
        "input_bytes": len(data),
        "payload_bytes": payload_len,
        "sentences": num_sentences,
        "words": total_words,
        "bytes_per_sentence": grammar.bytes_per_sentence,
        "words_per_sentence": grammar.words_per_sentence,
        "padding_bytes": padding_bytes,
        "has_checksums": pattern == "phrase",
        "overhead_ratio": total_words / max(len(data), 1),
    }
