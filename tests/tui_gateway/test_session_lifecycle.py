"""tui_gateway.server — session lifecycle: create/delete, profile scoping and mirrors.

Split from test_tui_gateway_server.py; shared fixtures and helpers live
in tests/tui_gateway/_server_test_helpers.py.
"""

import contextlib
import sys
import threading
import time
import types
from pathlib import Path
import pytest
from tui_gateway import server

from tests.tui_gateway._server_test_helpers import (
    _PARTIAL_COMPRESSED_HEAD,
    _PARTIAL_FAKE_HISTORY,
    _neuter_agent_prewarm_timer,  # autouse
    _open_request,
    _partial_compress_agent,
    _reap_leaked_notification_pollers,  # autouse
    _session,
)


def test_dead_build_thread_fails_fast_not_full_cap(monkeypatch):
    """A build thread that died without setting agent_ready means the build
    died hard — the waiter must fail promptly with a visible error instead of
    sitting out the full wait cap on a corpse."""
    emitted = []

    class _DeadThread:
        def is_alive(self):
            return False

    ready = threading.Event()  # never set
    session = _session(agent_ready=ready)
    session["agent"] = None
    session["running"] = True
    session["_agent_build_thread"] = _DeadThread()
    session["agent_error"] = "agent init failed: boom"
    server._sessions["sid"] = session

    try:
        monkeypatch.setattr(server, "_emit", lambda *args, **kwargs: emitted.append(args))
        # Short slices so the test is fast; the dead-thread check fires on the
        # first empty slice, far below the cap.
        monkeypatch.setattr(server, "_AGENT_BUILD_WAIT_SLICE", 0.01)

        start = time.monotonic()
        err = server._wait_agent_for_prompt(session, "rid-1", "sid")
        elapsed = time.monotonic() - start

        assert err is not None
        assert "boom" in (err.get("error") or {}).get("message", "")
        assert elapsed < 5.0, f"dead-thread detection took {elapsed:.1f}s"
    finally:
        server._sessions.pop("sid", None)


def test_wait_agent_for_prompt_honors_cancel_mid_wait(monkeypatch):
    """A cancel arriving during the patient wait must end it promptly and
    return None (the caller's cancel branch owns the user-visible event)."""
    ready = threading.Event()  # never set
    session = _session(agent_ready=ready)
    session["agent"] = None
    session["running"] = True
    server._sessions["sid"] = session

    try:
        monkeypatch.setattr(server, "_AGENT_BUILD_WAIT_SLICE", 0.01)

        def cancel_soon():
            time.sleep(0.05)
            with session["history_lock"]:
                session["_turn_cancel_requested"] = True

        canceller = threading.Thread(target=cancel_soon)
        canceller.start()
        start = time.monotonic()
        err = server._wait_agent_for_prompt(session, "rid-1", "sid")
        elapsed = time.monotonic() - start
        canceller.join()

        assert err is None
        assert elapsed < 5.0, f"cancel honored only after {elapsed:.1f}s"
    finally:
        server._sessions.pop("sid", None)


def test_agent_build_wait_cap_config_override(monkeypatch):
    """agent.build_wait_timeout in config.yaml overrides the default cap;
    invalid/absent values fall back to 600s."""
    monkeypatch.setattr(server, "_load_cfg", lambda: {"agent": {"build_wait_timeout": 90}})
    assert server._agent_build_wait_cap() == 90.0

    monkeypatch.setattr(server, "_load_cfg", lambda: {"agent": {}})
    default_cap = server._agent_build_wait_cap()
    assert default_cap > 0 and default_cap != 90.0

    monkeypatch.setattr(server, "_load_cfg", lambda: {"agent": {"build_wait_timeout": 0}})
    assert server._agent_build_wait_cap() == default_cap

    monkeypatch.setattr(server, "_load_cfg", lambda: {"agent": {"build_wait_timeout": "nonsense"}})
    assert server._agent_build_wait_cap() == default_cap


def test_wait_agent_for_prompt_expires_at_cap(monkeypatch):
    """A genuinely hung build (thread alive, never ready) still fails at the
    bounded cap with a message that tells the user their text was not sent."""
    class _AliveThread:
        def is_alive(self):
            return True

    ready = threading.Event()  # never set
    session = _session(agent_ready=ready)
    session["agent"] = None
    session["running"] = True
    session["_agent_build_thread"] = _AliveThread()
    server._sessions["sid"] = session

    try:
        monkeypatch.setattr(server, "_AGENT_BUILD_WAIT_SLICE", 0.01)
        monkeypatch.setattr(server, "_agent_build_wait_cap", lambda: 0.05)

        err = server._wait_agent_for_prompt(session, "rid-1", "sid")

        assert err is not None
        message = (err.get("error") or {}).get("message", "")
        assert "timed out" in message and "was not sent" in message
    finally:
        server._sessions.pop("sid", None)


def test_clear_pending_without_sid_clears_all():
    """_clear_pending(None) is the process-exit path — every open request is withdrawn, and a response for
    a withdrawn id is dropped quietly (no error frame back to the client)."""
    from tui_gateway import server_requests
    reqs = [_open_request("sid-x"), _open_request("sid-y", "sudo")]
    try:
        server._clear_pending(None)
        assert all(r.event.is_set() and not r.answered for r in reqs)
        assert server.dispatch({"jsonrpc": "2.0", "id": reqs[0].id, "result": {"answer": "late"}}) is None
    finally:
        server_requests.reset_for_tests()


# ---------------------------------------------------------------------------
# /model switch and other agent-mutating commands must reject while the
# session is running.  agent.switch_model() mutates self.model, self.provider,
# self.base_url, self.client etc. in place — the worker thread running
# agent.run_conversation is reading those on every iteration.  So a mid-turn
# config.set model must NOT switch in place; instead it queues the pick
# (session["pending_model_switch"]) and _apply_pending_model_switch applies it
# on the turn thread at the next turn start, where nothing is in flight.
# ---------------------------------------------------------------------------


def test_config_set_model_defers_while_running(monkeypatch):
    """/model via config.set queues the pick during an in-flight turn instead
    of rejecting or racing the worker thread."""
    seen = {"called": False}

    def _fake_apply(sid, session, raw, **_kwargs):
        seen["called"] = True
        return {"value": raw, "warning": ""}

    monkeypatch.setattr(server, "_apply_model_switch", _fake_apply)

    server._sessions["sid"] = _session(running=True)
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "config.set",
                "params": {
                    "session_id": "sid",
                    "key": "model",
                    "value": "anthropic/claude-sonnet-4.6",
                },
            }
        )
        assert not resp.get("error")
        result = resp["result"]
        assert result["deferred"] is True
        assert result["value"] == "anthropic/claude-sonnet-4.6"
        assert not seen["called"], (
            "_apply_model_switch ran mid-turn — would race the worker thread "
            "reading agent.model / agent.client; it must defer to turn start"
        )
        pending = server._sessions["sid"].get("pending_model_switch")
        assert pending and pending["raw"] == "anthropic/claude-sonnet-4.6"
    finally:
        server._sessions.pop("sid", None)


def test_apply_pending_model_switch_runs_queued_pick(monkeypatch):
    """The queued pick is consumed once, on the turn thread, via
    _apply_model_switch — and cleared so it can't re-fire next turn."""
    calls = []

    def _fake_apply(sid, session, raw, **kwargs):
        calls.append(raw)
        return {"value": raw, "warning": "", "confirm_required": False}

    monkeypatch.setattr(server, "_apply_model_switch", _fake_apply)

    session = _session(running=False)
    session["agent"] = object()
    session["pending_model_switch"] = {
        "raw": "anthropic/claude-sonnet-4.6",
        "confirm_expensive_model": False,
    }

    server._apply_pending_model_switch("sid", session)
    assert calls == ["anthropic/claude-sonnet-4.6"]
    assert "pending_model_switch" not in session

    # Idempotent: a second turn start with nothing queued is a no-op.
    server._apply_pending_model_switch("sid", session)
    assert calls == ["anthropic/claude-sonnet-4.6"]


def test_mirror_slash_side_effects_rejects_mutating_commands_while_running(monkeypatch):
    """Slash worker passthrough (e.g. /model, /personality, /prompt,
    /compress) must reject during an in-flight turn.  Same race as
    config.set — mutates live agent state while run_conversation is
    reading it."""
    import types

    applied = {"model": False, "compress": False}

    def _fake_apply_model(sid, session, arg):
        applied["model"] = True
        return {"value": arg, "warning": ""}

    def _fake_compress(session, focus):
        applied["compress"] = True
        return (0, {})

    monkeypatch.setattr(server, "_apply_model_switch", _fake_apply_model)
    monkeypatch.setattr(server, "_compress_session_history", _fake_compress)

    session = _session(running=True)
    session["agent"] = types.SimpleNamespace(model="x")

    for cmd, expected_name in [
        ("/model new/model", "model"),
        ("/personality default", "personality"),
        ("/prompt", "prompt"),
        ("/compress", "compress"),
    ]:
        warning = server._mirror_slash_side_effects("sid", session, cmd)
        assert (
            "session busy" in warning
        ), f"{cmd} should have returned busy warning, got: {warning!r}"
        assert f"/{expected_name}" in warning

    # None of the mutating side-effect helpers should have fired.
    assert not applied["model"], "model switch fired despite running session"
    assert not applied["compress"], "compress fired despite running session"


def test_mirror_slash_side_effects_allowed_when_idle(monkeypatch):
    """Regression guard: idle session still runs the side effects."""
    import types

    applied = {"model": False}

    def _fake_apply_model(sid, session, arg):
        applied["model"] = True
        return {"value": arg, "warning": ""}

    monkeypatch.setattr(server, "_apply_model_switch", _fake_apply_model)

    session = _session(running=False)
    session["agent"] = types.SimpleNamespace(model="x")

    warning = server._mirror_slash_side_effects("sid", session, "/model foo")
    # Should NOT contain "session busy" — the switch went through.
    assert "session busy" not in warning
    assert applied["model"]


def test_mirror_slash_compress_does_not_prelock_history(monkeypatch):
    """Regression guard: /compress side effect must not hold history_lock
    when calling _compress_session_history (the helper snapshots under
    the same non-reentrant lock internally). It also returns a before/after
    summary string (#46686)."""
    import types

    seen = {"compress": False, "sync": False}
    emitted = []

    def _fake_compress(session, focus_topic=None, **_kw):
        seen["compress"] = True
        assert not session["history_lock"].locked()
        # Simulate a real compaction shrinking the transcript.
        session["history"] = [{"role": "user", "content": "summary"}]
        return (1, {"total": 0})

    def _fake_sync(_sid, _session):
        seen["sync"] = True

    monkeypatch.setattr(server, "_compress_session_history", _fake_compress)
    monkeypatch.setattr(server, "_sync_session_key_after_compress", _fake_sync)
    monkeypatch.setattr(server, "_session_info", lambda _agent, *a: {"model": "x"})
    monkeypatch.setattr(server, "_emit", lambda *args: emitted.append(args))

    session = _session(running=False)
    session["history"] = [
        {"role": "user", "content": f"m{i}"} for i in range(6)
    ]
    session["agent"] = types.SimpleNamespace(model="x", _cached_system_prompt="", tools=None)

    warning = server._mirror_slash_side_effects("sid", session, "/compress")

    # Now returns a before/after summary (was "" before #46686).
    assert seen["compress"]
    assert seen["sync"]
    assert ("session.info", "sid", {"model": "x"}) in emitted
    assert warning  # before/after summary returned (#46686)


def test_compress_session_history_here_triggers_partial_compress():
    """/compress here [N] must split history into head/tail and rejoin after
    compression — the partial_compress module is used, not full compress.

    Before this fix, /compress here 3 passed "here 3" as focus_topic to the
    full compress, silently ignoring the boundary intent. The parsing lives
    in _compress_session_history — the choke point every manual-compress
    route (session.compress RPC, command.dispatch, slash-exec mirror)
    converges on — so 'here [N]' works everywhere (#35533).
    """
    compress_context_calls = []
    agent = _partial_compress_agent(compress_context_calls)

    session = _session(agent=agent)
    session["history"] = list(_PARTIAL_FAKE_HISTORY)
    session["history_version"] = 7

    removed, _usage = server._compress_session_history(session, "here 1")

    # agent._compress_context must have been called with the HEAD only
    assert len(compress_context_calls) == 1
    head_passed, focus_passed = compress_context_calls[0]
    assert head_passed == _PARTIAL_FAKE_HISTORY[:-2]
    assert focus_passed is None  # partial compress has no focus topic
    # Session history must now contain the rejoined transcript: compressed
    # head + the last exchange verbatim.
    assert session["history"] == _PARTIAL_COMPRESSED_HEAD + _PARTIAL_FAKE_HISTORY[-2:]
    assert session["history_version"] == 8
    assert removed == len(_PARTIAL_FAKE_HISTORY) - len(session["history"])


def test_compress_session_history_here_falls_back_on_degenerate_split():
    """/compress here with keep_last >= exchanges produces an empty tail —
    must fall back to full compression (whole history, no rejoined tail)."""
    compress_context_calls = []
    agent = _partial_compress_agent(compress_context_calls)

    # 4 messages = 2 exchanges; keep_last=5 leaves nothing to compress.
    short_history = _PARTIAL_FAKE_HISTORY[:4]
    session = _session(agent=agent)
    session["history"] = list(short_history)

    server._compress_session_history(session, "here 5")

    # Degenerate split → full compress of the whole history, focus_topic=None
    assert len(compress_context_calls) == 1
    head_passed, focus_passed = compress_context_calls[0]
    assert head_passed == short_history
    assert focus_passed is None
    assert session["history"] == _PARTIAL_COMPRESSED_HEAD


def test_compress_session_history_plain_focus_topic_not_parsed_as_partial():
    """/compress my topic must still do full compress with focus_topic set."""
    compress_context_calls = []
    agent = _partial_compress_agent(compress_context_calls)

    session = _session(agent=agent)
    session["history"] = list(_PARTIAL_FAKE_HISTORY)

    server._compress_session_history(session, "my topic")

    assert len(compress_context_calls) == 1
    head_passed, focus_passed = compress_context_calls[0]
    assert head_passed == _PARTIAL_FAKE_HISTORY  # full history, no split
    assert focus_passed == "my topic"
    assert session["history"] == _PARTIAL_COMPRESSED_HEAD


def test_session_compress_rpc_honors_here_argument(monkeypatch):
    """Route 1/3: the session.compress RPC must honor 'here [N]'."""
    compress_context_calls = []
    agent = _partial_compress_agent(compress_context_calls)
    session = _session(agent=agent)
    session["history"] = list(_PARTIAL_FAKE_HISTORY)
    server._sessions["sid"] = session

    monkeypatch.setattr(server, "_session_info", lambda *_a, **_kw: {"model": "x"})
    monkeypatch.setattr(server, "_sync_session_key_after_compress", lambda *a, **kw: None)
    monkeypatch.setattr(server, "_emit", lambda *args: None)

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.compress",
                "params": {"session_id": "sid", "focus_topic": "here 1"},
            }
        )
    finally:
        server._sessions.pop("sid", None)

    assert resp["result"]["status"] == "compressed"
    assert len(compress_context_calls) == 1
    head_passed, focus_passed = compress_context_calls[0]
    assert head_passed == _PARTIAL_FAKE_HISTORY[:-2]
    assert focus_passed is None
    assert session["history"] == _PARTIAL_COMPRESSED_HEAD + _PARTIAL_FAKE_HISTORY[-2:]


def test_command_dispatch_compress_honors_here_argument(monkeypatch):
    """Route 2/3: command.dispatch /compress must honor 'here [N]'."""
    compress_context_calls = []
    agent = _partial_compress_agent(compress_context_calls)
    session = _session(agent=agent)
    session["history"] = list(_PARTIAL_FAKE_HISTORY)
    server._sessions["sid"] = session

    monkeypatch.setattr(server, "_session_uses_compute_host", lambda *_a, **_kw: False)
    monkeypatch.setattr(server, "_session_info", lambda *_a, **_kw: {"model": "x"})
    monkeypatch.setattr(server, "_sync_session_key_after_compress", lambda *a, **kw: None)
    monkeypatch.setattr(server, "_emit", lambda *args: None)

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "command.dispatch",
                "params": {"session_id": "sid", "name": "compress", "arg": "here 1"},
            }
        )
    finally:
        server._sessions.pop("sid", None)

    assert resp["result"]["type"] == "exec"
    assert len(compress_context_calls) == 1
    head_passed, focus_passed = compress_context_calls[0]
    assert head_passed == _PARTIAL_FAKE_HISTORY[:-2]
    assert focus_passed is None
    assert session["history"] == _PARTIAL_COMPRESSED_HEAD + _PARTIAL_FAKE_HISTORY[-2:]


def test_mirror_slash_compress_honors_here_argument(monkeypatch):
    """Route 3/3: the slash-exec mirror must honor 'here [N]'."""
    compress_context_calls = []
    agent = _partial_compress_agent(compress_context_calls)
    session = _session(agent=agent)
    session["history"] = list(_PARTIAL_FAKE_HISTORY)

    monkeypatch.setattr(server, "_session_info", lambda *_a, **_kw: {"model": "x"})
    monkeypatch.setattr(server, "_sync_session_key_after_compress", lambda *a, **kw: None)
    monkeypatch.setattr(server, "_emit", lambda *args: None)

    warning = server._mirror_slash_side_effects("sid", session, "/compress here 1")

    assert "Compressed:" in warning
    assert len(compress_context_calls) == 1
    head_passed, focus_passed = compress_context_calls[0]
    assert head_passed == _PARTIAL_FAKE_HISTORY[:-2]
    assert focus_passed is None
    assert session["history"] == _PARTIAL_COMPRESSED_HEAD + _PARTIAL_FAKE_HISTORY[-2:]


# ---------------------------------------------------------------------------
# session.create / session.close race: fast /new churn must not orphan the
# global approval-notify registration. (Slash workers are no longer pre-warmed
# by the build thread — slash.exec spawns them on demand — so the build thread
# must ALSO never construct one here.)
# ---------------------------------------------------------------------------


@pytest.mark.real_agent_prewarm
def test_session_create_close_race_does_not_orphan_worker(monkeypatch):
    """Regression guard: if session.close runs while session.create's
    _build thread is still constructing the agent, the build thread
    must detect the orphan and unregister the notify registration it's
    about to install.  It must also never pre-warm a slash worker (each
    worker forks the full stdio MCP fleet; spawn is on-demand in
    slash.exec) — a worker constructed here would be a regression."""
    import threading

    created_workers: list[str] = []
    closed_workers: list[str] = []
    unregistered_keys: list[str] = []

    class _FakeWorker:
        def __init__(self, key, model, profile_home=None):
            self.key = key
            self._closed = False
            created_workers.append(key)

        def close(self):
            self._closed = True
            closed_workers.append(self.key)

    class _FakeAgent:
        def __init__(self):
            self.model = "x"
            self.provider = "openrouter"
            self.base_url = ""
            self.api_key = ""

    # Make _build block until we release it — simulates slow agent init.
    # Also signal when _build actually reaches _make_agent so the test
    # can close the session at the right moment: session.create now
    # defers _start_agent_build behind a 50ms timer (see the
    # `_deferred_build` path in @method("session.create")), so closing
    # before the build thread has even started would skip the orphan
    # detection entirely and the test would race a non-event.
    build_started = threading.Event()
    release_build = threading.Event()
    build_entered = threading.Event()

    def _slow_make_agent(sid, key, session_id=None, session_db=None, **_kwargs):
        build_started.set()
        build_entered.set()
        release_build.wait(timeout=3.0)
        return _FakeAgent()

    # Stub everything _build touches
    monkeypatch.setattr(server, "_make_agent", _slow_make_agent)
    monkeypatch.setattr(server, "_SlashWorker", _FakeWorker)
    monkeypatch.setattr(
        server,
        "_get_db",
        lambda: types.SimpleNamespace(create_session=lambda *a, **kw: None),
    )
    monkeypatch.setattr(server, "_session_info", lambda _a, *a2: {"model": "x"})
    monkeypatch.setattr(server, "_probe_credentials", lambda _a: None)
    monkeypatch.setattr(server, "_wire_callbacks", lambda _sid: None)
    monkeypatch.setattr(server, "_emit", lambda *a, **kw: None)

    # Shim register/unregister to observe leaks
    import tools.approval as _approval

    monkeypatch.setattr(_approval, "register_gateway_notify", lambda key, cb: None)
    monkeypatch.setattr(
        _approval,
        "unregister_gateway_notify",
        lambda key: unregistered_keys.append(key),
    )
    monkeypatch.setattr(_approval, "load_permanent_allowlist", lambda: None)

    # Start: session.create spawns _build thread, returns synchronously
    resp = server.handle_request(
        {
            "id": "1",
            "method": "session.create",
            "params": {"cols": 80},
        }
    )
    assert resp.get("result"), f"got error: {resp.get('error')}"
    sid = resp["result"]["session_id"]
    own_key = resp["result"]["stored_session_id"]
    assert build_entered.wait(timeout=1.0), "deferred build did not start"

    # Wait until the (deferred) build thread has actually entered
    # _make_agent — otherwise session.close pops _sessions[sid] before
    # _build ever runs, _start_agent_build never calls _build, and we
    # never exercise the orphan-cleanup path.
    assert build_started.wait(timeout=2.0), "build thread never entered _make_agent"

    # Build thread is blocked in _slow_make_agent.  Close the session
    # NOW — this pops _sessions[sid] before _build can install the
    # worker/notify.
    close_resp = server.handle_request(
        {
            "id": "2",
            "method": "session.close",
            "params": {"session_id": sid},
        }
    )
    assert close_resp.get("result", {}).get("closed") is True

    # At this point session.close saw slash_worker=None (never eagerly
    # installed) so it had nothing to close.  Release the build thread
    # and let it finish — it should detect the orphan and unregister
    # the notify, without ever having constructed a worker.
    release_build.set()

    # Give the build thread a moment to run through its finally.
    for _ in range(100):
        if own_key in unregistered_keys:
            break
        import time

        time.sleep(0.02)

    assert created_workers == [], (
        f"build thread pre-warmed a slash worker (spawn must stay on-demand "
        f"in slash.exec) — created_workers={created_workers}"
    )
    # Notify may be unregistered by both session.close (unconditional)
    # and the orphan-cleanup path; the key guarantee is that THIS session's
    # key gets unregistered (any prior close already popped the callback; the
    # duplicate is a no-op). Match on our own key, not the global count: the
    # registry is process-wide and a leaked _build thread from another
    # session.create test can append a foreign key here and falsely satisfy
    # a bare `>= 1`.
    assert own_key in unregistered_keys, (
        f"orphan notify registration was not unregistered — "
        f"{own_key} not in unregistered_keys={unregistered_keys}"
    )


@pytest.mark.real_agent_prewarm
def test_session_create_no_race_keeps_worker_alive(monkeypatch):
    """Regression guard: when session.close does NOT race, the build
    thread must install the notify normally and leave it alone (no
    over-eager cleanup) — and must not pre-warm a slash worker (spawn
    is on-demand in slash.exec)."""
    closed_workers: list[str] = []
    unregistered_keys: list[str] = []

    class _FakeWorker:
        def __init__(self, key, model, profile_home=None):
            self.key = key

        def close(self):
            closed_workers.append(self.key)

    class _FakeAgent:
        def __init__(self):
            self.model = "x"
            self.provider = "openrouter"
            self.base_url = ""
            self.api_key = ""

    monkeypatch.setattr(server, "_make_agent", lambda sid, key, session_db=None, **_kwargs: _FakeAgent())
    monkeypatch.setattr(server, "_SlashWorker", _FakeWorker)
    monkeypatch.setattr(
        server,
        "_get_db",
        lambda: types.SimpleNamespace(create_session=lambda *a, **kw: None),
    )
    monkeypatch.setattr(server, "_session_info", lambda _a, *a2: {"model": "x"})
    monkeypatch.setattr(server, "_probe_credentials", lambda _a: None)
    monkeypatch.setattr(server, "_wire_callbacks", lambda _sid: None)
    monkeypatch.setattr(server, "_emit", lambda *a, **kw: None)

    import tools.approval as _approval

    monkeypatch.setattr(_approval, "register_gateway_notify", lambda key, cb: None)
    monkeypatch.setattr(
        _approval,
        "unregister_gateway_notify",
        lambda key: unregistered_keys.append(key),
    )
    monkeypatch.setattr(_approval, "load_permanent_allowlist", lambda: None)

    # Isolate from sibling-test leakage: daemon build threads from prior
    # session.create tests in the same shard process mutate the shared
    # ``server._sessions`` dict under ``_sessions_lock`` and can replace/pop
    # entries mid-run, which would flip this build thread's ``replaced`` check
    # to True and trigger a spurious unregister. Snapshot, clear, and restore
    # so this test sees only its own session regardless of shard composition.
    _saved_sessions = dict(server._sessions)
    server._sessions.clear()

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.create",
                "params": {"cols": 80},
            }
        )
        sid = resp["result"]["session_id"]

        # Wait for the build to finish (ready event inside session dict).
        session = server._sessions[sid]
        built = session["agent_ready"].wait(timeout=10.0)
        assert built, "agent build did not complete within timeout"

        # Build finished without a close race — nothing should have been
        # cleaned up by the orphan check.  Scope the assertions to THIS
        # test's own session_key: a daemon build thread leaked from a prior
        # session.create test in the same shard process can fire close/
        # unregister against its own (foreign) key after we've patched the
        # global hooks, polluting these lists.  Filtering by this session's
        # key keeps the regression intent (this session's worker/notify must
        # survive) while making the test immune to shard composition.
        # (flaky under -j 8: foreign key e.g. 20260629_210208_d4f545)
        own_key = session["session_key"]
        own_closed = [k for k in closed_workers if k == own_key]
        own_unregistered = [k for k in unregistered_keys if k == own_key]
        assert (
            own_closed == []
        ), f"build thread closed its own worker despite no race: {own_closed}"
        assert (
            own_unregistered == []
        ), f"build thread unregistered its own notify despite no race: {own_unregistered}"

        # No pre-warmed worker: slash.exec spawns on demand, so a fresh
        # session that hasn't run a worker-routed command carries None.
        assert session.get("slash_worker") is None
    finally:
        # Cleanup + restore sibling sessions we snapshotted.
        server._sessions.clear()
        server._sessions.update(_saved_sessions)


def test_get_db_degrades_cleanly_when_sessiondb_init_fails(monkeypatch):
    fake_mod = types.ModuleType("hermes_state")

    class _BrokenSessionDB:
        def __init__(self):
            raise RuntimeError("locking protocol")

    fake_mod.SessionDB = _BrokenSessionDB

    def _broken_shared(_db_path=None):
        raise RuntimeError("locking protocol")

    monkeypatch.setitem(sys.modules, "hermes_state", fake_mod)
    fake_registry = types.ModuleType("hermes_state_registry")
    fake_registry.acquire = _broken_shared
    monkeypatch.setitem(sys.modules, "hermes_state_registry", fake_registry)
    monkeypatch.setattr(server, "_db", None)
    monkeypatch.setattr(server, "_db_error", None)

    assert server._get_db() is None
    assert server._db_error == "locking protocol"


def test_ensure_session_db_row_false_when_store_unavailable(monkeypatch):
    """Store unavailable → False, so prompt.submit can fail the send loudly
    instead of streaming into a store that will never save it (#98924)."""
    fake_mod = types.ModuleType("hermes_state")

    class _BrokenSessionDB:
        def __init__(self):
            raise RuntimeError("utf-8 boom")

    fake_mod.SessionDB = _BrokenSessionDB

    def _broken_shared(_db_path=None):
        raise RuntimeError("utf-8 boom")

    monkeypatch.setitem(sys.modules, "hermes_state", fake_mod)
    fake_registry = types.ModuleType("hermes_state_registry")
    fake_registry.acquire = _broken_shared
    monkeypatch.setitem(sys.modules, "hermes_state_registry", fake_registry)
    monkeypatch.setattr(server, "_db", None)
    monkeypatch.setattr(server, "_db_error", None)

    assert server._ensure_session_db_row({"session_key": "k1"}) is False


def test_ensure_session_db_row_true_when_row_persisted(monkeypatch):
    created = []

    class _FakeDB:
        def create_session(self, key, **_kwargs):
            created.append(key)

    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    monkeypatch.setattr(server, "_resolve_model", lambda: "test-model")

    assert server._ensure_session_db_row({"session_key": "k1", "cwd": "/tmp"}) is True
    assert created == ["k1"]


def test_prompt_submit_fails_loudly_when_store_unavailable(monkeypatch):
    """A send with no persistable store must fail the RPC with a real error
    (desktop maps it to a toast) instead of streaming the message into a
    store that will never save it (#98924)."""
    monkeypatch.setattr(server, "_load_cfg", lambda: {"dashboard": {}})
    monkeypatch.setattr(server, "_get_db", lambda: None)
    monkeypatch.setattr(server, "_db_error", "utf-8 decode failure")

    server._sessions["lost-sid"] = _session()
    try:
        resp = server.handle_request(
            {
                "id": "lost",
                "method": "prompt.submit",
                "params": {"session_id": "lost-sid", "text": "will vanish"},
            }
        )
    finally:
        server._sessions.pop("lost-sid", None)

    assert resp["error"]["code"] == 5072
    msg = resp["error"]["message"]
    assert "utf-8 decode failure" not in msg  # raw cause rides `data.details`, never the lead
    assert resp["error"]["data"]["code"] == "storage_unavailable"
    assert "utf-8 decode failure" in resp["error"]["data"]["details"]


@pytest.mark.real_agent_prewarm
def test_session_create_continues_when_state_db_is_unavailable(monkeypatch):
    class _FakeWorker:
        def __init__(self, key, model, profile_home=None):
            self.key = key

        def close(self):
            return None

    class _FakeAgent:
        def __init__(self):
            self.model = "x"
            self.provider = "openrouter"
            self.base_url = ""
            self.api_key = ""

    emits = []

    monkeypatch.setattr(server, "_make_agent", lambda sid, key, session_db=None, **_kwargs: _FakeAgent())
    monkeypatch.setattr(server, "_SlashWorker", _FakeWorker)
    monkeypatch.setattr(server, "_get_db", lambda: None)
    monkeypatch.setattr(server, "_session_info", lambda _a, *a2: {"model": "x"})
    monkeypatch.setattr(server, "_probe_credentials", lambda _a: None)
    monkeypatch.setattr(server, "_wire_callbacks", lambda _sid: None)
    monkeypatch.setattr(server, "_emit", lambda *a, **kw: emits.append(a))

    import tools.approval as _approval

    monkeypatch.setattr(_approval, "register_gateway_notify", lambda key, cb: None)
    monkeypatch.setattr(_approval, "load_permanent_allowlist", lambda: None)

    resp = server.handle_request(
        {"id": "1", "method": "session.create", "params": {"cols": 80}}
    )
    sid = resp["result"]["session_id"]
    session = server._sessions[sid]
    session["agent_ready"].wait(timeout=2.0)

    assert session["agent_error"] is None
    assert session["agent"] is not None
    assert not any(args and args[0] == "error" for args in emits)

    server._sessions.pop(sid, None)


def test_session_create_lazy_info_reports_desktop_contract(monkeypatch):
    """The lazy session.create info payload must carry desktop_contract, else
    the desktop GUI reads it as undefined and falsely warns "Backend out of
    date" on every launch even against a current backend."""

    class _FakeWorker:
        def __init__(self, key, model, profile_home=None):
            self.key = key

        def close(self):
            return None

    monkeypatch.setattr(server, "_SlashWorker", _FakeWorker)
    monkeypatch.setattr(server, "_get_db", lambda: None)
    monkeypatch.setattr(server, "_emit", lambda *a, **kw: None)
    monkeypatch.setattr(server, "_start_agent_build", lambda *a, **kw: None)

    resp = server.handle_request(
        {"id": "1", "method": "session.create", "params": {"cols": 80}}
    )
    info = resp["result"]["info"]

    assert info["desktop_contract"] == server.DESKTOP_BACKEND_CONTRACT

    server._sessions.pop(resp["result"]["session_id"], None)


def test_session_activate_lazy_info_reports_desktop_contract():
    """Activating an already-live *lazy* session (agent not built yet) must
    still advertise desktop_contract. _live_session_payload falls back to
    _fallback_session_info while session["agent"] is None; the desktop reads a
    missing field as contract 0 and falsely warns "Backend out of date" against
    a current backend (#68392). The sibling session.create path was fixed in
    #36112; this pins the session.activate path."""
    import threading

    sid = "lazy-activate-contract"
    server._sessions[sid] = {
        "agent": None,
        "created_at": 123.0,
        "history": [],
        "history_lock": threading.RLock(),
        "last_active": 123.0,
        "running": False,
        "session_key": sid,
        "transport": server._stdio_transport,
    }
    try:
        resp = server.handle_request(
            {
                "id": "activate-lazy",
                "method": "session.activate",
                "params": {"session_id": sid},
            }
        )
        info = resp["result"]["info"]
        assert info["lazy"] is True
        assert info["desktop_contract"] == server.DESKTOP_BACKEND_CONTRACT
    finally:
        server._sessions.pop(sid, None)


def test_session_list_returns_clean_error_when_state_db_is_unavailable(monkeypatch):
    monkeypatch.setattr(server, "_get_db", lambda: None)
    monkeypatch.setattr(server, "_db_error", "locking protocol")

    resp = server.handle_request({"id": "1", "method": "session.list", "params": {}})

    assert "error" in resp
    assert resp["error"]["data"]["code"] == "storage_unavailable"
    assert resp["error"]["data"]["details"] == "locking protocol"


# --------------------------------------------------------------------------
# session.delete — TUI resume picker `d` key
# --------------------------------------------------------------------------


def test_session_delete_requires_session_id(monkeypatch):
    """Empty / missing session_id is a 4006 client error (no DB call)."""
    called: list[tuple] = []

    class _DB:
        def delete_session(self, *a, **kw):
            called.append((a, kw))
            return True

    monkeypatch.setattr(server, "_get_db", lambda: _DB())

    resp = server.handle_request({"id": "1", "method": "session.delete", "params": {}})
    assert "error" in resp
    assert resp["error"]["code"] == 4006
    assert called == []


def test_session_delete_returns_db_unavailable_when_no_db(monkeypatch):
    monkeypatch.setattr(server, "_get_db", lambda: None)
    monkeypatch.setattr(server, "_db_error", "locked")

    resp = server.handle_request(
        {"id": "1", "method": "session.delete", "params": {"session_id": "abc"}}
    )

    assert "error" in resp
    assert resp["error"]["code"] == 5036
    assert resp["error"]["data"]["code"] == "storage_locked"


def test_session_delete_refuses_active_session(monkeypatch):
    """Cannot delete a session currently bound to a live TUI session."""
    called: list[str] = []

    class _DB:
        def delete_session(self, sid, sessions_dir=None, **_kw):
            called.append(sid)
            return True

    monkeypatch.setattr(server, "_get_db", lambda: _DB())
    monkeypatch.setitem(server._sessions, "live", {"session_key": "key-live"})
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.delete",
                "params": {"session_id": "key-live"},
            }
        )
    finally:
        server._sessions.pop("live", None)

    assert "error" in resp
    assert resp["error"]["code"] == 4023
    assert called == [], "delete_session must not be called for active sessions"


def test_session_delete_fails_closed_when_active_snapshot_raises(monkeypatch):
    """Concurrent ``_sessions`` mutation from another RPC thread can raise
    ``RuntimeError: dictionary changed size during iteration``.  When the
    handler can't enumerate active sessions safely it must refuse the
    delete (fail closed) rather than fall through and allow it."""

    class _DB:
        def delete_session(self, *a, **kw):
            raise AssertionError("delete must not run when active snapshot fails")

    class _ExplodingDict:
        def values(self):
            raise RuntimeError("dictionary changed size during iteration")

    monkeypatch.setattr(server, "_get_db", lambda: _DB())
    monkeypatch.setattr(server, "_sessions", _ExplodingDict())

    resp = server.handle_request(
        {"id": "1", "method": "session.delete", "params": {"session_id": "x"}}
    )

    assert "error" in resp
    assert resp["error"]["code"] == 5036


def test_session_delete_returns_4007_when_missing(monkeypatch):
    class _DB:
        def delete_session(self, sid, sessions_dir=None, **_kw):
            return False

    monkeypatch.setattr(server, "_get_db", lambda: _DB())

    resp = server.handle_request(
        {"id": "1", "method": "session.delete", "params": {"session_id": "ghost"}}
    )

    assert "error" in resp
    assert resp["error"]["code"] == 4007


def test_session_delete_propagates_db_exception(monkeypatch):
    class _DB:
        def delete_session(self, sid, sessions_dir=None, **_kw):
            raise RuntimeError("disk full")

    monkeypatch.setattr(server, "_get_db", lambda: _DB())

    resp = server.handle_request(
        {"id": "1", "method": "session.delete", "params": {"session_id": "x"}}
    )

    assert "error" in resp
    assert resp["error"]["code"] == 5036
    assert "disk full" in resp["error"]["message"]


def test_session_delete_success_returns_deleted_id(monkeypatch):
    """Happy path — DB delete succeeds, response carries the deleted id
    and the on-disk sessions dir is forwarded so transcript files get
    cleaned up alongside the row."""
    captured: dict = {}

    class _DB:
        def delete_session(self, sid, sessions_dir=None, **_kw):
            captured["sid"] = sid
            captured["sessions_dir"] = sessions_dir
            return True

    monkeypatch.setattr(server, "_get_db", lambda: _DB())

    resp = server.handle_request(
        {"id": "1", "method": "session.delete", "params": {"session_id": "old-1"}}
    )

    assert "result" in resp, resp
    assert resp["result"] == {"deleted": "old-1"}
    assert captured["sid"] == "old-1"
    # sessions_dir must be forwarded so transcript files get cleaned up
    # too — not just the SQLite row.  The autouse _isolate_hermes_home
    # fixture pins HERMES_HOME to a temp dir; the handler should append
    # /sessions to it.
    assert captured["sessions_dir"] is not None
    assert str(captured["sessions_dir"]).endswith("sessions")


# --------------------------------------------------------------------------
# session.* profile scoping (app-global remote mode) — #62503
# --------------------------------------------------------------------------


def test_session_list_honors_params_profile_opens_profile_db(monkeypatch, tmp_path):
    """Issue #62503: session.list must read the profile's state.db, not launch."""
    profile_home = tmp_path / "profiles" / "mlperf"
    profile_home.mkdir(parents=True)
    (profile_home / "state.db").write_bytes(b"")
    seen: dict = {}

    class LaunchDB:
        def list_sessions_rich(self, **kwargs):
            seen["launch"] = True
            return [{"id": "launch-1", "source": "tui", "title": "L"}]

    class ProfileDB:
        def __init__(self, db_path=None):
            seen["db_path"] = db_path

        def list_sessions_rich(self, **kwargs):
            seen["profile"] = True
            return [
                {
                    "id": "ml-1",
                    "source": "tui",
                    "title": "M",
                    "preview": "",
                    "started_at": 1,
                    "message_count": 1,
                }
            ]

        def close(self):
            seen["closed"] = True

    monkeypatch.setattr(server, "_profile_home", lambda p: profile_home if p == "mlperf" else None)
    monkeypatch.setattr(server, "_get_db", lambda: LaunchDB())
    monkeypatch.setattr(
        "hermes_cli.web_server_sessions._open_session_db_at_path",
        lambda db_path, *, read_only: ProfileDB(db_path=db_path),
    )

    resp = server.handle_request(
        {
            "id": "1",
            "method": "session.list",
            "params": {"profile": "mlperf", "limit": 5},
        }
    )
    assert "result" in resp, resp
    assert resp["result"]["sessions"][0]["id"] == "ml-1"
    assert seen.get("profile") is True
    assert seen.get("launch") is None
    assert str(seen.get("db_path")).endswith("state.db")
    assert seen.get("closed") is True


def test_session_most_recent_honors_params_profile(monkeypatch, tmp_path):
    """Issue #62503: session.most_recent must not return the launch profile tip."""
    profile_home = tmp_path / "profiles" / "mlperf"
    profile_home.mkdir(parents=True)

    class LaunchDB:
        def list_sessions_rich(self, **kwargs):
            return [{"id": "launch-tip", "source": "tui", "title": "L", "started_at": 9}]

    class ProfileDB2:
        def __init__(self, db_path=None):
            self.db_path = db_path

        def list_sessions_rich(self, **kwargs):
            return [
                {"id": "tool-noise", "source": "tool", "title": "t", "started_at": 9},
                {"id": "ml-tip", "source": "desktop", "title": "M", "started_at": 3},
            ]

        def close(self):
            pass

    monkeypatch.setattr(server, "_profile_home", lambda p: profile_home if p == "mlperf" else None)
    monkeypatch.setattr(server, "_get_db", lambda: LaunchDB())
    monkeypatch.setattr(
        "hermes_cli.web_server_sessions._open_session_db_at_path",
        lambda db_path, *, read_only: ProfileDB2(db_path=db_path),
    )

    resp = server.handle_request(
        {
            "id": "1",
            "method": "session.most_recent",
            "params": {"profile": "mlperf"},
        }
    )
    assert resp["result"]["session_id"] == "ml-tip"


def test_handoff_request_uses_session_profile_home(monkeypatch, tmp_path):
    """Handoff validation must read the owning session's gateway config."""
    import contextlib

    from gateway.config import GatewayConfig, HomeChannel, Platform, PlatformConfig
    from hermes_cli.config import get_hermes_home
    from tui_gateway import methods_session

    methods_session.register(server)
    profile_home = tmp_path / "profiles" / "coder"
    profile_home.mkdir(parents=True)
    seen_homes = []

    def load_config():
        home = get_hermes_home()
        seen_homes.append(home)
        config = GatewayConfig()
        if home == profile_home:
            config.platforms[Platform.DISCORD] = PlatformConfig(
                enabled=True,
                home_channel=HomeChannel(
                    platform=Platform.DISCORD,
                    chat_id="discord-home",
                    name="Hermes / #chat-coding",
                ),
            )
        return config

    class ProfileDB:
        def get_session(self, _key):
            return {"id": _key}

        def request_handoff(self, _key, platform):
            return platform == "discord"

    @contextlib.contextmanager
    def profile_db(_session):
        yield ProfileDB()

    monkeypatch.setattr("gateway.config.load_gateway_config", load_config)
    monkeypatch.setattr(server, "_ensure_session_db_row", lambda _session: None)
    monkeypatch.setattr(server, "_session_db", profile_db)
    server._sessions["handoff-profile"] = {
        "running": False,
        "session_key": "desktop-coder-session",
        "profile_home": str(profile_home),
    }
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "handoff.request",
                "params": {
                    "session_id": "handoff-profile",
                    "platform": "discord",
                },
            }
        )
    finally:
        server._sessions.pop("handoff-profile", None)

    assert "result" in resp, resp
    assert resp["result"]["queued"] is True
    assert seen_homes == [profile_home]
    assert get_hermes_home() != profile_home


def test_session_create_reports_requested_profile_name(monkeypatch, tmp_path):
    """Issue #62503: session.create info.profile_name must not always be launch."""
    profile_home = tmp_path / "profiles" / "mlperf"
    profile_home.mkdir(parents=True)

    def _clear():
        for session in list(server._sessions.values()):
            server._teardown_session(session)
        server._sessions.clear()

    monkeypatch.setattr(server, "_start_agent_build", lambda *a, **k: None)
    monkeypatch.setattr(server, "_schedule_agent_build", lambda *a, **k: None)
    monkeypatch.setattr(server, "_schedule_session_cap_enforcement", lambda *a, **k: None)
    monkeypatch.setattr(server, "_completion_cwd", lambda params=None: str(tmp_path))
    monkeypatch.setattr(server, "_profile_home", lambda p: profile_home if p == "mlperf" else None)
    monkeypatch.setattr(server, "_current_profile_name", lambda: "default")
    monkeypatch.setattr(server, "_claim_active_session_slot", lambda *a, **k: (None, None))
    _clear()
    try:
        resp = server._methods["session.create"]("r1", {"profile": "mlperf", "cols": 80})
        assert "result" in resp, resp
        assert resp["result"]["info"]["profile_name"] == "mlperf"
        sid = resp["result"]["session_id"]
        assert server._sessions[sid]["profile_home"] == str(profile_home)
    finally:
        _clear()


def test_session_delete_honors_params_profile_sessions_dir(monkeypatch, tmp_path):
    """Issue #62503: delete must target the profile state.db + sessions dir."""
    profile_home = tmp_path / "profiles" / "mlperf"
    (profile_home / "sessions").mkdir(parents=True)
    captured: dict = {}

    class ProfileDB:
        def __init__(self, db_path=None):
            captured["db_path"] = db_path

        def delete_session(self, sid, sessions_dir=None, **_kw):
            captured["sid"] = sid
            captured["sessions_dir"] = sessions_dir
            return True

        def close(self):
            captured["closed"] = True

    monkeypatch.setattr(server, "_profile_home", lambda p: profile_home if p == "mlperf" else None)
    monkeypatch.setattr(server, "_get_db", lambda: None)
    monkeypatch.setattr("hermes_state_registry.acquire", ProfileDB)

    resp = server.handle_request(
        {
            "id": "1",
            "method": "session.delete",
            "params": {"session_id": "old-ml", "profile": "mlperf"},
        }
    )
    assert "result" in resp, resp
    assert resp["result"] == {"deleted": "old-ml"}
    assert str(captured["db_path"]).endswith("state.db")
    assert Path(captured["sessions_dir"]) == profile_home / "sessions"
    assert captured.get("closed") is True


def test_session_title_uses_session_profile_db_not_launch(monkeypatch, tmp_path):
    """session.title on a non-launch profile session must not touch launch DB."""
    profile_home = tmp_path / "profiles" / "mlperf"
    profile_home.mkdir(parents=True)
    seen: dict = {}

    class LaunchDB:
        def get_session_title(self, _key):
            seen["launch_read"] = True
            return "from-launch"

        def set_session_title(self, _key, _title):
            seen["launch_write"] = True
            return True

        def get_session(self, _key):
            return {"id": _key, "title": "from-launch"}

    class ProfileDB:
        def __init__(self, db_path=None):
            self.db_path = db_path
            seen["db_path"] = db_path

        def get_session_title(self, _key):
            return seen.get("title")

        def get_session(self, _key):
            if "title" in seen:
                return {"id": _key, "title": seen["title"]}
            return None

        def set_session_title(self, _key, title):
            seen["title"] = title
            seen["profile_write"] = True
            return True

        def close(self):
            seen["closed"] = True

    server._sessions["sid"] = {
        "session_key": "ml-sess",
        "history": [],
        "history_lock": __import__("threading").Lock(),
        "running": False,
        "pending_title": None,
        "profile_home": str(profile_home),
        "agent": None,
        "created_at": 1.0,
        "last_active": 1.0,
    }
    monkeypatch.setattr(server, "_get_db", lambda: LaunchDB())
    monkeypatch.setattr("hermes_state_registry.acquire", ProfileDB)
    try:
        set_resp = server.handle_request(
            {
                "id": "1",
                "method": "session.title",
                "params": {"session_id": "sid", "title": "profile-title"},
            }
        )
        assert "result" in set_resp, set_resp
        assert set_resp["result"]["title"] == "profile-title"
        assert seen.get("profile_write") is True
        assert seen.get("launch_write") is None
        assert str(seen.get("db_path")).endswith("state.db")

        get_resp = server.handle_request(
            {"id": "2", "method": "session.title", "params": {"session_id": "sid"}}
        )
        assert get_resp["result"]["title"] == "profile-title"
        assert seen.get("launch_read") is None
    finally:
        server._sessions.pop("sid", None)


def test_session_history_uses_session_profile_db(monkeypatch, tmp_path):
    """session.history must read durable messages from the profile state.db."""
    profile_home = tmp_path / "profiles" / "mlperf"
    profile_home.mkdir(parents=True)
    seen: dict = {}

    class LaunchDB:
        def get_messages_as_conversation(self, _key, include_ancestors=True, **_kwargs):
            seen["launch"] = True
            return [{"role": "user", "content": "launch"}]

    class ProfileDB:
        def __init__(self, db_path=None):
            seen["db_path"] = db_path

        def get_messages_as_conversation(self, _key, include_ancestors=True, **_kwargs):
            seen["profile"] = True
            return [{"role": "user", "content": "from-profile"}]

        def close(self):
            seen["closed"] = True

    server._sessions["sid"] = {
        "session_key": "ml-sess",
        "history": [{"role": "user", "content": "mem"}],
        "history_lock": __import__("threading").Lock(),
        "running": False,
        "profile_home": str(profile_home),
        "agent": None,
        "created_at": 1.0,
        "last_active": 1.0,
    }
    monkeypatch.setattr(server, "_get_db", lambda: LaunchDB())
    monkeypatch.setattr("hermes_state_registry.acquire", ProfileDB)
    try:
        resp = server.handle_request(
            {"id": "1", "method": "session.history", "params": {"session_id": "sid"}}
        )
        assert "result" in resp, resp
        assert seen.get("profile") is True
        assert seen.get("launch") is None
        # Count comes from profile-backed conversation (1 msg), not bare mem list alone.
        assert resp["result"]["count"] == 1
    finally:
        server._sessions.pop("sid", None)
