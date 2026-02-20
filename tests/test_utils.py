import pytest

from app.utils import generate_short_code, hash_ip, generate_qr_code_bytes, generate_qr_code_base64, build_short_url


def test_generate_short_code_default_length():
    code = generate_short_code()
    assert len(code) == 8
    assert code.isalnum()


def test_generate_short_code_custom_length():
    code = generate_short_code(length=12)
    assert len(code) == 12


def test_generate_short_code_uniqueness():
    codes = {generate_short_code() for _ in range(100)}
    assert len(codes) == 100  # All unique (statistically guaranteed for 62^8)


def test_hash_ip():
    h = hash_ip("127.0.0.1")
    assert len(h) == 64  # SHA-256 hex
    assert h == hash_ip("127.0.0.1")  # Deterministic
    assert h != hash_ip("192.168.1.1")


def test_generate_qr_code_bytes():
    data = generate_qr_code_bytes("https://example.com")
    assert isinstance(data, bytes)
    assert data[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic bytes


def test_generate_qr_code_base64():
    b64 = generate_qr_code_base64("https://example.com")
    assert isinstance(b64, str)
    assert len(b64) > 0


def test_build_short_url():
    url = build_short_url("abc123")
    assert url.endswith("/abc123")
