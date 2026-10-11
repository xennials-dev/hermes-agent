"""tui_gateway.server — prompt completion delivery, session rows and title persistence.

Split from test_tui_gateway_server.py; shared fixtures and helpers live
in tests/tui_gateway/_server_test_helpers.py.
"""

import os
import threading
import time
import types
from unittest.mock import patch
import pytest
from tui_gateway import server
from tui_gateway.transport import bind_transport, reset_transport

from tests.tui_gateway._server_test_helpers import (
    _ImmediateThread,
    _RecordingAgent,
    _StopAfterOneNotificationPoll,
    _configure_immediate_prompt_run,
    _neuter_agent_prewarm_timer,  # autouse
    _reap_leaked_notification_pollers,  # autouse
    _session,
)


def test_prompt_submit_empty_truncation_allowed_with_confirm(monkeypatch):
    """Intentional restore/regenerate of the first user turn may wipe history."""

    seen = {}
    replaced = []

    class _Agent:
        def run_conversation(
            self, prompt, conversation_history=None, stream_callback=None, **_kwargs
        ):
            seen["prompt"] = prompt
            seen["history"] = conversation_history
            return {
                "final_response": "regenerated",
                "messages": [
                    *(conversation_history or []),
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": "regenerated"},
                ],
            }

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None, **_thread_options):
            self._target = target

        def start(self):
            self._target()

    class _FakeDB:
        def replace_messages(
            self,
            key,
            messages,
            active_only=False,
            archive_dropped=False,
            reject_active_turn_lease=False,
        ):
            replaced.append((key, list(messages)))

    history = [
        {"_row_id": 101, "role": "user", "content": "first"},
        {"_row_id": 102, "role": "assistant", "content": "ok"},
        {"_row_id": 103, "role": "user", "content": "second"},
        {"_row_id": 104, "role": "assistant", "content": "done"},
    ]
    server._sessions["confirm-empty-sid"] = _session(
        agent=_Agent(), history=list(history)
    )

    try:
        monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)
        monkeypatch.setattr(server, "_get_usage", lambda _a: {})
        monkeypatch.setattr(server, "render_message", lambda _t, _c: "")
        monkeypatch.setattr(server, "_emit", lambda *a: None)
        monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())

        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "confirm-empty-sid",
                    "text": "first",
                    "truncate_before_row_id": 101,
                    "truncate_before_user_ordinal": 0,
                    "confirm_truncate": True,
                    "confirm_empty_truncate": True,
                },
            }
        )
        assert resp.get("result"), f"got error: {resp.get('error')}"
        assert seen["prompt"] == "first"
        assert seen["history"] == []
        assert replaced == [("session-key", [])]
        assert server._sessions["confirm-empty-sid"]["history"] == [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "regenerated"},
        ]
    finally:
        server._sessions.pop("confirm-empty-sid", None)


def test_notification_poller_live_loop_requeues_foreign_completion_for_owner(
    monkeypatch,
):
    """A foreign live-loop dequeue is handed back to its proven owner."""
    import queue as _queue_mod

    from tools.process_registry import process_registry

    delivered = {"a": [], "b": []}
    emitted = []
    session_a = _session(session_key="session-a-live-handoff")
    session_b = _session(session_key="session-b-live-handoff")
    event = {
        "type": "completion",
        "session_id": "proc-live-handoff",
        "session_key": "session-a-live-handoff",
        "command": "echo owner",
        "exit_code": 0,
        "output": "owner",
    }
    isolated_queue: _queue_mod.Queue = _queue_mod.Queue()
    isolated_queue.put(event)
    monkeypatch.setattr(process_registry, "completion_queue", isolated_queue)
    monkeypatch.setattr(server, "_get_db", lambda: None)
    monkeypatch.setattr(server, "_emit", lambda *args, **_kwargs: emitted.append(args))

    def _deliver(_rid, sid, session, text, **_kw):
        delivered["a" if sid == "sid-a-live-handoff" else "b"].append(text)
        session["running"] = False

    monkeypatch.setattr(server, "_run_prompt_submit", _deliver)
    server._sessions.update(
        {
            "sid-a-live-handoff": session_a,
            "sid-b-live-handoff": session_b,
        }
    )
    process_registry._completion_consumed.discard(event["session_id"])

    try:
        server._notification_poller_loop(
            _StopAfterOneNotificationPoll(), "sid-b-live-handoff", session_b
        )

        assert delivered["b"] == []
        assert emitted == []
        assert isolated_queue.qsize() == 1
        assert isolated_queue.queue[0] is event

        server._notification_poller_loop(
            _StopAfterOneNotificationPoll(), "sid-a-live-handoff", session_a
        )

        assert len(delivered["a"]) == 1
        assert "proc-live-handoff" in delivered["a"][0]
        assert delivered["b"] == []
        assert isolated_queue.empty()
    finally:
        server._sessions.pop("sid-a-live-handoff", None)
        server._sessions.pop("sid-b-live-handoff", None)
        process_registry._completion_consumed.discard(event["session_id"])
        while not isolated_queue.empty():
            isolated_queue.get_nowait()


def test_completion_ownership_lineage_lookup_failure_fails_closed(monkeypatch):
    """A provenance lookup failure cannot turn an addressed event into ours."""
    import queue as _queue_mod

    from tools.process_registry import process_registry

    class _BrokenDB:
        def resolve_resume_session_id(self, _session_key):
            raise RuntimeError("lineage database unavailable")

    session = _session(session_key="unrelated-live-session")
    event = {
        "type": "completion",
        "session_id": "proc-unknown-lineage",
        "session_key": "unknown-parent",
        "command": "echo unknown",
        "exit_code": 0,
        "output": "unknown",
    }
    isolated_queue: _queue_mod.Queue = _queue_mod.Queue()
    isolated_queue.put(event)
    monkeypatch.setattr(process_registry, "completion_queue", isolated_queue)
    monkeypatch.setattr(server, "_get_db", lambda: _BrokenDB())

    drained = process_registry.drain_notifications(
        session_key="unrelated-live-session",
        owns_event=lambda candidate: server._session_owns_notification_event(
            "sid-unrelated-live", session, candidate
        ),
    )

    assert drained == []
    assert isolated_queue.qsize() == 1
    assert isolated_queue.get_nowait() is event


@pytest.mark.parametrize(
    "routing",
    [
        {"session_key": "missing-owner-key"},
        {"origin_ui_session_id": "missing-owner-sid"},
    ],
)
def test_notification_poller_live_loop_drops_addressed_orphan(
    monkeypatch, routing
):
    """A live poll never injects an addressed event whose owner is gone."""
    import queue as _queue_mod

    from tools.process_registry import process_registry

    delivered = []
    emitted = []
    session = _session(session_key="unrelated-live-key")
    event = {
        "type": "completion",
        "session_id": "proc-live-orphan",
        "command": "echo orphan",
        "exit_code": 0,
        "output": "orphan",
        **routing,
    }
    isolated_queue: _queue_mod.Queue = _queue_mod.Queue()
    isolated_queue.put(event)
    monkeypatch.setattr(process_registry, "completion_queue", isolated_queue)
    monkeypatch.setattr(server, "_get_db", lambda: None)
    monkeypatch.setattr(server, "_emit", lambda *args, **_kwargs: emitted.append(args))
    monkeypatch.setattr(
        server,
        "_run_prompt_submit",
        lambda _rid, _sid, _session, text, **_kw: delivered.append(text),
    )
    server._sessions["sid-live-orphan"] = session
    process_registry._completion_consumed.discard(event["session_id"])

    try:
        server._notification_poller_loop(
            _StopAfterOneNotificationPoll(), "sid-live-orphan", session
        )

        assert delivered == []
        assert emitted == []
        assert isolated_queue.empty()
    finally:
        server._sessions.pop("sid-live-orphan", None)
        process_registry._completion_consumed.discard(event["session_id"])
        while not isolated_queue.empty():
            isolated_queue.get_nowait()


@pytest.mark.parametrize(
    "routing",
    [
        {"session_key": "session-b"},
        {"origin_ui_session_id": "sid_gone"},
    ],
)
def test_notification_poller_drops_orphaned_events(monkeypatch, routing):
    """Addressed completions whose owner is gone are dropped, not hijacked."""
    import queue as _queue_mod

    from tools.process_registry import process_registry

    emitted = []
    delivered = []
    sess = _session(session_key="session-a")
    server._sessions["sid_a"] = sess
    monkeypatch.setattr(server, "_emit", lambda *a, **kw: emitted.append(a))
    monkeypatch.setattr(
        server,
        "_run_prompt_submit",
        lambda _rid, _sid, _session, text, **_kw: delivered.append(text),
    )
    monkeypatch.setattr(server, "_get_db", lambda: None)

    isolated_queue: _queue_mod.Queue = _queue_mod.Queue()
    monkeypatch.setattr(process_registry, "completion_queue", isolated_queue)
    process_registry._completion_consumed.discard("proc_ghost")
    isolated_queue.put(
        {
            "type": "completion",
            "session_id": "proc_ghost",
            "command": "echo from ghost",
            "exit_code": 0,
            "output": "ghost output",
            **routing,
        }
    )

    stop = threading.Event()
    stop.set()

    try:
        server._notification_poller_loop(stop, "sid_a", sess)

        assert [a for a in emitted if a[0] == "status.update"] == []
        assert delivered == []
    finally:
        server._sessions.pop("sid_a", None)
        while not process_registry.completion_queue.empty():
            process_registry.completion_queue.get_nowait()


@pytest.mark.parametrize(
    ("routing", "resolved_key"),
    [
        ({"session_key": "session-a"}, None),
        (
            {
                "session_key": "stale-durable-key",
                "origin_ui_session_id": "sid_a",
            },
            None,
        ),
        ({"session_key": "old-parent-key"}, "session-a"),
    ],
)
def test_notification_poller_delivers_owned_events(
    monkeypatch, routing, resolved_key
):
    """Direct, UI-origin, and compression-lineage owners are delivered."""
    import queue as _queue_mod

    from tools.process_registry import process_registry

    class _CompressionDB:
        def resolve_resume_session_id(self, key):
            return resolved_key if key == "old-parent-key" and resolved_key else key

    delivered = []
    emitted = []
    sess = _session(session_key="session-a")
    server._sessions["sid_a"] = sess
    monkeypatch.setattr(server, "_emit", lambda *a, **kw: emitted.append(a))
    monkeypatch.setattr(
        server,
        "_run_prompt_submit",
        lambda _rid, _sid, _session, text, **_kw: delivered.append(text),
    )
    monkeypatch.setattr(server, "_get_db", lambda: _CompressionDB())

    isolated_queue: _queue_mod.Queue = _queue_mod.Queue()
    monkeypatch.setattr(process_registry, "completion_queue", isolated_queue)
    process_registry._completion_consumed.discard("proc_mine")
    isolated_queue.put(
        {
            "type": "completion",
            "session_id": "proc_mine",
            "command": "echo mine",
            "exit_code": 0,
            "output": "mine",
            **routing,
        }
    )

    stop = threading.Event()
    stop.set()

    try:
        server._notification_poller_loop(stop, "sid_a", sess)

        status_calls = [a for a in emitted if a[0] == "status.update"]
        assert len(status_calls) == 1
        assert status_calls[0][2]["kind"] == "process"
        assert len(delivered) == 1
        assert "proc_mine" in delivered[0]
    finally:
        server._sessions.pop("sid_a", None)
        while not process_registry.completion_queue.empty():
            process_registry.completion_queue.get_nowait()


def test_run_prompt_submit_binds_exact_steer_authority_and_resets_contextvars(
    monkeypatch, tmp_path
):
    """The turn thread commissions children with this session generation only."""
    from tools.delegate_tool import _capture_gateway_steer_authority
    from tui_gateway.transport import (
        bind_transport,
        current_transport,
        reset_transport,
    )

    class _Transport:
        def write(self, _obj):
            return True

        def close(self):
            return None

    observed = {}
    owner_transport = _Transport()
    previous_transport = _Transport()
    previous_record = {"session_key": "previous-generation"}

    class _CapturingAgent(_RecordingAgent):
        def run_conversation(self, prompt, **kwargs):
            authority = _capture_gateway_steer_authority("sid-owner")
            observed["transport"] = authority[0]
            observed["record"] = authority[1]
            return super().run_conversation(prompt, **kwargs)

    _configure_immediate_prompt_run(monkeypatch, tmp_path)
    session = _session(
        session_key="session-owner",
        agent=_CapturingAgent([]),
        running=True,
        transport=owner_transport,
    )
    server._sessions["sid-owner"] = session
    transport_token = bind_transport(previous_transport)
    record_token = server._current_runtime_session_record.set(previous_record)
    try:
        server._run_prompt_submit("rid-owner", "sid-owner", session, "commission")

        assert observed == {"transport": owner_transport, "record": session}
        assert current_transport() is previous_transport
        assert server._current_runtime_session_record.get() is previous_record
    finally:
        server._current_runtime_session_record.reset(record_token)
        reset_transport(transport_token)
        server._sessions.pop("sid-owner", None)


def test_run_prompt_submit_rejects_worker_when_close_wins_publication(
    monkeypatch, tmp_path
):
    """A close claimed during message.start must prevent the worker from running."""
    _configure_immediate_prompt_run(monkeypatch, tmp_path, immediate_threads=False)
    emit_entered = threading.Event()
    release_emit = threading.Event()
    dispatch_results = []
    turns = []
    popped = []
    sid = "close-wins-publication"
    session = _session(
        session_key="close-wins-publication-key",
        agent=_RecordingAgent(turns),
        running=True,
    )

    def _blocking_emit(event, *_args, **_kwargs):
        if event == "message.start":
            emit_entered.set()
            assert release_emit.wait(timeout=2.0)

    monkeypatch.setattr(server, "_emit", _blocking_emit)
    server._sessions[sid] = session
    dispatch_thread = threading.Thread(
        target=lambda: dispatch_results.append(
            server._run_prompt_submit("rid", sid, session, "turn")
        )
    )

    try:
        dispatch_thread.start()
        assert emit_entered.wait(timeout=1.0)
        popped.append(server._pop_session_by_id(sid))
        assert popped == [session]
        release_emit.set()
        dispatch_thread.join(timeout=2.0)
    finally:
        release_emit.set()
        dispatch_thread.join(timeout=2.0)
        run_thread = session.get("_run_thread")
        if run_thread is not None and run_thread.is_alive():
            run_thread.join(timeout=2.0)
        server._sessions.pop(sid, None)

    assert dispatch_results == [False]
    assert session["running"] is False
    assert turns == []


@pytest.mark.parametrize("exit_code", [0, 7])
def test_run_prompt_submit_requeues_foreign_completion(
    monkeypatch, tmp_path, exit_code
):
    import queue as _queue_mod

    from tools.process_registry import process_registry

    _configure_immediate_prompt_run(monkeypatch, tmp_path)
    turns = []
    session_a = _session(session_key="session-a")
    session_b = _session(
        session_key="session-b",
        agent=_RecordingAgent(turns),
        running=True,
    )
    event = {
        "type": "completion",
        "session_id": f"proc_foreign_{exit_code}",
        "session_key": "session-a",
        "command": "safe-test-command",
        "exit_code": exit_code,
        "output": "foreign",
    }
    isolated_queue: _queue_mod.Queue = _queue_mod.Queue()
    isolated_queue.put(event)
    monkeypatch.setattr(process_registry, "completion_queue", isolated_queue)
    server._sessions["sid_a"] = session_a
    server._sessions["sid_b"] = session_b

    try:
        server._run_prompt_submit("rid-b", "sid_b", session_b, "session-b-turn")

        assert turns == ["session-b-turn"]
        assert isolated_queue.get_nowait() == event
        assert isolated_queue.empty()
    finally:
        server._sessions.pop("sid_a", None)
        server._sessions.pop("sid_b", None)
        process_registry._completion_consumed.discard(event["session_id"])


def test_run_prompt_submit_delivers_completion_observed_by_poll(monkeypatch, tmp_path):
    import queue as _queue_mod

    from tools.process_registry import process_registry

    _configure_immediate_prompt_run(monkeypatch, tmp_path)
    turns = []
    session = _session(
        session_key="session-a",
        agent=_RecordingAgent(turns),
        running=True,
    )
    event = {
        "type": "completion",
        "session_id": "proc_polled",
        "session_key": "session-a",
        "command": "safe-test-command",
        "exit_code": 0,
        "output": "observed but not consumed",
    }
    isolated_queue: _queue_mod.Queue = _queue_mod.Queue()
    isolated_queue.put(event)
    monkeypatch.setattr(process_registry, "completion_queue", isolated_queue)
    process_registry._completion_consumed.discard(event["session_id"])
    process_registry._poll_observed.add(event["session_id"])
    server._sessions["sid_a"] = session

    try:
        server._run_prompt_submit("rid-a", "sid_a", session, "session-a-turn")

        assert turns[0] == "session-a-turn"
        assert len(turns) == 2
        assert "proc_polled" in turns[1]
        assert isolated_queue.empty()
    finally:
        server._sessions.pop("sid_a", None)
        process_registry._completion_consumed.discard(event["session_id"])
        process_registry._poll_observed.discard(event["session_id"])


def test_run_prompt_submit_requeues_all_unstarted_notifications_with_real_threading(
    monkeypatch, tmp_path
):
    import queue as _queue_mod

    from tools.process_registry import process_registry

    _configure_immediate_prompt_run(
        monkeypatch, tmp_path, immediate_threads=False
    )
    real_thread_class = threading.Thread
    threads = []
    nested_started = threading.Event()
    release_nested = threading.Event()
    turns = []

    def _recording_thread(*args, **kwargs):
        thread = real_thread_class(*args, **kwargs)
        threads.append(thread)
        return thread

    class _BlockingNotificationAgent(_RecordingAgent):
        def run_conversation(self, prompt, conversation_history=None, stream_callback=None, **_kwargs):
            turns.append(prompt)
            if "proc_batch_1" in prompt:
                nested_started.set()
                if not release_nested.wait(timeout=5):
                    raise TimeoutError("notification turn was not released")
            return {"final_response": "", "messages": []}

    monkeypatch.setattr(server.threading, "Thread", _recording_thread)
    session = _session(
        session_key="session-a",
        agent=_BlockingNotificationAgent(turns),
        running=True,
    )
    events = [
        {
            "type": "completion",
            "session_id": f"proc_batch_{index}",
            "session_key": "session-a",
            "command": "safe-test-command",
            "exit_code": 0,
            "output": f"owned-{index}",
        }
        for index in range(1, 4)
    ]
    # Consecutive completions share one turn (#104671); a watch_match is a turn
    # barrier, so it is the in-flight turn behind which batch_2/batch_3 must survive.
    events[0].update(type="watch_match", pattern="owned-1")
    isolated_queue: _queue_mod.Queue = _queue_mod.Queue()
    for event in events:
        isolated_queue.put(event)
    monkeypatch.setattr(process_registry, "completion_queue", isolated_queue)
    server._sessions["sid_a"] = session

    try:
        server._run_prompt_submit("rid-a", "sid_a", session, "session-a-turn")

        assert nested_started.wait(timeout=5)
        threads[0].join(timeout=5)
        assert not threads[0].is_alive()
        # Membership, not order: the completion_queue is process-global, and
        # notification pollers leaked by earlier session.init tests in this
        # file legitimately steal-and-requeue foreign-session events (see
        # _notification_poller_loop's belongs-elsewhere branch), rotating the
        # queue. The requeue contract is that batch_2 and batch_3 both remain
        # queued (never consumed) while batch_1's turn is in flight — so drain
        # with a deadline (an event may be transiently held by a poller
        # mid-cycle) and assert exactly {batch_2, batch_3} come back.
        queued: dict = {}
        deadline = time.time() + 5.0
        while time.time() < deadline and set(queued) != {
            "proc_batch_2",
            "proc_batch_3",
        }:
            try:
                evt = isolated_queue.get(timeout=0.1)
            except _queue_mod.Empty:
                continue
            queued[evt["session_id"]] = evt
        assert set(queued) == {"proc_batch_2", "proc_batch_3"}
    finally:
        release_nested.set()
        for thread in threads:
            thread.join(timeout=5)
        server._sessions.pop("sid_a", None)
        while not isolated_queue.empty():
            isolated_queue.get_nowait()
        for event in events:
            process_registry._completion_consumed.discard(event["session_id"])
            process_registry._poll_observed.discard(event["session_id"])


def test_run_prompt_submit_delivers_completion_owned_through_compression_lineage(
    monkeypatch, tmp_path
):
    import queue as _queue_mod

    from tools.process_registry import process_registry

    class _CompressionDB:
        def resolve_resume_session_id(self, key):
            return "new-child-key" if key == "old-parent-key" else key

    _configure_immediate_prompt_run(monkeypatch, tmp_path)
    monkeypatch.setattr(server, "_get_db", lambda: _CompressionDB())
    ownership_checks = []
    original_owns_event = server._session_owns_notification_event

    def _record_ownership_check(sid, checked_session, checked_event):
        ownership_checks.append(checked_event["session_id"])
        return original_owns_event(sid, checked_session, checked_event)

    monkeypatch.setattr(
        server, "_session_owns_notification_event", _record_ownership_check
    )
    turns = []
    session = _session(
        session_key="new-child-key",
        agent=_RecordingAgent(turns),
        running=True,
    )
    event = {
        "type": "completion",
        "session_id": "proc_precompression",
        "session_key": "old-parent-key",
        "command": "safe-test-command",
        "exit_code": 0,
        "output": "owned",
    }
    isolated_queue: _queue_mod.Queue = _queue_mod.Queue()
    isolated_queue.put(event)
    monkeypatch.setattr(process_registry, "completion_queue", isolated_queue)
    server._sessions["sid_b"] = session

    try:
        server._run_prompt_submit("rid-b", "sid_b", session, "session-b-turn")

        assert turns[0] == "session-b-turn"
        assert len(turns) == 2
        assert "proc_precompression" in turns[1]
        assert ownership_checks == ["proc_precompression"]
        assert isolated_queue.empty()
    finally:
        server._sessions.pop("sid_b", None)
        process_registry._completion_consumed.discard(event["session_id"])


def test_run_prompt_submit_prefers_origin_ui_session_id(monkeypatch, tmp_path):
    import queue as _queue_mod

    from tools.process_registry import process_registry

    _configure_immediate_prompt_run(monkeypatch, tmp_path)
    ownership_checks = []
    original_owns_event = server._session_owns_notification_event

    def _record_ownership_check(sid, checked_session, checked_event):
        ownership_checks.append(checked_event["session_id"])
        return original_owns_event(sid, checked_session, checked_event)

    monkeypatch.setattr(
        server, "_session_owns_notification_event", _record_ownership_check
    )
    turns = []
    session = _session(
        session_key="current-key",
        agent=_RecordingAgent(turns),
        running=True,
    )
    event = {
        "type": "completion",
        "session_id": "proc_origin_owned",
        "session_key": "stale-durable-key",
        "origin_ui_session_id": "sid_b",
        "command": "safe-test-command",
        "exit_code": 0,
        "output": "owned",
    }
    isolated_queue: _queue_mod.Queue = _queue_mod.Queue()
    isolated_queue.put(event)
    monkeypatch.setattr(process_registry, "completion_queue", isolated_queue)
    server._sessions["sid_b"] = session

    try:
        server._run_prompt_submit("rid-b", "sid_b", session, "session-b-turn")

        assert turns[0] == "session-b-turn"
        assert len(turns) == 2
        assert "proc_origin_owned" in turns[1]
        assert ownership_checks == ["proc_origin_owned"]
        assert isolated_queue.empty()
    finally:
        server._sessions.pop("sid_b", None)
        process_registry._completion_consumed.discard(event["session_id"])



    """session.create must NOT eagerly write a DB row.

    Every TUI/desktop launch opens a session here just to paint the composer;
    eagerly creating a row left an empty "Untitled" session behind for every
    launch the user never typed into. The row is created lazily on first prompt.
    """
    created = []

    class _FakeDB:
        def create_session(self, *args, **kwargs):
            created.append((args, kwargs))

    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    monkeypatch.setattr(server, "_start_agent_build", lambda *a, **k: None)
    monkeypatch.setattr(
        server.threading,
        "Timer",
        lambda *a, **k: types.SimpleNamespace(daemon=False, start=lambda: None),
    )

    resp = server.handle_request(
        {"id": "1", "method": "session.create", "params": {"cols": 80}}
    )
    sid = resp["result"]["session_id"]
    try:
        assert resp["result"]["stored_session_id"]
        assert created == [], "session.create should not persist an empty DB row"
    finally:
        server._sessions.pop(sid, None)


def test_ensure_session_db_row_persists_explicit_cwd(monkeypatch, tmp_path):
    """An explicitly chosen workspace is persisted as the session cwd."""
    created = []

    class _FakeDB:
        def create_session(self, key, source=None, model=None, model_config=None, parent_session_id=None, cwd=None, profile_name=None, user_id=None):
            created.append(
                {"key": key, "source": source, "model": model, "model_config": model_config, "cwd": cwd}
            )

    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    monkeypatch.setattr(server, "_resolve_model", lambda: "test-model")
    monkeypatch.delenv("HERMES_DESKTOP", raising=False)
    monkeypatch.delenv("HERMES_DESKTOP_TERMINAL", raising=False)

    server._ensure_session_db_row({"session_key": "k1", "cwd": str(tmp_path), "explicit_cwd": True})

    assert created == [
        {"key": "k1", "source": "tui", "model": "test-model", "model_config": None, "cwd": str(tmp_path)}
    ]


def test_ensure_session_db_row_persists_session_source(monkeypatch):
    created = []

    class _FakeDB:
        def create_session(self, key, source=None, model=None, model_config=None, parent_session_id=None, cwd=None, profile_name=None, user_id=None):
            created.append(
                {"key": key, "source": source, "model": model, "model_config": model_config, "cwd": cwd}
            )

    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    monkeypatch.setattr(server, "_resolve_model", lambda: "test-model")

    server._ensure_session_db_row({"session_key": "k1", "source": "tool"})

    assert created == [
        {"key": "k1", "source": "tool", "model": "test-model", "model_config": None, "cwd": None}
    ]


def test_ensure_session_db_row_records_a_terminal_workspace(monkeypatch, tmp_path):
    """A terminal session's directory IS its workspace, so the row records it.

    The user cd'd there before running hermes. Leaving it null stranded the row
    with no cwd and no git_repo_root, so the sidebar could never place the
    session under its project.
    """
    created = []

    class _FakeDB:
        def create_session(self, key, source=None, model=None, model_config=None, parent_session_id=None, cwd=None, profile_name=None, user_id=None):
            created.append(
                {"key": key, "source": source, "model": model, "model_config": model_config, "cwd": cwd}
            )

    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    monkeypatch.setattr(server, "_resolve_model", lambda: "test-model")
    monkeypatch.delenv("HERMES_DESKTOP", raising=False)
    monkeypatch.delenv("HERMES_DESKTOP_TERMINAL", raising=False)

    server._ensure_session_db_row({"session_key": "k1", "cwd": str(tmp_path)})

    assert created == [
        {"key": "k1", "source": "tui", "model": "test-model", "model_config": None, "cwd": str(tmp_path)}
    ]


def test_ensure_session_db_row_defaults_desktop_to_no_workspace(monkeypatch, tmp_path):
    """The desktop launches from wherever the bundle was opened, so an unpicked
    cwd is an artifact — those chats stay null and group under "No workspace"."""
    created = []

    class _FakeDB:
        def create_session(self, key, source=None, model=None, model_config=None, parent_session_id=None, cwd=None, profile_name=None, user_id=None):
            created.append(
                {"key": key, "source": source, "model": model, "model_config": model_config, "cwd": cwd}
            )

    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    monkeypatch.setattr(server, "_resolve_model", lambda: "test-model")

    server._ensure_session_db_row({"session_key": "k1", "source": "desktop", "cwd": str(tmp_path)})

    assert created == [
        {"key": "k1", "source": "desktop", "model": "test-model", "model_config": None, "cwd": None}
    ]


def test_ensure_session_db_row_persists_session_model_override(monkeypatch):
    """The session's composer pick (model + effort + fast) must own the DB row.

    Regression for the "switched to gpt-5.5, reconnect snapped back to opus"
    bug: the row was created with the global default and won the INSERT-OR-IGNORE
    race, so resume rebuilt from the global model and silently reverted the
    chat. The override model + a model_config carrying provider/reasoning/
    service_tier must be persisted so session.resume restores all three.
    """
    created = []

    class _FakeDB:
        def create_session(self, key, source=None, model=None, model_config=None, parent_session_id=None, cwd=None, profile_name=None, user_id=None):
            created.append(
                {"key": key, "model": model, "model_config": model_config, "cwd": cwd}
            )

    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    monkeypatch.setattr(server, "_resolve_model", lambda: "global/default")

    server._ensure_session_db_row(
        {
            "session_key": "k1",
            "model_override": {"model": "openai/gpt-5.5", "provider": "openrouter"},
            "create_reasoning_override": {"effort": "high"},
            "create_service_tier_override": "priority",
        }
    )

    assert len(created) == 1
    row = created[0]
    assert row["model"] == "openai/gpt-5.5"
    assert row["model_config"]["model"] == "openai/gpt-5.5"
    assert row["model_config"]["provider"] == "openrouter"
    assert row["model_config"]["reasoning_config"] == {"effort": "high"}
    assert row["model_config"]["service_tier"] == "priority"


def test_ensure_session_db_row_no_override_uses_global(monkeypatch):
    """A chat that made no explicit pick falls back to the global model and
    writes no model_config (so it tracks the profile default)."""
    created = []

    class _FakeDB:
        def create_session(self, key, source=None, model=None, model_config=None, parent_session_id=None, cwd=None, profile_name=None, user_id=None):
            created.append({"model": model, "model_config": model_config})

    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    monkeypatch.setattr(server, "_resolve_model", lambda: "global/default")

    server._ensure_session_db_row({"session_key": "k1", "model_override": None})

    assert created == [{"model": "global/default", "model_config": None}]


def test_ensure_session_db_row_stamps_profile_name(monkeypatch, tmp_path):
    """A profile session's row carries its owning profile_name, so unified
    multi-profile aggregation never has to guess from which state.db file the
    row happened to be read (the cross-profile session-jump bug)."""
    profile_home = tmp_path / "profiles" / "mlperf"
    profile_home.mkdir(parents=True)
    created = []

    class _ProfileDB:
        def __init__(self, db_path=None):
            created.append({"db_path": db_path})

        def create_session(self, key, **kwargs):
            created[-1].update({"key": key, "profile_name": kwargs.get("profile_name")})

        def close(self):
            pass

    monkeypatch.setattr("hermes_state_registry.acquire", _ProfileDB)
    monkeypatch.setattr(server, "_resolve_model", lambda: "test-model")

    server._ensure_session_db_row(
        {"session_key": "k1", "profile_home": str(profile_home)}
    )

    assert created and created[0]["key"] == "k1"
    assert created[0]["profile_name"] == "mlperf"
    assert created[0]["db_path"] == profile_home / "state.db"


def test_ensure_session_db_row_stamps_launch_profile_name(monkeypatch):
    """A launch-profile session row is stamped with the ACTUAL profile name,
    never NULL. NULL-as-launch-profile rows vanish from the desktop sidebar
    (profile-keyed matching) and break @session:<profile>/<id> deep links, and
    the #94724 one-shot backfill cannot keep repairing rows minted after it
    ran (#99222)."""
    created = []

    class _FakeDB:
        def create_session(self, key, **kwargs):
            created.append({"key": key, "profile_name": kwargs.get("profile_name")})

    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    monkeypatch.setattr(server, "_resolve_model", lambda: "test-model")
    monkeypatch.setattr(server, "_current_profile_name", lambda: "default")

    server._ensure_session_db_row({"session_key": "k1"})

    assert created and created[0]["key"] == "k1"
    assert created[0]["profile_name"] == "default"


def test_session_title_clears_pending_after_persist(monkeypatch):
    class _FakeDB:
        def __init__(self):
            self.title = "old"

        def get_session_title(self, _key):
            return self.title

        def get_session(self, _key):
            return {"id": _key, "title": self.title}

        def set_session_title(self, _key, title):
            self.title = title
            return True

    db = _FakeDB()
    emitted = []
    server._sessions["sid"] = _session(pending_title="stale")
    monkeypatch.setattr(server, "_get_db", lambda: db)
    monkeypatch.setattr(server, "_emit", lambda *args: emitted.append(args))
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.title",
                "params": {"session_id": "sid", "title": "fresh"},
            }
        )

        assert resp["result"]["pending"] is False
        assert resp["result"]["title"] == "fresh"
        assert server._sessions["sid"]["pending_title"] is None
        assert emitted[-1][0:2] == ("session.info", "sid")
        assert emitted[-1][2]["title"] == "fresh"
    finally:
        server._sessions.pop("sid", None)


def test_session_title_does_not_queue_noop_when_row_exists(monkeypatch):
    class _FakeDB:
        def __init__(self):
            self.title = "same title"

        def get_session_title(self, _key):
            return self.title

        def get_session(self, _key):
            return {"id": _key, "title": self.title}

        def set_session_title(self, _key, _title):
            # Simulate sqlite UPDATE rowcount==0 for no-op update.
            return False

    server._sessions["sid"] = _session(pending_title="stale")
    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.title",
                "params": {"session_id": "sid", "title": "same title"},
            }
        )

        assert resp["result"]["pending"] is False
        assert resp["result"]["title"] == "same title"
        assert server._sessions["sid"]["pending_title"] is None
    finally:
        server._sessions.pop("sid", None)


def test_session_title_get_falls_back_to_pending_when_db_read_throws(monkeypatch):
    class _FakeDB:
        def get_session_title(self, _key):
            raise RuntimeError("db temporarily locked")

    server._sessions["sid"] = _session(pending_title="queued title")
    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    try:
        resp = server.handle_request(
            {"id": "1", "method": "session.title", "params": {"session_id": "sid"}}
        )
        assert resp["result"]["title"] == "queued title"
    finally:
        server._sessions.pop("sid", None)


def test_session_title_get_retries_persist_for_pending_title(monkeypatch):
    class _FakeDB:
        def __init__(self):
            self.title = ""

        def get_session_title(self, _key):
            return self.title

        def set_session_title(self, _key, title):
            self.title = title
            return True

        def get_session(self, _key):
            return {"id": _key, "title": self.title}

    db = _FakeDB()
    server._sessions["sid"] = _session(pending_title="queued title")
    monkeypatch.setattr(server, "_get_db", lambda: db)
    try:
        resp = server.handle_request(
            {"id": "1", "method": "session.title", "params": {"session_id": "sid"}}
        )
        assert resp["result"]["title"] == "queued title"
        assert server._sessions["sid"]["pending_title"] is None
    finally:
        server._sessions.pop("sid", None)


def test_session_title_get_retries_pending_even_when_db_has_title(monkeypatch):
    class _FakeDB:
        def __init__(self):
            self.title = "auto title"

        def get_session_title(self, _key):
            return self.title

        def set_session_title(self, _key, title):
            self.title = title
            return True

        def get_session(self, _key):
            return {"id": _key, "title": self.title}

    db = _FakeDB()
    server._sessions["sid"] = _session(pending_title="queued title")
    monkeypatch.setattr(server, "_get_db", lambda: db)
    try:
        resp = server.handle_request(
            {"id": "1", "method": "session.title", "params": {"session_id": "sid"}}
        )
        assert resp["result"]["title"] == "queued title"
        assert server._sessions["sid"]["pending_title"] is None
    finally:
        server._sessions.pop("sid", None)


def test_session_title_rejects_empty_title_with_specific_error_code(monkeypatch):
    class _FakeDB:
        def get_session_title(self, _key):
            return ""

    server._sessions["sid"] = _session()
    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.title",
                "params": {"session_id": "sid", "title": "   "},
            }
        )
        assert "error" in resp
        assert resp["error"]["code"] == 4021
    finally:
        server._sessions.pop("sid", None)


def test_session_title_set_maps_valueerror_to_user_error(monkeypatch):
    class _FakeDB:
        def get_session_title(self, _key):
            return ""

        def get_session(self, _key):
            return {"id": _key}

        def set_session_title(self, _key, _title):
            raise ValueError("Title already in use")

    server._sessions["sid"] = _session()
    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.title",
                "params": {"session_id": "sid", "title": "dup"},
            }
        )
        assert "error" in resp
        assert resp["error"]["code"] == 4022
        assert "already in use" in resp["error"]["message"]
    finally:
        server._sessions.pop("sid", None)


def test_session_title_set_errors_when_row_lookup_fails_after_noop(monkeypatch):
    class _FakeDB:
        def get_session_title(self, _key):
            return ""

        def get_session(self, _key):
            raise RuntimeError("row lookup failed")

        def set_session_title(self, _key, _title):
            return False

    server._sessions["sid"] = _session()
    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.title",
                "params": {"session_id": "sid", "title": "fresh"},
            }
        )
        assert "error" in resp
        assert resp["error"]["code"] == 5007
        assert "row lookup failed" in resp["error"]["message"]
    finally:
        server._sessions.pop("sid", None)


def test_session_create_drops_pending_title_on_valueerror(monkeypatch):
    """When set_session_title raises ValueError during post-message title flush,
    pending_title should be dropped (non-retryable). Updated for post-#18370
    lazy session creation where title is applied post-first-message.
    """

    class _Agent:
        session_id = "test-session"
        model = "x"
        provider = "openrouter"
        base_url = ""
        api_key = ""
        _cached_system_prompt = ""

        def run_conversation(self, prompt, **kw):
            return {
                "final_response": "ok",
                "messages": [{"role": "assistant", "content": "ok"}],
            }

    class _FakeDB:
        def set_session_title(self, _key, _title):
            raise ValueError("Title already in use")

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None, **kw):
            self._target = target

        def start(self):
            self._target()

    agent = _Agent()
    session = {
        "agent": agent,
        "session_key": "test-session",
        "history": [],
        "history_lock": threading.Lock(),
        "history_version": 0,
        "running": False,
        "attached_images": [],
        "image_counter": 0,
        "cols": 80,
        "slash_worker": None,
        "show_reasoning": False,
        "tool_progress_mode": "all",
        "pending_title": "duplicate title",
    }

    server._sessions["sid"] = session
    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    monkeypatch.setattr(server, "_emit", lambda *a, **kw: None)
    monkeypatch.setattr(server, "make_stream_renderer", lambda cols: None)
    monkeypatch.setattr(server, "render_message", lambda raw, cols: None)
    monkeypatch.setattr(
        server, "_sync_session_key_after_compress", lambda *a, **kw: None
    )
    monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)

    try:
        server.handle_request(
            {"id": "1", "method": "prompt.submit", "params": {"session_id": "sid", "text": "hello"}}
        )
        assert session["pending_title"] is None
    finally:
        server._sessions.pop("sid", None)


def test_config_set_yolo_toggles_session_scope():
    from tools.approval import clear_session, is_session_yolo_enabled

    server._sessions["sid"] = _session()
    try:
        resp_on = server.handle_request(
            {
                "id": "1",
                "method": "config.set",
                "params": {"session_id": "sid", "key": "yolo"},
            }
        )
        assert resp_on["result"]["value"] == "1"
        assert is_session_yolo_enabled("session-key") is True

        resp_off = server.handle_request(
            {
                "id": "2",
                "method": "config.set",
                "params": {"session_id": "sid", "key": "yolo"},
            }
        )
        assert resp_off["result"]["value"] == "0"
        assert is_session_yolo_enabled("session-key") is False
    finally:
        clear_session("session-key")
        server._sessions.clear()


def test_config_set_yolo_stale_session_id_is_refused_not_process_scoped(monkeypatch):
    """A runtime id the backend no longer holds must answer 4001 so the client resumes, not flip
    the process HERMES_YOLO_MODE that every child spawned afterwards inherits."""
    monkeypatch.setenv("HERMES_YOLO_MODE", "0")  # setenv, not delenv: undo must also drop a leaked "1"

    with patch.dict(server._sessions, {}, clear=True):
        resp = server.handle_request(
            {
                "id": "1",
                "method": "config.set",
                "params": {"session_id": "reaped-sid", "key": "yolo", "value": "1"},
            }
        )

    assert resp.get("error", {}).get("code") == 4001, resp
    assert os.environ["HERMES_YOLO_MODE"] == "0"


def test_config_set_yolo_global_scope_writes_approvals_mode(tmp_path, monkeypatch):
    """Shift+click the desktop zap -> scope="global" flips persistent approvals.mode."""
    import hermes_yaml as yaml

    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.safe_dump({"approvals": {"mode": "manual"}}))
    monkeypatch.setattr(server, "_hermes_home", tmp_path)

    resp_on = server.handle_request(
        {
            "id": "1",
            "method": "config.set",
            "params": {"key": "yolo", "scope": "global"},
        }
    )
    assert resp_on["result"]["value"] == "1"
    assert resp_on["result"]["scope"] == "global"
    assert yaml.safe_load(cfg_path.read_text())["approvals"]["mode"] == "off"

    resp_off = server.handle_request(
        {
            "id": "2",
            "method": "config.set",
            "params": {"key": "yolo", "scope": "global"},
        }
    )
    assert resp_off["result"]["value"] == "0"
    assert yaml.safe_load(cfg_path.read_text())["approvals"]["mode"] == "manual"


def test_config_get_approval_mode_uses_smart_default_when_key_is_missing(
    tmp_path, monkeypatch
):
    import hermes_yaml as yaml

    monkeypatch.setattr(server, "_hermes_home", tmp_path)
    # Point the canonical resolver (load_config → env HERMES_HOME) at the
    # temp home too, so the smart default is asserted against THIS config
    # rather than whatever the developer's real ~/.hermes happens to hold.
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    (tmp_path / "config.yaml").write_text(
        yaml.safe_dump({"approvals": {"timeout": 15}})
    )

    response = server.handle_request(
        {"id": "1", "method": "config.get", "params": {"key": "approvals.mode"}}
    )
    assert response["result"]["value"] == "smart"
