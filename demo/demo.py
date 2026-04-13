#!/usr/bin/env python3
"""Interactive demo of mnemo — grammatical mnemonic encoding.

Run: python3 demo/demo.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.codec import encode, decode, encode_hex, decode_hex, describe_encoding
from src.formats import FormatCodec
from src.analysis import (
    uniqueness_score,
    error_detection_capability,
    hamming_distance_words,
    diff_encodings,
    encoding_entropy,
)


def section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def demo_basic_encoding():
    section("1. Basic Encoding: Text to Mnemonics")

    text = "hello"
    data = text.encode("utf-8")

    for pattern in ["clause", "phrase", "mini"]:
        encoded = encode(data, pattern)
        decoded = decode(encoded, pattern)
        info = describe_encoding(data, pattern)
        print(f"  Pattern: {pattern}")
        print(f"  Input:   '{text}' ({len(data)} bytes)")
        print(f"  Encoded: {encoded}")
        print(f"  Words:   {info['words']} ({info['words_per_sentence']}/sentence)")
        print(f"  Decoded: {decoded.decode('utf-8')}")
        print()


def demo_git_hash():
    section("2. Git Commit Hash Encoding")

    git_hash = "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"
    print(f"  SHA-1:    {git_hash}")
    print()

    for pattern in ["clause", "mini"]:
        encoded = encode_hex(git_hash, pattern)
        decoded = decode_hex(encoded, pattern)
        info = describe_encoding(bytes.fromhex(git_hash), pattern)
        print(f"  [{pattern}] {encoded}")
        print(f"  Sentences: {info['sentences']}, Words: {info['words']}")
        print(f"  Verified:  {decoded == git_hash}")
        print()


def demo_uuid():
    section("3. UUID Encoding")

    codec = FormatCodec(pattern="clause")
    uuid_str = "550e8400-e29b-41d4-a716-446655440000"

    encoded, fmt = codec.encode_auto(uuid_str)
    decoded, _ = codec.decode_auto(encoded)

    print(f"  UUID:     {uuid_str}")
    print(f"  Detected: {fmt}")
    print(f"  Encoded:  {encoded}")
    print(f"  Decoded:  {decoded}")
    print(f"  Match:    {decoded == uuid_str}")


def demo_ip_addresses():
    section("4. IP Address Encoding")

    codec = FormatCodec(pattern="clause")

    for ip in ["192.168.1.1", "10.0.0.1", "2001:db8::1"]:
        encoded, fmt = codec.encode_auto(ip)
        decoded, _ = codec.decode_auto(encoded)
        print(f"  {ip}")
        print(f"    Format:  {fmt}")
        print(f"    Encoded: {encoded}")
        print(f"    Decoded: {decoded}")
        print()


def demo_error_detection():
    section("5. Error Detection")

    data = b"secure"
    encoded = encode(data, "clause")
    print(f"  Original: {encoded}")
    print()

    # Show what happens with wrong word count
    print("  Swap two words (noun <-> adjective):")
    words = encoded.split(".")[0].strip().split()
    words[0], words[1] = words[1], words[0]
    corrupted = " ".join(words) + ". " + ".".join(encoded.split(".")[1:])
    try:
        decode(corrupted, "clause")
        print("    ERROR: corruption not detected!")
    except Exception as e:
        print(f"    Caught: {type(e).__name__}: {e}")
    print()

    # Phrase pattern checksum
    encoded_phrase = encode(data, "phrase")
    print(f"  Phrase pattern: {encoded_phrase}")

    # Corrupt a data word within its category
    from src.wordbank import WordBank
    bank = WordBank()
    sentences = encoded_phrase.split(".")
    sent_words = sentences[0].strip().split()
    # Find and replace the adjective at position 1
    adj_words = bank.words_for_category("adjective")
    orig = sent_words[1].lower()
    for w in adj_words:
        if w != orig:
            sent_words[1] = w.capitalize()
            break
    sentences[0] = " ".join(sent_words)
    corrupted_phrase = ".".join(sentences)
    print(f"  Corrupted: {corrupted_phrase}")
    try:
        decode(corrupted_phrase, "phrase")
        print("    ERROR: corruption not detected!")
    except Exception as e:
        print(f"    Caught: {type(e).__name__}: {e}")


def demo_comparison():
    section("6. Comparing Similar Data")

    data1 = b"\xde\xad\xbe\xef\x00"
    data2 = b"\xde\xad\xbe\xef\x01"  # Only last byte differs

    enc1 = encode(data1, "clause")
    enc2 = encode(data2, "clause")

    print(f"  Data 1: {data1.hex()} -> {enc1}")
    print(f"  Data 2: {data2.hex()} -> {enc2}")
    print(f"  Hamming distance: {hamming_distance_words(enc1, enc2)} words")
    print(f"  Differences:")
    for pos, w1, w2 in diff_encodings(enc1, enc2):
        print(f"    Position {pos}: '{w1}' -> '{w2}'")


def demo_analysis():
    section("7. Encoding Analysis")

    # Random-ish data
    data = bytes(range(50))
    encoded = encode(data, "clause")

    info = describe_encoding(data, "clause")
    print(f"  Input:         {len(data)} bytes")
    print(f"  Sentences:     {info['sentences']}")
    print(f"  Total words:   {info['words']}")
    print(f"  Uniqueness:    {uniqueness_score(encoded):.2%}")
    print(f"  Entropy:       {encoding_entropy(encoded):.2f} bits/word")
    print(f"  Padding:       {info['padding_bytes']} bytes")
    print()

    # Error detection properties
    for pattern in ["clause", "phrase", "mini"]:
        props = error_detection_capability(pattern)
        print(f"  [{pattern}] {props['data_slots']} data + "
              f"{props['checksum_slots']} checksum slots")
        print(f"    Slot swap detection:    {props['slot_swap_detection']}")
        print(f"    Same-slot corruption:   {props['wrong_word_same_slot']}")


def demo_auto_detect():
    section("8. Auto-Detection")

    codec = FormatCodec()
    test_values = [
        "192.168.0.1",
        "550e8400-e29b-41d4-a716-446655440000",
        "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
        "0xdeadbeef",
        "Hello, World!",
    ]

    for val in test_values:
        encoded, fmt = codec.encode_auto(val)
        decoded, _ = codec.decode_auto(encoded)
        words = sum(len(s.strip().split()) for s in encoded.split(".") if s.strip())
        print(f"  {val}")
        print(f"    -> [{fmt}] {words} words: {encoded[:70]}{'...' if len(encoded) > 70 else ''}")
        print()


if __name__ == "__main__":
    print()
    print("  MNEMO — Grammatical Mnemonic Encoding")
    print("  ======================================")
    print("  Turning binary data into memorable sentences")
    print()

    demo_basic_encoding()
    demo_git_hash()
    demo_uuid()
    demo_ip_addresses()
    demo_error_detection()
    demo_comparison()
    demo_analysis()
    demo_auto_detect()

    section("Done!")
    print("  All demos completed successfully.")
    print()
