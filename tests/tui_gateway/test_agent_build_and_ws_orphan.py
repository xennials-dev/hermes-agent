"""tui_gateway.server — model config sync, agent construction and ws-orphan reaping.

Split from test_tui_gateway_server.py; shared fixtures and helpers live
in tests/tui_gateway/_server_test_helpers.py.
"""

import subprocess
import threading
import time
import types
import pytest
from tui_gateway import server
from tui_gateway.transport import bind_transport, reset_transport

from tests.tui_gateway._server_test_helpers import (
    _LoginSocket,
    _capture_make_agent_kwargs,
    _login_session,
    _neuter_agent_prewarm_timer,  # autouse
    _patch_config_model,
    _reap_leaked_notification_pollers,  # autouse
    _session,
    _sync_test_session,
)


def test_config_sync_treats_auto_provider_as_unset(monkeypatch):
    _patch_config_model(monkeypatch, "new/model", provider="auto")
    session = _sync_test_session(config_model_seen=("old/model", ""))
    calls = []
    monkeypatch.setattr(
        server,
        "_apply_model_switch",
        lambda sid, sess, raw, **kw: calls.append(raw),
    )

    server._sync_agent_model_with_config("sid", session)

    assert calls == ["new/model"]


def test_config_sync_skips_session_pinned_by_model_command(monkeypatch):
    _patch_config_model(monkeypatch, "new/model")
    session = _sync_test_session(
        config_model_seen=("old/model", ""),
        model_override={"model": "pinned/model"},
    )
    monkeypatch.setattr(
        server,
        "_apply_model_switch",
        lambda *a, **k: pytest.fail("pinned session must not be switched"),
    )

    server._sync_agent_model_with_config("sid", session)


def test_config_sync_noop_when_config_unchanged(monkeypatch):
    _patch_config_model(monkeypatch, "old/model")
    session = _sync_test_session(config_model_seen=("old/model", ""))
    monkeypatch.setattr(
        server,
        "_apply_model_switch",
        lambda *a, **k: pytest.fail("unchanged config must not switch"),
    )

    server._sync_agent_model_with_config("sid", session)


def test_config_sync_adopts_baseline_when_agent_already_on_target(monkeypatch):
    # Branched/resumed sessions reach their first sync with no snapshot but
    # an agent already built from config; that must not trigger a switch.
    _patch_config_model(monkeypatch, "old/model")
    session = _sync_test_session()
    monkeypatch.setattr(
        server,
        "_apply_model_switch",
        lambda *a, **k: pytest.fail("agent already on target must not switch"),
    )

    server._sync_agent_model_with_config("sid", session)

    assert session["config_model_seen"] == ("old/model", "")


def test_config_sync_switches_when_only_provider_differs(monkeypatch):
    _patch_config_model(monkeypatch, "old/model", provider="nous")
    session = _sync_test_session(config_model_seen=("old/model", ""))
    calls = []
    monkeypatch.setattr(
        server,
        "_apply_model_switch",
        lambda sid, sess, raw, **kw: calls.append(raw),
    )

    server._sync_agent_model_with_config("sid", session)

    assert calls == ["old/model --provider nous"]


def test_config_sync_failure_emits_error_once_per_edit(monkeypatch):
    _patch_config_model(monkeypatch, "broken/model")
    session = _sync_test_session(config_model_seen=("old/model", ""))

    def boom(*a, **k):
        raise ValueError("no such model")

    monkeypatch.setattr(server, "_apply_model_switch", boom)
    emits = []
    monkeypatch.setattr(
        server, "_emit", lambda ev, sid, payload: emits.append((ev, payload))
    )

    server._sync_agent_model_with_config("sid", session)
    server._sync_agent_model_with_config("sid", session)

    assert len(emits) == 1
    assert emits[0][0] == "error"
    assert "broken/model" in emits[0][1]["message"]


def test_config_sync_config_wins_over_env_seed(monkeypatch):
    # Hosted instances set HERMES_INFERENCE_MODEL as a provision-time seed;
    # the per-turn sync must follow config.yaml edits, not stay pinned to it.
    monkeypatch.setenv("HERMES_INFERENCE_MODEL", "seed/model")
    monkeypatch.delenv("HERMES_MODEL", raising=False)
    monkeypatch.setattr(server, "_load_cfg", lambda: {"model": {"default": "new/model"}})
    session = _sync_test_session(config_model_seen=("seed/model", ""))
    calls = []
    monkeypatch.setattr(
        server,
        "_apply_model_switch",
        lambda sid, sess, raw, **kw: calls.append(raw),
    )

    server._sync_agent_model_with_config("sid", session)

    assert calls == ["new/model"]
    assert session["config_model_seen"] == ("new/model", "")


def test_config_sync_ignores_env_seed_without_config_model(monkeypatch):
    # `hermes --tui -m <model>` sets HERMES_MODEL/HERMES_INFERENCE_MODEL as a
    # launch-scoped seed. When config.yaml has NO model.default (typical
    # custom-provider-only setup), the sync must NOT adopt the env seed as a
    # config target — doing so replayed the -m flag as a /model switch and
    # (with persist_switch_by_default=True) wrote it into config.yaml
    # permanently.
    monkeypatch.setenv("HERMES_MODEL", "one-shot/model")
    monkeypatch.setenv("HERMES_INFERENCE_MODEL", "one-shot/model")
    monkeypatch.setattr(
        server, "_load_cfg", lambda: {"model": {"provider": "custom:mylocal"}}
    )
    session = _sync_test_session()
    monkeypatch.setattr(
        server,
        "_apply_model_switch",
        lambda *a, **k: pytest.fail("env seed must not trigger a config sync switch"),
    )

    server._sync_agent_model_with_config("sid", session)


def test_apply_model_switch_persist_override_false_never_persists(monkeypatch):
    # Internal callers (config sync, /moa one-shot + restore) pass
    # persist_override=False; even with persist_switch_by_default=True the
    # switch must not write config.yaml.
    import types as _types

    result = _types.SimpleNamespace(
        success=True,
        new_model="new/model",
        target_provider="nous",
        base_url="",
        api_key="key",
        api_mode="chat_completions",
        warning_message="",
        model_info=None,
        error_message="",
    )
    monkeypatch.setattr(
        "hermes_cli.model_switch.switch_model", lambda **kw: result
    )
    monkeypatch.setattr(
        "hermes_cli.model_switch.resolve_persist_behavior",
        lambda *a: pytest.fail("persist_override must bypass resolve_persist_behavior"),
    )
    monkeypatch.setattr(
        "hermes_cli.model_switch.persist_model_selection",
        lambda _r: pytest.fail("persist_override=False must not persist"),
    )
    monkeypatch.setattr(
        "hermes_cli.model_cost_guard.expensive_model_warning",
        lambda *a, **k: None,
    )
    session = {"agent": None}

    out = server._apply_model_switch(
        "sid", session, "new/model --provider nous", persist_override=False
    )

    assert out["value"] == "new/model"
    assert session["model_override"]["model"] == "new/model"


def test_startup_runtime_uses_tui_provider_env(monkeypatch):
    monkeypatch.setenv("HERMES_MODEL", "nous/hermes-test")
    monkeypatch.setenv("HERMES_TUI_PROVIDER", "nous")
    monkeypatch.delenv("HERMES_INFERENCE_PROVIDER", raising=False)

    assert server._resolve_startup_runtime() == ("nous/hermes-test", "nous")


def test_startup_runtime_does_not_treat_inference_provider_as_explicit(monkeypatch):
    monkeypatch.setenv("HERMES_MODEL", "nous/hermes-test")
    monkeypatch.delenv("HERMES_TUI_PROVIDER", raising=False)
    monkeypatch.setenv("HERMES_INFERENCE_PROVIDER", "nous")
    monkeypatch.setattr(
        "hermes_cli.models.detect_static_provider_for_model",
        lambda model, provider: None,
    )

    assert server._resolve_startup_runtime() == ("nous/hermes-test", None)


def test_load_fallback_model_merges_chain_providers_first(monkeypatch):
    # Parity with HermesCLI / gateway: fallback_providers stays first and keeps
    # its order, with any distinct legacy fallback_model entry merged in after
    # (deduped on provider/model/base_url).
    fallback_chain = [
        {"provider": "openrouter", "model": "openai/gpt-5.5"},
        {"provider": "anthropic", "model": "claude-sonnet-4-6"},
    ]
    monkeypatch.setattr(
        server,
        "_load_cfg",
        lambda: {
            "fallback_model": {"provider": "legacy", "model": "legacy-model"},
            "fallback_providers": fallback_chain,
        },
    )

    assert server._load_fallback_model() == [
        {"provider": "openrouter", "model": "openai/gpt-5.5"},
        {"provider": "anthropic", "model": "claude-sonnet-4-6"},
        {"provider": "legacy", "model": "legacy-model"},
    ]


def test_make_agent_passes_configured_fallback_chain(monkeypatch):
    captured = {}
    fallback_chain = [
        {"provider": "openrouter", "model": "openai/gpt-5.5"},
    ]

    def fake_agent(**kwargs):
        captured.update(kwargs)
        return types.SimpleNamespace(model=kwargs.get("model"))

    monkeypatch.delenv("HERMES_MODEL", raising=False)
    monkeypatch.delenv("HERMES_INFERENCE_MODEL", raising=False)
    monkeypatch.delenv("HERMES_TUI_PROVIDER", raising=False)
    monkeypatch.delenv("HERMES_DESKTOP", raising=False)
    monkeypatch.delenv("HERMES_DESKTOP_TERMINAL", raising=False)
    monkeypatch.setattr(
        server,
        "_load_cfg",
        lambda: {
            "model": {"default": "gpt-5.5", "provider": "openai-codex"},
            "fallback_providers": fallback_chain,
        },
    )
    monkeypatch.setattr(
        "hermes_cli.runtime_provider.resolve_runtime_provider",
        lambda requested=None, target_model=None: {
            "provider": "openai-codex",
            "base_url": "https://chatgpt.com/backend-api/codex",
            "api_key": "token",
            "api_mode": "codex_responses",
            "credential_pool": None,
        },
    )
    monkeypatch.setattr("run_agent.AIAgent", fake_agent)
    monkeypatch.setattr(server, "_load_enabled_toolsets", lambda *_a, **_kw: ["file"])
    monkeypatch.setattr(server, "_get_db", lambda: None)

    agent = server._make_agent("sid", "session-key")

    assert agent.model == "gpt-5.5"
    assert captured["fallback_model"] == fallback_chain
    assert captured["platform"] == "tui"


def test_make_agent_forwards_agent_disabled_toolsets(monkeypatch):
    """``agent.disabled_toolsets`` must reach AIAgent in gateway sessions too: only the AIAgent
    filter strips a toolset out of composite defaults (``hermes-cli``), which the gateway's
    enabled-list resolver can't reach into (#44499)."""
    captured = _capture_make_agent_kwargs(monkeypatch)
    monkeypatch.setattr(server, "_load_enabled_toolsets", lambda *_a, **_kw: ["file"])
    monkeypatch.setattr(server, "_load_disabled_toolsets", lambda: ["browser"])

    server._make_agent("sid", "session-key")

    assert captured["disabled_toolsets"] == ["browser"]


def test_make_agent_disabled_toolsets_none_by_default(monkeypatch):
    captured = _capture_make_agent_kwargs(monkeypatch)
    monkeypatch.setattr(server, "_load_enabled_toolsets", lambda *_a, **_kw: ["file"])
    monkeypatch.setattr(server, "_load_disabled_toolsets", lambda: None)

    server._make_agent("sid", "session-key")

    assert captured["disabled_toolsets"] is None


@pytest.mark.parametrize("identity, user_id", [
    ({"user_id": "oidc|abc123", "provider": "oidc"}, "oidc:oidc|abc123"),
    ({"user_id": "alice", "provider": "basic"}, "basic:alice"),
    ({"user_id": "alice", "provider": "oidc"}, "oidc:alice"),
    (None, None),
    ({"user_id": "server-internal", "provider": "server-internal"}, None),
    ({"user_id": "", "provider": "oidc"}, None),
    ({"user_id": "abc", "provider": ""}, None),
])
def test_make_agent_passes_the_authenticated_dashboard_user_as_user_id(monkeypatch, identity, user_id):
    """WSTransport.auth_identity reaches the agent as ``user_id`` prefixed with the login provider, so a
    basic-auth ``alice`` and an OIDC ``alice`` stay two memory peers. The legacy token, stdio and the PTY
    child's server-internal credential name no human, so the agent gets no user id for them."""
    captured = _capture_make_agent_kwargs(monkeypatch)
    transport = types.SimpleNamespace(auth_identity=identity)
    monkeypatch.setitem(server._sessions, "sid-auth", {"session_key": "k", "transport": transport})

    server._make_agent("sid-auth", "k")

    assert captured["user_id"] == user_id


def test_make_agent_passes_no_user_id_for_an_unknown_session(monkeypatch):
    captured = _capture_make_agent_kwargs(monkeypatch)
    server._sessions.pop("sid-missing", None)

    server._make_agent("sid-missing", "k")

    assert captured["user_id"] is None


def test_make_agent_keeps_the_login_after_a_second_window_attaches_and_detaches(monkeypatch):
    """A pop-out turns the transport slot into a FanoutTransport, which names no login. The rebuild must read the
    login the record was created with, before and after the pop-out goes away."""
    captured = _capture_make_agent_kwargs(monkeypatch)
    first, popout = _LoginSocket(), _LoginSocket()
    record = _login_session(monkeypatch, "sid-popout", "k", first)

    assert server._attach_session_transport(record, popout)
    server._make_agent("sid-popout", "k")
    assert captured["user_id"] == "basic:alice"

    server._detach_session_transport(record, popout)
    server._make_agent("sid-popout", "k")
    assert captured["user_id"] == "basic:alice"


def test_build_branch_agent_carries_the_parent_login(monkeypatch, tmp_path):
    """The branch agent is built before its record exists, so the parent's login is passed to the build and
    copied onto the new record."""
    captured = _capture_make_agent_kwargs(monkeypatch)
    socket = _LoginSocket()
    parent = _login_session(monkeypatch, "sid-parent", "parent-key", socket, cwd=str(tmp_path), source="desktop")

    def fake_init_session(sid, key, agent, history, **kwargs):
        monkeypatch.setitem(server._sessions, sid, {"session_key": key, "transport": server._stdio_transport})

    monkeypatch.setattr(server, "_set_session_context", lambda key, cwd=None: [])
    monkeypatch.setattr(server, "_clear_session_context", lambda tokens: None)
    monkeypatch.setattr(server, "_init_session", fake_init_session)
    monkeypatch.setattr(server, "_transfer_db_to_agent", lambda *args: False)
    token = bind_transport(socket)
    try:
        server._build_branch_agent(parent, "sid-branch", "branch-key", [], "desktop")
    finally:
        reset_transport(token)

    assert captured["user_id"] == "basic:alice"
    assert server._sessions["sid-branch"]["auth_user_id"] == "basic:alice"


def test_deferred_session_record_stamps_the_creating_login():
    token = bind_transport(_LoginSocket("carol", "oidc"))
    try:
        record = server._deferred_session_record(
            "deferred-key", cols=80, cwd="/tmp", history=[], lease=None)
    finally:
        reset_transport(token)

    assert record["auth_user_id"] == "oidc:carol"
    assert server._session_auth_user_id(record) == "oidc:carol"


def test_compute_host_turn_frame_carries_the_session_login(monkeypatch):
    record = _login_session(monkeypatch, "sid-host", "host-key", _LoginSocket(), history=[],
                            history_lock=threading.Lock(), cwd="/tmp", cols=80)
    monkeypatch.setattr(server, "_session_cwd", lambda session: "/tmp")

    frame = server._compute_host_turn_frame("rid", "sid-host", record, "hello")

    assert frame["auth_user_id"] == "basic:alice"


def test_attaching_a_different_login_keeps_the_creator_and_warns_once(monkeypatch):
    """Ownership is not enforced. The record keeps the creator's login, and the attach is logged once with both
    ids rather than on every prompt the second client sends."""
    creator, other = _LoginSocket("alice"), _LoginSocket("bob")
    record = _login_session(monkeypatch, "sid-shared", "shared-key", creator)

    assert server._attach_session_transport(record, other)
    assert server._attach_session_transport(record, other)

    assert server._session_auth_user_id(record) == "basic:alice"


def test_background_agent_kwargs_preserves_full_fallback_chain(monkeypatch):
    chain = [
        {"provider": "openrouter", "model": "openai/gpt-5.5"},
        {"provider": "anthropic", "model": "claude-sonnet-4-6"},
    ]
    agent = types.SimpleNamespace(
        model="gpt-5.5",
        provider="openai-codex",
        _fallback_chain=chain,
    )
    monkeypatch.setattr(server, "_load_cfg", lambda: {"max_turns": 25})
    monkeypatch.setattr(server, "_load_enabled_toolsets", lambda *_a, **_kw: ["file"])
    monkeypatch.setattr(server, "_get_db", lambda: None)

    kwargs = server._background_agent_kwargs(agent, "task-id")

    assert kwargs["fallback_model"] == chain


def test_background_agent_kwargs_preserves_empty_fallback_chain(monkeypatch):
    agent = types.SimpleNamespace(
        model="gpt-5.5",
        provider="anthropic",
        _fallback_chain=[],
    )
    monkeypatch.setattr(
        server,
        "_load_cfg",
        lambda: {
            "max_turns": 25,
            "fallback_providers": [
                {"provider": "openrouter", "model": "openai/gpt-5.5"},
            ],
        },
    )
    monkeypatch.setattr(server, "_load_enabled_toolsets", lambda *_a, **_kw: ["file"])
    monkeypatch.setattr(server, "_get_db", lambda: None)

    kwargs = server._background_agent_kwargs(agent, "task-id")

    assert kwargs["fallback_model"] == []


def test_background_agent_kwargs_forwards_agent_disabled_toolsets(monkeypatch):
    agent = types.SimpleNamespace(
        model="gpt-5.5",
        provider="anthropic",
        _fallback_chain=[],
        disabled_toolsets=["browser"],
    )
    monkeypatch.setattr(server, "_load_cfg", lambda: {"max_turns": 25})
    monkeypatch.setattr(server, "_load_enabled_toolsets", lambda *_a, **_kw: ["file"])
    monkeypatch.setattr(server, "_get_db", lambda: None)

    kwargs = server._background_agent_kwargs(agent, "task-id")

    assert kwargs["disabled_toolsets"] == ["browser"]


def test_background_agent_kwargs_falls_back_to_config_disabled_toolsets(monkeypatch):
    agent = types.SimpleNamespace(
        model="gpt-5.5",
        provider="anthropic",
        _fallback_chain=[],
    )
    monkeypatch.setattr(server, "_load_cfg", lambda: {"max_turns": 25})
    monkeypatch.setattr(server, "_load_enabled_toolsets", lambda *_a, **_kw: ["file"])
    monkeypatch.setattr(server, "_load_disabled_toolsets", lambda: ["browser"])
    monkeypatch.setattr(server, "_get_db", lambda: None)

    kwargs = server._background_agent_kwargs(agent, "task-id")

    assert kwargs["disabled_toolsets"] == ["browser"]


def test_startup_runtime_resolves_short_alias_without_network(monkeypatch):
    monkeypatch.setenv("HERMES_MODEL", "sonnet")
    monkeypatch.delenv("HERMES_TUI_PROVIDER", raising=False)
    monkeypatch.delenv("HERMES_INFERENCE_PROVIDER", raising=False)
    monkeypatch.setattr(server, "_load_cfg", lambda: {"model": {"provider": "auto"}})
    monkeypatch.setattr(
        "hermes_cli.models.fetch_openrouter_models",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("network lookup should not run")
        ),
    )

    model, provider = server._resolve_startup_runtime()

    assert provider == "anthropic"
    assert model.startswith("claude-sonnet")


def test_startup_runtime_does_not_call_network_detector(monkeypatch):
    monkeypatch.setenv("HERMES_MODEL", "sonnet")
    monkeypatch.delenv("HERMES_TUI_PROVIDER", raising=False)
    monkeypatch.delenv("HERMES_INFERENCE_PROVIDER", raising=False)
    monkeypatch.setattr(server, "_load_cfg", lambda: {"model": {"provider": "auto"}})
    monkeypatch.setattr(
        "hermes_cli.models.detect_provider_for_model",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("network detector called")
        ),
    )

    model, provider = server._resolve_startup_runtime()

    assert model
    assert provider in {None, "anthropic"}


def test_session_close_commits_memory_and_fires_finalize_hook(monkeypatch):
    calls = {"hooks": []}

    agent = types.SimpleNamespace(session_id="session-key")
    agent.commit_memory_session = lambda history: calls.setdefault("history", history)
    server._sessions["sid"] = _session(
        agent=agent, history=[{"role": "user", "content": "hello"}]
    )
    monkeypatch.setattr(
        server,
        "_notify_session_boundary",
        lambda event, session_id, *_args: calls["hooks"].append((event, session_id)),
    )

    try:
        resp = server.handle_request(
            {"id": "1", "method": "session.close", "params": {"session_id": "sid"}}
        )
        assert resp["result"]["closed"] is True
        assert calls["history"] == [{"role": "user", "content": "hello"}]
        assert ("on_session_finalize", "session-key") in calls["hooks"]
    finally:
        server._sessions.pop("sid", None)


def test_session_close_releases_resume_lock_before_slow_teardown(monkeypatch):
    """One slow session finalizer must not stall unrelated session.resume RPCs."""
    teardown_started = threading.Event()
    release_teardown = threading.Event()
    response = {}

    def _slow_teardown(_session, *, end_reason="tui_close"):
        assert end_reason == "tui_close"
        teardown_started.set()
        assert release_teardown.wait(timeout=2.0)

    monkeypatch.setattr(server, "_teardown_session", _slow_teardown)
    server._sessions["slow-close"] = _session()

    def _close():
        response.update(
            server.handle_request(
                {
                    "id": "close",
                    "method": "session.close",
                    "params": {"session_id": "slow-close"},
                }
            )
        )

    thread = threading.Thread(target=_close)
    thread.start()
    acquired = False
    try:
        assert teardown_started.wait(timeout=1.0)
        assert "slow-close" not in server._sessions
        acquired = server._session_resume_lock.acquire(timeout=0.2)
        assert acquired, "slow teardown kept the global resume lock held"
    finally:
        if acquired:
            server._session_resume_lock.release()
        release_teardown.set()
        thread.join(timeout=2.0)
        server._sessions.pop("slow-close", None)

    assert not thread.is_alive()
    assert response["result"] == {"closed": True}


def test_session_close_settles_active_turn_before_teardown(monkeypatch):
    """Close must not tear down agent resources while their turn is unwinding."""
    turn_started = threading.Event()
    release_turn = threading.Event()
    teardown_started = threading.Event()
    response = {}

    def _turn():
        turn_started.set()
        assert release_turn.wait(timeout=2.0)

    def _teardown(_session, *, end_reason="tui_close"):
        if end_reason == "tui_close":
            teardown_started.set()

    session = _session()
    run_thread = threading.Thread(target=_turn)
    session["_run_thread"] = run_thread
    server._sessions["settle-close"] = session
    monkeypatch.setattr(server, "_teardown_session", _teardown)
    monkeypatch.setattr(
        server, "_TURN_SETTLE_BEFORE_CLOSE_SECONDS", 1.0, raising=False
    )

    close_thread = threading.Thread(
        target=lambda: response.update(
            server.handle_request(
                {
                    "id": "close",
                    "method": "session.close",
                    "params": {"session_id": "settle-close"},
                }
            )
        )
    )
    run_thread.start()
    close_thread.start()
    try:
        assert turn_started.wait(timeout=1.0)
        assert not teardown_started.wait(timeout=0.1)
        release_turn.set()
        close_thread.join(timeout=2.0)
    finally:
        release_turn.set()
        run_thread.join(timeout=2.0)
        close_thread.join(timeout=2.0)
        server._sessions.pop("settle-close", None)

    assert not close_thread.is_alive()
    assert teardown_started.is_set()
    assert response["result"] == {"closed": True}


def test_ws_orphan_reap_interrupts_isolated_turn_then_reaps(monkeypatch):
    callbacks = []
    interrupted = []
    torn_down = []

    class _Timer:
        def __init__(self, _delay, callback):
            callbacks.append(callback)
            self.daemon = False

        def start(self):
            return None

    class _Supervisor:
        def interrupt(self, sid, *, request_id=None):
            interrupted.append((sid, request_id))

    session = _session(
        agent=None,
        agent_ready=threading.Event(),
        transport=server._detached_ws_transport,
        running=True,
        _compute_host_active=True,
        history=[{"role": "assistant", "content": "partial"}],
        queued_prompt={"text": "must not run"},
    )
    server._sessions["isolated-sid"] = session
    monkeypatch.setattr(server, "_WS_ORPHAN_REAP_GRACE_S", 0.01)
    monkeypatch.setattr(server.threading, "Timer", _Timer)
    monkeypatch.setattr(
        server, "_load_cfg", lambda: {"dashboard": {"turn_isolation": True}}
    )
    monkeypatch.setattr(
        server, "_get_compute_host_supervisor", lambda _cfg=None: _Supervisor()
    )
    monkeypatch.setattr(
        server,
        "_teardown_popped_session",
        lambda claimed, *, end_reason: torn_down.append((claimed, end_reason)) or True,
    )

    try:
        server._schedule_ws_orphan_reap("isolated-sid")
        callbacks.pop(0)()

        assert interrupted == [("isolated-sid", "client-gone-isolated-sid")]
        assert session["_turn_cancel_requested"] is True
        assert session["queued_prompt"] is None
        assert session["history"] == [{"role": "assistant", "content": "partial"}]
        assert len(callbacks) == 1

        callbacks.pop(0)()

        assert interrupted == [("isolated-sid", "client-gone-isolated-sid")]
        assert len(callbacks) == 1

        session["running"] = False
        callbacks.pop(0)()

        assert "isolated-sid" not in server._sessions
        assert torn_down == [(session, "ws_orphan_reap")]
    finally:
        server._sessions.pop("isolated-sid", None)


def test_ws_orphan_reap_spares_turn_reattached_within_grace(monkeypatch):
    callbacks = []
    interrupted = []

    class _Timer:
        def __init__(self, _delay, callback):
            callbacks.append(callback)

        def start(self):
            return None

    class _LiveThread:
        def is_alive(self):
            return True

    class _LiveTransport:
        def write(self, *_args, **_kwargs):
            return True

    disconnecting_transport = _LiveTransport()
    session = _session(
        agent=types.SimpleNamespace(
            interrupt=lambda: interrupted.append("interrupted")
        ),
        transport=disconnecting_transport,
        running=True,
        _run_thread=_LiveThread(),
    )
    server._sessions["reattached-sid"] = session
    monkeypatch.setattr(server, "_WS_ORPHAN_REAP_GRACE_S", 0.01)
    monkeypatch.setattr(server.threading, "Timer", _Timer)
    monkeypatch.setattr(server, "_load_cfg", lambda: {})

    try:
        server._close_sessions_for_transport(disconnecting_transport)
        assert session["transport"] is server._detached_ws_transport

        session["transport"] = _LiveTransport()
        callbacks.pop(0)()

        assert interrupted == []
        assert "reattached-sid" in server._sessions
        assert callbacks == []
    finally:
        server._sessions.pop("reattached-sid", None)


def test_session_resume_does_not_rebind_after_client_gone_interrupt_claim(monkeypatch):
    class _DB:
        def get_session(self, session_id):
            assert session_id == "stored-sid"
            return {"id": session_id, "cwd": "/tmp"}

        def resolve_resume_session_id(self, session_id):
            return session_id

    live_transport = object()
    session = _session(
        session_key="stored-sid",
        transport=server._detached_ws_transport,
        running=True,
        _client_gone_interrupt_requested=True,
    )
    server._sessions["live-sid"] = session
    monkeypatch.setattr(server, "_get_db", lambda: _DB())
    monkeypatch.setattr(server, "current_transport", lambda: live_transport)

    try:
        response = server.handle_request(
            {
                "id": "resume-after-claim",
                "method": "session.resume",
                "params": {"session_id": "stored-sid"},
            }
        )

        assert response is not None
        assert response["error"]["code"] == 4009
        assert session["transport"] is server._detached_ws_transport
    finally:
        server._sessions.pop("live-sid", None)


def test_ws_orphan_reap_defers_running_turn_for_active_delegation(monkeypatch):
    callbacks = []
    interrupted = []
    delegation_active = iter((True, False, False))

    class _Timer:
        def __init__(self, _delay, callback):
            callbacks.append(callback)

        def start(self):
            return None

    class _LiveThread:
        def is_alive(self):
            return True

    def _interrupt():
        interrupted.append("interrupted")
        session["running"] = False

    session = _session(
        agent=types.SimpleNamespace(interrupt=_interrupt),
        transport=server._detached_ws_transport,
        running=True,
        _run_thread=_LiveThread(),
    )
    server._sessions["delegating-turn"] = session
    monkeypatch.setattr(server, "_WS_ORPHAN_REAP_GRACE_S", 0.01)
    monkeypatch.setattr(server.threading, "Timer", _Timer)
    monkeypatch.setattr(server, "_load_cfg", lambda: {})
    monkeypatch.setattr(
        server,
        "_session_has_active_delegations",
        lambda *_args, **_kwargs: next(delegation_active),
    )
    monkeypatch.setattr(server, "_teardown_popped_session", lambda *_args, **_kwargs: True)

    try:
        server._schedule_ws_orphan_reap("delegating-turn")
        callbacks.pop(0)()

        assert interrupted == []
        assert len(callbacks) == 1

        callbacks.pop(0)()

        assert interrupted == ["interrupted"]
        assert len(callbacks) == 1

        callbacks.pop(0)()
        assert "delegating-turn" not in server._sessions
    finally:
        server._sessions.pop("delegating-turn", None)


def test_ws_orphan_reap_interrupts_in_process_turn(monkeypatch):
    callbacks = []
    interrupted = []

    class _Timer:
        def __init__(self, _delay, callback):
            callbacks.append(callback)

        def start(self):
            return None

    class _LiveThread:
        def is_alive(self):
            return True

    def _interrupt():
        interrupted.append("interrupted")
        session["running"] = False

    session = _session(
        agent=types.SimpleNamespace(interrupt=_interrupt),
        transport=server._detached_ws_transport,
        running=True,
        _run_thread=_LiveThread(),
    )
    server._sessions["inline-sid"] = session
    monkeypatch.setattr(server, "_WS_ORPHAN_REAP_GRACE_S", 0.01)
    monkeypatch.setattr(server.threading, "Timer", _Timer)
    monkeypatch.setattr(server, "_load_cfg", lambda: {})

    try:
        server._schedule_ws_orphan_reap("inline-sid")
        callbacks.pop(0)()

        assert interrupted == ["interrupted"]
        assert session["_turn_cancel_requested"] is True
        assert len(callbacks) == 1
    finally:
        server._sessions.pop("inline-sid", None)


def test_ws_disconnect_running_sidecar_still_closes_without_orphan_timer(monkeypatch):
    closed = []
    scheduled = []
    transport = object()
    server._sessions["sidecar-sid"] = _session(
        transport=transport,
        running=True,
        close_on_disconnect=True,
    )
    monkeypatch.setattr(
        server,
        "_teardown_popped_session",
        lambda session, *, end_reason: closed.append((session["_sid"], end_reason)) or True,
    )
    monkeypatch.setattr(
        server, "_schedule_ws_orphan_reap", lambda sid: scheduled.append(sid)
    )

    try:
        reaped, detached = server._close_sessions_for_transport(transport)

        assert (reaped, detached) == (1, 0)
        assert closed == [("sidecar-sid", "ws_disconnect")]
        assert scheduled == []
    finally:
        server._sessions.pop("sidecar-sid", None)


def test_ws_orphan_reap_releases_resume_lock_before_slow_teardown(monkeypatch):
    """Grace reaping claims under the lock but finalizes after releasing it."""
    scheduled = {}
    teardown_started = threading.Event()
    release_teardown = threading.Event()

    class _Timer:
        def __init__(self, _delay, callback):
            scheduled["callback"] = callback

        def start(self):
            return None

    def _slow_teardown(_session, *, end_reason="tui_close"):
        assert end_reason == "ws_orphan_reap"
        teardown_started.set()
        assert release_teardown.wait(timeout=10.0)

    monkeypatch.setattr(server, "_WS_ORPHAN_REAP_GRACE_S", 0.01)
    monkeypatch.setattr(server.threading, "Timer", _Timer)
    monkeypatch.setattr(server, "_teardown_session", _slow_teardown)
    server._sessions["slow-orphan"] = _session(
        transport=server._detached_ws_transport,
        running=False,
    )

    server._schedule_ws_orphan_reap("slow-orphan")
    thread = threading.Thread(target=scheduled["callback"])
    thread.start()
    acquired = False
    try:
        assert teardown_started.wait(timeout=10.0)
        assert "slow-orphan" not in server._sessions
        acquired = server._session_resume_lock.acquire(timeout=2.0)
        assert acquired, "orphan teardown kept the global resume lock held"
    finally:
        if acquired:
            server._session_resume_lock.release()
        release_teardown.set()
        thread.join(timeout=10.0)
        server._sessions.pop("slow-orphan", None)

    assert not thread.is_alive()


def test_ws_orphan_reap_reschedules_while_mid_turn_then_reaps(monkeypatch):
    """A detached session that is still running must keep the reap timer (#85578)."""
    callbacks = []
    torn_down = []

    class _Timer:
        def __init__(self, _delay, callback):
            callbacks.append(callback)
            self.daemon = False

        def start(self):
            return None

    monkeypatch.setattr(server, "_WS_ORPHAN_REAP_GRACE_S", 0.01)
    monkeypatch.setattr(server.threading, "Timer", _Timer)
    monkeypatch.setattr(
        server,
        "_teardown_session",
        lambda session, *, end_reason="tui_close": torn_down.append(
            (session, end_reason)
        ),
    )
    live = _session(
        transport=server._detached_ws_transport,
        running=True,
    )
    server._sessions["midturn-sid"] = live

    try:
        server._schedule_ws_orphan_reap("midturn-sid")
        callbacks.pop(0)()

        assert "midturn-sid" in server._sessions
        assert len(callbacks) == 1
        assert torn_down == []

        live["running"] = False
        callbacks.pop(0)()

        assert "midturn-sid" not in server._sessions
        assert len(torn_down) == 1
        assert torn_down[0][1] == "ws_orphan_reap"
    finally:
        server._sessions.pop("midturn-sid", None)


def test_ws_orphan_reap_waits_for_active_delegation_then_reaps(monkeypatch):
    from tools import async_delegation

    callbacks = []
    torn_down = []
    delegation_id = "deleg_ws_orphan_reap_test"

    class _Timer:
        def __init__(self, _delay, callback):
            callbacks.append(callback)
            self.daemon = False

        def start(self):
            return None

    monkeypatch.setattr(server, "_WS_ORPHAN_REAP_GRACE_S", 0.01)
    monkeypatch.setattr(server.threading, "Timer", _Timer)
    monkeypatch.setattr(
        server,
        "_teardown_session",
        lambda session, *, end_reason="tui_close": torn_down.append(
            (session, end_reason)
        ),
    )
    server._sessions["delegating-sid"] = _session(
        transport=server._detached_ws_transport,
        running=False,
    )
    with async_delegation._records_lock:
        async_delegation._records[delegation_id] = {
            "status": "running",
            "origin_ui_session_id": "delegating-sid",
        }

    try:
        server._schedule_ws_orphan_reap("delegating-sid")
        callbacks.pop(0)()

        assert "delegating-sid" in server._sessions
        assert len(callbacks) == 1
        assert torn_down == []

        with async_delegation._records_lock:
            async_delegation._records[delegation_id]["status"] = "completed"
        callbacks.pop(0)()

        assert "delegating-sid" not in server._sessions
        assert len(torn_down) == 1
        assert torn_down[0][1] == "ws_orphan_reap"
    finally:
        server._sessions.pop("delegating-sid", None)
        with async_delegation._records_lock:
            async_delegation._records.pop(delegation_id, None)


def test_ws_orphan_reap_retries_when_delegation_lookup_fails(monkeypatch):
    from tools import async_delegation

    callbacks = []
    torn_down = []

    class _Timer:
        def __init__(self, _delay, callback):
            callbacks.append(callback)
            self.daemon = False

        def start(self):
            return None

    def _raise_lookup_error(*_args, **_kwargs):
        raise RuntimeError("delegation registry unavailable")

    monkeypatch.setattr(server, "_WS_ORPHAN_REAP_GRACE_S", 0.01)
    monkeypatch.setattr(server.threading, "Timer", _Timer)
    monkeypatch.setattr(
        async_delegation, "has_live_for_session", _raise_lookup_error
    )
    monkeypatch.setattr(
        server,
        "_teardown_session",
        lambda session, *, end_reason="tui_close": torn_down.append(
            (session, end_reason)
        ),
    )
    server._sessions["lookup-error-sid"] = _session(
        transport=server._detached_ws_transport,
        running=False,
    )

    try:
        server._schedule_ws_orphan_reap("lookup-error-sid")
        callbacks.pop(0)()

        assert "lookup-error-sid" in server._sessions
        assert len(callbacks) == 1
        assert torn_down == []
    finally:
        server._sessions.pop("lookup-error-sid", None)


def test_finalize_session_closes_slash_worker(monkeypatch):
    """_finalize_session closes the slash_worker subprocess itself.

    Regression for #38095: the worker cleanup used to live only in the
    callers (_teardown_session / _shutdown_sessions), so any code path that
    finalized a session without going through them leaked the worker. Folding
    close() into the single _finalized-guarded chokepoint makes the cleanup
    defense-in-depth and idempotent.
    """
    closed = {"count": 0}

    class _FakeWorker:
        def close(self):
            closed["count"] += 1

    monkeypatch.setattr(server, "_notify_session_boundary", lambda *a, **k: None)
    monkeypatch.setattr(server, "_get_db", lambda: None)

    session = _session(slash_worker=_FakeWorker())

    server._finalize_session(session)
    assert closed["count"] == 1
    assert session.get("_finalized") is True

    # Idempotent: a second finalize (or a follow-up teardown) must not
    # re-close the worker — the _finalized guard short-circuits.
    server._finalize_session(session)
    server._teardown_session(session)
    assert closed["count"] == 1


def test_close_transport_rebinds_session_to_remaining_viewer(monkeypatch):
    """Closing a pop-out window's transport must leave the session with the
    still-open window instead of stranding it on the drop sentinel (#83716).

    The rebind #83716 added is gone; multi-client fan-out subsumes it. Both
    windows are attached to the slot at once, so the pop-out is a fan-out peer
    rather than a viewer waiting to be promoted, and closing it detaches that
    peer while retaining the surviving ordered mailbox. This pins the same
    guarantee through the mechanism that replaced the rebind: the session is
    not parked, not reaped, not handed to the orphan reaper, and the surviving
    window keeps receiving frames.
    """
    reap_calls = []
    monkeypatch.setattr(server, "_schedule_ws_orphan_reap", lambda sid: reap_calls.append(sid))

    class _LiveTransport:
        def __init__(self):
            self.frames = []
            self.received = threading.Event()

        def write(self, obj=None, *a, **k):
            self.frames.append(obj)
            self.received.set()
            return True

    main = _LiveTransport()
    popout = _LiveTransport()
    session = _session(transport=None, running=False)
    # Build the state the way production does: every window that resumes goes
    # through _live_session_payload, which attaches it into the slot and then
    # stamps it into the viewers registry.
    server._attach_session_transport(session, main)
    server._attach_session_transport(session, popout)
    session["viewers"] = {main: 100.0, popout: 200.0}
    server._sessions["multi-sid"] = session
    assert isinstance(session["transport"], server.FanoutTransport)

    try:
        reaped, detached = server._close_sessions_for_transport(popout)

        assert reaped == 0 and detached == 0
        assert server._session_transport_contains(session, main)
        assert not server._session_transport_contains(session, popout)
        assert "multi-sid" not in reap_calls
        assert server._ws_session_is_orphaned(session) is False

        # And it is still a working stream, not just a surviving reference.
        server._emit("message.delta", "multi-sid", {"text": "still here"})
        assert main.received.wait(timeout=5)
        assert [(f.get("params") or {}).get("type") for f in main.frames] == [
            "message.delta"
        ]
        assert popout.frames == []
    finally:
        # The fake slot must not outlive the test: _sessions is module state and
        # later sweeps would walk it.
        server._sessions.pop("multi-sid", None)


def test_close_transport_detaches_when_no_viewers_remain(monkeypatch):
    """The last viewer closing still lands the session on the drop sentinel
    and schedules the grace reap (unchanged single-window behavior)."""
    reap_calls = []
    monkeypatch.setattr(server, "_schedule_ws_orphan_reap", lambda sid: reap_calls.append(sid))

    class _LiveTransport:
        def write(self, *a, **k):
            return True

    only = _LiveTransport()
    session = _session(transport=only, running=False)
    session["viewers"] = {only: 100.0}
    server._sessions["solo-sid"] = session

    reaped, detached = server._close_sessions_for_transport(only)

    assert reaped == 0 and detached == 1
    assert session["transport"] is server._detached_ws_transport
    assert reap_calls == ["solo-sid"]


def test_close_transport_skips_dead_remaining_viewers(monkeypatch):
    """A viewer whose socket is already dead must not hold the session open.

    #83716's rebind refused to hand the session to a dead viewer; fan-out
    membership keeps that filter through _transport_is_live_peer, which is what
    decides whether anything survives the departing client. Both windows are
    ATTACHED here, which is the state production builds — a viewer that was
    never attached leaves the slot single-client and exercises the ordinary park
    path instead of this one.
    """
    reap_calls = []
    monkeypatch.setattr(server, "_schedule_ws_orphan_reap", lambda sid: reap_calls.append(sid))

    class _LiveTransport:
        def write(self, *a, **k):
            return True

    dead = _LiveTransport()
    popout = _LiveTransport()
    session = _session(transport=None, running=False)
    server._attach_session_transport(session, dead)
    server._attach_session_transport(session, popout)
    session["viewers"] = {dead: 100.0, popout: 200.0}
    assert isinstance(session["transport"], server.FanoutTransport)
    # The socket goes away without a disconnect reaching the gateway; the latch
    # _transport_is_dead reads is the only trace it leaves behind.
    dead._closed = True
    server._sessions["dead-viewer-sid"] = session

    try:
        reaped, detached = server._close_sessions_for_transport(popout)

        assert reaped == 0 and detached == 1
        assert session["transport"] is server._detached_ws_transport
        assert reap_calls == ["dead-viewer-sid"]
    finally:
        server._sessions.pop("dead-viewer-sid", None)


def test_live_session_payload_registers_transport_as_viewer():
    """Resume/activate through _live_session_payload must register the caller
    as a viewer so the disconnect path has something to re-bind to (#83716)."""
    class _LiveTransport:
        def write(self, *a, **k):
            return True

    t = _LiveTransport()
    session = _session(transport=server._detached_ws_transport, running=False)
    server._live_session_payload("viewer-sid", session, transport=t)

    assert session["transport"] is t
    assert t in session.get("viewers", {})


def test_ws_orphan_reap_spares_reattached_session(monkeypatch):
    """A session that rebinds a live transport is NOT considered orphaned."""

    class _LiveTransport:
        def write(self, *a, **k):
            return True

    # Reattached: transport is a live (non-stdio) transport.
    reattached = _session(transport=_LiveTransport(), running=False)
    assert server._ws_session_is_orphaned(reattached) is False

    # Mid-turn sessions are also spared even if detached.
    mid_turn = _session(transport=server._detached_ws_transport, running=True)
    assert server._ws_session_is_orphaned(mid_turn) is False

    # Already finalized sessions are spared (idempotency).
    done = _session(
        transport=server._detached_ws_transport,
        running=False,
        _finalized=True,
    )
    assert server._ws_session_is_orphaned(done) is False


def test_resume_rebind_cancels_pending_ws_orphan_reap(monkeypatch):
    """Re-binding a live transport via _live_session_payload must cancel the
    pending ws-orphan reap Timer (storm killer, part 1)."""
    cancelled = []

    class _Timer:
        def __init__(self, _delay, fn):
            self.fn = fn

        def start(self):
            return None

        def cancel(self):
            cancelled.append(self)

    class _LiveTransport:
        def write(self, *a, **k):
            return True

    monkeypatch.setattr(server, "_WS_ORPHAN_REAP_GRACE_S", 0.01)
    monkeypatch.setattr(server.threading, "Timer", _Timer)
    session = _session(transport=server._detached_ws_transport, running=False)
    server._sessions["cancel-sid"] = session

    try:
        server._schedule_ws_orphan_reap("cancel-sid")
        assert "cancel-sid" in server._pending_ws_reaps

        server._live_session_payload("cancel-sid", session, transport=_LiveTransport())

        assert "cancel-sid" not in server._pending_ws_reaps
        assert len(cancelled) == 1
    finally:
        server._sessions.pop("cancel-sid", None)
        server._pending_ws_reaps.pop("cancel-sid", None)


def test_claim_or_reuse_live_winner_cancels_pending_reap(monkeypatch):
    """The winner's pending reap is cancelled only once guarded reuse is accepted."""
    cancelled = []

    class _Timer:
        def __init__(self, _delay, fn):
            self.fn = fn

        def start(self):
            return None

        def cancel(self):
            cancelled.append(self)

    monkeypatch.setattr(server, "_WS_ORPHAN_REAP_GRACE_S", 0.01)
    monkeypatch.setattr(server.threading, "Timer", _Timer)
    agent = types.SimpleNamespace(session_id="stored-claim")
    winner = _session(
        agent=agent,
        session_key="stored-claim",
        transport=server._detached_ws_transport,
        running=False,
    )
    server._sessions["winner-sid"] = winner

    try:
        server._schedule_ws_orphan_reap("winner-sid")
        assert "winner-sid" in server._pending_ws_reaps

        live = server._claim_or_reuse_live(
            "fresh-sid", "stored-claim", _session(), None
        )

        assert live == ("winner-sid", winner)
        assert "winner-sid" in server._pending_ws_reaps
        assert cancelled == []
        assert winner["transport"] is server._detached_ws_transport

        transport = object()
        monkeypatch.setattr(server, "current_transport", lambda: transport)
        ctx = server._Resume(1, {"omit_messages": True}, "stored-claim")
        response = server._resume_reuse_live(ctx, *live)

        assert response["result"]["session_id"] == "winner-sid"
        assert winner["transport"] is transport
        assert "winner-sid" not in server._pending_ws_reaps
        assert len(cancelled) == 1
    finally:
        server._sessions.pop("winner-sid", None)
        server._sessions.pop("fresh-sid", None)
        server._pending_ws_reaps.pop("winner-sid", None)
