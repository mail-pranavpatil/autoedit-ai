from autoedit.security import encrypt_secret, decrypt_secret


def test_encrypt_roundtrip():
    secret = "ya29.access-token"
    assert decrypt_secret(encrypt_secret(secret)) == secret
