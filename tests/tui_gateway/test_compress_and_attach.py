"""tui_gateway.server — model switching, history compression and file/image attachments.

Split from test_tui_gateway_server.py; shared fixtures and helpers live
in tests/tui_gateway/_server_test_helpers.py.
"""

import os
import sys
import threading
import types
from pathlib import Path
from unittest.mock import patch
from tui_gateway import server

from tests.tui_gateway._server_test_helpers import (
    _ImmediateThread,
    _neuter_agent_prewarm_timer,  # autouse
    _reap_leaked_notification_pollers,  # autouse
    _session,
)


def test_config_set_model_explicit_provider_surfaces_selected_provider_errors(monkeypatch):
    seen = {"build": 0, "wait": 0}
    session = _session()
    session["agent"] = None
    server._sessions["sid"] = session
    monkeypatch.setattr(server, "_load_cfg", lambda: {"model": {"default": "broken/model", "provider": "openrouter"}})
    monkeypatch.setattr(server, "_start_agent_build", lambda *_args: seen.__setitem__("build", seen["build"] + 1))
    monkeypatch.setattr(server, "_wait_agent", lambda *_args: seen.__setitem__("wait", seen["wait"] + 1))

    def fake_runtime_provider(*, requested=None, **_kwargs):
        if requested is None:
            raise RuntimeError("broken default provider should not be initialized")
        if requested == "anthropic":
            raise RuntimeError("missing anthropic API key")
        raise RuntimeError(f"unexpected provider {requested}")

    monkeypatch.setattr("hermes_cli.runtime_provider.resolve_runtime_provider", fake_runtime_provider)

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "config.set",
                "params": {
                    "session_id": "sid",
                    "key": "model",
                    "value": "claude-sonnet-4.6 --provider anthropic",
                },
            }
        )

        assert resp["error"]["code"] == 5001
        assert "anthropic" in resp["error"]["message"].lower()
        assert "missing anthropic api key" in resp["error"]["message"].lower()
        assert seen["build"] == 0
        assert seen["wait"] == 0
    finally:
        server._sessions.pop("sid", None)


def test_config_set_model_does_not_leak_inference_provider_env(monkeypatch):
    """A /model switch must NOT mutate process-global env vars. The desktop /
    dashboard tui_gateway backend hosts every same-profile session in one
    process; writing HERMES_INFERENCE_PROVIDER on a switch leaked the new
    provider into every other live session's next agent rebuild. The switch
    must instead record a per-session override and leave shared env untouched.

    (Was test_config_set_model_syncs_inference_provider_env, which asserted the
    leaky env-sync contract that caused the cross-session contamination bug.)
    """

    class _Agent:
        provider = "openrouter"
        model = "old/model"
        base_url = ""
        api_key = "sk-or"

        def switch_model(self, **_kwargs):
            return None

    result = types.SimpleNamespace(
        success=True,
        new_model="claude-sonnet-4.6",
        target_provider="anthropic",
        api_key="sk-ant",
        base_url="https://api.anthropic.com",
        api_mode="anthropic_messages",
        warning_message="",
    )

    session = _session(agent=_Agent())
    server._sessions["sid"] = session
    monkeypatch.setenv("HERMES_INFERENCE_PROVIDER", "openrouter")
    monkeypatch.setattr(
        "hermes_cli.model_switch.switch_model", lambda **_kwargs: result
    )
    monkeypatch.setattr(server, "_restart_slash_worker", lambda sid, session: None)
    monkeypatch.setattr(server, "_emit", lambda *args, **kwargs: None)

    try:
        server.handle_request(
            {
                "id": "1",
                "method": "config.set",
                "params": {
                    "session_id": "sid",
                    "key": "model",
                    "value": "claude-sonnet-4.6 --provider anthropic",
                },
            }
        )

        # Shared process env is UNCHANGED (the contamination vector is gone).
        assert os.environ["HERMES_INFERENCE_PROVIDER"] == "openrouter"
        # The switch was recorded as a per-session override instead.
        assert session["model_override"]["provider"] == "anthropic"
        assert session["model_override"]["model"] == "claude-sonnet-4.6"
    finally:
        server._sessions.clear()


def test_config_set_model_records_per_session_override_not_env(monkeypatch):
    """Regression for #16857 via the per-session override (not env vars):
    /model must record the user's explicit provider on the session so a later
    /new (which rebuilds via _make_agent honoring model_override) honours that
    choice — WITHOUT writing process-global env vars that would leak into
    sibling sessions.

    (Was test_config_set_model_syncs_tui_provider_unconditionally.)
    """

    class _Agent:
        provider = "openrouter"
        model = "old/model"
        base_url = ""
        api_key = "sk-or"

        def switch_model(self, **_kwargs):
            return None

    result = types.SimpleNamespace(
        success=True,
        new_model="deepseek-v4-pro",
        target_provider="custom:xuanji",
        api_key="sk-xuanji",
        base_url="https://xuanji.example/v1",
        api_mode="chat_completions",
        warning_message="",
    )

    session = _session(agent=_Agent())
    server._sessions["sid"] = session
    monkeypatch.delenv("HERMES_TUI_PROVIDER", raising=False)
    monkeypatch.delenv("HERMES_INFERENCE_PROVIDER", raising=False)
    monkeypatch.setattr(
        "hermes_cli.model_switch.switch_model", lambda **_kwargs: result
    )
    monkeypatch.setattr(server, "_restart_slash_worker", lambda sid, session: None)
    monkeypatch.setattr(server, "_emit", lambda *args, **kwargs: None)

    try:
        server.handle_request(
            {
                "id": "1",
                "method": "config.set",
                "params": {
                    "session_id": "sid",
                    "key": "model",
                    "value": "deepseek-v4-pro --provider custom:xuanji",
                },
            }
        )

        # No process-global env mutation.
        assert "HERMES_TUI_PROVIDER" not in os.environ
        assert "HERMES_INFERENCE_PROVIDER" not in os.environ
        # The user's explicit provider + resolved endpoint live on the session,
        # carried into the next /new rebuild by _make_agent.
        override = session["model_override"]
        assert override["provider"] == "custom:xuanji"
        assert override["model"] == "deepseek-v4-pro"
        assert override["base_url"] == "https://xuanji.example/v1"
        assert override["api_key"] == "sk-xuanji"
        assert override["api_mode"] == "chat_completions"
    finally:
        server._sessions.clear()


def test_config_set_model_switches_agent_without_touching_env(monkeypatch):
    """A /model switch mutates the target session's agent in place and records
    a per-session override; it does NOT write HERMES_MODEL / HERMES_TUI_PROVIDER
    etc. into the shared process environment.

    (Was test_config_set_model_syncs_tui_provider_env.)
    """

    class Agent:
        model = "gpt-5.3-codex"
        provider = "openai-codex"
        base_url = ""
        api_key = ""
        session_id = "sid"
        _cached_system_prompt = "Model: gpt-5.3-codex\nProvider: openai-codex"

        def switch_model(self, **kwargs):
            self.model = kwargs["new_model"]
            self.provider = kwargs["new_provider"]

        def _build_system_prompt(self, _system_message=None):
            return f"Model: {self.model}\nProvider: {self.provider}"

    class SessionDB:
        def __init__(self):
            self.model_config = None
            self.system_prompt = None
            self.messages = []

        def get_session(self, _session_id):
            return {"model_config": self.model_config}

        def update_session_meta(self, _session_id, model_config_json, _model=None):
            self.model_config = model_config_json

        def update_system_prompt(self, _session_id, system_prompt):
            self.system_prompt = system_prompt

        def append_message(self, session_id, role, content=None, **_kwargs):
            self.messages.append(
                {"session_id": session_id, "role": role, "content": content}
            )

    agent = Agent()
    db = SessionDB()
    agent._session_db = db
    session = _session(agent=agent)
    server._sessions["sid"] = session
    monkeypatch.setenv("HERMES_TUI_PROVIDER", "openai-codex")
    monkeypatch.delenv("HERMES_MODEL", raising=False)
    monkeypatch.delenv("HERMES_INFERENCE_MODEL", raising=False)
    monkeypatch.setattr(server, "_restart_slash_worker", lambda sid, session: None)
    monkeypatch.setattr(server, "_emit", lambda *args, **kwargs: None)

    def fake_switch_model(**kwargs):
        return types.SimpleNamespace(
            success=True,
            new_model="anthropic/claude-sonnet-4.6",
            target_provider="anthropic",
            api_key="key",
            base_url="https://api.anthropic.com",
            api_mode="anthropic_messages",
            warning_message="",
        )

    monkeypatch.setattr("hermes_cli.model_switch.switch_model", fake_switch_model)

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "config.set",
                "params": {
                    "session_id": "sid",
                    "key": "model",
                    "value": "anthropic/claude-sonnet-4.6 --provider anthropic",
                },
            }
        )

        assert resp["result"]["value"] == "anthropic/claude-sonnet-4.6"
        # Agent switched in place...
        assert agent.model == "anthropic/claude-sonnet-4.6"
        assert agent.provider == "anthropic"
        # ...override recorded on the session...
        assert session["model_override"]["model"] == "anthropic/claude-sonnet-4.6"
        assert session["model_override"]["provider"] == "anthropic"
        # ...the persisted prompt snapshot tracks the new runtime identity too.
        # Without this, the next turn restored the old system prompt from the DB:
        # API calls went to the new model, but "what model are you?" still read
        # "Model: old/model" from the stored prompt.
        assert db.system_prompt == (
            "Model: anthropic/claude-sonnet-4.6\nProvider: anthropic"
        )
        assert agent._cached_system_prompt == db.system_prompt
        assert session["history"][-1]["role"] == "user"
        assert "changed to anthropic/claude-sonnet-4.6" in session["history"][-1]["content"]
        assert db.messages[-1] == {
            "session_id": "session-key",
            "role": "user",
            "content": session["history"][-1]["content"],
        }
        # ...and the shared process env was NOT touched.
        assert os.environ["HERMES_TUI_PROVIDER"] == "openai-codex"
        assert "HERMES_MODEL" not in os.environ
        assert "HERMES_INFERENCE_MODEL" not in os.environ
    finally:
        server._sessions.clear()


def test_config_set_model_once_keeps_env_and_records_restore(monkeypatch):
    class Agent:
        model = "old/model"
        provider = "openrouter"
        base_url = "https://openrouter.ai/api/v1"
        api_key = "sk-old"
        api_mode = "chat_completions"

        def switch_model(self, **kwargs):
            self.model = kwargs["new_model"]
            self.provider = kwargs["new_provider"]
            self.api_key = kwargs["api_key"]
            self.base_url = kwargs["base_url"]
            self.api_mode = kwargs["api_mode"]

    result = types.SimpleNamespace(
        success=True,
        new_model="claude-sonnet-4.6",
        target_provider="anthropic",
        api_key="sk-ant",
        base_url="https://api.anthropic.com",
        api_mode="anthropic_messages",
        warning_message="",
    )
    seen = {}
    agent = Agent()
    session = _session(agent=agent)
    server._sessions["sid"] = session
    monkeypatch.setenv("HERMES_INFERENCE_PROVIDER", "openrouter")
    monkeypatch.setenv("HERMES_MODEL", "old/model")
    monkeypatch.setattr(
        "hermes_cli.model_switch.switch_model",
        lambda **kwargs: seen.update(kwargs) or result,
    )
    monkeypatch.setattr(server, "_restart_slash_worker", lambda *args, **kwargs: None)
    monkeypatch.setattr(server, "_emit", lambda *args, **kwargs: None)

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "config.set",
                "params": {
                    "session_id": "sid",
                    "key": "model",
                    "value": "claude-sonnet-4.6 --provider anthropic --once",
                },
            }
        )

        assert resp["result"]["scope"] == "once"
        assert seen["is_global"] is False
        assert agent.model == "claude-sonnet-4.6"
        assert session["one_turn_model_restore"]["model"] == "old/model"
        assert os.environ["HERMES_INFERENCE_PROVIDER"] == "openrouter"
        assert os.environ["HERMES_MODEL"] == "old/model"
    finally:
        server._sessions.clear()


def test_config_set_model_once_requires_live_session(monkeypatch):
    monkeypatch.setattr(
        "hermes_cli.model_switch.switch_model",
        lambda **_: (_ for _ in ()).throw(AssertionError("switch should not run")),
    )

    resp = server.handle_request(
        {
            "id": "1",
            "method": "config.set",
            "params": {
                "key": "model",
                "value": "claude-sonnet-4.6 --provider anthropic --once",
            },
        }
    )

    assert resp["error"]["code"] == 5001


def test_config_set_model_sessionless_rejected(monkeypatch):
    """Sessionless config.set model must 4001 before _apply_model_switch.

    Missing session_id and a stale session_id miss both take the sessionless
    branch; unscoped values and legacy --global must be rejected the same way
    so a Desktop client cannot persist model.default before session.create.
    """
    called = {"n": 0}

    def boom(*a, **k):
        called["n"] += 1
        raise AssertionError("_apply_model_switch must not run")

    monkeypatch.setattr(server, "_apply_model_switch", boom)
    for value in ["some-model", "some-model --provider openai-codex --global"]:
        resp = server.handle_request({
            "id": "1", "method": "config.set",
            "params": {"key": "model", "value": value},
        })
        assert resp["error"]["code"] == 4001
        assert called["n"] == 0

    resp = server.handle_request({
        "id": "1", "method": "config.set",
        "params": {"session_id": "missing-sid", "key": "model", "value": "some-model --global"},
    })
    assert resp["error"]["code"] == 4001
    assert called["n"] == 0


def test_config_set_model_live_session_still_applies_switch(monkeypatch):
    """CONTROL: a live session still reaches _apply_model_switch, including --global."""
    called = {"raw": []}

    def fake_apply(sid, session, raw, **_kwargs):
        called["raw"].append(raw)
        return {"value": "some-model", "warning": "", "scope": "global"}

    server._sessions["sid"] = _session()
    monkeypatch.setattr(server, "_apply_model_switch", fake_apply)
    try:
        resp = server.handle_request({
            "id": "1", "method": "config.set",
            "params": {
                "session_id": "sid",
                "key": "model",
                "value": "some-model --provider openai-codex --global",
            },
        })
        assert "error" not in resp
        assert called["raw"] == ["some-model --provider openai-codex --global"]
    finally:
        server._sessions.pop("sid", None)


def test_config_set_model_session_switch_clears_pending_once_restore(monkeypatch):
    class Agent:
        model = "temp/model"
        provider = "anthropic"
        base_url = "https://api.anthropic.com"
        api_key = "sk-temp"
        api_mode = "anthropic_messages"

        def switch_model(self, **kwargs):
            self.model = kwargs["new_model"]
            self.provider = kwargs["new_provider"]
            self.api_key = kwargs["api_key"]
            self.base_url = kwargs["base_url"]
            self.api_mode = kwargs["api_mode"]

    result = types.SimpleNamespace(
        success=True,
        new_model="new/model",
        target_provider="openrouter",
        api_key="sk-new",
        base_url="https://openrouter.ai/api/v1",
        api_mode="chat_completions",
        warning_message="",
    )
    session = _session(agent=Agent())
    session["one_turn_model_restore"] = {"model": "old/model"}
    server._sessions["sid"] = session
    monkeypatch.setattr("hermes_cli.model_switch.switch_model", lambda **_kwargs: result)
    monkeypatch.setattr(server, "_restart_slash_worker", lambda *args, **kwargs: None)
    monkeypatch.setattr(server, "_emit", lambda *args, **kwargs: None)

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "config.set",
                "params": {
                    "session_id": "sid",
                    "key": "model",
                    "value": "new/model --provider openrouter --session",
                },
            }
        )

        assert resp["result"]["scope"] == "session"
        assert "one_turn_model_restore" not in session
    finally:
        server._sessions.clear()


def test_restore_agent_model_runtime_falls_back_to_switch_model():
    class Agent:
        model = "temp/model"
        provider = "anthropic"
        base_url = "https://api.anthropic.com"
        api_key = "sk-temp"
        api_mode = "anthropic_messages"

        def switch_model(self, **kwargs):
            self.model = kwargs["new_model"]
            self.provider = kwargs["new_provider"]
            self.api_key = kwargs["api_key"]
            self.base_url = kwargs["base_url"]
            self.api_mode = kwargs["api_mode"]

    agent = Agent()

    server._restore_agent_model_runtime(
        agent,
        {
            "model": "old/model",
            "provider": "openrouter",
            "api_key": "sk-old",
            "base_url": "https://openrouter.ai/api/v1",
            "api_mode": "chat_completions",
        },
    )

    assert agent.model == "old/model"
    assert agent.provider == "openrouter"
    assert agent.base_url == "https://openrouter.ai/api/v1"


def test_config_set_personality_rejects_unknown_name(monkeypatch):
    monkeypatch.setattr(
        server,
        "_available_personalities",
        lambda cfg=None: {"helpful": "You are helpful."},
    )
    resp = server.handle_request(
        {
            "id": "1",
            "method": "config.set",
            "params": {"key": "personality", "value": "bogus"},
        }
    )

    assert "error" in resp


def test_config_set_personality_preserves_history_and_returns_info(monkeypatch):
    agent = types.SimpleNamespace(
        ephemeral_system_prompt=None, _cached_system_prompt="old"
    )
    session = _session(
        agent=agent,
        history=[{"role": "user", "text": "hi"}],
        history_version=4,
    )
    emits = []
    writes = []

    server._sessions["sid"] = session
    monkeypatch.setattr(
        server,
        "_available_personalities",
        lambda cfg=None: {"helpful": "You are helpful."},
    )
    monkeypatch.setattr(
        server, "_session_info", lambda agent, *a: {"model": getattr(agent, "model", "?")}
    )
    monkeypatch.setattr(server, "_emit", lambda *args: emits.append(args))
    # Persistence now flows through the single owner (hermes_cli.personality),
    # never _write_config_key / agent.system_prompt.
    import hermes_cli.personality as personality_mod

    monkeypatch.setattr(
        personality_mod,
        "persist_personality",
        lambda name: writes.append(("display.personality", name)) or True,
    )
    monkeypatch.setattr(
        server,
        "_write_config_key",
        lambda path, value: writes.append((path, value)),
    )

    resp = server.handle_request(
        {
            "id": "1",
            "method": "config.set",
            "params": {"session_id": "sid", "key": "personality", "value": "helpful"},
        }
    )

    assert resp["result"]["history_reset"] is False
    assert resp["result"]["info"] == {"model": "?"}
    # History is preserved with a pivot marker appended
    assert len(session["history"]) == 2
    assert session["history"][0] == {"role": "user", "text": "hi"}
    assert session["history"][1]["role"] == "user"
    assert "personality" in session["history"][1]["content"].lower()
    assert "You are helpful." in session["history"][1]["content"]
    assert session["history_version"] == 5
    # Agent's system prompt was updated in-place; cached prompt untouched
    assert agent.ephemeral_system_prompt == "You are helpful."
    assert agent._cached_system_prompt == "old"
    assert ("session.info", "sid", {"model": "?"}) in emits
    assert ("display.personality", "helpful") in writes
    assert not any(path == "agent.system_prompt" for path, _ in writes)


def test_compress_session_history_passes_force():
    """_compress_session_history is manual-only (session.compress RPC, slash
    compress/compact, slash-worker mirror) — it must bypass the
    summary-failure cooldown via force=True, matching the CLI and gateway
    manual-compress handlers."""
    from unittest.mock import MagicMock

    agent = MagicMock()
    agent.context_compressor = None  # keep _get_usage on the simple path
    compressed = [{"role": "user", "content": "summary"}]
    agent._compress_context.return_value = (compressed, "")
    # Explicit non-lock-skip: MagicMock getattr would return a truthy mock.
    agent._compression_skipped_due_to_lock = False
    session = _session(
        agent=agent,
        history=[
            {"role": "user", "content": "one"},
            {"role": "assistant", "content": "two"},
            {"role": "user", "content": "three"},
            {"role": "assistant", "content": "four"},
        ],
    )

    removed, _usage = server._compress_session_history(session)

    assert removed == 3
    assert session["history"] == compressed
    assert agent._compress_context.call_args.kwargs.get("force") is True


def test_compress_session_history_works_when_auto_compaction_disabled():
    """compression.enabled: false disables *automatic* compaction only —
    manual /compress must still work on every TUI route (session.compress
    RPC, slash compress/compact, slash-worker mirror), all of which converge
    on _compress_session_history. Pin that the helper never gates on
    agent.compression_enabled (#64438)."""
    from unittest.mock import MagicMock

    agent = MagicMock()
    agent.compression_enabled = False
    agent.context_compressor = None  # keep _get_usage on the simple path
    compressed = [{"role": "user", "content": "summary"}]
    agent._compress_context.return_value = (compressed, "")
    # Explicit non-lock-skip: MagicMock getattr would return a truthy mock.
    agent._compression_skipped_due_to_lock = False
    session = _session(
        agent=agent,
        history=[
            {"role": "user", "content": "one"},
            {"role": "assistant", "content": "two"},
            {"role": "user", "content": "three"},
            {"role": "assistant", "content": "four"},
        ],
    )

    removed, _usage = server._compress_session_history(session)

    assert removed == 3
    assert session["history"] == compressed
    agent._compress_context.assert_called_once()
    assert agent._compress_context.call_args.kwargs.get("force") is True


def test_session_compress_uses_compress_helper(monkeypatch):
    agent = types.SimpleNamespace()
    server._sessions["sid"] = _session(agent=agent)

    monkeypatch.setattr(
        server,
        "_compress_session_history",
        lambda session, focus_topic=None, **_kw: (2, {"total": 42}),
    )
    monkeypatch.setattr(server, "_session_info", lambda _agent, *a: {"model": "x"})

    with patch("tui_gateway.server._emit") as emit:
        resp = server.handle_request(
            {"id": "1", "method": "session.compress", "params": {"session_id": "sid"}}
        )

    assert resp["result"]["removed"] == 2
    assert resp["result"]["usage"]["total"] == 42
    emit.assert_any_call("session.info", "sid", {"model": "x"})
    # Final status.update clears the pinned "compressing" indicator so the
    # status bar can revert to the neutral state when compaction finishes.
    emit.assert_any_call("status.update", "sid", {"kind": "status", "text": "ready"})


def test_session_compress_normalizes_messages_for_desktop_transcript(monkeypatch):
    history = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call-1",
                    "function": {"name": "read_file", "arguments": '{"path":"secret.txt"}'},
                }
            ],
        },
        {"role": "tool", "tool_call_id": "call-1", "content": "very sensitive tool output"},
    ]
    agent = types.SimpleNamespace()
    server._sessions["sid"] = _session(agent=agent, history=history)
    monkeypatch.setattr(server, "_compress_session_history", lambda *_args, **_kwargs: (0, {}))
    monkeypatch.setattr(server, "_session_info", lambda *_args: {})

    try:
        response = server.handle_request(
            {"id": "1", "method": "session.compress", "params": {"session_id": "sid"}}
        )
    finally:
        server._sessions.pop("sid", None)

    assert response["result"]["messages"] == server._history_to_messages(history)
    assert "very sensitive tool output" not in str(response["result"]["messages"])


def test_session_compress_returns_compute_host_history(monkeypatch):
    session = _session(agent=None, _compute_host_active=True)
    server._sessions["sid"] = session
    ack = {
        "type": "control.ack",
        "output": "Compressed 4 → 2 messages",
        "messages": [{"role": "user", "content": "compressed context"}],
        "session_info": {"usage": {"total": 42}},
    }
    monkeypatch.setattr(server, "_session_uses_compute_host", lambda _session: True)
    monkeypatch.setattr(server, "_send_compute_host_control", lambda *args, **kwargs: ack)

    try:
        resp = server.handle_request(
            {"id": "1", "method": "session.compress", "params": {"session_id": "sid"}}
        )
    finally:
        server._sessions.pop("sid", None)

    assert resp["result"] == {
        "status": "compressed",
        "turn_isolation": True,
        "host_ack": {key: value for key, value in ack.items() if key != "messages"},
        "info": {"usage": {"total": 42}},
        "messages": [{"role": "user", "text": "compressed context"}],
        "usage": {"total": 42},
    }


def test_session_compress_forwards_config_ceiling_budget_to_compute_host(monkeypatch):
    session = _session(agent=None, _compute_host_active=True)
    server._sessions["sid"] = session
    calls = []

    def send_control(*args, **kwargs):
        calls.append((args, kwargs))
        return {
            "type": "control.ack",
            "result": {
                "status": "compressed",
                "messages": [],
                "removed": 0,
                "summary": {"headline": "Already compressed", "noop": True},
            },
        }

    monkeypatch.setattr(server, "_session_uses_compute_host", lambda _session: True)
    monkeypatch.setattr(server, "_send_compute_host_control", send_control)
    monkeypatch.setattr(
        server, "_load_cfg", lambda: {"compression": {"context_total_ceiling_seconds": 300}}
    )

    try:
        resp = server.handle_request(
            {"id": "1", "method": "session.compress", "params": {"session_id": "sid"}}
        )
    finally:
        server._sessions.pop("sid", None)

    assert resp["result"]["status"] == "compressed"
    assert len(calls) == 1
    (sid_arg,), kwargs = calls[0]
    assert sid_arg == "sid"
    assert kwargs["route_name"] == "session.compress"
    assert kwargs["command"] == "/compress"
    assert kwargs["wait"] is True
    # #97948: the waiter follows compression.context_total_ceiling_seconds
    # (+30s slack) instead of a hard-coded 120s, and registers a late-ack
    # handler so a compress that outlives it is still adopted.
    assert kwargs["timeout"] == 330.0
    assert callable(kwargs["on_late_ack"])


def test_session_compress_preserves_compute_host_aborted_summary(monkeypatch):
    session = _session(agent=None, _compute_host_active=True)
    server._sessions["sid"] = session
    result = {
        "status": "aborted",
        "messages": [{"role": "user", "content": "preserved context"}],
        "removed": 0,
        "summary": {
            "aborted": True,
            "headline": "Compression aborted: 6 messages preserved",
            "note": "No compression provider is configured.",
        },
    }
    monkeypatch.setattr(server, "_session_uses_compute_host", lambda _session: True)
    monkeypatch.setattr(
        server,
        "_send_compute_host_control",
        lambda *args, **kwargs: {
            "type": "control.ack",
            "result": result,
            "session_key": "rotated-host-key",
            "history_version": 7,
            "message_count": 1,
            "session_info": {"model": "host-model"},
        },
    )

    try:
        resp = server.handle_request(
            {"id": "1", "method": "session.compress", "params": {"session_id": "sid"}}
        )
    finally:
        server._sessions.pop("sid", None)

    assert resp["result"] == {**result, "turn_isolation": True}
    assert session["session_key"] == "rotated-host-key"
    assert session["history_version"] == 7
    assert session["_metadata_message_count"] == 1
    assert session["_metadata_mirror"]["model"] == "host-model"


def test_session_compress_reports_aborted_summary_without_success(monkeypatch):
    compression_state = types.SimpleNamespace(
        _last_compress_aborted=True,
        _last_summary_fallback_used=False,
        _last_summary_error=(
            "Provider 'opencode-zen' is set in config.yaml but no API key was found."
        ),
    )
    agent = types.SimpleNamespace(
        context_compressor=compression_state,
        _cached_system_prompt="",
        tools=None,
    )
    history = [{"role": "user", "content": f"m{i}"} for i in range(6)]
    server._sessions["sid"] = _session(agent=agent, history=history)

    monkeypatch.setattr(
        server,
        "_compress_session_history",
        lambda session, focus_topic=None, **_kw: (0, {"total": 42}),
    )
    monkeypatch.setattr(server, "_session_info", lambda _agent, *a: {"model": "x"})

    try:
        with patch("tui_gateway.server._emit"):
            resp = server.handle_request(
                {
                    "id": "1",
                    "method": "session.compress",
                    "params": {"session_id": "sid"},
                }
            )

        result = resp["result"]
        assert result["status"] == "aborted"
        assert result["removed"] == 0
        assert result["summary"]["aborted"] is True
        assert "no API key was found" in result["summary"]["note"]
        assert "Compressed:" not in result["summary"]["headline"]
    finally:
        server._sessions.pop("sid", None)


def test_session_compress_syncs_session_key_after_rotation(monkeypatch):
    """LCM notification follows the TUI's final session-key transition."""
    from agent.conversation_compression import (
        _queue_context_engine_compression_notification,
    )

    events = []
    agent = types.SimpleNamespace(
        session_id="rotated-id",
        context_compressor=types.SimpleNamespace(
            on_session_start=lambda *_args, **_kwargs: events.append("notify")
        ),
    )
    server._sessions["sid"] = _session(agent=agent)
    server._sessions["sid"]["session_key"] = "old-key"
    server._sessions["sid"]["pending_title"] = "stale title"

    def _compress(session, focus_topic=None, **_kw):
        _queue_context_engine_compression_notification(
            session["agent"],
            new_session_id="rotated-id",
            old_session_id="old-key",
        )
        return 2, {"total": 42}

    monkeypatch.setattr(server, "_compress_session_history", _compress)
    monkeypatch.setattr(server, "_session_info", lambda _agent, *a: {"model": "x"})
    restart_calls = []
    monkeypatch.setattr(
        server,
        "_restart_slash_worker",
        lambda sid, s: (restart_calls.append(s), events.append("sync")),
    )

    try:
        with patch("tui_gateway.server._emit"):
            server.handle_request(
                {
                    "id": "1",
                    "method": "session.compress",
                    "params": {"session_id": "sid"},
                }
            )

        assert server._sessions["sid"]["session_key"] == "rotated-id"
        assert server._sessions["sid"]["pending_title"] is None
        assert len(restart_calls) == 1
        assert events == ["sync", "notify"]
    finally:
        server._sessions.pop("sid", None)


def test_session_compress_sync_failure_discards_lcm_notification(monkeypatch):
    from agent.conversation_compression import (
        _queue_context_engine_compression_notification,
    )

    events = []
    agent = types.SimpleNamespace(
        session_id="rotated-id",
        context_compressor=types.SimpleNamespace(
            on_session_start=lambda *_args, **_kwargs: events.append("notify")
        ),
    )
    server._sessions["sid"] = _session(agent=agent)
    server._sessions["sid"]["session_key"] = "old-key"

    def _compress(session, focus_topic=None, **_kw):
        _queue_context_engine_compression_notification(
            session["agent"],
            new_session_id="rotated-id",
            old_session_id="old-key",
        )
        return 2, {"total": 42}

    monkeypatch.setattr(server, "_compress_session_history", _compress)
    monkeypatch.setattr(
        server,
        "_session_info",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("finalization failed")),
    )

    try:
        with patch("tui_gateway.server._emit"):
            resp = server.handle_request(
                {
                    "id": "1",
                    "method": "session.compress",
                    "params": {"session_id": "sid"},
                }
            )
        assert resp["error"]["code"] == 5005
        assert events == []
    finally:
        server._sessions.pop("sid", None)


def test_slash_exec_r7_read_commands_use_metadata_mirror_flag_on(monkeypatch):
    class _ExplodingWorker:
        def __init__(self, *args, **kwargs):
            raise AssertionError("slash worker should not run for isolated read commands")

    history_from_db = [
        {"role": "user", "content": "live question from state db"},
        {"role": "assistant", "content": "live answer from state db"},
    ]

    class _DB:
        def get_session(self, key):
            assert key == "session-key"
            return {
                "title": "Live title",
                "started_at": 1_700_000_000,
                "updated_at": 1_700_000_060,
                "pinned": True,
            }

        def get_resume_conversations(self, session_id):
            return (
                self.get_messages_as_conversation(session_id, repair_alternation=True),
                self.get_messages_as_conversation(session_id, include_ancestors=True),
            )

        def get_ancestor_display_prefix(self, _sid):
            return []

        def get_messages_as_conversation(self, key, include_ancestors=True, repair_alternation=False, **_kwargs):
            assert key == "session-key"
            assert include_ancestors is True
            return list(history_from_db)

    server._sessions["sid"] = _session(
        agent=None,
        history=[{"role": "user", "content": "stale parent mirror"}],
        _compute_host_active=True,
        _metadata_mirror={
            "model": "host-model",
            "provider": "host-provider",
            "system_prompt": "host system prompt",
            "tools": {"core": ["terminal", "read_file"]},
            "usage": {
                "model": "host-model",
                "input": 100,
                "output": 20,
                "reasoning": 5,
                "prompt": 120,
                "completion": 20,
                "total": 140,
                "calls": 2,
                "context_used": 80,
                "context_max": 1000,
                "context_percent": 8,
                "compressions": 1,
            },
        },
        _metadata_message_count=2,
    )
    monkeypatch.setattr(server, "_SlashWorker", _ExplodingWorker)
    monkeypatch.setattr(server, "_get_db", lambda: _DB())
    monkeypatch.setattr(server, "_load_cfg", lambda: {"dashboard": {"turn_isolation": True}})

    cases = {
        "usage": "140",
        "history": "live question from state db",
        "prompt": "host system prompt",
        "status": "140",
        "context": "Context usage: 80 / 1,000 tokens",
        "tools": "terminal",
        "help": "/status",
    }

    try:
        for command, expected in cases.items():
            resp = server.handle_request(
                {
                    "id": command,
                    "method": "slash.exec",
                    "params": {"command": command, "session_id": "sid"},
                }
            )
            assert "result" in resp, (command, resp)
            assert expected in resp["result"]["output"]
            assert "stale parent mirror" not in resp["result"]["output"]
            assert "(._.)" not in resp["result"]["output"]
        mirrored_usage = server._sessions["sid"]["_metadata_mirror"]["usage"]
        for estimated in (True, False):
            mirrored_usage["context_estimated"] = estimated
            mirrored_usage["context_source"] = "local_estimate" if estimated else "provider_usage"
            response = server.handle_request({
                "id": "context-provenance", "method": "slash.exec",
                "params": {"command": "context", "session_id": "sid"},
            })
            mark = "~" if estimated else ""
            assert f"Context usage: {mark}80 / 1,000 tokens ({mark}8.0%)" in response["result"]["output"]
    finally:
        server._sessions.pop("sid", None)


def test_prompt_submit_sets_approval_session_key(monkeypatch):
    from tools.approval import get_current_session_key

    captured = {}

    class _Agent:
        def run_conversation(self, prompt, conversation_history=None, stream_callback=None, **_kwargs):
            captured["session_key"] = get_current_session_key(default="")
            return {
                "final_response": "ok",
                "messages": [{"role": "assistant", "content": "ok"}],
            }

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None, **_thread_options):
            self._target = target

        def start(self):
            self._target()

    server._sessions["sid"] = _session(agent=_Agent())
    monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)
    monkeypatch.setattr(server, "_emit", lambda *args, **kwargs: None)
    monkeypatch.setattr(server, "make_stream_renderer", lambda cols: None)
    monkeypatch.setattr(server, "render_message", lambda raw, cols: None)

    resp = server.handle_request(
        {
            "id": "1",
            "method": "prompt.submit",
            "params": {"session_id": "sid", "text": "ping"},
        }
    )

    assert resp["result"]["status"] == "streaming"
    assert captured["session_key"] == "session-key"


def test_prompt_submit_expands_context_refs(monkeypatch):
    captured = {}

    class _Agent:
        model = "test/model"
        base_url = ""
        api_key = ""

        def run_conversation(self, prompt, conversation_history=None, stream_callback=None, **_kwargs):
            captured["prompt"] = prompt
            return {
                "final_response": "ok",
                "messages": [{"role": "assistant", "content": "ok"}],
            }

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None, **_thread_options):
            self._target = target

        def start(self):
            self._target()

    fake_ctx = types.ModuleType("agent.context_references")
    fake_ctx.preprocess_context_references = (
        lambda message, **kwargs: types.SimpleNamespace(
            blocked=False,
            message="expanded prompt",
            warnings=[],
            references=[],
            injected_tokens=0,
        )
    )
    fake_meta = types.ModuleType("agent.model_metadata")
    fake_meta.get_model_context_length = lambda *args, **kwargs: 100000

    server._sessions["sid"] = _session(agent=_Agent())
    monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)
    monkeypatch.setattr(server, "_emit", lambda *args, **kwargs: None)
    monkeypatch.setattr(server, "make_stream_renderer", lambda cols: None)
    monkeypatch.setattr(server, "render_message", lambda raw, cols: None)
    monkeypatch.setitem(sys.modules, "agent.context_references", fake_ctx)
    monkeypatch.setitem(sys.modules, "agent.model_metadata", fake_meta)

    server.handle_request(
        {
            "id": "1",
            "method": "prompt.submit",
            "params": {"session_id": "sid", "text": "@diff"},
        }
    )

    assert captured["prompt"] == "expanded prompt"


def test_image_attach_appends_local_image(monkeypatch):
    fake_cli = types.ModuleType("cli")
    fake_cli._IMAGE_EXTENSIONS = {".png"}
    fake_cli._detect_file_drop = lambda raw: {
        "path": Path("/tmp/cat.png"),
        "is_image": True,
        "remainder": "",
    }
    fake_cli._split_path_input = lambda raw: (raw, "")
    fake_cli._resolve_attachment_path = lambda raw: Path("/tmp/cat.png")

    server._sessions["sid"] = _session()
    monkeypatch.setitem(sys.modules, "cli", fake_cli)

    resp = server.handle_request(
        {
            "id": "1",
            "method": "image.attach",
            "params": {"session_id": "sid", "path": "/tmp/cat.png"},
        }
    )

    assert resp["result"]["attached"] is True
    assert resp["result"]["name"] == "cat.png"
    assert len(server._sessions["sid"]["attached_images"]) == 1


def test_image_attach_accepts_unquoted_screenshot_path_with_spaces(monkeypatch):
    screenshot = Path("/tmp/Screenshot 2026-04-21 at 1.04.43 PM.png")
    fake_cli = types.ModuleType("cli")
    fake_cli._IMAGE_EXTENSIONS = {".png"}
    fake_cli._detect_file_drop = lambda raw: {
        "path": screenshot,
        "is_image": True,
        "remainder": "",
    }
    fake_cli._split_path_input = lambda raw: (
        "/tmp/Screenshot",
        "2026-04-21 at 1.04.43 PM.png",
    )
    fake_cli._resolve_attachment_path = lambda raw: None

    server._sessions["sid"] = _session()
    monkeypatch.setitem(sys.modules, "cli", fake_cli)

    resp = server.handle_request(
        {
            "id": "1",
            "method": "image.attach",
            "params": {"session_id": "sid", "path": str(screenshot)},
        }
    )

    assert resp["result"]["attached"] is True
    assert resp["result"]["path"] == str(screenshot)
    assert resp["result"]["remainder"] == ""
    assert len(server._sessions["sid"]["attached_images"]) == 1


def test_file_attach_uploads_remote_file_into_session_workspace(monkeypatch, tmp_path):
    """Remote case: client path doesn't exist on gateway → decode data_url bytes.

    Staged into the session home's ``attachments/`` dir (bind-mounted into
    container backends) rather than the workspace (#76577).
    """
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    home = tmp_path / "home"
    fake_cli = types.ModuleType("cli")
    fake_cli._detect_file_drop = lambda raw: None
    fake_cli._split_path_input = lambda raw: (raw, "")
    fake_cli._resolve_attachment_path = lambda raw: None

    server._sessions["sid"] = _session(cwd=str(workspace), profile_home=str(home))
    monkeypatch.setitem(sys.modules, "cli", fake_cli)

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "file.attach",
                "params": {
                    "session_id": "sid",
                    "path": "/Users/alice/Downloads/report.txt",
                    "name": "report.txt",
                    "data_url": "data:text/plain;base64,aGVsbG8gd29ybGQ=",
                },
            }
        )

        stored = home / "attachments" / "report.txt"
        assert resp["result"]["attached"] is True
        assert resp["result"]["uploaded"] is True
        assert resp["result"]["path"] == str(stored)
        assert resp["result"]["ref_text"] == f"@file:{stored}"
        assert stored.read_text(encoding="utf-8") == "hello world"
    finally:
        server._sessions.pop("sid", None)


def test_file_attach_copies_gateway_visible_file_outside_workspace(monkeypatch, tmp_path):
    """Local case: gateway can see the file but it's outside the workspace → copy in."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    home = tmp_path / "home"
    source = tmp_path / "outside.txt"
    source.write_text("outside workspace", encoding="utf-8")
    fake_cli = types.ModuleType("cli")
    fake_cli._detect_file_drop = lambda raw: None
    fake_cli._split_path_input = lambda raw: (raw, "")
    fake_cli._resolve_attachment_path = lambda raw: source

    server._sessions["sid"] = _session(cwd=str(workspace), profile_home=str(home))
    monkeypatch.setitem(sys.modules, "cli", fake_cli)

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "file.attach",
                "params": {"session_id": "sid", "path": str(source)},
            }
        )

        stored = home / "attachments" / "outside.txt"
        assert resp["result"]["attached"] is True
        assert resp["result"]["uploaded"] is True
        assert resp["result"]["ref_text"] == f"@file:{stored}"
        assert stored.read_text(encoding="utf-8") == "outside workspace"
    finally:
        server._sessions.pop("sid", None)


def test_file_attach_uses_in_workspace_file_without_copying(monkeypatch, tmp_path):
    """Local case: file already inside the workspace → ref it directly, no copy."""
    workspace = tmp_path / "workspace"
    (workspace / "data").mkdir(parents=True)
    source = workspace / "data" / "exam.csv"
    source.write_text("a,b,c\n1,2,3\n", encoding="utf-8")
    fake_cli = types.ModuleType("cli")
    fake_cli._detect_file_drop = lambda raw: None
    fake_cli._split_path_input = lambda raw: (raw, "")
    fake_cli._resolve_attachment_path = lambda raw: source

    server._sessions["sid"] = _session(cwd=str(workspace))
    monkeypatch.setitem(sys.modules, "cli", fake_cli)

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "file.attach",
                "params": {"session_id": "sid", "path": str(source)},
            }
        )

        assert resp["result"]["attached"] is True
        assert resp["result"]["uploaded"] is False
        assert resp["result"]["ref_text"] == "@file:data/exam.csv"
        # No copy: nothing staged under desktop-attachments or the home
        # attachments dir.
        assert not (workspace / ".hermes" / "desktop-attachments").exists()
        assert not (tmp_path / "home" / "attachments").exists()
    finally:
        server._sessions.pop("sid", None)


def test_file_attach_errors_when_unresolvable_and_no_bytes(monkeypatch, tmp_path):
    """Remote path not on gateway and no data_url → actionable error, not a stage."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    fake_cli = types.ModuleType("cli")
    fake_cli._detect_file_drop = lambda raw: None
    fake_cli._split_path_input = lambda raw: (raw, "")
    fake_cli._resolve_attachment_path = lambda raw: None

    server._sessions["sid"] = _session(cwd=str(workspace))
    monkeypatch.setitem(sys.modules, "cli", fake_cli)

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "file.attach",
                "params": {"session_id": "sid", "path": "/Users/alice/missing.txt"},
            }
        )

        assert "error" in resp
    finally:
        server._sessions.pop("sid", None)


def test_file_attach_quotes_ref_with_spaces(monkeypatch, tmp_path):
    """Staged names with spaces must be backtick-quoted so the @file: ref parses."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    fake_cli = types.ModuleType("cli")
    fake_cli._detect_file_drop = lambda raw: None
    fake_cli._split_path_input = lambda raw: (raw, "")
    fake_cli._resolve_attachment_path = lambda raw: None

    server._sessions["sid"] = _session(cwd=str(workspace), profile_home=str(tmp_path / "home"))
    monkeypatch.setitem(sys.modules, "cli", fake_cli)

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "file.attach",
                "params": {
                    "session_id": "sid",
                    "name": "my exam schedule.csv",
                    "data_url": "data:text/csv;base64,YSxiCg==",
                },
            }
        )

        stored = tmp_path / "home" / "attachments" / "my exam schedule.csv"
        assert resp["result"]["attached"] is True
        assert resp["result"]["ref_text"] == f"@file:`{stored}`"
        assert stored.read_text(encoding="utf-8") == "a,b\n"
    finally:
        server._sessions.pop("sid", None)


def test_file_attach_workspace_storage_follows_the_owning_profiles_config(monkeypatch, tmp_path):
    """``attachments.storage: workspace`` is read from the SESSION's profile config.

    Opt-in profiles stage under ``<workspace>/.hermes/attachments`` (inside the
    allowed ref root, #110662); a profile without the opt-in keeps the
    bind-mounted ``<profile home>/attachments`` — one serve process, two homes,
    each session follows its own profile's config.
    """
    workspace_a = tmp_path / "work-a"
    workspace_a.mkdir()
    home_a = tmp_path / "home-a"
    home_a.mkdir()
    (home_a / "config.yaml").write_text("attachments:\n  storage: workspace\n", encoding="utf-8")

    def fake_resolve(raw):
        return None

    fake_cli = types.ModuleType("cli")
    fake_cli._detect_file_drop = lambda raw: None
    fake_cli._split_path_input = lambda raw: (raw, "")
    fake_cli._resolve_attachment_path = fake_resolve
    monkeypatch.setitem(sys.modules, "cli", fake_cli)

    def attach(sid: str, params: dict) -> dict:
        return server.handle_request(
            {"id": "1", "method": "file.attach", "params": {"session_id": sid, **params}}
        )

    try:
        server._sessions["sid-a"] = _session(cwd=str(workspace_a), profile_home=str(home_a))
        resp = attach(
            "sid-a",
            {
                "path": "/Users/alice/Downloads/report.txt",
                "name": "report.txt",
                "data_url": "data:text/plain;base64,aGVsbG8=",
            },
        )

        staged_a = workspace_a / ".hermes" / "attachments" / "report.txt"
        assert resp["result"]["attached"] is True
        assert resp["result"]["path"] == str(staged_a)
        assert staged_a.read_text(encoding="utf-8") == "hello"
        # Workspace staging lands inside the allowed ref root: the ref is
        # workspace-relative, not an absolute out-of-workspace path.
        assert resp["result"]["ref_text"] == "@file:.hermes/attachments/report.txt"
        assert not (home_a / "attachments").exists()

        # Same serve process, second profile WITHOUT the opt-in: staging stays
        # on that profile's hermes-home attachments dir.
        workspace_b = tmp_path / "work-b"
        workspace_b.mkdir()
        home_b = tmp_path / "home-b"
        home_b.mkdir()
        server._sessions["sid-b"] = _session(cwd=str(workspace_b), profile_home=str(home_b))
        resp = attach(
            "sid-b",
            {
                "path": "/Users/alice/Downloads/report.txt",
                "name": "report.txt",
                "data_url": "data:text/plain;base64,aGVsbG8=",
            },
        )

        staged_b = home_b / "attachments" / "report.txt"
        assert resp["result"]["path"] == str(staged_b)
        assert staged_b.read_text(encoding="utf-8") == "hello"
        assert not (workspace_b / ".hermes").exists()
    finally:
        server._sessions.pop("sid-a", None)
        server._sessions.pop("sid-b", None)
