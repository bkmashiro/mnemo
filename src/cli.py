#!/usr/bin/env python3
"""Command-line interface for mnemo.

Usage:
    mnemo encode <value> [--pattern=clause] [--format=auto]
    mnemo decode <text> [--pattern=clause]
    mnemo info <value> [--pattern=clause]
    mnemo verify <text> [--pattern=clause]
    mnemo wordlist [--category=all]
"""

from __future__ import annotations
import argparse
import sys
import json

from .codec import encode, decode, encode_hex, decode_hex, describe_encoding
from .formats import FormatCodec
from .grammar import GrammarError, PATTERNS
from .wordbank import WordBank


def cmd_encode(args):
    """Encode a value into mnemonic sentences."""
    codec = FormatCodec(pattern=args.pattern)

    if args.format == "auto":
        encoded, fmt = codec.encode_auto(args.value)
        if not args.quiet:
            print(f"[detected: {fmt}]", file=sys.stderr)
    elif args.format == "hex":
        encoded = encode_hex(args.value, args.pattern)
        fmt = "hex"
    elif args.format == "utf8":
        encoded = encode(args.value.encode("utf-8"), args.pattern)
        fmt = "utf8"
    elif args.format == "raw":
        # Read from stdin as bytes
        data = sys.stdin.buffer.read() if args.value == "-" else args.value.encode("latin-1")
        encoded = encode(data, args.pattern)
        fmt = "raw"
    else:
        print(f"Unknown format: {args.format}", file=sys.stderr)
        sys.exit(1)

    print(encoded)


def cmd_decode(args):
    """Decode mnemonic sentences back to the original value."""
    text = args.text

    # If text is "-", read from stdin
    if text == "-":
        text = sys.stdin.read().strip()

    try:
        if args.format == "auto":
            codec = FormatCodec(pattern=args.pattern)
            value, fmt = codec.decode_auto(text)
            if not args.quiet:
                print(f"[format: {fmt}]", file=sys.stderr)
            print(value)
        elif args.format == "hex":
            print(decode_hex(text, args.pattern))
        elif args.format == "utf8":
            data = decode(text, args.pattern)
            print(data.decode("utf-8"))
        else:
            data = decode(text, args.pattern)
            sys.stdout.buffer.write(data)
    except GrammarError as e:
        print(f"Decode error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_info(args):
    """Show encoding metadata for a value."""
    codec = FormatCodec(pattern=args.pattern)
    _, fmt = codec._detect_and_convert(args.value)

    if fmt in ("hex", "sha1", "sha256"):
        hex_str = args.value.replace("0x", "")
        if len(hex_str) % 2:
            hex_str = "0" + hex_str
        data = bytes.fromhex(hex_str)
    else:
        data = args.value.encode("utf-8")

    # Add format tag byte
    info = describe_encoding(bytes([FormatCodec.FORMAT_TAGS[fmt]]) + data, args.pattern)
    info["detected_format"] = fmt

    if args.json:
        print(json.dumps(info, indent=2))
    else:
        print(f"  Input format:       {fmt}")
        print(f"  Input bytes:        {info['input_bytes']}")
        print(f"  Pattern:            {info['pattern']}")
        print(f"  Sentences:          {info['sentences']}")
        print(f"  Total words:        {info['words']}")
        print(f"  Bytes/sentence:     {info['bytes_per_sentence']}")
        print(f"  Words/sentence:     {info['words_per_sentence']}")
        print(f"  Padding bytes:      {info['padding_bytes']}")
        print(f"  Checksum:           {'yes' if info['has_checksums'] else 'no'}")
        print(f"  Words/input byte:   {info['overhead_ratio']:.2f}")


def cmd_verify(args):
    """Verify that mnemonic text is structurally valid and decodes correctly."""
    text = args.text
    if text == "-":
        text = sys.stdin.read().strip()

    bank = WordBank()
    from .grammar import Grammar
    grammar = Grammar(args.pattern)

    sentences = [s.strip().rstrip(".").strip() for s in text.split(".") if s.strip()]

    all_ok = True
    for i, sent in enumerate(sentences):
        words = sent.lower().split()
        errors = grammar.validate_structure(words, bank)
        if errors:
            all_ok = False
            print(f"Sentence {i + 1}: INVALID")
            for err in errors:
                print(f"  - {err}")
        else:
            print(f"Sentence {i + 1}: OK ({len(words)} words)")

    # Try full decode
    try:
        codec = FormatCodec(pattern=args.pattern)
        value, fmt = codec.decode_auto(text)
        print(f"\nDecode: SUCCESS (format={fmt})")
        print(f"Value: {value}")
    except Exception as e:
        all_ok = False
        print(f"\nDecode: FAILED ({e})")

    sys.exit(0 if all_ok else 1)


def cmd_wordlist(args):
    """Print the word list for one or all categories."""
    bank = WordBank()
    categories = bank.CATEGORIES if args.category == "all" else [args.category]

    for cat in categories:
        if cat not in bank.CATEGORIES:
            print(f"Unknown category: {cat}", file=sys.stderr)
            sys.exit(1)
        words = bank.words_for_category(cat)
        print(f"=== {cat.upper()} ({len(words)} words) ===")
        for i, word in enumerate(words):
            print(f"  {i:3d}: {word}")
        print()


def main():
    parser = argparse.ArgumentParser(
        prog="mnemo",
        description="Grammatical mnemonic encoding for binary data",
    )
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress informational messages")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # encode
    p_enc = subparsers.add_parser("encode", help="Encode a value")
    p_enc.add_argument("value", help="Value to encode (or '-' for stdin)")
    p_enc.add_argument("--pattern", "-p", default="clause",
                        choices=list(PATTERNS.keys()))
    p_enc.add_argument("--format", "-f", default="auto",
                        choices=["auto", "hex", "utf8", "raw"])
    p_enc.set_defaults(func=cmd_encode)

    # decode
    p_dec = subparsers.add_parser("decode", help="Decode mnemonic text")
    p_dec.add_argument("text", help="Mnemonic text (or '-' for stdin)")
    p_dec.add_argument("--pattern", "-p", default="clause",
                        choices=list(PATTERNS.keys()))
    p_dec.add_argument("--format", "-f", default="auto",
                        choices=["auto", "hex", "utf8", "raw"])
    p_dec.set_defaults(func=cmd_decode)

    # info
    p_info = subparsers.add_parser("info", help="Show encoding info")
    p_info.add_argument("value", help="Value to analyze")
    p_info.add_argument("--pattern", "-p", default="clause",
                        choices=list(PATTERNS.keys()))
    p_info.add_argument("--json", "-j", action="store_true")
    p_info.set_defaults(func=cmd_info)

    # verify
    p_ver = subparsers.add_parser("verify", help="Verify mnemonic text")
    p_ver.add_argument("text", help="Mnemonic text to verify (or '-' for stdin)")
    p_ver.add_argument("--pattern", "-p", default="clause",
                        choices=list(PATTERNS.keys()))
    p_ver.set_defaults(func=cmd_verify)

    # wordlist
    p_wl = subparsers.add_parser("wordlist", help="Print word lists")
    p_wl.add_argument("--category", "-c", default="all",
                       choices=["all"] + list(WordBank.CATEGORIES))
    p_wl.set_defaults(func=cmd_wordlist)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
