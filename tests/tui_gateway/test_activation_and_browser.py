"""tui_gateway.server — session activation, verification status and browser management.

Split from test_tui_gateway_server.py; shared fixtures and helpers live
in tests/tui_gateway/_server_test_helpers.py.
"""

import json
import os
import sys
import threading
import time
import types
from unittest.mock import patch
from hermes_constants import reset_hermes_home_override, set_hermes_home_override
from hermes_cli.browser_connect import ChromeDebugLaunch
from tui_gateway import server

from tests.tui_gateway._server_test_helpers import (
    _FakeAgentForBackground,
    _ImmediateThread,
    _neuter_agent_prewarm_timer,  # autouse
    _reap_leaked_notification_pollers,  # autouse
    _session,
    _setup_make_agent_mocks,
    _stub_urlopen,
    _stub_urlopen_capture,
)


def test_session_activate_returns_inflight_stream_before_completion(monkeypatch):
    """Switching into a still-running live session must hydrate partial output.

    The committed session history is only updated after run_conversation returns,
    so session.activate needs an explicit in-flight payload sourced from the
    backend stream callback.
    """
    started = threading.Event()
    release = threading.Event()
    done = threading.Event()

    class _Agent:
        model = "model-live"

        def run_conversation(self, prompt, conversation_history=None, stream_callback=None, **_kwargs):
            assert prompt == "write a long answer"
            assert conversation_history == []
            stream_callback("partial ")
            stream_callback("answer")
            started.set()
            assert release.wait(2), "test timed out waiting to finish fake model turn"
            return {
                "final_response": "partial answer complete",
                "messages": [
                    {"role": "user", "content": "write a long answer"},
                    {"role": "assistant", "content": "partial answer complete"},
                ],
            }

    server._sessions["sid-live"] = _session(agent=_Agent())
    monkeypatch.setattr(server, "make_stream_renderer", lambda cols: None)
    monkeypatch.setattr(server, "render_message", lambda raw, cols: None)
    monkeypatch.setattr(server, "_get_db", lambda: None)
    monkeypatch.setattr(server, "_session_info", lambda agent: {"model": agent.model})

    def _emit(event, sid, payload=None):
        if event == "message.complete":
            done.set()

    monkeypatch.setattr(server, "_emit", _emit)

    try:
        submit = server.handle_request(
            {
                "id": "submit",
                "method": "prompt.submit",
                "params": {"session_id": "sid-live", "text": "write a long answer"},
            }
        )
        assert submit["result"]["status"] == "streaming"
        assert started.wait(2), "fake model did not stream before activation"

        resp = server.handle_request(
            {
                "id": "activate",
                "method": "session.activate",
                "params": {"session_id": "sid-live"},
            }
        )

        inflight = resp["result"].get("inflight")
        assert inflight == {
            "assistant": "partial answer",
            "streaming": True,
            "user": "write a long answer",
        }
        turn_started_at = resp["result"]["turn_started_at"]
        assert turn_started_at == server._sessions["sid-live"]["inflight_turn"]["started_at"]
        assert turn_started_at > 0
        assert resp["result"]["messages"] == []

        release.set()
        assert done.wait(2), "fake model turn did not complete"
        completed = server.handle_request(
            {
                "id": "activate-done",
                "method": "session.activate",
                "params": {"session_id": "sid-live"},
            }
        )
        assert completed["result"].get("inflight") is None
        assert completed["result"]["turn_started_at"] is None
        assert completed["result"]["messages"] == [
            {"role": "user", "text": "write a long answer"},
            {"role": "assistant", "text": "partial answer complete"},
        ]
    finally:
        release.set()
        done.wait(2)
        server._sessions.pop("sid-live", None)


def test_session_activate_returns_prompt_queued_during_busy_turn(monkeypatch):
    """A full client restart must recover an accepted next-turn prompt.

    Busy prompts are intentionally not durable until they drain. Their only
    authoritative copy is ``queued_prompt``, so the live projection must expose
    that copy without leaking the transport object.
    """
    monkeypatch.setattr(server, "_load_busy_input_mode", lambda: "queue")
    monkeypatch.setattr(server, "_session_info", lambda agent: {"model": agent.model})
    agent = types.SimpleNamespace(model="model-live")
    session = _session(
        agent=agent,
        running=True,
        inflight_turn={
            "assistant": "partial answer",
            "streaming": True,
            "user": "current prompt",
        },
    )
    server._sessions["sid-live"] = session
    try:
        queued = server._handle_busy_submit(
            "submit", "sid-live", session, "newest prompt", object()
        )
        assert queued["result"]["status"] == "queued"

        activated = server.handle_request(
            {
                "id": "activate",
                "method": "session.activate",
                "params": {"session_id": "sid-live"},
            }
        )

        assert activated["result"]["queued"] == {"user": "newest prompt"}
        assert "transport" not in activated["result"]["queued"]
    finally:
        server._sessions.pop("sid-live", None)


def test_session_activate_switches_live_session_without_closing_siblings(monkeypatch):
    monkeypatch.setattr(server, "_session_info", lambda agent: {"model": agent.model})
    server._sessions["sid-a"] = _session(
        agent=types.SimpleNamespace(model="model-a"),
        history=[{"role": "user", "content": "old"}],
        session_key="key-a",
    )
    server._sessions["sid-b"] = _session(
        agent=types.SimpleNamespace(model="model-b"),
        history=[
            {"role": "user", "content": "new prompt"},
            {"role": "assistant", "content": "new answer"},
        ],
        running=True,
        session_key="key-b",
    )
    try:
        resp = server.handle_request(
            {"id": "1", "method": "session.activate", "params": {"session_id": "sid-b"}}
        )

        assert "sid-a" in server._sessions
        assert "sid-b" in server._sessions
        assert resp["result"]["session_id"] == "sid-b"
        assert resp["result"]["session_key"] == "key-b"
        assert resp["result"]["running"] is True
        assert resp["result"]["status"] == "working"
        assert resp["result"]["info"] == {"model": "model-b"}
        assert resp["result"]["messages"] == [
            {"role": "user", "text": "new prompt"},
            {"role": "assistant", "text": "new answer"},
        ]
    finally:
        server._sessions.pop("sid-a", None)
        server._sessions.pop("sid-b", None)


def test_session_activate_can_omit_duplicate_desktop_transcript(monkeypatch):
    monkeypatch.setattr(server, "_session_info", lambda agent: {"model": agent.model})
    server._sessions["sid-large"] = _session(
        agent=types.SimpleNamespace(model="model-large"),
        history=[
            {"role": "user", "content": "large prompt"},
            {"role": "assistant", "content": "large answer"},
        ],
        session_key="key-large",
    )
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.activate",
                "params": {"session_id": "sid-large", "omit_messages": True},
            }
        )

        assert resp["result"]["messages"] == []
        assert resp["result"]["message_count"] == 2
        assert resp["result"]["messages_omitted"] is True
        assert resp["result"]["session_key"] == "key-large"
    finally:
        server._sessions.pop("sid-large", None)


# ── session.most_recent ──────────────────────────────────────────────


def test_session_most_recent_returns_first_non_denied(monkeypatch):
    """Drops `tool` rows like session.list does, returns the first hit."""

    class _DB:
        def list_sessions_rich(self, *, source=None, limit=200, order_by_last_active=False, compact_rows=False):
            return [
                {"id": "tool-1", "source": "tool", "title": "noise", "started_at": 100},
                {"id": "tui-1", "source": "tui", "title": "real", "started_at": 99},
            ]

    monkeypatch.setattr(server, "_get_db", lambda: _DB())

    resp = server.handle_request(
        {"id": "1", "method": "session.most_recent", "params": {}}
    )

    assert resp["result"]["session_id"] == "tui-1"
    assert resp["result"]["title"] == "real"
    assert resp["result"]["source"] == "tui"


def test_session_most_recent_returns_null_when_only_tool_rows(monkeypatch):
    class _DB:
        def list_sessions_rich(self, *, source=None, limit=200, order_by_last_active=False, compact_rows=False):
            return [{"id": "tool-1", "source": "tool", "started_at": 1}]

    monkeypatch.setattr(server, "_get_db", lambda: _DB())

    resp = server.handle_request(
        {"id": "1", "method": "session.most_recent", "params": {}}
    )

    assert resp["result"]["session_id"] is None


def test_session_most_recent_skips_unknown_source_rows(monkeypatch):
    """#54320: a token-accounting guard placeholder (source='unknown') must never be
    picked for auto-resume — the row can outrank the session the user actually opened."""

    class _DB:
        def list_sessions_rich(self, *, source=None, limit=200, order_by_last_active=False, compact_rows=False):
            return [
                {"id": "guard-1", "source": "unknown", "title": "", "started_at": 101},
                {"id": "tui-1", "source": "tui", "title": "real", "started_at": 100},
            ]

    monkeypatch.setattr(server, "_get_db", lambda: _DB())

    resp = server.handle_request(
        {"id": "1", "method": "session.most_recent", "params": {}}
    )

    assert resp["result"]["session_id"] == "tui-1"
    assert resp["result"]["source"] == "tui"


def test_session_most_recent_returns_null_when_only_unknown_rows(monkeypatch):
    class _DB:
        def list_sessions_rich(self, *, source=None, limit=200, order_by_last_active=False, compact_rows=False):
            return [{"id": "guard-1", "source": "unknown", "started_at": 1}]

    monkeypatch.setattr(server, "_get_db", lambda: _DB())

    resp = server.handle_request(
        {"id": "1", "method": "session.most_recent", "params": {}}
    )

    assert resp["result"]["session_id"] is None


def test_session_most_recent_folds_db_exception_into_null_result(monkeypatch):
    """Per contract, errors are folded into the null-result shape so
    callers don't have to special-case JSON-RPC error envelopes for
    'no answer' (Copilot review on #17130)."""

    class _BrokenDB:
        def list_sessions_rich(self, *, source=None, limit=200, order_by_last_active=False, compact_rows=False):
            raise RuntimeError("db locked")

    monkeypatch.setattr(server, "_get_db", lambda: _BrokenDB())

    resp = server.handle_request(
        {"id": "1", "method": "session.most_recent", "params": {}}
    )

    assert "error" not in resp
    assert resp["result"]["session_id"] is None


def test_session_most_recent_handles_db_unavailable(monkeypatch):
    monkeypatch.setattr(server, "_get_db", lambda: None)

    resp = server.handle_request(
        {"id": "1", "method": "session.most_recent", "params": {}}
    )

    assert resp["result"]["session_id"] is None


# ── verification.status ──────────────────────────────────────────────


def test_verification_status_returns_recorded_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_VERIFY_ON_STOP", "1")  # ledger is inert when the guard is off
    profile_home = tmp_path / "profiles" / "verify"
    profile_home.mkdir(parents=True)
    monkeypatch.setattr(server, "_profile_home", lambda p: profile_home if p == "verify" else None)
    token = set_hermes_home_override(profile_home)
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").mkdir()
    (project / "package.json").write_text(
        json.dumps({"scripts": {"test": "vitest"}}),
        encoding="utf-8",
    )
    (project / "pnpm-lock.yaml").write_text("", encoding="utf-8")
    try:
        from agent.verification_evidence import record_terminal_result

        record_terminal_result(
            command="pnpm run test",
            cwd=project,
            session_id="sid",
            exit_code=0,
            output="green",
        )

        resp = server.handle_request(
            {
                "id": "1",
                "method": "verification.status",
                "params": {"cwd": str(project), "session_id": "sid", "profile": "verify"},
            }
        )
    finally:
        reset_hermes_home_override(token)

    verification = resp["result"]["verification"]
    assert verification["status"] == "passed"
    assert verification["evidence"]["canonical_command"] == "pnpm run test"
    assert verification["evidence"]["scope"] == "full"


def test_verification_status_outside_workspace_is_not_applicable(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_VERIFY_ON_STOP", "1")  # ledger is inert when the guard is off
    # A cwd with no project facts (outside any code workspace) must report
    # not_applicable. Force the "no facts" precondition rather than relying on
    # tmp_path's ancestors being pristine — a stray marker file in a shared
    # tmp-root ancestor (e.g. /tmp/package.json left by another tool) would
    # otherwise make _marker_root() resolve tmp_path as a workspace and flip
    # the status to "unverified".
    import agent.coding_context as coding_context

    monkeypatch.setattr(coding_context, "project_facts_for", lambda _cwd=None: None)

    home = tmp_path / ".hermes"
    home.mkdir()
    token = set_hermes_home_override(home)
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "verification.status",
                "params": {"cwd": str(tmp_path), "session_id": "sid"},
            }
        )
    finally:
        reset_hermes_home_override(token)

    assert resp["result"]["verification"]["status"] == "not_applicable"


def test_browser_manage_status_reads_env_var(monkeypatch):
    """Status returns the env var verbatim (no network I/O)."""
    monkeypatch.setenv("BROWSER_CDP_URL", "http://127.0.0.1:9222")

    resp = server.handle_request(
        {"id": "1", "method": "browser.manage", "params": {"action": "status"}}
    )

    assert resp["result"]["connected"] is True
    assert resp["result"]["url"] == "http://127.0.0.1:9222"


def test_browser_manage_status_falls_back_to_config_cdp_url(monkeypatch):
    """When env is unset, status surfaces ``browser.cdp_url`` from
    config.yaml so users see what the next tool call will read."""
    monkeypatch.delenv("BROWSER_CDP_URL", raising=False)

    fake_cfg = types.SimpleNamespace(
        read_raw_config=lambda: {"browser": {"cdp_url": "http://lan:9222"}}
    )
    with patch.dict(sys.modules, {"hermes_cli.config": fake_cfg}):
        resp = server.handle_request(
            {"id": "1", "method": "browser.manage", "params": {"action": "status"}}
        )

    assert resp["result"] == {"connected": True, "url": "http://lan:9222"}


def test_browser_manage_connect_sets_env_and_cleans_twice(monkeypatch):
    """`/browser connect` must reach the live process: set env, reap browser
    sessions before AND after publishing the new URL.  The double-cleanup
    closes the supervisor swap window where ``_ensure_cdp_supervisor``
    could re-attach to the *old* CDP endpoint between steps."""
    monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
    cleanup_calls: list[str] = []

    def _cleanup_all():
        cleanup_calls.append(os.environ.get("BROWSER_CDP_URL", ""))

    fake = types.SimpleNamespace(
        cleanup_all_browsers=_cleanup_all,
        _get_cdp_override=lambda: os.environ.get("BROWSER_CDP_URL", ""),
    )
    with patch.dict(sys.modules, {"tools.browser_tool_lifecycle": fake}):
        _stub_urlopen(monkeypatch, ok=True)
        resp = server.handle_request(
            {
                "id": "1",
                "method": "browser.manage",
                "params": {"action": "connect", "url": "http://127.0.0.1:9222"},
            }
        )

    assert resp["result"]["connected"] is True
    assert resp["result"]["url"] == "http://127.0.0.1:9222"
    assert os.environ.get("BROWSER_CDP_URL") == "http://127.0.0.1:9222"
    # First cleanup runs against the OLD env (none here), second against the NEW.
    assert cleanup_calls == ["", "http://127.0.0.1:9222"]


def test_browser_manage_connect_defaults_to_loopback(monkeypatch):
    monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
    fake = types.SimpleNamespace(
        cleanup_all_browsers=lambda: None,
        _get_cdp_override=lambda: os.environ.get("BROWSER_CDP_URL", ""),
    )
    with patch.dict(sys.modules, {"tools.browser_tool_lifecycle": fake}):
        urls = _stub_urlopen_capture(monkeypatch, ok=True)
        resp = server.handle_request(
            {"id": "1", "method": "browser.manage", "params": {"action": "connect"}}
        )

    assert resp["result"]["connected"] is True
    assert resp["result"]["url"] == "http://127.0.0.1:9222"
    assert urls[0] == "http://127.0.0.1:9222/json/version"


def test_browser_manage_connect_default_local_reports_launch_hint(monkeypatch):
    monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
    # No ``platform.system`` fake: the resolved system string only flows into
    # ``launch_chrome_debug`` / ``manual_chrome_debug_command`` /
    # ``get_chrome_debug_candidates``, all of which are mocked below — the
    # host's real value never reaches unmocked code.
    emitted: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        server,
        "_emit",
        lambda evt, sid, payload=None: emitted.append((evt, payload or {})),
    )
    fake = types.SimpleNamespace(
        cleanup_all_browsers=lambda: None,
        _get_cdp_override=lambda: os.environ.get("BROWSER_CDP_URL", ""),
    )
    with patch.dict(sys.modules, {"tools.browser_tool_lifecycle": fake}):
        _stub_urlopen(monkeypatch, ok=False)
        with (
            patch(
                "hermes_cli.browser_connect.launch_chrome_debug",
                return_value=ChromeDebugLaunch(),
            ),
            patch("hermes_cli.browser_connect.local_port_in_use", return_value=False),
            patch("hermes_cli.browser_connect.manual_chrome_debug_command", return_value=None),
            patch(
                "hermes_cli.browser_connect.get_chrome_debug_candidates",
                return_value=[],
            ),
        ):
            resp = server.handle_request(
                {
                    "id": "1",
                    "method": "browser.manage",
                    "params": {
                        "action": "connect",
                        "session_id": "sess-1",
                        "url": "http://localhost:9222",
                    },
                }
            )

    assert resp["result"]["connected"] is False
    assert resp["result"]["url"] == "http://127.0.0.1:9222"
    assert resp["result"]["messages"]
    assert "BROWSER_CDP_URL" not in os.environ
    progress = [p["message"] for evt, p in emitted if evt == "browser.progress"]
    assert progress == resp["result"]["messages"]


def test_browser_manage_connect_no_session_skips_progress_events(monkeypatch):
    """Without a session_id the TUI prints messages from the response;
    emitting ``browser.progress`` events would double-render. Gate the
    emit so callers without a session see the bundled list only."""
    monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
    emitted: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        server,
        "_emit",
        lambda evt, sid, payload=None: emitted.append((evt, payload or {})),
    )
    fake = types.SimpleNamespace(
        cleanup_all_browsers=lambda: None,
        _get_cdp_override=lambda: os.environ.get("BROWSER_CDP_URL", ""),
    )
    with patch.dict(sys.modules, {"tools.browser_tool_lifecycle": fake}):
        _stub_urlopen(monkeypatch, ok=False)
        with (
            patch(
                "hermes_cli.browser_connect.launch_chrome_debug",
                return_value=ChromeDebugLaunch(),
            ),
            patch("hermes_cli.browser_connect.manual_chrome_debug_command", return_value=None),
            patch(
                "hermes_cli.browser_connect.get_chrome_debug_candidates",
                return_value=[],
            ),
        ):
            resp = server.handle_request(
                {
                    "id": "1",
                    "method": "browser.manage",
                    "params": {"action": "connect", "url": "http://localhost:9222"},
                }
            )

    assert resp["result"]["connected"] is False
    assert resp["result"]["messages"]  # bundled list still populated
    assert [evt for evt, _ in emitted if evt == "browser.progress"] == []


def test_browser_manage_connect_handles_null_url(monkeypatch):
    """Explicit ``{"url": null}`` (or empty string) must fall back to the
    default loopback URL instead of raising a TypeError that gets swallowed
    by the outer 5031 catch."""
    monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
    fake = types.SimpleNamespace(
        cleanup_all_browsers=lambda: None,
        _get_cdp_override=lambda: os.environ.get("BROWSER_CDP_URL", ""),
    )
    with patch.dict(sys.modules, {"tools.browser_tool_lifecycle": fake}):
        _stub_urlopen(monkeypatch, ok=True)
        resp = server.handle_request(
            {
                "id": "1",
                "method": "browser.manage",
                "params": {"action": "connect", "url": None},
            }
        )

    assert resp["result"]["connected"] is True
    assert resp["result"]["url"] == "http://127.0.0.1:9222"


def test_browser_manage_connect_rejects_non_string_url(monkeypatch):
    monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
    resp = server.handle_request(
        {
            "id": "1",
            "method": "browser.manage",
            "params": {"action": "connect", "url": 9222},
        }
    )

    assert resp["error"]["code"] == 4015
    assert "BROWSER_CDP_URL" not in os.environ


def test_browser_manage_connect_default_local_retries_after_launch(monkeypatch):
    monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
    monkeypatch.setattr(server.time, "sleep", lambda _seconds: None)
    fake = types.SimpleNamespace(
        cleanup_all_browsers=lambda: None,
        _get_cdp_override=lambda: os.environ.get("BROWSER_CDP_URL", ""),
    )

    class _Resp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    # IPv4 answers only from the 3rd probe onwards (browser still starting);
    # the IPv6 loopback never answers.
    attempts = {"n": 0}

    def _opener(url, timeout=2.0):  # noqa: ARG001 — match urllib signature
        if "[::1]" in url:
            raise OSError("no IPv6 listener")
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise OSError("not ready")
        return _Resp()

    import urllib.request

    monkeypatch.setattr(urllib.request.OpenerDirector, "open", lambda _self, url, *a, timeout=2.0, **k: _opener(url, timeout=timeout))
    launched = ChromeDebugLaunch(launched=True)
    with patch.dict(sys.modules, {"tools.browser_tool_lifecycle": fake}):
        with (
            patch(
                "hermes_cli.browser_connect.launch_chrome_debug",
                return_value=launched,
            ),
            patch("hermes_cli.browser_connect.local_port_in_use", return_value=False),
        ):
            resp = server.handle_request(
                {"id": "1", "method": "browser.manage", "params": {"action": "connect"}}
            )

    assert resp["result"]["connected"] is True
    assert resp["result"]["url"] == "http://127.0.0.1:9222"
    assert os.environ["BROWSER_CDP_URL"] == "http://127.0.0.1:9222"


def test_browser_manage_connect_finds_ipv6_only_browser(monkeypatch):
    """Regression: an IDE debugger squatting 127.0.0.1:9222 pushes the debug
    browser onto [::1]:9222. Connect must discover and adopt the IPv6
    endpoint instead of timing out against the squatter."""
    monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
    fake = types.SimpleNamespace(
        cleanup_all_browsers=lambda: None,
        _get_cdp_override=lambda: os.environ.get("BROWSER_CDP_URL", ""),
    )

    class _Resp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    def _opener(url, timeout=2.0):  # noqa: ARG001 — match urllib signature
        if "[::1]" in url:
            return _Resp()
        raise OSError("IPv4 loopback held by a non-CDP squatter")

    import urllib.request

    monkeypatch.setattr(urllib.request.OpenerDirector, "open", lambda _self, url, *a, timeout=2.0, **k: _opener(url, timeout=timeout))
    with patch.dict(sys.modules, {"tools.browser_tool_lifecycle": fake}):
        resp = server.handle_request(
            {"id": "1", "method": "browser.manage", "params": {"action": "connect"}}
        )

    assert resp["result"]["connected"] is True
    assert resp["result"]["url"] == "http://[::1]:9222"
    assert os.environ["BROWSER_CDP_URL"] == "http://[::1]:9222"


def test_browser_manage_connect_squatted_port_launches_on_alternate(monkeypatch):
    """When neither loopback speaks CDP but the port is held by another
    application, connect must pick an alternate port for the launch and
    say so — never fight the squatter for 9222."""
    monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
    monkeypatch.setattr(server.time, "sleep", lambda _seconds: None)
    fake = types.SimpleNamespace(
        cleanup_all_browsers=lambda: None,
        _get_cdp_override=lambda: os.environ.get("BROWSER_CDP_URL", ""),
    )

    class _Resp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    def _opener(url, timeout=2.0):  # noqa: ARG001 — match urllib signature
        if ":9223" in url and "127.0.0.1" in url:
            return _Resp()  # relaunched browser comes up on the alternate port
        raise OSError("9222 squatted / nothing else listening")

    import urllib.request

    monkeypatch.setattr(urllib.request.OpenerDirector, "open", lambda _self, url, *a, timeout=2.0, **k: _opener(url, timeout=timeout))
    launch_ports: list[int] = []

    def _launch(port, _system):
        launch_ports.append(port)
        return ChromeDebugLaunch(launched=True)

    with patch.dict(sys.modules, {"tools.browser_tool_lifecycle": fake}):
        with (
            patch("hermes_cli.browser_connect.launch_chrome_debug", side_effect=_launch),
            patch("hermes_cli.browser_connect.local_port_in_use", return_value=True),
            patch("hermes_cli.browser_connect.find_free_debug_port", return_value=9223),
        ):
            resp = server.handle_request(
                {"id": "1", "method": "browser.manage", "params": {"action": "connect"}}
            )

    assert launch_ports == [9223]
    assert resp["result"]["connected"] is True
    assert resp["result"]["url"] == "http://127.0.0.1:9223"
    assert os.environ["BROWSER_CDP_URL"] == "http://127.0.0.1:9223"


def test_browser_manage_connect_rejects_unreachable_endpoint(monkeypatch):
    """An unreachable endpoint must NOT mutate the env or reap sessions."""
    monkeypatch.setenv("BROWSER_CDP_URL", "http://existing:9222")
    cleanup_calls: list[str] = []
    fake = types.SimpleNamespace(
        cleanup_all_browsers=lambda: cleanup_calls.append(
            os.environ.get("BROWSER_CDP_URL", "")
        ),
        _get_cdp_override=lambda: os.environ.get("BROWSER_CDP_URL", ""),
    )
    with patch.dict(sys.modules, {"tools.browser_tool_lifecycle": fake}):
        _stub_urlopen(monkeypatch, ok=False)
        resp = server.handle_request(
            {
                "id": "1",
                "method": "browser.manage",
                "params": {"action": "connect", "url": "http://unreachable:9222"},
            }
        )

    assert "error" in resp
    # Env preserved; nothing reaped.
    assert os.environ["BROWSER_CDP_URL"] == "http://existing:9222"
    assert cleanup_calls == []


def test_browser_manage_connect_normalizes_bare_host_port(monkeypatch):
    """Persist a parsed `scheme://host:port` URL so `_get_cdp_override`
    can normalize it; storing a bare host:port would break subsequent
    tool calls (Copilot review on #17120)."""
    monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
    fake = types.SimpleNamespace(
        cleanup_all_browsers=lambda: None,
        _get_cdp_override=lambda: os.environ.get("BROWSER_CDP_URL", ""),
    )
    with patch.dict(sys.modules, {"tools.browser_tool_lifecycle": fake}):
        _stub_urlopen(monkeypatch, ok=True)
        resp = server.handle_request(
            {
                "id": "1",
                "method": "browser.manage",
                "params": {"action": "connect", "url": "127.0.0.1:9222"},
            }
        )

    assert resp["result"]["connected"] is True
    # Bare host:port got promoted to a full URL with explicit scheme.
    assert resp["result"]["url"].startswith("http://")
    assert os.environ["BROWSER_CDP_URL"].startswith("http://")


def test_browser_manage_connect_strips_discovery_path(monkeypatch):
    """User-supplied discovery paths like `/json` or `/json/version`
    must collapse to bare `scheme://host:port`; otherwise
    ``_resolve_cdp_override`` will append ``/json/version`` again and
    produce a duplicate path (Copilot review round-2 on #17120)."""
    monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
    fake = types.SimpleNamespace(
        cleanup_all_browsers=lambda: None,
        _get_cdp_override=lambda: os.environ.get("BROWSER_CDP_URL", ""),
    )
    with patch.dict(sys.modules, {"tools.browser_tool_lifecycle": fake}):
        _stub_urlopen(monkeypatch, ok=True)
        resp = server.handle_request(
            {
                "id": "1",
                "method": "browser.manage",
                "params": {"action": "connect", "url": "http://127.0.0.1:9222/json"},
            }
        )

    assert resp["result"]["connected"] is True
    assert resp["result"]["url"] == "http://127.0.0.1:9222"
    assert os.environ["BROWSER_CDP_URL"] == "http://127.0.0.1:9222"


def test_browser_manage_connect_preserves_devtools_browser_endpoint(monkeypatch):
    """Concrete devtools websocket endpoints (e.g. Browserbase) must
    survive verbatim — we only collapse discovery-style paths."""
    monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
    fake = types.SimpleNamespace(
        cleanup_all_browsers=lambda: None,
        _get_cdp_override=lambda: os.environ.get("BROWSER_CDP_URL", ""),
    )
    concrete = "ws://browserbase.example/devtools/browser/abc123"

    class _OkSocket:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    with patch.dict(sys.modules, {"tools.browser_tool_lifecycle": fake}):
        # If urlopen is reached for a concrete ws endpoint, the test
        # would still pass because _stub_urlopen returned ok=True before;
        # patch it to assert-fail so we prove the HTTP probe is skipped.
        with patch(
            "urllib.request.urlopen", side_effect=AssertionError("urlopen called")
        ):
            with patch("socket.create_connection", return_value=_OkSocket()):
                resp = server.handle_request(
                    {
                        "id": "1",
                        "method": "browser.manage",
                        "params": {"action": "connect", "url": concrete},
                    }
                )

    assert resp["result"]["connected"] is True
    assert resp["result"]["url"] == concrete
    assert os.environ["BROWSER_CDP_URL"] == concrete


def test_browser_manage_connect_local_devtools_ws_preserves_path(monkeypatch):
    """Regression: ``ws://127.0.0.1:9222/devtools/browser/<id>`` is a real
    connectable endpoint; default-local normalization must not strip the
    ``/devtools/browser/...`` path or it breaks valid local CDP connects."""
    monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
    fake = types.SimpleNamespace(
        cleanup_all_browsers=lambda: None,
        _get_cdp_override=lambda: os.environ.get("BROWSER_CDP_URL", ""),
    )
    concrete = "ws://127.0.0.1:9222/devtools/browser/abc123"

    class _OkSocket:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    with patch.dict(sys.modules, {"tools.browser_tool_lifecycle": fake}):
        with patch("socket.create_connection", return_value=_OkSocket()):
            resp = server.handle_request(
                {
                    "id": "1",
                    "method": "browser.manage",
                    "params": {"action": "connect", "url": concrete},
                }
            )

    assert resp["result"]["connected"] is True
    assert resp["result"]["url"] == concrete
    assert os.environ["BROWSER_CDP_URL"] == concrete


def test_browser_manage_connect_rejects_invalid_port(monkeypatch):
    monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
    resp = server.handle_request(
        {
            "id": "1",
            "method": "browser.manage",
            "params": {"action": "connect", "url": "http://localhost:abc"},
        }
    )

    assert resp["error"]["code"] == 4015
    assert "BROWSER_CDP_URL" not in os.environ


def test_browser_manage_connect_rejects_missing_host(monkeypatch):
    monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
    resp = server.handle_request(
        {
            "id": "1",
            "method": "browser.manage",
            "params": {"action": "connect", "url": "http://:9222"},
        }
    )

    assert resp["error"]["code"] == 4015
    assert "BROWSER_CDP_URL" not in os.environ


def test_browser_manage_connect_concrete_ws_skips_http_probe(monkeypatch):
    """Regression for round-2 Copilot review: a hosted CDP endpoint
    (no HTTP discovery) must connect via TCP-only reachability check.
    The HTTP probe used to reject these even though they're valid."""
    monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
    fake = types.SimpleNamespace(
        cleanup_all_browsers=lambda: None,
        _get_cdp_override=lambda: os.environ.get("BROWSER_CDP_URL", ""),
    )
    concrete = "wss://chrome.browserless.io/devtools/browser/sess-1"

    seen_targets: list[tuple[str, int]] = []

    class _OkSocket:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def _fake_create_connection(addr, timeout=None):
        seen_targets.append(addr)
        return _OkSocket()

    with patch.dict(sys.modules, {"tools.browser_tool_lifecycle": fake}):
        # urlopen would 404/ECONNREFUSED on a real hosted CDP endpoint;
        # asserting it's never called proves the probe was skipped.
        with patch(
            "urllib.request.urlopen", side_effect=AssertionError("urlopen called")
        ):
            with patch("socket.create_connection", side_effect=_fake_create_connection):
                resp = server.handle_request(
                    {
                        "id": "1",
                        "method": "browser.manage",
                        "params": {"action": "connect", "url": concrete},
                    }
                )

    assert resp["result"] == {"connected": True, "url": concrete}
    # wss → port 443, host preserved verbatim.
    assert seen_targets == [("chrome.browserless.io", 443)]


def test_browser_manage_connect_concrete_ws_tcp_unreachable(monkeypatch):
    """If the TCP reachability check fails for a concrete ws endpoint,
    return a clear 5031 error — no fallback to the HTTP probe (which
    can never succeed for these URLs anyway)."""
    monkeypatch.delenv("BROWSER_CDP_URL", raising=False)
    fake = types.SimpleNamespace(
        cleanup_all_browsers=lambda: None,
        _get_cdp_override=lambda: os.environ.get("BROWSER_CDP_URL", ""),
    )
    concrete = "ws://offline.example/devtools/browser/missing"

    with patch.dict(sys.modules, {"tools.browser_tool_lifecycle": fake}):
        with patch("socket.create_connection", side_effect=OSError("ECONNREFUSED")):
            resp = server.handle_request(
                {
                    "id": "1",
                    "method": "browser.manage",
                    "params": {"action": "connect", "url": concrete},
                }
            )

    assert "error" in resp
    assert resp["error"]["code"] == 5031


def test_browser_manage_disconnect_drops_env_and_cleans(monkeypatch):
    monkeypatch.setenv("BROWSER_CDP_URL", "http://127.0.0.1:9222")
    cleanup_count = {"n": 0}
    fake = types.SimpleNamespace(
        cleanup_all_browsers=lambda: cleanup_count.__setitem__(
            "n", cleanup_count["n"] + 1
        ),
        _get_cdp_override=lambda: os.environ.get("BROWSER_CDP_URL", ""),
    )
    with patch.dict(sys.modules, {"tools.browser_tool_lifecycle": fake}):
        resp = server.handle_request(
            {"id": "1", "method": "browser.manage", "params": {"action": "disconnect"}}
        )

    assert resp["result"] == {"connected": False}
    assert "BROWSER_CDP_URL" not in os.environ
    # Two cleanups: once before env removal, once after, matching connect.
    assert cleanup_count["n"] == 2


# ── config.get indicator normalization ───────────────────────────────




def test_config_get_indicator_normalizes_casing_and_whitespace(monkeypatch):
    """Hand-edited config.yaml stays consistent with what the TUI shows.

    Frontend's `normalizeIndicatorStyle` lowercases + trims, so config.get
    must do the same — otherwise `/indicator` prints 'EMOJI ' while the
    UI is actually rendering the kaomoji default."""
    monkeypatch.setattr(
        server, "_load_cfg", lambda: {"display": {"tui_status_indicator": " EMOJI "}}
    )
    resp = server.handle_request(
        {"id": "1", "method": "config.get", "params": {"key": "indicator"}}
    )
    assert resp["result"] == {"value": "emoji"}


def test_config_get_indicator_falls_back_to_default_for_unknown(monkeypatch):
    """An unknown value in config.yaml falls back to the same default
    the frontend uses (`_INDICATOR_DEFAULT`)."""
    monkeypatch.setattr(
        server, "_load_cfg", lambda: {"display": {"tui_status_indicator": "rainbow"}}
    )
    resp = server.handle_request(
        {"id": "1", "method": "config.get", "params": {"key": "indicator"}}
    )
    assert resp["result"] == {"value": "kaomoji"}


# ── config.set indicator validation ──────────────────────────────────


def test_config_set_indicator_accepts_known_value(monkeypatch):
    written: dict = {}
    monkeypatch.setattr(
        server,
        "_write_config_key",
        lambda k, v: written.update({k: v}),
    )
    resp = server.handle_request(
        {
            "id": "1",
            "method": "config.set",
            "params": {"key": "indicator", "value": "EMOJI"},
        }
    )
    assert resp["result"] == {"key": "indicator", "value": "emoji"}
    assert written == {"display.tui_status_indicator": "emoji"}


# ── reload.env ───────────────────────────────────────────────────────




def test_reload_env_rpc_surfaces_errors(monkeypatch):
    def _broken():
        raise RuntimeError("env path locked")

    fake = types.SimpleNamespace(reload_env=_broken)
    with patch.dict(sys.modules, {"hermes_cli.config": fake}):
        resp = server.handle_request({"id": "1", "method": "reload.env", "params": {}})

    assert "error" in resp
    assert "env path locked" in resp["error"]["message"]


def test_make_agent_reads_nested_max_turns(monkeypatch):
    _setup_make_agent_mocks(monkeypatch, {"agent": {"max_turns": 200}})

    with patch("run_agent.AIAgent") as mock_agent:
        server._make_agent("sid1", "key1")

    assert mock_agent.call_args.kwargs["max_iterations"] == 200


def test_make_agent_nested_max_turns_takes_priority(monkeypatch):
    _setup_make_agent_mocks(
        monkeypatch, {"agent": {"max_turns": 400}, "max_turns": 100}
    )

    with patch("run_agent.AIAgent") as mock_agent:
        server._make_agent("sid1", "key1")

    assert mock_agent.call_args.kwargs["max_iterations"] == 400


def test_make_agent_uses_session_runtime_overrides(monkeypatch):
    _setup_make_agent_mocks(monkeypatch, {})
    resolved = {}

    def fake_resolve_runtime_provider(requested=None, target_model=None):
        resolved["requested"] = requested
        resolved["target_model"] = target_model
        return {
            "provider": requested,
            "base_url": None,
            "api_key": None,
            "api_mode": None,
            "command": None,
            "args": None,
            "credential_pool": None,
        }

    monkeypatch.setattr(
        "hermes_cli.runtime_provider.resolve_runtime_provider",
        fake_resolve_runtime_provider,
    )

    with patch("run_agent.AIAgent") as mock_agent:
        server._make_agent(
            "sid1",
            "key1",
            model_override="gpt-5.4",
            provider_override="openai-codex",
            reasoning_config_override={"enabled": True, "effort": "high"},
            service_tier_override="priority",
        )

    assert resolved == {"requested": "openai-codex", "target_model": "gpt-5.4"}
    assert mock_agent.call_args.kwargs["model"] == "gpt-5.4"
    assert mock_agent.call_args.kwargs["provider"] == "openai-codex"
    assert mock_agent.call_args.kwargs["reasoning_config"] == {"enabled": True, "effort": "high"}
    assert mock_agent.call_args.kwargs["service_tier"] == "priority"


def test_make_agent_handles_null_agent_config(monkeypatch):
    _setup_make_agent_mocks(monkeypatch, {"agent": None, "max_turns": 80})

    with patch("run_agent.AIAgent") as mock_agent:
        server._make_agent("sid1", "key1")

    assert mock_agent.call_args.kwargs["max_iterations"] == 80


def test_background_agent_kwargs_reads_nested_max_turns(monkeypatch):
    monkeypatch.setattr(server, "_load_cfg", lambda: {"agent": {"max_turns": 300}})

    kwargs = server._background_agent_kwargs(_FakeAgentForBackground(), "task_1")

    assert kwargs["max_iterations"] == 300


def test_background_agent_kwargs_falls_back_to_root_max_turns(monkeypatch):
    monkeypatch.setattr(server, "_load_cfg", lambda: {"max_turns": 50})

    kwargs = server._background_agent_kwargs(_FakeAgentForBackground(), "task_1")

    assert kwargs["max_iterations"] == 50


def test_background_agent_kwargs_handles_null_agent_config(monkeypatch):
    monkeypatch.setattr(server, "_load_cfg", lambda: {"agent": None, "max_turns": 40})

    kwargs = server._background_agent_kwargs(_FakeAgentForBackground(), "task_1")

    assert kwargs["max_iterations"] == 40


def test_notification_poller_delivers_completion(monkeypatch):
    """Poller picks up completion events and triggers agent turns."""
    import queue as _queue_mod

    from tools.process_registry import process_registry

    turns = []
    emitted = []

    class _Agent:
        def run_conversation(self, prompt, conversation_history=None, stream_callback=None, **_kwargs):
            turns.append(prompt)
            return {
                "final_response": "ok",
                "messages": [{"role": "assistant", "content": "ok"}],
            }

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None, **_thread_options):
            self._target = target
        def start(self):
            self._target()

    sess = _session(agent=_Agent())
    server._sessions["sid_poll"] = sess
    monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)
    monkeypatch.setattr(server, "_emit", lambda *a, **kw: emitted.append(a))
    monkeypatch.setattr(server, "make_stream_renderer", lambda cols: None)
    monkeypatch.setattr(server, "render_message", lambda raw, cols: None)

    # Isolate the completion queue for the duration of this test. The poller
    # reads process_registry.completion_queue by attribute at runtime; the
    # event below carries no session_key, so any *other* poller (a leaked
    # daemon thread from another test, or a concurrent one in the same xdist
    # worker) is allowed to dequeue and dispatch it to its own session — whose
    # agent may be a fixture double without run_conversation. A fresh Queue
    # here fully isolates this test; monkeypatch restores the original on
    # teardown. (Same pattern as test_notification_poller_requeues_when_busy.)
    isolated_queue: _queue_mod.Queue = _queue_mod.Queue()
    monkeypatch.setattr(process_registry, "completion_queue", isolated_queue)
    process_registry._completion_consumed.discard("proc_poller_test")

    stop = threading.Event()

    # Put event on queue, then immediately signal stop so the poller
    # runs exactly one iteration.
    isolated_queue.put({
        "type": "completion",
        "session_id": "proc_poller_test",
        "command": "echo hello",
        "exit_code": 0,
        "output": "hello",
    })
    stop.set()

    try:
        server._notification_poller_loop(stop, "sid_poll", sess)

        # Should have emitted a status.update with kind=process
        status_calls = [a for a in emitted if a[0] == "status.update"]
        assert len(status_calls) >= 1
        assert status_calls[0][2]["kind"] == "process"

        # Should have triggered an agent turn
        assert len(turns) == 1
        assert "proc_poller_test" in turns[0]
    finally:
        server._sessions.pop("sid_poll", None)
        while not process_registry.completion_queue.empty():
            process_registry.completion_queue.get_nowait()


def test_notification_poller_skips_consumed(monkeypatch):
    """Already-consumed completions are not dispatched by the poller."""
    import queue as _queue_mod

    from tools.process_registry import process_registry

    turns = []

    class _Agent:
        def run_conversation(self, prompt, conversation_history=None, stream_callback=None, **_kwargs):
            turns.append(prompt)
            return {"final_response": "ok", "messages": []}

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None, **_thread_options):
            self._target = target
        def start(self):
            self._target()

    sess = _session(agent=_Agent())
    server._sessions["sid_skip"] = sess
    monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)
    monkeypatch.setattr(server, "_emit", lambda *a, **kw: None)
    monkeypatch.setattr(server, "make_stream_renderer", lambda cols: None)
    monkeypatch.setattr(server, "render_message", lambda raw, cols: None)

    # Isolate the completion queue so a concurrent/leaked poller in the same
    # xdist worker can't dequeue this session_key-less event before our poller
    # does. monkeypatch restores the shared singleton on teardown. (Same
    # pattern as test_notification_poller_requeues_when_busy.)
    isolated_queue: _queue_mod.Queue = _queue_mod.Queue()
    monkeypatch.setattr(process_registry, "completion_queue", isolated_queue)

    process_registry._completion_consumed.add("proc_already_done")
    isolated_queue.put({
        "type": "completion",
        "session_id": "proc_already_done",
        "command": "echo x",
        "exit_code": 0,
        "output": "x",
    })

    stop = threading.Event()
    stop.set()

    try:
        server._notification_poller_loop(stop, "sid_skip", sess)
        assert len(turns) == 0
    finally:
        server._sessions.pop("sid_skip", None)
        process_registry._completion_consumed.discard("proc_already_done")
        while not process_registry.completion_queue.empty():
            process_registry.completion_queue.get_nowait()


def test_notification_poller_requeues_when_busy(monkeypatch):
    """When the agent is busy, the poller requeues the event."""
    import queue as _queue_mod

    from tools.process_registry import process_registry

    emitted = []

    sess = _session(running=True)  # agent is busy
    server._sessions["sid_busy"] = sess
    monkeypatch.setattr(server, "_emit", lambda *a, **kw: emitted.append(a))

    # Isolate the completion queue for the duration of this test. The poller
    # reads process_registry.completion_queue by attribute at runtime, so a
    # fresh Queue here means no concurrently-running test in the same xdist
    # worker can put/get on the shared singleton mid-run and drain the event
    # we expect to be requeued. monkeypatch restores the original on teardown.
    isolated_queue: _queue_mod.Queue = _queue_mod.Queue()
    monkeypatch.setattr(process_registry, "completion_queue", isolated_queue)
    process_registry._completion_consumed.discard("proc_busy_test")

    evt = {
        "type": "completion",
        "session_id": "proc_busy_test",
        "command": "make build",
        "exit_code": 0,
        "output": "ok",
    }
    isolated_queue.put(evt)

    stop = threading.Event()
    stop.set()

    try:
        server._notification_poller_loop(stop, "sid_busy", sess)

        # Status update was emitted (user sees it)
        status_calls = [a for a in emitted if a[0] == "status.update"]
        assert len(status_calls) == 1

        # Event was requeued (agent was busy, no turn triggered)
        assert not isolated_queue.empty()
        requeued = isolated_queue.get_nowait()
        assert requeued["session_id"] == "proc_busy_test"
    finally:
        server._sessions.pop("sid_busy", None)
        while not process_registry.completion_queue.empty():
            process_registry.completion_queue.get_nowait()
