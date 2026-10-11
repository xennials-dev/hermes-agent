"""tui_gateway.server — session branching, model options and live prompt surfacing.

Split from test_tui_gateway_server.py; shared fixtures and helpers live
in tests/tui_gateway/_server_test_helpers.py.
"""

import contextlib
import logging
import os
import threading
import types
from unittest.mock import Mock, patch
from hermes_constants import reset_hermes_home_override, set_hermes_home_override
from tui_gateway import server

from tests.tui_gateway._server_test_helpers import (
    _ImmediateThread,
    _neuter_agent_prewarm_timer,  # autouse
    _reap_leaked_notification_pollers,  # autouse
    _session,
)


def test_session_history_ships_durable_row_ids(monkeypatch):
    """session.history must request row-id stamps — clients resolve truncation
    targets by content against this projection (#87059 client half)."""
    seen: dict = {}

    class _Db:
        def get_messages_as_conversation(self, _key, include_ancestors=False, include_row_ids=False, **_kwargs):
            seen["include_row_ids"] = include_row_ids

            return [
                {"role": "user", "content": "hello", "_row_id": 41},
                {"role": "assistant", "content": "hi"},
            ]

    server._sessions["rowid-hist-sid"] = {
        "session_key": "rowid-sess",
        "history": [],
        "history_lock": __import__("threading").Lock(),
        "running": False,
        "agent": None,
        "created_at": 1.0,
        "last_active": 1.0,
    }
    monkeypatch.setattr(server, "_get_db", lambda: _Db())
    try:
        resp = server.handle_request(
            {"id": "1", "method": "session.history", "params": {"session_id": "rowid-hist-sid"}}
        )
        assert "result" in resp, resp
        assert seen.get("include_row_ids") is True
        user_rows = [m for m in resp["result"]["messages"] if m.get("role") == "user"]
        assert user_rows and user_rows[0].get("row_id") == 41
    finally:
        server._sessions.pop("rowid-hist-sid", None)


def test_session_status_uses_session_profile_db(monkeypatch, tmp_path):
    """session.status must load meta from the session profile state.db."""
    profile_home = tmp_path / "profiles" / "mlperf"
    profile_home.mkdir(parents=True)
    seen: dict = {}

    class LaunchDB:
        def get_session(self, _key):
            seen["launch"] = True
            return {"id": _key, "title": "launch-title", "started_at": 1}

    class ProfileDB:
        def __init__(self, db_path=None):
            seen["db_path"] = db_path

        def get_session(self, _key):
            seen["profile"] = True
            return {"id": _key, "title": "profile-title", "started_at": 42}

        def close(self):
            seen["closed"] = True

    server._sessions["sid"] = {
        "session_key": "ml-sess",
        "history": [],
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
            {"id": "1", "method": "session.status", "params": {"session_id": "sid"}}
        )
        assert "result" in resp, resp
        assert "profile-title" in resp["result"]["output"]
        assert seen.get("profile") is True
        assert seen.get("launch") is None
    finally:
        server._sessions.pop("sid", None)


def test_teardown_ends_session_in_profile_db(monkeypatch, tmp_path):
    """_teardown_session must end_session on the profile store, not launch."""
    profile_home = tmp_path / "profiles" / "mlperf"
    profile_home.mkdir(parents=True)
    seen: dict = {}

    class LaunchDB:
        def get_session(self, _key):
            seen["launch"] = True
            return {"id": _key, "source": "tui"}

        def end_session(self, _key, _reason):
            seen["launch_end"] = True

    class ProfileDB:
        def __init__(self, db_path=None):
            seen["db_path"] = db_path

        def get_session(self, _key):
            seen["profile"] = True
            return {"id": _key, "source": "tui"}

        def end_session(self, key, reason):
            seen["ended"] = (key, reason)

        def close(self):
            seen["closed"] = True

    monkeypatch.setattr(server, "_get_db", lambda: LaunchDB())
    monkeypatch.setattr("hermes_state_registry.acquire", ProfileDB)
    session = {
        "session_key": "ml-sess",
        "profile_home": str(profile_home),
        "agent": None,
        "history": [],
        "source": "tui",
    }
    server._teardown_session(session, end_reason="closed")
    assert seen.get("ended") == ("ml-sess", "closed")
    assert seen.get("launch_end") is None
    assert seen.get("launch") is None
    assert str(seen.get("db_path")).endswith("state.db")


def test_session_branch_writes_to_parent_profile_db(monkeypatch, tmp_path):
    """session.branch must copy history into the parent's profile state.db."""
    profile_home = tmp_path / "profiles" / "mlperf"
    profile_home.mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    seen: dict = {"msgs": []}

    class LaunchDB:
        def get_session_title(self, _key):
            seen["launch"] = True
            return "L"

        def create_session(self, *a, **k):
            seen["launch_create"] = True

        def append_message(self, **k):
            seen["launch_msg"] = True

        def set_session_title(self, *a, **k):
            return True

    class ProfileDB:
        def __init__(self, db_path=None):
            seen["db_path"] = db_path
            seen.setdefault("inits", 0)
            seen["inits"] += 1

        def get_session_title(self, _key):
            return "parent"

        def get_next_title_in_lineage(self, current):
            return f"{current} (branch)"

        def create_session(self, new_key, **kwargs):
            seen["created"] = new_key
            seen["parent"] = kwargs.get("parent_session_id")
            seen["profile_name"] = kwargs.get("profile_name")

        def append_message(self, **kwargs):
            seen["msgs"].append(kwargs)

        def append_messages_batch(self, session_id, messages, **kwargs):
            for m in messages:
                seen["msgs"].append(dict(m, session_id=session_id))
            return list(range(1, len(messages) + 1))

        def set_session_title(self, key, title):
            seen["title"] = (key, title)
            return True

        def get_session(self, key):
            return {"id": key, "cwd": str(tmp_path)}

        def update_session_cwd(self, *a, **k):
            return None

        def close(self):
            seen["closed"] = True

    class FakeAgent:
        def __init__(self):
            self.model = "test-model"
            self.session_id = None

    parent = {
        "session_key": "parent-key",
        "history": [{"role": "user", "content": "hi"}],
        "history_lock": __import__("threading").Lock(),
        "running": False,
        "cols": 80,
        "profile_home": str(profile_home),
        "source": "tui",
        "agent": FakeAgent(),
        "created_at": 1.0,
        "last_active": 1.0,
        "cwd": str(tmp_path),
    }
    server._sessions["parent"] = parent
    monkeypatch.setattr(server, "_get_db", lambda: LaunchDB())
    monkeypatch.setattr("hermes_state_registry.acquire", ProfileDB)
    monkeypatch.setattr(server, "_claim_active_session_slot", lambda *a, **k: (None, None))

    def _fake_make_agent(*a, **k):
        seen["agent_session_db"] = k.get("session_db")
        seen["agent_cwd"] = k.get("cwd_override")
        return FakeAgent()

    monkeypatch.setattr(server, "_make_agent", _fake_make_agent)
    monkeypatch.setattr(server, "_set_session_context", lambda *a, **k: {})
    monkeypatch.setattr(server, "_clear_session_context", lambda *a, **k: None)
    monkeypatch.setattr(server, "_resolve_model", lambda: "test-model")
    monkeypatch.setattr(server, "_session_cwd", lambda s: str(tmp_path))
    monkeypatch.setattr(server, "_register_session_cwd", lambda *a, **k: None)
    monkeypatch.setattr(server, "_attach_worker", lambda *a, **k: None)
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.branch_whole",
                "params": {"session_id": "parent", "name": "forked"},
            }
        )
        assert "result" in resp, resp
        assert seen.get("created")
        assert seen.get("parent") == "parent-key"
        # The branch row is self-describing: stamped with the parent's owning
        # profile, not left NULL for aggregators to mis-tag as "default".
        assert seen.get("profile_name") == "mlperf"
        assert resp["result"].get("messages_omitted") is True
        assert "messages" not in resp["result"]
        assert seen.get("title") == (seen["created"], "forked")
        assert len(seen["msgs"]) == 1
        assert seen.get("launch") is None
        assert seen.get("launch_create") is None
        child_sid = resp["result"]["session_id"]
        assert server._sessions[child_sid]["profile_home"] == str(profile_home)
        # The branched AGENT must be bound to the parent profile's state.db —
        # not just the row. Otherwise its own flushes (and a later compression
        # rotation) land on the launch db, splitting the lineage again.
        assert isinstance(seen.get("agent_session_db"), ProfileDB)
        assert seen.get("agent_cwd") == str(tmp_path)
    finally:
        for k in list(server._sessions):
            server._sessions.pop(k, None)


def test_session_create_persists_seeded_branch_child(monkeypatch):
    """A desktop branch (session.create with parent_session_id + seeded
    messages) must persist its row + transcript immediately (#93959).

    The renderer re-fetches the fresh child via REST and defer_history
    hydration right after create; both read the DB. An unpersisted child
    404s/hydrates empty, the client fail-latch refuses to bind it, and the
    user gets an infinite spinner whose optimistic row vanishes on restart.
    """

    class _FakeAgent:
        def __init__(self):
            self.model = "test-model"

    seen: dict = {}

    class _FakeDB:
        def get_session_title(self, key):
            seen["parent_title"] = key
            return "My Parent Session"

        def get_next_title_in_lineage(self, current):
            return f"{current} #2"

        def create_session(self, key, **kwargs):
            seen["created"] = key
            seen["parent"] = kwargs.get("parent_session_id")
            seen["branched_from"] = (kwargs.get("model_config") or {}).get("_branched_from")

        def append_messages_batch(self, session_id, messages, **kwargs):
            seen["messages"] = list(messages)

        def set_auto_title(self, key, title, *, source):
            seen["title"] = title
            seen["title_source"] = source
            return True

    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    monkeypatch.setattr(server, "_make_agent", lambda sid, key, session_db=None, **_kw: _FakeAgent())
    monkeypatch.setattr(server, "_SlashWorker", lambda *a, **k: None)
    monkeypatch.setattr(server, "_session_info", lambda _a, *a2: {"model": "x"})
    monkeypatch.setattr(server, "_probe_credentials", lambda _a: None)
    monkeypatch.setattr(server, "_wire_callbacks", lambda _sid: None)
    monkeypatch.setattr(server, "_emit", lambda *a, **kw: None)

    import tools.approval as _approval

    monkeypatch.setattr(_approval, "register_gateway_notify", lambda key, cb: None)
    monkeypatch.setattr(_approval, "load_permanent_allowlist", lambda: None)

    seeded = [
        {"role": "user", "content": "hello from parent"},
        {"role": "assistant", "content": "parent reply"},
    ]

    resp = server.handle_request(
        {
            "id": "1",
            "method": "session.create",
            "params": {
                "cols": 96,
                "source": "desktop",
                "parent_session_id": "20260823_084113_6de211",
                "messages": seeded,
            },
        }
    )

    assert "result" in resp, resp
    key = resp["result"]["stored_session_id"]

    # Row persisted up front with lineage linkage and a lineage title —
    # not deferred to the first prompt.
    assert seen.get("created") == key
    assert seen.get("parent") == "20260823_084113_6de211"
    assert seen.get("branched_from") == "20260823_084113_6de211"
    assert seen.get("title") == "My Parent Session #2"
    assert seen.get("title_source") == "derived"

    # Seeded transcript copied into the durable row so REST prefetch and
    # defer_history hydration both find it immediately.
    assert len(seen.get("messages") or []) == 2
    assert seen["messages"][0]["content"] == "hello from parent"

    # The live record no longer queues the title — the DB already holds it.
    runtime_sid = resp["result"]["session_id"]
    assert server._sessions[runtime_sid]["pending_title"] is None

    server._sessions.pop(runtime_sid, None)


def test_session_branch_stored_copies_parent_history_without_returning_transcript(monkeypatch):
    """Whole-session desktop branches read the parent in the gateway, not in the renderer."""

    class _Scope:
        def __init__(self, db):
            self.db = db

        def __enter__(self):
            return self.db

        def __exit__(self, *_args):
            return False

    class _FakeDB:
        def get_resume_conversations(self, key):
            assert key == "parent"
            return [], [
                {"role": "user", "content": "first question", "timestamp": 1},
                {"role": "assistant", "content": "first answer", "timestamp": 2},
            ]

    class _FakeAgent:
        model = "test-model"

    seen: dict = {}
    db = _FakeDB()

    monkeypatch.setattr(server, "_profile_db", lambda _params: _Scope(db))
    monkeypatch.setattr(
        server,
        "_seed_branch_row",
        lambda _record, _key, _parent, history, *_args: seen.update(history=list(history)),
    )
    monkeypatch.setattr(server, "_make_agent", lambda *_args, **_kwargs: _FakeAgent())
    monkeypatch.setattr(server, "_session_info", lambda *_args: {"model": "test-model"})

    resp = server.handle_request(
        {
            "id": "1",
            "method": "session.branch_stored",
            "params": {
                "cols": 96,
                "parent_session_id": "parent",
                "source": "desktop",
            },
        }
    )

    assert "result" in resp, resp
    assert [message["content"] for message in seen["history"]] == ["first question", "first answer"]
    assert resp["result"]["message_count"] == 2
    assert resp["result"].get("messages_omitted") is True
    assert "messages" not in resp["result"]


def test_session_create_branch_seed_failure_does_not_break_create(monkeypatch):
    """Best-effort persistence: a broken DB must not fail session.create."""

    class _FakeAgent:
        def __init__(self):
            self.model = "test-model"

    class _BrokenDB:
        def get_session_title(self, key):
            raise RuntimeError("db down")

    monkeypatch.setattr(server, "_get_db", lambda: _BrokenDB())
    monkeypatch.setattr(server, "_make_agent", lambda sid, key, session_db=None, **_kw: _FakeAgent())
    monkeypatch.setattr(server, "_SlashWorker", lambda *a, **k: None)
    monkeypatch.setattr(server, "_session_info", lambda _a, *a2: {"model": "x"})
    monkeypatch.setattr(server, "_probe_credentials", lambda _a: None)
    monkeypatch.setattr(server, "_wire_callbacks", lambda _sid: None)
    monkeypatch.setattr(server, "_emit", lambda *a, **kw: None)

    import tools.approval as _approval

    monkeypatch.setattr(_approval, "register_gateway_notify", lambda key, cb: None)
    monkeypatch.setattr(_approval, "load_permanent_allowlist", lambda: None)

    resp = server.handle_request(
        {
            "id": "1",
            "method": "session.create",
            "params": {
                "source": "desktop",
                "parent_session_id": "parent-1",
                "messages": [{"role": "user", "content": "seed"}],
            },
        }
    )

    # Create itself still succeeds — the lazy first-prompt path remains as
    # the fallback for the seed.
    assert "result" in resp

    server._sessions.pop(resp["result"]["stored_session_id"], None)


def test_session_create_seed_failure_after_row_compensates(monkeypatch):
    """Partial-failure compensation (#93959 review): if the row commits but
    the transcript copy fails, the just-created child is DELETED so the lazy
    first-prompt fallback can retry cleanly. Without this, a durable empty
    row defeats _ensure_session_db_row's INSERT OR IGNORE and the renderer
    fail-latches on a transcript-less session again."""

    class _FakeAgent:
        def __init__(self):
            self.model = "test-model"

    seen: dict = {}

    class _FakeDB:
        def get_session_title(self, key):
            return "Parent"

        def get_next_title_in_lineage(self, current):
            return f"{current} #2"

        def create_session(self, key, **kwargs):
            seen["created"] = key

        def append_messages_batch(self, session_id, messages, **kwargs):
            raise RuntimeError("transcript write failed")

        def delete_session(self, session_id):
            seen["deleted"] = session_id
            return True

    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    monkeypatch.setattr(server, "_make_agent", lambda sid, key, session_db=None, **_kw: _FakeAgent())
    monkeypatch.setattr(server, "_SlashWorker", lambda *a, **k: None)
    monkeypatch.setattr(server, "_session_info", lambda _a, *a2: {"model": "x"})
    monkeypatch.setattr(server, "_probe_credentials", lambda _a: None)
    monkeypatch.setattr(server, "_wire_callbacks", lambda _sid: None)
    monkeypatch.setattr(server, "_emit", lambda *a, **kw: None)

    import tools.approval as _approval

    monkeypatch.setattr(_approval, "register_gateway_notify", lambda key, cb: None)
    monkeypatch.setattr(_approval, "load_permanent_allowlist", lambda: None)

    resp = server.handle_request(
        {
            "id": "1",
            "method": "session.create",
            "params": {
                "source": "desktop",
                "parent_session_id": "parent-1",
                "title": "My Branch",
                "messages": [{"role": "user", "content": "seed"}],
            },
        }
    )

    assert "result" in resp
    key = resp["result"]["stored_session_id"]
    # The half-written child was rolled back — no durable empty row left to
    # shadow the lazy seed path.
    assert seen.get("deleted") == key
    # pending_title survived: it still lands via the lazy post-turn apply.
    runtime_sid = resp["result"]["session_id"]
    assert server._sessions[runtime_sid]["pending_title"] == "My Branch"

    server._sessions.pop(runtime_sid, None)


def test_session_create_seed_disk_full_keeps_row_for_retry(monkeypatch):
    """Disk-full is NOT compensated: the row stays (deleting data on a full
    disk can make things worse), create still succeeds, and the failure is
    observable at warning level (#93959 review)."""

    import logging as _logging

    class _FakeAgent:
        def __init__(self):
            self.model = "test-model"

    class _FakeDB:
        def get_session_title(self, key):
            return "Parent"

        def get_next_title_in_lineage(self, current):
            return f"{current} #2"

        def create_session(self, key, **kwargs):
            pass

        def append_messages_batch(self, session_id, messages, **kwargs):
            raise OSError(28, "No space left on device")

    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    monkeypatch.setattr(server, "_make_agent", lambda sid, key, session_db=None, **_kw: _FakeAgent())
    monkeypatch.setattr(server, "_SlashWorker", lambda *a, **k: None)
    monkeypatch.setattr(server, "_session_info", lambda _a, *a2: {"model": "x"})
    monkeypatch.setattr(server, "_probe_credentials", lambda _a: None)
    monkeypatch.setattr(server, "_wire_callbacks", lambda _sid: None)
    monkeypatch.setattr(server, "_emit", lambda *a, **kw: None)

    import tools.approval as _approval

    monkeypatch.setattr(_approval, "register_gateway_notify", lambda key, cb: None)
    monkeypatch.setattr(_approval, "load_permanent_allowlist", lambda: None)

    records: list = []

    class _Capture(_logging.Handler):
        def emit(self, record):
            records.append(record)

    handler = _Capture(level=_logging.WARNING)
    root = _logging.getLogger()
    root.addHandler(handler)
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.create",
                "params": {
                    "source": "desktop",
                    "parent_session_id": "parent-1",
                    "messages": [{"role": "user", "content": "seed"}],
                },
            }
        )
    finally:
        root.removeHandler(handler)

    assert "result" in resp
    # The failure surfaced at WARNING (observable), not buried at debug.
    warnings = [r for r in records if r.levelno >= _logging.WARNING]
    assert warnings

    server._sessions.pop(resp["result"]["stored_session_id"], None)


def test_session_create_without_parent_still_defers_row(monkeypatch):
    """Plain drafts keep the lazy-row contract: no parent + no explicit branch
    intent means no eager persistence (the original draft-hygiene invariant)."""

    class _FakeAgent:
        def __init__(self):
            self.model = "test-model"

    calls: dict = {"create": 0}

    class _FakeDB:
        def create_session(self, *a, **k):
            calls["create"] += 1

    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())
    monkeypatch.setattr(server, "_make_agent", lambda sid, key, session_db=None, **_kw: _FakeAgent())
    monkeypatch.setattr(server, "_SlashWorker", lambda *a, **k: None)
    monkeypatch.setattr(server, "_session_info", lambda _a, *a2: {"model": "x"})
    monkeypatch.setattr(server, "_probe_credentials", lambda _a: None)
    monkeypatch.setattr(server, "_wire_callbacks", lambda _sid: None)
    monkeypatch.setattr(server, "_emit", lambda *a, **kw: None)

    import tools.approval as _approval

    monkeypatch.setattr(_approval, "register_gateway_notify", lambda key, cb: None)
    monkeypatch.setattr(_approval, "load_permanent_allowlist", lambda: None)

    resp = server.handle_request(
        {"id": "1", "method": "session.create", "params": {"cols": 80}}
    )
    sid = resp["result"]["session_id"]
    server._sessions[sid]["agent_ready"].wait(timeout=2.0)

    assert calls["create"] == 0, "plain drafts must not persist eagerly"

    server._sessions.pop(sid, None)


def test_session_branch_installs_parent_profile_secret_scope(monkeypatch, tmp_path):
    """The branched agent must be built under the parent profile's secrets.

    session.branch already binds the parent's HERMES_HOME and state.db, but the
    secret scope is what makes get_secret() resolve that profile's .env. Without
    it the build falls through to process os.environ — the LAUNCH profile's
    credentials — which is exactly the cross-profile resolution #67605 fixed for
    session.create / session.resume.
    """
    import threading

    from agent.secret_scope import current_secret_scope

    profile_home = tmp_path / "profiles" / "mlperf"
    profile_home.mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    (profile_home / ".env").write_text(
        "PROXMOX_TOKEN=mlperf-secret\n", encoding="utf-8"
    )
    seen: dict = {"msgs": []}

    class ProfileDB:
        def __init__(self, db_path=None):
            pass

        def get_session_title(self, _key):
            return "parent"

        def get_next_title_in_lineage(self, current):
            return f"{current} (branch)"

        def create_session(self, new_key, **kwargs):
            seen["created"] = new_key

        def append_message(self, **kwargs):
            seen["msgs"].append(kwargs)

        def append_messages_batch(self, session_id, messages, **kwargs):
            for m in messages:
                seen["msgs"].append(dict(m, session_id=session_id))
            return list(range(1, len(messages) + 1))

        def set_session_title(self, key, title):
            return True

        def get_session(self, key):
            return {"id": key, "cwd": str(tmp_path)}

        def update_session_cwd(self, *a, **k):
            return None

        def close(self):
            return None

    class FakeAgent:
        def __init__(self):
            self.model = "test-model"
            self.session_id = None

    parent = {
        "session_key": "parent-key",
        "history": [{"role": "user", "content": "hi"}],
        "history_lock": threading.Lock(),
        "running": False,
        "cols": 80,
        "profile_home": str(profile_home),
        "source": "tui",
        "agent": FakeAgent(),
        "created_at": 1.0,
        "last_active": 1.0,
        "cwd": str(tmp_path),
    }
    server._sessions["parent"] = parent
    monkeypatch.setattr(server, "_get_db", lambda: ProfileDB())
    monkeypatch.setattr("hermes_state_registry.acquire", ProfileDB)
    monkeypatch.setattr(server, "_claim_active_session_slot", lambda *a, **k: (None, None))

    def _fake_make_agent(*a, **k):
        scope = current_secret_scope()
        seen["scope"] = dict(scope) if scope else None
        return FakeAgent()

    monkeypatch.setattr(server, "_make_agent", _fake_make_agent)
    monkeypatch.setattr(server, "_set_session_context", lambda *a, **k: {})
    monkeypatch.setattr(server, "_clear_session_context", lambda *a, **k: None)
    monkeypatch.setattr(server, "_resolve_model", lambda: "test-model")
    monkeypatch.setattr(server, "_session_cwd", lambda s: str(tmp_path))
    monkeypatch.setattr(server, "_register_session_cwd", lambda *a, **k: None)
    monkeypatch.setattr(server, "_attach_worker", lambda *a, **k: None)
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.branch",
                "params": {"session_id": "parent", "name": "forked"},
            }
        )
        assert "result" in resp, resp
        assert seen.get("scope") == {"PROXMOX_TOKEN": "mlperf-secret"}
    finally:
        for k in list(server._sessions):
            server._sessions.pop(k, None)


def test_session_branch_uses_persisted_display_history_after_compaction(monkeypatch, tmp_path):
    """A live branch must copy the complete visible transcript, not the compacted model tail."""
    profile_home = tmp_path / "profiles" / "mlperf"
    profile_home.mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    seen: dict = {"msgs": []}

    display_history = [
        {"role": "user", "content": "first question", "timestamp": 1.0},
        {"role": "assistant", "content": "first answer", "timestamp": 2.0},
        {"role": "assistant", "content": "", "tool_calls": [{"id": "call-1"}]},
        {"role": "tool", "content": "tool output", "tool_call_id": "call-1"},
        {"role": "user", "content": "second question", "timestamp": 3.0},
        {"role": "assistant", "content": "second answer", "timestamp": 4.0},
    ]

    class LaunchDB:
        def get_session_title(self, _key):
            return "launch"

    class ProfileDB:
        def __init__(self, db_path=None):
            seen.setdefault("inits", 0)
            seen["inits"] += 1

        def get_session_title(self, _key):
            return "parent"

        def get_next_title_in_lineage(self, current):
            return f"{current} (branch)"

        def get_resume_conversations(self, key):
            assert key == "parent-key"
            # The model projection has already been compacted to a summary + tail;
            # the display projection still contains every visible turn.
            return (
                [{"role": "assistant", "content": "compact summary"}],
                display_history,
            )

        def create_session(self, _new_key, **_kwargs):
            return None

        def append_message(self, **kwargs):
            seen["msgs"].append(kwargs)

        def append_messages_batch(self, session_id, messages, **kwargs):
            for message in messages:
                seen["msgs"].append(dict(message, session_id=session_id))
            return list(range(1, len(messages) + 1))

        def set_session_title(self, _key, _title):
            return True

        def set_auto_title(self, _key, _title, *, source="llm"):
            seen["title_source"] = source
            return True

        def get_session(self, key):
            return {"id": key, "cwd": str(tmp_path)}

        def update_session_cwd(self, *args, **kwargs):
            return None

        def close(self):
            return None

    class FakeAgent:
        model = "test-model"
        session_id = None

    parent = {
        "session_key": "parent-key",
        # This is the model-fed projection after compaction: the old turns are
        # absent here even though the display projection above retains them.
        "history": [
            {"role": "assistant", "content": "compact summary"},
            {"role": "user", "content": "second question"},
            {"role": "assistant", "content": "second answer"},
        ],
        "history_lock": threading.Lock(),
        "running": False,
        "cols": 80,
        "profile_home": str(profile_home),
        "source": "tui",
        "agent": FakeAgent(),
        "created_at": 1.0,
        "last_active": 1.0,
        "cwd": str(tmp_path),
    }
    server._sessions["parent"] = parent
    monkeypatch.setattr(server, "_get_db", lambda: LaunchDB())
    monkeypatch.setattr("hermes_state_registry.acquire", ProfileDB)
    monkeypatch.setattr(server, "_claim_active_session_slot", lambda *args, **kwargs: (None, None))
    monkeypatch.setattr(server, "_make_agent", lambda *args, **kwargs: FakeAgent())
    monkeypatch.setattr(server, "_set_session_context", lambda *args, **kwargs: {})
    monkeypatch.setattr(server, "_clear_session_context", lambda *args, **kwargs: None)
    monkeypatch.setattr(server, "_resolve_model", lambda: "test-model")
    monkeypatch.setattr(server, "_session_cwd", lambda _session: str(tmp_path))
    monkeypatch.setattr(server, "_register_session_cwd", lambda *args, **kwargs: None)
    monkeypatch.setattr(server, "_attach_worker", lambda *args, **kwargs: None)

    try:
        response = server.handle_request(
            {
                "id": "1",
                "method": "session.branch",
                "params": {"session_id": "parent", "count": 4},
            }
        )

        assert "result" in response, response
        assert seen.get("title_source") == "derived"
        assert [message["content"] for message in seen["msgs"]] == [
            "first question",
            "first answer",
            "second question",
            "second answer",
        ]
        assert [message["text"] for message in response["result"]["messages"]] == [
            "first question",
            "first answer",
            "second question",
            "second answer",
        ]
    finally:
        for key in list(server._sessions):
            server._sessions.pop(key, None)


# --------------------------------------------------------------------------
# model.options — curated-list parity with `hermes model` and classic /model
# --------------------------------------------------------------------------


def test_model_options_does_not_overwrite_curated_models(monkeypatch):
    """The TUI model.options handler must surface the same curated model
    list as `hermes model` and the classic CLI /model picker.

    Regression: earlier versions of this handler unconditionally replaced
    each provider's curated ``models`` field with ``provider_model_ids()``
    (live /models catalog).  That pulled in hundreds of non-agentic models
    for providers like Nous whose /models endpoint returns image/video
    generators, rerankers, embeddings, and TTS models alongside chat models.
    """
    curated_providers = [
        {
            "slug": "nous",
            "name": "Nous",
            "models": ["moonshotai/kimi-k2.5", "anthropic/claude-opus-4.7"],
            "total_models": 30,
            "source": "built-in",
            "is_current": False,
            "is_user_defined": False,
        },
    ]

    monkeypatch.setattr(
        server,
        "_load_cfg",
        lambda: {"providers": {}, "custom_providers": []},
    )

    with patch(
        "hermes_cli.model_switch.list_authenticated_providers",
        return_value=curated_providers,
    ):
        # If provider_model_ids gets called at all, the handler is still
        # overwriting curated with live — that's the regression we're
        # guarding against.
        with patch("hermes_cli.models.provider_model_ids") as live_fetch:
            resp = server._methods["model.options"](99, {"session_id": ""})

    assert "result" in resp, resp
    providers = resp["result"]["providers"]
    nous = next((p for p in providers if p.get("slug") == "nous"), None)
    assert nous is not None
    assert nous["models"] == [
        "moonshotai/kimi-k2.5",
        "anthropic/claude-opus-4.7",
    ]
    assert nous["total_models"] == 30
    # Handler must not consult the live catalog — curated is the truth.
    live_fetch.assert_not_called()


def test_model_options_propagates_list_exception(monkeypatch):
    """If list_authenticated_providers itself raises, surface as an RPC
    error rather than swallowing to a blank picker."""
    monkeypatch.setattr(
        server,
        "_load_cfg",
        lambda: {"providers": {}, "custom_providers": []},
    )
    with patch(
        "hermes_cli.model_switch.list_authenticated_providers",
        side_effect=RuntimeError("catalog blew up"),
    ):
        resp = server._methods["model.options"](77, {"session_id": ""})
    assert "error" in resp
    assert resp["error"]["code"] == 5033
    assert "catalog blew up" in resp["error"]["message"]


def test_model_options_preserves_canonical_custom_row_after_agent_init(monkeypatch):
    from hermes_cli.inventory import ConfigContext

    class _Agent:
        provider = "custom"
        model = "qwen3.6:35b-65k"
        base_url = "http://127.0.0.1:11434/v1"

    server._sessions["custom-session"] = _session(agent=_Agent())
    monkeypatch.setattr(server, "_resolve_model", lambda: "")
    monkeypatch.setattr(
        "hermes_cli.inventory.load_picker_context",
        lambda: ConfigContext(
            current_provider="custom:local-ollama",
            current_model="qwen3.6:35b-65k",
            current_base_url="http://127.0.0.1:11434/v1",
            user_providers={},
            custom_providers=[],
        ),
    )
    canonical = Mock(return_value="custom:local-ollama")
    monkeypatch.setattr(
        "hermes_cli.runtime_provider.canonical_custom_identity",
        canonical,
    )
    monkeypatch.setattr(
        "hermes_cli.model_switch.list_authenticated_providers",
        lambda **_kwargs: [
            {
                "slug": "custom:local-ollama",
                "name": "Local Ollama",
                "is_current": True,
                "is_user_defined": True,
                "models": ["qwen3.6:35b-65k"],
                "total_models": 1,
            },
            {
                "slug": "anthropic",
                "name": "Anthropic",
                "is_current": False,
                "is_user_defined": False,
                "models": ["claude-sonnet-4.6"],
                "total_models": 1,
            },
        ],
    )
    monkeypatch.setattr(
        "hermes_cli.auth.is_provider_explicitly_configured",
        lambda _slug: False,
    )
    monkeypatch.setattr("hermes_cli.inventory._apply_pricing", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("hermes_cli.inventory._apply_capabilities", lambda *_args, **_kwargs: None)

    resp = server._methods["model.options"](
        102,
        {"session_id": "custom-session", "explicit_only": True},
    )

    assert "result" in resp, resp
    assert resp["result"]["provider"] == "custom:local-ollama"
    assert [row["slug"] for row in resp["result"]["providers"]] == [
        "custom:local-ollama"
    ]


def test_model_save_key_uses_credential_lifecycle_and_picker_context(monkeypatch):
    env_var = "TEST_PROVIDER_API_KEY"
    agent = object()
    picker_ctx = object()
    provider = {
        "slug": "test-provider",
        "name": "Test Provider",
        "models": ["test-model"],
        "total_models": 1,
    }
    server._sessions["save-key-session"] = _session(agent=agent)
    monkeypatch.setattr(
        "hermes_cli.auth.PROVIDER_REGISTRY",
        {
            "test-provider": types.SimpleNamespace(
                name="Test Provider",
                auth_type="api_key",
                api_key_env_vars=(env_var,),
            )
        },
    )
    monkeypatch.setattr("hermes_cli.config.is_managed", lambda: False)
    save_credential = Mock()
    monkeypatch.setattr(
        "hermes_cli.credential_lifecycle.save_provider_env_credential",
        save_credential,
    )
    picker_context = Mock(return_value=picker_ctx)
    monkeypatch.setattr(server, "_model_picker_context", picker_context)
    build_payload = Mock(return_value={"providers": [provider]})
    monkeypatch.setattr(
        "hermes_cli.inventory.build_models_payload",
        build_payload,
    )
    monkeypatch.setenv(env_var, "previous-value")
    fake_key = "replacement-" + "value"

    resp = server._methods["model.save_key"](
        103,
        {
            "slug": "test-provider",
            "api_key": fake_key,
            "session_id": "save-key-session",
        },
    )

    assert "result" in resp, resp
    assert resp["result"]["provider"] == {**provider, "authenticated": True}
    save_credential.assert_called_once_with(env_var, fake_key)


def test_model_save_key_reconciles_the_launch_profiles_stale_setup_record(monkeypatch, tmp_path):
    """The gated picker's own chat waits on ``setup.status``, which answers from the boot record:
    a key saved for the launch profile must flip a ``False`` record (+ ``setup.ready``) at once;
    a key saved for another profile (``profile`` param) must leave the launch record alone."""
    from hermes_cli import free_tier_bootstrap as fb

    monkeypatch.setattr("hermes_cli.auth.PROVIDER_REGISTRY", {"test-provider": types.SimpleNamespace(
        name="Test Provider", auth_type="api_key", api_key_env_vars=("TEST_PROVIDER_API_KEY",))})
    monkeypatch.setattr("hermes_cli.config.is_managed", lambda: False)
    monkeypatch.setattr("hermes_cli.credential_lifecycle.save_provider_env_credential", Mock())
    monkeypatch.setattr("hermes_cli.inventory.build_models_payload", Mock(return_value={"providers": []}))
    monkeypatch.setenv("TEST_PROVIDER_API_KEY", "previous-value")  # save_key exports the new key
    monkeypatch.setattr(fb, "_inventory_other_providers", lambda: True)
    monkeypatch.setattr(fb, "_resolve_inference", lambda: "test-provider")
    broadcasts = []
    monkeypatch.setattr(fb, "_broadcast", broadcasts.append)
    other_home = tmp_path / "profiles" / "other"  # model.save_key is profile scoped: "other" must exist
    other_home.mkdir(parents=True)
    monkeypatch.setattr(server, "_profile_home", lambda name: other_home if name == "other" else None)
    fb.reset_for_tests()
    stale = fb.SetupRecord(provider_configured=False, inference_provider="", free_tier=False,
                           has_identity=False, other_providers=False)
    with fb._lock:
        fb._record, fb._started = stale, True
        fb._done.set()
    try:
        params = {"slug": "test-provider", "api_key": "k-" + "1"}
        assert "result" in server._methods["model.save_key"](104, {**params, "profile": "other"})
        assert fb.current_record() is stale and broadcasts == [], "another profile's key is not ours"
        assert "result" in server._methods["model.save_key"](105, params)
        record = fb.current_record()
        assert record.provider_configured is True and record.inference_provider == "test-provider"
        assert broadcasts == [record]
    finally:
        fb.reset_for_tests()


# ---------------------------------------------------------------------------
# prompt.submit — auto-title
# ---------------------------------------------------------------------------




def test_prompt_submit_releases_old_history_before_heap_trim(monkeypatch, tmp_path):
    """The post-turn heap trim must run after the turn's pre-turn history snapshots are dropped:
    malloc_trim cannot return pages still referenced, so a retained snapshot of a large tool
    result pins them for the life of the process. Observed through a weak reference to the old
    message, not by reading the finisher's local variable names."""
    import contextlib
    import gc
    import weakref

    class _Msg(dict):
        """dict itself is not weakref-able."""

    observed = {}
    order = []

    class _Agent:
        def run_conversation(self, prompt, conversation_history=None, stream_callback=None, **_kw):
            return {"final_response": "reply", "messages": [{"role": "assistant", "content": "reply"}]}

    def _trim(**_kwargs):
        order.append("trim")
        gc.collect()
        observed["alive_at_trim"] = old_ref() is not None

    old = _Msg(role="tool", tool_call_id="old", content="x" * 20_000)
    old_ref = weakref.ref(old)
    session = _session(agent=_Agent())
    profile_home = tmp_path / "profiles" / "worker"
    profile_home.mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    session["profile_home"] = str(profile_home)
    session["history"] = [old]
    del old
    server._sessions["sid_trim"] = session
    try:
        monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)
        monkeypatch.setattr(server, "_get_usage", lambda _a: {})
        monkeypatch.setattr(server, "render_message", lambda _t, _c: "")
        monkeypatch.setattr(server, "_emit", lambda *a: None)
        monkeypatch.setattr(server, "set_hermes_home_override", lambda _home: object())
        monkeypatch.setattr(server, "reset_hermes_home_override", lambda _token: order.append("reset_home"))
        monkeypatch.setattr(server, "_session_profile_runtime_scope", lambda _session, **_kw: contextlib.nullcontext())
        monkeypatch.setattr("hermes_cli.mem_trim.trim_memory", _trim)

        resp = server.handle_request(
            {"id": "1", "method": "prompt.submit", "params": {"session_id": "sid_trim", "text": "hi"}})

        assert resp is not None and resp.get("result")
        assert order == ["trim", "reset_home"]
        assert observed["alive_at_trim"] is False, "a pre-turn history snapshot survived to the heap trim"
    finally:
        server._sessions.pop("sid_trim", None)


def test_prompt_submit_wires_live_title_rename_callback(monkeypatch):
    """The gateway hands the agent a hook so a new title repaints the sidebar.

    Titling itself moved into the shared turn prologue (agent/turn_context.py),
    so the gateway's only remaining job is delivering the rename event. Asserted
    by calling the hook the gateway installed and checking what it emits.
    """

    class _Agent:
        model = "gpt-5.6-sol"
        provider = "openai-codex"
        base_url = "https://chatgpt.example.test/backend-api/codex"
        api_key = object()
        api_mode = "codex_responses"

        def run_conversation(self, prompt, conversation_history=None, stream_callback=None, **_kwargs):
            return {
                "final_response": "Rome was founded in 753 BC.",
                "messages": [
                    {"role": "user", "content": "Tell me about Rome"},
                    {"role": "assistant", "content": "Rome was founded in 753 BC."},
                ],
            }

    agent = _Agent()
    server._sessions["sid"] = _session(agent=agent)
    emitted = []
    monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)
    monkeypatch.setattr(
        server, "_emit", lambda kind, sid, payload=None, **kw: emitted.append((kind, payload))
    )
    monkeypatch.setattr(server, "make_stream_renderer", lambda cols: None)
    monkeypatch.setattr(server, "render_message", lambda raw, cols: None)
    monkeypatch.setattr(server, "_get_db", lambda: None)

    server.handle_request(
        {
            "id": "1",
            "method": "prompt.submit",
            "params": {"session_id": "sid", "text": "Tell me about Rome"},
        }
    )

    hook = getattr(agent, "_on_session_title", None)
    assert callable(hook), "gateway did not install a live title-rename hook"
    # Titling is two-stage, and a local surface wants both: the sidebar renames
    # off the derived slice instantly and sharpens when the model's lands. Only
    # the lanes that spend a rate-limited remote rename filter by stage.
    hook("tell me about rome", "derived")
    hook("Founding of Rome", "llm")
    assert [payload["title"] for kind, payload in emitted if kind == "session.title"] == [
        "tell me about rome",
        "Founding of Rome",
    ]
    assert (
        "session.title",
        {"session_id": "session-key", "title": "Founding of Rome"},
    ) in emitted


def test_prompt_submit_surfaces_backend_error_as_visible_text(monkeypatch):
    """When the backend fails with no visible response (e.g. invalid model slug
    → provider 4xx), the TUI must surface result['error'] as visible text
    instead of emitting a blank message.complete turn."""

    class _Agent:
        def run_conversation(self, prompt, conversation_history=None, stream_callback=None, **_kwargs):
            return {
                "final_response": None,
                "messages": [],
                "api_calls": 0,
                "completed": False,
                "failed": True,
                "error": "HTTP 400: invalid model id 'kimi-k2.6'",
            }

    server._sessions["sid"] = _session(agent=_Agent())
    monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)

    emitted: list[tuple[str, str, dict]] = []
    monkeypatch.setattr(
        server,
        "_emit",
        lambda event, sid, payload=None: emitted.append((event, sid, payload or {})),
    )
    monkeypatch.setattr(server, "make_stream_renderer", lambda cols: None)
    monkeypatch.setattr(server, "render_message", lambda raw, cols: None)
    monkeypatch.setattr(server, "_get_db", lambda: None)

    server.handle_request(
        {
            "id": "1",
            "method": "prompt.submit",
            "params": {"session_id": "sid", "text": "hello"},
        }
    )

    complete_events = [e for e in emitted if e[0] == "message.complete"]
    assert complete_events, "expected message.complete to be emitted"
    payload = complete_events[-1][2]
    assert payload.get("status") == "error"
    text = payload.get("text", "")
    assert "invalid model id 'kimi-k2.6'" in text
    assert payload.get("error") == "HTTP 400: invalid model id 'kimi-k2.6'"


def test_prompt_submit_preserves_empty_response_without_error(monkeypatch):
    """An empty final_response with NO backend error must stay empty — do not
    synthesize an error string. Preserves the existing None/empty-sentinel
    semantics owned by downstream handlers."""

    class _Agent:
        def run_conversation(self, prompt, conversation_history=None, stream_callback=None, **_kwargs):
            return {
                "final_response": None,
                "messages": [],
                "api_calls": 1,
                "completed": True,
            }

    server._sessions["sid"] = _session(agent=_Agent())
    monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)

    emitted: list[tuple[str, str, dict]] = []
    monkeypatch.setattr(
        server,
        "_emit",
        lambda event, sid, payload=None: emitted.append((event, sid, payload or {})),
    )
    monkeypatch.setattr(server, "make_stream_renderer", lambda cols: None)
    monkeypatch.setattr(server, "render_message", lambda raw, cols: None)
    monkeypatch.setattr(server, "_get_db", lambda: None)

    server.handle_request(
        {
            "id": "1",
            "method": "prompt.submit",
            "params": {"session_id": "sid", "text": "hello"},
        }
    )

    complete_events = [e for e in emitted if e[0] == "message.complete"]
    assert complete_events, "expected message.complete to be emitted"
    payload = complete_events[-1][2]
    # Status stays "complete" because no error flag was set
    assert payload.get("status") == "complete"
    # Text stays empty — we did NOT fabricate an "Error:" string
    text = payload.get("text", "")
    assert text in {"", None}, f"expected empty text, got {text!r}"


# ── active live TUI sessions ─────────────────────────────────────────


def test_session_active_list_reports_live_sessions(monkeypatch):
    class _DB:
        def get_session_title(self, key):
            return {"key-a": "Research", "key-b": "Implement"}.get(key, "")

    previous_sessions = dict(server._sessions)
    server._sessions.clear()
    monkeypatch.setattr(server, "_get_db", lambda: _DB())
    server._sessions["sid-a"] = _session(
        agent=types.SimpleNamespace(model="model-a"),
        history=[{"role": "user", "content": "find docs"}],
        session_key="key-a",
        created_at=10.0,
        last_active=20.0,
    )
    server._sessions["sid-b"] = _session(
        agent=types.SimpleNamespace(model="model-b"),
        history=[{"role": "assistant", "content": "writing code"}],
        running=True,
        session_key="key-b",
        created_at=11.0,
        last_active=30.0,
    )
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.active_list",
                "params": {"current_session_id": "sid-b"},
            }
        )
    finally:
        server._sessions.clear()
        server._sessions.update(previous_sessions)

    session_rows = resp["result"]["sessions"]
    assert [row["id"] for row in session_rows] == ["sid-a", "sid-b"]

    rows = {row["id"]: row for row in session_rows}
    assert rows["sid-a"] == {
        "current": False,
        "id": "sid-a",
        "last_active": 20.0,
        "message_count": 1,
        "model": "model-a",
        "preview": "find docs",
        "session_key": "key-a",
        "started_at": 10.0,
        "status": "idle",
        "title": "Research",
    }
    assert rows["sid-b"]["current"] is True
    assert rows["sid-b"]["status"] == "working"
    assert rows["sid-b"]["title"] == "Implement"
    assert rows["sid-b"]["preview"] == "writing code"


def test_session_active_list_excludes_finalized_sessions(monkeypatch):
    """#38950: a finalized-but-not-yet-popped session must not inflate the count.

    The WS grace-reap and idle reaper set ``_finalized`` inside
    ``_teardown_session`` before popping the entry from ``_sessions``. During
    that window ``session.active_list`` would otherwise still report the dead
    session, which is exactly the footer "N sessions" count that only ever grew
    until a gateway restart. A live session on the real stdio transport (the
    standalone ``hermes --tui`` case) must still be reported.
    """
    class _DB:
        def get_session_title(self, key):
            return {"key-live": "Live", "key-dead": "Dead"}.get(key, "")

    previous_sessions = dict(server._sessions)
    server._sessions.clear()
    monkeypatch.setattr(server, "_get_db", lambda: _DB())
    server._sessions["sid-live"] = _session(
        agent=types.SimpleNamespace(model="model-live"),
        history=[{"role": "user", "content": "still here"}],
        session_key="key-live",
        created_at=10.0,
        last_active=20.0,
    )
    dead = _session(
        agent=types.SimpleNamespace(model="model-dead"),
        history=[{"role": "user", "content": "gone"}],
        session_key="key-dead",
        created_at=11.0,
        last_active=21.0,
    )
    dead["_finalized"] = True
    server._sessions["sid-dead"] = dead
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.active_list",
                "params": {},
            }
        )
    finally:
        server._sessions.clear()
        server._sessions.update(previous_sessions)

    session_rows = resp["result"]["sessions"]
    assert [row["id"] for row in session_rows] == ["sid-live"]
