"""mnemo - Grammatical mnemonic encoding for binary data.

Converts arbitrary binary data into memorable English sentences
using linguistic grammar (adjective-noun-verb-adjective-noun)
with built-in error detection from grammatical structure.
"""

from .codec import encode, decode, encode_hex, decode_hex
from .wordbank import WordBank
from .grammar import Grammar, GrammarError

__version__ = "1.0.0"
__all__ = [
    "encode",
    "decode",
    "encode_hex",
    "decode_hex",
    "WordBank",
    "Grammar",
    "GrammarError",
]
