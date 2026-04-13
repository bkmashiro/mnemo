"""Format-aware encoding for common data types.

Provides convenient encode/decode for:
  - UUID (128-bit)
  - IPv4 address
  - IPv6 address
  - Git commit hash (SHA-1, 160-bit)
  - Arbitrary hex strings
  - Raw bytes / UTF-8 strings
"""

from __future__ import annotations
import re
import uuid
import ipaddress
import struct
from typing import Tuple

from .codec import encode, decode


class FormatCodec:
    """Encode and decode common data formats with automatic detection."""

    # Format tags prepended as a single byte to distinguish types on decode
    FORMAT_TAGS = {
        "raw":    0x00,
        "utf8":   0x01,
        "uuid":   0x02,
        "ipv4":   0x03,
        "ipv6":   0x04,
        "sha1":   0x05,
        "sha256": 0x06,
        "hex":    0x07,
    }
    TAG_TO_FORMAT = {v: k for k, v in FORMAT_TAGS.items()}

    def __init__(self, pattern: str = "clause"):
        self.pattern = pattern

    def encode_auto(self, value: str) -> Tuple[str, str]:
        """Auto-detect format and encode.

        Returns (encoded_text, detected_format).
        """
        fmt, data = self._detect_and_convert(value)
        tagged = bytes([self.FORMAT_TAGS[fmt]]) + data
        return encode(tagged, self.pattern), fmt

    def decode_auto(self, text: str) -> Tuple[str, str]:
        """Decode and return (value_string, format).

        Returns the value in its original string representation.
        """
        raw = decode(text, self.pattern)
        if not raw:
            return "", "raw"

        tag = raw[0]
        data = raw[1:]
        fmt = self.TAG_TO_FORMAT.get(tag, "raw")

        return self._convert_back(fmt, data), fmt

    def _detect_and_convert(self, value: str) -> Tuple[str, bytes]:
        """Detect the format of a string value and convert to bytes."""
        value = value.strip()

        # UUID: 8-4-4-4-12 hex with dashes
        uuid_re = re.compile(
            r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-'
            r'[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
        )
        if uuid_re.match(value):
            return "uuid", uuid.UUID(value).bytes

        # IPv4
        ipv4_re = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
        if ipv4_re.match(value):
            try:
                addr = ipaddress.IPv4Address(value)
                return "ipv4", addr.packed
            except ValueError:
                pass

        # IPv6
        if ":" in value and not value.startswith("0x"):
            try:
                addr = ipaddress.IPv6Address(value)
                return "ipv6", addr.packed
            except ValueError:
                pass

        # SHA-1 (40 hex chars)
        sha1_re = re.compile(r'^[0-9a-fA-F]{40}$')
        if sha1_re.match(value):
            return "sha1", bytes.fromhex(value)

        # SHA-256 (64 hex chars)
        sha256_re = re.compile(r'^[0-9a-fA-F]{64}$')
        if sha256_re.match(value):
            return "sha256", bytes.fromhex(value)

        # Generic hex (with 0x prefix or even-length hex)
        hex_re = re.compile(r'^(0x)?[0-9a-fA-F]+$')
        if hex_re.match(value):
            hex_str = value[2:] if value.startswith("0x") else value
            if len(hex_str) % 2:
                hex_str = "0" + hex_str
            # Only treat as hex if it looks hex-ish (has a-f chars or 0x prefix)
            if value.startswith("0x") or re.search(r'[a-fA-F]', value):
                return "hex", bytes.fromhex(hex_str)

        # Default: UTF-8 string
        return "utf8", value.encode("utf-8")

    def _convert_back(self, fmt: str, data: bytes) -> str:
        """Convert bytes back to the original string representation."""
        if fmt == "uuid":
            return str(uuid.UUID(bytes=data))
        elif fmt == "ipv4":
            return str(ipaddress.IPv4Address(data))
        elif fmt == "ipv6":
            return str(ipaddress.IPv6Address(data))
        elif fmt == "sha1":
            return data.hex()
        elif fmt == "sha256":
            return data.hex()
        elif fmt == "hex":
            return data.hex()
        elif fmt == "utf8":
            return data.decode("utf-8")
        else:
            return data.hex()
