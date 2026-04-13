# mnemo

**Grammatical mnemonic encoding for binary data.**

mnemo converts arbitrary binary data — git hashes, UUIDs, IP addresses, API keys, checksums — into memorable, grammatically-structured English sentences and back. Unlike flat word-list schemes (e.g., BIP39), mnemo uses linguistic grammar: adjective-noun-verb-adjective-noun sentences that read like surreal micro-stories.

```
deadbeef  ->  "Fluid rest quash honey helm. Starry hawk print fluid vine."

192.168.1.1  ->  "Fluid rest serve olive mesh. Coral ridge print fluid vine."

550e8400-e29b-41d4-a716-...  ->  "Fluid cloak voice glad gale. Young vine cycle twisty fog. ..."
```

## Why?

- **Verbal communication**: Read a git hash to someone over the phone
- **Human-readable checksums**: Verify file integrity by reading a sentence
- **Memorable keys**: Turn API tokens into something you can actually remember
- **Error detection**: Grammar structure catches corruption — a noun in an adjective slot signals tampering

## How It Works

Each sentence encodes a fixed number of bytes. Every word slot has a part-of-speech (adjective, noun, verb, determiner) mapped to a disjoint set of 256 words. Each word encodes exactly one byte (log2(256) = 8 bits).

### Sentence Patterns

| Pattern | Structure | Bytes/sentence | Words | Error detection |
|---------|-----------|----------------|-------|-----------------|
| `clause` | adj noun verb adj noun | 5 | 5 | Slot-swap (POS mismatch) |
| `phrase` | det adj noun verb det adj noun | 5 | 7 | Slot-swap + checksum determiners |
| `mini` | adj noun verb | 3 | 3 | Slot-swap (POS mismatch) |

The `phrase` pattern adds two determiner words that serve as checksums over the data bytes, catching within-category corruption.

### Disjoint Word Sets

The four POS categories (adjective, noun, verb, determiner) have completely disjoint word sets — no word appears in more than one category. This means if a word appears in the wrong grammatical slot during decoding, corruption is immediately detected.

### Auto-Detection

The format-aware codec automatically detects input types:
- **UUID**: `550e8400-e29b-41d4-...`
- **IPv4**: `192.168.1.1`
- **IPv6**: `2001:db8::1`
- **SHA-1**: 40-character hex
- **SHA-256**: 64-character hex
- **Hex**: `0x`-prefixed or hex with a-f characters
- **UTF-8**: Everything else

## Installation

No external dependencies. Python 3.10+.

```bash
git clone <repo> && cd mnemo
```

## Usage

### Python API

```python
from src import encode, decode, encode_hex, decode_hex
from src.formats import FormatCodec

# Basic encoding
encoded = encode(b"hello", pattern="clause")
# -> "Fluid rest graft feisty mane. Thorny spark print fluid vine."
decoded = decode(encoded, pattern="clause")
# -> b"hello"

# Hex data (git hashes, etc.)
encoded = encode_hex("deadbeef")
decoded = decode_hex(encoded)  # -> "deadbeef"

# Auto-detect format
codec = FormatCodec()
encoded, fmt = codec.encode_auto("192.168.1.1")  # fmt = "ipv4"
value, fmt = codec.decode_auto(encoded)  # -> ("192.168.1.1", "ipv4")

# With checksums (phrase pattern)
encoded = encode(b"secure", pattern="phrase")
decoded = decode(encoded, pattern="phrase")
```

### Command Line

```bash
# Encode
python3 -m src encode "Hello, World!"
python3 -m src encode "0xdeadbeef" --format hex
python3 -m src encode "192.168.1.1"

# Decode
python3 -m src decode "Fluid rest graft feisty mane. Thorny spark print fluid vine."

# Verify integrity
python3 -m src verify "Fluid rest graft feisty mane. Thorny spark print fluid vine."

# Show encoding metadata
python3 -m src info "deadbeef"

# Print word lists
python3 -m src wordlist --category noun
```

## Project Structure

```
mnemo/
  src/
    __init__.py      # Public API exports
    __main__.py      # CLI entry point
    wordbank.py      # 4x256 disjoint word sets with seed-based shuffling
    grammar.py       # Sentence patterns, validation, checksums
    codec.py         # Core encode/decode with length headers and padding
    formats.py       # Format-aware codec with auto-detection
    analysis.py      # Encoding analysis utilities
    cli.py           # Command-line interface
  tests/
    test_wordbank.py # Word bank disjointness, round-trips, determinism
    test_grammar.py  # Pattern validation, checksums, structure
    test_codec.py    # Encode/decode round-trips across all patterns
    test_formats.py  # Format detection and round-trips
    test_analysis.py # Analysis utility tests
  demo/
    demo.py          # Interactive demo showing all features
  README.md
```

## Running Tests

```bash
python3 -m pytest tests/ -v
```

## Running the Demo

```bash
python3 demo/demo.py
```

## Design Notes

### Seed Numbers

The word-to-byte mappings are deterministically derived from 16 seed numbers using SHA-256 hash chains. This ensures the mapping is reproducible across implementations while appearing random (no alphabetical ordering that might leak information about byte values).

### Length Header

All encoded data is prefixed with a 2-byte big-endian length header, allowing the decoder to strip padding from the final chunk. Maximum encodable data size: 65,535 bytes.

### Error Detection Layers

1. **Word count**: Wrong number of words per sentence
2. **POS mismatch**: Word found in wrong grammatical category (disjoint sets guarantee 100% detection)
3. **Checksum determiners** (phrase pattern): SHA-256-derived check bytes catch within-category word substitution
4. **Unknown word**: Word not in any category

### Encoding Efficiency

| Data type | Bytes | Pattern | Words | Words/byte |
|-----------|-------|---------|-------|------------|
| IPv4 | 4 | clause | 10 | 1.67 |
| UUID | 16 | clause | 20 | 1.18 |
| SHA-1 | 20 | clause | 25 | 1.18 |
| SHA-256 | 32 | clause | 40 | 1.18 |

The overhead converges to 1.0 words/byte for data larger than a few chunks, since the 2-byte length header is amortized.

## License

MIT
