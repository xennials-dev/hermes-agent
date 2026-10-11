"""tui_gateway.server — history-versioned prompt submit, interrupts and agent-build waits.

Split from test_tui_gateway_server.py; shared fixtures and helpers live
in tests/tui_gateway/_server_test_helpers.py.
"""

import threading
import types
import pytest
from tui_gateway import server

from tests.tui_gateway._server_test_helpers import (
    _ImmediateThread,
    _dispatch_sync,
    _neuter_agent_prewarm_timer,  # autouse
    _open_request,
    _reap_leaked_notification_pollers,  # autouse
    _session,
    _wake_lease_double,
)


def test_prompt_submit_sanitizes_bracketed_paste_before_agent(monkeypatch):
    """prompt.submit must sanitize corrupted user text before run_conversation."""
    captured: dict[str, str] = {}

    class _Agent:
        def run_conversation(self, prompt, conversation_history=None, stream_callback=None, **_kwargs):
            captured["prompt"] = prompt
            return {
                "final_response": "ok",
                "messages": [{"role": "assistant", "content": "ok"}],
            }

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None, **kw):
            self._target = target

        def start(self):
            self._target()

    corrupted = "hello[" + "~[[e" * 8
    server._sessions["sid"] = _session(agent=_Agent())
    try:
        monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)
        monkeypatch.setattr(server, "_get_usage", lambda _a: {})
        monkeypatch.setattr(server, "render_message", lambda _t, _c: "")
        monkeypatch.setattr(server, "_emit", lambda *a: None)
        monkeypatch.setattr(server, "_start_agent_build", lambda *a, **k: None)
        monkeypatch.setattr(server, "_ensure_session_db_row", lambda *a, **k: None)
        monkeypatch.setattr(server, "_persist_branch_seed", lambda *a, **k: None)

        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {"session_id": "sid", "text": corrupted},
            }
        )
        assert resp.get("result"), f"got error: {resp.get('error')}"
        assert captured["prompt"] == "hello"
    finally:
        server._sessions.pop("sid", None)


def test_prompt_submit_history_version_match_persists_normally(monkeypatch):
    """Regression guard: the backstop does not affect the happy path."""

    class _Agent:
        def run_conversation(self, prompt, conversation_history=None, stream_callback=None, **_kwargs):
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
    emits: list[tuple] = []
    try:
        monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)
        monkeypatch.setattr(server, "_get_usage", lambda _a: {})
        monkeypatch.setattr(server, "render_message", lambda _t, _c: "")
        monkeypatch.setattr(server, "_emit", lambda *a: emits.append(a))

        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {"session_id": "sid", "text": "hi"},
            }
        )
        assert resp.get("result")

        # History was written
        assert server._sessions["sid"]["history"] == [
            {"role": "assistant", "content": "reply"}
        ]
        assert server._sessions["sid"]["history_version"] == 1

        # No warning should be attached
        complete_calls = [a for a in emits if a[0] == "message.complete"]
        assert len(complete_calls) == 1
        _, _, payload = complete_calls[0]
        assert "warning" not in payload
    finally:
        server._sessions.pop("sid", None)


def test_prompt_submit_snapshots_history_after_pending_model_switch(monkeypatch):
    marker = {"role": "user", "content": "[model switched]"}
    seen = {}

    class _Agent:
        def run_conversation(self, prompt, conversation_history=None, **_kwargs):
            seen["history"] = conversation_history
            return {
                "final_response": "reply",
                "messages": [
                    *(conversation_history or []),
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": "reply"},
                ],
            }

    class _ImmediateThread:
        def __init__(self, target=None, **_kwargs):
            self._target = target

        def start(self):
            self._target()

    def _apply_pending(_sid, session):
        with session["history_lock"]:
            session["history"].append(marker)
            session["history_version"] += 1

    server._sessions["sid"] = _session(agent=_Agent())
    server._sessions["sid"]["pending_model_switch"] = {"raw": "new-model"}
    emits = []
    try:
        monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)
        monkeypatch.setattr(server, "_apply_pending_model_switch", _apply_pending)
        monkeypatch.setattr(server, "_sync_agent_model_with_config", lambda *_a: None)
        monkeypatch.setattr(server, "_get_usage", lambda _a: {})
        monkeypatch.setattr(server, "render_message", lambda *_a: "")
        monkeypatch.setattr(server, "_emit", lambda *a: emits.append(a))

        server.handle_request(
            {"id": "1", "method": "prompt.submit", "params": {"session_id": "sid", "text": "hi"}}
        )

        assert seen["history"] == [marker]
        assert server._sessions["sid"]["history"][-1] == {
            "role": "assistant", "content": "reply"
        }
        complete = [a for a in emits if a[0] == "message.complete"]
        assert "warning" not in complete[0][2]
    finally:
        server._sessions.pop("sid", None)


def test_prompt_submit_can_truncate_before_user_ordinal(monkeypatch):
    """Desktop user-message edits should restart the turn from the edited user."""

    seen = {}

    class _Agent:
        def run_conversation(self, prompt, conversation_history=None, stream_callback=None, **_kwargs):
            seen["prompt"] = prompt
            seen["history"] = conversation_history
            return {
                "final_response": "edited reply",
                "messages": [
                    *(conversation_history or []),
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": "edited reply"},
                ],
            }

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None, **_thread_options):
            self._target = target

        def start(self):
            self._target()

    original_history = [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "first reply"},
        {"role": "user", "content": "second"},
        {"role": "assistant", "content": "second reply"},
    ]
    server._sessions["sid"] = _session(agent=_Agent(), history=original_history)

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

    stub_db = _StubDb()

    try:
        monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)
        monkeypatch.setattr(server, "_get_usage", lambda _a: {})
        monkeypatch.setattr(server, "render_message", lambda _t, _c: "")
        monkeypatch.setattr(server, "_emit", lambda *a: None)
        monkeypatch.setattr(server, "_get_db", lambda: stub_db)

        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "sid",
                    "text": "edited second",
                    "truncate_before_user_ordinal": 1,
                    "confirm_truncate": True,
                },
            }
        )
        assert resp.get("result"), f"got error: {resp.get('error')}"

        assert seen["prompt"] == "edited second"
        assert seen["history"] == original_history[:2]
        assert server._sessions["sid"]["history"] == [
            *original_history[:2],
            {"role": "user", "content": "edited second"},
            {"role": "assistant", "content": "edited reply"},
        ]
        assert server._sessions["sid"]["history_version"] == 2
        assert stub_db.replaced == [("session-key", original_history[:2])]
    finally:
        server._sessions.pop("sid", None)


def test_prompt_submit_truncation_signals_busy_instead_of_queueing(monkeypatch):
    """#113942: editing a message while the turn it belongs to is still running

    must not be silently absorbed as a steered correction or a plain follow-up
    queued to run AFTER the live turn — both would drop the truncation and
    leave the original (un-edited) turn's reply intact, which reads to the
    user as "my edit was rejected". It must surface as the same "session busy"
    (4009) the desktop client's edit path already retries through (interrupt,
    then poll) until the turn actually clears.
    """
    agent = types.SimpleNamespace()  # no redirect/steer support -> would fall to queue+interrupt
    server._sessions["sid"] = _session(agent=agent, running=True)

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "sid",
                    "text": "edited while thinking",
                    "truncate_before_user_ordinal": 0,
                    "confirm_truncate": True,
                    "confirm_empty_truncate": True,
                },
            }
        )

        assert resp.get("error", {}).get("code") == 4009
        # The edit must not have been silently accepted as a queued follow-up.
        assert server._sessions["sid"].get("queued_prompt") is None
        assert server._sessions["sid"]["running"] is True
    finally:
        server._sessions.pop("sid", None)


def test_prompt_submit_truncation_refuses_redirect_of_live_turn():
    """The redirect-capable agent (the Desktop's normal case) is the branch that silently
    absorbed the edit: `busy_input_mode=interrupt` turned the rewind into a mid-turn
    redirect and left the un-edited transcript in place."""
    redirected = []
    agent = types.SimpleNamespace(
        _supports_active_turn_redirect=True, redirect=lambda text: redirected.append(text) or True)
    server._sessions["sid"] = _session(agent=agent, running=True, history=[{"role": "user", "content": "original"}])

    try:
        resp = server.handle_request({
            "id": "1", "method": "prompt.submit",
            "params": {"session_id": "sid", "text": "edited while thinking", "truncate_before_user_ordinal": 0,
                       "confirm_truncate": True, "confirm_empty_truncate": True}})

        assert resp.get("error", {}).get("code") == 4009
        assert redirected == []
        assert server._sessions["sid"]["history"] == [{"role": "user", "content": "original"}]
    finally:
        server._sessions.pop("sid", None)


def test_prompt_submit_refuses_turn_when_truncate_persist_fails(monkeypatch):
    """If replace_messages fails during edit/regenerate truncate, do not run the turn.

    Memory-first + fail-open left session['history'] short while state.db kept
    the old tail. The agent flush then appends the new exchange on top of the
    'undone' turns — durable zombie history. Write first; on failure leave
    memory and DB unchanged and return 5008.
    """
    original_history = [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "first reply"},
        {"role": "user", "content": "second"},
        {"role": "assistant", "content": "second reply"},
    ]
    sess = _session(history=list(original_history))
    server._sessions["trunc-fail-sid"] = sess

    class _FailDb:
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
            raise OSError("disk full")

    monkeypatch.setattr(server, "_get_db", lambda: _FailDb())
    monkeypatch.setattr(
        server, "_start_inflight_turn", lambda *a, **k: pytest.fail("must not start a turn")
    )
    monkeypatch.setattr(
        server, "_start_agent_build", lambda *a, **k: pytest.fail("must not start a turn")
    )

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "trunc-fail-sid",
                    "text": "edited second",
                    "truncate_before_user_ordinal": 1,
                    "confirm_truncate": True,
                },
            }
        )
        assert "error" in resp
        assert resp["error"]["code"] == 5008
        # Memory left intact — same list contents as before the refused cut.
        assert sess["history"] == original_history
        assert sess["history_version"] == 0
        assert sess.get("running") is not True
    finally:
        server._sessions.pop("trunc-fail-sid", None)


# ---------------------------------------------------------------------------
# session.interrupt must only cancel pending prompts owned by the calling
# session — it must not blast-resolve clarify/sudo/secret prompts on
# unrelated sessions sharing the same tui_gateway process.  Without
# session scoping the other sessions' prompts silently resolve to empty
# strings, unblocking their agent threads as if the user cancelled.
# ---------------------------------------------------------------------------


def test_prompt_submit_truncate_ordinal_skips_display_kind_rows(monkeypatch):
    """truncate_before_user_ordinal must count only real user turns.

    display_kind timeline rows (model_switch, async_delegation_complete, …)
    are role=user but no client counts them as user turns. Without the
    filter, a trailing marker shifts the ordinal so the wrong message is
    targeted for truncation.
    """

    seen = {}

    class _Agent:
        def run_conversation(self, prompt, conversation_history=None, stream_callback=None, **_kwargs):
            seen["prompt"] = prompt
            seen["history"] = conversation_history
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

    original_history = [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "first reply"},
        {"role": "user", "content": "second"},
        {"role": "assistant", "content": "second reply"},
        {
            "role": "user",
            "content": "background agent finished",
            "display_kind": "async_delegation_complete",
        },
    ]
    server._sessions["sid"] = _session(agent=_Agent(), history=original_history)

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

    stub_db = _StubDb()

    try:
        monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)
        monkeypatch.setattr(server, "_get_usage", lambda _a: {})
        monkeypatch.setattr(server, "render_message", lambda _t, _c: "")
        monkeypatch.setattr(server, "_emit", lambda *a: None)
        monkeypatch.setattr(server, "_get_db", lambda: stub_db)

        # ordinal=1 means "truncate before the 2nd-from-last real user turn"
        # which is "first". The display_kind marker must NOT shift the ordinal.
        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "sid",
                    "text": "edited first",
                    "truncate_before_user_ordinal": 1,
                    "confirm_truncate": True,
                },
            }
        )
        assert resp.get("result"), f"got error: {resp.get('error')}"

        # With display_kind filter: user_indices = [0, 2] (indices of "first" and "second").
        # ordinal=1 → user_indices[1] = 2, truncated = history[:2] = [first, first reply].
        # Without the filter: user_indices = [0, 2, 4] (includes the marker),
        # ordinal=1 → user_indices[1] = 2, same result by luck — but ordinal=0
        # would truncate to history[:0] vs history[:0], and higher ordinals shift.
        assert seen["history"] == original_history[:2], (
            f"Expected truncation to first 2 messages, got {seen['history']}"
        )
        assert stub_db.replaced == [("session-key", original_history[:2])], (
            f"Expected DB replace with first 2 messages, got {stub_db.replaced}"
        )
    finally:
        server._sessions.pop("sid", None)


def test_prompt_submit_truncate_translates_display_prefix_ordinal(monkeypatch):
    """Full-lineage Desktop ordinals must truncate the tip segment (#82462).

    After compression, session["history"] is the tip while display_history_prefix
    still holds ancestor user turns the UI shows. A client ordinal that includes
    those ancestors must map into the tip, not 4018.
    """

    seen = {}

    class _Agent:
        def run_conversation(self, prompt, conversation_history=None, stream_callback=None, **_kwargs):
            seen["prompt"] = prompt
            seen["history"] = conversation_history
            return {
                "final_response": "edited reply",
                "messages": [
                    *(conversation_history or []),
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": "edited reply"},
                ],
            }

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None, **_thread_options):
            self._target = target

        def start(self):
            self._target()

    tip_history = [
        {"role": "user", "content": "post-compress A"},
        {"role": "assistant", "content": "reply A"},
        {"role": "user", "content": "post-compress B"},
        {"role": "assistant", "content": "reply B"},
    ]
    display_prefix = [
        {"role": "user", "content": "pre-compress 1"},
        {"role": "assistant", "content": "pre reply 1"},
        {"role": "user", "content": "pre-compress 2"},
        {"role": "assistant", "content": "pre reply 2"},
    ]
    # Desktop lineage: pre1=0, pre2=1, postA=2, postB=3
    desktop_ordinal_for_post_b = 3

    server._sessions["sid"] = _session(
        agent=_Agent(),
        history=tip_history,
        display_history_prefix=display_prefix,
    )

    class _StubDb:
        def __init__(self):
            self.replaced = []

        def get_messages_as_conversation(self, *_args, **_kwargs):
            # Empty durable transcript: proves this ephemeral-style session
            # may take the ordinal-only path past the durability gate.
            return []

        def replace_messages(
            self,
            session_id,
            messages,
            active_only=False,
            archive_dropped=False,
            reject_active_turn_lease=False,
        ):
            assert reject_active_turn_lease is True
            self.replaced.append((session_id, list(messages)))

    stub_db = _StubDb()

    try:
        monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)
        monkeypatch.setattr(server, "_get_usage", lambda _a: {})
        monkeypatch.setattr(server, "render_message", lambda _t, _c: "")
        monkeypatch.setattr(server, "_emit", lambda *a: None)
        monkeypatch.setattr(server, "_get_db", lambda: stub_db)

        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "sid",
                    "text": "edited post B",
                    "truncate_before_user_ordinal": desktop_ordinal_for_post_b,
                    "confirm_truncate": True,
                },
            }
        )
        assert resp.get("result"), f"got error: {resp.get('error')}"
        assert seen["prompt"] == "edited post B"
        assert seen["history"] == tip_history[:2]
        assert stub_db.replaced == [("session-key", tip_history[:2])]
    finally:
        server._sessions.pop("sid", None)


def test_prompt_submit_truncate_oor_includes_structured_user_turn_count(monkeypatch):
    """4018 after compaction must carry recovery fields for Desktop (#82462)."""

    tip_history = [
        {"role": "user", "content": "post-compress A"},
        {"role": "assistant", "content": "reply A"},
    ]
    display_prefix = [
        {"role": "user", "content": "pre-compress 1"},
        {"role": "assistant", "content": "pre reply 1"},
    ]
    # Ordinal 0 points at the ancestor prefix — not editable from the tip.
    server._sessions["sid"] = _session(
        history=tip_history,
        display_history_prefix=display_prefix,
    )

    try:
        monkeypatch.setattr(
            server, "_start_inflight_turn", lambda *a, **k: pytest.fail("must not start a turn")
        )
        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "sid",
                    "text": "edit ancestor",
                    "truncate_before_user_ordinal": 0,
                    "confirm_truncate": True,
                },
            }
        )
        err = resp.get("error") or {}
        assert err.get("code") == 4018
        data = err.get("data") or {}
        assert data.get("user_turn_count") == 1
        assert data.get("ordinal") == 0
        assert data.get("segment_ordinal") == -1
        assert data.get("prefix_user_count") == 1
    finally:
        server._sessions.pop("sid", None)


def test_prompt_submit_row_id_accepts_full_lineage_ordinal(monkeypatch):
    """Desktop sends rowId + a full-lineage ordinal; both must agree (#82462).

    After compression the client's visible-user ordinal counts the ancestor
    prefix turns while the gateway resolves the row id tip-relative. The
    reconcile cross-check must treat `tip_ordinal + prefix_user_count` as
    agreement, not #82756 drift — and the cut stays aimed by the row id.
    """
    from agent.context_compressor import (
        HISTORICAL_TASK_HEADING,
        SUMMARY_PREFIX,
        _SUMMARY_END_MARKER,
    )

    tip_history = [
        {"_row_id": 501, "role": "user", "content": "post-compress A"},
        {"_row_id": 502, "role": "assistant", "content": "reply A"},
        {"_row_id": 503, "role": "user", "content": "post-compress B"},
        {"_row_id": 504, "role": "assistant", "content": "reply B"},
    ]
    display_prefix = [
        {"role": "user", "content": "pre-compress 1"},
        {"role": "assistant", "content": "pre reply 1"},
        {
            # Legacy pure handoffs did not always carry display_kind=hidden.
            # They are physically user rows but not visible/user-originated
            # turns, so they must not shift the Desktop lineage ordinal.
            "role": "user",
            "content": (
                f"{SUMMARY_PREFIX}\n{HISTORICAL_TASK_HEADING}\nold task\n\n"
                f"{_SUMMARY_END_MARKER}"
            ),
        },
        {"role": "user", "content": "pre-compress 2"},
        {"role": "assistant", "content": "pre reply 2"},
    ]

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
            assert reject_active_turn_lease is True
            replaced.append((key, list(messages)))

    sess = _session(history=list(tip_history), display_history_prefix=display_prefix)
    server._sessions["lineage-row-sid"] = sess
    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    monkeypatch.setattr(server, "_start_agent_build", lambda *a, **k: None)

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {
                    "session_id": "lineage-row-sid",
                    "text": "edited post B",
                    # Row id resolves to tip ordinal 1; the client counted the
                    # 2 ancestor user turns, so its lineage ordinal is 3.
                    "truncate_before_row_id": 503,
                    "truncate_before_user_ordinal": 3,
                    "confirm_truncate": True,
                },
            }
        )
        assert resp.get("error") is None, f"got error: {resp.get('error')}"
        assert sess["history"] == tip_history[:2]
    finally:
        # Release the slot the first turn claimed, as _finalize_session does in
        # production. Popping alone leaks the lease, and the second session below
        # uses the same session_key -- so without this the test fences itself out
        # of its own key and never reaches the mismatch it is checking.
        server._release_active_session_slot(sess)
        server._sessions.pop("lineage-row-sid", None)

    # A genuinely stale ordinal (matches neither the tip space nor the
    # lineage space) must still refuse with the #82756 mismatch.
    sess2 = _session(history=list(tip_history), display_history_prefix=display_prefix)
    server._sessions["lineage-row-sid-2"] = sess2
    monkeypatch.setattr(
        server, "_start_agent_build", lambda *a, **k: pytest.fail("must not start a turn")
    )
    try:
        resp = server.handle_request(
            {
                "id": "2",
                "method": "prompt.submit",
                "params": {
                    "session_id": "lineage-row-sid-2",
                    "text": "edited post B",
                    "truncate_before_row_id": 503,
                    "truncate_before_user_ordinal": 2,
                    "confirm_truncate": True,
                },
            }
        )
        assert resp.get("error") is not None
        assert resp["error"]["code"] == 4030
    finally:
        server._release_active_session_slot(sess2)
        server._sessions.pop("lineage-row-sid-2", None)


def test_interrupt_only_clears_own_session_pending():
    """session.interrupt on session A withdraws A's open server→client requests (a request.cancel each)
    and must NOT touch session B's — otherwise B's clarify/sudo/secret prompt silently resolves as if
    the user cancelled it."""
    import types
    from tui_gateway import server_requests

    session_a = _session()
    session_a["agent"] = types.SimpleNamespace(interrupt=lambda: None)
    session_b = _session()
    session_b["agent"] = types.SimpleNamespace(interrupt=lambda: None)
    server._sessions["sid_a"] = session_a
    server._sessions["sid_b"] = session_b
    req_a1, req_a2, req_b = _open_request("sid_a"), _open_request("sid_a", "sudo"), _open_request("sid_b")

    try:
        resp = server.handle_request({"id": "1", "method": "session.interrupt", "params": {"session_id": "sid_a"}})
        assert resp.get("result"), f"got error: {resp.get('error')}"

        assert req_a1.event.is_set() and req_a2.event.is_set() and not req_a1.answered
        assert not req_b.event.is_set(), (
            "CRITICAL: session.interrupt on sid_a released a prompt belonging to sid_b")
        assert server_requests.open_requests("sid_a") == []
        assert [r["id"] for r in server_requests.open_requests("sid_b")] == [req_b.id]
    finally:
        server._sessions.pop("sid_a", None)
        server._sessions.pop("sid_b", None)
        server_requests.reset_for_tests()


def test_accepted_interrupt_resumes_wake_mismatch_does_not(monkeypatch):
    """An accepted interrupt re-arms the caller's paused detector; a hosted-task mismatch does not."""
    wake_word, state, pause_listening, resume_listening = _wake_lease_double()
    owner = types.SimpleNamespace(_closed=False)
    state["lease"] = owner
    session = _session(
        agent=types.SimpleNamespace(interrupt=lambda: None),
        running=True,
        _hosted_room_task={"task_id": "active"},
    )
    server._sessions["sid"] = session
    monkeypatch.setattr(wake_word, "pause_listening", pause_listening)
    monkeypatch.setattr(wake_word, "resume_listening", resume_listening)
    monkeypatch.setattr(server, "_voice_wake_owner", None)
    try:
        paused = _dispatch_sync(
            {"id": "pause", "method": "wake.pause", "params": {}}, transport=owner
        )
        mismatch = _dispatch_sync(
            {
                "id": "mismatch",
                "method": "session.interrupt",
                "params": {"session_id": "sid", "expected_hosted_task_id": "stale"},
            },
            transport=owner,
        )
        assert paused["result"]["paused"] is True
        assert mismatch["result"] == {"status": "not_interrupted", "interrupted": False}
        assert state["paused"] is True
        assert state["resumed"] == []

        accepted = _dispatch_sync(
            {"id": "ok", "method": "session.interrupt", "params": {"session_id": "sid"}},
            transport=owner,
        )
        assert accepted.get("result", {}).get("status") == "interrupted"
        assert state == {"lease": owner, "paused": False, "resumed": [owner]}
    finally:
        server._sessions.pop("sid", None)


def test_interrupt_error_after_tts_stop_still_resumes_wake(monkeypatch):
    """TTS is cut before session lookup and the compute-host call; a later error must still re-arm."""
    wake_word, state, pause_listening, resume_listening = _wake_lease_double()
    owner = types.SimpleNamespace(_closed=False)
    state["lease"] = owner
    session = _session(agent=types.SimpleNamespace(interrupt=lambda: None), running=True)
    server._sessions["sid"] = session
    monkeypatch.setattr(wake_word, "pause_listening", pause_listening)
    monkeypatch.setattr(wake_word, "resume_listening", resume_listening)
    monkeypatch.setattr(server, "_voice_wake_owner", None)
    monkeypatch.setattr(server, "_session_uses_compute_host", lambda _session: True)

    def _host_failed(*_args, **_kwargs):
        raise RuntimeError("host failed")

    monkeypatch.setattr(server, "_interrupt_session_turn", _host_failed)
    try:
        paused = _dispatch_sync(
            {"id": "pause", "method": "wake.pause", "params": {}}, transport=owner
        )
        missing = _dispatch_sync(
            {"id": "missing", "method": "session.interrupt", "params": {"session_id": "gone"}},
            transport=owner,
        )
        assert paused["result"]["paused"] is True
        assert missing["error"]["code"] == 4001
        assert state["paused"] is False
        assert state["resumed"] == [owner]

        _dispatch_sync({"id": "pause-2", "method": "wake.pause", "params": {}}, transport=owner)
        failed = _dispatch_sync(
            {"id": "host", "method": "session.interrupt", "params": {"session_id": "sid"}},
            transport=owner,
        )
        assert failed["error"]["code"] == 5019
        assert state["paused"] is False
        assert state["resumed"] == [owner, owner]
    finally:
        server._sessions.pop("sid", None)


def test_interrupt_resumes_voice_wake_owner_not_a_foreign_lease(monkeypatch):
    """Interrupt resumes a voice-owned pause even when the caller differs, and leaves a foreign lease paused."""
    wake_word, state, pause_listening, resume_listening = _wake_lease_double()
    voice_owner = types.SimpleNamespace(_closed=False, role="voice")
    caller = types.SimpleNamespace(_closed=False, role="caller")
    foreign = types.SimpleNamespace(_closed=False, role="foreign")
    state["lease"] = voice_owner
    session = _session(agent=types.SimpleNamespace(interrupt=lambda: None), running=True)
    server._sessions["sid"] = session
    monkeypatch.setattr(wake_word, "pause_listening", pause_listening)
    monkeypatch.setattr(wake_word, "resume_listening", resume_listening)
    monkeypatch.setattr(server, "_voice_wake_owner", voice_owner)
    try:
        paused = _dispatch_sync(
            {"id": "pause", "method": "wake.pause", "params": {}}, transport=voice_owner
        )
        accepted = _dispatch_sync(
            {"id": "ok", "method": "session.interrupt", "params": {"session_id": "sid"}},
            transport=caller,
        )
        assert paused["result"]["paused"] is True
        assert accepted.get("result", {}).get("status") == "interrupted"
        assert state["paused"] is False
        assert any(item is voice_owner for item in state["resumed"])
        assert all(item is not caller for item in state["resumed"])

        state["lease"] = foreign
        state["paused"] = True
        state["resumed"] = []
        monkeypatch.setattr(server, "_voice_wake_owner", None)
        foreign_held = _dispatch_sync(
            {"id": "foreign", "method": "session.interrupt", "params": {"session_id": "sid"}},
            transport=caller,
        )
        assert foreign_held.get("result", {}).get("status") == "interrupted"
        assert state["paused"] is True
        assert state["resumed"] == []
    finally:
        server._sessions.pop("sid", None)


def test_run_prompt_submit_registers_turn_thread_for_interrupt(monkeypatch):
    """_run_prompt_submit must expose the actual turn thread to session.interrupt.

    prompt.submit's outer wrapper only waits for agent initialization, then
    _run_prompt_submit starts the real conversation thread. If the session keeps
    the wrapper thread handle, stop/esc sees a dead thread and never calls
    agent.interrupt() on the live turn.
    """
    calls = {"interrupted": False, "started": False}

    class _FakeThread:
        def __init__(self, target=None, daemon=None, **_thread_options):
            self.target = target

        def start(self):
            calls["started"] = True

        def is_alive(self):
            return True

    agent = types.SimpleNamespace(
        interrupt=lambda: calls.__setitem__("interrupted", True),
        run_conversation=lambda *args, **kwargs: {},
    )
    session = _session(agent=agent, running=True)
    server._sessions["sid"] = session

    try:
        monkeypatch.setattr(server.threading, "Thread", _FakeThread)
        monkeypatch.setattr(server, "_emit", lambda *args, **kwargs: None)

        server._run_prompt_submit("1", "sid", session, "hello")

        assert session.get("_run_thread") is not None
        resp = server.handle_request(
            {"id": "2", "method": "session.interrupt", "params": {"session_id": "sid"}}
        )

        assert resp.get("result"), f"got error: {resp.get('error')}"
        assert calls["interrupted"] is True
    finally:
        server._sessions.pop("sid", None)


def test_interrupt_drops_queued_prompt_for_session():
    """Explicit stop cancels a queued next turn instead of auto-draining it."""
    calls = {"interrupted": False}

    class _LiveThread:
        def is_alive(self):
            return True

    session = _session(
        agent=types.SimpleNamespace(
            interrupt=lambda: calls.__setitem__("interrupted", True)
        ),
        running=True,
        queued_prompt={"text": "next prompt", "transport": None},
        queued_prompts=[{"text": "later prompt", "image_paths": ["/tmp/later.png"], "transport": None}],
        _run_thread=_LiveThread(),
    )
    server._sessions["sid"] = session

    try:
        resp = server.handle_request(
            {"id": "1", "method": "session.interrupt", "params": {"session_id": "sid"}}
        )

        assert resp.get("result"), f"got error: {resp.get('error')}"
        assert calls["interrupted"] is True
        assert session.get("queued_prompt") is None
        assert session.get("queued_prompts") is None
    finally:
        server._sessions.pop("sid", None)


def test_interrupt_before_agent_ready_prevents_late_turn_start(monkeypatch):
    """Stop during lazy agent startup must not start the turn after init finishes."""
    threads = []
    calls = {"run_prompt": 0}

    class _FakeThread:
        def __init__(self, target=None, daemon=None, **_thread_options):
            self.target = target
            threads.append(self)

        def start(self):
            return None

        def is_alive(self):
            return True

    session = _session()
    session["agent"] = None
    server._sessions["sid"] = session

    try:
        monkeypatch.setattr(server.threading, "Thread", _FakeThread)
        monkeypatch.setattr(server, "_emit", lambda *args, **kwargs: None)
        monkeypatch.setattr(server, "_ensure_session_db_row", lambda session: None)
        monkeypatch.setattr(server, "_persist_branch_seed", lambda session: None)
        monkeypatch.setattr(server, "_start_agent_build", lambda sid, session: None)
        monkeypatch.setattr(server, "_wait_agent", lambda session, rid: None)
        monkeypatch.setattr(
            server,
            "_run_prompt_submit",
            lambda *args, **kwargs: calls.__setitem__(
                "run_prompt", calls["run_prompt"] + 1
            ),
        )

        submit = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {"session_id": "sid", "text": "hello"},
            }
        )
        assert submit.get("result"), f"got error: {submit.get('error')}"
        assert session["running"] is True
        assert len(threads) == 1

        stop = server.handle_request(
            {"id": "2", "method": "session.interrupt", "params": {"session_id": "sid"}}
        )
        assert stop.get("result"), f"got error: {stop.get('error')}"

        threads[0].target()

        assert calls["run_prompt"] == 0
        assert session["running"] is False
        assert session.get("inflight_turn") is None
    finally:
        server._sessions.pop("sid", None)


def test_cancelled_turn_before_agent_ready_emits_error_event(monkeypatch):
    """A turn cancelled during lazy agent startup must surface an error event.

    Sibling of test_interrupt_before_agent_ready_prevents_late_turn_start: that
    test only asserts `_run_prompt_submit` is skipped, mocking `_emit` to a
    no-op so it cannot catch a silent drop. This test captures `_emit` and
    asserts the client receives an `error` event with a human-readable message,
    so the Desktop composer can show feedback instead of hanging on a
    `{"status":"streaming"}` reply that never produces a turn (issue #63078
    server-side half).
    """
    threads = []
    emitted = []
    calls = {"run_prompt": 0}

    class _FakeThread:
        def __init__(self, target=None, daemon=None, **_thread_options):
            self.target = target
            threads.append(self)

        def start(self):
            return None

        def is_alive(self):
            return True

    session = _session()
    session["agent"] = None
    server._sessions["sid"] = session

    try:
        monkeypatch.setattr(server.threading, "Thread", _FakeThread)
        monkeypatch.setattr(server, "_emit", lambda *args, **kwargs: emitted.append(args))
        monkeypatch.setattr(server, "_ensure_session_db_row", lambda session: None)
        monkeypatch.setattr(server, "_persist_branch_seed", lambda session: None)
        monkeypatch.setattr(server, "_start_agent_build", lambda sid, session: None)
        monkeypatch.setattr(server, "_wait_agent", lambda session, rid: None)
        monkeypatch.setattr(
            server,
            "_run_prompt_submit",
            lambda *args, **kwargs: calls.__setitem__(
                "run_prompt", calls["run_prompt"] + 1
            ),
        )

        submit = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {"session_id": "sid", "text": "hello"},
            }
        )
        assert submit.get("result"), f"got error: {submit.get('error')}"
        assert session["running"] is True

        # User hits Stop while the agent is still building.
        stop = server.handle_request(
            {"id": "2", "method": "session.interrupt", "params": {"session_id": "sid"}}
        )
        assert stop.get("result"), f"got error: {stop.get('error')}"
        assert session.get("_turn_cancel_requested") is True

        # The deferred run thread now wakes up; without the emit it would bail
        # silently and the Desktop would never learn the turn was dropped.
        threads[0].target()

        assert calls["run_prompt"] == 0
        assert session["running"] is False
        assert session.get("inflight_turn") is None
        # Exactly one error event addressed to this session.
        error_events = [e for e in emitted if e and len(e) >= 2 and e[0] == "error" and e[1] == "sid"]
        assert len(error_events) == 1, f"expected one error event, got: {emitted}"
        msg = error_events[0][2].get("message", "")
        assert "cancelled" in msg.lower(), f"unexpected message: {msg}"
    finally:
        server._sessions.pop("sid", None)


def test_session_not_running_before_agent_ready_emits_error_event(monkeypatch):
    """When `running` is cleared by something other than an explicit interrupt
    (e.g. a concurrent session.create race that resets the flag), the deferred
    run thread must still emit an error event rather than disappearing silently.
    """
    threads = []
    emitted = []
    calls = {"run_prompt": 0}

    class _FakeThread:
        def __init__(self, target=None, daemon=None, **_thread_options):
            self.target = target
            threads.append(self)

        def start(self):
            return None

        def is_alive(self):
            return True

    session = _session()
    session["agent"] = None
    server._sessions["sid"] = session

    try:
        monkeypatch.setattr(server.threading, "Thread", _FakeThread)
        monkeypatch.setattr(server, "_emit", lambda *args, **kwargs: emitted.append(args))
        monkeypatch.setattr(server, "_ensure_session_db_row", lambda session: None)
        monkeypatch.setattr(server, "_persist_branch_seed", lambda session: None)
        monkeypatch.setattr(server, "_start_agent_build", lambda sid, session: None)
        monkeypatch.setattr(server, "_wait_agent", lambda session, rid: None)
        monkeypatch.setattr(
            server,
            "_run_prompt_submit",
            lambda *args, **kwargs: calls.__setitem__(
                "run_prompt", calls["run_prompt"] + 1
            ),
        )

        submit = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {"session_id": "sid", "text": "hello"},
            }
        )
        assert submit.get("result"), f"got error: {submit.get('error')}"
        assert session["running"] is True

        # Simulate a concurrent path clearing `running` without setting the
        # cancel flag (the other branch of the guard).
        with session["history_lock"]:
            session["running"] = False

        threads[0].target()

        assert calls["run_prompt"] == 0
        assert session.get("inflight_turn") is None
        error_events = [e for e in emitted if e and len(e) >= 2 and e[0] == "error" and e[1] == "sid"]
        assert len(error_events) == 1, f"expected one error event, got: {emitted}"
        msg = error_events[0][2].get("message", "")
        assert msg.strip(), f"empty error message: {emitted}"
    finally:
        server._sessions.pop("sid", None)


def test_slow_agent_build_delivers_prompt_instead_of_timing_out(monkeypatch):
    """#63078 server-side half: a deferred build slower than the old 30s
    ``_wait_agent`` cliff must NOT eat the first message. The patient wait
    keeps the pending prompt attached and delivers it as soon as the
    still-running build completes."""
    threads = []
    emitted = []
    calls = {"run_prompt": 0}

    class _FakeThread:
        def __init__(self, target=None, daemon=None, **_thread_options):
            self.target = target
            threads.append(self)

        def start(self):
            return None

        def is_alive(self):
            return True

    ready = threading.Event()
    session = _session(agent_ready=ready)
    session["agent"] = None
    server._sessions["sid"] = session

    # The build "completes" only after the wait loop has already gone through
    # several empty slices — i.e. well past what a single fixed-timeout wait
    # slice would tolerate.
    slices = {"n": 0}

    class _SlowReady:
        def wait(self, timeout=None):
            slices["n"] += 1
            if slices["n"] >= 3:
                ready.set()
                session["agent"] = types.SimpleNamespace()
                return True
            return False

        def is_set(self):
            return ready.is_set()

    session["agent_ready"] = _SlowReady()

    try:
        monkeypatch.setattr(server.threading, "Thread", _FakeThread)
        monkeypatch.setattr(server, "_emit", lambda *args, **kwargs: emitted.append(args))
        monkeypatch.setattr(server, "_ensure_session_db_row", lambda session: None)
        monkeypatch.setattr(server, "_persist_branch_seed", lambda session: None)
        monkeypatch.setattr(server, "_start_agent_build", lambda sid, session: None)
        monkeypatch.setattr(
            server,
            "_run_prompt_submit",
            lambda *args, **kwargs: calls.__setitem__(
                "run_prompt", calls["run_prompt"] + 1
            ),
        )

        submit = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {"session_id": "sid", "text": "first message"},
            }
        )
        assert submit.get("result"), f"got error: {submit.get('error')}"

        threads[0].target()

        # The message was DELIVERED, not dropped, and no error event fired.
        assert calls["run_prompt"] == 1
        error_events = [e for e in emitted if e and e[0] == "error"]
        assert not error_events, f"unexpected error events: {error_events}"
    finally:
        server._sessions.pop("sid", None)


def test_slow_agent_build_emits_keyed_progress_notice(monkeypatch):
    """Past the slow threshold the patient wait must tell the user once
    (keyed notification.show) and clear the notice when the build lands —
    a long wait is acceptable, a silent one is not."""
    threads = []
    emitted = []
    calls = {"run_prompt": 0}

    class _FakeThread:
        def __init__(self, target=None, daemon=None, **_thread_options):
            self.target = target
            threads.append(self)

        def start(self):
            return None

        def is_alive(self):
            return True

    ready = threading.Event()
    session = _session(agent_ready=ready)
    session["agent"] = None
    server._sessions["sid"] = session

    slices = {"n": 0}

    class _SlowReady:
        def wait(self, timeout=None):
            slices["n"] += 1
            if slices["n"] >= 3:
                ready.set()
                session["agent"] = types.SimpleNamespace()
                return True
            return False

        def is_set(self):
            return ready.is_set()

    session["agent_ready"] = _SlowReady()

    try:
        monkeypatch.setattr(server.threading, "Thread", _FakeThread)
        # Every wait slice lands past the slow threshold.
        monkeypatch.setattr(server, "_AGENT_BUILD_SLOW_NOTICE_AFTER", 0.0)
        monkeypatch.setattr(server, "_emit", lambda *args, **kwargs: emitted.append(args))
        monkeypatch.setattr(server, "_ensure_session_db_row", lambda session: None)
        monkeypatch.setattr(server, "_persist_branch_seed", lambda session: None)
        monkeypatch.setattr(server, "_start_agent_build", lambda sid, session: None)
        monkeypatch.setattr(
            server,
            "_run_prompt_submit",
            lambda *args, **kwargs: calls.__setitem__(
                "run_prompt", calls["run_prompt"] + 1
            ),
        )

        submit = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {"session_id": "sid", "text": "first message"},
            }
        )
        assert submit.get("result"), f"got error: {submit.get('error')}"

        threads[0].target()

        assert calls["run_prompt"] == 1
        shows = [e for e in emitted if e and e[0] == "notification.show" and e[1] == "sid"]
        clears = [e for e in emitted if e and e[0] == "notification.clear" and e[1] == "sid"]
        # Exactly one keyed notice, replaced-in-place semantics, then cleared.
        assert len(shows) == 1, f"expected one slow-build notice, got: {shows}"
        assert shows[0][2].get("key") == server._AGENT_BUILD_SLOW_NOTICE_KEY
        assert len(clears) == 1 and clears[0][2].get("key") == server._AGENT_BUILD_SLOW_NOTICE_KEY
    finally:
        server._sessions.pop("sid", None)


def test_agent_build_failure_surfaces_error_and_drops_turn(monkeypatch):
    """When the build itself FAILS (agent_error set when ready fires), the
    prompt must not run and the failure must reach the client as a visible
    error event — never a silent drop.

    prompt.submit retries a completed failed build once (fresh provider
    resolution un-wedges sessions whose failure cause was fixed), so the
    build stub here is a faithful failing build: it sets agent_error and
    fires the session's CURRENT ready event (the retry installs a new one).
    A no-op stub would leave that event unset and hang the patient wait."""
    threads = []
    emitted = []
    calls = {"run_prompt": 0}

    class _FakeThread:
        def __init__(self, target=None, daemon=None, **_thread_options):
            self.target = target
            threads.append(self)

        def start(self):
            return None

        def is_alive(self):
            return True

    ready = threading.Event()
    ready.set()  # build finished...
    session = _session(agent_ready=ready)
    session["agent"] = None
    session["agent_error"] = "No LLM provider configured"  # ...but failed
    server._sessions["sid"] = session

    def _failing_build(sid, session):
        session["agent_error"] = "No LLM provider configured"
        session["agent_ready"].set()

    try:
        monkeypatch.setattr(server.threading, "Thread", _FakeThread)
        monkeypatch.setattr(server, "_emit", lambda *args, **kwargs: emitted.append(args))
        monkeypatch.setattr(server, "_ensure_session_db_row", lambda session: None)
        monkeypatch.setattr(server, "_persist_branch_seed", lambda session: None)
        monkeypatch.setattr(server, "_start_agent_build", _failing_build)
        monkeypatch.setattr(
            server,
            "_run_prompt_submit",
            lambda *args, **kwargs: calls.__setitem__(
                "run_prompt", calls["run_prompt"] + 1
            ),
        )

        submit = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {"session_id": "sid", "text": "first message"},
            }
        )
        assert submit.get("result"), f"got error: {submit.get('error')}"

        threads[0].target()

        assert calls["run_prompt"] == 0
        assert session["running"] is False
        # #71184 upgraded failure delivery from a bare "error" event to a
        # terminal message.complete frame (status=error, recoverable) so
        # failed turns are retained as replayable inflight snapshots. The
        # contract this test pins is unchanged: the build failure must reach
        # the client VISIBLY — never a silent drop.
        failure_frames = [
            e
            for e in emitted
            if e
            and e[0] in ("error", "message.complete")
            and e[1] == "sid"
            and (
                "No LLM provider configured" in str(e[2].get("message", ""))
                or "No LLM provider configured" in str(e[2].get("error", ""))
                or "No LLM provider configured" in str(e[2].get("text", ""))
            )
        ]
        assert len(failure_frames) == 1, f"expected one visible failure frame, got: {emitted}"
        frame = failure_frames[0]
        if frame[0] == "message.complete":
            assert frame[2].get("status") == "error"
    finally:
        server._sessions.pop("sid", None)
