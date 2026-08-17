from autoedit.security import create_session_token, read_session_token, encrypt_secret, decrypt_secret


def test_session_roundtrip():
    token = create_session_token("user-123")
    assert read_session_token(token) == "user-123"


def test_encrypt_roundtrip():
    secret = "ya29.access-token"
    assert decrypt_secret(encrypt_secret(secret)) == secret
