import base64
import json

from autoedit.security import create_oauth_state, read_oauth_state


def test_state_carries_platform():
    assert read_oauth_state(create_oauth_state("ios"))["p"] == "ios"
    assert read_oauth_state(create_oauth_state())["p"] == "web"


def test_state_nonce_differs():
    assert create_oauth_state("web") != create_oauth_state("web")


def test_state_rejects_tamper():
    body, sig = create_oauth_state("web").split(".", 1)
    # broken signature
    assert read_oauth_state(f"{body}.{sig[:-1]}0") is None
    assert read_oauth_state("not-a-token") is None
    # forging platform=ios without re-signing must not verify
    forged = base64.urlsafe_b64encode(json.dumps({"p": "ios", "n": "x"}).encode()).decode()
    assert read_oauth_state(f"{forged}.{sig}") is None
