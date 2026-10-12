"""Unit tests for the Synthesia Interactive Avatar skill client."""

from __future__ import annotations

import io
import json
import sys
import urllib.error
from pathlib import Path
from unittest import mock

import pytest

SCRIPTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "creative"
    / "synthesia-avatar"
    / "scripts"
)
sys.path.insert(0, str(SCRIPTS_DIR))

import synthesia_client as sc


class DummyResponse:
    def __init__(self, data: dict, status: int = 200, headers: dict | None = None):
        self.data = data
        self.status = status
        self.headers = headers or {"Request-Id": "req_test123"}

    def read(self) -> bytes:
        return json.dumps(self.data).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def test_client_init_requires_key(monkeypatch):
    monkeypatch.delenv("SYNTHESIA_API_KEY", raising=False)
    monkeypatch.setattr(sc, "_load_env_key", lambda key: None)
    with pytest.raises(ValueError, match="SYNTHESIA_API_KEY is required"):
        sc.SynthesiaClient(api_key=None)


def test_client_init_with_key():
    client = sc.SynthesiaClient(api_key="test_key")
    assert client.api_key == "test_key"
    assert client.base_url == sc.DEFAULT_BASE_URL


def test_validate_key_success(monkeypatch):
    client = sc.SynthesiaClient(api_key="test_key")

    # Mock 400 validation error (authentication passed, but missing fields)
    err = urllib.error.HTTPError(
        url="https://developers.synthesia.io/api/interactive-avatars/sessions",
        code=400,
        msg="Bad Request",
        hdrs={"Request-Id": "req_val123"},
        fp=io.BytesIO(b'{"status": 400, "title": "Invalid request", "code": "validation_error", "detail": "body.avatarIds: Field required"}'),
    )
    monkeypatch.setattr(urllib.request, "urlopen", mock.Mock(side_effect=err))

    res = client.validate_key()
    assert res["valid"] is True
    assert res["request_id"] == "req_val123"


def test_validate_key_unauthorized(monkeypatch):
    client = sc.SynthesiaClient(api_key="bad_key")

    err = urllib.error.HTTPError(
        url="https://developers.synthesia.io/api/interactive-avatars/sessions",
        code=401,
        msg="Unauthorized",
        hdrs={},
        fp=io.BytesIO(b'{"status": 401, "title": "Unauthorized", "code": "unauthorized", "detail": "Invalid token"}'),
    )
    monkeypatch.setattr(urllib.request, "urlopen", mock.Mock(side_effect=err))

    res = client.validate_key()
    assert res["valid"] is False
    assert res["status"] == 401


def test_provision_avatar(monkeypatch):
    client = sc.SynthesiaClient(api_key="test_key")
    expected = {"id": "av_6c9edb85", "status": "queued", "done": False}

    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        mock.Mock(return_value=DummyResponse(expected, status=202)),
    )

    res = client.provision_avatar("av_6c9edb85", regenerate=False)
    assert res == expected


def test_get_avatar_status(monkeypatch):
    client = sc.SynthesiaClient(api_key="test_key")
    expected = {"id": "av_6c9edb85", "status": "completed", "done": True}

    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        mock.Mock(return_value=DummyResponse(expected, status=200)),
    )

    res = client.get_avatar_status("av_6c9edb85")
    assert res["status"] == "completed"
    assert res["done"] is True


def test_start_session(monkeypatch):
    client = sc.SynthesiaClient(api_key="test_key")
    expected = {"sessionId": "sess_987", "status": "connected"}

    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        mock.Mock(return_value=DummyResponse(expected, status=201)),
    )

    res = client.start_session(
        avatar_ids=["av_6c9edb85"],
        livekit_url="wss://livekit.example.com",
        livekit_token="token_abc",
    )
    assert res == expected


def test_cli_validate_key(monkeypatch, capsys):
    client_mock = mock.Mock()
    client_mock.validate_key.return_value = {"valid": True, "message": "OK"}
    monkeypatch.setattr(sc, "SynthesiaClient", lambda **kw: client_mock)

    ret = sc.main(["validate-key"])
    assert ret == 0
    captured = capsys.readouterr()
    assert '"valid": true' in captured.out


def test_cli_provision_avatar(monkeypatch, capsys):
    client_mock = mock.Mock()
    client_mock.provision_avatar.return_value = {"id": "av_123", "done": False}
    monkeypatch.setattr(sc, "SynthesiaClient", lambda **kw: client_mock)

    ret = sc.main(["provision-avatar", "--source-id", "av_123"])
    assert ret == 0
    client_mock.provision_avatar.assert_called_once_with("av_123", regenerate=False)
    captured = capsys.readouterr()
    assert '"id": "av_123"' in captured.out


def test_cli_avatar_status(monkeypatch, capsys):
    client_mock = mock.Mock()
    client_mock.get_avatar_status.return_value = {"id": "av_123", "status": "completed", "done": True}
    monkeypatch.setattr(sc, "SynthesiaClient", lambda **kw: client_mock)

    ret = sc.main(["avatar-status", "--source-id", "av_123"])
    assert ret == 0
    client_mock.get_avatar_status.assert_called_once_with("av_123")
    captured = capsys.readouterr()
    assert '"status": "completed"' in captured.out


def test_cli_start_session(monkeypatch, capsys):
    client_mock = mock.Mock()
    client_mock.start_session.return_value = {"sessionId": "s_1"}
    monkeypatch.setattr(sc, "SynthesiaClient", lambda **kw: client_mock)

    ret = sc.main([
        "start-session",
        "--avatar-id",
        "av_123",
        "--livekit-url",
        "wss://livekit.io",
        "--livekit-token",
        "tok_1",
    ])
    assert ret == 0
    client_mock.start_session.assert_called_once_with(
        avatar_ids=["av_123"],
        livekit_url="wss://livekit.io",
        livekit_token="tok_1",
    )
