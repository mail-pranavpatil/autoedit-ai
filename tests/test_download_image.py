import httpx
import pytest

from autoedit import drive
from autoedit.drive import ImageFetchError, _assert_public_host, download_image


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "169.254.169.254", "10.0.0.5", "::1"])
def test_assert_public_host_rejects_private(host):
    with pytest.raises(ImageFetchError):
        _assert_public_host(host)


def test_assert_public_host_allows_public(monkeypatch):
    monkeypatch.setattr(
        drive.socket, "getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 0))]
    )
    _assert_public_host("example.com")  # no raise


class _Stream:
    def __init__(self, *, ctype="image/jpeg", body=b"\xff\xd8\xff\xe0data", redirect=None):
        self.headers = {"content-type": ctype}
        if redirect:
            self.headers["location"] = redirect
        self.is_redirect = redirect is not None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def raise_for_status(self):
        pass

    def iter_bytes(self):
        yield b"\xff\xd8\xff\xe0data"


def _client_returning(stream):
    class _C:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def stream(self, method, url):
            return stream

    return _C


def test_rejects_non_image_content_type(monkeypatch, tmp_path):
    monkeypatch.setattr(
        drive.socket, "getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 0))]
    )
    monkeypatch.setattr(httpx, "Client", _client_returning(_Stream(ctype="text/html")))
    with pytest.raises(ImageFetchError):
        download_image("https://example.com/x", tmp_path / "x.jpg")


def test_rejects_private_host_before_any_request(monkeypatch, tmp_path):
    monkeypatch.setattr(
        httpx, "Client", _client_returning(_Stream())  # would succeed if reached
    )
    with pytest.raises(ImageFetchError):
        download_image("http://169.254.169.254/latest/meta-data", tmp_path / "x.jpg")


def test_rejects_non_http_scheme(tmp_path):
    with pytest.raises(ImageFetchError):
        download_image("file:///etc/passwd", tmp_path / "x.jpg")


def test_happy_path_probes_and_keeps_file(monkeypatch, tmp_path):
    monkeypatch.setattr(
        drive.socket, "getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 0))]
    )
    monkeypatch.setattr(httpx, "Client", _client_returning(_Stream()))
    monkeypatch.setattr(
        "autoedit.media.probe_media", lambda p: {"width": 1600, "height": 1200}
    )
    dest = tmp_path / "ok.jpg"
    download_image("https://example.com/ok.jpg", dest)
    assert dest.exists() and dest.read_bytes()


def test_small_image_rejected(monkeypatch, tmp_path):
    monkeypatch.setattr(
        drive.socket, "getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 0))]
    )
    monkeypatch.setattr(httpx, "Client", _client_returning(_Stream()))
    monkeypatch.setattr("autoedit.media.probe_media", lambda p: {"width": 120, "height": 90})
    dest = tmp_path / "small.jpg"
    with pytest.raises(ImageFetchError):
        download_image("https://example.com/small.jpg", dest)
    assert not dest.exists()
