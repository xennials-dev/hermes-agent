"""tui_gateway.server — truncation targeting and notification event routing.

Split from test_tui_gateway_server.py; shared fixtures and helpers live
in tests/tui_gateway/_server_test_helpers.py.
"""

import contextlib
import threading
import types
import pytest
from tools import async_delegation as ad
from tui_gateway import server

from tests.tui_gateway._server_test_helpers import (
    _dispatch_sync,
    _neuter_agent_prewarm_timer,  # autouse
    _reap_leaked_notification_pollers,  # autouse
    _session,
)


def test_superseded_runtime_finalized_without_reclaimed_broadcast(monkeypatch):
    """When a resume mints a fresh runtime for a stored id whose prior runtime
    is sentinel-parked, the old record is finalized quietly with end_reason
    superseded_by_resume — no session.reclaimed broadcast, and its pending
    reap Timer is cancelled (storm killer, part 2)."""
    cancelled = []
    broadcasts = []
    torn_down = []

    class _Timer:
        def __init__(self, _delay, fn):
            self.fn = fn

        def start(self):
            return None

        def cancel(self):
            cancelled.append(self)

    monkeypatch.setattr(server, "_WS_ORPHAN_REAP_GRACE_S", 0.01)
    monkeypatch.setattr(server.threading, "Timer", _Timer)
    monkeypatch.setattr(
        server,
        "_broadcast_global_event",
        lambda event, payload=None: broadcasts.append((event, payload)),
    )
    monkeypatch.setattr(
        server,
        "_teardown_popped_session",
        lambda popped, *, end_reason: torn_down.append((popped, end_reason)) or True,
    )
    monkeypatch.setattr(server, "_register_session_cwd", lambda _s: None)

    old_agent = types.SimpleNamespace(session_id="stored-super")
    old = _session(
        agent=old_agent,
        session_key="stored-super",
        transport=server._detached_ws_transport,
        running=False,
    )
    server._sessions["old-sid"] = old
    fresh = _session(session_key="stored-super")

    try:
        server._schedule_ws_orphan_reap("old-sid")
        assert "old-sid" in server._pending_ws_reaps

        # The old runtime looks live to _find_live_session_by_key, so make it
        # invisible the way a real mint path would (its client is gone and the
        # resume slow path only mints after the fast path found no live match:
        # mark it finalized-for-lookup via a different stored key is wrong —
        # instead simulate the mint race by removing it from lookup).
        old["_finalized"] = False
        monkeypatch.setattr(server, "_find_live_session_by_key", lambda _k, *_a: None)

        result = server._claim_or_reuse_live("new-sid", "stored-super", fresh, None)

        assert result is None
        assert server._sessions.get("new-sid") is fresh
        assert "old-sid" not in server._sessions
        assert "old-sid" not in server._pending_ws_reaps
        assert len(cancelled) == 1
        assert torn_down == [(old, "superseded_by_resume")]
        assert broadcasts == []  # no session.reclaimed storm
    finally:
        server._sessions.pop("old-sid", None)
        server._sessions.pop("new-sid", None)
        server._pending_ws_reaps.pop("old-sid", None)
        server._pending_ws_reaps.pop("new-sid", None)


def test_lazy_unpersisted_resume_rebinds_transport_and_cancels_reap(monkeypatch):
    """The lazy/unpersisted resume branch (no state.db row yet — every fresh
    Bot Chat) must ALSO rebind the transport and cancel the pending reap when
    it hands back a sentinel-parked live record. Found by live WS E2E after
    the #93361 merge: the unit-covered paths (_live_session_payload,
    _reuse_live_response, _claim_or_reuse_live) all cancelled, but this branch
    returned the record while leaving it on the drop sentinel with the reap
    Timer armed — the storm survived for unpersisted sessions (storm killer,
    part 3)."""
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

    live_transport = _LiveTransport()
    monkeypatch.setattr(server, "_WS_ORPHAN_REAP_GRACE_S", 0.01)
    monkeypatch.setattr(server.threading, "Timer", _Timer)
    monkeypatch.setattr(server, "current_transport", lambda: live_transport)
    # get_session/get_session_by_title miss -> forces the unpersisted branch
    monkeypatch.setattr(
        server,
        "_get_db",
        lambda: types.SimpleNamespace(
            get_session=lambda _t: None,
            get_session_by_title=lambda _t: None,
        ),
    )

    session = _session(
        session_key="stored-lazy",
        transport=server._detached_ws_transport,
        running=False,
        history=[],
        profile_home=None,
    )
    server._sessions["lazy-sid"] = session

    try:
        server._schedule_ws_orphan_reap("lazy-sid")
        assert "lazy-sid" in server._pending_ws_reaps

        resp = _dispatch_sync(
            {
                "id": "lz1",
                "method": "session.resume",
                "params": {"session_id": "stored-lazy", "omit_messages": True},
            },
            transport=live_transport,
        )

        assert resp is not None and resp["result"]["session_id"] == "lazy-sid"
        assert session["transport"] is live_transport
        assert "lazy-sid" not in server._pending_ws_reaps
        assert len(cancelled) == 1
    finally:
        server._sessions.pop("lazy-sid", None)
        server._pending_ws_reaps.pop("lazy-sid", None)


def test_ws_orphan_reap_still_fires_when_never_resumed(monkeypatch):
    """Nobody re-resumes: the reap fires normally and unregisters its Timer."""
    callbacks = []
    torn_down = []

    class _Timer:
        def __init__(self, _delay, fn):
            callbacks.append(fn)

        def start(self):
            return None

        def cancel(self):
            return None

    monkeypatch.setattr(server, "_WS_ORPHAN_REAP_GRACE_S", 0.01)
    monkeypatch.setattr(server.threading, "Timer", _Timer)
    monkeypatch.setattr(
        server,
        "_teardown_popped_session",
        lambda popped, *, end_reason: torn_down.append((popped, end_reason)) or True,
    )
    session = _session(transport=server._detached_ws_transport, running=False)
    server._sessions["lonely-sid"] = session

    try:
        server._schedule_ws_orphan_reap("lonely-sid")
        assert "lonely-sid" in server._pending_ws_reaps
        callbacks.pop(0)()

        assert "lonely-sid" not in server._sessions
        assert "lonely-sid" not in server._pending_ws_reaps
        assert torn_down == [(session, "ws_orphan_reap")]
    finally:
        server._sessions.pop("lonely-sid", None)
        server._pending_ws_reaps.pop("lonely-sid", None)


def test_ws_orphan_reap_spares_detached_session_with_running_async_delegation(monkeypatch):
    """A detached desktop session with live background delegation is parked.

    Regression for Desktop session switches / transient WS detaches: the parent
    turn is idle, but a background delegate_task still owns the session's
    return address. Reaping immediately interrupts the child and turns its
    completion into an unowned orphan.
    """
    timers = []
    closed = []

    class _Timer:
        def __init__(self, _delay, fn):
            self.fn = fn
            timers.append(self)

        def start(self):
            return None

    class _DB:
        def get_session(self, _session_id):
            return {"id": "sess_bg", "source": "desktop"}

    monkeypatch.setattr(server, "_WS_ORPHAN_REAP_GRACE_S", 0.01)
    monkeypatch.setattr(server.threading, "Timer", _Timer)
    monkeypatch.setattr(server, "_get_db", lambda: _DB())
    monkeypatch.setattr(
        server,
        "_teardown_popped_session",
        lambda session, *, end_reason="tui_close": (
            closed.append((session["_sid"], end_reason)) if session is not None else None
        ),
    )

    server._sessions["bg-sid"] = _session(
        transport=server._detached_ws_transport,
        running=False,
        session_key="sess_bg",
    )
    ad._reset_for_tests()
    try:
        with ad._records_lock:
            ad._records["deleg_bg"] = {
                "delegation_id": "deleg_bg",
                "status": "running",
                "session_key": "sess_bg",
                "origin_ui_session_id": "bg-sid",
                "interrupt_fn": lambda: None,
            }

        server._schedule_ws_orphan_reap("bg-sid")
        assert len(timers) == 1

        timers.pop(0).fn()

        assert closed == []
        assert "bg-sid" in server._sessions
        assert len(timers) == 1

        with ad._records_lock:
            ad._records["deleg_bg"]["status"] = "finalizing"
            ad._records["deleg_bg"]["interrupt_fn"] = None

        timers.pop(0).fn()

        assert closed == []
        assert "bg-sid" in server._sessions
        assert len(timers) == 1

        with ad._records_lock:
            ad._records["deleg_bg"]["status"] = "completed"

        timers.pop(0).fn()

        assert closed == [("bg-sid", "ws_orphan_reap")]
    finally:
        ad._reset_for_tests()
        server._sessions.pop("bg-sid", None)


def test_ws_orphan_reap_disabled_when_grace_zero(monkeypatch):
    """Grace=0 disables the reaper entirely (pre-fix park-forever behaviour)."""
    fired = {"timer": False}

    class _Timer:
        def __init__(self, *a, **k):
            fired["timer"] = True

        def start(self):
            pass

    monkeypatch.setattr(server, "_WS_ORPHAN_REAP_GRACE_S", 0.0)
    monkeypatch.setattr(server.threading, "Timer", _Timer)
    server._schedule_ws_orphan_reap("any-sid")
    assert fired["timer"] is False


def test_ws_orphan_reap_defers_running_turn_with_fresh_activity(monkeypatch):
    """#98028/#100325: a client-absent turn whose activity clock is fresh is
    NOT interrupted — it keeps running detached and the reaper re-polls at the
    grace interval. Once the clock goes stale the wedged-turn interrupt fires,
    and after the turn settles the session is reaped as before."""
    callbacks = []
    delays = []
    interrupted = []
    torn_down = []

    class _Timer:
        def __init__(self, delay, callback):
            delays.append(delay)
            callbacks.append(callback)
            self.daemon = False

        def start(self):
            return None

    activity = {"seconds_since_activity": 1.0}
    agent = types.SimpleNamespace(
        get_activity_summary=lambda: dict(activity),
        interrupt=lambda message=None: interrupted.append("interrupted"),
    )

    class _DeadThread:
        def is_alive(self):
            return False

    session = _session(
        agent=agent,
        transport=server._detached_ws_transport,
        running=True,
        _run_thread=_DeadThread(),
    )
    server._sessions["fresh-sid"] = session
    monkeypatch.setattr(server, "_WS_ORPHAN_REAP_GRACE_S", 0.01)
    monkeypatch.setattr(server, "_WS_ORPHAN_ACTIVITY_STALE_S", 300.0)
    monkeypatch.setattr(server.threading, "Timer", _Timer)
    monkeypatch.setattr(server, "_load_cfg", lambda: {})
    monkeypatch.setattr(
        server,
        "_teardown_popped_session",
        lambda claimed, *, end_reason: torn_down.append((claimed, end_reason)) or True,
    )

    try:
        server._schedule_ws_orphan_reap("fresh-sid")

        # Two grace cycles with fresh activity: no interrupt, reschedule at
        # the GRACE interval (not the 1s interrupt-settle poll).
        for _ in range(2):
            callbacks.pop(0)()
            assert interrupted == []
            assert not session.get("_client_gone_interrupt_requested")
            assert delays[-1] == server._WS_ORPHAN_REAP_GRACE_S
            assert "fresh-sid" in server._sessions

        # Activity goes stale (turn wedged) -> interrupt fires on next poll.
        activity["seconds_since_activity"] = 301.0
        callbacks.pop(0)()
        assert interrupted == ["interrupted"]
        assert session["_client_gone_interrupt_requested"] is True

        # Turn settles -> reap proceeds exactly as today.
        session["running"] = False
        callbacks.pop(0)()
        assert "fresh-sid" not in server._sessions
        assert torn_down == [(session, "ws_orphan_reap")]
    finally:
        server._sessions.pop("fresh-sid", None)


def test_ws_orphan_activity_gate_zero_restores_interrupt_at_grace(monkeypatch):
    """ws_orphan_activity_stale_s=0 opts out: fresh activity no longer defers
    the client-gone interrupt (pre-#98028 behaviour)."""
    callbacks = []
    interrupted = []

    class _Timer:
        def __init__(self, _delay, callback):
            callbacks.append(callback)
            self.daemon = False

        def start(self):
            return None

    class _LiveThread:
        def is_alive(self):
            return True

    agent = types.SimpleNamespace(
        get_activity_summary=lambda: {"seconds_since_activity": 0.5},
        interrupt=lambda message=None: interrupted.append("interrupted"),
    )
    session = _session(
        agent=agent,
        transport=server._detached_ws_transport,
        running=True,
        _run_thread=_LiveThread(),
    )
    server._sessions["optout-sid"] = session
    monkeypatch.setattr(server, "_WS_ORPHAN_REAP_GRACE_S", 0.01)
    monkeypatch.setattr(server, "_WS_ORPHAN_ACTIVITY_STALE_S", 0.0)
    monkeypatch.setattr(server.threading, "Timer", _Timer)
    monkeypatch.setattr(server, "_load_cfg", lambda: {})

    try:
        server._schedule_ws_orphan_reap("optout-sid")
        callbacks.pop(0)()
        assert interrupted == ["interrupted"]
        assert session["_client_gone_interrupt_requested"] is True
    finally:
        server._sessions.pop("optout-sid", None)


def test_ws_orphan_activity_gate_unreadable_summary_stays_eligible(monkeypatch):
    """A broken/opaque activity summary must fail CLOSED (not fresh): the
    wedged-turn interrupt-at-grace safety net is preserved."""

    def _boom():
        raise RuntimeError("summary unavailable")

    agent = types.SimpleNamespace(get_activity_summary=_boom)
    monkeypatch.setattr(server, "_WS_ORPHAN_ACTIVITY_STALE_S", 300.0)
    assert server._ws_orphan_turn_activity_is_fresh({"agent": agent}) is False
    # No agent / no summary method: same conservative answer.
    assert server._ws_orphan_turn_activity_is_fresh({"agent": None}) is False
    assert (
        server._ws_orphan_turn_activity_is_fresh(
            {"agent": types.SimpleNamespace()}
        )
        is False
    )
    # Never-stamped clock (None) is not fresh either.
    agent2 = types.SimpleNamespace(
        get_activity_summary=lambda: {"seconds_since_activity": None}
    )
    assert server._ws_orphan_turn_activity_is_fresh({"agent": agent2}) is False


def test_init_session_fires_reset_hook(monkeypatch):
    hooks = []

    class _FakeWorker:
        def __init__(self, key, model, profile_home=None):
            self.key = key

        def close(self):
            return None

    monkeypatch.setattr(server, "_SlashWorker", _FakeWorker)
    monkeypatch.setattr(server, "_wire_callbacks", lambda _sid: None)
    monkeypatch.setattr(server, "_emit", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        server,
        "_notify_session_boundary",
        lambda event, session_id, *_args: hooks.append((event, session_id)),
    )

    import tools.approval as _approval

    monkeypatch.setattr(_approval, "register_gateway_notify", lambda key, cb: None)
    monkeypatch.setattr(_approval, "load_permanent_allowlist", lambda: None)

    sid = "sid"
    try:
        server._init_session(
            sid,
            "session-key",
            types.SimpleNamespace(model="x"),
            history=[],
            cols=80,
        )
        assert ("on_session_reset", "session-key") in hooks
    finally:
        server._sessions.pop(sid, None)


def test_session_title_creates_row_and_sets_immediately_when_not_ready(monkeypatch):
    """An explicit /title before the first message must persist NOW, not queue.

    Regression: the desktop deferred the DB row to the first prompt, so a
    /title typed before any message only stashed ``pending_title`` and relied
    on a post-turn apply block. When that turn never landed under the session
    key, the title was silently lost and the sidebar fell back to the message
    preview. The handler now creates the row up front (mirroring the messaging
    gateway) so an explicit /title takes effect immediately.
    """
    state = {"row": None, "title": None, "ensured": False}

    class _FakeDB:
        def get_session_title(self, _key):
            return state["title"]

        def get_session(self, _key):
            return state["row"]

        def set_session_title(self, _key, title):
            # Mirrors SessionDB: UPDATE affects 0 rows until the row exists.
            if state["row"] is None:
                return False
            state["title"] = title
            return True

    fake_db = _FakeDB()

    def _fake_ensure_row(_session):
        # The real _ensure_session_db_row does an INSERT OR IGNORE.
        state["ensured"] = True
        state["row"] = {"id": "session-key", "title": None}

    import contextlib

    @contextlib.contextmanager
    def _fake_session_db(_session):
        yield fake_db

    server._sessions["sid"] = _session(pending_title=None)
    monkeypatch.setattr(server, "_get_db", lambda: fake_db)
    monkeypatch.setattr(server, "_ensure_session_db_row", _fake_ensure_row)
    monkeypatch.setattr(server, "_session_db", _fake_session_db)
    try:
        set_resp = server.handle_request(
            {
                "id": "1",
                "method": "session.title",
                "params": {"session_id": "sid", "title": "my-custom-name"},
            }
        )

        # No longer queued — the row is created and the title set immediately.
        assert set_resp["result"]["pending"] is False
        assert set_resp["result"]["title"] == "my-custom-name"
        assert state["ensured"] is True, "the row must be created up front"
        assert state["title"] == "my-custom-name"
        assert server._sessions["sid"]["pending_title"] is None

        # A subsequent read reflects the persisted title.
        get_resp = server.handle_request(
            {"id": "2", "method": "session.title", "params": {"session_id": "sid"}}
        )
        assert get_resp["result"]["title"] == "my-custom-name"
    finally:
        server._sessions.pop("sid", None)


def test_session_title_falls_back_to_queue_when_row_create_fails(monkeypatch):
    """If row creation can't take (DB down / racing writer), keep the queue.

    The post-turn apply block is still the recovery path, so a /title that
    can't persist up front must not be dropped — it falls back to
    ``pending_title`` exactly as before.
    """

    class _FakeDB:
        def get_session_title(self, _key):
            return None

        def get_session(self, _key):
            return None

        def set_session_title(self, _key, _title):
            return False

    fake_db = _FakeDB()

    def _fake_ensure_row(_session):
        # Simulate a persist that didn't take — row still absent.
        pass

    import contextlib

    @contextlib.contextmanager
    def _fake_session_db(_session):
        yield fake_db

    server._sessions["sid"] = _session(pending_title=None)
    monkeypatch.setattr(server, "_get_db", lambda: fake_db)
    monkeypatch.setattr(server, "_ensure_session_db_row", _fake_ensure_row)
    monkeypatch.setattr(server, "_session_db", _fake_session_db)
    try:
        set_resp = server.handle_request(
            {
                "id": "1",
                "method": "session.title",
                "params": {"session_id": "sid", "title": "queued title"},
            }
        )

        assert set_resp["result"]["pending"] is True
        assert set_resp["result"]["title"] == "queued title"
        assert server._sessions["sid"]["pending_title"] == "queued title"

        get_resp = server.handle_request(
            {"id": "2", "method": "session.title", "params": {"session_id": "sid"}}
        )
        assert get_resp["result"]["title"] == "queued title"
    finally:
        server._sessions.pop("sid", None)


def test_notification_event_routing_by_session_key(monkeypatch):
    """Background-process events surface only in the session that owns them."""
    mine = _session(session_key="mine")
    other = _session(session_key="other")
    monkeypatch.setattr(server, "_sessions", {"a": mine, "b": other})

    # My own event → handle it.
    assert server._notification_event_belongs_elsewhere("a", mine, {"session_key": "mine"}) is False
    # Global/system event with no owner → handle it.
    assert server._notification_event_belongs_elsewhere("a", mine, {"session_key": ""}) is False
    assert server._notification_event_belongs_elsewhere("a", mine, {}) is False
    # Owned by another *live* session → defer to that session's poller.
    assert server._notification_event_belongs_elsewhere("a", mine, {"session_key": "other"}) is True
    # Owner is gone (not in _sessions) → handle as fallback so it isn't lost.
    assert server._notification_event_belongs_elsewhere("a", mine, {"session_key": "ghost"}) is False


def test_async_delegation_event_prefers_origin_ui_session(monkeypatch):
    """Detached subagent completions return to the commissioning TUI tab.

    Regression: when the durable session key was stale/orphaned, whichever
    desktop poller woke first could consume the async result and inject it into
    an unrelated session.
    """
    mine = _session(session_key="current-key")
    other = _session(session_key="unrelated-key")
    monkeypatch.setattr(server, "_sessions", {"origin-sid": mine, "other-sid": other})
    monkeypatch.setattr(server, "_get_db", lambda: None)
    evt = {
        "type": "async_delegation",
        "session_key": "stale-or-rotated-key",
        "origin_ui_session_id": "origin-sid",
    }

    assert server._notification_event_belongs_elsewhere("other-sid", other, evt) is True
    assert server._notification_event_belongs_elsewhere("origin-sid", mine, evt) is False


def test_notification_event_follows_compression_continuation(monkeypatch):
    """Events keyed to a compressed parent route to the live continuation."""
    old_parent = _session(session_key="old-parent")
    live_tip = _session(session_key="new-tip")
    monkeypatch.setattr(server, "_sessions", {"old-sid": old_parent, "tip-sid": live_tip})

    class _DB:
        def resolve_resume_session_id(self, session_id):
            return "new-tip" if session_id == "old-parent" else session_id

    monkeypatch.setattr(server, "_get_db", lambda: _DB())
    evt = {"type": "async_delegation", "session_key": "old-parent"}

    assert server._notification_event_belongs_elsewhere("old-sid", old_parent, evt) is True
    assert server._notification_event_belongs_elsewhere("tip-sid", live_tip, evt) is False
    # A third session must leave it alone for the continuation's poller.
    third = _session(session_key="third")
    monkeypatch.setattr(
        server,
        "_sessions",
        {"old-sid": old_parent, "tip-sid": live_tip, "third-sid": third},
    )
    assert server._notification_event_belongs_elsewhere("third-sid", third, evt) is True


def test_finalized_origin_ui_session_falls_back_to_live_continuation(monkeypatch):
    """A closed origin tab must not steal its resumed continuation's result."""
    finalized_origin = _session(session_key="old-parent", _finalized=True)
    live_tip = _session(session_key="new-tip")
    monkeypatch.setattr(
        server,
        "_sessions",
        {"origin-sid": finalized_origin, "tip-sid": live_tip},
    )

    class _DB:
        def resolve_resume_session_id(self, session_id):
            return "new-tip" if session_id == "old-parent" else session_id

    monkeypatch.setattr(server, "_get_db", lambda: _DB())
    evt = {
        "type": "async_delegation",
        "session_key": "old-parent",
        "origin_ui_session_id": "origin-sid",
    }

    assert server._notification_event_belongs_elsewhere("origin-sid", finalized_origin, evt) is True
    assert server._notification_event_belongs_elsewhere("tip-sid", live_tip, evt) is False


def test_prompt_submit_rejects_negative_truncate_ordinal(monkeypatch):
    """A negative truncate_before_user_ordinal must be rejected, not honoured.

    The handler validates the upper bound (`ordinal >= len(user_indices)`) but a
    negative ordinal would otherwise slip through and hit Python negative
    indexing: `user_indices[-1]` selects the LAST user turn, truncating history
    to everything before it and persisting that loss via replace_messages — an
    unrecoverable overwrite of the session DB. Reject it on the safe 4018 path
    and leave the in-memory history and the DB untouched.
    """
    replaced = []

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
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": "second"},
        {"role": "assistant", "content": "done"},
    ]
    server._sessions["trunc-sid"] = _session(history=list(history))
    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    # If the guard ever lets a negative ordinal through, these would run and the
    # session would be marked busy; failing here makes that regression loud.
    monkeypatch.setattr(
        server, "_start_agent_build", lambda *a, **k: pytest.fail("must not start a turn")
    )
    monkeypatch.setattr(
        server, "_start_inflight_turn", lambda *a, **k: pytest.fail("must not start a turn")
    )

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "trunc-sid",
                    "text": "next",
                    "truncate_before_user_ordinal": -1,
                    "confirm_truncate": True,
                },
            }
        )
        assert resp["error"]["code"] == 4018
        # History and the DB are left exactly as they were — no silent loss.
        assert server._sessions["trunc-sid"]["history"] == history
        assert server._sessions["trunc-sid"]["running"] is False
        assert replaced == []
    finally:
        server._sessions.pop("trunc-sid", None)


def test_prompt_submit_refuses_boolean_ordinal(monkeypatch):
    """A JSON `true` ordinal must return 4004, not coerce to turn 1.

    bool is an int subclass, so `int(True) == 1`: a client bug that sends
    `truncate_before_user_ordinal: true` with confirm_truncate would aim a
    confirmed rewind at the SECOND user turn and hard-truncate everything
    after the first — the same silent-loss class as #82756.
    """
    history = [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "reply 1"},
        {"role": "user", "content": "second"},
        {"role": "assistant", "content": "reply 2"},
    ]
    server._sessions["bool-trunc-sid"] = _session(history=list(history))
    monkeypatch.setattr(
        server, "_start_agent_build", lambda *a, **k: pytest.fail("must not start a turn")
    )
    monkeypatch.setattr(
        server, "_start_inflight_turn", lambda *a, **k: pytest.fail("must not start a turn")
    )

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "bool-trunc-sid",
                    "text": "new turn",
                    "truncate_before_user_ordinal": True,
                    "confirm_truncate": True,
                },
            }
        )
        assert resp.get("error") is not None
        assert resp["error"]["code"] == 4004
        assert server._sessions["bool-trunc-sid"]["history"] == history
    finally:
        server._sessions.pop("bool-trunc-sid", None)


def test_prompt_submit_refuses_confirm_truncate_without_target(monkeypatch):
    """confirm_truncate with no ordinal is leaked rewind state — fail fast.

    The desktop auto-attaches confirm_truncate whenever it builds truncation
    params (#82756); a bare flag on an ordinary submit means the client's
    composer state is corrupted. Refusing loudly surfaces the client bug
    instead of quietly ignoring the flag.
    """
    history = [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "reply 1"},
    ]
    server._sessions["bare-confirm-sid"] = _session(history=list(history))
    monkeypatch.setattr(
        server, "_start_agent_build", lambda *a, **k: pytest.fail("must not start a turn")
    )
    monkeypatch.setattr(
        server, "_start_inflight_turn", lambda *a, **k: pytest.fail("must not start a turn")
    )

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "bare-confirm-sid",
                    "text": "new turn",
                    "confirm_truncate": True,
                },
            }
        )
        assert resp.get("error") is not None
        assert resp["error"]["code"] == 4004
        assert server._sessions["bare-confirm-sid"]["history"] == history
    finally:
        server._sessions.pop("bare-confirm-sid", None)


def test_prompt_submit_refuses_unconfirmed_nonempty_truncation(monkeypatch):
    """An ordinal without confirm_truncate must not drop the session tail.

    #80763: a desktop client carried a leftover truncate_before_user_ordinal
    into an ORDINARY submit. The request was indistinguishable from a real
    rewind — in-range ordinal, non-empty result — so the empty-truncation guard
    never fired and replace_messages() DELETEd 244 durable rows (296 -> 52).
    Intent has to be stated: refuse on 4029 and leave memory and DB untouched.
    """
    replaced = []

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
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": "second"},
        {"role": "assistant", "content": "done"},
        {"role": "user", "content": "third"},
        {"role": "assistant", "content": "sure"},
    ]
    server._sessions["unconfirmed-trunc-sid"] = _session(history=list(history))
    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    monkeypatch.setattr(
        server, "_start_agent_build", lambda *a, **k: pytest.fail("must not start a turn")
    )
    monkeypatch.setattr(
        server, "_start_inflight_turn", lambda *a, **k: pytest.fail("must not start a turn")
    )

    def _submit(**extra):
        return server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "unconfirmed-trunc-sid",
                    "text": "an ordinary typed message",
                    "truncate_before_user_ordinal": 2,
                    **extra,
                },
            }
        )

    try:
        resp = _submit()
        assert resp["error"]["code"] == 4029
        assert "confirm_truncate" in resp["error"]["message"]
        # Explicit falsey values must not satisfy the opt-in either.
        for falsey in (False, 0, "", "false", "no"):
            assert _submit(confirm_truncate=falsey)["error"]["code"] == 4029, falsey
        # confirm_empty_truncate is a different gate — it must not stand in for
        # rewind intent on a cut that leaves the transcript non-empty.
        assert _submit(confirm_empty_truncate=True)["error"]["code"] == 4029
        session = server._sessions["unconfirmed-trunc-sid"]
        assert session["history"] == history
        assert session["history_version"] == 0
        assert session["running"] is False
        assert replaced == []
    finally:
        server._sessions.pop("unconfirmed-trunc-sid", None)


def test_prompt_submit_truncates_by_message_id(monkeypatch):
    """#82756: truncate_before_message_id resolves target message and cuts history accurately."""
    replaced = []

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
        {"id": "msg-1", "role": "user", "content": "first"},
        {"role": "assistant", "content": "reply 1"},
        {"id": "msg-2", "role": "user", "content": "second"},
        {"role": "assistant", "content": "reply 2"},
    ]
    server._sessions["msg-id-trunc-sid"] = _session(history=list(history))
    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    monkeypatch.setattr(
        server, "_start_agent_build", lambda *a, **k: None
    )
    monkeypatch.setattr(
        server, "_start_inflight_turn", lambda *a, **k: None
    )

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "msg-id-trunc-sid",
                    "text": "new turn",
                    "truncate_before_message_id": "msg-2",
                    "confirm_truncate": True,
                },
            }
        )
        assert resp.get("result") is not None
        assert len(replaced) == 1
        assert replaced[0][1] == history[:2]
    finally:
        server._sessions.pop("msg-id-trunc-sid", None)


def test_prompt_submit_truncation_falls_back_to_sid_when_session_key_null(monkeypatch):
    """#81904: a NULL session_key must not FK-fail the truncation persist.

    CLI-origin sessions resumed in the Desktop have no session_key; the
    truncation path used to call replace_messages(None, ...), whose reinsert
    violated the messages.session_id FK ("FOREIGN KEY constraint failed" →
    "Restore failed"). The persist must key off the session id instead —
    for CLI-origin rows the durable sessions.id IS the requested sid.
    """
    replaced = []

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
        {"_row_id": 102, "role": "assistant", "content": "reply 1"},
        {"_row_id": 103, "role": "user", "content": "second"},
        {"_row_id": 104, "role": "assistant", "content": "reply 2"},
    ]
    server._sessions["null-key-trunc-sid"] = _session(
        history=list(history), session_key=None
    )
    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    monkeypatch.setattr(server, "_start_agent_build", lambda *a, **k: None)
    monkeypatch.setattr(server, "_start_inflight_turn", lambda *a, **k: None)

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "null-key-trunc-sid",
                    "text": "new turn",
                    "truncate_before_row_id": 103,
                    "truncate_before_user_ordinal": 1,
                    "confirm_truncate": True,
                },
            }
        )
        assert resp.get("result") is not None
        assert len(replaced) == 1
        # Keyed by the session id, never None (the FK-violating value).
        assert replaced[0][0] == "null-key-trunc-sid"
        assert replaced[0][1] == history[:2]
    finally:
        server._sessions.pop("null-key-trunc-sid", None)


def test_prompt_submit_refuses_ordinal_and_message_id_mismatch(monkeypatch):
    """#82756: A mismatch between truncate_before_user_ordinal and truncate_before_message_id must return 4030."""
    history = [
        {"id": "msg-1", "role": "user", "content": "first"},
        {"role": "assistant", "content": "reply 1"},
        {"id": "msg-2", "role": "user", "content": "second"},
        {"role": "assistant", "content": "reply 2"},
    ]
    server._sessions["mismatch-trunc-sid"] = _session(history=list(history))
    monkeypatch.setattr(
        server, "_start_agent_build", lambda *a, **k: pytest.fail("must not start a turn")
    )
    monkeypatch.setattr(
        server, "_start_inflight_turn", lambda *a, **k: pytest.fail("must not start a turn")
    )

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "mismatch-trunc-sid",
                    "text": "new turn",
                    "truncate_before_message_id": "msg-2",  # ordinal index 1
                    "truncate_before_user_ordinal": 0,      # mismatch (stale 0)
                    "confirm_truncate": True,
                },
            }
        )
        assert resp.get("error") is not None
        assert resp["error"]["code"] == 4030
    finally:
        server._sessions.pop("mismatch-trunc-sid", None)


def test_prompt_submit_refuses_ordinal_only_when_history_has_row_ids(monkeypatch):
    """A durable session must not trust an ordinal without a row-id target."""
    replaced = []

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
        {"_row_id": 102, "role": "assistant", "content": "reply 1"},
        {"_row_id": 103, "role": "user", "content": "second"},
        {"_row_id": 104, "role": "assistant", "content": "reply 2"},
    ]
    server._sessions["ordinal-only-durable-sid"] = _session(history=list(history))
    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    monkeypatch.setattr(
        server, "_start_agent_build", lambda *a, **k: pytest.fail("must not start a turn")
    )
    monkeypatch.setattr(
        server, "_start_inflight_turn", lambda *a, **k: pytest.fail("must not start a turn")
    )

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "ordinal-only-durable-sid",
                    "text": "retry",
                    "truncate_before_user_ordinal": 1,
                    "confirm_truncate": True,
                },
            }
        )

        assert resp["error"]["code"] == 4004
        assert "truncate_before_row_id" in resp["error"]["message"]
        assert server._sessions["ordinal-only-durable-sid"]["history"] == history
        assert server._sessions["ordinal-only-durable-sid"]["running"] is False
        assert replaced == []
    finally:
        server._sessions.pop("ordinal-only-durable-sid", None)


def test_prompt_submit_refuses_ordinal_only_when_durable_history_is_unstamped(monkeypatch):
    """Durability comes from state.db, not optional stamps on the live copy."""
    replaced = []
    history = [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "reply 1"},
        {"role": "user", "content": "second"},
        {"role": "assistant", "content": "reply 2"},
    ]

    class _FakeDB:
        def get_messages_as_conversation(self, key, **kwargs):
            assert key == "session-key"
            assert kwargs["include_row_ids"] is True
            return [dict(message, _row_id=100 + index) for index, message in enumerate(history)]

        def replace_messages(self, key, messages, active_only=False, archive_dropped=False):
            replaced.append((key, list(messages)))

    server._sessions["unstamped-durable-sid"] = _session(history=list(history))
    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    monkeypatch.setattr(
        server, "_start_agent_build", lambda *a, **k: pytest.fail("must not start a turn")
    )
    monkeypatch.setattr(
        server, "_start_inflight_turn", lambda *a, **k: pytest.fail("must not start a turn")
    )

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "unstamped-durable-sid",
                    "text": "retry",
                    "truncate_before_user_ordinal": 1,
                    "confirm_truncate": True,
                },
            }
        )

        assert resp["error"]["code"] == 4004
        assert "truncate_before_row_id" in resp["error"]["message"]
        assert server._sessions["unstamped-durable-sid"]["history"] == history
        assert replaced == []
    finally:
        server._sessions.pop("unstamped-durable-sid", None)


def test_prompt_submit_truncates_by_row_id(monkeypatch):
    """#82959: prompt.submit with truncate_before_row_id must cut at the target row id."""
    replaced = []

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
        {"_row_id": 102, "role": "assistant", "content": "reply 1"},
        {"_row_id": 103, "role": "user", "content": "second"},
        {"_row_id": 104, "role": "assistant", "content": "reply 2"},
    ]
    sess = _session(history=list(history))
    server._sessions["row-id-trunc-sid"] = sess
    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    started = []
    monkeypatch.setattr(
        server, "_start_agent_build", lambda *a, **k: started.append(k)
    )

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "row-id-trunc-sid",
                    "text": "new turn",
                    "truncate_before_row_id": 103,
                    "truncate_before_user_ordinal": 1,
                    "confirm_truncate": True,
                },
            }
        )
        assert resp.get("error") is None
        assert len(sess["history"]) == 2
        assert sess["history"][-1]["content"] == "reply 1"
        assert len(replaced) == 1
        assert replaced[0][1] == history[:2]
    finally:
        server._sessions.pop("row-id-trunc-sid", None)


def test_prompt_submit_truncates_by_string_row_id(monkeypatch):
    """#82959: String row IDs in history match correctly against integer truncate_before_row_id."""
    replaced = []

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
        {"_row_id": "101", "role": "user", "content": "first"},
        {"_row_id": "102", "role": "assistant", "content": "reply 1"},
        {"_row_id": "103", "role": "user", "content": "second"},
        {"_row_id": "104", "role": "assistant", "content": "reply 2"},
    ]
    sess = _session(history=list(history))
    server._sessions["str-row-id-trunc-sid"] = sess
    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    monkeypatch.setattr(server, "_start_agent_build", lambda *a, **k: None)

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "str-row-id-trunc-sid",
                    "text": "new turn",
                    "truncate_before_row_id": 103,
                    "confirm_truncate": True,
                },
            }
        )
        assert resp.get("error") is None
        assert len(sess["history"]) == 2
    finally:
        server._sessions.pop("str-row-id-trunc-sid", None)


def test_prompt_submit_refuses_ordinal_and_row_id_mismatch(monkeypatch):
    """#82959: A mismatch between truncate_before_user_ordinal and truncate_before_row_id must return 4030."""
    history = [
        {"_row_id": 201, "role": "user", "content": "first"},
        {"_row_id": 202, "role": "assistant", "content": "reply 1"},
        {"_row_id": 203, "role": "user", "content": "second"},
        {"_row_id": 204, "role": "assistant", "content": "reply 2"},
    ]
    server._sessions["row-mismatch-sid"] = _session(history=list(history))
    monkeypatch.setattr(
        server, "_start_agent_build", lambda *a, **k: pytest.fail("must not start a turn")
    )

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "row-mismatch-sid",
                    "text": "new turn",
                    "truncate_before_row_id": 203,  # user turn ordinal 1
                    "truncate_before_user_ordinal": 0,  # mismatch (stale 0)
                    "confirm_truncate": True,
                },
            }
        )
        assert resp.get("error") is not None
        assert resp["error"]["code"] == 4030
    finally:
        server._sessions.pop("row-mismatch-sid", None)


def test_prompt_submit_refuses_boolean_row_id(monkeypatch):
    """Boolean truncate_before_row_id must return 4004."""
    history = [
        {"_row_id": 301, "role": "user", "content": "first"},
        {"_row_id": 302, "role": "assistant", "content": "reply 1"},
    ]
    server._sessions["bool-row-sid"] = _session(history=list(history))
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "bool-row-sid",
                    "text": "new turn",
                    "truncate_before_row_id": True,
                    "confirm_truncate": True,
                },
            }
        )
        assert resp.get("error") is not None
        assert resp["error"]["code"] == 4004
    finally:
        server._sessions.pop("bool-row-sid", None)


def test_prompt_submit_row_id_not_found(monkeypatch):
    """Unknown truncate_before_row_id must return 4018."""
    history = [
        {"_row_id": 401, "role": "user", "content": "first"},
    ]
    server._sessions["missing-row-sid"] = _session(history=list(history))
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "missing-row-sid",
                    "text": "new turn",
                    "truncate_before_row_id": 999,
                    "confirm_truncate": True,
                },
            }
        )
        assert resp.get("error") is not None
        assert resp["error"]["code"] == 4018
    finally:
        server._sessions.pop("missing-row-sid", None)


def test_prompt_submit_row_id_ignores_platform_id_fallback(monkeypatch):
    """truncate_before_row_id must not match string platform IDs."""
    history = [
        {"id": "999", "role": "user", "content": "first"},
        {"role": "assistant", "content": "reply 1"},
    ]
    server._sessions["string-id-sid"] = _session(history=list(history))
    try:
        resp = server.handle_request({
            "id": "1",
            "method": "prompt.submit",
            "params": {
                "session_id": "string-id-sid",
                "text": "new turn",
                "truncate_before_row_id": 999,
                "confirm_truncate": True,
            }
        })
        assert resp.get("error") is not None
        assert resp["error"]["code"] == 4018
    finally:
        server._sessions.pop("string-id-sid", None)


def test_prompt_submit_refuses_empty_truncation_without_confirm(monkeypatch):
    """A confirmed rewind still must not wipe a non-empty transcript by accident.

    Ordinal 0 cuts at the first user message (history[:0] == []) and
    replace_messages() would DELETE every durable row. Even a submit that
    declares rewind intent needs the second opt-in for that edge.
    """
    replaced = []

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
    server._sessions["empty-trunc-sid"] = _session(history=list(history))
    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    monkeypatch.setattr(
        server, "_start_agent_build", lambda *a, **k: pytest.fail("must not start a turn")
    )
    monkeypatch.setattr(
        server, "_start_inflight_turn", lambda *a, **k: pytest.fail("must not start a turn")
    )

    try:
        # Missing confirm → refuse.
        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "empty-trunc-sid",
                    "text": "fresh typed message",
                    "truncate_before_row_id": 101,
                    "truncate_before_user_ordinal": 0,
                    "confirm_truncate": True,
                },
            }
        )
        assert resp["error"]["code"] == 4028
        assert "confirm_empty_truncate" in resp["error"]["message"]
        # Explicit falsey values must not satisfy the opt-in either.
        for falsey in (False, 0, "", "false", "no"):
            resp = server.handle_request(
                {
                    "id": "1",
                    "method": "prompt.submit",
                    "params": {
                        "session_id": "empty-trunc-sid",
                        "text": "fresh typed message",
                        "truncate_before_row_id": 101,
                        "truncate_before_user_ordinal": 0,
                        "confirm_truncate": True,
                        "confirm_empty_truncate": falsey,
                    },
                }
            )
            assert resp["error"]["code"] == 4028, falsey
        assert server._sessions["empty-trunc-sid"]["history"] == history
        assert server._sessions["empty-trunc-sid"]["running"] is False
        assert server._sessions["empty-trunc-sid"]["history_version"] == 0
        assert replaced == []
    finally:
        server._sessions.pop("empty-trunc-sid", None)
