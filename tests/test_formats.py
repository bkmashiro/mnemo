"""Tests for the format-aware codec."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.formats import FormatCodec


class TestAutoDetection:
    """Test automatic format detection."""

    def setup_method(self):
        self.codec = FormatCodec(pattern="clause")

    def test_uuid_detection(self):
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        encoded, fmt = self.codec.encode_auto(uuid_str)
        assert fmt == "uuid"
        decoded, fmt2 = self.codec.decode_auto(encoded)
        assert fmt2 == "uuid"
        assert decoded == uuid_str

    def test_ipv4_detection(self):
        ip = "192.168.1.1"
        encoded, fmt = self.codec.encode_auto(ip)
        assert fmt == "ipv4"
        decoded, fmt2 = self.codec.decode_auto(encoded)
        assert fmt2 == "ipv4"
        assert decoded == ip

    def test_ipv4_edge_cases(self):
        for ip in ["0.0.0.0", "255.255.255.255", "10.0.0.1", "127.0.0.1"]:
            encoded, fmt = self.codec.encode_auto(ip)
            assert fmt == "ipv4"
            decoded, _ = self.codec.decode_auto(encoded)
            assert decoded == ip

    def test_sha1_detection(self):
        sha1 = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"
        encoded, fmt = self.codec.encode_auto(sha1)
        assert fmt == "sha1"
        decoded, fmt2 = self.codec.decode_auto(encoded)
        assert fmt2 == "sha1"
        assert decoded == sha1

    def test_sha256_detection(self):
        sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        encoded, fmt = self.codec.encode_auto(sha256)
        assert fmt == "sha256"
        decoded, fmt2 = self.codec.decode_auto(encoded)
        assert fmt2 == "sha256"
        assert decoded == sha256

    def test_hex_detection(self):
        hex_str = "0xdeadbeef"
        encoded, fmt = self.codec.encode_auto(hex_str)
        assert fmt == "hex"
        decoded, fmt2 = self.codec.decode_auto(encoded)
        assert fmt2 == "hex"
        assert decoded == "deadbeef"

    def test_utf8_fallback(self):
        text = "Hello, world!"
        encoded, fmt = self.codec.encode_auto(text)
        assert fmt == "utf8"
        decoded, fmt2 = self.codec.decode_auto(encoded)
        assert fmt2 == "utf8"
        assert decoded == text

    def test_numeric_string_as_utf8(self):
        """Pure digits without hex chars should be UTF-8."""
        text = "12345"
        encoded, fmt = self.codec.encode_auto(text)
        assert fmt == "utf8"
        decoded, _ = self.codec.decode_auto(encoded)
        assert decoded == text


class TestFormatRoundTrips:
    """Test round-trips with different patterns."""

    @pytest.mark.parametrize("pattern", ["clause", "phrase", "mini"])
    def test_uuid_all_patterns(self, pattern):
        codec = FormatCodec(pattern=pattern)
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        encoded, _ = codec.encode_auto(uuid_str)
        decoded, _ = codec.decode_auto(encoded)
        assert decoded == uuid_str

    @pytest.mark.parametrize("pattern", ["clause", "phrase", "mini"])
    def test_ipv4_all_patterns(self, pattern):
        codec = FormatCodec(pattern=pattern)
        ip = "192.168.1.1"
        encoded, _ = codec.encode_auto(ip)
        decoded, _ = codec.decode_auto(encoded)
        assert decoded == ip

    @pytest.mark.parametrize("pattern", ["clause", "phrase", "mini"])
    def test_utf8_all_patterns(self, pattern):
        codec = FormatCodec(pattern=pattern)
        text = "The quick brown fox"
        encoded, _ = codec.encode_auto(text)
        decoded, _ = codec.decode_auto(encoded)
        assert decoded == text


class TestIPv6:
    """Test IPv6 encoding."""

    def setup_method(self):
        self.codec = FormatCodec(pattern="clause")

    def test_ipv6_full(self):
        ip = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        encoded, fmt = self.codec.encode_auto(ip)
        assert fmt == "ipv6"
        decoded, fmt2 = self.codec.decode_auto(encoded)
        assert fmt2 == "ipv6"
        # IPv6 normalizes, so compare as addresses
        import ipaddress
        assert ipaddress.IPv6Address(decoded) == ipaddress.IPv6Address(ip)

    def test_ipv6_loopback(self):
        ip = "::1"
        encoded, fmt = self.codec.encode_auto(ip)
        assert fmt == "ipv6"
        decoded, _ = self.codec.decode_auto(encoded)
        import ipaddress
        assert ipaddress.IPv6Address(decoded) == ipaddress.IPv6Address(ip)
