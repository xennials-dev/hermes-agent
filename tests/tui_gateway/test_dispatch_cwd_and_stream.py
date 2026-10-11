"""tui_gateway.server — turn dispatch, session cwd resolution, stream writes and usage ticker.

Split from test_tui_gateway_server.py; shared fixtures and helpers live
in tests/tui_gateway/_server_test_helpers.py.
"""

import json
import logging
import os
import sys
import threading
import time
import types
from datetime import datetime
from hermes_constants import reset_hermes_home_override, set_hermes_home_override
from hermes_cli.active_sessions import active_session_registry_snapshot
from tui_gateway import server

from tests.tui_gateway._server_test_helpers import (
    _BrokenStdout,
    _ChunkyStdout,
    _ImmediateThread,
    _dispatch_sync,
    _neuter_agent_prewarm_timer,  # autouse
    _reap_leaked_notification_pollers,  # autouse
    _session,
    _write_profile_cfg,
)


def test_session_slot_is_claimed_on_first_turn_not_on_create(monkeypatch, tmp_path):
    home = tmp_path / ".hermes"
    home.mkdir()
    (home / "config.yaml").write_text("max_concurrent_sessions: 1\n", encoding="utf-8")
    token = set_hermes_home_override(home)

    def _clear_server_sessions():
        for session in list(server._sessions.values()):
            server._teardown_session(session)
        server._sessions.clear()

    try:
        server._cfg_cache = None
        server._cfg_sig = None
        server._cfg_path = None
        _clear_server_sessions()
        monkeypatch.setattr(server, "_start_agent_build", lambda *args, **kwargs: None)
        monkeypatch.setattr(server, "_completion_cwd", lambda params=None: str(tmp_path))

        # Opening a chat must NOT take a slot. Every tile paint and every
        # background reconnect-resume calls session.create, and an unprompted
        # draft has no DB row and is filtered out of the sidebar — so a slot
        # held here is invisible to the user while still starving the other
        # surfaces that share this cap.
        first = server._methods["session.create"]("r1", {"cols": 80})
        second = server._methods["session.create"]("r2", {"cols": 80})
        assert "result" in first and "result" in second
        sid = first["result"]["session_id"]
        other = second["result"]["session_id"]
        assert active_session_registry_snapshot() == []

        # The first turn is what claims the slot, and is re-entrant.
        assert server._ensure_active_session_slot(sid, server._sessions[sid]) is None
        assert server._ensure_active_session_slot(sid, server._sessions[sid]) is None
        assert len(active_session_registry_snapshot()) == 1

        blocked = server._ensure_active_session_slot(other, server._sessions[other])
        assert blocked  # refusal reason returned; exact wording not pinned

        closed = server._methods["session.close"]("r3", {"session_id": sid})
        assert closed["result"]["closed"] is True
        assert active_session_registry_snapshot() == []

        assert server._ensure_active_session_slot(other, server._sessions[other]) is None
    finally:
        _clear_server_sessions()
        server._cfg_cache = None
        server._cfg_sig = None
        server._cfg_path = None
        reset_hermes_home_override(token)


def test_session_context_uses_session_cwd(monkeypatch, tmp_path):
    """Desktop/TUI sessions must pin the agent cwd per session.

    The gateway process itself is often launched from apps/desktop in dev, so
    falling back to os.getcwd() makes agents answer from the desktop app folder
    even when the sidebar/session cwd is a real project.
    """
    from agent.runtime_cwd import resolve_agent_cwd

    sid = "cwd-sid"
    session_key = "cwd-key"
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").mkdir()
    launcher = tmp_path / "apps" / "desktop"
    launcher.mkdir(parents=True)

    server._sessions[sid] = {"session_key": session_key, "cwd": str(project)}
    monkeypatch.delenv("TERMINAL_CWD", raising=False)
    monkeypatch.chdir(launcher)

    tokens = server._set_session_context(session_key)
    try:
        assert resolve_agent_cwd() == project
    finally:
        server._clear_session_context(tokens)
        server._sessions.pop(sid, None)


def test_handoff_fail_marks_only_inflight_rows(monkeypatch):
    class DbContext:
        def __init__(self, db):
            self.db = db

        def __enter__(self):
            return self.db

        def __exit__(self, *_args):
            return False

    class FakeDb:
        def __init__(self, state):
            self.state = state
            self.failed_with = None

        def get_handoff_state(self, _key):
            return {"state": self.state, "platform": "telegram", "error": None}

        def fail_handoff(self, _key, error):
            self.failed_with = error
            self.state = "failed"

    sid = "rt-handoff"
    server._sessions[sid] = {"session_key": "stored-handoff"}
    try:
        pending = FakeDb("pending")
        monkeypatch.setattr(server, "_session_db", lambda _session: DbContext(pending))
        result = server._methods["handoff.fail"]("r1", {"session_id": sid, "error": "timed out"})
        assert result["result"] == {"failed": True, "state": "failed"}
        assert pending.failed_with == "timed out"

        completed = FakeDb("completed")
        monkeypatch.setattr(server, "_session_db", lambda _session: DbContext(completed))
        result = server._methods["handoff.fail"]("r2", {"session_id": sid, "error": "late timeout"})
        assert result["result"] == {"failed": False, "state": "completed"}
        assert completed.failed_with is None
    finally:
        server._sessions.pop(sid, None)


def test_dashboard_process_isolation_config_coerces_raw_values():
    cfg = {
        "dashboard": {
            "turn_isolation": "yes",
            "compute_host_heartbeat_secs": "30",
            "compute_host_respawn_max": "0",
        }
    }

    assert server._load_dashboard_process_isolation_config(cfg) == {
        "turn_isolation": True,
        "compute_host_heartbeat_secs": 30,
        "compute_host_respawn_max": 0,
    }

    malformed = {"dashboard": "enabled"}
    assert server._load_dashboard_process_isolation_config(malformed) == {
        "turn_isolation": False,
        "compute_host_heartbeat_secs": 15,
        "compute_host_respawn_max": 3,
    }


def test_prompt_submit_dispatches_to_compute_host_when_turn_isolation_enabled(monkeypatch):
    class FakeSupervisor:
        def __init__(self):
            self.frames = []
            self.callback = None

        def submit_turn(self, frame, *, on_complete=None):
            self.frames.append(frame)
            self.callback = on_complete
            return frame["request_id"]

    fake_supervisor = FakeSupervisor()
    seed_history = [{"role": "user", "content": "previous"}]
    server._sessions["iso-sid"] = _session(history=list(seed_history))
    server._sessions["iso-sid"]["agent"] = None
    server._sessions["iso-sid"]["agent_ready"] = threading.Event()
    parent_writes = {"ensure_session": 0, "persist_seed": 0}
    monkeypatch.setattr(
        server,
        "_load_cfg",
        lambda: {"dashboard": {"turn_isolation": True}},
    )
    monkeypatch.setattr(
        server,
        "_ensure_session_db_row",
        lambda _session: parent_writes.__setitem__(
            "ensure_session", parent_writes["ensure_session"] + 1
        ),
    )
    monkeypatch.setattr(
        server,
        "_persist_branch_seed",
        lambda _session: parent_writes.__setitem__(
            "persist_seed", parent_writes["persist_seed"] + 1
        ),
    )
    monkeypatch.setattr(server, "_get_compute_host_supervisor", lambda _cfg=None: fake_supervisor)

    try:
        resp = server.handle_request(
            {
                "id": "submit",
                "method": "prompt.submit",
                "params": {"session_id": "iso-sid", "text": "hello"},
            }
        )
        assert resp["result"] == {"status": "streaming", "turn_isolation": True}
        assert fake_supervisor.frames[0]["type"] == "turn.start"
        assert fake_supervisor.frames[0]["sid"] == "iso-sid"
        assert fake_supervisor.frames[0]["text"] == "hello"
        assert fake_supervisor.frames[0]["history"] == seed_history
        assert server._sessions["iso-sid"]["history"] == seed_history
        assert parent_writes == {"ensure_session": 0, "persist_seed": 0}
        assert server._sessions["iso-sid"]["running"] is True

        fake_supervisor.callback(
            {
                "type": "turn.end",
                "sid": "iso-sid",
                "request_id": "submit",
                "history_version": 1,
            }
        )
        assert server._sessions["iso-sid"]["running"] is False
        assert server._sessions["iso-sid"]["history_version"] == 1
    finally:
        server._sessions.pop("iso-sid", None)


def test_compute_host_explicit_images_do_not_clear_later_attachment(monkeypatch):
    class _Supervisor:
        def submit_turn(self, _frame, *, on_complete=None):
            session["attached_images"].append("/tmp/c.png")

    session = _session(attached_images=[])
    monkeypatch.setattr(server, "_get_compute_host_supervisor", lambda _cfg=None: _Supervisor())

    response = server._submit_prompt_to_compute_host(
        "r1", "sid", session, "B", image_paths=["/tmp/b.png"]
    )

    assert response["result"]["status"] == "streaming"
    assert session["attached_images"] == ["/tmp/c.png"]


def test_prompt_submit_unknown_session_logs_warning(caplog):
    """A submit against a reaped runtime id must leave a diagnosable trace.

    Regression for #90428: messages sent into a session whose in-memory
    runtime was detached on WS disconnect and orphan-reaped vanished
    silently — the 4001 was never logged, so "request arrived and was
    rejected" was indistinguishable from "request never arrived".
    """
    for session in list(server._sessions.values()):
        server._teardown_session(session)
    server._sessions.clear()

    with caplog.at_level(logging.WARNING, logger="tui_gateway.server"):
        resp = _dispatch_sync(
            {
                "id": "r1",
                "method": "prompt.submit",
                "params": {"session_id": "gone-sid", "text": "hello"},
            }
        )

    assert resp["id"] == "r1"
    assert resp["error"]["code"] == 4001
    # The runtime id and method name must be in the warning so a client looping
    # on a stale runtime id is attributable from logs (exact wording not pinned).
    assert any(
        rec.levelno >= logging.WARNING
        and "gone-sid" in rec.getMessage()
        and "prompt.submit" in rec.getMessage()
        for rec in caplog.records
    )


def test_prompt_submit_fails_open_inline_when_compute_host_dispatch_breaks(monkeypatch):
    class _BrokenSupervisor:
        def submit_turn(self, frame, *, on_complete=None):
            if on_complete is not None:
                on_complete(
                    {
                        "type": "turn.error",
                        "request_id": frame["request_id"],
                        "reason": "send_failed",
                        "message": "broken pipe",
                    }
                )
            raise BrokenPipeError("broken pipe")

    class _ImmediateThread:
        def __init__(self, target=None, **_kwargs):
            self._target = target

        def start(self):
            assert self._target is not None
            self._target()

    session = _session(agent=None, agent_ready=threading.Event())
    server._sessions["iso-fallback"] = session
    inline_calls = []
    monkeypatch.setattr(server, "_load_cfg", lambda: {"dashboard": {"turn_isolation": True}})
    monkeypatch.setattr(server, "_get_compute_host_supervisor", lambda _cfg=None: _BrokenSupervisor())
    monkeypatch.setattr(server, "_ensure_session_db_row", lambda _session: None)
    monkeypatch.setattr(server, "_persist_branch_seed", lambda _session: None)
    monkeypatch.setattr(server, "_start_agent_build", lambda _sid, _session: None)
    monkeypatch.setattr(server, "_wait_agent", lambda _session, _rid: None)
    # The deferred inline-fallback thread now waits via the patient variant.
    monkeypatch.setattr(server, "_wait_agent_for_prompt", lambda _session, _rid, _sid: None)
    monkeypatch.setattr(
        server,
        "_run_prompt_submit",
        lambda rid, sid, _session, text, **_kwargs: inline_calls.append((rid, sid, text)),
    )
    monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)

    try:
        resp = server.handle_request(
            {
                "id": "fallback-turn",
                "method": "prompt.submit",
                "params": {"session_id": "iso-fallback", "text": "hello"},
            }
        )
    finally:
        server._sessions.pop("iso-fallback", None)

    assert resp == {
        "jsonrpc": "2.0",
        "id": "fallback-turn",
        "result": {"status": "streaming"},
    }
    assert inline_calls == [("fallback-turn", "iso-fallback", "hello")]
    assert session.get("_compute_host_active") is not True


def test_compute_host_turn_end_updates_metadata_mirror(monkeypatch):
    # _session_info embeds get_update_result(), whose value flips whenever the
    # background update-check thread happens to finish. This test compares two
    # snapshots taken at different times, so pin the value to keep it
    # deterministic regardless of how long the preceding tests ran.
    import hermes_cli.banner as _banner

    monkeypatch.setattr(_banner, "get_update_result", lambda timeout=0.5: None)
    session = _session(
        agent=None,
        agent_ready=threading.Event(),
        history=[{"role": "user", "content": "serving process must not read this"}],
        _compute_host_active=True,
    )
    server._sessions["iso-sid"] = session
    emitted = []
    monkeypatch.setattr(server, "_emit", lambda event, sid, payload=None: emitted.append((event, sid, payload)))

    try:
        server._on_compute_host_turn_done(
            "turn-1",
            "iso-sid",
            session,
            {
                "type": "turn.end",
                "sid": "iso-sid",
                "request_id": "turn-1",
                "session_key": "rotated-session-key",
                "history_version": 4,
                "message_count": 3,
                "session_info": {
                    "model": "host-model",
                    "provider": "host-provider",
                    "system_prompt": "host system prompt",
                    "tools": {"core": ["terminal"]},
                    "usage": {"total": 140, "context_used": 80, "context_max": 1000},
                },
            },
        )

        assert session["session_key"] == "rotated-session-key"
        assert session["history_version"] == 4
        assert session["_metadata_mirror"]["model"] == "host-model"
        info = server._session_info(None, session)
        assert info["model"] == "host-model"
        assert info["provider"] == "host-provider"
        assert info["system_prompt"] == "host system prompt"
        assert info["tools"] == {"core": ["terminal"]}
        assert info["usage"]["total"] == 140
        assert "credential_warning" not in info
        assert emitted[-1] == ("session.info", "iso-sid", info)
    finally:
        server._sessions.pop("iso-sid", None)


def test_compute_host_open_request_survives_activation_and_proxies_locks_and_responses(monkeypatch):
    """A host-owned server request (batch clarify) is mirrored by the parent so `open_requests` replays it;
    `clarify.lock` and the client's response frame are relayed to the child that owns the wait."""
    class _Supervisor:
        def __init__(self):
            self.responses = []

        def respond(self, sid, params, *, timeout=15.0):
            self.responses.append((sid, dict(params), timeout))
            lock = params.get("lock") or {}
            remaining = ["q1"] if lock.get("question_id") == "q0" else []
            return {"type": "respond.ack", "response": {"result": {"status": "ok", "remaining": remaining}}}

    sid = "host-clarify"
    supervisor = _Supervisor()
    session = _session(agent=None, agent_ready=threading.Event(), _compute_host_active=True)
    server._sessions[sid] = session
    monkeypatch.setattr(server, "_load_cfg", lambda: {"dashboard": {"turn_isolation": True}})
    monkeypatch.setattr(server, "_get_compute_host_supervisor", lambda _cfg=None: supervisor)
    monkeypatch.setattr(server, "write_json", lambda _message: True)

    questions = [{"qid": "q0", "question": "First?", "choices": ["a"]}, {"qid": "q1", "question": "Second?", "choices": ["b"]}]
    try:
        server._relay_compute_host_rpc({"jsonrpc": "2.0", "id": "srq-host", "method": "clarify",
                                        "params": {"session_id": sid, "questions": questions}})

        activated = server._live_session_payload(sid, session)
        assert activated["open_requests"] == [{"id": "srq-host", "method": "clarify",
                                               "params": {"session_id": sid, "questions": questions}}]

        response = server.handle_request({"id": "lock-q0", "method": "clarify.lock",
                                          "params": {"request_id": "srq-host", "question_id": "q0", "answer": "a"}})
        assert response["result"] == {"status": "ok", "remaining": ["q1"]}
        assert supervisor.responses == [(sid, {"lock": {"request_id": "srq-host", "question_id": "q0", "answer": "a"}}, 15.0)]
        assert server._live_session_payload(sid, session)["open_requests"][0]["params"]["answers"] == {"q0": "a"}

        # The client's response frame (cancel-all) is relayed to the child and clears the mirror.
        assert server.dispatch({"jsonrpc": "2.0", "id": "srq-host", "result": {}}) is None
        assert supervisor.responses[-1] == (sid, {"frame": {"jsonrpc": "2.0", "id": "srq-host", "result": {}}}, 15.0)
        assert "open_requests" not in server._live_session_payload(sid, session)
    finally:
        server._sessions.pop(sid, None)


def test_compute_host_interrupt_forwards_when_parent_running_mirror_is_stale(monkeypatch):
    """The host, not the parent's mirrored running flag, owns interruption."""
    interrupted = []

    class _Supervisor:
        def interrupt(self, sid, *, request_id=None):
            interrupted.append((sid, request_id))

    sid = "host-stale-running"
    server._sessions[sid] = _session(
        agent=None,
        agent_ready=threading.Event(),
        _compute_host_active=True,
        running=False,
    )
    monkeypatch.setattr(server, "_load_cfg", lambda: {"dashboard": {"turn_isolation": True}})
    monkeypatch.setattr(server, "_get_compute_host_supervisor", lambda _cfg=None: _Supervisor())

    try:
        response = server.handle_request(
            {"id": "interrupt", "method": "session.interrupt", "params": {"session_id": sid}}
        )
        assert response["result"] == {"status": "interrupted", "turn_isolation": True}
        assert interrupted == [(sid, "interrupt-interrupt")]
    finally:
        server._sessions.pop(sid, None)


def test_compute_host_interrupt_skips_lazy_session_with_no_hosted_turn(monkeypatch):
    """A lazy session that never submitted a hosted turn must not spawn a host.

    ``HostSupervisor.interrupt()`` calls ``start()``, so forwarding the
    interrupt unconditionally would launch a compute-host child just to
    deliver an interrupt for a session with no work in it.
    """
    class _Supervisor:
        def interrupt(self, sid, *, request_id=None):  # pragma: no cover - must not run
            raise AssertionError("interrupt must not be forwarded for idle lazy sessions")

    sid = "lazy-idle"
    session = _session(
        agent_ready=threading.Event(),
        running=False,
    )
    session["agent"] = None  # _session() substitutes a namespace for None
    server._sessions[sid] = session
    monkeypatch.setattr(server, "_load_cfg", lambda: {"dashboard": {"turn_isolation": True}})
    monkeypatch.setattr(server, "_get_compute_host_supervisor", lambda _cfg=None: _Supervisor())

    try:
        response = server.handle_request(
            {"id": "interrupt", "method": "session.interrupt", "params": {"session_id": sid}}
        )
        assert response["result"] == {"status": "interrupted", "turn_isolation": True}
    finally:
        server._sessions.pop(sid, None)


def test_slash_exec_compress_flag_on_applies_host_control_mirror(monkeypatch):
    class _ExplodingWorker:
        def __init__(self, *args, **kwargs):
            raise AssertionError("slash worker should not run for isolated /compress")

    class _FakeSupervisor:
        def __init__(self):
            self.controls = []

        def control(self, sid, *, route_name, payload=None, wait=True, timeout=30.0, on_late_ack=None):
            self.controls.append((sid, route_name, dict(payload or {}), wait))
            return {
                "type": "control.ack",
                "sid": sid,
                "request_id": (payload or {}).get("request_id", "control-1"),
                "route_name": route_name,
                "output": "Compressed 4 → 2 messages",
                "session_key": "host-rotated-key",
                "history_version": 9,
                "message_count": 2,
                "session_info": {
                    "model": "host-model",
                    "provider": "host-provider",
                    "usage": {"total": 42},
                },
            }

    fake = _FakeSupervisor()
    session = _session(agent=None, agent_ready=threading.Event(), _compute_host_active=True)
    server._sessions["sid"] = session
    monkeypatch.setattr(server, "_load_cfg", lambda: {"dashboard": {"turn_isolation": True}})
    monkeypatch.setattr(server, "_get_compute_host_supervisor", lambda _cfg=None: fake)
    monkeypatch.setattr(server, "_SlashWorker", _ExplodingWorker)
    monkeypatch.setattr(server, "_compress_session_history", lambda *a, **k: (_ for _ in ()).throw(AssertionError("parent compressed")))
    monkeypatch.setattr(server, "_sync_session_key_after_compress", lambda *a, **k: (_ for _ in ()).throw(AssertionError("parent identity guard ran")))

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "slash.exec",
                "params": {"command": "compress focus", "session_id": "sid"},
            }
        )
    finally:
        server._sessions.pop("sid", None)

    assert resp["result"]["output"] == "Compressed 4 → 2 messages"
    assert fake.controls[0][1] == "slash.compress"
    assert fake.controls[0][2]["command"] == "/compress focus"
    assert session["session_key"] == "host-rotated-key"
    assert session["history_version"] == 9
    assert server._session_info(None, session)["model"] == "host-model"


def test_prompt_submit_golden_transcript_matches_flag_off_and_on(monkeypatch):
    class _ImmediateThread:
        def __init__(self, target=None, daemon=None, **_kwargs):
            self._target = target

        def start(self):
            assert self._target is not None
            self._target()

    class _Agent:
        model = "gold-model"
        provider = "gold-provider"
        session_id = "session-key"
        session_input_tokens = 10
        session_output_tokens = 5
        session_prompt_tokens = 10
        session_completion_tokens = 5
        session_total_tokens = 15
        session_api_calls = 1
        context_compressor = None

        def clear_interrupt(self):
            return None

        def run_conversation(self, prompt, conversation_history=None, stream_callback=None, **_kwargs):
            if stream_callback is not None:
                stream_callback("hi")
            return {
                "final_response": "hi",
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": "hi"},
                ],
            }

    fixed_info = {"model": "gold-model", "provider": "gold-provider", "usage": {"total": 15}}
    usage = server._get_usage(_Agent())
    monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)
    monkeypatch.setattr(server, "_ensure_session_db_row", lambda _session: None)
    monkeypatch.setattr(server, "_persist_branch_seed", lambda _session: None)
    monkeypatch.setattr(server, "_session_info", lambda _agent, _session=None: dict(fixed_info))
    monkeypatch.setattr(server, "make_stream_renderer", lambda _cols: None)
    monkeypatch.setattr(server, "render_message", lambda _raw, _cols: None)
    fake_title = types.ModuleType("agent.title_generator")
    setattr(fake_title, "maybe_auto_title", lambda *args, **kwargs: None)
    monkeypatch.setitem(sys.modules, "agent.title_generator", fake_title)

    def run_flag_off():
        events = []
        monkeypatch.setattr(server, "_emit", lambda event, sid, payload=None: events.append((event, sid, payload)))
        monkeypatch.setattr(server, "_load_cfg", lambda: {"dashboard": {"turn_isolation": False}})
        server._sessions["sid"] = _session(
            agent=_Agent(), model_override={"model": "gold-model", "provider": "gold-provider"}
        )
        try:
            response = server.handle_request(
                {"id": "turn-1", "method": "prompt.submit", "params": {"session_id": "sid", "text": "hello"}}
            )
            assert response["result"]["status"] == "streaming"
            return events
        finally:
            server._sessions.pop("sid", None)

    def run_flag_on():
        events = []
        monkeypatch.setattr(server, "_emit", lambda event, sid, payload=None: events.append((event, sid, payload)))
        monkeypatch.setattr(server, "_load_cfg", lambda: {"dashboard": {"turn_isolation": True}})

        class _FakeSupervisor:
            def submit_turn(self, frame, *, on_complete=None):
                sid = frame["sid"]
                server._emit("message.start", sid)
                server._emit("message.delta", sid, {"text": "hi"})
                server._emit("message.complete", sid, {"text": "hi", "usage": usage, "status": "complete"})
                server._emit("session.info", sid, dict(fixed_info))
                if on_complete is not None:
                    on_complete(
                        {
                            "type": "turn.end",
                            "sid": sid,
                            "request_id": frame["request_id"],
                            "session_key": "session-key",
                            "history_version": 1,
                            "message_count": 2,
                            "session_info": dict(fixed_info),
                            "session_info_emitted": True,
                        }
                    )
                return frame["request_id"]

        monkeypatch.setattr(server, "_get_compute_host_supervisor", lambda _cfg=None: _FakeSupervisor())
        session = _session(
            agent=None,
            agent_ready=threading.Event(),
            _compute_host_active=True,
            model_override={"model": "gold-model", "provider": "gold-provider"},
        )
        session["agent"] = None
        server._sessions["sid"] = session
        try:
            response = server.handle_request(
                {"id": "turn-1", "method": "prompt.submit", "params": {"session_id": "sid", "text": "hello"}}
            )
            assert response["result"]["status"] == "streaming"
            return events
        finally:
            server._sessions.pop("sid", None)

    assert run_flag_on() == run_flag_off()


def test_session_context_explicit_cwd_for_ephemeral_task(monkeypatch, tmp_path):
    """Background/preview tasks use ephemeral ids absent from `_sessions`, so the
    parent workspace is passed explicitly; it must pin instead of clearing back
    to the gateway launch dir."""
    from agent.runtime_cwd import resolve_agent_cwd

    project = tmp_path / "project"
    project.mkdir()
    launcher = tmp_path / "apps" / "desktop"
    launcher.mkdir(parents=True)

    monkeypatch.delenv("TERMINAL_CWD", raising=False)
    monkeypatch.chdir(launcher)

    tokens = server._set_session_context("bg_deadbe", cwd=str(project))
    try:
        assert resolve_agent_cwd() == project
    finally:
        server._clear_session_context(tokens)


def test_profile_scoped_mcp_discovery_uses_target_home(monkeypatch, tmp_path):
    """MCP discovery must start under the selected profile's HERMES_HOME."""
    from hermes_cli import mcp_startup
    from hermes_constants import get_hermes_home
    from tui_gateway import entry

    profile_home = tmp_path / "profiles" / "sheepyr"
    profile_home.mkdir(parents=True)

    (profile_home / "config.yaml").write_text(
        "mcp_servers:\n"
        "  bluesky_sheepyr:\n"
        "    command: test-command\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "default"))
    token = set_hermes_home_override(str(profile_home))

    seen = []

    monkeypatch.setattr(mcp_startup, "_mcp_discovery_started", set())
    monkeypatch.setattr(mcp_startup, "_mcp_discovery_thread", {})
    # ensure_mcp_discovery_started flips this module global; monkeypatch it so
    # the enablement doesn't leak into sibling tests in this file.
    monkeypatch.setattr(entry, "_mcp_discovery_enabled", False)
    monkeypatch.setattr(
        mcp_startup,
        "_discover_mcp_tools_without_interactive_oauth",
        lambda: seen.append(str(get_hermes_home())),
    )

    try:
        entry.ensure_mcp_discovery_started()
        thread = mcp_startup._current_home_thread()
        assert thread is not None
        thread.join(timeout=2)
    finally:
        reset_hermes_home_override(token)

    assert seen == [str(profile_home)]


def test_profile_scoped_agent_build_starts_mcp_discovery_in_profile_home(
    monkeypatch, tmp_path
):
    """Agent construction must start MCP discovery under the selected profile."""
    import threading
    import uuid

    from hermes_constants import get_hermes_home

    profile_home = tmp_path / "profiles" / "sheepyr"
    profile_home.mkdir(parents=True)

    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "default"))

    seen = []
    built = threading.Event()

    monkeypatch.setattr(
        server,
        "_make_agent",
        lambda *args, **kwargs: built.set()
        or type("Agent", (), {"model": "test"})(),
    )
    monkeypatch.setattr(
        "tui_gateway.entry.ensure_mcp_discovery_started",
        lambda: seen.append(str(get_hermes_home())),
    )
    monkeypatch.setattr(server, "_wire_callbacks", lambda _sid: None)
    monkeypatch.setattr(server, "_SlashWorker", lambda *args: None)
    monkeypatch.setattr(server, "_attach_worker", lambda *args: None)
    monkeypatch.setattr(server, "_config_model_target", lambda: ("", ""))
    # CI runs this huge file serially under load; a prior session's _build can
    # still be finishing (session.info emit) when the next test starts, so a
    # 2s Event wait flakes. Unique sid + longer bound; still fail closed.
    monkeypatch.setattr(server, "_start_notification_poller", lambda *a, **k: None)
    monkeypatch.setattr(server, "_schedule_mcp_late_refresh", lambda *a, **k: None)
    monkeypatch.setattr(server, "_emit", lambda *a, **k: None)

    ready = threading.Event()
    sid = f"test-sid-{uuid.uuid4().hex[:8]}"
    session = {
        "agent_ready": ready,
        "session_key": f"test-key-{uuid.uuid4().hex[:8]}",
        "profile_home": str(profile_home),
    }

    server._sessions[sid] = session
    try:
        server._start_agent_build(sid, session)
        assert built.wait(timeout=15), "agent build thread never called _make_agent"
        assert ready.wait(timeout=5), "agent_ready never set after build"
    finally:
        server._sessions.pop(sid, None)

    assert seen == [str(profile_home)]


def test_profile_scoped_agent_build_installs_secret_scope(monkeypatch, tmp_path):
    """Agent construction must install the selected profile's secret scope.

    Without it, get_secret() falls through to process os.environ, so a session
    "switched" to profile X resolves credentials from the LAUNCH profile's
    .env (#67605 item 2).
    """
    import threading
    import uuid

    from agent.secret_scope import current_secret_scope

    profile_home = tmp_path / "profiles" / "grace"
    profile_home.mkdir(parents=True)
    (profile_home / ".env").write_text(
        "PROXMOX_TOKEN=grace-secret\n", encoding="utf-8"
    )

    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "default"))

    scopes = []
    built = threading.Event()

    def _fake_make_agent(*args, **kwargs):
        scope = current_secret_scope()
        scopes.append(dict(scope) if scope else None)
        built.set()
        return type("Agent", (), {"model": "test"})()

    monkeypatch.setattr(server, "_make_agent", _fake_make_agent)
    monkeypatch.setattr(
        "tui_gateway.entry.ensure_mcp_discovery_started", lambda: None
    )
    monkeypatch.setattr(server, "_wire_callbacks", lambda _sid: None)
    monkeypatch.setattr(server, "_SlashWorker", lambda *args: None)
    monkeypatch.setattr(server, "_attach_worker", lambda *args: None)
    monkeypatch.setattr(server, "_config_model_target", lambda: ("", ""))
    # Same CI flake class as the MCP profile-home test: bound wait + less work
    # on the build thread (no poller / late MCP refresh / session.info emit).
    monkeypatch.setattr(server, "_start_notification_poller", lambda *a, **k: None)
    monkeypatch.setattr(server, "_schedule_mcp_late_refresh", lambda *a, **k: None)
    monkeypatch.setattr(server, "_emit", lambda *a, **k: None)

    ready = threading.Event()
    sid = f"test-secret-sid-{uuid.uuid4().hex[:8]}"
    session = {
        "agent_ready": ready,
        "session_key": f"test-secret-key-{uuid.uuid4().hex[:8]}",
        "profile_home": str(profile_home),
    }

    server._sessions[sid] = session
    try:
        server._start_agent_build(sid, session)
        assert built.wait(timeout=15), "agent build thread never called _make_agent"
        assert ready.wait(timeout=5), "agent_ready never set after build"
    finally:
        server._sessions.pop(sid, None)

    assert scopes == [{"PROXMOX_TOKEN": "grace-secret"}]


def test_profile_configured_cwd_reads_target_profile(tmp_path):
    """A profile's own terminal.cwd is read from its config.yaml."""
    project = tmp_path / "proj"
    project.mkdir()
    home = _write_profile_cfg(tmp_path / "home", str(project))
    assert server._profile_configured_cwd(home) == str(project)


def test_profile_configured_cwd_skips_placeholders_and_missing(tmp_path):
    """Placeholder values, missing config, and bad paths fall through to None."""
    assert server._profile_configured_cwd(None) is None
    assert server._profile_configured_cwd(tmp_path / "nope") is None
    for placeholder in (".", "auto", "cwd", ""):
        home = _write_profile_cfg(tmp_path / placeholder.strip("."), placeholder)
        assert server._profile_configured_cwd(home) is None
    home = _write_profile_cfg(tmp_path / "ghost", str(tmp_path / "does-not-exist"))
    assert server._profile_configured_cwd(home) is None


def test_completion_cwd_prefers_profile_over_stale_env(monkeypatch, tmp_path):
    """Issue #40334: a new session bound to another profile must use THAT
    profile's terminal.cwd, not the launch profile's stale TERMINAL_CWD."""
    profile_b = tmp_path / "ef-design"
    profile_b.mkdir()
    home = _write_profile_cfg(tmp_path / "home-b", str(profile_b))
    stale = tmp_path / "mahjong"
    stale.mkdir()

    monkeypatch.setenv("TERMINAL_CWD", str(stale))
    monkeypatch.setattr(server, "_hermes_home", tmp_path / "launch-home")
    monkeypatch.setattr(server, "_profile_home", lambda name: home if name else None)

    assert server._completion_cwd({"profile": "ef-design"}) == str(profile_b)
    # No profile and no launch config → fallback to the launch env var.
    assert server._completion_cwd({}) == str(stale)


def test_completion_cwd_prefers_launch_config_over_stale_env(monkeypatch, tmp_path):
    """Dashboard /chat's launch-profile in-memory gateway must honor config.

    The embedded Node TUI child gets TERMINAL_CWD from the dashboard PTY bridge,
    but the default-profile chat attaches to the dashboard process's already
    running in-memory gateway. That process may not have TERMINAL_CWD in its own
    environment (or has a stale one), so config.yaml is read directly and wins
    over the process env before falling back to the launch directory.
    """
    configured = tmp_path / "omni"
    configured.mkdir()
    stale = tmp_path / "hermes-agent"
    stale.mkdir()
    launch_home = _write_profile_cfg(tmp_path / "launch-home", str(configured))

    monkeypatch.setenv("TERMINAL_CWD", str(stale))
    monkeypatch.setattr(server, "_hermes_home", launch_home)
    monkeypatch.setattr(server, "_profile_home", lambda _name: None)

    assert server._completion_cwd({}) == str(configured)


def test_default_session_cwd_prefers_launch_config(monkeypatch, tmp_path):
    """A freshly created / resumed session with no explicit cwd lands in the
    configured terminal.cwd, not os.getcwd(), even when the in-memory gateway
    process env carries a stale TERMINAL_CWD."""
    configured = tmp_path / "workspace"
    configured.mkdir()
    stale = tmp_path / "launch-dir"
    stale.mkdir()
    launch_home = _write_profile_cfg(tmp_path / "launch-home", str(configured))

    monkeypatch.setenv("TERMINAL_CWD", str(stale))
    monkeypatch.setattr(server, "_hermes_home", launch_home)

    assert server._default_session_cwd() == str(configured)

    # No launch config → fall back to the process env var.
    (launch_home / "config.yaml").write_text("{}", encoding="utf-8")
    assert server._default_session_cwd() == str(stale)


def test_completion_cwd_explicit_cwd_wins_over_profile(monkeypatch, tmp_path):
    """An explicit client-provided cwd still beats the profile config."""
    explicit = tmp_path / "explicit"
    explicit.mkdir()
    profile_b = tmp_path / "configured"
    profile_b.mkdir()
    home = _write_profile_cfg(tmp_path / "home-c", str(profile_b))

    monkeypatch.setattr(server, "_profile_home", lambda name: home if name else None)
    result = server._completion_cwd(
        {"cwd": str(explicit), "cwd_explicit": True, "profile": "ef-design"}
    )
    assert result == str(explicit)


def test_completion_cwd_profile_overrides_inherited_workspace(monkeypatch, tmp_path):
    """Issue #52589: the desktop seeds a new chat's cwd from its app-global workspace
    (the launch profile's configured directory) — that inherited default must NOT
    override the target profile's own ``terminal.cwd``."""
    launch_ws = tmp_path / "workspace"
    launch_ws.mkdir()
    profile_ws = tmp_path / "products"
    profile_ws.mkdir()
    home = _write_profile_cfg(tmp_path / "home-dev", str(profile_ws))

    monkeypatch.setattr(server, "_profile_home", lambda name: home if name else None)
    # No cwd_explicit: the client cwd is the inherited app-global workspace.
    assert (
        server._completion_cwd({"profile": "dev", "cwd": str(launch_ws)}) == str(profile_ws)
    )


def test_completion_cwd_explicit_pick_wins_over_profile(monkeypatch, tmp_path):
    """Issue #52589 regression guard: a deliberate workspace pick (``cwd_explicit``)
    still beats the profile's configured ``terminal.cwd``."""
    explicit = tmp_path / "explicit-lane"
    explicit.mkdir()
    profile_ws = tmp_path / "products"
    profile_ws.mkdir()
    home = _write_profile_cfg(tmp_path / "home-dev", str(profile_ws))

    monkeypatch.setattr(server, "_profile_home", lambda name: home if name else None)
    assert (
        server._completion_cwd(
            {"profile": "dev", "cwd": str(explicit), "cwd_explicit": True}
        )
        == str(explicit)
    )


def test_completion_cwd_inherited_workspace_without_profile_cfg_kept(monkeypatch, tmp_path):
    """An inherited workspace stays when the target profile has NO configured
    terminal.cwd — the profile override only applies when one exists (#52589)."""
    launch_ws = tmp_path / "workspace"
    launch_ws.mkdir()
    no_cfg_home = tmp_path / "home-plain"
    no_cfg_home.mkdir()
    (no_cfg_home / "config.yaml").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(server, "_profile_home", lambda name: no_cfg_home if name else None)
    assert server._completion_cwd({"profile": "plain", "cwd": str(launch_ws)}) == str(launch_ws)


def test_terminal_task_cwd_local_backend_uses_session_cwd(monkeypatch, tmp_path):
    """A local terminal backend must keep host-validated session cwd behaviour."""
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.setenv("TERMINAL_ENV", "local")
    monkeypatch.delenv("TERMINAL_CWD", raising=False)

    assert server._terminal_task_cwd({"cwd": str(project)}) == str(project)


def test_terminal_task_cwd_ssh_uses_remote_path_unvalidated(monkeypatch):
    """SSH (non-local) backend: the configured remote cwd is used verbatim even
    though it does not exist on the local host. This is the jonbohz fix — host
    `isdir()` validation would otherwise discard the remote path and fall back
    to os.getcwd(), running commands against the wrong machine."""
    remote = "/home/jonboh/workspace/proj"  # does not exist on this host
    assert not os.path.isdir(remote)
    monkeypatch.setenv("TERMINAL_ENV", "ssh")
    monkeypatch.setenv("TERMINAL_CWD", remote)

    assert server._terminal_task_cwd({"cwd": "/some/host/dir"}) == remote


def test_terminal_task_cwd_ssh_falls_back_to_config(monkeypatch):
    """When TERMINAL_CWD is unset, the SSH path reads terminal.cwd from config."""
    remote = "/home/jonboh/workspace/from-config"
    monkeypatch.setenv("TERMINAL_ENV", "ssh")
    monkeypatch.delenv("TERMINAL_CWD", raising=False)
    monkeypatch.setattr(server, "_load_cfg", lambda: {"terminal": {"cwd": remote}})

    assert server._terminal_task_cwd({"cwd": "/some/host/dir"}) == remote


def test_terminal_task_cwd_ssh_sentinel_cwd_uses_remote_home(monkeypatch):
    """An SSH placeholder must not register the TUI host's session cwd."""
    monkeypatch.setenv("TERMINAL_ENV", "ssh")
    monkeypatch.setenv("TERMINAL_CWD", "auto")
    monkeypatch.setattr(server, "_load_cfg", lambda: {"terminal": {"cwd": "."}})

    assert server._terminal_task_cwd({"cwd": "/host/session/dir"}) == "~"


def test_write_json_serializes_concurrent_writes(monkeypatch):
    """Assert StdioTransport holds _stdout_lock across the full stream.write.

    The old char-by-char sleep mock made this test take long enough that
    leftover background write_json calls from earlier cases in this file
    could append an extra line (intermittent ``assert 9 == 8`` on CI/main).
    Match the WS concurrent-send check: count in-flight writes, and only
    assert on frames that carry this test's marker payload.
    """
    marker = "x" * 24
    active = 0
    max_active = 0
    gate = threading.Lock()
    frames: list[str] = []

    class RecordingStdout:
        def write(self, text: str) -> int:
            nonlocal active, max_active
            with gate:
                active += 1
                max_active = max(max_active, active)
            try:
                # Release the GIL while "in write" so a missing outer lock
                # would let another thread bump max_active above 1.
                time.sleep(0.01)
                frames.append(text)
            finally:
                with gate:
                    active -= 1
            return len(text)

        def flush(self) -> None:
            return None

    monkeypatch.setattr(server, "_real_stdout", RecordingStdout())

    barrier = threading.Barrier(8)

    def _worker(seq: int) -> None:
        barrier.wait(timeout=5)
        server.write_json({"seq": seq, "text": marker})

    threads = [threading.Thread(target=_worker, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
        assert not t.is_alive()

    assert max_active == 1

    ours = []
    for frame in frames:
        assert frame.endswith("\n"), frame
        obj = json.loads(frame)
        if obj.get("text") == marker and "seq" in obj:
            ours.append(obj)

    assert {obj["seq"] for obj in ours} == set(range(8))
    assert len(ours) == 8


def test_write_json_returns_false_on_broken_pipe(monkeypatch):
    monkeypatch.setattr(server, "_real_stdout", _BrokenStdout())

    assert server.write_json({"ok": True}) is False


def test_write_json_unserializable_payload_becomes_error_frame(monkeypatch, caplog):
    """The stdio twin of the WS guard (#92506): an unserializable result must reach the Ink TUI /
    stdio bridge as a JSON-RPC error frame with the original id plus a log line, not kill the pool
    worker silently while the client waits forever."""
    import datetime
    import logging

    out = _ChunkyStdout()
    monkeypatch.setattr(server, "_real_stdout", out)
    with caplog.at_level(logging.ERROR, logger="tui_gateway.transport"):
        assert server.write_json({"jsonrpc": "2.0", "id": "profiles",
                                  "result": {"created": datetime.datetime(2026, 8, 22)}}) is True
    frame = json.loads("".join(out.parts))
    assert frame["id"] == "profiles" and frame["error"]["code"] == -32603
    assert "datetime" in frame["error"]["message"]
    assert any(rec.levelno >= logging.ERROR for rec in caplog.records)


def test_write_json_drops_detached_ws_frames(monkeypatch):
    out = _ChunkyStdout()
    monkeypatch.setattr(server, "_real_stdout", out)
    server._sessions["detached-sid"] = {"transport": server._detached_ws_transport}
    try:
        assert server.write_json({
            "jsonrpc": "2.0",
            "method": "event",
            "params": {"session_id": "detached-sid", "type": "message.delta"},
        }) is False
        assert out.parts == []
    finally:
        server._sessions.pop("detached-sid", None)


def test_usage_ticker_emits_wrapped_usage_payload(monkeypatch):
    # The live ticker must nest the snapshot under a "usage" key, matching the
    # message.complete / session.info payloads the desktop & TUI handlers read
    # as payload.usage. Emitting the bare _get_usage() dict (payload.input/total
    # …) silently drops every live tick on the client side.
    events: list[tuple[str, str, dict]] = []
    monkeypatch.setattr(
        server, "_emit", lambda event_type, sid, payload: events.append((event_type, sid, payload))
    )
    snapshot = {"input": 1200, "total": 1280}
    monkeypatch.setattr(server, "_get_usage", lambda agent: dict(snapshot))

    stop, thread = server._start_usage_ticker("sess-1", object(), interval=0.01)
    # The dedup baseline is sampled synchronously inside _start_usage_ticker,
    # so this mutation is guaranteed to read as the first counter movement.
    snapshot["total"] = 2400
    try:
        deadline = time.time() + 1.0
        while not events and time.time() < deadline:
            time.sleep(0.01)
    finally:
        stop.set()
        thread.join(timeout=2.0)

    assert events, "ticker never emitted"
    event_type, sid, payload = events[0]
    assert event_type == "session.usage"
    assert sid == "sess-1"
    assert payload == {"usage": {"input": 1200, "total": 2400}}


def test_usage_ticker_skips_unchanged_snapshots(monkeypatch):
    # A single long API call leaves the token counters frozen for many
    # intervals; the ticker must emit nothing at all (the client already has
    # the turn-start values from the previous message.complete / session.info).
    # Only a changed snapshot emits.
    events: list[dict] = []
    monkeypatch.setattr(
        server, "_emit", lambda event_type, sid, payload: events.append(payload)
    )
    snapshot = {"input": 1200, "total": 1280}
    monkeypatch.setattr(server, "_get_usage", lambda agent: dict(snapshot))

    stop, thread = server._start_usage_ticker("sess-1", object(), interval=0.01)
    try:
        # ~15 ticks with counters frozen at the turn-start baseline: zero frames.
        time.sleep(0.15)
        assert events == []

        # Counters move → the next tick emits the new snapshot.
        snapshot["total"] = 2400
        deadline = time.time() + 1.0
        while not events and time.time() < deadline:
            time.sleep(0.01)
    finally:
        stop.set()
        thread.join(timeout=2.0)

    assert events == [{"usage": {"input": 1200, "total": 2400}}]


def test_usage_ticker_baseline_sampled_before_thread_start(monkeypatch):
    """The dedup baseline must be sampled synchronously in _start_usage_ticker,
    not inside the ticker thread: a late-scheduled thread would otherwise seed
    itself with counters the turn's first API call already bumped, absorbing
    that first growth so it never emits."""
    events: list[dict] = []
    monkeypatch.setattr(
        server, "_emit", lambda event_type, sid, payload: events.append(payload)
    )
    snapshot = {"input": 1200, "total": 1280}
    monkeypatch.setattr(server, "_get_usage", lambda agent: dict(snapshot))

    class _SlowStartThread(threading.Thread):
        def start(self):
            # Deterministic stand-in for a scheduler delay: the turn's first
            # API call bumps the counters before the ticker thread ever runs.
            snapshot["total"] = 2400
            super().start()

    monkeypatch.setattr(server, "_RealThread", _SlowStartThread)

    stop, thread = server._start_usage_ticker("sess-1", object(), interval=0.01)
    try:
        deadline = time.time() + 1.0
        while not events and time.time() < deadline:
            time.sleep(0.01)
    finally:
        stop.set()
        thread.join(timeout=2.0)

    # An in-thread seed would have read 2400 as the baseline and stayed
    # silent; the synchronous seed (1280) sees it as the first growth.
    assert events == [{"usage": {"input": 1200, "total": 2400}}]


def test_usage_ticker_stop_join_prevents_late_ticks(monkeypatch):
    """The stop sequence (set + join) must guarantee no session.usage after it
    returns: a tick captured mid-turn but emitted after message.complete would
    roll the client's final usage back to a stale snapshot (clients merge
    payload.usage unconditionally)."""
    events: list[str] = []
    monkeypatch.setattr(
        server, "_emit", lambda event_type, sid, payload: events.append(event_type)
    )

    in_snapshot = threading.Event()
    release = threading.Event()
    calls = {"n": 0}

    def _blocking_get_usage(agent):
        calls["n"] += 1
        if calls["n"] == 1:
            return {"total": 0}  # dedup seed
        # First real tick: hold it mid-snapshot so the stop lands while the
        # iteration is already past the stop.wait() gate.
        in_snapshot.set()
        release.wait(2.0)
        return {"total": 999}

    monkeypatch.setattr(server, "_get_usage", _blocking_get_usage)

    stop, thread = server._start_usage_ticker("sess-1", object(), interval=0.01)
    assert in_snapshot.wait(2.0), "ticker never reached a snapshot"

    # Turn ends while the tick is mid-snapshot: run the exact stop sequence
    # _run_prompt_submit uses, then emit message.complete.
    stop.set()
    release.set()
    thread.join(timeout=2.0)
    assert not thread.is_alive(), "ticker thread survived the stop sequence"
    server._emit("message.complete", "sess-1", {})

    # The in-flight tick was dropped (stop re-checked before emit), so nothing
    # can land after — let alone overwrite — the final usage.
    assert "session.usage" not in events
    assert events[-1] == "message.complete"


def test_run_prompt_submit_never_ticks_after_message_complete(monkeypatch):
    """End-to-end ordering through _run_prompt_submit: live session.usage ticks
    happen strictly before message.complete, never after it."""
    events: list[str] = []
    tick_seen = threading.Event()

    def _record_emit(event_type, sid, payload=None):
        events.append(event_type)
        if event_type == "session.usage":
            tick_seen.set()

    monkeypatch.setattr(server, "_emit", _record_emit)

    counter = {"n": 0}

    def _moving_usage(agent):
        counter["n"] += 1
        return {"total": counter["n"]}  # moves every sample → every tick emits

    monkeypatch.setattr(server, "_get_usage", _moving_usage)
    real_ticker = server._start_usage_ticker
    monkeypatch.setattr(
        server,
        "_start_usage_ticker",
        lambda sid, agent, interval=1.0: real_ticker(sid, agent, interval=0.01),
    )
    monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)
    monkeypatch.setattr(server, "make_stream_renderer", lambda cols: None)
    monkeypatch.setattr(server, "render_message", lambda raw, cols: None)
    monkeypatch.setattr(server, "_get_db", lambda: None)

    class _Agent:
        def run_conversation(
            self,
            prompt,
            conversation_history=None,
            stream_callback=None,
            persist_user_message=None,
        ):
            # Hold the turn open until at least one live tick has fired.
            assert tick_seen.wait(5.0), "no live tick during the turn"
            return {"final_response": "done", "messages": [], "completed": True}

    server._sessions["sid"] = _session(agent=_Agent())
    try:
        server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {"session_id": "sid", "text": "hello"},
            }
        )
    finally:
        server._sessions.pop("sid", None)

    assert "session.usage" in events
    assert "message.complete" in events
    last_tick = max(i for i, e in enumerate(events) if e == "session.usage")
    assert last_tick < events.index("message.complete")
