"""Tests for FernetEncryption and API-key hashing."""

import pytest
from cryptography.fernet import Fernet

from app.core.security import FernetEncryption, generate_api_key, hash_api_key, verify_api_key


# ---------------------------------------------------------------------------
# FernetEncryption
# ---------------------------------------------------------------------------

class TestFernetEncryption:
    """Round-trip and error-case tests for FernetEncryption."""

    def test_encrypt_returns_string(self):
        enc = FernetEncryption()
        ciphertext = enc.encrypt("sk-my-secret-key-12345")
        assert isinstance(ciphertext, str)
        assert len(ciphertext) > 0

    def test_encrypt_decrypt_roundtrip(self):
        enc = FernetEncryption()
        plaintext = "sk-openai-super-secret-key-abc123"
        ciphertext = enc.encrypt(plaintext)
        recovered = enc.decrypt(ciphertext)
        assert recovered == plaintext

    def test_ciphertext_differs_from_plaintext(self):
        enc = FernetEncryption()
        plaintext = "my-secret"
        ciphertext = enc.encrypt(plaintext)
        assert ciphertext != plaintext

    def test_two_encryptions_of_same_plaintext_differ(self):
        """Fernet uses a random IV — same input should produce different ciphertext."""
        enc = FernetEncryption()
        plaintext = "same-value"
        c1 = enc.encrypt(plaintext)
        c2 = enc.encrypt(plaintext)
        assert c1 != c2  # Different nonces each time

    def test_decrypt_corrupted_ciphertext_raises(self):
        enc = FernetEncryption()
        with pytest.raises(ValueError, match="Failed to decrypt"):
            enc.decrypt("this-is-not-valid-ciphertext")

    def test_decrypt_plaintext_raises(self):
        enc = FernetEncryption()
        with pytest.raises(ValueError):
            enc.decrypt("sk-openai-super-secret-key-abc123")

    def test_empty_string_roundtrip(self):
        enc = FernetEncryption()
        ciphertext = enc.encrypt("")
        assert enc.decrypt(ciphertext) == ""

    def test_unicode_roundtrip(self):
        enc = FernetEncryption()
        plaintext = "日本語テスト🔑"
        assert enc.decrypt(enc.encrypt(plaintext)) == plaintext


# ---------------------------------------------------------------------------
# API Key hashing
# ---------------------------------------------------------------------------

class TestApiKeyHashing:
    def test_hash_produces_hex_string(self):
        h = hash_api_key("my-dashboard-key")
        assert isinstance(h, str)
        assert all(c in "0123456789abcdef" for c in h)

    def test_same_key_same_hash(self):
        h1 = hash_api_key("same-key")
        h2 = hash_api_key("same-key")
        assert h1 == h2

    def test_different_keys_different_hashes(self):
        h1 = hash_api_key("key-one")
        h2 = hash_api_key("key-two")
        assert h1 != h2

    def test_verify_correct_key(self):
        raw = "my-api-key"
        stored_hash = hash_api_key(raw)
        assert verify_api_key(raw, stored_hash) is True

    def test_verify_wrong_key(self):
        stored_hash = hash_api_key("correct-key")
        assert verify_api_key("wrong-key", stored_hash) is False


# ---------------------------------------------------------------------------
# Key generation
# ---------------------------------------------------------------------------

class TestGenerateApiKey:
    def test_generates_string(self):
        key = generate_api_key()
        assert isinstance(key, str)

    def test_default_prefix(self):
        key = generate_api_key()
        assert key.startswith("sk_")

    def test_custom_prefix(self):
        key = generate_api_key(prefix="dash")
        assert key.startswith("dash_")

    def test_keys_are_unique(self):
        keys = {generate_api_key() for _ in range(100)}
        assert len(keys) == 100
