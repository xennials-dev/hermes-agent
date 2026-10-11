"""tui_gateway.server — voice/wake/record, tool loading and history-to expansion.

Split from test_tui_gateway_server.py; shared fixtures and helpers live
in tests/tui_gateway/_server_test_helpers.py.
"""

import json
import os
import sys
import threading
import types
from tui_gateway import server

from tests.tui_gateway._server_test_helpers import (
    _dispatch_sync,
    _neuter_agent_prewarm_timer,  # autouse
    _reap_leaked_notification_pollers,  # autouse
)


def test_usage_ticker_unbounded_join_waits_out_blocked_emit(monkeypatch):
    """A tick stalled inside _emit (a transport write can block up to
    _WS_WRITE_TIMEOUT_S = 10s on a stalled event loop) must be waited out by
    the stop sequence, not abandoned: stop.set() + an unbounded join may only
    return after the in-flight emit has fully flushed, so nothing can land
    after message.complete."""
    order: list[str] = []
    in_emit = threading.Event()
    release = threading.Event()

    def _stalled_emit(event_type, sid, payload):
        in_emit.set()
        release.wait(10.0)  # the stalled transport write
        order.append(event_type)

    monkeypatch.setattr(server, "_emit", _stalled_emit)

    counter = {"n": 0}

    def _moving_usage(agent):
        counter["n"] += 1
        return {"total": counter["n"]}  # moves every sample → a tick emits

    monkeypatch.setattr(server, "_get_usage", _moving_usage)

    stop, thread = server._start_usage_ticker("sess-1", object(), interval=0.01)
    assert in_emit.wait(2.0), "no tick got in flight"

    # Run the exact stop sequence _run_prompt_submit uses, on a side thread so
    # the test can observe whether it returns while the emit is still stuck.
    stopped = threading.Event()

    def _stop_sequence():
        stop.set()
        thread.join()
        stopped.set()

    stopper = threading.Thread(target=_stop_sequence, daemon=True)
    stopper.start()

    # While the tick is stalled in the transport write, the stop sequence must
    # NOT complete — a timed join returning here is exactly the bug: the
    # caller would proceed to message.complete with the tick still pending.
    assert not stopped.wait(0.2), "stop sequence returned with the tick still in flight"

    release.set()
    assert stopped.wait(2.0), "stop sequence never completed after the emit flushed"
    stopper.join(timeout=2.0)

    # The flushed tick strictly precedes anything the caller emits afterwards.
    order.append("message.complete")
    assert order == ["session.usage", "message.complete"]


def test_tui_verbose_tool_details_fail_closed_when_redaction_fails(monkeypatch):
    redact_module = types.ModuleType("agent.redact")

    def fail_redaction(*_args, **_kwargs):
        raise RuntimeError("redaction unavailable")

    setattr(redact_module, "redact_sensitive_text", fail_redaction)
    monkeypatch.setitem(sys.modules, "agent.redact", redact_module)

    assert server._redact_tui_verbose_text("api_key=secret") == ""
    assert server._tool_args_text({"api_key": "secret"}) == ""
    assert server._tool_result_text("token=secret") == ""


def test_tui_verbose_tool_details_are_capped_before_emit(monkeypatch):
    monkeypatch.setattr(server, "_TUI_VERBOSE_TEXT_MAX_CHARS", 12)
    monkeypatch.setattr(server, "_TUI_VERBOSE_TEXT_MAX_LINES", 2)

    capped = server._cap_tui_verbose_text("one\ntwo\nthree\nfour")

    assert capped.endswith("three\nfour")
    assert "one" not in capped


def test_tui_verbose_default_cap_stays_small(monkeypatch):
    # Regression guard for #34095: the verbose tool text shipped to the TUI is
    # rendered into a persisted, expanded-by-default trail block for the whole
    # session. Raising this cap back toward the old 16KB re-introduces the Ink
    # render-tree blowup that silently OOM-killed the TUI. Keep it small.
    huge = "x" * 40_000
    capped = server._cap_tui_verbose_text(huge)

    assert len(capped) < 2_000


def test_tui_verbose_tool_events_omit_details_when_redaction_fails(monkeypatch):
    redact_module = types.ModuleType("agent.redact")

    def fail_redaction(*_args, **_kwargs):
        raise RuntimeError("redaction unavailable")

    setattr(redact_module, "redact_sensitive_text", fail_redaction)
    monkeypatch.setitem(sys.modules, "agent.redact", redact_module)

    events: list[tuple[str, str, dict]] = []
    monkeypatch.setattr(
        server, "_emit", lambda event_type, sid, payload: events.append((event_type, sid, payload))
    )
    monkeypatch.setitem(
        server._sessions,
        "redaction-test",
        {"tool_progress_mode": "verbose", "tool_started_at": {}},
    )

    server._on_tool_start("redaction-test", "tool-1", "terminal", {"command": "pwd"})
    server._on_tool_complete("redaction-test", "tool-1", "terminal", {"command": "pwd"}, "done")

    assert events[0][0] == "tool.start"
    assert events[1][0] == "tool.complete"
    assert "args_text" not in events[0][2]
    assert "result_text" not in events[1][2]


def test_tui_tool_output_risk_event_exposes_metadata_without_raw_output(monkeypatch):
    events: list[tuple[str, str, dict]] = []
    monkeypatch.setattr(
        server, "_emit", lambda event_type, sid, payload: events.append((event_type, sid, payload))
    )
    monkeypatch.setitem(
        server._sessions,
        "risk-test",
        {"tool_progress_mode": "all"},
    )

    server._on_tool_progress(
        "risk-test",
        "tool.output_risk",
        "web_extract",
        tool_call_id="tool-1",
        risk_metadata={
            "risk": "high",
            "findings": ["prompt_injection"],
            "redacted": False,
        },
    )

    assert events == [(
        "tool.output_risk",
        "risk-test",
        {
            "tool_id": "tool-1",
            "name": "web_extract",
            "risk": "high",
            "findings": ["prompt_injection"],
            "redacted": False,
        },
    )]
    assert "result" not in events[0][2]


def test_tui_clarify_lifecycle_events_emit_when_tool_progress_off(monkeypatch):
    events: list[tuple[str, str, dict]] = []
    monkeypatch.setattr(
        server, "_emit", lambda event_type, sid, payload: events.append((event_type, sid, payload))
    )
    monkeypatch.setitem(
        server._sessions,
        "clarify-off-test",
        {"tool_progress_mode": "off", "tool_started_at": {}},
    )

    args = {"question": "Pick one", "choices": ["A", "B"]}
    result = '{"question":"Pick one","choices_offered":["A","B"],"user_response":"A"}'

    server._on_tool_start("clarify-off-test", "tool-clarify", "clarify", args)
    server._on_tool_complete("clarify-off-test", "tool-clarify", "clarify", args, result)

    assert [event[0] for event in events] == ["tool.start", "tool.complete"]
    assert events[0][2]["name"] == "clarify"
    assert events[0][2]["tool_id"] == "tool-clarify"
    assert events[1][2]["result"]["user_response"] == "A"


def test_tui_non_interactive_tool_lifecycle_stays_hidden_when_tool_progress_off(monkeypatch):
    events: list[tuple[str, str, dict]] = []
    monkeypatch.setattr(
        server, "_emit", lambda event_type, sid, payload: events.append((event_type, sid, payload))
    )
    monkeypatch.setitem(
        server._sessions,
        "terminal-off-test",
        {"tool_progress_mode": "off", "tool_started_at": {}},
    )

    server._on_tool_start("terminal-off-test", "tool-1", "terminal", {"command": "pwd"})
    server._on_tool_complete("terminal-off-test", "tool-1", "terminal", {"command": "pwd"}, "done")

    assert events == []


def test_dispatch_rejects_non_object_request():
    resp = server.dispatch([])

    assert resp["id"] is None
    assert resp["error"]["code"] == -32600


def test_dispatch_rejects_non_object_params():
    resp = server.dispatch({"id": "1", "method": "session.create", "params": []})

    assert resp["id"] == "1"
    assert resp["error"]["code"] == -32602


def test_system_battery_fails_open(monkeypatch):
    def boom():
        raise RuntimeError("no battery subsystem")

    monkeypatch.setitem(
        sys.modules,
        "agent.battery",
        types.SimpleNamespace(read_battery=boom, battery_category=lambda _s: "dim"),
    )

    resp = server.dispatch({"id": "b2", "method": "system.battery", "params": {}})

    assert resp["result"]["available"] is False
    assert resp["result"]["percent"] is None


def test_config_set_battery_toggles_and_persists(monkeypatch):
    writes: dict[str, object] = {}
    monkeypatch.setattr(server, "_load_cfg", lambda: {"display": {"battery": False}})
    monkeypatch.setattr(
        server, "_write_config_key", lambda k, v: writes.__setitem__(k, v)
    )

    resp = server.dispatch(
        {"id": "c1", "method": "config.set", "params": {"key": "battery", "value": ""}}
    )

    assert resp["result"] == {"key": "battery", "value": "on"}
    assert writes == {"display.battery": True}


def test_config_set_battery_explicit_off(monkeypatch):
    writes: dict[str, object] = {}
    monkeypatch.setattr(server, "_load_cfg", lambda: {"display": {"battery": True}})
    monkeypatch.setattr(
        server, "_write_config_key", lambda k, v: writes.__setitem__(k, v)
    )

    resp = server.dispatch(
        {
            "id": "c2",
            "method": "config.set",
            "params": {"key": "battery", "value": "off"},
        }
    )

    assert resp["result"] == {"key": "battery", "value": "off"}
    assert writes == {"display.battery": False}


def test_voice_toggle_returns_configured_record_key(monkeypatch):
    monkeypatch.setattr(
        server,
        "_load_cfg",
        lambda: {"voice": {"record_key": "ctrl+o"}},
    )
    monkeypatch.setitem(
        sys.modules,
        "tools.voice_mode",
        types.SimpleNamespace(
            check_voice_requirements=lambda: {"available": True, "details": ""}
        ),
    )
    # ``voice.toggle`` action=on mutates ``os.environ["HERMES_VOICE"]``
    # directly (CLI parity, runtime-only flag). Take monkeypatch
    # ownership of the var so the change is reverted at teardown and
    # later tests don't inherit a stale ON state (Copilot round-5
    # review on #19835).
    monkeypatch.setenv("HERMES_VOICE", "0")

    on_resp = _dispatch_sync(
        {"id": "voice-on", "method": "voice.toggle", "params": {"action": "on"}}
    )
    status_resp = _dispatch_sync(
        {"id": "voice-status", "method": "voice.toggle", "params": {"action": "status"}}
    )

    assert on_resp["result"]["record_key"] == "ctrl+o"
    assert status_resp["result"]["record_key"] == "ctrl+o"


def test_voice_toggle_handles_non_dict_voice_cfg(monkeypatch):
    """Round-3 Copilot review regression on #19835.

    ``_load_cfg()`` is raw ``yaml.safe_load()`` output — a hand-edited
    ``voice: true`` / ``voice: cmd+b`` / ``voice: null`` leaves ``voice``
    as a bool/str/None, not a dict. Previously ``.get("record_key")``
    on a non-dict broke every ``voice.toggle`` branch. Now it falls
    back to the documented default.
    """
    monkeypatch.setitem(
        sys.modules,
        "tools.voice_mode",
        types.SimpleNamespace(
            check_voice_requirements=lambda: {"available": True, "details": ""}
        ),
    )

    for bad in (True, "cmd+b", None, 42, ["ctrl+b"]):
        monkeypatch.setattr(server, "_load_cfg", lambda b=bad: {"voice": b})

        status_resp = _dispatch_sync(
            {
                "id": "voice-status",
                "method": "voice.toggle",
                "params": {"action": "status"},
            }
        )

        assert (
            status_resp["result"]["record_key"] == "ctrl+b"
        ), f"voice.record_key fell back to default for voice={bad!r}"

    # Round-4 follow-up: the YAML root itself may be a non-dict. A
    # hand-edit that collapses config.yaml to a scalar / list would
    # otherwise crash ``.get("voice")`` before the inner isinstance
    # guard gets a chance to run.
    for bad_root in (True, None, [], "ctrl+b", 42):
        monkeypatch.setattr(server, "_load_cfg", lambda r=bad_root: r)

        status_resp = _dispatch_sync(
            {
                "id": "voice-status-root",
                "method": "voice.toggle",
                "params": {"action": "status"},
            }
        )

        assert (
            status_resp["result"]["record_key"] == "ctrl+b"
        ), f"voice.record_key fell back to default for root={bad_root!r}"


def test_voice_record_start_handles_non_dict_voice_cfg(monkeypatch):
    """Round-7 Copilot review regression on #19835.

    The ``voice.record`` start path previously read
    ``_load_cfg().get("voice", {}).get(...)`` without any shape checks.
    When ``voice`` is a non-dict (bool/scalar/list) ``get`` raises
    AttributeError and the handler returns 5025 instead of falling
    back to the VAD defaults. Now it uses ``_voice_cfg_dict()`` and
    non-numeric silence values are coerced to the documented defaults.
    """
    captured: dict = {}

    def fake_start_continuous(**kwargs):
        captured.update(kwargs)

    monkeypatch.setitem(
        sys.modules,
        "hermes_cli.voice",
        types.SimpleNamespace(
            start_continuous=fake_start_continuous, stop_continuous=lambda: None
        ),
    )
    monkeypatch.setenv("HERMES_VOICE", "1")

    for bad in (True, "cmd+b", None, 42, ["ctrl+b"], {"silence_threshold": "loud"}):
        captured.clear()
        monkeypatch.setattr(server, "_load_cfg", lambda b=bad: {"voice": b})

        resp = _dispatch_sync(
            {
                "id": "voice-record",
                "method": "voice.record",
                "params": {"action": "start"},
            }
        )

        assert (
            "result" in resp
        ), f"voice.record raised for voice={bad!r}: {resp.get('error')}"
        assert resp["result"]["status"] == "recording"
        assert captured["silence_threshold"] == 200
        assert captured["silence_duration"] == 3.0
        assert captured["auto_restart"] is False


    # Round-12 Copilot review regression on #19835: ``bool`` is a subclass
    # of ``int``, so the naive ``isinstance(threshold, (int, float))``
    # guard would forward ``silence_threshold: true`` as ``1`` instead
    # of falling back to the documented 200 default.
    for bad_bool_cfg in (
        {"silence_threshold": True, "silence_duration": False},
        {"silence_threshold": False},
        {"silence_duration": True},
    ):
        captured.clear()
        monkeypatch.setattr(server, "_load_cfg", lambda c=bad_bool_cfg: {"voice": c})

        resp = _dispatch_sync(
            {
                "id": "voice-record-bool",
                "method": "voice.record",
                "params": {"action": "start"},
            }
        )

        assert "result" in resp, f"voice.record raised for bool cfg={bad_bool_cfg!r}"
        assert (
            captured["silence_threshold"] == 200
        ), f"bool silence_threshold leaked through for {bad_bool_cfg!r}"
        assert (
            captured["silence_duration"] == 3.0
        ), f"bool silence_duration leaked through for {bad_bool_cfg!r}"
        assert captured["auto_restart"] is False


def test_prompt_submit_typed_stop_phrase_ends_voice_chat(monkeypatch):
    """Typed bare stop phrase during an active voice chat is consumed at the
    prompt.submit choke point: voice mode flips off, a distinct
    voice.transcript {stop_phrase, typed} event fires, and NO turn starts.
    """
    calls = {"stop_continuous": 0}
    emitted = []
    monkeypatch.setattr(
        server, "_emit", lambda event, sid, payload=None: emitted.append((event, payload))
    )
    monkeypatch.setitem(
        sys.modules,
        "tools.voice_mode",
        types.SimpleNamespace(
            is_voice_stop_phrase=lambda t: t.strip().lower().strip(".!?") == "stop"
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "hermes_cli.voice",
        types.SimpleNamespace(
            stop_continuous=lambda force_transcribe=False: calls.__setitem__(
                "stop_continuous", calls["stop_continuous"] + 1
            )
        ),
    )
    monkeypatch.setattr(server, "_tts_stream_stop", lambda user_barge=False: None)
    monkeypatch.setenv("HERMES_VOICE", "1")
    monkeypatch.setenv("HERMES_VOICE_TTS", "1")

    resp = server.dispatch(
        {
            "id": "typed-stop",
            "method": "prompt.submit",
            "params": {"session_id": "any-sid", "text": "Stop."},
        }
    )

    assert resp["result"] == {"voice_stopped": True}
    assert os.environ["HERMES_VOICE"] == "0"
    assert os.environ["HERMES_VOICE_TTS"] == "0"
    assert calls["stop_continuous"] == 1
    assert ("voice.transcript", {"stop_phrase": True, "typed": True}) in emitted


def test_prompt_submit_typed_stop_passes_through_when_voice_off(monkeypatch):
    """Outside a voice chat, typed "stop" is a normal message — the stop
    matcher must not even be consulted (guard is on voice mode)."""
    monkeypatch.setitem(
        sys.modules,
        "tools.voice_mode",
        types.SimpleNamespace(
            is_voice_stop_phrase=lambda t: (_ for _ in ()).throw(
                AssertionError("stop matcher must not run when voice is off")
            )
        ),
    )
    monkeypatch.setenv("HERMES_VOICE", "0")

    resp = server.dispatch(
        {
            "id": "typed-stop-off",
            "method": "prompt.submit",
            "params": {"session_id": "missing-sid", "text": "stop"},
        }
    )

    # The submit proceeds into normal handling (here: unknown session error),
    # NOT the voice_stopped consumption path.
    assert resp.get("result") != {"voice_stopped": True}


def test_wake_owner_is_sticky_and_routes_detection_to_first_transport(monkeypatch):
    from tools import wake_word

    state = {"owner": None, "callback": None, "paused": False}
    voice_callbacks = {}

    def start_listening(callback, *, owner, config, external_audio=False):
        if state["owner"] is not None and state["owner"] is not owner:
            raise wake_word.WakeWordInUse
        state.update(
            owner=owner,
            callback=callback,
            paused=False,
            external_audio=bool(external_audio),
        )

    def pause_listening(*, owner):
        if state["owner"] is not owner:
            return False
        state["paused"] = True
        return True

    def stop_listening(*, owner):
        if state["owner"] is not owner:
            return False
        state.update(owner=None, callback=None, paused=False)
        return True

    def resume_listening(*, owner):
        if state["owner"] is not owner:
            return False
        state["paused"] = False
        return True

    def start_continuous(**callbacks):
        voice_callbacks.update(callbacks)
        return True

    monkeypatch.setattr(wake_word, "load_wake_word_config", lambda: {
        "enabled": True,
        "phrase": "hey hermes",
        "surface": "auto",
        "start_new_session": True,
    })
    monkeypatch.setattr(wake_word, "check_wake_word_requirements", lambda _cfg: {
        "available": True,
        "phrase": "hey hermes",
        "provider": "test",
        "hint": "",
    })
    monkeypatch.setattr(wake_word, "start_listening", start_listening)
    monkeypatch.setattr(wake_word, "pause_listening", pause_listening)
    monkeypatch.setattr(wake_word, "stop_listening", stop_listening)
    monkeypatch.setattr(wake_word, "owns_listener", lambda owner: state["owner"] is owner)
    monkeypatch.setattr(
        wake_word,
        "is_listening",
        lambda: state["owner"] is not None and not state["paused"],
    )
    monkeypatch.setattr(
        wake_word,
        "resume_listening",
        resume_listening,
    )
    monkeypatch.setitem(
        sys.modules,
        "hermes_cli.voice",
        types.SimpleNamespace(
            start_continuous=start_continuous,
            stop_continuous=lambda **_kwargs: None,
        ),
    )
    monkeypatch.setenv("HERMES_VOICE", "1")

    first = types.SimpleNamespace(_closed=False)
    second = types.SimpleNamespace(_closed=False)
    emitted = []
    monkeypatch.setattr(
        server,
        "_emit",
        lambda event, sid, payload: emitted.append(
            (event, sid, payload, server.current_transport())
        ),
    )
    server._wake_owner_transport = None
    server._wake_owner_surface = ""
    try:
        started = _dispatch_sync({
            "id": "wake-1",
            "method": "wake.start",
            "params": {"surface": "gui", "session_id": "first-session"},
        }, transport=first)
        denied = _dispatch_sync({
            "id": "wake-2",
            "method": "wake.start",
            "params": {"surface": "tui", "session_id": "second-session"},
        }, transport=second)
        denied_stop = server.dispatch({
            "id": "wake-stop-2",
            "method": "wake.stop",
            "params": {},
        }, transport=second)
        denied_voice_stop = _dispatch_sync({
            "id": "voice-stop-2",
            "method": "voice.record",
            "params": {"action": "stop"},
        }, transport=second)

        assert started["result"]["started"] is True
        assert denied["result"] == {
            "started": False,
            "reason": "owned",
            "owner_surface": "gui",
        }
        assert denied_stop["result"] == {
            "stopped": False,
            "reason": "not_owner",
            "disabled_persisted": False,
        }
        assert denied_voice_stop["result"] == {
            "status": "busy",
            "reason": "wake_owned",
        }

        state["callback"]()
        assert emitted == [(
            "wake.detected",
            "first-session",
            {"phrase": "hey hermes", "profile": None, "start_new_session": True},
            first,
        )]
        assert state["paused"] is True

        voice_started = _dispatch_sync({
            "id": "voice-start-1",
            "method": "voice.record",
            "params": {"action": "start", "session_id": "first-session"},
        }, transport=first)
        assert voice_started["result"]["status"] == "recording"
        voice_callbacks["on_status"]("idle")
        assert state["paused"] is False

        stopped = server.dispatch({
            "id": "wake-stop-1",
            "method": "wake.stop",
            "params": {},
        }, transport=first)
        assert stopped["result"] == {
            "stopped": True,
            "reason": None,
            "disabled_persisted": False,
        }

        reclaimed = _dispatch_sync({
            "id": "wake-reclaim-2",
            "method": "wake.start",
            "params": {"surface": "tui", "session_id": "second-session"},
        }, transport=second)
        assert reclaimed["result"]["started"] is True
        assert state["owner"] is second

        state["callback"]()
        assert emitted[-1] == (
            "wake.detected",
            "second-session",
            {"phrase": "hey hermes", "profile": None, "start_new_session": True},
            second,
        )

        stopped_again = server.dispatch({
            "id": "wake-stop-2-after-reclaim",
            "method": "wake.stop",
            "params": {},
        }, transport=second)
        assert stopped_again["result"] == {
            "stopped": True,
            "reason": None,
            "disabled_persisted": False,
        }
    finally:
        server._wake_owner_transport = None
        server._wake_owner_surface = ""


def test_wake_toggle_persists_enabled_flag_only_on_explicit_gesture(monkeypatch):
    """The ear toggle / /wake on|off write wake_word.enabled; auto-arm never does."""
    from tools import wake_word

    config = {"enabled": False, "phrase": "hey hermes", "surface": "auto",
              "start_new_session": True}
    persisted = []

    def fake_persist(enabled):
        persisted.append(enabled)
        config["enabled"] = enabled
        return True

    monkeypatch.setattr(server, "_persist_wake_enabled", fake_persist)
    monkeypatch.setattr(wake_word, "load_wake_word_config", lambda: dict(config))
    monkeypatch.setattr(wake_word, "check_wake_word_requirements", lambda _cfg: {
        "available": True,
        "phrase": "hey hermes",
        "provider": "test",
        "hint": "",
    })
    listener = {"owner": None}
    monkeypatch.setattr(
        wake_word, "start_listening",
        lambda callback, *, owner, config, external_audio=False: listener.update(
            owner=owner, external_audio=bool(external_audio)
        ),
    )
    monkeypatch.setattr(
        wake_word, "stop_listening",
        lambda *, owner: listener["owner"] is owner and not listener.update(owner=None),
    )
    monkeypatch.setattr(wake_word, "owns_listener", lambda owner: listener["owner"] is owner)

    transport = types.SimpleNamespace(_closed=False)
    server._wake_owner_transport = None
    server._wake_owner_surface = ""
    try:
        # Passive auto-arm (no persist): refused, config untouched.
        passive = _dispatch_sync({
            "id": "wake-passive",
            "method": "wake.start",
            "params": {"surface": "gui"},
        }, transport=transport)
        assert passive["result"] == {"started": False, "reason": "disabled"}
        assert persisted == []

        # Explicit gesture: enables in config AND arms.
        clicked = _dispatch_sync({
            "id": "wake-click",
            "method": "wake.start",
            "params": {"surface": "gui", "persist": True},
        }, transport=transport)
        assert clicked["result"]["started"] is True
        assert clicked["result"]["enabled_persisted"] is True
        assert persisted == [True]

        # Explicit stop: disables in config.
        stopped = server.dispatch({
            "id": "wake-click-off",
            "method": "wake.stop",
            "params": {"persist": True},
        }, transport=transport)
        assert stopped["result"]["stopped"] is True
        assert stopped["result"]["disabled_persisted"] is True
        assert persisted == [True, False]

        # persist does NOT override an explicit surface scoping.
        config.update(enabled=True, surface="tui")
        scoped = _dispatch_sync({
            "id": "wake-scoped",
            "method": "wake.start",
            "params": {"surface": "gui", "persist": True},
        }, transport=transport)
        assert scoped["result"] == {"started": False, "reason": "disabled_for_surface"}
        assert persisted == [True, False]
    finally:
        server._wake_owner_transport = None
        server._wake_owner_surface = ""


def test_voice_record_start_forwards_max_recording_seconds(monkeypatch):
    """voice.max_recording_seconds must reach start_continuous from the TUI.

    The CLI wiring alone doesn't cover TUI recordings: the gateway forwards
    recorder params explicitly, so a missing kwarg here silently leaves the
    cap dead in the TUI while CLI tests stay green. Semantics mirror the
    silence params: non-numeric / bool / missing falls back to the documented
    120 default, an explicit numeric value <= 0 disables the cap.
    """
    captured: dict = {}

    def fake_start_continuous(**kwargs):
        captured.update(kwargs)

    monkeypatch.setitem(
        sys.modules,
        "hermes_cli.voice",
        types.SimpleNamespace(
            start_continuous=fake_start_continuous, stop_continuous=lambda: None
        ),
    )
    monkeypatch.setenv("HERMES_VOICE", "1")

    for cfg, expected in (
        ({"max_recording_seconds": 45}, 45),        # explicit cap forwarded as-is
        ({"max_recording_seconds": 0}, 0.0),        # explicit 0 = disabled
        ({"max_recording_seconds": -5}, 0.0),       # negative = disabled
        ({}, 120.0),                                # missing = documented default
        ({"max_recording_seconds": True}, 120.0),   # bool must not become 1s cap
        ({"max_recording_seconds": "long"}, 120.0), # garbage = documented default
    ):
        captured.clear()
        monkeypatch.setattr(server, "_load_cfg", lambda c=cfg: {"voice": c})

        resp = _dispatch_sync(
            {
                "id": "voice-record-cap",
                "method": "voice.record",
                "params": {"action": "start"},
            }
        )

        assert "result" in resp, f"voice.record raised for cfg={cfg!r}: {resp.get('error')}"
        assert resp["result"]["status"] == "recording"
        assert (
            captured["max_recording_seconds"] == expected
        ), f"cfg={cfg!r} forwarded {captured.get('max_recording_seconds')!r}, expected {expected!r}"


def test_voice_record_start_cuts_inflight_tts(monkeypatch):
    """PTT barge-in (#40010): arming the mic cuts in-flight streaming TTS.

    The CLI record-key handler already cuts TTS before starting a capture;
    the gateway's ``voice.record`` start path did not, so a TUI/Desktop user
    pressing push-to-talk mid-reply kept hearing the agent talk over them.
    The cut must happen before ``start_continuous`` arms the mic, and must
    latch as a user barge (the next turn's model note), not a mode change.
    """
    order: list[str] = []
    tts_calls: list[bool] = []

    def fake_start_continuous(**_kwargs):
        order.append("start_continuous")
        return True

    monkeypatch.setitem(
        sys.modules,
        "hermes_cli.voice",
        types.SimpleNamespace(
            start_continuous=fake_start_continuous, stop_continuous=lambda **_kwargs: None
        ),
    )
    monkeypatch.setattr(server, "_load_cfg", lambda: {"voice": {}})
    monkeypatch.setattr(
        server, "_tts_stream_stop", lambda user_barge=True: tts_calls.append(user_barge)
    )
    monkeypatch.setenv("HERMES_VOICE", "1")

    resp = _dispatch_sync(
        {
            "id": "voice-record-tts-cut",
            "method": "voice.record",
            "params": {"action": "start"},
        }
    )

    assert resp is not None and "result" in resp, f"voice.record raised: {resp and resp.get('error')}"
    assert tts_calls == [True], "PTT start must cut TTS as a user barge"
    assert order == ["start_continuous"], "start_continuous must still arm the mic"


def test_voice_record_stop_forces_transcription(monkeypatch):
    captured: dict = {}

    def fake_stop_continuous(**kwargs):
        captured.update(kwargs)

    monkeypatch.setitem(
        sys.modules,
        "hermes_cli.voice",
        types.SimpleNamespace(
            start_continuous=lambda **_kwargs: None,
            stop_continuous=fake_stop_continuous,
        ),
    )

    resp = _dispatch_sync(
        {
            "id": "voice-record-stop",
            "method": "voice.record",
            "params": {"action": "stop"},
        }
    )

    assert resp["result"]["status"] == "stopped"
    assert captured["force_transcribe"] is True


def test_voice_record_stop_updates_event_session_id(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "hermes_cli.voice",
        types.SimpleNamespace(
            start_continuous=lambda **_kwargs: True,
            stop_continuous=lambda **_kwargs: None,
        ),
    )
    monkeypatch.setattr(server, "_voice_event_sid", "old-session")

    resp = _dispatch_sync(
        {
            "id": "voice-record-stop-session",
            "method": "voice.record",
            "params": {"action": "stop", "session_id": "new-session"},
        }
    )

    assert resp["result"]["status"] == "stopped"
    assert server._voice_event_sid == "new-session"


def test_voice_record_start_reports_busy_when_stop_is_in_progress(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "hermes_cli.voice",
        types.SimpleNamespace(
            start_continuous=lambda **_kwargs: False,
            stop_continuous=lambda **_kwargs: None,
        ),
    )
    monkeypatch.setenv("HERMES_VOICE", "1")
    monkeypatch.setattr(server, "_load_cfg", lambda: {"voice": {}})

    resp = _dispatch_sync(
        {
            "id": "voice-record-busy",
            "method": "voice.record",
            "params": {"action": "start"},
        }
    )

    assert resp["result"]["status"] == "busy"


def test_voice_toggle_tts_branch_also_carries_record_key(monkeypatch):
    """Round-2 Copilot review regression on #19835.

    The ``tts`` branch used to omit ``record_key`` from its response, so a
    TUI client would parse ``r.record_key ?? 'ctrl+b'`` and reset a
    custom binding to the default on every TTS toggle. Every branch of
    ``voice.toggle`` now carries the configured key so frontend state
    stays authoritative.
    """
    monkeypatch.setattr(
        server,
        "_load_cfg",
        lambda: {"voice": {"record_key": "ctrl+space"}},
    )
    monkeypatch.setitem(
        sys.modules,
        "tools.voice_mode",
        types.SimpleNamespace(
            check_voice_requirements=lambda: {"available": True, "details": ""}
        ),
    )
    monkeypatch.setenv("HERMES_VOICE", "1")
    # setenv (not delenv) — the handler writes HERMES_VOICE_TTS directly, and
    # delenv on an absent var registers no teardown, leaking TTS=1 into every
    # later test in the file (which now spins up the streaming TTS pipeline).
    monkeypatch.setenv("HERMES_VOICE_TTS", "0")

    tts_resp = _dispatch_sync(
        {"id": "voice-tts", "method": "voice.toggle", "params": {"action": "tts"}}
    )

    assert tts_resp["result"]["record_key"] == "ctrl+space"
    assert tts_resp["result"]["tts"] is True


def test_load_enabled_toolsets_prefers_tui_env(monkeypatch):
    monkeypatch.setenv("HERMES_TUI_TOOLSETS", "web, terminal, ,memory")

    assert server._load_enabled_toolsets() == ["web", "terminal", "memory"]


def test_load_enabled_toolsets_filters_invalid_tui_env(monkeypatch, capsys):
    monkeypatch.setenv("HERMES_TUI_TOOLSETS", "web, nope")
    monkeypatch.setitem(
        sys.modules,
        "hermes_cli.plugins",
        types.SimpleNamespace(discover_plugins=lambda: None),
    )

    assert server._load_enabled_toolsets() == ["web"]
    assert "nope" in capsys.readouterr().err


def test_load_enabled_toolsets_accepts_plugin_env_after_discovery(monkeypatch):
    monkeypatch.setenv("HERMES_TUI_TOOLSETS", "plugin_demo")

    import toolsets

    discovered = {"ready": False}
    original_validate = toolsets.validate_toolset

    def fake_validate(name):
        return name == "plugin_demo" and discovered["ready"] or original_validate(name)

    monkeypatch.setattr(toolsets, "validate_toolset", fake_validate)
    monkeypatch.setitem(
        sys.modules,
        "hermes_cli.plugins",
        types.SimpleNamespace(
            discover_plugins=lambda: discovered.update({"ready": True})
        ),
    )

    assert server._load_enabled_toolsets() == ["plugin_demo"]


def test_load_enabled_toolsets_folds_project_into_focus_posture(monkeypatch):
    # Focus-mode coding posture returns before the config fallback, but it's
    # still a GUI-only resolver — `project` must come along so the desktop keeps
    # the project tools while sitting in a repo.
    monkeypatch.delenv("HERMES_TUI_TOOLSETS", raising=False)

    import agent.coding_context as cc

    monkeypatch.setattr(cc, "coding_selection", lambda **_: ["coding", "figma"])

    assert server._load_enabled_toolsets("tui") == ["coding", "figma", "project"]


def test_load_enabled_toolsets_honors_disabled_project_on_focus_path(monkeypatch):
    """#54433: focus/coding posture must not re-add `project` when disabled."""
    monkeypatch.delenv("HERMES_TUI_TOOLSETS", raising=False)

    import agent.coding_context as cc

    monkeypatch.setattr(cc, "coding_selection", lambda **_: ["coding", "figma"])
    monkeypatch.setattr(server, "_load_disabled_toolsets", lambda: ["project"])

    result = server._load_enabled_toolsets("tui")
    assert result == ["coding", "figma"]
    assert "project" not in result


def test_load_enabled_toolsets_honors_disabled_project_on_configured_fallback(
    monkeypatch,
):
    """#54433: configured/fallback path must not re-add disabled `project`."""
    monkeypatch.delenv("HERMES_TUI_TOOLSETS", raising=False)

    import agent.coding_context as cc
    import hermes_cli.tools_config as tools_config_mod

    monkeypatch.setattr(cc, "coding_selection", lambda **_: None)
    monkeypatch.setattr(
        tools_config_mod,
        "_get_platform_tools",
        lambda *_args, **_kwargs: {"memory", "web"},
    )
    monkeypatch.setattr(server, "_load_disabled_toolsets", lambda: ["project"])

    result = server._load_enabled_toolsets("tui")
    assert result == ["memory", "web"]
    assert "project" not in result


def test_with_session_toolsets_keeps_desktop_ui_when_project_disabled(monkeypatch):
    """#54433: a disabled name is subtracted from the client-surface fold-in, but
    ``desktop_ui`` — the client's own control surface — survives the subtraction."""
    monkeypatch.setattr(server, "_load_disabled_toolsets", lambda: ["project"])

    assert server._with_session_toolsets(["memory"], "desktop") == [
        "memory",
        "desktop_ui",
    ]
    # Nothing disabled: the fold-in keeps both client-surface toolsets.
    monkeypatch.setattr(server, "_load_disabled_toolsets", lambda: None)
    assert server._with_session_toolsets(["memory"], "desktop") == [
        "memory",
        "desktop_ui",
        "project",
    ]


def test_load_enabled_toolsets_rejects_disabled_mcp_env(monkeypatch, capsys):
    monkeypatch.setenv("HERMES_TUI_TOOLSETS", "mcp-off")
    monkeypatch.setitem(
        sys.modules,
        "hermes_cli.plugins",
        types.SimpleNamespace(discover_plugins=lambda: None),
    )

    import hermes_cli.config as config_mod

    monkeypatch.setattr(
        config_mod,
        "read_raw_config",
        lambda: {"mcp_servers": {"mcp-off": {"enabled": False}}},
    )
    monkeypatch.setattr(
        config_mod, "load_config", lambda: {"platform_toolsets": {"cli": ["memory"]}}
    )

    # Sorted: ["memory", "project"]. `kanban` is a configurable opt-in and is
    # never recovered onto a saved list; `project` is GUI-only, folded in by
    # _load_enabled_toolsets. Toolsets inside their first release
    # (_RECENTLY_SHIPPED_TOOLSETS) are back-filled onto saved lists that never
    # offered them — allow those too.
    from hermes_cli.tools_config import _RECENTLY_SHIPPED_TOOLSETS

    result = server._load_enabled_toolsets()
    assert result is not None
    assert {"memory", "project"} <= set(result)
    assert "kanban" not in result
    assert set(result) - {"memory", "project"} <= _RECENTLY_SHIPPED_TOOLSETS
    err = capsys.readouterr().err
    assert "mcp-off" in err


def test_load_enabled_toolsets_falls_back_when_tui_env_invalid(monkeypatch, capsys):
    monkeypatch.setenv("HERMES_TUI_TOOLSETS", "nope")
    monkeypatch.setitem(
        sys.modules,
        "hermes_cli.plugins",
        types.SimpleNamespace(discover_plugins=lambda: None),
    )

    import hermes_cli.config as config_mod

    monkeypatch.setattr(
        config_mod, "load_config", lambda: {"platform_toolsets": {"cli": ["memory"]}}
    )

    from hermes_cli.tools_config import _RECENTLY_SHIPPED_TOOLSETS

    result = server._load_enabled_toolsets()
    assert result is not None
    assert {"memory", "project"} <= set(result)
    assert "kanban" not in result
    assert set(result) - {"memory", "project"} <= _RECENTLY_SHIPPED_TOOLSETS
    assert capsys.readouterr().err.strip()  # a fallback warning is printed


def test_load_enabled_toolsets_warns_when_config_fallback_fails(monkeypatch, capsys):
    monkeypatch.setenv("HERMES_TUI_TOOLSETS", "nope")
    monkeypatch.setitem(
        sys.modules,
        "hermes_cli.plugins",
        types.SimpleNamespace(discover_plugins=lambda: None),
    )

    import hermes_cli.config as config_mod

    monkeypatch.setattr(
        config_mod, "load_config", lambda: (_ for _ in ()).throw(RuntimeError("boom"))
    )

    assert server._load_enabled_toolsets() is None
    assert capsys.readouterr().err.strip()  # a warning is printed


def test_load_enabled_toolsets_honors_builtin_env_if_config_fails(monkeypatch):
    monkeypatch.setenv("HERMES_TUI_TOOLSETS", "web")

    import hermes_cli.config as config_mod

    monkeypatch.setattr(
        config_mod, "load_config", lambda: (_ for _ in ()).throw(RuntimeError("boom"))
    )

    assert server._load_enabled_toolsets() == ["web"]


def test_load_enabled_toolsets_all_env_means_all(monkeypatch):
    monkeypatch.setenv("HERMES_TUI_TOOLSETS", "all")

    assert server._load_enabled_toolsets() is None


def test_load_disabled_toolsets_reads_agent_config(monkeypatch):
    import hermes_cli.config as config_mod

    monkeypatch.setattr(
        config_mod,
        "load_config",
        lambda: {"agent": {"disabled_toolsets": ["browser"]}},
    )

    assert server._load_disabled_toolsets() == ["browser"]


def test_load_disabled_toolsets_none_when_unset_or_config_fails(monkeypatch):
    import hermes_cli.config as config_mod

    monkeypatch.setattr(config_mod, "load_config", lambda: {"agent": {"disabled_toolsets": []}})
    assert server._load_disabled_toolsets() is None

    monkeypatch.setattr(config_mod, "load_config", lambda: {})
    assert server._load_disabled_toolsets() is None

    monkeypatch.setattr(
        config_mod, "load_config", lambda: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    assert server._load_disabled_toolsets() is None


def test_load_enabled_toolsets_reports_disabled_mcp_separately(monkeypatch, capsys):
    monkeypatch.setenv("HERMES_TUI_TOOLSETS", "web,mcp-off,nope")
    monkeypatch.setitem(
        sys.modules,
        "hermes_cli.plugins",
        types.SimpleNamespace(discover_plugins=lambda: None),
    )

    import hermes_cli.config as config_mod

    monkeypatch.setattr(
        config_mod,
        "read_raw_config",
        lambda: {"mcp_servers": {"mcp-off": {"enabled": False}}},
    )

    assert server._load_enabled_toolsets() == ["web"]
    err = capsys.readouterr().err
    assert "nope" in err
    assert "mcp-off" in err


def test_history_to_messages_preserves_tool_calls_for_resume_display():
    history = [
        {"role": "user", "content": "first prompt"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_1",
                    "function": {
                        "name": "search_files",
                        "arguments": json.dumps({"pattern": "resume"}),
                    },
                }
            ],
        },
        {"role": "tool", "content": "{}", "tool_call_id": "call_1"},
        {"role": "assistant", "content": "first answer"},
        {"role": "user", "content": "second prompt"},
    ]

    assert server._history_to_messages(history) == [
        {"role": "user", "text": "first prompt"},
        {
            "args": {"pattern": "resume"},
            "context": "resume",
            "name": "search_files",
            "role": "tool",
            "tool_call_id": history[2]["tool_call_id"],
        },
        {"role": "assistant", "text": "first answer"},
        {"role": "user", "text": "second prompt"},
    ]


def test_history_to_messages_types_the_failed_turn_boundary_for_resume():
    """Desktop keys the failed-turn boundary on ``display_kind`` (a room poller must not post it
    as the member's reply); rows written before the closer typed it are typed on read."""
    from agent.turn_failure_copy import FAILED_TURN_DISPLAY_KIND, FAILED_TURN_NOTICE, PARTIAL_FAILED_TURN_NOTICE

    history = [
        {"role": "user", "content": "a"},
        {"role": "assistant", "content": FAILED_TURN_NOTICE, "display_kind": FAILED_TURN_DISPLAY_KIND},
        {"role": "user", "content": "b"},
        {"role": "assistant", "content": PARTIAL_FAILED_TURN_NOTICE},  # legacy untyped row
        {"role": "user", "content": "c"},
        {"role": "assistant", "content": f"Quoting Hermes: {FAILED_TURN_NOTICE}"},  # a real reply
    ]

    assert [m.get("display_kind") for m in server._history_to_messages(history)] == [
        None, FAILED_TURN_DISPLAY_KIND, None, FAILED_TURN_DISPLAY_KIND, None, None,
    ]


def test_history_to_messages_drops_pure_compaction_scaffolding():
    from agent.context_compressor import (
        HISTORICAL_TASK_HEADING,
        SUMMARY_PREFIX,
        _SUMMARY_END_MARKER,
    )

    summary = (
        f"{SUMMARY_PREFIX}\n\n"
        f"{HISTORICAL_TASK_HEADING}\nold work\n\n"
        f"{_SUMMARY_END_MARKER}"
    )

    assert server._history_to_messages(
        [
            {"role": "user", "content": summary},
            {"role": "assistant", "content": "real answer"},
        ]
    ) == [{"role": "assistant", "text": "real answer"}]


def test_history_to_messages_preserves_live_ask_without_compaction_scaffolding():
    from agent.context_compressor import (
        HISTORICAL_TASK_HEADING,
        SUMMARY_PREFIX,
        _SUMMARY_END_MARKER,
    )

    carrier = (
        f"{SUMMARY_PREFIX}\n\n"
        f"{HISTORICAL_TASK_HEADING}\nold work\n\n"
        f"{_SUMMARY_END_MARKER}\n\n"
        "test the browser controller"
    )

    assert server._history_to_messages(
        [
            {
                "role": "user",
                "content": carrier,
                "tool_calls": [{"id": "stale"}],
                "reasoning": "internal compaction reasoning",
            }
        ]
    ) == [{"role": "user", "text": "test the browser controller"}]


def test_history_to_messages_unwraps_merged_assistant_carrier():
    from agent.context_compressor import (
        HISTORICAL_TASK_HEADING,
        SUMMARY_PREFIX,
        _MERGED_PRIOR_CONTEXT_HEADER,
        _MERGED_SUMMARY_DELIMITER,
        _SUMMARY_END_MARKER,
    )

    carrier = (
        f"{_MERGED_PRIOR_CONTEXT_HEADER}\n"
        "real completed answer\n\n"
        f"{_MERGED_SUMMARY_DELIMITER}\n\n"
        f"{SUMMARY_PREFIX}\n\n"
        f"{HISTORICAL_TASK_HEADING}\nold work\n\n"
        f"{_SUMMARY_END_MARKER}"
    )

    assert server._history_to_messages(
        [
            {
                "role": "assistant",
                "content": carrier,
                "tool_calls": [{"id": "stale"}],
                "reasoning_details": [{"summary": "internal"}],
            }
        ]
    ) == [{"role": "assistant", "text": "real completed answer"}]


def test_history_to_messages_ships_full_tool_args():
    # This is the display projection. `context` is an 80-char preview for
    # collapsed row titles. A renderer that shows the full call (the expanded
    # `$` transcript in the desktop) rebuilds it from `args`. When the
    # projection dropped the args, the preview truncation was permanent.
    long_command = "echo " + "x" * 200
    history = [
        {"role": "user", "content": "run it"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_1",
                    "function": {
                        "name": "terminal",
                        "arguments": json.dumps({"command": long_command}),
                    },
                }
            ],
        },
        {"role": "tool", "content": "{}", "tool_call_id": "call_1"},
    ]

    rows = server._history_to_messages(history)
    assert rows[1]["args"] == {"command": long_command}
    # The preview stays alongside for the collapsed title.
    assert rows[1]["context"]

    # A tool row with no recorded args keeps the old small shape.
    argless = server._history_to_messages(
        [{"role": "tool", "content": "{}", "tool_call_id": "missing"}]
    )
    assert "args" not in argless[0]


def test_tool_start_ships_full_args(monkeypatch):
    # The desktop rebuilds the expanded row's `$` transcript from args. When
    # only the 80-char `context` preview shipped, the expanded command was
    # truncated until tool.complete. tool.complete already ships full args to
    # every client, so tool.start does too. There is no per-client gate.
    events: list[tuple[str, str, dict]] = []
    monkeypatch.setattr(
        server, "_emit", lambda event_type, sid, payload: events.append((event_type, sid, payload))
    )
    long_command = "echo " + "y" * 200
    monkeypatch.setitem(
        server._sessions,
        "args-test",
        {"source": "desktop", "tool_progress_mode": "all", "tool_started_at": {}},
    )

    server._on_tool_start("args-test", "tool-1", "terminal", {"command": long_command})
    server._on_tool_start("args-test", "tool-2", "terminal", {})

    assert events[0][2]["args"] == {"command": long_command}
    # Empty args stay omitted. Argless tools get no noise key.
    assert "args" not in events[1][2]
