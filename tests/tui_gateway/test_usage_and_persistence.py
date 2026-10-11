"""tui_gateway.server — usage reporting, TTS streaming, clarify callbacks and persistence.

Split from test_tui_gateway_server.py; shared fixtures and helpers live
in tests/tui_gateway/_server_test_helpers.py.
"""

import os
import sys
import threading
import time
import types
import pytest
from tui_gateway import server

from tests.tui_gateway._server_test_helpers import (
    BRANCH_CODEX_MESSAGE_ITEMS,
    BRANCH_CODEX_REASONING_ITEMS,
    BRANCH_REASONING,
    BRANCH_REASONING_CONTENT,
    BRANCH_REASONING_DETAILS,
    _BareAgent,
    _ImmediateThread,
    _branch_history,
    _branched_assistant,
    _branched_marker,
    _capture_server_request,
    _fake_tts_modules,
    _neuter_agent_prewarm_timer,  # autouse
    _reap_leaked_notification_pollers,  # autouse
    _session,
)


def test_get_usage_perf_readouts_present():
    """cache_hit_pct / avg_latency_s / avg_tps mirror the classic CLI bar."""
    from collections import deque

    class _PerfAgent:
        model = "x"
        session_prompt_tokens = 27_873
        session_cache_read_tokens = 24_369
        _api_latency_history = deque([2.1, 4.3], maxlen=10)
        _api_output_history = deque([130, 190], maxlen=10)

    usage = server._get_usage(_PerfAgent())
    assert usage["cache_hit_pct"] == 87
    assert usage["avg_latency_s"] == 3.2
    assert usage["avg_tps"] == 50.0  # true throughput sum(out)/sum(lat), not mean of ratios


def test_get_usage_perf_readouts_omitted_without_data():
    """Zero cache reads / empty history omit the keys — never fabricate 0s."""

    class _ColdAgent:
        model = "x"
        session_prompt_tokens = 100
        session_cache_read_tokens = 0

    usage = server._get_usage(_ColdAgent())
    assert "cache_hit_pct" not in usage
    assert "avg_latency_s" not in usage
    assert "avg_tps" not in usage


def test_get_usage_perf_readouts_guard_negative_latency():
    """Odd provider timings (negative durations seen in logs) are dropped."""
    from collections import deque

    class _WeirdAgent:
        model = "x"
        _api_latency_history = deque([-0.8], maxlen=10)
        _api_output_history = deque([100], maxlen=10)

    usage = server._get_usage(_WeirdAgent())
    assert "avg_latency_s" not in usage
    assert "avg_tps" not in usage


def test_get_usage_includes_active_subagents(monkeypatch):
    import tools.async_delegation as ad_mod
    monkeypatch.setattr(ad_mod, "active_count", lambda: 4)
    usage = server._get_usage(_BareAgent())
    assert usage["active_subagents"] == 4


def test_get_usage_safe_when_active_count_raises(monkeypatch):
    """A raising active_count() must not break the usage payload."""
    import tools.async_delegation as ad_mod

    def _boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(ad_mod, "active_count", _boom)
    usage = server._get_usage(_BareAgent())
    # Field omitted, but the rest of the payload is intact.
    assert "active_subagents" not in usage
    assert usage["model"] == "x"


# ---------------------------------------------------------------------------
# _resolve_runtime_with_fallback — init-time provider fallback
# ---------------------------------------------------------------------------

class TestResolveRuntimeWithFallback:
    """Tests for _resolve_runtime_with_fallback(): init-time provider
    fallback when the primary provider raises AuthError."""

    def test_primary_success_returns_runtime(self, monkeypatch):
        """When primary resolve succeeds, return its result directly."""
        expected = {"provider": "openai", "api_key": "tok"}
        monkeypatch.setattr(
            "hermes_cli.runtime_provider.resolve_runtime_provider",
            lambda **kw: expected,
        )
        resolution = server._resolve_runtime_with_fallback(
            {"requested": "openai"}
        )
        assert resolution.runtime == expected
        assert resolution.selected_model is None
        assert resolution.used_fallback is False

    def test_auth_error_tries_fallback_chain(self, monkeypatch):
        """On AuthError from primary, walk fallback_providers chain."""
        from hermes_cli.auth import AuthError

        fallback_runtime = {"provider": "deepseek", "api_key": "fb-tok"}

        def fake_resolve(**kwargs):
            if kwargs.get("requested") == "openai-codex":
                raise AuthError("No Codex credentials stored")
            return fallback_runtime

        monkeypatch.setattr(
            "hermes_cli.runtime_provider.resolve_runtime_provider",
            fake_resolve,
        )
        monkeypatch.setattr(
            server,
            "_load_fallback_model",
            lambda: [{"provider": "deepseek", "model": "deepseek-v4-pro"}],
        )
        resolution = server._resolve_runtime_with_fallback(
            {"requested": "openai-codex"},
        )
        assert resolution.runtime == fallback_runtime
        assert resolution.selected_model == "deepseek-v4-pro"
        assert resolution.used_fallback is True


    def test_auth_error_skips_provider_only_fallback(self, monkeypatch):
        """Auth fallback requires one complete provider/model pair."""
        from hermes_cli.auth import AuthError

        requested = []
        fallback_runtime = {"provider": "openrouter", "api_key": "fb-tok"}

        def fake_resolve(**kwargs):
            requested.append(kwargs.get("requested"))
            if kwargs.get("requested") == "openai-codex":
                raise AuthError("No Codex credentials stored")
            return fallback_runtime

        monkeypatch.setattr(
            "hermes_cli.runtime_provider.resolve_runtime_provider",
            fake_resolve,
        )
        monkeypatch.setattr(
            server,
            "_load_fallback_model",
            lambda: [
                {"provider": "anthropic"},
                {"provider": "openrouter", "model": "z-ai/glm-5.2"},
            ],
        )

        resolution = server._resolve_runtime_with_fallback(
            {"requested": "openai-codex"}
        )

        assert requested == ["openai-codex", "openrouter"]
        assert resolution.runtime == fallback_runtime
        assert resolution.selected_model == "z-ai/glm-5.2"
        assert resolution.used_fallback is True

    def test_fallback_entry_key_env_resolves_api_key(self, monkeypatch):
        """A fallback entry naming its key via key_env passes the resolved
        env value as explicit_api_key (#43861, @VrtxOmega)."""
        from hermes_cli.auth import AuthError

        monkeypatch.setenv("FB_TEST_KEY", "env-resolved-key")
        captured = {}
        fallback_runtime = {"provider": "openrouter", "api_key": "x"}

        def fake_resolve(**kwargs):
            if kwargs.get("requested") == "openai-codex":
                raise AuthError("No Codex credentials stored")
            captured.update(kwargs)
            return fallback_runtime

        monkeypatch.setattr(
            "hermes_cli.runtime_provider.resolve_runtime_provider",
            fake_resolve,
        )
        monkeypatch.setattr(
            server,
            "_load_fallback_model",
            lambda: [
                {
                    "provider": "openrouter",
                    "model": "z-ai/glm-5.2",
                    "key_env": "FB_TEST_KEY",
                }
            ],
        )
        resolution = server._resolve_runtime_with_fallback(
            {"requested": "openai-codex"}
        )
        assert resolution.used_fallback is True
        assert captured.get("explicit_api_key") == "env-resolved-key"

    def test_auth_error_all_fallbacks_fail_raises(self, monkeypatch):
        """When all fallbacks also fail, re-raise the original AuthError."""
        from hermes_cli.auth import AuthError

        def fake_resolve(**kwargs):
            raise AuthError("No credentials for " + str(kwargs.get("requested")))

        monkeypatch.setattr(
            "hermes_cli.runtime_provider.resolve_runtime_provider",
            fake_resolve,
        )
        monkeypatch.setattr(
            server,
            "_load_fallback_model",
            lambda: [{"provider": "deepseek", "model": "deepseek-v4-pro"}],
        )
        import pytest

        with pytest.raises(AuthError, match="No credentials for openai-codex"):
            server._resolve_runtime_with_fallback(
                {"requested": "openai-codex"},
            )

    def test_auth_error_skips_non_dict_entries(self, monkeypatch):
        """Fallback chain entries that are not dicts are skipped."""
        from hermes_cli.auth import AuthError

        fallback_runtime = {"provider": "anthropic", "api_key": "ant-tok"}

        def fake_resolve(**kwargs):
            if kwargs.get("requested") == "openai-codex":
                raise AuthError("No Codex credentials stored")
            return fallback_runtime

        monkeypatch.setattr(
            "hermes_cli.runtime_provider.resolve_runtime_provider",
            fake_resolve,
        )
        monkeypatch.setattr(
            server,
            "_load_fallback_model",
            lambda: [
                "invalid-string-entry",
                {"provider": "anthropic", "model": "claude-sonnet-4-6"},
            ],
        )
        resolution = server._resolve_runtime_with_fallback(
            {"requested": "openai-codex"},
        )
        assert resolution.runtime == fallback_runtime
        assert resolution.selected_model == "claude-sonnet-4-6"
        assert resolution.used_fallback is True

    def test_make_agent_uses_fallback_on_auth_error(self, monkeypatch):
        """Integration: _make_agent falls back to configured fallback
        provider when the primary provider raises AuthError."""
        import types

        from hermes_cli.auth import AuthError

        captured = {}
        fallback_runtime = {
            "provider": "deepseek",
            "api_key": "fb-tok",
            "base_url": "https://fallback.invalid/v1",
        }

        def fake_resolve(**kwargs):
            if kwargs.get("requested") in (None, "openai-codex"):
                raise AuthError("No Codex credentials stored")
            return fallback_runtime

        def fake_agent(**kwargs):
            captured.update(kwargs)
            return types.SimpleNamespace(model=kwargs.get("model"))

        monkeypatch.delenv("HERMES_MODEL", raising=False)
        monkeypatch.delenv("HERMES_INFERENCE_MODEL", raising=False)
        monkeypatch.delenv("HERMES_TUI_PROVIDER", raising=False)
        monkeypatch.setattr(
            server,
            "_load_cfg",
            lambda: {
                "model": {"default": "gpt-5.5", "provider": "openai-codex"},
                "fallback_providers": [
                    {"provider": "deepseek", "model": "deepseek-v4-pro"},
                ],
            },
        )
        monkeypatch.setattr(
            "hermes_cli.runtime_provider.resolve_runtime_provider",
            fake_resolve,
        )
        monkeypatch.setattr("run_agent.AIAgent", fake_agent)
        monkeypatch.setattr(server, "_load_enabled_toolsets", lambda *_a, **_kw: ["file"])
        monkeypatch.setattr(server, "_get_db", lambda: None)

        agent = server._make_agent(
            "sid",
            "session-key",
            model_override={
                "model": "gpt-5.5",
                "provider": "openai-codex",
                "base_url": "https://chatgpt.com/backend-api/codex",
                "api_key": "stale-codex-token",
            },
        )

        assert agent.model == "deepseek-v4-pro"
        assert captured["provider"] == "deepseek"
        assert captured["base_url"] == "https://fallback.invalid/v1"
        assert captured["api_key"] == "fb-tok"


def test_get_usage_does_not_substitute_cumulative_total_for_context_used():
    """An external context engine that does not report last_prompt_tokens must
    not have the cumulative lifetime session_total_tokens shown as its current
    context occupancy — that substitution produced impossible 1.9m/120k (100%)
    status-bar readings (#50421). With no real current occupancy known,
    context_used/percent stay unset rather than wrong."""
    agent = types.SimpleNamespace(
        model="test-model",
        session_total_tokens=1_900_000,
        context_compressor=types.SimpleNamespace(
            last_prompt_tokens=0,
            context_length=120_000,
            compression_count=0,
        ),
    )
    usage = server._get_usage(agent)
    assert usage.get("context_used") != 1_900_000
    assert "context_used" not in usage
    assert "context_percent" not in usage


def test_get_usage_reports_real_current_occupancy():
    """When the compressor reports a real current prompt size, context_used is
    that value (not the cumulative total) and the percent is sane."""
    agent = types.SimpleNamespace(
        model="test-model",
        session_total_tokens=1_900_000,
        context_compressor=types.SimpleNamespace(
            last_prompt_tokens=60_000,
            context_length=120_000,
            compression_count=2,
        ),
    )
    usage = server._get_usage(agent)
    assert usage["context_used"] == 60_000
    assert usage["context_max"] == 120_000
    assert usage["context_percent"] == 50


def test_get_usage_clamps_post_compression_sentinel():
    """Right after a compression, last_prompt_tokens is the -1 sentinel
    (conversation_compression sets it until the next real usage report). It is
    truthy, so `or 0` doesn't neutralize it — the guard must clamp <0 to 0 so
    the transitional turn emits no gauge instead of leaking context_used=-1."""
    agent = types.SimpleNamespace(
        model="test-model",
        session_total_tokens=4_000_000,
        context_compressor=types.SimpleNamespace(
            last_prompt_tokens=-1,
            context_length=1_048_576,
            compression_count=6,
        ),
    )
    usage = server._get_usage(agent)
    assert "context_used" not in usage
    assert "context_percent" not in usage


def test_tts_stream_begin_requires_voice_tts(monkeypatch):
    monkeypatch.setenv("HERMES_VOICE_TTS", "0")
    assert server._tts_stream_begin() is None


def test_tts_stream_begin_requires_working_provider(monkeypatch):
    monkeypatch.setenv("HERMES_VOICE_TTS", "1")
    _fake_tts_modules(monkeypatch, requirements=False)
    assert server._tts_stream_begin() is None


def test_tts_stream_begin_and_stop_lifecycle(monkeypatch):
    """begin() spawns the consumer; stop() cuts it and clears the slot."""
    monkeypatch.setenv("HERMES_VOICE_TTS", "1")
    monkeypatch.setenv("HERMES_VOICE", "0")  # no barge-in monitor (no mic)
    playback_stops: list = []
    started = _fake_tts_modules(monkeypatch, playback_stops=playback_stops)

    text_queue = server._tts_stream_begin()
    assert text_queue is not None
    assert started["queue"] is text_queue

    with server._tts_stream_lock:
        state = server._tts_stream_state
    assert state is not None and not state["stop"].is_set()

    server._tts_stream_stop()
    assert state["stop"].is_set()
    assert playback_stops == [True]
    with server._tts_stream_lock:
        assert server._tts_stream_state is None


def test_tts_stream_begin_barges_in_on_previous_pipeline(monkeypatch):
    """A new turn's pipeline stops the previous turn's speech (one speaker)."""
    monkeypatch.setenv("HERMES_VOICE_TTS", "1")
    monkeypatch.setenv("HERMES_VOICE", "0")
    _fake_tts_modules(monkeypatch)

    server._tts_stream_begin()
    with server._tts_stream_lock:
        first = server._tts_stream_state
    server._tts_stream_begin()
    assert first is not None and first["stop"].is_set()
    server._tts_stream_stop()


def test_tts_stream_stop_latches_interruption_for_next_turn(monkeypatch):
    """Cutting live speech (interrupt / typing barge) marks the latch the next
    turn's model note consumes; a mode change (user_barge=False) does not."""
    import tools.tts_streaming as ts

    ts._interrupted_at = None
    monkeypatch.setenv("HERMES_VOICE_TTS", "1")
    monkeypatch.setenv("HERMES_VOICE", "0")
    _fake_tts_modules(monkeypatch)

    server._tts_stream_begin()
    server._tts_stream_stop()  # default: user barge
    assert ts.take_speech_interrupted() is True

    server._tts_stream_begin()
    server._tts_stream_stop(user_barge=False)  # /voice off
    assert ts.take_speech_interrupted() is False


def test_tts_stream_stop_after_natural_finish_does_not_latch(monkeypatch):
    """Speech that already finished (done set) isn't an interruption."""
    import tools.tts_streaming as ts

    ts._interrupted_at = None
    monkeypatch.setenv("HERMES_VOICE_TTS", "1")
    monkeypatch.setenv("HERMES_VOICE", "0")
    _fake_tts_modules(monkeypatch)

    server._tts_stream_begin()
    with server._tts_stream_lock:
        server._tts_stream_state["done"].set()
    server._tts_stream_stop()
    assert ts.take_speech_interrupted() is False


def test_tts_stream_vad_barge_in_cuts_pipeline_and_submits_capture(monkeypatch, tmp_path):
    """User speech during playback cuts TTS at the moment of detection
    (voice.interrupted), then the captured interruption is transcribed and
    emitted as voice.transcript so the TUI submits it — complete from its
    first syllable, no re-record round trip. The cut also latches the
    speech-interrupted note for the next turn."""
    import tools.tts_streaming as ts

    ts._interrupted_at = None
    monkeypatch.setenv("HERMES_VOICE_TTS", "1")
    monkeypatch.setenv("HERMES_VOICE", "1")
    monkeypatch.setattr(server, "_load_cfg", lambda: {"voice": {"barge_in": True}})
    events: list = []
    monkeypatch.setattr(
        server, "_voice_emit", lambda event, payload=None: events.append((event, payload))
    )

    wav = tmp_path / "barge.wav"
    wav.write_bytes(b"RIFF")

    def fake_listen(should_stop, is_playing=None, on_trigger=None, **_kw):
        on_trigger("playback")  # playback cut happens at detection
        return str(wav)

    _fake_tts_modules(
        monkeypatch,
        listen=fake_listen,
        transcribe=lambda path, model=None: {"success": True, "transcript": "stop, actually—"},
    )

    server._tts_stream_begin()
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline and wav.exists():
        time.sleep(0.01)  # unlink (finally) runs after the transcript emit
    assert ("voice.interrupted", None) in events
    assert ("voice.transcript", {"text": "stop, actually—"}) in events
    assert not wav.exists()  # capture temp file cleaned up
    assert ts.take_speech_interrupted() is True  # VAD cut latches the model note
    server._tts_stream_stop()


def test_full_duplex_generation_phase_interrupts_running_turn(monkeypatch, tmp_path):
    """Speech DURING LLM generation (no TTS audio yet) must interrupt the
    in-flight agent turn via the same seam session.interrupt uses, and the
    captured interjection is emitted as voice.transcript. This is the
    half-duplex gap: previously no listener existed until playback started."""
    import tools.tts_streaming as ts

    ts._interrupted_at = None
    monkeypatch.setenv("HERMES_VOICE", "1")
    monkeypatch.setenv("HERMES_VOICE_TTS", "0")
    monkeypatch.setattr(server, "_load_cfg", lambda: {"voice": {"barge_in": True}})
    events: list = []
    monkeypatch.setattr(
        server, "_voice_emit", lambda event, payload=None: events.append((event, payload))
    )

    wav = tmp_path / "interject.wav"
    wav.write_bytes(b"RIFF")

    interrupted = threading.Event()
    fake_agent = types.SimpleNamespace(interrupt=lambda: interrupted.set())
    fake_session = {"running": True, "agent": fake_agent}
    monkeypatch.setattr(server, "_sessions", {"sid-fd": fake_session})

    def fake_listen(should_stop, is_playing=None, on_trigger=None, **_kw):
        assert is_playing is not None and is_playing() is False  # generation phase
        on_trigger("generation")
        return str(wav)

    _fake_tts_modules(
        monkeypatch,
        listen=fake_listen,
        transcribe=lambda path, model=None: {"success": True, "transcript": "wait, try another way"},
    )

    server._arm_full_duplex_listener()

    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline and wav.exists():
        time.sleep(0.01)
    assert interrupted.is_set()  # the running turn was interrupted
    assert ("voice.interrupted", None) in events
    assert ("voice.transcript", {"text": "wait, try another way"}) in events
    assert not wav.exists()


def test_full_duplex_stop_phrase_mid_generation_ends_voice_chat(monkeypatch, tmp_path):
    """Bare 'stop' during generation = interrupt the turn AND end the voice
    chat ('stop everything'), emitted as the explicit stop_phrase signal."""
    monkeypatch.setenv("HERMES_VOICE", "1")
    monkeypatch.setattr(server, "_load_cfg", lambda: {"voice": {"barge_in": True}})
    events: list = []
    monkeypatch.setattr(
        server, "_voice_emit", lambda event, payload=None: events.append((event, payload))
    )

    wav = tmp_path / "stop.wav"
    wav.write_bytes(b"RIFF")

    interrupted = threading.Event()
    fake_agent = types.SimpleNamespace(interrupt=lambda: interrupted.set())
    monkeypatch.setattr(
        server, "_sessions", {"sid-fd": {"running": True, "agent": fake_agent}}
    )

    def fake_listen(should_stop, is_playing=None, on_trigger=None, **_kw):
        on_trigger("generation")
        return str(wav)

    _fake_tts_modules(
        monkeypatch,
        listen=fake_listen,
        transcribe=lambda path, model=None: {"success": True, "transcript": "stop"},
    )
    # is_voice_stop_phrase lives in the faked tools.voice_mode namespace.
    sys.modules["tools.voice_mode"].is_voice_stop_phrase = (
        lambda text: text.strip().lower() == "stop"
    )
    monkeypatch.setitem(
        sys.modules,
        "hermes_cli.voice",
        types.SimpleNamespace(stop_continuous=lambda **_kw: None, speak_text=lambda *a, **k: None),
    )

    server._arm_full_duplex_listener()

    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline and wav.exists():
        time.sleep(0.01)
    assert interrupted.is_set()
    assert ("voice.transcript", {"stop_phrase": True, "text": "stop"}) in events
    assert os.environ.get("HERMES_VOICE") == "0"  # voice chat ended


def test_speak_text_with_barge_arms_monitor_and_cuts_playback(monkeypatch, tmp_path):
    """The fallback whole-reply speak path (streaming pipeline couldn't
    start) and the voice.tts RPC must be barge-able too: speaking over the
    reply cuts playback and the captured interruption is emitted as
    voice.transcript — previously these paths called speak_text bare and
    were uninterruptible by voice."""
    import tools.tts_streaming as ts

    ts._interrupted_at = None
    monkeypatch.setenv("HERMES_VOICE", "1")
    monkeypatch.setenv("HERMES_VOICE_TTS", "1")
    monkeypatch.setattr(
        server,
        "_load_cfg",
        lambda: {"voice": {"barge_in": True, "barge_in_grace_seconds": 0}},
    )
    events: list = []
    monkeypatch.setattr(
        server, "_voice_emit", lambda event, payload=None: events.append((event, payload))
    )

    wav = tmp_path / "barge.wav"
    wav.write_bytes(b"RIFF")

    speak_calls = {}
    speak_started = threading.Event()
    release_speak = threading.Event()

    def fake_speak_text(text, stop_event=None):
        speak_calls["text"] = text
        speak_calls["stop_event"] = stop_event
        speak_started.set()
        release_speak.wait(5)

    monkeypatch.setitem(
        sys.modules,
        "hermes_cli.voice",
        types.SimpleNamespace(speak_text=fake_speak_text),
    )

    def fake_listen(should_stop, is_playing=None, on_trigger=None, **_kw):
        speak_started.wait(5)
        on_trigger("playback")  # user talks over the reply → cut now
        return str(wav)

    _fake_tts_modules(
        monkeypatch,
        listen=fake_listen,
        transcribe=lambda path, model=None: {"success": True, "transcript": "hang on"},
    )

    server._speak_text_with_barge("a long spoken reply")

    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline and ("voice.transcript", {"text": "hang on"}) not in events:
        time.sleep(0.01)
    release_speak.set()

    assert speak_calls["text"] == "a long spoken reply"
    # The pipeline stop event is shared with speak_text so a streaming
    # dispatch inside it is cut too.
    assert speak_calls["stop_event"] is not None
    assert speak_calls["stop_event"].is_set()
    assert ("voice.interrupted", None) in events
    assert ("voice.transcript", {"text": "hang on"}) in events
    assert ts.take_speech_interrupted() is True


def test_speak_text_with_barge_no_monitor_when_voice_mode_off(monkeypatch):
    """Auto-speak with voice mode off (no mic loop) must not open the mic."""
    monkeypatch.setenv("HERMES_VOICE", "0")
    monkeypatch.setenv("HERMES_VOICE_TTS", "1")
    monkeypatch.setattr(server, "_load_cfg", lambda: {"voice": {"barge_in": True}})

    listened = threading.Event()

    def fake_listen(should_stop, capture=False, on_trigger=None, **_kw):
        listened.set()
        return None

    done_speaking = threading.Event()
    monkeypatch.setitem(
        sys.modules,
        "hermes_cli.voice",
        types.SimpleNamespace(
            speak_text=lambda text, stop_event=None: done_speaking.set()
        ),
    )
    _fake_tts_modules(monkeypatch, listen=fake_listen)

    server._speak_text_with_barge("quiet reply")
    assert done_speaking.wait(5)
    time.sleep(0.1)
    assert not listened.is_set()


def test_clarify_callback_uses_configured_timeout(monkeypatch):
    """The TUI/desktop clarify bridge sends a ``clarify`` server request with the canonical clarify timeout
    (via _clarify_timeout_seconds), and returns the response's ``answer``."""
    monkeypatch.setattr(server, "_clarify_timeout_seconds", lambda: 42)
    captured = _capture_server_request(monkeypatch, {"answer": "answer"})

    result = server._agent_cbs("sid-1")["clarify_callback"]("Pick one", ["a", "b"])

    assert result == "answer"
    assert captured["method"] == "clarify" and captured["sid"] == "sid-1"
    assert captured["timeout"] == 42
    assert captured["params"] == {"question": "Pick one", "choices": ["a", "b"]}


def test_clarify_callback_multi_select_hint(monkeypatch):
    """multi_select=True adds the hint to the params; the single-select shape stays byte-identical to the
    pre-multi-select protocol (older renderers must never see the extra field)."""
    captured = _capture_server_request(monkeypatch, {"answer": "answer"})
    cb = server._agent_cbs("sid-1")["clarify_callback"]

    cb("Pick many", ["a", "b"], multi_select=True)
    assert captured["params"] == {"question": "Pick many", "choices": ["a", "b"], "multi_select": True}

    cb("Pick one", ["a", "b"], multi_select=False)
    assert captured["params"] == {"question": "Pick one", "choices": ["a", "b"]}


@pytest.mark.parametrize(
    ("configured", "expected"),
    [(0, None), (-1, None), (42, 42)],
)
def test_clarify_timeout_seconds_maps_non_positive_to_unlimited(monkeypatch, configured, expected):
    """A ``<= 0`` clarify timeout means unlimited and reaches the server request as None
    (wait(None) waits forever) rather than an immediate wait(0) skip."""
    monkeypatch.setattr("tools.clarify_gateway.get_clarify_timeout", lambda: configured)

    assert server._clarify_timeout_seconds() == expected


def test_build_persist_message_with_image_refs_without_images_returns_text(monkeypatch):
    """#70720: when no images are attached the persisted message is the raw
    prompt — no @image directive prefix is introduced."""
    assert server._build_persist_message_with_image_refs("what is this?", []) == "what is this?"
    assert server._build_persist_message_with_image_refs("", []) == ""


def test_build_persist_message_with_image_refs_appends_existing_paths(monkeypatch, tmp_path):
    """Attached images that still exist on disk are persisted as trailing
    ``@image:<path>`` directive lines so the desktop renders them after a
    restart (instead of the vision-only enrichment that silently breaks)."""
    img = tmp_path / "cat.png"
    img.write_bytes(b"\x89PNG")

    result = server._build_persist_message_with_image_refs("what is in this photo?", [str(img)])

    assert result == f"what is in this photo?\n@image:{img}"


def test_build_persist_message_with_image_refs_skips_missing_paths(monkeypatch, tmp_path):
    """Only paths that still exist are persisted; a missing file must not
    inject a dangling @image ref into the transcript."""
    existing = tmp_path / "a.png"
    existing.write_bytes(b"png")
    missing = str(tmp_path / "gone.png")

    result = server._build_persist_message_with_image_refs("compare them", [str(existing), missing])

    assert result == f"compare them\n@image:{existing}"


def test_build_persist_message_with_image_refs_without_text_is_refs_only(monkeypatch, tmp_path):
    """A stand-alone attachment (no caption) persists as just the directive
    line, so a bare image survives in history and is not dropped as empty."""
    img = tmp_path / "only.png"
    img.write_bytes(b"png")

    assert server._build_persist_message_with_image_refs("", [str(img)]) == f"@image:{img}"


def test_build_persist_message_quotes_paths_containing_spaces(tmp_path):
    """The unquoted alternative in the directive pattern is ``\\S+``, so a path
    with a space parses as a truncated ref with the tail left as loose text.
    Desktop composer images live in the app's userData dir, which on macOS is
    ``~/Library/Application Support/...`` — a space every time."""
    img_dir = tmp_path / "Application Support" / "Hermes" / "composer-images"
    img_dir.mkdir(parents=True)
    img = img_dir / "cat.png"
    img.write_bytes(b"png")

    result = server._build_persist_message_with_image_refs("what is this?", [str(img)])

    assert result == f"what is this?\n@image:`{img}`"


def test_persist_user_message_mirrors_the_shape_sent_to_the_model(tmp_path):
    """A native-vision turn sends ``content`` as a parts list, and the session
    store ignores a plain-string override for a list payload. The override must
    mirror the list shape (ref text + the original image parts) or it is
    silently dropped and the attachment never reaches history."""
    img = tmp_path / "cat.png"
    img.write_bytes(b"png")
    image_part = {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}}
    native_parts = [{"type": "text", "text": "api-only text"}, image_part]

    override = server._build_persist_user_message("what is this?", [str(img)], native_parts)

    assert override == [{"type": "text", "text": f"what is this?\n@image:{img}"}, image_part]


def test_persist_user_message_stays_a_string_for_text_mode(tmp_path):
    """Text-mode (vision-preprocessed) turns send a string, so the override
    stays a string — the shape the session store rewrites directly."""
    img = tmp_path / "cat.png"
    img.write_bytes(b"png")

    override = server._build_persist_user_message("what is this?", [str(img)], "enriched api-only text")

    assert override == f"what is this?\n@image:{img}"


def test_native_vision_turn_persists_a_renderable_image_ref(tmp_path):
    """End to end through the real session-store flush: whichever image input
    mode the turn used, the durable row carries an ``@image:`` ref the desktop
    can render after a restart."""
    from unittest.mock import MagicMock

    from agent.image_routing import build_native_content_parts
    from run_agent import AIAgent

    img_dir = tmp_path / "Application Support" / "composer-images"
    img_dir.mkdir(parents=True)
    img = img_dir / "cat.png"
    img.write_bytes(
        bytes.fromhex(
            "89504e470d0a1a0a0000000d494844520000000100000001080600000"
            "01f15c4890000000a49444154789c6360000002000100ffff0300000600"
            "0557bfabd40000000049454e44ae426082"
        )
    )
    native_parts, skipped = build_native_content_parts("what is in this photo?", [str(img)])
    assert not skipped

    agent = AIAgent.__new__(AIAgent)
    agent._session_db = MagicMock()
    agent._session_db_created = True
    agent.session_id = "s-1"
    agent._last_flushed_db_idx = 0
    agent._persist_disabled = False
    agent._flushed_db_message_ids = set()
    agent._flushed_db_message_session_id = None
    agent._pending_cli_user_message = None
    agent._persist_user_message_timestamp = None
    agent._persist_user_message_idx = 0
    agent._persist_user_message_override = server._build_persist_user_message(
        "what is in this photo?", [str(img)], native_parts
    )

    agent._flush_messages_to_session_db([{"role": "user", "content": native_parts}], [])

    written = agent._session_db.append_messages_batch.call_args.kwargs["messages"][0]["content"]
    assert f"@image:`{img}`" in written
    assert "what is in this photo?" in written
    # The model keeps the pixels for the rest of the session.
    assert any(part.get("type") == "image_url" for part in agent._persist_user_message_override)


def test_prompt_submit_passes_persist_user_message_to_agent(monkeypatch):
    """#70720: _run_prompt_submit must forward the (image-ref-aware) persisted
    user message to run_conversation via persist_user_message, so the gateway
    stores the UI-recognizable form instead of the vision enrichment."""
    captured = {}

    class _Agent:
        def run_conversation(self, prompt, conversation_history=None, stream_callback=None, **_kwargs):
            captured["persist_user_message"] = _kwargs.get("persist_user_message")
            return {
                "final_response": "reply",
                "messages": [{"role": "assistant", "content": "reply"}],
            }

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None, **_thread_options):
            self._target = target

        def start(self):
            self._target()

    server._sessions["sid"] = _session(agent=_Agent())
    try:
        monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)
        monkeypatch.setattr(server, "_get_usage", lambda _a: {})
        monkeypatch.setattr(server, "render_message", lambda _t, _c: "")
        monkeypatch.setattr(server, "_emit", lambda *a: None)

        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {"session_id": "sid", "text": "hi"},
            }
        )
        assert resp.get("result")

        # Without attachments the persist form equals the raw prompt.
        assert captured.get("persist_user_message") == "hi"
    finally:
        server._sessions.pop("sid", None)


def test_fallback_session_info_reports_session_cwd_not_launch_dir(monkeypatch):
    """A lazily-resumed session must report ITS workspace, not the gateway's.

    ``_fallback_session_info`` used ``_default_session_cwd()`` — the directory the
    gateway process happened to start in — so the desktop Files pane painted the
    wrong project for any session resumed without a built agent (#71254).
    """
    monkeypatch.setattr(server, "_default_session_cwd", lambda: "/gateway/launch/dir")
    monkeypatch.setattr(server.git_probe, "branch", lambda cwd: "bb/feature")
    monkeypatch.setattr(server, "_project_info_for_cwd", lambda cwd: None)
    monkeypatch.setattr(server, "_resolve_model", lambda: "test-model")

    info = server._fallback_session_info({"cwd": "/projects/session-own-repo"})

    assert info["cwd"] == "/projects/session-own-repo"
    assert info["branch"] == "bb/feature"


def test_fallback_session_info_always_emits_branch(monkeypatch):
    """``branch`` is always present so a client can CLEAR a stale label.

    Omitting the key left the desktop showing the previous conversation's branch
    after switching into a non-git session.
    """
    monkeypatch.setattr(server, "_default_session_cwd", lambda: "/gateway/launch/dir")
    monkeypatch.setattr(server.git_probe, "branch", lambda cwd: "")
    monkeypatch.setattr(server, "_project_info_for_cwd", lambda cwd: None)
    monkeypatch.setattr(server, "_resolve_model", lambda: "test-model")

    info = server._fallback_session_info({"cwd": "/plain/folder"})

    assert "branch" in info
    assert info["branch"] == ""


def test_persist_branch_seed_keeps_reasoning_fields(monkeypatch, tmp_path):
    """The seed write must carry the parent's reasoning fields.

    A branch is a draft until its first submit, so this is the only write that
    ever persists the copied transcript. Persisting role/content alone left the
    branch resuming without the parent's reasoning, preserved thinking blocks or
    Codex encrypted-reasoning/message-item continuation state.
    """
    from hermes_state import SessionDB

    db = SessionDB(db_path=tmp_path / "state.db")
    session = _session(
        session_key="branch-key",
        parent_session_id="parent-key",
        history=_branch_history(),
        seeded=True,  # stamped by session.create: this history exists only in memory
    )
    try:
        db.create_session("branch-key", source="tui")
        monkeypatch.setattr(server, "_get_db", lambda: db)

        server._persist_branch_seed(session)

        assistant = _branched_assistant(db, "branch-key")
        assert assistant["reasoning"] == BRANCH_REASONING
        assert assistant["reasoning_content"] == BRANCH_REASONING_CONTENT
        assert assistant["reasoning_details"] == BRANCH_REASONING_DETAILS
        assert assistant["codex_reasoning_items"] == BRANCH_CODEX_REASONING_ITEMS
        assert assistant["codex_message_items"] == BRANCH_CODEX_MESSAGE_ITEMS
        marker = _branched_marker(db, "branch-key")
        assert marker is not None, (
            "the branch seed dropped display_kind: the marker re-entered the "
            "truncate ordinal address space as a phantom user turn (#82756)"
        )
        assert session["_branch_seed_persisted"] is True
    finally:
        db.close()


def test_session_branch_keeps_reasoning_fields(monkeypatch, tmp_path):
    """session.branch copies the live transcript with its reasoning fields.

    Same drop as the seed path: the copy loop wrote only role/content, so the
    new session row replayed without the reasoning context the parent had.
    """
    from hermes_state import SessionDB

    db = SessionDB(db_path=tmp_path / "state.db")
    server._sessions["sid"] = _session(history=_branch_history())
    try:
        db.create_session("session-key", source="tui")
        monkeypatch.setattr(server, "_get_db", lambda: db)
        monkeypatch.setattr(server, "_new_session_key", lambda: "branch-key")
        monkeypatch.setattr(server, "_start_agent_build", lambda sid, session: None)
        monkeypatch.setattr(server, "_wait_agent", lambda session, rid: None)
        monkeypatch.setattr(
            server, "_claim_active_session_slot", lambda *args, **kwargs: (None, None)
        )
        monkeypatch.setattr(server, "_resolve_model", lambda: "test-model")
        monkeypatch.setattr(server, "_session_cwd", lambda session: str(tmp_path))
        monkeypatch.setattr(
            server, "_make_agent", lambda *args, **kwargs: types.SimpleNamespace()
        )
        monkeypatch.setattr(server, "_init_session", lambda *args, **kwargs: None)

        resp = server.handle_request(
            {"id": "1", "method": "session.branch", "params": {"session_id": "sid"}}
        )

        assert resp.get("result"), f"got error: {resp.get('error')}"
        assert db.get_session_title_source("branch-key") == SessionDB.TITLE_SOURCE_DERIVED
        assistant = _branched_assistant(db, "branch-key")
        assert assistant["reasoning"] == BRANCH_REASONING
        assert assistant["reasoning_content"] == BRANCH_REASONING_CONTENT
        assert assistant["reasoning_details"] == BRANCH_REASONING_DETAILS
        assert assistant["codex_reasoning_items"] == BRANCH_CODEX_REASONING_ITEMS
        assert assistant["codex_message_items"] == BRANCH_CODEX_MESSAGE_ITEMS
        marker = _branched_marker(db, "branch-key")
        assert marker is not None, (
            "session.branch dropped display_kind: the marker re-entered the "
            "truncate ordinal address space as a phantom user turn (#82756)"
        )
    finally:
        server._sessions.pop("sid", None)
        db.close()


# ── _save_cfg comment-preservation regression tests ────────────────────────
#
# Until ~mid-2026 _save_cfg used yaml.safe_dump on a deep-loaded config dict.
# Every /personality (or /reasoning, /details_mode, /prompt, ...) write
# silently rewrote ~/.hermes/config.yaml top-to-bottom — top-level keys
# reordered alphabetically, comments stripped, kaomoji/Chinese in stored
# personality prompts mangled to \uXXXX escapes. These tests pin the
# user-visible behavior of the comment-preserving replacement so we don't
# regress.


def test_save_cfg_preserves_user_comments(tmp_path, monkeypatch):
    """The TUI gateway must not strip user-edited comments on setting writes."""
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        "# top of file note\n"
        "model:\n"
        "  # provider rationale\n"
        "  default: claude-opus-4-7\n"
        "display:\n"
        "  skin: default  # trailing skin note\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(server, "_hermes_home", tmp_path)

    server._save_cfg(
        {
            "model": {"default": "claude-opus-4-7"},
            "display": {"skin": "mono"},
        }
    )

    text = cfg_path.read_text(encoding="utf-8")
    assert "# top of file note" in text
    assert "# provider rationale" in text
    assert "# trailing skin note" in text

    import hermes_yaml as _yaml

    parsed = _yaml.safe_load(text)
    assert parsed["display"]["skin"] == "mono"


def test_save_cfg_preserves_top_level_key_order(tmp_path, monkeypatch):
    """Top-level keys must keep the file's hand-edited ordering instead of
    being rewritten alphabetically by the underlying YAML dumper."""
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        "model:\n"
        "  default: claude-opus-4-7\n"
        "toolsets:\n"
        "  - hermes-cli\n"
        "agent:\n"
        "  max_turns: 90\n"
        "display:\n"
        "  skin: default\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(server, "_hermes_home", tmp_path)

    # Caller's dict iteration order is intentionally alphabetical to confirm
    # the helper consults disk order, not caller order.
    server._save_cfg(
        {
            "agent": {"max_turns": 90},
            "display": {"skin": "mono"},
            "model": {"default": "claude-opus-4-7"},
            "toolsets": ["hermes-cli"],
        }
    )

    text = cfg_path.read_text(encoding="utf-8")
    top_keys = [
        line.split(":", 1)[0]
        for line in text.splitlines()
        if line and not line.startswith(" ") and not line.startswith("-")
        and not line.startswith("#")
    ]
    assert top_keys == ["model", "toolsets", "agent", "display"]


def test_save_cfg_keeps_unicode_personalities_readable(tmp_path, monkeypatch):
    """The catgirl/kawaii personality prompts must stay readable on disk
    instead of being \\uXXXX-escaped on every unrelated setting write."""
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        "agent:\n"
        "  personalities:\n"
        "    catgirl: \"nya (=^･ω･^=) 你好\"\n"
        "display:\n"
        "  skin: default\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(server, "_hermes_home", tmp_path)

    # Simulate an unrelated /skin write — must not corrupt the catgirl
    # personality string sitting in agent.personalities.
    server._save_cfg(
        {
            "agent": {"personalities": {"catgirl": "nya (=^･ω･^=) 你好"}},
            "display": {"skin": "mono"},
        }
    )

    text = cfg_path.read_text(encoding="utf-8")
    assert "你好" in text
    assert "(=^･ω･^=)" in text
    assert "\\u4f60" not in text


def test_personality_marker_does_not_shift_truncate_ordinal(monkeypatch):
    """A personality pivot must not occupy a slot in the ordinal address space.

    ``_apply_personality_to_session`` injects its pivot as ``role=user`` so
    strict OpenAI-compatible providers accept it mid-conversation. Untagged, the
    ordinal filter (``role == "user" and not display_kind``) counted it as a
    real user turn while no client renders it as one, so every rewind issued
    after a personality change resolved one turn too early and
    ``replace_messages()`` hard-deleted the extra span (#82756, third occurrence
    after #70516 / #80763).

    The sibling ``test_prompt_submit_truncate_ordinal_skips_display_kind_rows``
    pins the filter itself; this one pins the producer, which is where the
    invariant was actually broken.
    """

    class _Agent:
        def run_conversation(self, prompt, conversation_history=None, stream_callback=None, **_kwargs):
            return {
                "final_response": "reply",
                "messages": [
                    *(conversation_history or []),
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": "reply"},
                ],
            }

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None, **_thread_options):
            self._target = target

        def start(self):
            self._target()

    class _StubDb:
        def __init__(self):
            self.replaced = []

        def get_messages_as_conversation(self, *_args, **_kwargs):
            return []

        def replace_messages(
            self,
            session_id,
            messages,
            active_only=False,
            archive_dropped=False,
            reject_active_turn_lease=False,
        ):
            self.replaced.append((session_id, list(messages)))

    session = _session(
        agent=_Agent(),
        history=[
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "first reply"},
        ],
    )
    server._sessions["personality-ordinal-sid"] = session
    stub_db = _StubDb()

    try:
        monkeypatch.setattr(server, "_session_info", lambda *a, **k: {})
        monkeypatch.setattr(server, "_emit", lambda *a: None)

        # Real production injection point — not a hand-written marker dict.
        server._apply_personality_to_session(
            "personality-ordinal-sid", session, "talk like a pirate", "pirate"
        )

        marker = session["history"][-1]
        assert marker["role"] == "user", "provider compatibility: pivot rides as a user turn"

        # Two more real turns land after the personality change.
        session["history"].extend(
            [
                {"role": "user", "content": "second"},
                {"role": "assistant", "content": "second reply"},
                {"role": "user", "content": "third"},
                {"role": "assistant", "content": "third reply"},
            ]
        )
        history_before = list(session["history"])
        third_index = history_before.index({"role": "user", "content": "third"})

        monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)
        monkeypatch.setattr(server, "_get_usage", lambda _a: {})
        monkeypatch.setattr(server, "render_message", lambda _t, _c: "")
        monkeypatch.setattr(server, "_get_db", lambda: stub_db)

        # The client counts three user bubbles (first=0, second=1, third=2) —
        # it never sees the pivot. Rewinding to "third" must cut exactly there.
        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "personality-ordinal-sid",
                    "text": "third, reworded",
                    "truncate_before_user_ordinal": 2,
                    "confirm_truncate": True,
                },
            }
        )
        assert resp.get("result"), f"got error: {resp.get('error')}"

        expected = history_before[:third_index]
        assert stub_db.replaced == [("session-key", expected)], (
            "the pivot shifted the ordinal: the cut landed at "
            f"{len(stub_db.replaced[0][1]) if stub_db.replaced else None} instead of {third_index}"
        )
        # The turn before the target must survive — that is the span the three
        # reported incidents lost.
        assert {"role": "user", "content": "second"} in expected
        # And the mechanism that keeps it out of the address space, so a future
        # producer cannot regress this by dropping the tag.
        assert marker.get("display_kind"), (
            "an untagged role=user pivot silently consumes a truncate ordinal slot"
        )
    finally:
        server._sessions.pop("personality-ordinal-sid", None)


def test_prompt_submit_truncation_archives_instead_of_deleting(monkeypatch):
    """The rewind write must be recoverable, not a hard DELETE.

    #70516 / #80763 / #82756 all ended at this one call, and all three were
    unrecoverable for the same reason: `replace_messages` DELETEs the rows and
    the FTS entry goes with them. Guarding the *aim* of a rewind still leaves
    every other way of aiming it wrong terminal, so the write itself has to
    stop destroying. The storage-layer contract this relies on is pinned in
    tests/hermes_state/test_replace_messages_archive_siblings.py.
    """

    captured = {}

    class _Agent:
        def run_conversation(self, prompt, conversation_history=None, stream_callback=None, **_kwargs):
            return {
                "final_response": "reply",
                "messages": [
                    *(conversation_history or []),
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": "reply"},
                ],
            }

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None, **_thread_options):
            self._target = target

        def start(self):
            self._target()

    class _StubDb:
        def get_messages_as_conversation(self, *_args, **_kwargs):
            return []

        def replace_messages(
            self,
            session_id,
            messages,
            active_only=False,
            archive_dropped=False,
            reject_active_turn_lease=False,
        ):
            captured["active_only"] = active_only
            captured["archive_dropped"] = archive_dropped
            captured["reject_active_turn_lease"] = reject_active_turn_lease

    server._sessions["archive-trunc-sid"] = _session(
        agent=_Agent(),
        history=[
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "first reply"},
            {"role": "user", "content": "second"},
            {"role": "assistant", "content": "second reply"},
        ],
    )

    try:
        monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)
        monkeypatch.setattr(server, "_session_info", lambda *a, **k: {})
        monkeypatch.setattr(server, "_emit", lambda *a: None)
        monkeypatch.setattr(server, "_get_usage", lambda _a: {})
        monkeypatch.setattr(server, "render_message", lambda _t, _c: "")
        monkeypatch.setattr(server, "_get_db", lambda: _StubDb())

        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "archive-trunc-sid",
                    "text": "second, reworded",
                    "truncate_before_user_ordinal": 1,
                    "confirm_truncate": True,
                },
            }
        )

        assert resp.get("result"), f"got error: {resp.get('error')}"
        assert captured.get("archive_dropped") is True, (
            "a rewind must soft-archive the turns it drops, not DELETE them"
        )
        # #80216: still must not touch rows archived by an earlier compaction.
        assert captured.get("active_only") is True
        assert captured.get("reject_active_turn_lease") is True
    finally:
        server._sessions.pop("archive-trunc-sid", None)
