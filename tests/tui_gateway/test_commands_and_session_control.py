"""tui_gateway.server — commands catalog, session control RPCs, steer and redirect.

Split from test_tui_gateway_server.py; shared fixtures and helpers live
in tests/tui_gateway/_server_test_helpers.py.
"""

import json
import subprocess
import sys
import threading
import types
from pathlib import Path
from unittest.mock import Mock
from tui_gateway import server

from tests.tui_gateway._server_test_helpers import (
    _ImmediateThread,
    _RecordingSteerAgent,
    _neuter_agent_prewarm_timer,  # autouse
    _reap_leaked_notification_pollers,  # autouse
    _session,
)


def test_file_attach_workspace_storage_falls_back_for_non_local_workspace(monkeypatch, tmp_path):
    """Workspace storage only applies to a workspace on THIS host.

    A session bound to a remote cwd (ssh profile) can't be written from the
    gateway; those attachments keep the bind-mounted ``<profile home>/attachments``
    so container/remote backends still receive them (#76577).
    """
    home = tmp_path / "home"
    home.mkdir()
    (home / "config.yaml").write_text("attachments:\n  storage: workspace\n", encoding="utf-8")
    remote_cwd = str(tmp_path / "remote-host" / "agent-a")  # does not exist here
    fake_cli = types.ModuleType("cli")
    fake_cli._detect_file_drop = lambda raw: None
    fake_cli._split_path_input = lambda raw: (raw, "")
    fake_cli._resolve_attachment_path = lambda raw: None
    monkeypatch.setitem(sys.modules, "cli", fake_cli)

    server._sessions["sid"] = _session(cwd=remote_cwd, profile_home=str(home))

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "file.attach",
                "params": {
                    "session_id": "sid",
                    "path": "/Users/alice/Downloads/report.txt",
                    "name": "report.txt",
                    "data_url": "data:text/plain;base64,aGVsbG8=",
                },
            }
        )

        stored = home / "attachments" / "report.txt"
        assert resp["result"]["attached"] is True
        assert resp["result"]["path"] == str(stored)
        assert stored.read_text(encoding="utf-8") == "hello"
    finally:
        server._sessions.pop("sid", None)


def test_commands_catalog_surfaces_quick_commands(monkeypatch):
    monkeypatch.setattr(
        server,
        "_load_cfg",
        lambda: {
            "quick_commands": {
                "build": {"type": "exec", "command": "npm run build"},
                "git": {"type": "alias", "target": "/shell git"},
                "notes": {
                    "type": "exec",
                    "command": "cat NOTES.md",
                    "description": "Open design notes",
                },
            }
        },
    )

    resp = server.handle_request(
        {"id": "1", "method": "commands.catalog", "params": {}}
    )

    pairs = dict(resp["result"]["pairs"])
    assert "npm run build" in pairs["/build"]
    assert pairs["/git"].startswith("alias →")
    assert pairs["/notes"] == "Open design notes"

    user_cat = next(
        c for c in resp["result"]["categories"] if c["name"] == "User commands"
    )
    user_pairs = dict(user_cat["pairs"])
    assert set(user_pairs) == {"/build", "/git", "/notes"}

    assert resp["result"]["canon"]["/build"] == "/build"
    assert resp["result"]["canon"]["/notes"] == "/notes"


def test_commands_catalog_ranks_skill_commands_by_recorded_usage(monkeypatch):
    """Skill entries carry the usage + origin the `/` menu ranks on.

    Without it the menu is alphabetical, so a bundled skill the user has never
    opened outranks the one they invoke daily.
    """
    monkeypatch.setattr(
        server,
        "_skill_usage_lookup",
        lambda: (
            lambda name: {"research": 60, "work": 172}.get(name, 0),
            lambda name: "bundled" if name == "research-paper-writing" else "local",
        ),
    )
    monkeypatch.setattr(
        "agent.skill_commands.scan_skill_commands",
        lambda: {
            "/research": {"name": "research", "description": "Look it up"},
            "/research-paper-writing": {
                "name": "research-paper-writing",
                "description": "Write a paper",
            },
            "/work": {"name": "work", "description": "Fresh worktree"},
        },
    )

    resp = server.handle_request(
        {"id": "1", "method": "commands.catalog", "params": {}}
    )

    skills = resp["result"]["skills"]
    assert skills["/work"] == {"usage": 172, "origin": "local"}
    assert skills["/research"] == {"usage": 60, "origin": "local"}
    assert skills["/research-paper-writing"] == {"usage": 0, "origin": "bundled"}

    # Every advertised skill command is rankable — a missing entry silently
    # sorts that skill to the bottom of the menu.
    advertised = {name for name, _ in resp["result"]["pairs"]}
    assert set(skills) <= advertised
    assert resp["result"]["skill_count"] == len(skills)


def test_commands_catalog_survives_an_unreadable_usage_sidecar(monkeypatch):
    """A broken/absent .usage.json degrades to no ranking, never a broken menu."""
    monkeypatch.setattr(
        "tools.skill_usage.load_usage",
        lambda: (_ for _ in ()).throw(OSError("sidecar is gone")),
    )

    resp = server.handle_request(
        {"id": "1", "method": "commands.catalog", "params": {}}
    )

    assert "error" not in resp
    assert all(
        entry == {"usage": 0, "origin": "local"}
        for entry in resp["result"]["skills"].values()
    )


def test_commands_catalog_has_no_duplicate_or_alias_colliding_names():
    """No command may be advertised twice, and no advertised command may
    shadow an alias of a different command (e.g. the historical /compact
    collision where the registry aliased compact -> compress while the TUI
    also registered its own /compact display toggle; see #57133)."""
    resp = server.handle_request(
        {"id": "1", "method": "commands.catalog", "params": {}}
    )

    names = [name for name, _ in resp["result"]["pairs"]]
    dupes = {n for n in names if names.count(n) > 1}
    assert not dupes, f"duplicate commands advertised in catalog: {sorted(dupes)}"

    canon = resp["result"]["canon"]
    colliding = {
        name
        for name in names
        if canon.get(name.lower(), name) != name
    }
    assert not colliding, (
        f"catalog commands shadow aliases of other commands: {sorted(colliding)}"
    )


def test_commands_catalog_filters_gateway_only_commands_and_keeps_status_visible():
    resp = server.handle_request(
        {"id": "1", "method": "commands.catalog", "params": {}}
    )

    pairs = dict(resp["result"]["pairs"])
    canon = resp["result"]["canon"]

    assert "/status" in pairs
    assert canon["/status"] == "/status"
    assert "/approvals" in pairs

    assert "/topic" not in pairs
    assert "/approve" not in pairs
    assert "/deny" not in pairs
    assert "/sethome" not in pairs

    assert "/update" in pairs
    assert canon["/update"] == "/update"

    assert "/topic" not in canon
    assert "/approve" not in canon
    assert "/deny" not in canon
    assert "/set-home" not in canon


def test_commands_catalog_includes_desktop_meta_without_skills():
    resp = server.handle_request(
        {"id": "1", "method": "commands.catalog", "params": {}}
    )

    commands = resp["result"]["commands"]
    assert commands["/compact"]["argument_mode"] == commands["/compress"]["argument_mode"]

    for skill in resp["result"]["skills"]:
        assert skill not in commands


def test_commands_catalog_includes_plugin_commands(monkeypatch):
    monkeypatch.setattr(
        "hermes_cli.plugins.get_plugin_commands",
        lambda: {
            "lcm": {
                "description": "Latent consistency",
                "args_hint": "<prompt>",
                "argument_mode": "text",
            }
        },
    )

    resp = server.handle_request(
        {"id": "1", "method": "commands.catalog", "params": {}}
    )

    assert resp["result"]["commands"]["/lcm"] == {
        "argument_mode": "text",
        "desktop": None,
    }
    pairs = dict(resp["result"]["pairs"])
    assert "/lcm" in pairs
    plugin_cat = next(
        c for c in resp["result"]["categories"] if c["name"] == "Plugin commands"
    )
    assert "/lcm" in dict(plugin_cat["pairs"])


def test_plugin_slash_command_runs_under_the_session_env(monkeypatch):
    # TUI/Desktop sibling of #108698: command.dispatch and slash.exec ran plugin handlers on the RPC
    # thread with no HERMES_SESSION_* binding, so a handler reading get_session_env() saw "" (or the
    # launch process's inherited values) instead of the session it was invoked from.
    from gateway.session_context import get_session_env

    seen = {}

    def handler(arg):
        seen["key"] = get_session_env("HERMES_SESSION_KEY")
        return f"ok:{arg}"

    monkeypatch.setattr("hermes_cli.plugins.get_plugin_command_handler",
                        lambda name: handler if name == "whoami" else None)
    monkeypatch.setattr(server, "_sessions", {"sid-p": {"session_key": "agent:tui:key-p", "cwd": ""}})

    res = server._methods["command.dispatch"]("d", {"name": "whoami", "arg": "x", "session_id": "sid-p"})

    assert res["result"] == {"type": "plugin", "output": "ok:x"}
    assert seen["key"] == "agent:tui:key-p"
    # Nothing leaks past the RPC.
    assert get_session_env("HERMES_SESSION_KEY") in ("", None)


def test_session_status_reads_live_gateway_agent(monkeypatch):
    agent = types.SimpleNamespace(
        model="live-model",
        provider="live-provider",
        session_total_tokens=1234,
    )
    server._sessions["sid"] = _session(agent=agent, running=True)

    class _DB:
        def get_session(self, key):
            assert key == "session-key"
            return {
                "title": "Live TUI",
                "started_at": 1_700_000_000,
                "updated_at": 1_700_000_060,
            }

    monkeypatch.setattr(server, "_get_db", lambda: _DB())
    try:
        resp = server.handle_request(
            {"id": "1", "method": "session.status", "params": {"session_id": "sid"}}
        )
    finally:
        server._sessions.pop("sid", None)

    out = resp["result"]["output"]
    for value in ("session-key", "Live TUI", "live-model", "live-provider", "1,234"):
        assert value in out


def test_session_status_reads_live_compute_host_metadata(monkeypatch):
    agent = types.SimpleNamespace(
        model="stale-gateway-model",
        provider="stale-gateway-provider",
    )
    server._sessions["sid"] = _session(
        agent=agent,
        _compute_host_active=True,
        _metadata_mirror={
            "model": "live-host-model",
            "provider": "live-host-provider",
        },
    )
    monkeypatch.setattr(server, "_get_db", lambda: None)

    try:
        resp = server.handle_request(
            {"id": "1", "method": "session.status", "params": {"session_id": "sid"}}
        )
    finally:
        server._sessions.pop("sid", None)

    assert "Model: live-host-model (live-host-provider)" in resp["result"]["output"]


def test_session_status_falls_back_to_agent_before_first_host_frame(monkeypatch):
    agent = types.SimpleNamespace(model="live-model", provider="live-provider")
    server._sessions["sid"] = _session(agent=agent, _compute_host_active=True)
    monkeypatch.setattr(server, "_get_db", lambda: None)

    try:
        resp = server.handle_request(
            {"id": "1", "method": "session.status", "params": {"session_id": "sid"}}
        )
    finally:
        server._sessions.pop("sid", None)

    assert "Model: live-model (live-provider)" in resp["result"]["output"]


def test_skills_reload_runs_in_gateway_process(monkeypatch):
    import agent.skill_commands as skill_commands

    called = {}
    monkeypatch.setattr(
        skill_commands,
        "reload_skills",
        lambda: called.setdefault(
            "result",
            {
                "added": [{"name": "new-skill", "description": "demo"}],
                "removed": [],
                "total": 42,
            },
        ),
    )

    resp = server.handle_request({"id": "1", "method": "skills.reload", "params": {}})

    assert "new-skill" in resp["result"]["output"]


def test_snapshot_restore_is_blocked_from_tui_worker():
    server._sessions["sid"] = _session()
    try:
        worker_resp = server.handle_request(
            {
                "id": "1",
                "method": "slash.exec",
                "params": {"command": "snapshot restore latest", "session_id": "sid"},
            }
        )
        dispatch_resp = server.handle_request(
            {
                "id": "2",
                "method": "command.dispatch",
                "params": {
                    "arg": "restore latest",
                    "name": "snapshot",
                    "session_id": "sid",
                },
            }
        )
    finally:
        server._sessions.pop("sid", None)

    assert worker_resp["error"]["code"] == 4018
    assert (
        "snapshot restore mutates live config/state" in worker_resp["error"]["message"]
    )
    assert dispatch_resp["result"]["type"] == "exec"
    assert (
        "/snapshot restore is blocked in the TUI" in dispatch_resp["result"]["output"]
    )


def test_command_dispatch_exec_nonzero_surfaces_error(monkeypatch):
    monkeypatch.setattr(
        server,
        "_load_cfg",
        lambda: {"quick_commands": {"boom": {"type": "exec", "command": "boom"}}},
    )
    monkeypatch.setattr(
        server.subprocess,
        "run",
        lambda *args, **kwargs: types.SimpleNamespace(
            returncode=1, stdout="", stderr="failed"
        ),
    )

    resp = server.handle_request(
        {"id": "1", "method": "command.dispatch", "params": {"name": "boom"}}
    )

    assert "error" in resp
    assert "failed" in resp["error"]["message"]


def test_input_detect_drop_path_with_spaces(tmp_path):
    """input.detect_drop correctly handles image paths containing spaces."""
    # Create a minimal PNG file with a space in its name
    img = tmp_path / "screenshot with spaces.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")  # valid PNG header

    server._sessions["sid"] = _session()

    resp = server.handle_request(
        {
            "id": "2",
            "method": "input.detect_drop",
            "params": {"session_id": "sid", "text": str(img)},
        }
    )

    assert resp["result"]["matched"] is True
    assert resp["result"]["is_image"] is True
    assert resp["result"]["path"] == str(img)
    assert resp["result"]["text"] == f"[User attached image: {img.name}]"
    # Verify attachment was recorded in the session
    assert len(server._sessions["sid"]["attached_images"]) == 1
    assert server._sessions["sid"]["attached_images"][0] == str(img)


def test_input_detect_drop_path_with_spaces_and_remainder(tmp_path):
    """input.detect_drop splits remainder when path contains spaces."""
    img = tmp_path / "photo with space.jpg"
    img.write_bytes(b"\xff\xd8\xff" + b"fakejpeg")  # minimal-ish JPEG header

    server._sessions["sid"] = _session()

    user_input = f"{img} describe this image"
    resp = server.handle_request(
        {
            "id": "3",
            "method": "input.detect_drop",
            "params": {"session_id": "sid", "text": user_input},
        }
    )

    assert resp["result"]["matched"] is True
    assert resp["result"]["is_image"] is True
    assert resp["result"]["path"] == str(img)
    # Remainder becomes the text sent to the model
    assert resp["result"]["text"] == "describe this image"
    assert server._sessions["sid"]["attached_images"][0] == str(img)


def test_rollback_restore_resolves_number_and_file_path():
    calls = {}

    class _Mgr:
        enabled = True
        unsupported_backend_reason = staticmethod(lambda task_id="default": None)

        def list_checkpoints(self, cwd):
            return [{"hash": "aaa111"}, {"hash": "bbb222"}]

        def restore(self, cwd, target, file_path=None):
            calls["args"] = (cwd, target, file_path)
            return {"success": True, "message": "done"}

    server._sessions["sid"] = _session(
        agent=types.SimpleNamespace(_checkpoint_mgr=_Mgr()), history=[]
    )
    resp = server.handle_request(
        {
            "id": "1",
            "method": "rollback.restore",
            "params": {"session_id": "sid", "hash": "2", "file_path": "src/app.tsx"},
        }
    )

    assert resp["result"]["success"] is True
    assert calls["args"][1] == "bbb222"
    assert calls["args"][2] == "src/app.tsx"


def test_rollback_restore_truncates_from_real_user_turn_not_marker(monkeypatch):
    """rollback.restore must truncate from the last *real* user turn,
    not a display_kind timeline marker (same bug class as /undo).
    """
    from pathlib import Path as _Path

    class _Mgr:
        enabled = True
        unsupported_backend_reason = staticmethod(lambda task_id="default": None)

        def list_checkpoints(self, cwd):
            return [{"hash": "abc123"}]

        def restore(self, cwd, target, file_path=None):
            return {"success": True, "message": "restored"}

    history = [
        {"role": "user", "content": "first question"},
        {"role": "assistant", "content": "first answer"},
        {"role": "user", "content": "second question"},
        {"role": "assistant", "content": "second answer"},
        {
            "role": "user",
            "content": "background agent finished",
            "display_kind": "async_delegation_complete",
        },
    ]
    server._sessions["sid"] = _session(
        agent=types.SimpleNamespace(_checkpoint_mgr=_Mgr()),
        history=list(history),
        session_key="",
    )
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "rollback.restore",
                "params": {"session_id": "sid", "hash": "abc123"},
            }
        )

        assert resp["result"]["success"] is True
        assert resp["result"]["history_removed"] == 3  # q2 + a2 + marker
        # Only first exchange remains
        remaining = server._sessions["sid"]["history"]
        assert [m["content"] for m in remaining] == ["first question", "first answer"]
    finally:
        server._sessions.pop("sid", None)


def test_rollback_restore_skips_legacy_compaction_handoff(monkeypatch):
    """rollback.restore must not truncate from a legacy standalone compaction
    handoff — a durable role=user row persisted pre-#80622 with NO
    display_kind. Same bug class as the display_kind marker above, caught
    only by the is_user_originated_turn predicate.
    """
    from agent.context_compressor import (
        COMPRESSED_SUMMARY_METADATA_KEY,
        HISTORICAL_TASK_HEADING,
        SUMMARY_PREFIX,
        _SUMMARY_END_MARKER,
    )

    class _Mgr:
        enabled = True
        unsupported_backend_reason = staticmethod(lambda task_id="default": None)

        def list_checkpoints(self, cwd):
            return [{"hash": "abc123"}]

        def restore(self, cwd, target, file_path=None):
            return {"success": True, "message": "restored"}

    handoff = {
        "role": "user",
        "content": (
            f"{SUMMARY_PREFIX}\n{HISTORICAL_TASK_HEADING}\n"
            f"User asked: 'old task'\n\n{_SUMMARY_END_MARKER}"
        ),
        COMPRESSED_SUMMARY_METADATA_KEY: True,
        # NOTE: no display_kind — the legacy-persistence shape (#80622).
    }
    history = [
        {"role": "user", "content": "first question"},
        {"role": "assistant", "content": "first answer"},
        {"role": "user", "content": "second question"},
        {"role": "assistant", "content": "second answer"},
        handoff,
    ]
    server._sessions["sid"] = _session(
        agent=types.SimpleNamespace(_checkpoint_mgr=_Mgr()),
        history=list(history),
        session_key="",
    )
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "rollback.restore",
                "params": {"session_id": "sid", "hash": "abc123"},
            }
        )

        assert resp["result"]["success"] is True
        # Truncation lands on "second question", not the handoff row.
        assert resp["result"]["history_removed"] == 3  # q2 + a2 + handoff
        remaining = server._sessions["sid"]["history"]
        assert [m["content"] for m in remaining] == ["first question", "first answer"]
    finally:
        server._sessions.pop("sid", None)


# ── session.steer ────────────────────────────────────────────────────


def test_rollback_restore_preserves_composite_carrier_scaffold(monkeypatch, tmp_path):
    """A checkpoint restore drops the live ask but keeps compacted context."""
    from agent.context_compressor import (
        HISTORICAL_TASK_HEADING,
        SUMMARY_PREFIX,
        _SUMMARY_END_MARKER,
    )
    from hermes_state import SessionDB

    class _Mgr:
        enabled = True
        unsupported_backend_reason = staticmethod(lambda task_id="default": None)

        def list_checkpoints(self, cwd):
            return [{"hash": "abc123"}]

        def restore(self, cwd, target, file_path=None):
            return {"success": True, "message": "restored"}

    carrier = {
        "role": "user",
        "content": (
            f"{SUMMARY_PREFIX}\n{HISTORICAL_TASK_HEADING}\nold task\n\n"
            f"{_SUMMARY_END_MARKER}\n\nREAL ASK"
        ),
    }
    db = SessionDB(db_path=tmp_path / "state.db")
    db.create_session("rollback-carrier", source="tui")
    db.append_message("rollback-carrier", "user", carrier["content"])
    db.append_message("rollback-carrier", "assistant", "answer")
    durable = db.get_messages_as_conversation("rollback-carrier")
    agent = types.SimpleNamespace(
        _checkpoint_mgr=_Mgr(),
        _session_messages=list(durable),
        _last_flushed_db_idx=len(durable),
        _db_flush_scan_prefix=list(durable),
    )
    server._sessions["sid"] = _session(
        agent=agent,
        history=list(durable),
        session_key="rollback-carrier",
    )
    monkeypatch.setattr(server, "_get_db", lambda: db)
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "rollback.restore",
                "params": {"session_id": "sid", "hash": "abc123"},
            }
        )

        assert "result" in resp, resp
        assert resp["result"]["success"] is True
        assert resp["result"]["history_removed"] == 2
        remaining = server._sessions["sid"]["history"]
        assert len(remaining) == 1
        assert remaining[0]["display_kind"] == "hidden"
        assert SUMMARY_PREFIX in remaining[0]["content"]
        assert "REAL ASK" not in remaining[0]["content"]
        cold = db.get_messages_as_conversation(
            "rollback-carrier", include_row_ids=True
        )
        assert len(cold) == 1
        assert cold[0]["content"] == remaining[0]["content"]
        assert cold[0]["display_kind"] == "hidden"
        assert cold[0]["_row_id"] == remaining[0]["_row_id"]
        assert agent._session_messages == remaining
        assert agent._last_flushed_db_idx == 1
        assert agent._db_flush_scan_prefix == remaining
        inactive = db.get_messages_as_conversation(
            "rollback-carrier", include_inactive=True
        )
        assert any("REAL ASK" in str(message.get("content")) for message in inactive)
        assert any(message.get("content") == "answer" for message in inactive)
    finally:
        server._sessions.pop("sid", None)
        db.close()


def test_session_steer_calls_agent_steer_when_agent_supports_it():
    """The TUI RPC method must call agent.steer(text) and return a
    queued status without touching interrupt state.
    """
    calls = {}

    class _Agent:
        def steer(self, text):
            calls["steer_text"] = text
            return True

        def interrupt(self, *args, **kwargs):
            calls["interrupt_called"] = True

    server._sessions["sid"] = _session(agent=_Agent(), running=True)
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.steer",
                "params": {"session_id": "sid", "text": "also check auth.log"},
            }
        )
    finally:
        server._sessions.pop("sid", None)

    assert "result" in resp, resp
    assert resp["result"]["status"] == "queued"
    assert resp["result"]["text"] == "also check auth.log"
    assert calls["steer_text"] == "also check auth.log"
    assert "interrupt_called" not in calls  # must NOT interrupt


def test_session_steer_on_idle_session_is_rejected_not_parked():
    """#64578: with no live turn a steer has no tool call to ride. Accepting it parked the text in
    the agent's pending-steer slot, where the next turn's pre-API drain spliced it after an OLD tool
    row. It must come back 'rejected' (clients then send it as a normal prompt) and never reach
    agent.steer()."""
    agent = _RecordingSteerAgent()
    server._sessions["sid"] = _session(agent=agent, running=False)
    try:
        resp = server.handle_request(
            {"id": "1", "method": "session.steer", "params": {"session_id": "sid", "text": "check the logs"}}
        )
    finally:
        server._sessions.pop("sid", None)

    assert resp["result"]["status"] == "rejected", resp
    assert agent.steered == []


def test_steer_slash_on_idle_session_sends_as_next_turn():
    """#64578: idle `/steer <text>` via command.dispatch must go out as a normal next-turn message
    with a notice saying so, not claim "Steer queued" while stashing the text on the agent."""
    agent = _RecordingSteerAgent()
    server._sessions["sid"] = _session(agent=agent, running=False)
    try:
        res = server._methods["command.dispatch"](
            "1", {"name": "steer", "arg": "check the logs", "session_id": "sid"})
    finally:
        server._sessions.pop("sid", None)

    result = res["result"]
    assert result["type"] == "send"
    assert result["message"] == "check the logs"
    assert result.get("notice")
    assert agent.steered == []


def test_steer_slash_during_live_turn_still_steers():
    agent = _RecordingSteerAgent()
    server._sessions["sid"] = _session(agent=agent, running=True)
    try:
        res = server._methods["command.dispatch"](
            "1", {"name": "steer", "arg": "check the logs", "session_id": "sid"})
    finally:
        server._sessions.pop("sid", None)

    assert res["result"]["type"] == "exec"
    assert agent.steered == ["check the logs"]


def test_session_steer_rejects_empty_text():
    server._sessions["sid"] = _session(
        agent=types.SimpleNamespace(steer=lambda t: True)
    )
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.steer",
                "params": {"session_id": "sid", "text": "   "},
            }
        )
    finally:
        server._sessions.pop("sid", None)

    assert "error" in resp, resp
    assert resp["error"]["code"] == 4002


def test_session_steer_errors_when_agent_has_no_steer_method():
    server._sessions["sid"] = _session(agent=types.SimpleNamespace())  # no steer()
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.steer",
                "params": {"session_id": "sid", "text": "hi"},
            }
        )
    finally:
        server._sessions.pop("sid", None)

    assert "error" in resp, resp
    assert resp["error"]["code"] == 4010


def test_session_redirect_calls_capable_core_agent(monkeypatch):
    calls = []
    agent = types.SimpleNamespace(
        _supports_active_turn_redirect=True,
        redirect=lambda text: calls.append(text) or True,
    )
    session = _session(agent=agent)
    session["inflight_turn"] = {"user": "original request", "assistant": "partial reply"}
    server._sessions["sid"] = session
    try:
        before = session.get("last_active")
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.redirect",
                "params": {"session_id": "sid", "text": "use Postgres"},
            }
        )
    finally:
        server._sessions.pop("sid", None)

    assert resp["result"] == {
        "status": "redirected",
        "text": "use Postgres",
    }
    assert calls == ["use Postgres"]
    # The correction is recorded alongside the prompt that started the turn,
    # never over it — resume must be able to rebuild both bubbles.
    assert session["inflight_turn"]["user"] == "original request"
    assert session["inflight_turn"]["corrections"] == ["use Postgres"]
    assert session.get("last_active") is not None
    assert before is None or session["last_active"] >= before


def test_session_redirect_rpc_drops_queued_duplicate_of_inflight_user():
    """#84417: Desktop ``session.redirect`` must purge stale self-duplicates.

    Production path: renderer steers via ``session.redirect`` (not
    ``prompt.submit``). A self-copy of the live original user text already in
    the server queue must not survive a successful redirect — otherwise
    post-turn ``_drain_queued_prompt`` restarts prompt P after Q is handled.
    Unrelated next-turn envelopes stay.
    """
    original = "deepseek released a new flash model — I changed all settings to flash"
    agent = types.SimpleNamespace(
        _supports_active_turn_redirect=True,
        redirect=lambda text: True,
    )
    session = _session(agent=agent, running=True)
    session["inflight_turn"] = {
        "user": original,
        "assistant": "partial",
        "streaming": True,
        "error": "",
    }
    session["queued_prompt"] = {"text": original, "transport": "ws-1"}
    session["queued_prompts"] = [
        {"text": original, "transport": "ws-1"},
        {"text": "unrelated later task", "transport": "ws-1"},
    ]
    server._sessions["sid"] = session
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.redirect",
                "params": {
                    "session_id": "sid",
                    "text": "what about the pricing instead?",
                },
            }
        )
    finally:
        server._sessions.pop("sid", None)

    assert resp["result"]["status"] == "redirected"
    assert session["inflight_turn"]["user"] == original
    assert session["inflight_turn"]["corrections"] == [
        "what about the pricing instead?"
    ]
    # Self-duplicates of the live original are gone; legitimate follow-up kept.
    assert session.get("queued_prompt") == {
        "text": "unrelated later task",
        "transport": "ws-1",
    }
    assert not session.get("queued_prompts")


def test_session_redirect_build_window_scrubs_stale_p_when_queuing_q():
    """#84417: build-window queue of Q must not leave P ahead of Q."""
    original = "live original P"
    session = _session(running=True)
    session["agent"] = None  # async agent build window
    session["inflight_turn"] = {
        "user": original,
        "assistant": "",
        "streaming": True,
        "error": "",
    }
    session["queued_prompt"] = {"text": original, "transport": "ws-1"}
    server._sessions["sid"] = session
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.redirect",
                "params": {"session_id": "sid", "text": "correction Q"},
            }
        )
    finally:
        server._sessions.pop("sid", None)

    assert resp["result"] == {"status": "queued", "text": "correction Q"}
    assert session["queued_prompt"]["text"] == "correction Q"
    assert not session.get("queued_prompts")


def test_session_redirect_records_correction_without_erasing_prompt():
    """A redirect must not overwrite the turn's original user text.

    The inflight snapshot is the only thing session.resume can replay, so
    overwriting ``user`` erased the prompt that started the turn and the
    client repainted the thread with the user's message missing.
    """
    session = {}
    server._start_inflight_turn(session, "remove the session counts")
    server._append_inflight_delta(session, "Moving.")
    server._record_inflight_correction(session, "hurry up")
    server._record_inflight_correction(session, "and the worktree ones")

    snapshot = server._inflight_snapshot(session)
    assert snapshot is not None

    assert snapshot["user"] == "remove the session counts"
    assert snapshot["corrections"] == ["hurry up", "and the worktree ones"]


def test_inflight_snapshot_carries_arrival_order_offsets():
    """Each correction records how much assistant text had already streamed.

    Resuming clients rebuild ARRIVAL order from these boundaries: the
    correction bubble lands after the output the user had already seen and
    before the output it redirected (#73793), instead of above the whole
    reply.
    """
    session = {}
    server._start_inflight_turn(session, "remove the session counts")
    server._append_inflight_delta(session, "Moving.")
    server._record_inflight_correction(session, "hurry up")
    server._append_inflight_delta(session, "Still.")
    server._record_inflight_correction(session, "and the worktree ones")
    server._append_inflight_delta(session, "Done soon.")

    snapshot = server._inflight_snapshot(session)
    assert snapshot is not None

    assert snapshot["corrections"] == ["hurry up", "and the worktree ones"]
    assert snapshot["correction_offsets"] == [len("Moving."), len("Moving.Still.")]


def test_turn_admission_carries_synthetic_display_metadata_into_inflight_snapshot(monkeypatch):
    """A reconnect must retain the typed synthetic user bubble (#112144)."""
    monkeypatch.setattr(server, "_ensure_active_session_slot", lambda *_args: None)
    agent = Mock()
    session = {"agent": agent, "attached_images": [], "history_lock": threading.RLock()}
    display_metadata = {"display_text": "Finished syncing the workspace"}

    assert server._admit_prompt_turn(
        "sid", session, "process completed", None, None, "process_complete", display_metadata,
    ) == ([], agent)

    snapshot = server._inflight_snapshot(session)

    assert snapshot is not None
    assert snapshot["display_kind"] == "process_complete"
    assert snapshot["display_metadata"] == {"display_text": "Finished syncing the workspace"}


def test_inflight_snapshot_omits_offsets_when_not_fully_recorded():
    """A pre-upgrade in-memory turn may carry corrections without offsets.

    The parallel list is only sent when every correction has one, so clients
    can trust the pairing and older snapshots degrade to the no-offset path.
    """
    session = {}
    server._start_inflight_turn(session, "prompt")
    turn = session["inflight_turn"]
    turn["corrections"] = ["legacy correction"]

    snapshot = server._inflight_snapshot(session)
    assert snapshot is not None

    assert snapshot["corrections"] == ["legacy correction"]
    assert "correction_offsets" not in snapshot


def test_inflight_snapshot_omits_corrections_when_none_recorded():
    session = {}
    server._start_inflight_turn(session, "just the prompt")

    snapshot = server._inflight_snapshot(session)
    assert snapshot is not None
    assert "corrections" not in snapshot


def test_new_turn_does_not_inherit_prior_turn_corrections():
    session = {}
    server._start_inflight_turn(session, "first prompt")
    server._record_inflight_correction(session, "first correction")
    server._start_inflight_turn(session, "second prompt")

    snapshot = server._inflight_snapshot(session)
    assert snapshot is not None

    assert snapshot["user"] == "second prompt"
    assert "corrections" not in snapshot


def test_session_redirect_queues_during_agent_build_window(monkeypatch):
    # A fresh turn flips running=True and builds the agent asynchronously, so
    # session["agent"] is briefly None. A correction landing here must queue
    # (lossless, reaches the model next turn), not hard-reject as unsupported.
    session = _session(running=True)
    session["agent"] = None
    server._sessions["sid"] = session
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.redirect",
                "params": {"session_id": "sid", "text": "wait, use SQLite"},
            }
        )
    finally:
        server._sessions.pop("sid", None)

    assert resp["result"] == {"status": "queued", "text": "wait, use SQLite"}
    assert session["queued_prompt"]["text"] == "wait, use SQLite"


def test_session_redirect_rejects_when_idle_without_agent(monkeypatch):
    # No live turn and no agent: nothing to redirect, and we must not queue a
    # phantom turn — keep the explicit unsupported rejection.
    session = _session(running=False)
    session["agent"] = None
    server._sessions["sid"] = session
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.redirect",
                "params": {"session_id": "sid", "text": "hi"},
            }
        )
    finally:
        server._sessions.pop("sid", None)

    assert resp["error"]["code"] == 4010
    assert session.get("queued_prompt") is None


def test_session_info_includes_session_title(monkeypatch):
    class _FakeDB:
        def get_session_title(self, key):
            assert key == "session-key"
            return "Dashboard title"

    monkeypatch.setattr(server, "_get_db", lambda: _FakeDB())

    info = server._session_info(
        types.SimpleNamespace(tools=[], model="test/model", provider="openai-codex"),
        {"session_key": "session-key", "history": []},
    )

    assert info["title"] == "Dashboard title"


def test_session_info_reports_pending_model_switch(monkeypatch):
    """A model queued mid-turn shows as the session's model in session.info, so
    the end-of-turn settle doesn't blip the UI back to the still-live old model
    before the switch applies at the next turn start."""
    agent = types.SimpleNamespace(tools=[], model="old/model", provider="openai")
    session = {
        "session_key": "",
        "history": [],
        "pending_model_switch": {
            "raw": "new/model --provider anthropic",
            "display_model": "new/model",
            "display_provider": "anthropic",
        },
    }

    info = server._session_info(agent, session)
    assert info["model"] == "new/model"
    assert info["provider"] == "anthropic"

    # With nothing queued the live agent model wins, as before.
    session.pop("pending_model_switch")
    assert server._session_info(agent, session)["model"] == "old/model"


def test_session_info_includes_turn_started_at():
    agent = types.SimpleNamespace(tools=[], model="", provider="")
    session = {
        "history": [],
        "inflight_turn": {"started_at": 1_700_000_123.5},
        "running": True,
    }

    assert server._session_info(agent, session)["turn_started_at"] == 1_700_000_123.5

    session["inflight_turn"] = None
    session["running"] = False
    assert server._session_info(agent, session)["turn_started_at"] is None


# ---------------------------------------------------------------------------
# History-mutating commands must reject while session.running is True.
# Without these guards, prompt.submit's post-run history write either
# clobbers the mutation (version matches) or silently drops the agent's
# output (version mismatch) — both produce UI<->backend state desync.
# ---------------------------------------------------------------------------


def test_session_undo_rejects_while_running():
    """Fix for TUI silent-drop #1: /undo must not mutate history
    while the agent is mid-turn — would either clobber the undo or
    cause prompt.submit to silently drop the agent's response."""
    server._sessions["sid"] = _session(
        running=True,
        history=[
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ],
    )
    try:
        resp = server.handle_request(
            {"id": "1", "method": "session.undo", "params": {"session_id": "sid"}}
        )
        assert resp.get("error"), "session.undo should reject while running"
        assert resp["error"]["code"] == 4009
        # History must be unchanged
        assert len(server._sessions["sid"]["history"]) == 2
    finally:
        server._sessions.pop("sid", None)


def test_session_undo_allowed_when_idle():
    """Regression guard: when not running, /undo still works."""
    server._sessions["sid"] = _session(
        running=False,
        session_key="",
        history=[
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ],
    )
    try:
        resp = server.handle_request(
            {"id": "1", "method": "session.undo", "params": {"session_id": "sid"}}
        )
        assert resp.get("result"), f"got error: {resp.get('error')}"
        assert resp["result"]["removed"] == 2
        assert server._sessions["sid"]["history"] == []
    finally:
        server._sessions.pop("sid", None)


def test_session_compress_rejects_while_running(monkeypatch):
    server._sessions["sid"] = _session(running=True)
    try:
        resp = server.handle_request(
            {"id": "1", "method": "session.compress", "params": {"session_id": "sid"}}
        )
        assert resp.get("error")
        assert resp["error"]["code"] == 4009
    finally:
        server._sessions.pop("sid", None)


def test_rollback_restore_rejects_full_history_while_running(monkeypatch):
    """Full-history rollback must reject; file-scoped rollback still allowed."""
    server._sessions["sid"] = _session(running=True)
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "rollback.restore",
                "params": {"session_id": "sid", "hash": "abc"},
            }
        )
        assert resp.get("error"), "full-history rollback should reject while running"
        assert resp["error"]["code"] == 4009
    finally:
        server._sessions.pop("sid", None)


def test_prompt_submit_history_version_mismatch_surfaces_warning(monkeypatch):
    """Fix for TUI silent-drop #2: the defensive backstop at prompt.submit
    must attach a 'warning' to message.complete when history was
    mutated externally during the turn (instead of silently dropping
    the agent's output)."""
    # Agent bumps history_version itself mid-run to simulate an external
    # mutation slipping past the guards.
    session_ref = {"s": None}

    class _RacyAgent:
        def run_conversation(self, prompt, conversation_history=None, stream_callback=None, **_kwargs):
            # Simulate: something external bumped history_version
            # while we were running.
            with session_ref["s"]["history_lock"]:
                session_ref["s"]["history_version"] += 1
            return {
                "final_response": "agent reply",
                "messages": [{"role": "assistant", "content": "agent reply"}],
            }

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None, **_thread_options):
            self._target = target

        def start(self):
            self._target()

    server._sessions["sid"] = _session(agent=_RacyAgent())
    session_ref["s"] = server._sessions["sid"]
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
        assert resp.get("result"), f"got error: {resp.get('error')}"

        # History should NOT contain the agent's output (version mismatch)
        assert server._sessions["sid"]["history"] == []

        # message.complete must carry a 'warning' so the UI / operator
        # knows the output was not persisted.
        complete_calls = [a for a in emits if a[0] == "message.complete"]
        assert len(complete_calls) == 1
        _, _, payload = complete_calls[0]
        assert "warning" in payload, (
            "message.complete must include a 'warning' field on "
            "history_version mismatch — otherwise the UI silently "
            "shows output that was never persisted"
        )
        assert (
            "not saved" in payload["warning"].lower()
            or "changed" in payload["warning"].lower()
        )
    finally:
        server._sessions.pop("sid", None)


def test_prompt_submit_merges_on_model_switch_marker(monkeypatch):
    """#76870: when a model-switch marker is the only history mutation during
    a turn, the agent's output must be merged into the current history (which
    now contains the marker) instead of being discarded.

    This test covers BOTH cases:
    - No prior marker in turn-start history (first switch in a session)
    - Prior marker existed (every subsequent switch — the original PR #77274
      fix was dead code here because _append_model_switch_marker strips the
      old marker before appending the new one, producing a net-zero length
      delta that the positional slice missed).
    """
    from tui_gateway.server import _MODEL_SWITCH_MARKER_PREFIX

    session_ref = {"s": None}

    def _make_marker(model: str) -> dict:
        return {
            "role": "user",
            "content": f"{_MODEL_SWITCH_MARKER_PREFIX}{model}.]",
            "display_kind": "model_switch",
        }

    class _MarkerAgent:
        def __init__(self, new_history_state: list):
            self._new_history_state = new_history_state

        def run_conversation(self, prompt, conversation_history=None, stream_callback=None, **_kwargs):
            # Simulate _append_model_switch_marker: strip prior markers, append new one.
            with session_ref["s"]["history_lock"]:
                hist = session_ref["s"]["history"]
                hist[:] = [h for h in hist if not _is_marker(h)]
                hist.append(_make_marker("new-model"))
                session_ref["s"]["history_version"] += 1
            # result["messages"] = conversation_history + user msg + assistant reply
            return {
                "final_response": "agent reply",
                "messages": list(conversation_history) + [
                    {"role": "user", "content": "hi"},
                    {"role": "assistant", "content": "agent reply"},
                ],
            }

    def _is_marker(entry) -> bool:
        from tui_gateway.server import _is_model_switch_marker
        return _is_model_switch_marker(entry)

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None, **_thread_options):
            self._target = target

        def start(self):
            self._target()

    # Test both: no prior marker, and prior marker present
    for label, prior_history in [
        ("no prior marker", [{"role": "user", "content": "hello"}]),
        ("with prior marker", [
            {"role": "user", "content": "hello"},
            _make_marker("old-model"),
            {"role": "assistant", "content": "hi there"},
        ]),
    ]:
        server._sessions["sid"] = _session(
            agent=_MarkerAgent([]),
            history=list(prior_history),
        )
        session_ref["s"] = server._sessions["sid"]
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
            assert resp.get("result"), f"[{label}] got error: {resp.get('error')}"

            final_history = server._sessions["sid"]["history"]

            # The agent's new messages must be present in the persisted history.
            assistant_msgs = [
                e for e in final_history
                if isinstance(e, dict) and e.get("role") == "assistant"
                and e.get("content") == "agent reply"
            ]
            assert len(assistant_msgs) == 1, (
                f"[{label}] agent output was not merged into history "
                f"(got {len(assistant_msgs)} assistant 'agent reply' messages)"
            )

            # The model-switch marker must be present.
            markers = [e for e in final_history if _is_marker(e)]
            assert len(markers) == 1, (
                f"[{label}] expected exactly 1 model-switch marker, got {len(markers)}"
            )
            assert "new-model" in markers[0]["content"]

            # No warning should be surfaced — the merge succeeded.
            complete_calls = [a for a in emits if a[0] == "message.complete"]
            assert len(complete_calls) == 1
            _, _, payload = complete_calls[0]
            assert "warning" not in payload, (
                f"[{label}] merge path should not surface a warning"
            )
        finally:
            server._sessions.pop("sid", None)


def test_prompt_submit_merges_on_personality_pivot_marker(monkeypatch):
    """A personality pivot injected mid-turn must merge like a model switch.

    `/personality` applies immediately — there is no deferred queue for it the
    way `pending_model_switch` defers a mid-turn model change — so choosing a
    personality while a turn is running bumps `history_version` from the RPC
    thread. The mid-turn reconciliation only recognized the model-switch
    marker, so the pivot read as a genuine desync and the finished turn was
    dropped from session history: the user saw the reply and it was never
    stored (#82756).
    """
    session_ref: dict[str, dict | None] = {"s": None}

    class _PivotAgent:
        def run_conversation(
            self, prompt, conversation_history=None, stream_callback=None, **_kwargs
        ):
            # Real injection point, mid-turn, exactly as the personality RPC
            # would reach it from the other thread.
            server._apply_personality_to_session(
                "sid", session_ref["s"], "Answer tersely.", "terse"
            )
            return {
                "final_response": "agent reply",
                "messages": list(conversation_history)
                + [
                    {"role": "user", "content": "hi"},
                    {"role": "assistant", "content": "agent reply"},
                ],
            }

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None, **_thread_options):
            self._target = target

        def start(self):
            self._target()

    server._sessions["sid"] = _session(
        agent=_PivotAgent(),
        history=[{"role": "user", "content": "hello"}],
    )
    session_ref["s"] = server._sessions["sid"]
    emits: list[tuple] = []
    try:
        monkeypatch.setattr(server.threading, "Thread", _ImmediateThread)
        monkeypatch.setattr(server, "_get_usage", lambda _a: {})
        monkeypatch.setattr(server, "render_message", lambda _t, _c: "")
        monkeypatch.setattr(server, "_session_info", lambda *a, **k: {})
        monkeypatch.setattr(server, "_emit", lambda *a: emits.append(a))

        resp = server.handle_request(
            {
                "id": "1",
                "method": "prompt.submit",
                "params": {"session_id": "sid", "text": "hi"},
            }
        )
        assert resp.get("result"), f"got error: {resp.get('error')}"

        final_history = server._sessions["sid"]["history"]

        assistant_msgs = [
            e
            for e in final_history
            if isinstance(e, dict)
            and e.get("role") == "assistant"
            and e.get("content") == "agent reply"
        ]
        assert len(assistant_msgs) == 1, (
            "the personality pivot discarded the finished turn instead of "
            f"merging it (got {len(assistant_msgs)} assistant replies)"
        )

        pivots = [
            e
            for e in final_history
            if isinstance(e, dict) and e.get("display_kind") == "personality_switch"
        ]
        assert len(pivots) == 1, f"expected exactly 1 pivot, got {len(pivots)}"

        complete_calls = [a for a in emits if a[0] == "message.complete"]
        assert len(complete_calls) == 1
        _, _, payload = complete_calls[0]
        assert "warning" not in payload, "merge path should not surface a warning"
    finally:
        server._sessions.pop("sid", None)
