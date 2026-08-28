import pytest
from tools.tts_streaming import resolve_streaming_provider, NemotronVoiceStreamer


def test_nemotron_voice_streamer_available(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-testkey-12345")
    assert NemotronVoiceStreamer.available() is True


def test_resolve_streaming_provider_nemotron(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-testkey-12345")
    tts_config = {"provider": "nemotron", "nemotron": {"voice": "English-US.Female-1"}}
    streamer = resolve_streaming_provider(tts_config)
    assert streamer is not None
    assert isinstance(streamer, NemotronVoiceStreamer)
    assert streamer.sample_rate == 24000
