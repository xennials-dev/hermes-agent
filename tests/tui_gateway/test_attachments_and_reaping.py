"""tui_gateway.server — attachments, restart/reap sweeps, TTL/LRU and billing surface.

Split from test_tui_gateway_server.py; shared fixtures and helpers live
in tests/tui_gateway/_server_test_helpers.py.
"""

import json
import os
import subprocess
import threading
import time
import types
from datetime import datetime
from pathlib import Path
import pytest
from tui_gateway import server

from tests.tui_gateway._server_test_helpers import (
    _BillingHeaders,
    _PNG_1X1_B64,
    _attach_bytes_cli,
    _idle_evictable_session,
    _neuter_agent_prewarm_timer,  # autouse
    _periodic_trim_calls,
    _reap_leaked_notification_pollers,  # autouse
    _session,
    _sub_rpc,
)


def test_session_save_writes_under_hermes_home_with_system_prompt(monkeypatch, tmp_path):
    """TUI /save (session.save RPC) must snapshot under the Hermes profile
    home — not the project/workspace CWD — and include the system prompt,
    mirroring the classic CLI /save and the dashboard save export.

    Regression: the gateway handler wrote ``hermes_conversation_*.json`` to
    ``os.path.abspath(...)`` (the workspace CWD) and only exported ``model``
    and ``messages``, so ``system_prompt`` was missing.
    """
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))

    # Run from a different CWD to prove the snapshot does NOT leak there.
    work = tmp_path / "workspace"
    work.mkdir()
    monkeypatch.chdir(work)

    sid = "save-sid"
    agent = types.SimpleNamespace(
        model="hermes-test",
        session_id="20260101_120000_abc123",
        session_start=datetime(2026, 1, 1, 12, 0, 0),
        _cached_system_prompt="You are Hermes.",
    )
    history = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]
    server._sessions[sid] = {
        "agent": agent,
        "session_key": "save-key",
        "history": history,
        "history_lock": threading.Lock(),
        "created_at": 1735732800.0,
    }
    try:
        resp = server._methods["session.save"]("1", {"session_id": sid})
    finally:
        server._sessions.pop(sid, None)

    assert "result" in resp, resp
    saved_file = Path(resp["result"]["file"])

    # Must NOT leak into the workspace/project CWD.
    assert not list(work.glob("hermes_conversation_*.json"))

    saved_dir = home / "sessions" / "saved"
    assert saved_file.parent == saved_dir
    assert saved_file.exists()

    payload = json.loads(saved_file.read_text())
    assert payload["model"] == "hermes-test"
    assert payload["session_id"] == "20260101_120000_abc123"
    assert payload["session_start"] == "2026-01-01T12:00:00"
    assert payload["system_prompt"] == "You are Hermes."
    assert payload["messages"] == history


def test_session_save_proxies_to_compute_host_history(monkeypatch):
    """Isolated turns own history in the host; /save must not export the stale parent mirror."""
    sid = "save-host-sid"
    server._sessions[sid] = _session(agent=None, _compute_host_active=True)
    calls = []

    def send_control(control_sid, **kwargs):
        calls.append((control_sid, kwargs))
        return {"type": "control.ack", "result": {"file": "/tmp/host-save.json"}}

    monkeypatch.setattr(server, "_session_uses_compute_host", lambda _session: True)
    monkeypatch.setattr(server, "_send_compute_host_control", send_control)
    try:
        resp = server._methods["session.save"]("1", {"session_id": sid})
    finally:
        server._sessions.pop(sid, None)

    assert resp["result"] == {"file": "/tmp/host-save.json"}
    assert calls == [(sid, {"route_name": "session.save", "wait": True})]


def test_notification_event_dedup_key_preserves_distinct_watch_matches():
    """Watch-match identity includes match content, not just session/type."""
    base = {
        "type": "watch_match",
        "session_id": "proc_watch",
        "command": "tail -f app.log",
        "pattern": "READY",
        "output": "READY on port 8000",
        "suppressed": 0,
    }

    identical = dict(base)
    distinct_output = {**base, "output": "READY on port 9000"}
    distinct_pattern = {**base, "pattern": "MIGRATION_DONE"}

    base_key = server._notification_event_dedup_key(base)
    assert server._notification_event_dedup_key(identical) == base_key
    assert server._notification_event_dedup_key(distinct_output) != base_key
    assert server._notification_event_dedup_key(distinct_pattern) != base_key


def test_notification_poller_emits_distinct_watch_matches_once(monkeypatch):
    """Distinct watch matches from one process emit; exact replay is deduped."""
    import queue as _queue_mod

    from tools.process_registry import process_registry

    turns = []
    emitted = []

    def _fake_run_prompt_submit(rid, sid, session, text):
        turns.append(text)
        with session["history_lock"]:
            session["running"] = False

    sess = _session()
    server._sessions["sid_watch_dedup"] = sess
    monkeypatch.setattr(server, "_emit", lambda *a, **kw: emitted.append(a))
    monkeypatch.setattr(server, "_run_prompt_submit", _fake_run_prompt_submit)

    isolated_queue: _queue_mod.Queue = _queue_mod.Queue()
    monkeypatch.setattr(process_registry, "completion_queue", isolated_queue)

    base = {
        "type": "watch_match",
        "session_id": "proc_watch_dedup",
        "command": "tail -f app.log",
        "pattern": "READY",
        "output": "READY on port 8000",
        "suppressed": 0,
    }
    isolated_queue.put(base)
    isolated_queue.put({**base, "output": "READY on port 9000"})
    isolated_queue.put(dict(base))

    stop = threading.Event()
    stop.set()

    try:
        server._notification_poller_loop(stop, "sid_watch_dedup", sess)
        status_calls = [a for a in emitted if a[0] == "status.update"]
        assert len(status_calls) == 2
        status_text = "\n".join(call[2]["text"] for call in status_calls)
        assert "READY on port 8000" in status_text
        assert "READY on port 9000" in status_text
        assert len(turns) == 3
    finally:
        server._sessions.pop("sid_watch_dedup", None)
        while not process_registry.completion_queue.empty():
            process_registry.completion_queue.get_nowait()


def test_notification_event_dedup_key_keeps_completions_one_shot():
    """Completion identity remains process-session scoped to avoid floods."""
    first = {
        "type": "completion",
        "session_id": "proc_done",
        "command": "make build",
        "exit_code": 0,
        "output": "first output",
    }
    replay = {
        "type": "completion",
        "session_id": "proc_done",
        "command": "make build --again",
        "exit_code": 1,
        "output": "different output should not change completion key",
    }

    assert server._notification_event_dedup_key(first) == server._notification_event_dedup_key(
        replay
    )


def test_image_attach_bytes_writes_to_gateway_dir(monkeypatch, tmp_path):
    """Remote client uploads base64 bytes; gateway writes them to its own disk."""
    _attach_bytes_cli(monkeypatch)
    monkeypatch.setattr(server, "_hermes_home", tmp_path)
    server._sessions["abx"] = _session()

    resp = server.handle_request(
        {
            "id": "1",
            "method": "image.attach_bytes",
            "params": {
                "session_id": "abx",
                "content_base64": _PNG_1X1_B64,
                "filename": "shot.png",
            },
        }
    )

    res = resp["result"]
    assert res["attached"] is True
    written = Path(res["path"])
    assert written.is_file()
    assert written.parent == tmp_path / "images"
    assert written.read_bytes().startswith(b"\x89PNG")
    assert len(server._sessions["abx"]["attached_images"]) == 1
    assert res["bytes"] > 0


def test_image_attach_bytes_accepts_data_url_prefix(monkeypatch, tmp_path):
    _attach_bytes_cli(monkeypatch)
    monkeypatch.setattr(server, "_hermes_home", tmp_path)
    server._sessions["abx2"] = _session()

    resp = server.handle_request(
        {
            "id": "1",
            "method": "image.attach_bytes",
            "params": {
                "session_id": "abx2",
                "content_base64": f"data:image/png;base64,{_PNG_1X1_B64}",
            },
        }
    )
    assert resp["result"]["attached"] is True


def test_image_attach_bytes_data_alias_and_magic_sniff(monkeypatch, tmp_path):
    """Older desktop builds send `data` (not content_base64); ext sniffed from bytes."""
    _attach_bytes_cli(monkeypatch)
    monkeypatch.setattr(server, "_hermes_home", tmp_path)
    server._sessions["abx3"] = _session()

    resp = server.handle_request(
        {
            "id": "1",
            "method": "image.attach_bytes",
            "params": {"session_id": "abx3", "data": _PNG_1X1_B64},
        }
    )
    res = resp["result"]
    assert res["attached"] is True
    assert Path(res["path"]).suffix == ".png"  # sniffed from magic bytes


def test_image_attach_bytes_rejects_invalid_base64(monkeypatch, tmp_path):
    _attach_bytes_cli(monkeypatch)
    monkeypatch.setattr(server, "_hermes_home", tmp_path)
    server._sessions["abx4"] = _session()

    resp = server.handle_request(
        {
            "id": "1",
            "method": "image.attach_bytes",
            "params": {"session_id": "abx4", "content_base64": "!!!not base64!!!"},
        }
    )
    assert "error" in resp
    assert resp["error"]["code"] == 4017


def test_image_attach_bytes_rejects_oversize(monkeypatch, tmp_path):
    import base64 as _b64

    _attach_bytes_cli(monkeypatch)
    monkeypatch.setattr(server, "_hermes_home", tmp_path)
    monkeypatch.setattr(server, "_ATTACH_BYTES_MAX_BYTES", 10)
    server._sessions["abx5"] = _session()

    big = _b64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 100).decode("ascii")
    resp = server.handle_request(
        {
            "id": "1",
            "method": "image.attach_bytes",
            "params": {"session_id": "abx5", "content_base64": big},
        }
    )
    assert "error" in resp
    assert resp["error"]["code"] == 4018


def test_image_attach_bytes_rejects_unsupported_extension(monkeypatch, tmp_path):
    _attach_bytes_cli(monkeypatch)
    monkeypatch.setattr(server, "_hermes_home", tmp_path)
    server._sessions["abx6"] = _session()

    # filename hint forces a non-image extension; magic sniff is bypassed by hint
    resp = server.handle_request(
        {
            "id": "1",
            "method": "image.attach_bytes",
            "params": {
                "session_id": "abx6",
                "content_base64": _PNG_1X1_B64,
                "filename": "evil.exe",
            },
        }
    )
    assert "error" in resp
    assert resp["error"]["code"] == 4016


def test_pdf_attach_requires_poppler(monkeypatch, tmp_path):
    """Without pdftoppm on PATH, pdf.attach returns a clear 5028."""
    _attach_bytes_cli(monkeypatch)
    monkeypatch.setattr(server, "_hermes_home", tmp_path)
    monkeypatch.setattr("shutil.which", lambda _name: None)
    server._sessions["pdf1"] = _session()

    resp = server.handle_request(
        {
            "id": "1",
            "method": "pdf.attach",
            "params": {"session_id": "pdf1", "content_base64": "JVBERi0xLjQK"},
        }
    )
    assert "error" in resp
    assert resp["error"]["code"] == 5028


def test_pdf_attach_rejects_non_pdf_bytes(monkeypatch, tmp_path):
    import base64 as _b64

    _attach_bytes_cli(monkeypatch)
    monkeypatch.setattr(server, "_hermes_home", tmp_path)
    monkeypatch.setattr("shutil.which", lambda _name: "/usr/bin/pdftoppm")
    server._sessions["pdf2"] = _session()

    not_pdf = _b64.b64encode(b"this is not a pdf").decode("ascii")
    resp = server.handle_request(
        {
            "id": "1",
            "method": "pdf.attach",
            "params": {"session_id": "pdf2", "content_base64": not_pdf},
        }
    )
    assert "error" in resp
    assert resp["error"]["code"] == 4017


def test_pdf_attach_requires_path_or_bytes(monkeypatch, tmp_path):
    _attach_bytes_cli(monkeypatch)
    monkeypatch.setattr(server, "_hermes_home", tmp_path)
    monkeypatch.setattr("shutil.which", lambda _name: "/usr/bin/pdftoppm")
    server._sessions["pdf3"] = _session()

    resp = server.handle_request(
        {"id": "1", "method": "pdf.attach", "params": {"session_id": "pdf3"}}
    )
    assert "error" in resp
    assert resp["error"]["code"] == 4015


def test_decode_attach_base64_helper():
    import base64 as _b64

    raw = _b64.b64encode(b"hello").decode("ascii")
    assert server._decode_attach_base64(raw, mime_prefix="image/") == b"hello"
    assert (
        server._decode_attach_base64(f"data:image/png;base64,{raw}", mime_prefix="image/")
        == b"hello"
    )
    # whitespace inside payload is tolerated
    assert server._decode_attach_base64(raw[:4] + "\n" + raw[4:], mime_prefix="image/") == b"hello"
    assert server._decode_attach_base64("@@@", mime_prefix="image/") is None


def test_sniff_image_ext_magic_and_filename():
    assert server._sniff_image_ext(b"\x89PNG\r\n\x1a\n") == ".png"
    assert server._sniff_image_ext(b"\xff\xd8\xff\xe0") == ".jpg"
    assert server._sniff_image_ext(b"GIF89a....") == ".gif"
    assert server._sniff_image_ext(b"RIFF1234WEBPxxxx") == ".webp"
    assert server._sniff_image_ext(b"BM......") == ".bmp"
    assert server._sniff_image_ext(b"unknown") == ".png"  # fallback
    # filename hint wins over magic bytes
    assert server._sniff_image_ext(b"\x89PNG", "photo.jpeg") == ".jpeg"


def test_slash_worker_close_reaps_zombie_and_closes_fds():
    """A hung worker is SIGKILLed, the zombie reaped, all pipes closed — once."""
    calls = {k: 0 for k in ("terminate", "kill", "wait", "stdin", "stdout", "stderr")}

    class FakeStream:
        def __init__(self, name):
            self.name = name

        def close(self):
            calls[self.name] += 1

    class FakeProc:
        stdin, stdout, stderr = (FakeStream(n) for n in ("stdin", "stdout", "stderr"))

        def poll(self):
            return None  # always alive -> forces terminate then kill

        def terminate(self):
            calls["terminate"] += 1

        def kill(self):
            calls["kill"] += 1

        def wait(self, timeout=None):
            calls["wait"] += 1
            raise subprocess.TimeoutExpired(cmd="x", timeout=timeout)

    worker = object.__new__(server._SlashWorker)
    worker.proc = FakeProc()

    worker.close()
    worker.close()  # idempotent

    assert calls["terminate"] == 1
    assert calls["kill"] == 1
    assert calls["wait"] >= 2  # reaped after both terminate and kill
    assert calls["stdin"] == calls["stdout"] == calls["stderr"] == 1


def test_close_session_by_id_is_idempotent_and_full(monkeypatch):
    """One call tears the session down fully; a second is a no-op."""
    calls = {"worker": 0, "agent": 0, "unreg": 0, "finalize": 0}

    class W:
        def close(self):
            calls["worker"] += 1

    class A:
        def close(self):
            calls["agent"] += 1

    def _fake_finalize(s, end_reason="tui_close"):
        # Real _finalize_session is the single chokepoint that closes the
        # slash-worker; mirror that here so the test exercises the actual
        # teardown contract (worker close lives in finalize, not the caller).
        calls["finalize"] += 1
        w = s.get("slash_worker")
        if w:
            w.close()

    monkeypatch.setattr(server, "_finalize_session", _fake_finalize)
    monkeypatch.setattr(
        "tools.approval.unregister_gateway_notify",
        lambda key: calls.__setitem__("unreg", calls["unreg"] + 1), raising=False,
    )
    server._sessions["sid-1"] = {"session_key": "k1", "agent": A(), "slash_worker": W()}

    assert server._close_session_by_id("sid-1", end_reason="ws_disconnect") is True
    assert server._close_session_by_id("sid-1", end_reason="ws_disconnect") is False
    assert calls == {"worker": 1, "agent": 1, "unreg": 1, "finalize": 1}
    assert "sid-1" not in server._sessions


def test_attach_worker_closes_orphan_when_session_already_torn_down():
    """A worker built after its session was reaped must be closed, not orphaned."""
    closed = []

    class W:
        def close(self):
            closed.append(True)

    server._sessions.pop("gone", None)
    detached = {"session_key": "k"}  # not in _sessions -> already torn down
    server._attach_worker("gone", detached, W())

    assert closed == [True]
    assert "slash_worker" not in detached
    assert "gone" not in server._sessions


def test_attach_worker_stores_worker_on_live_session():
    class W:
        def close(self):
            raise AssertionError("must not close a worker for a live session")

    live = {"session_key": "k"}
    server._sessions["live"] = live
    worker = W()
    try:
        server._attach_worker("live", live, worker)
        assert live["slash_worker"] is worker
    finally:
        server._sessions.pop("live", None)


def test_restart_slash_worker_closes_orphan_when_session_reaped(monkeypatch):
    """Post-turn restart of a session reaped mid-flight (e.g. close_on_disconnect
    fired while `running` flipped false) must close both the stale worker and
    the fresh replacement, not orphan either."""
    closed = []

    class _FakeWorker:
        def __init__(self, *a, **k):
            pass

        def close(self):
            closed.append(True)

    monkeypatch.setattr(server, "_SlashWorker", _FakeWorker)
    server._sessions.pop("reaped", None)
    # not in _sessions -> torn down concurrently; carries a live worker so the
    # restart path actually runs (a workerless session is a restart no-op now)
    reaped = {"session_key": "k", "slash_worker": _FakeWorker()}
    server._restart_slash_worker("reaped", reaped)

    # stale worker closed by the restart, fresh worker closed by _attach_worker
    # (sid no longer maps to this session)
    assert closed == [True, True]
    assert "reaped" not in server._sessions


def test_restart_slash_worker_stores_on_live_session(monkeypatch):
    class _FakeWorker:
        def __init__(self, *a, **k):
            pass

        def close(self):
            pass

    monkeypatch.setattr(server, "_SlashWorker", _FakeWorker)
    old_worker = _FakeWorker()
    live = {"session_key": "k", "slash_worker": old_worker}
    server._sessions["live-restart"] = live
    try:
        server._restart_slash_worker("live-restart", live)
        assert isinstance(live["slash_worker"], _FakeWorker)
        assert live["slash_worker"] is not old_worker
    finally:
        server._sessions.pop("live-restart", None)


def test_restart_slash_worker_noop_without_worker(monkeypatch):
    """A session that never spawned a worker (slash.exec not used yet) must
    stay workerless across a restart — spawning here would fork the per-worker
    stdio MCP fleet for sessions that never run worker-routed commands."""
    spawned = []

    class _FakeWorker:
        def __init__(self, *a, **k):
            spawned.append(True)

        def close(self):
            pass

    monkeypatch.setattr(server, "_SlashWorker", _FakeWorker)
    live = {"session_key": "k", "slash_worker": None}
    server._sessions["lazy-noop"] = live
    try:
        server._restart_slash_worker("lazy-noop", live)
        assert spawned == []
        assert live["slash_worker"] is None
    finally:
        server._sessions.pop("lazy-noop", None)


def test_slash_exec_concurrent_first_use_spawns_single_worker(monkeypatch):
    """With eager pre-warm removed, slash.exec is the only spawn path — two
    concurrent worker-routed commands on a fresh session must not each fork a
    full MCP-fleet worker. The per-session spawn lock serializes first use."""
    import time as _time

    spawned = []
    barrier = threading.Barrier(2, timeout=5)

    class _SlowWorker:
        def __init__(self, *a, **k):
            spawned.append(self)
            _time.sleep(0.05)  # widen the None-observation window

        def run(self, cmd):
            return f"ran {cmd}"

        def close(self):
            pass

    monkeypatch.setattr(server, "_SlashWorker", _SlowWorker)
    monkeypatch.setattr(server, "_mirror_slash_side_effects", lambda *a, **k: None)
    session = _session(slash_worker=None)
    server._sessions["race-spawn"] = session

    results = []

    def _exec(n):
        barrier.wait()
        resp = server.handle_request(
            {
                "id": str(n),
                "method": "slash.exec",
                "params": {"command": "/context", "session_id": "race-spawn"},
            }
        )
        results.append(resp)

    try:
        threads = [threading.Thread(target=_exec, args=(i,)) for i in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)
        assert len(spawned) == 1, (
            f"concurrent slash.exec spawned {len(spawned)} workers — first-use "
            f"spawn must be serialized per session"
        )
        assert session["slash_worker"] is spawned[0]
        assert all("result" in r for r in results), results
    finally:
        server._sessions.pop("race-spawn", None)


def test_close_sessions_for_transport_closes_flagged_repoints_rest(monkeypatch):
    seen = []
    monkeypatch.setattr(
        server,
        "_teardown_popped_session",
        lambda session, *, end_reason: seen.append((session["_sid"], end_reason)) or True,
    )
    # Detached session "b" would schedule a real grace-reap threading.Timer that
    # outlives the test; grace=0 short-circuits it so no thread lingers.
    monkeypatch.setattr(server, "_WS_ORPHAN_REAP_GRACE_S", 0)
    transport = object()  # the disconnecting transport
    server._sessions.clear()
    server._sessions["a"] = {"transport": transport, "close_on_disconnect": True}
    server._sessions["b"] = {"transport": transport, "close_on_disconnect": False}
    try:
        server._close_sessions_for_transport(transport, end_reason="ws_disconnect")
        assert seen == [("a", "ws_disconnect")]  # only the flagged one closed
        assert server._sessions["b"]["transport"] is server._detached_ws_transport  # re-pointed
    finally:
        server._sessions.clear()


@pytest.mark.parametrize("close_on_disconnect", [True, False])
def test_close_sessions_for_transport_skips_session_rebound_before_claim(
    monkeypatch, close_on_disconnect
):
    """A resume between snapshot and claim keeps either session type alive."""
    reaps = []
    teardowns = []
    monkeypatch.setattr(
        server, "_schedule_ws_orphan_reap", lambda sid: reaps.append(sid)
    )
    monkeypatch.setattr(
        server,
        "_teardown_popped_session",
        lambda session, *, end_reason: teardowns.append((session, end_reason)) or True,
    )
    old_transport = object()  # the disconnecting transport
    new_transport = object()  # live rebind target (no _closed attr → alive)
    session = {"transport": old_transport, "close_on_disconnect": close_on_disconnect}
    original_sessions_lock = server._sessions_lock
    rebound = threading.Event()

    class _SnapshotInterlock:
        """Rebind in a second thread immediately after the ownership snapshot."""

        def __init__(self):
            self._snapshot_released = False

        def __enter__(self):
            original_sessions_lock.acquire()
            return self

        def __exit__(self, exc_type, exc, traceback):
            original_sessions_lock.release()
            if not self._snapshot_released:
                self._snapshot_released = True

                def _resume_rebind():
                    with server._session_resume_lock:
                        session["transport"] = new_transport
                    rebound.set()

                thread = threading.Thread(target=_resume_rebind)
                thread.start()
                assert rebound.wait(timeout=1)
                thread.join(timeout=1)
            return False

    monkeypatch.setattr(server, "_sessions_lock", _SnapshotInterlock())
    server._sessions.clear()
    server._sessions["rebound"] = session
    try:
        reaped, detached = server._close_sessions_for_transport(old_transport)
        assert reaped == 0
        assert detached == 0
        assert server._sessions["rebound"] is session
        assert session["transport"] is new_transport
        assert teardowns == []
        assert reaps == []
    finally:
        server._sessions.clear()


def test_session_create_records_close_on_disconnect_flag(monkeypatch):
    monkeypatch.setattr(server, "_start_agent_build", lambda sid, session: None)
    server._sessions.clear()
    try:
        on = server.handle_request(
            {"id": "1", "method": "session.create", "params": {"close_on_disconnect": True}}
        )["result"]["session_id"]
        off = server.handle_request(
            {"id": "2", "method": "session.create", "params": {}}
        )["result"]["session_id"]
        assert server._sessions[on]["close_on_disconnect"]
        assert not server._sessions[off]["close_on_disconnect"]
    finally:
        server._sessions.clear()


def test_session_create_records_source(monkeypatch):
    monkeypatch.setattr(server, "_start_agent_build", lambda sid, session: None)
    server._sessions.clear()
    try:
        sid = server.handle_request(
            {"id": "1", "method": "session.create", "params": {"source": "tool"}}
        )["result"]["session_id"]
        assert server._sessions[sid]["source"] == "tool"
    finally:
        server._sessions.clear()


def test_shutdown_sessions_closes_every_session_via_helper(monkeypatch):
    seen = []
    monkeypatch.setattr(
        server, "_close_session_by_id",
        lambda sid, *, end_reason: seen.append((sid, end_reason)),
    )
    server._sessions.clear()
    server._sessions["a"] = {}
    server._sessions["b"] = {}
    try:
        server._shutdown_sessions()
        assert sorted(sid for sid, _ in seen) == ["a", "b"]
        assert {reason for _, reason in seen} == {"tui_shutdown"}
    finally:
        server._sessions.clear()


def test_session_is_evictable_when_idle_dead_and_quiescent(monkeypatch):
    monkeypatch.setattr(server, "_session_pending_kind", lambda sid: "")
    now = time.time()
    assert server._session_is_evictable("s", _idle_evictable_session(now), now) is True


def test_session_not_evictable_violating_each_exemption(monkeypatch):
    monkeypatch.setattr(server, "_session_pending_kind", lambda sid: "")
    now = time.time()
    live_transport = type("T", (), {"_closed": False})()

    running = _idle_evictable_session(now) | {"running": True}
    assert server._session_is_evictable("s", running, now) is False

    starting = _idle_evictable_session(now)
    starting["agent_ready"] = threading.Event()  # not set -> still starting
    assert server._session_is_evictable("s", starting, now) is False

    on_socket = _idle_evictable_session(now) | {"transport": live_transport}
    assert server._session_is_evictable("s", on_socket, now) is False

    recent = _idle_evictable_session(now) | {"last_active": now}
    assert server._session_is_evictable("s", recent, now) is False

    young = _idle_evictable_session(now) | {"created_at": now}
    assert server._session_is_evictable("s", young, now) is False

    # Pending input request, even when everything else looks idle.
    monkeypatch.setattr(server, "_session_pending_kind", lambda sid: "input")
    assert server._session_is_evictable("s", _idle_evictable_session(now), now) is False


def test_reap_idle_sessions_closes_only_evictable(monkeypatch):
    closed = []
    monkeypatch.setattr(server, "_session_pending_kind", lambda sid: "")
    monkeypatch.setattr(
        server, "_close_session_by_id",
        lambda sid, *, end_reason, predicate=None: closed.append((sid, end_reason)),
    )
    now = time.time()
    server._sessions.clear()
    server._sessions["stale"] = _idle_evictable_session(now)
    server._sessions["fresh"] = _idle_evictable_session(now) | {"last_active": now}
    try:
        server._reap_idle_sessions()
        assert closed == [("stale", "idle_timeout")]
    finally:
        server._sessions.clear()


def test_periodic_trim_deferred_while_a_session_is_busy_or_attached(monkeypatch):
    """The gen-2 collect + malloc_trim stalls the loop for its whole duration (#58576): it must not run
    while any session is mid-turn or still holds a live client, whatever the other sessions look like."""
    calls = _periodic_trim_calls(monkeypatch)
    now = time.time()
    live = types.SimpleNamespace(_closed=False)
    for busy in ({"running": True}, {"transport": live}):
        server._sessions.clear()
        server._sessions["idle"] = _idle_evictable_session(now)
        server._sessions["busy"] = _idle_evictable_session(now) | busy
        try:
            server._reap_idle_sessions()
            assert calls == [], busy
        finally:
            server._sessions.clear()


def test_periodic_trim_runs_once_every_session_is_quiescent(monkeypatch):
    """Every quiescent scan trims, even with no victims: no sessions at all, or only recent (not yet
    TTL-evictable) sessions that are detached and idle."""
    calls = _periodic_trim_calls(monkeypatch)
    now = time.time()
    for sessions in ({}, {"parked": _idle_evictable_session(now) | {"last_active": now, "created_at": now}}):
        calls.clear()
        server._sessions.clear()
        server._sessions.update(sessions)
        try:
            server._reap_idle_sessions()
            assert len(calls) == 1, sessions
        finally:
            server._sessions.clear()


def test_turn_completion_trim_skips_while_another_session_is_running(monkeypatch):
    """The finishing session is still marked running when _finish_turn runs, so only OTHER sessions gate its
    trim: a sole session trims at every turn end; a second in-flight turn defers it (#58576)."""
    calls = _periodic_trim_calls(monkeypatch)
    monkeypatch.setattr(server, "_clear_session_context", lambda tokens: None)
    now = time.time()
    own = _idle_evictable_session(now) | {"running": True, "transport": types.SimpleNamespace(_closed=False)}
    server._sessions.clear()
    server._sessions["own"] = own
    try:
        server._finish_turn("own", own, server._TurnRun(agent=None, one_turn_restore=None, terminal_callback=None, receipt_committed=True))
        assert len(calls) == 1

        calls.clear()
        server._sessions["other"] = _idle_evictable_session(now) | {"running": True}
        server._finish_turn("own", own, server._TurnRun(agent=None, one_turn_restore=None, terminal_callback=None, receipt_committed=True))
        assert calls == []
    finally:
        server._sessions.clear()


def test_reap_idle_sessions_logs_trim_failure(monkeypatch, caplog):
    import hermes_cli.mem_trim as mem_trim

    _periodic_trim_calls(monkeypatch)
    monkeypatch.setattr(mem_trim, "trim_memory", lambda **_kw: (_ for _ in ()).throw(RuntimeError("boom")))
    server._sessions.clear()
    try:
        with caplog.at_level("DEBUG", logger="tui_gateway.server"):
            server._reap_idle_sessions()
        assert "boom" in caplog.text
    finally:
        server._sessions.clear()


def test_ttl_reaper_spares_session_with_active_delegation(monkeypatch):
    from tools import async_delegation

    closed = []
    delegation_id = "deleg_ttl_reaper_test"
    monkeypatch.setattr(server, "_session_pending_kind", lambda sid: "")
    monkeypatch.setattr(server, "_enforce_session_cap", lambda: None)
    monkeypatch.setattr(server, "_reclaim_orphaned_leases", lambda: None)
    monkeypatch.setattr(
        server,
        "_close_session_by_id",
        lambda sid, *, end_reason, predicate=None: closed.append((sid, end_reason)),
    )
    now = time.time()
    server._sessions.clear()
    server._sessions["delegating-ttl"] = _idle_evictable_session(now)
    with async_delegation._records_lock:
        async_delegation._records[delegation_id] = {
            "status": "running",
            "origin_ui_session_id": "delegating-ttl",
        }

    try:
        server._reap_idle_sessions()
        assert closed == []
    finally:
        server._sessions.clear()
        with async_delegation._records_lock:
            async_delegation._records.pop(delegation_id, None)


def test_lru_reaper_spares_active_delegation_and_evicts_idle_peer(monkeypatch):
    from tools import async_delegation

    closed = []
    delegation_id = "deleg_lru_reaper_test"
    monkeypatch.setattr(server, "_session_pending_kind", lambda sid: "")
    monkeypatch.setattr(server, "_max_live_sessions", lambda: 1)
    monkeypatch.setattr(
        server,
        "_close_session_by_id",
        lambda sid, *, end_reason, predicate=None: closed.append((sid, end_reason)),
    )
    now = time.time()
    server._sessions.clear()
    server._sessions["delegating-lru"] = _idle_evictable_session(now) | {
        "last_active": now - 20 * 3600
    }
    server._sessions["idle-peer"] = _idle_evictable_session(now)
    with async_delegation._records_lock:
        async_delegation._records[delegation_id] = {
            "status": "running",
            "origin_ui_session_id": "delegating-lru",
        }

    try:
        server._enforce_session_cap()
        assert closed == [("idle-peer", "lru_evict")]
    finally:
        server._sessions.clear()
        with async_delegation._records_lock:
            async_delegation._records.pop(delegation_id, None)


def test_ttl_reaper_revalidates_session_before_teardown(monkeypatch):
    closed = []
    calls = {"count": 0}
    live_transport = type("T", (), {"_closed": False})()
    original_is_evictable = server._session_is_evictable
    monkeypatch.setattr(server, "_session_pending_kind", lambda sid: "")
    monkeypatch.setattr(server, "_enforce_session_cap", lambda: None)
    monkeypatch.setattr(server, "_reclaim_orphaned_leases", lambda: None)
    monkeypatch.setattr(
        server,
        "_teardown_session",
        lambda session, *, end_reason: closed.append((session, end_reason)),
    )

    def _reattach_after_scan(sid, session, now):
        calls["count"] += 1
        evictable = original_is_evictable(sid, session, now)
        if calls["count"] == 1:
            session["transport"] = live_transport
        return evictable

    monkeypatch.setattr(server, "_session_is_evictable", _reattach_after_scan)
    now = time.time()
    server._sessions.clear()
    server._sessions["ttl-race"] = _idle_evictable_session(now)

    try:
        server._reap_idle_sessions()
        assert server._sessions["ttl-race"]["transport"] is live_transport
        assert calls["count"] == 2
        assert closed == []
    finally:
        server._sessions.clear()


def test_lru_reaper_revalidates_and_tries_next_candidate(monkeypatch):
    closed = []
    live_transport = type("T", (), {"_closed": False})()
    original_is_evictable = server._session_is_lru_evictable
    monkeypatch.setattr(server, "_session_pending_kind", lambda sid: "")
    monkeypatch.setattr(server, "_max_live_sessions", lambda: 1)
    monkeypatch.setattr(
        server,
        "_teardown_session",
        lambda session, *, end_reason: closed.append((session, end_reason)),
    )

    def _reattach_oldest_after_scan(sid, session):
        evictable = original_is_evictable(sid, session)
        if sid == "lru-race" and session.get("transport") is server._detached_ws_transport:
            session["transport"] = live_transport
        return evictable

    monkeypatch.setattr(server, "_session_is_lru_evictable", _reattach_oldest_after_scan)
    now = time.time()
    server._sessions.clear()
    server._sessions["lru-race"] = _idle_evictable_session(now) | {
        "last_active": now - 20 * 3600
    }
    server._sessions["idle-peer"] = _idle_evictable_session(now)

    try:
        server._enforce_session_cap()
        assert server._sessions["lru-race"]["transport"] is live_transport
        assert "idle-peer" not in server._sessions
        assert [reason for _session, reason in closed] == ["lru_evict"]
    finally:
        server._sessions.clear()


def test_session_create_records_ui_model_as_session_override(monkeypatch):
    """The desktop composer owns its model as plain UI state and ships it on
    session.create. The gateway must record it as a PER-SESSION override (built
    into the agent), never a global config write — picking a model for a new chat
    must not mutate the profile default.
    """
    monkeypatch.setattr(server, "_enable_gateway_prompts", lambda: None)
    # Don't run the real deferred build in this storage-focused test.
    monkeypatch.setattr(server, "_start_agent_build", lambda *a, **k: None)
    try:
        resp = server._methods["session.create"](
            "r1",
            {
                "cols": 80,
                "model": "claude-sonnet-4.6",
                "provider": "anthropic",
                "reasoning_effort": "high",
                "fast": True,
            },
        )
        sid = resp["result"]["session_id"]
        sess = server._sessions[sid]
        assert sess["model_override"] == {"model": "claude-sonnet-4.6", "provider": "anthropic"}
        assert sess["create_reasoning_override"] is not None
        assert sess["create_service_tier_override"] == "priority"
        # The immediate response reflects the override (not the global default) so
        # the client never clobbers its sticky pick before the build lands.
        assert resp["result"]["info"]["model"] == "claude-sonnet-4.6"
        assert resp["result"]["info"]["provider"] == "anthropic"

        # Explicit false is not the same as omission: it must suppress a Fast
        # profile default for this session's first request.
        normal = server._methods["session.create"](
            "r2", {"cols": 80, "fast": False}
        )
        normal_sess = server._sessions[normal["result"]["session_id"]]
        assert normal_sess["create_service_tier_override"] == ""

        # No knobs → no overrides; the session builds from the profile default.
        plain = server._methods["session.create"]("r3", {"cols": 80})
        plain_sess = server._sessions[plain["result"]["session_id"]]
        assert plain_sess["model_override"] is None
        assert plain_sess["create_reasoning_override"] is None
        assert plain_sess["create_service_tier_override"] is None
    finally:
        server._sessions.clear()


@pytest.mark.parametrize("service_tier_override", ["priority", ""])
def test_start_agent_build_passes_session_model_override(
    monkeypatch, service_tier_override
):
    """A model staged on the session (e.g. by session.create from the desktop
    composer) must reach _make_agent so the first build runs on it directly —
    no global config, no build-then-switch.
    """
    captured = {}

    class FakeWorker:
        def __init__(self, *_a, **_k):
            pass

        def close(self):
            pass

    def fake_make_agent(sid, key, session_id=None, session_db=None, **kwargs):
        captured.update(kwargs)
        return types.SimpleNamespace(model="claude-sonnet-4.6")

    monkeypatch.setattr(
        server, "_set_session_context", lambda target, cwd=None: []
    )
    monkeypatch.setattr(server, "_clear_session_context", lambda tokens: None)
    monkeypatch.setattr(server, "_make_agent", fake_make_agent)
    monkeypatch.setattr(server, "_SlashWorker", FakeWorker)
    monkeypatch.setattr(server, "_attach_worker", lambda *a, **k: None)
    monkeypatch.setattr(server, "_wire_callbacks", lambda _sid: None)
    monkeypatch.setattr(server, "_emit", lambda *a, **k: None)
    monkeypatch.setattr(server, "_session_info", lambda *a, **k: {})
    monkeypatch.setattr(server, "_start_notification_poller", lambda *a, **k: None)
    monkeypatch.setattr(server, "_notify_session_boundary", lambda *a, **k: None)
    monkeypatch.setattr(server, "_probe_config_health", lambda *_a: None)

    sid = "build-sid"
    override = {"model": "claude-sonnet-4.6", "provider": "anthropic"}
    reasoning = {"enabled": True, "effort": "high"}
    session = {
        "agent": None,
        "agent_ready": threading.Event(),
        "session_key": "k1",
        "profile_home": None,
        "model_override": override,
        "create_reasoning_override": reasoning,
        "create_service_tier_override": service_tier_override,
    }
    server._sessions[sid] = session
    try:
        server._start_agent_build(sid, session)
        assert session["agent_ready"].wait(timeout=3), "agent build did not finish"
        assert captured.get("model_override") == override
        assert captured.get("reasoning_config_override") == reasoning
        assert captured.get("service_tier_override") == service_tier_override
        assert session["agent"].model == "claude-sonnet-4.6"
    finally:
        server._sessions.clear()


# ── billing/subscription state + error serialization ─────────────────


def test_reset_session_agent_clears_session_overrides(monkeypatch):
    """/new is a full conversation boundary: session-scoped /model, /reasoning,
    and /fast overrides do NOT carry into the fresh agent — it re-derives
    everything from config.yaml (#48055, #23131)."""
    captured = {}
    new_agent = types.SimpleNamespace(model="openai/gpt-5.4", service_tier="")
    session = _session(
        agent=types.SimpleNamespace(
            model="openai/gpt-5.4",
            reasoning_config={"enabled": True, "effort": "high"},
            service_tier="",
        ),
        model_override={"model": "openai/gpt-5.4"},
        create_reasoning_override={"enabled": True, "effort": "high"},
        create_service_tier_override="",
    )

    def make_agent(*_args, **kwargs):
        captured.update(kwargs)
        return new_agent

    monkeypatch.setattr(server, "_set_session_context", lambda _key: [])
    monkeypatch.setattr(server, "_clear_session_context", lambda _tokens: None)
    monkeypatch.setattr(server, "_make_agent", make_agent)
    monkeypatch.setattr(server, "_config_model_target", lambda: ("", ""))
    monkeypatch.setattr(server, "_load_show_reasoning", lambda: True)
    monkeypatch.setattr(server, "_load_tool_progress_mode", lambda: "all")
    monkeypatch.setattr(server, "_session_info", lambda *_args: {})
    monkeypatch.setattr(server, "_emit", lambda *_args: None)
    monkeypatch.setattr(server, "_restart_slash_worker", lambda *_args: None)

    server._reset_session_agent("sid", session)

    # No session overrides forwarded — fresh agent builds from config.
    assert "model_override" not in captured
    assert "reasoning_config_override" not in captured
    assert "service_tier_override" not in captured
    # And the session pins are gone so a later rebuild can't resurrect them.
    assert "model_override" not in session
    assert "create_reasoning_override" not in session
    assert "create_service_tier_override" not in session
    assert session["agent"] is new_agent


@pytest.mark.parametrize(
    "card,expected",
    [
        ("canonical", {"kind": "canonical"}),
        (
            "distinct",
            {
                "kind": "distinct",
                "payment_method_id": "pm_auto",
                "brand": None,
                "last4": None,
            },
        ),
        ("none", {"kind": "none"}),
    ],
)
def test_billing_state_serializes_auto_reload_card_union(monkeypatch, card, expected):
    from agent.billing_view import AutoReload, AutoReloadCard, BillingState

    monkeypatch.setattr(server, "_usage_payload", lambda state: {"available": False})
    auto_reload_card = AutoReloadCard(
        kind=card,
        payment_method_id="pm_auto" if card == "distinct" else None,
    )
    state = BillingState(
        logged_in=True,
        auto_reload=AutoReload(enabled=True, card=auto_reload_card),
    )

    result = server._serialize_billing_state(state)

    assert result["auto_reload"]["card"] == expected


def test_billing_state_serializes_server_plan_capability(monkeypatch):
    from agent.billing_view import BillingState

    monkeypatch.setattr(server, "_usage_payload", lambda state: {"available": False})
    state = BillingState(
        logged_in=True,
        role="MEMBER",
        can_change_plan_raw=True,
    )

    result = server._serialize_billing_state(state)

    assert result["is_admin"] is False
    assert result["can_change_plan"] is True


@pytest.mark.parametrize(
    "status,error,retry_after",
    [
        (503, "stripe_unavailable", 75),
        (429, "upgrade_cap_exceeded", None),
        (429, "rate_limited", None),
    ],
)
def test_billing_error_serialization_preserves_server_code(
    status, error, retry_after
):
    import hermes_cli.nous_billing as nb

    headers = _BillingHeaders({"Retry-After": str(retry_after)}) if retry_after else None
    with pytest.raises(nb.BillingTransient) as ei:
        nb._raise_for_error(status, {"error": error}, headers)

    result = server._serialize_billing_error(ei.value)

    assert result["error"] == error
    assert ei.value.error == error
    assert result["retry_after"] == retry_after


def test_billing_rate_limit_without_error_defaults_wire_code():
    import hermes_cli.nous_billing as nb

    exc = nb.BillingRateLimited("slow down", status=429, retry_after=10)

    result = server._serialize_billing_error(exc)

    assert result["error"] == "rate_limited"


def test_subscription_preview_serializes_quote(monkeypatch):
    import hermes_cli.nous_billing as nb

    monkeypatch.setattr(
        nb,
        "post_subscription_preview",
        lambda subscription_type_id: {
            "effect": "charge_now",
            "reason": None,
            "currentTierId": "plus",
            "currentTierName": "Plus",
            "targetTierId": "ultra",
            "targetTierName": "Ultra",
            "monthlyCreditsDelta": "6000",
            "amountDueNowCents": 1234,
            "effectiveAt": None,
        },
    )
    res = _sub_rpc("subscription.preview", {"subscription_type_id": "ultra"})
    assert res["ok"] is True
    assert res["effect"] == "charge_now"
    assert res["amount_due_now_cents"] == 1234
    assert res["target_tier_name"] == "Ultra"
    assert res["monthly_credits_delta"] == "6000"


def test_subscription_preview_requires_tier():
    res = _sub_rpc("subscription.preview", {})
    assert res["ok"] is False
    assert res["error"] == "invalid_request"


def test_subscription_preview_scope_error_maps_to_step_up(monkeypatch):
    import hermes_cli.nous_billing as nb

    def _raise(subscription_type_id):
        raise nb.BillingScopeRequired("billing:manage required")

    monkeypatch.setattr(nb, "post_subscription_preview", _raise)
    res = _sub_rpc("subscription.preview", {"subscription_type_id": "ultra"})
    assert res["ok"] is False
    assert res["error"] == "insufficient_scope"


def test_subscription_change_cancellation(monkeypatch):
    import hermes_cli.nous_billing as nb

    seen = {}

    def _put(*, subscription_type_id=None, cancel=False):
        seen["tier"] = subscription_type_id
        seen["cancel"] = cancel
        return {"rail": "stripe", "cancelAtPeriodEnd": True, "message": "Scheduled to cancel."}

    monkeypatch.setattr(nb, "put_subscription_pending_change", _put)
    res = _sub_rpc("subscription.change", {"cancel": True})
    assert res["ok"] is True
    assert seen == {"tier": None, "cancel": True}
    assert res["message"] == "Scheduled to cancel."


def test_subscription_change_tier_downgrade(monkeypatch):
    import hermes_cli.nous_billing as nb

    seen = {}

    def _put(*, subscription_type_id=None, cancel=False):
        seen["tier"] = subscription_type_id
        seen["cancel"] = cancel
        return {"rail": "stripe", "changeType": "downgrade", "targetTierName": "Plus", "message": "Scheduled."}

    monkeypatch.setattr(nb, "put_subscription_pending_change", _put)
    res = _sub_rpc("subscription.change", {"subscription_type_id": "plus"})
    assert res["ok"] is True
    assert seen == {"tier": "plus", "cancel": False}


def test_subscription_change_requires_tier_or_cancel():
    res = _sub_rpc("subscription.change", {})
    assert res["ok"] is False
    assert res["error"] == "invalid_request"


def test_subscription_upgrade_echoes_status_and_idempotency(monkeypatch):
    import hermes_cli.nous_billing as nb

    seen = {}

    def _upgrade(*, subscription_type_id, idempotency_key):
        seen["key"] = idempotency_key
        return {"status": "upgraded", "targetTierId": "ultra", "targetTierName": "Ultra"}

    monkeypatch.setattr(nb, "post_subscription_upgrade", _upgrade)
    res = _sub_rpc("subscription.upgrade", {"subscription_type_id": "ultra", "idempotency_key": "k-1"})
    assert res["ok"] is True
    assert res["status"] == "upgraded"
    assert res["target_tier_name"] == "Ultra"
    assert res["idempotency_key"] == "k-1"
    assert seen["key"] == "k-1"


def test_subscription_upgrade_requires_action_surfaces_recovery(monkeypatch):
    import hermes_cli.nous_billing as nb

    monkeypatch.setattr(
        nb,
        "post_subscription_upgrade",
        lambda *, subscription_type_id, idempotency_key: {
            "status": "requires_action",
            "reason": "authentication_required",
            "recoveryUrl": "https://portal.example/subscription?org_id=o",
        },
    )
    res = _sub_rpc("subscription.upgrade", {"subscription_type_id": "ultra"})
    # The RPC succeeds; the CHARGE needs 3DS → status + recovery_url for the portal.
    assert res["ok"] is True
    assert res["status"] == "requires_action"
    assert res["recovery_url"].startswith("https://portal.example")
    assert res["idempotency_key"]  # minted when the caller omits one
