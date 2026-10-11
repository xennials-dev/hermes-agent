"""tui_gateway.server — history expansion, session resume and stored runtime restoration.

Split from test_tui_gateway_server.py; shared fixtures and helpers live
in tests/tui_gateway/_server_test_helpers.py.
"""

import json
import threading
import time
import types
from unittest.mock import patch
import pytest
from tui_gateway import server

from tests.tui_gateway._server_test_helpers import (
    _neuter_agent_prewarm_timer,  # autouse
    _patch_config_model,
    _reap_leaked_notification_pollers,  # autouse
    _session,
    _sync_test_session,
    _two_repo_project_skill_sessions,
)


def test_history_to_messages_keeps_reasoning_only_assistant_turn():
    # A thinking-only assistant turn (reasoning present, no visible text) is
    # persisted and recallable, but was dropped from the resumed session view
    # as "empty" -- so it vanished while the agent could still recall it from
    # the transcript. Keep it (with reasoning) so the desktop "Thinking…"
    # disclosure renders. (#44022)
    history = [
        {"role": "user", "content": "think about this"},
        {"role": "assistant", "content": "", "reasoning": "step-by-step thoughts"},
        {"role": "assistant", "content": "here is the answer"},
    ]

    assert server._history_to_messages(history) == [
        {"role": "user", "text": "think about this"},
        {"role": "assistant", "text": "", "reasoning": "step-by-step thoughts"},
        {"role": "assistant", "text": "here is the answer"},
    ]


def test_history_to_messages_still_drops_empty_assistant_without_reasoning():
    # A genuinely empty assistant turn (no text, no reasoning, no tool calls)
    # remains filtered out -- the fix only spares reasoning-bearing turns.
    history = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "", "reasoning": ""},
        {"role": "assistant", "content": "   "},
        {"role": "assistant", "content": "real reply"},
    ]

    assert server._history_to_messages(history) == [
        {"role": "user", "text": "hi"},
        {"role": "assistant", "text": "real reply"},
    ]


def test_history_to_messages_renders_multimodal_content():
    # bb/gui preserves image URLs in the resume payload so the desktop
    # renderer's extractEmbeddedImages can pull them back out and display
    # the actual image instead of a placeholder. This also keeps the
    # resume payload in sync with the cached message.
    history = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "look here"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,abc"}},
            ],
        },
        {"role": "assistant", "content": "saw it"},
    ]

    assert server._history_to_messages(history) == [
        {"role": "user", "text": "look here\ndata:image/png;base64,abc"},
        {"role": "assistant", "text": "saw it"},
    ]


def test_history_to_messages_strips_legacy_discord_triggering_note():
    # Rows written before the gateway persisted the authored text carry the model-facing
    # routing note in user ``content``; this projection heals them for TUI/web resume
    # (the desktop hydration strip is the same rule). Reply pointer and assistant rows are kept.
    from gateway.run_inbound import discord_triggering_note

    note = discord_triggering_note("123")
    history = [
        {"role": "user", "content": f"{note}\n\n[Replying to: hi]\nwhat is up"},
        {"role": "assistant", "content": f"echo: {note}"},
    ]

    assert server._history_to_messages(history) == [
        {"role": "user", "text": "[Replying to: hi]\nwhat is up"},
        {"role": "assistant", "text": f"echo: {note}"},
    ]


def test_history_to_messages_hides_gateway_system_markers():
    # Model-switch / personality notices are persisted as role=user [System: …]
    # rows so strict providers accept them mid-history, but they are model-facing
    # metadata -- never a user turn. They must not render as a user bubble on any
    # surface, and dropping them from the display projection also stops the
    # stored marker from shifting the desktop's user-message ordinals and
    # duplicating the optimistic prompt (#67603).
    history = [
        {"role": "user", "content": "first question"},
        {"role": "assistant", "content": "first answer"},
        {
            "role": "user",
            "content": "[System: The active model for this chat has changed to k3.]",
        },
        {"role": "user", "content": "second question"},
        {"role": "assistant", "content": "second answer"},
        {
            "role": "user",
            "content": (
                "[System: The user has changed the assistant's personality. "
                "Adopt the new persona going forward.]"
            ),
        },
    ]

    assert server._history_to_messages(history) == [
        {"role": "user", "text": "first question"},
        {"role": "assistant", "text": "first answer"},
        {"role": "user", "text": "second question"},
        {"role": "assistant", "text": "second answer"},
    ]


def test_history_to_messages_drops_display_hidden_scaffolding():
    # A mid-stream steer persists an interrupted-turn checkpoint. When nothing
    # reached the screen the row carries only model-facing scaffolding and is
    # marked display_kind="hidden"; the scaffolded bytes live in the server-only
    # api_content sidecar for provider replay. This projection -- the single
    # display source every client reads -- must drop the row by its declared
    # display_kind, not just the "[System:" string convention, or the raw
    # "[This response was interrupted by a user correction.]" paints as an
    # assistant bubble (and api_content must never ship to a client).
    history = [
        {"role": "user", "content": "go"},
        {
            "role": "assistant",
            "content": "[This response was interrupted by a user correction.]",
            "api_content": "[This response was interrupted by a user correction.]",
            "display_kind": "hidden",
        },
        {"role": "user", "content": "i love you"},
        {
            "role": "assistant",
            "content": "Love you too",
            "api_content": (
                "[This response was interrupted by a user correction.]\n\n"
                "Visible response before the interruption:\n\nLove you too"
            ),
        },
    ]

    projected = server._history_to_messages(history)

    assert projected == [
        {"role": "user", "text": "go"},
        {"role": "user", "text": "i love you"},
        {"role": "assistant", "text": "Love you too"},
    ]
    # Server-only sidecar never crosses the wire.
    assert all("api_content" not in m for m in projected)


def test_history_to_messages_projects_a_skill_turn_to_its_invocation():
    # A /skill invocation is persisted EXPANDED: the activation note plus the
    # entire skill body. That payload is model-facing scaffolding -- this
    # projection is the single display source every client reads, so it must
    # hand back the invocation the user typed and never the body. Without it a
    # chat bubble renders the whole skill as if the user had written it.
    scaffolded = (
        '[IMPORTANT: The user has invoked the "work" skill, indicating they '
        "want you to follow its instructions. The full skill content is "
        "loaded below.]\n\n"
        "# /work\n\nSPIN UP A WORKTREE, never the primary checkout.\n\n"
        "The user has provided the following instruction alongside the skill "
        "invocation: fix the title leak"
    )

    history = [
        {"role": "user", "content": scaffolded},
        {"role": "assistant", "content": "on it"},
    ]

    assert server._history_to_messages(history) == [
        {
            "role": "user",
            "text": "/work fix the title leak",
            "display_kind": "skill_invocation",
        },
        {"role": "assistant", "text": "on it"},
    ]


def test_history_to_messages_projects_a_bare_skill_turn_to_the_command():
    scaffolded = (
        '[IMPORTANT: The user has invoked the "work" skill, indicating they '
        "want you to follow its instructions. The full skill content is "
        "loaded below.]\n\n# /work\n\nSPIN UP A WORKTREE."
    )

    assert server._history_to_messages([{"role": "user", "content": scaffolded}]) == [
        {"role": "user", "text": "/work", "display_kind": "skill_invocation"}
    ]


def test_expand_skill_invocation_for_replay_round_trips_the_projection(
    tmp_path, monkeypatch
):
    # Rewind/regenerate replays a turn from what the transcript SHOWS, and a
    # skill turn shows its invocation. Re-running that verbatim would send the
    # agent the literal "/work fix it" instead of the skill, so the server
    # re-expands it — the exact inverse of _skill_scaffold_projection, with the
    # body never leaving the server.
    import agent.skill_commands as skill_commands
    import agent.skill_utils as skill_utils
    import tools.skills_tool as skills_tool

    skills_dir = tmp_path / "skills"
    (skills_dir / "worktree-kickoff").mkdir(parents=True)
    (skills_dir / "worktree-kickoff" / "SKILL.md").write_text(
        "---\nname: worktree-kickoff\ndescription: Spin up a worktree\n---\n\n"
        "# kickoff\n\nSPIN UP A WORKTREE, never the primary checkout.\n"
    )
    monkeypatch.setattr(skills_tool, "SKILLS_DIR", skills_dir)
    monkeypatch.setattr(skill_utils, "get_external_skills_dirs", lambda *a, **k: [])
    monkeypatch.setattr(skill_commands, "_skill_commands", {})
    monkeypatch.setattr(skill_commands, "_skill_commands_platform", None)
    skill_commands.scan_skill_commands()

    expanded = server._expand_skill_invocation_for_replay(
        "/worktree-kickoff fix it", "task-1"
    )

    assert "SPIN UP A WORKTREE" in expanded
    assert server._skill_scaffold_projection(expanded) == "/worktree-kickoff fix it"


def test_expand_skill_invocation_for_replay_leaves_ordinary_text_alone(monkeypatch):
    import agent.skill_commands as skill_commands
    import agent.skill_utils as skill_utils

    monkeypatch.setattr(skill_utils, "get_external_skills_dirs", lambda *a, **k: [])
    monkeypatch.setattr(skill_commands, "_skill_commands", {})
    monkeypatch.setattr(skill_commands, "_skill_commands_platform", None)

    assert server._expand_skill_invocation_for_replay("just words", "t") == "just words"
    # A core slash command is not a skill — nothing to expand.
    assert server._expand_skill_invocation_for_replay("/status", "t") == "/status"


def test_command_dispatch_and_catalog_resolve_project_skills_from_the_session_cwd(tmp_path, monkeypatch):
    # TUI/desktop: the RPC thread has no session context and the terminal scope / process env resolve a
    # placeholder ``terminal.cwd`` to $HOME, so project skills of the session's repo never registered and
    # ``/<name>`` died with "not a quick/plugin/bundle/skill command". Two sessions in two trusted repos
    # in ONE process must each catalog and dispatch their own repo's skill (the cached registry is
    # keyed by project root, not just platform + home).
    import agent.skill_utils as skill_utils

    _two_repo_project_skill_sessions(tmp_path, monkeypatch)
    for sid, own, other in (("sid-a", "alpha-skill", "beta-skill"), ("sid-b", "beta-skill", "alpha-skill")):
        catalog = server._methods["commands.catalog"]("c", {"session_id": sid})["result"]
        assert f"/{own}" in catalog["skills"] and f"/{other}" not in catalog["skills"]
        res = server._methods["command.dispatch"]("d", {"name": own, "arg": "go", "session_id": sid})
        assert res["result"]["type"] == "skill", res
        assert f"BODY OF {own.upper()}" in res["result"]["message"]
        miss = server._methods["command.dispatch"]("m", {"name": other, "arg": "", "session_id": sid})
        assert miss["error"]["code"] == 4018
    # Nothing leaks past the RPC: the thread's logical cwd is unbound again.
    assert skill_utils.find_project_root() is None


def test_complete_slash_and_skills_reload_are_bound_to_the_session_cwd(tmp_path, monkeypatch):
    # The '/' popup and /reload-skills ran the registry unbound: the popup never offered a project skill
    # ``command.dispatch`` accepts, and a rescan after that dispatch reported the session's project skills
    # as "Removed" and republished a registry without them.
    import agent.skill_commands as skill_commands

    _two_repo_project_skill_sessions(tmp_path, monkeypatch)
    items = server._methods["complete.slash"]("s", {"text": "/alph", "session_id": "sid-a"})["result"]["items"]
    assert [i["text"] for i in items if i["kind"] == "skill"] == ["alpha-skill"]
    assert server._methods["command.dispatch"]("d", {"name": "alpha-skill", "arg": "", "session_id": "sid-a"})[
        "result"]["type"] == "skill"
    reload = server._methods["skills.reload"]("r", {"session_id": "sid-a"})["result"]
    assert reload["result"]["removed"] == [] and "/alpha-skill" in skill_commands._skill_commands, reload["output"]
    # Another session's reload resolves ITS repo, not the launch env.
    other = server._methods["skills.reload"]("r", {"session_id": "sid-b"})["result"]
    assert {i["name"] for i in other["result"]["added"]} == {"beta-skill"}, other["output"]


def test_history_to_messages_types_a_legacy_auto_continue_row():
    # A crash-interrupted turn used to be typed only AFTER it finished, so a
    # turn killed a second time (or any row written before turn-start typing
    # landed) sits in the DB untyped and painted the raw recovery note as a
    # user bubble. The projection recognizes the synthetic note's fixed
    # prefix so those rows still read as a timeline event.
    history = [
        {"role": "user", "content": "keep going"},
        {"role": "user", "content": server._auto_continue_note("keep going")},
    ]

    projected = server._history_to_messages(history)

    assert projected == [
        {"role": "user", "text": "keep going"},
        {
            "role": "user",
            "text": server._auto_continue_note("keep going"),
            "display_kind": "auto_continue",
        },
    ]


def test_history_to_messages_keeps_real_user_bracket_text():
    # Only role=user rows whose text OPENS with the [System: marker sentinel are
    # bookkeeping notices. A genuine user turn that merely mentions the token is
    # a real message and stays visible.
    history = [
        {"role": "user", "content": "why does [System: ...] show up in my chat?"},
        {"role": "assistant", "content": "it should not"},
    ]

    assert server._history_to_messages(history) == [
        {"role": "user", "text": "why does [System: ...] show up in my chat?"},
        {"role": "assistant", "text": "it should not"},
    ]


@pytest.mark.parametrize("omit_messages", [False, True])
def test_session_resume_uses_parent_lineage_for_display(monkeypatch, omit_messages):
    captured = {}
    target = "tip-omit" if omit_messages else "tip-full"

    class FakeDB:
        def get_session(self, target):
            return {"id": target}

        def reopen_session(self, target):
            captured["reopened"] = target

        def get_resume_conversations(self, session_id):
            return (
                self.get_messages_as_conversation(session_id, repair_alternation=True),
                self.get_messages_as_conversation(session_id, include_ancestors=True),
            )

        def get_ancestor_display_prefix(self, _sid):
            return []

        def get_messages_as_conversation(
            self,
            target,
            include_ancestors=False,
            repair_alternation=False,
            include_row_ids=False,
            **_kwargs,
        ):
            captured.setdefault("history_calls", []).append(
                (target, include_ancestors, include_row_ids)
            )
            return (
                [
                    {"role": "user", "content": "root prompt"},
                    {"role": "assistant", "content": "root answer"},
                ]
                if include_ancestors
                else [{"role": "user", "content": "tip prompt"}]
            )

    monkeypatch.setattr(server, "_get_db", lambda: FakeDB())
    monkeypatch.setattr(server, "_enable_gateway_prompts", lambda: None)
    monkeypatch.setattr(server, "_set_session_context", lambda target: [])
    monkeypatch.setattr(server, "_clear_session_context", lambda tokens: None)
    monkeypatch.setattr(
        server,
        "_make_agent",
        lambda *args, **kwargs: types.SimpleNamespace(model="test"),
    )
    monkeypatch.setattr(
        server,
        "_session_info",
        lambda agent, *a: {"model": "test", "tools": {}, "skills": {}},
    )
    monkeypatch.setattr(
        server, "_init_session", lambda sid, key, agent, history, cols=80, **_kwargs: None
    )
    # The deferred pre-warm timer is neutered module-wide by the autouse
    # _neuter_agent_prewarm_timer fixture; this test only asserts the
    # returned display history.

    params = {"session_id": target}
    if omit_messages:
        params["omit_messages"] = True
    resp = server.handle_request(
        {"id": "1", "method": "session.resume", "params": params}
    )

    expected = [] if omit_messages else [
        {"role": "user", "text": "root prompt"},
        {"role": "assistant", "text": "root answer"},
    ]
    assert resp["result"]["messages"] == expected
    assert resp["result"]["message_count"] == (1 if omit_messages else 2)
    assert resp["result"]["messages_omitted"] is omit_messages


def test_live_visible_history_falls_back_without_db_or_key():
    in_memory = [{"role": "user", "content": "hi"}]
    # No DB handle available.
    assert server._live_visible_history({"session_key": "s"}, None, in_memory) == in_memory

    # DB available but the session has no persist key yet.
    class DB:
        def get_messages_as_conversation(self, *a, **k):  # pragma: no cover - not reached
            raise AssertionError("must not query without a session_key")

    assert server._live_visible_history({}, DB(), in_memory) == in_memory


def test_live_visible_history_falls_back_when_db_empty():
    """A brand-new live session whose first turn hasn't been flushed keeps its
    in-memory history rather than rendering empty."""
    in_memory = [{"role": "user", "content": "fresh turn not flushed yet"}]

    class EmptyDB:
        def get_messages_as_conversation(self, *a, **k):
            return []

    assert server._live_visible_history({"session_key": "s"}, EmptyDB(), in_memory) == in_memory


def test_live_visible_history_falls_back_when_db_raises():
    in_memory = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "yo"}]

    class BrokenDB:
        def get_messages_as_conversation(self, *a, **k):
            raise RuntimeError("db exploded")

    assert server._live_visible_history({"session_key": "s"}, BrokenDB(), in_memory) == in_memory


def test_live_visible_history_keeps_candidate_and_fresh_tail():
    """The hard case: the persisted candidate (missing from in-memory) AND a
    not-yet-flushed live turn (missing from the DB) must BOTH survive."""
    # Persisted display: has the verification candidate, lags the newest turn.
    db_display = [
        {"role": "user", "content": "turn 1"},
        {"role": "assistant", "content": "long substantive answer",
         "finish_reason": "verification_required"},
        {"role": "assistant", "content": "terse verified reply"},
    ]
    # In-memory model history: candidate collapsed out, but has a fresh turn 2.
    in_memory = [
        {"role": "user", "content": "turn 1"},
        {"role": "assistant", "content": "terse verified reply"},
        {"role": "user", "content": "turn 2 not flushed"},
        {"role": "assistant", "content": "turn 2 reply not flushed"},
    ]

    class DB:
        def get_messages_as_conversation(self, key, include_ancestors=False, repair_alternation=False, **_kwargs):
            return list(db_display)

    result = server._live_visible_history({"session_key": "s1"}, DB(), in_memory)
    assert result == [
        {"role": "user", "content": "turn 1"},
        {"role": "assistant", "content": "long substantive answer",
         "finish_reason": "verification_required"},
        {"role": "assistant", "content": "terse verified reply"},
        {"role": "user", "content": "turn 2 not flushed"},
        {"role": "assistant", "content": "turn 2 reply not flushed"},
    ]


def test_reconcile_display_with_live_trusts_db_when_tail_absent():
    """If the DB tail isn't in memory (DB ahead / diverged), don't duplicate —
    serve the persisted display."""
    db_display = [
        {"role": "user", "content": "a"},
        {"role": "assistant", "content": "b"},
    ]
    in_memory = [{"role": "user", "content": "unrelated"}]
    assert server._reconcile_display_with_live(db_display, in_memory) == db_display
    assert server._reconcile_display_with_live([], in_memory) == in_memory
    assert server._reconcile_display_with_live(db_display, []) == db_display


def test_live_visible_history_matches_eager_resume_with_real_db(tmp_path):
    """E2E cross-builder consistency against a real SessionDB.

    A persisted verification candidate (finish_reason=verification_required)
    is collapsed out of the model history by repair_message_sequence but kept
    in the display lineage (#65919). The warm/live projection
    (_live_visible_history) must equal the eager session.resume display
    projection — both keeping the candidate — so switching to a live session
    shows the same substantive answer a cold resume would.
    """
    from hermes_state import SessionDB

    db = SessionDB(db_path=tmp_path / "state.db")
    db.create_session("s1", source="tui")
    db.append_message("s1", role="user", content="do the thing")
    db.append_message(
        "s1", role="assistant", content="long substantive answer",
        finish_reason="verification_required",
    )
    db.append_message(
        "s1", role="assistant", content="terse verified reply", finish_reason="stop",
    )

    model_history, display_history = db.get_resume_conversations("s1")

    # The divergence #65919 introduced: candidate absent from the model
    # projection, present in the display projection.
    assert not any("long substantive" in (m.get("content") or "") for m in model_history)
    assert any("long substantive" in (m.get("content") or "") for m in display_history)

    # Eager session.resume serves the display projection.
    eager_messages = server._history_to_messages(display_history)
    # Warm/live reuse: in-memory history is the collapsed model projection.
    live_history = server._live_visible_history({"session_key": "s1"}, db, list(model_history))
    # They must agree — the candidate survives the warm switch.
    assert server._history_to_messages(live_history) == eager_messages
    assert any(m.get("text") == "long substantive answer" for m in eager_messages)


def test_live_visible_history_keeps_candidate_and_new_flushed_turn_real_db(tmp_path):
    """Real-DB variant of the combined case: a candidate from turn 1 AND a
    fully-flushed turn 2 both appear once."""
    from hermes_state import SessionDB

    db = SessionDB(db_path=tmp_path / "state.db")
    db.create_session("s1", source="tui")
    db.append_message("s1", role="user", content="turn 1")
    db.append_message(
        "s1", role="assistant", content="candidate answer",
        finish_reason="verification_required",
    )
    db.append_message("s1", role="assistant", content="verified reply", finish_reason="stop")
    db.append_message("s1", role="user", content="turn 2")
    db.append_message("s1", role="assistant", content="turn 2 reply", finish_reason="stop")

    model_history, display_history = db.get_resume_conversations("s1")
    live_history = server._live_visible_history({"session_key": "s1"}, db, list(model_history))
    texts = [m.get("text") for m in server._history_to_messages(live_history)]

    assert texts == [
        "turn 1",
        "candidate answer",
        "verified reply",
        "turn 2",
        "turn 2 reply",
    ]


def test_live_session_payload_reads_profile_db_not_launch_db(monkeypatch, tmp_path):
    """Warm/live reuse for a non-launch profile session must open that
    profile's state.db, not the process launch DB.

    App-global remote mode stores verification candidates in the resumed
    profile's DB. ``_live_session_payload`` previously hard-coded
    ``_get_db()`` (launch), so the display projection missed those rows and
    fell back to collapsed in-memory model history — while eager
    ``session.resume`` against the same profile still showed them.
    """
    from hermes_state import SessionDB

    launch_home = tmp_path / "launch"
    profile_home = tmp_path / "profile"
    launch_home.mkdir()
    profile_home.mkdir()

    launch_db = SessionDB(db_path=launch_home / "state.db")
    profile_db = SessionDB(db_path=profile_home / "state.db")
    profile_db.create_session("s-profile", source="tui")
    profile_db.append_message("s-profile", role="user", content="do the thing")
    profile_db.append_message(
        "s-profile",
        role="assistant",
        content="long substantive answer",
        finish_reason="verification_required",
    )
    profile_db.append_message(
        "s-profile",
        role="assistant",
        content="terse verified reply",
        finish_reason="stop",
    )
    model_history, display_history = profile_db.get_resume_conversations("s-profile")
    assert not any("long substantive" in (m.get("content") or "") for m in model_history)
    assert any("long substantive" in (m.get("content") or "") for m in display_history)

    session = {
        "session_key": "s-profile",
        "profile_home": str(profile_home),
        "agent": None,
        "history": list(model_history),
        "display_history_prefix": [],
        "history_lock": threading.Lock(),
        "created_at": 1.0,
        "last_active": 1.0,
        "running": False,
    }
    # Launch DB has no row for this session — the pre-fix path would miss
    # candidates and fall back to collapsed in-memory history.
    monkeypatch.setattr(server, "_get_db", lambda: launch_db)

    payload = server._live_session_payload("live1", session, touch=False)
    texts = [m.get("text") for m in payload.get("messages") or []]

    assert "long substantive answer" in texts
    assert texts == [m.get("text") for m in server._history_to_messages(display_history)]


def test_lazy_child_watch_resume_serves_candidate_inclusive_display(monkeypatch, tmp_path):
    """The delegated-child watch-window cold resume (lazy=True) must serve the
    verbatim display projection so a persisted verification candidate is not
    collapsed out of the watch window (#65919 sibling of the warm-payload fix).
    """
    from hermes_state import SessionDB

    db = SessionDB(db_path=tmp_path / "state.db")
    db.create_session("child1", source="tui")
    db.append_message("child1", role="user", content="child prompt")
    db.append_message(
        "child1", role="assistant", content="child substantive answer",
        finish_reason="verification_required",
    )
    db.append_message(
        "child1", role="assistant", content="child terse reply", finish_reason="stop",
    )

    lease = types.SimpleNamespace(session_id="child1", release=lambda: None)

    monkeypatch.setattr(server, "_get_db", lambda: db)
    monkeypatch.setattr(server, "_enable_gateway_prompts", lambda: None)
    monkeypatch.setattr(
        server, "_claim_active_session_slot", lambda *a, **k: (lease, None)
    )
    monkeypatch.setattr(
        server, "_deferred_session_record", lambda *a, **k: {"created_at": 123.0}
    )
    monkeypatch.setattr(server, "_claim_or_reuse_live", lambda *a, **k: None)
    monkeypatch.setattr(server, "_child_run_active", lambda *a, **k: False)
    monkeypatch.setattr(server, "_schedule_session_cap_enforcement", lambda *a, **k: None)

    resp = server.handle_request(
        {
            "id": "1",
            "method": "session.resume",
            "params": {"session_id": "child1", "lazy": True},
        }
    )

    assert "error" not in resp, resp
    texts = [m.get("text") for m in resp["result"]["messages"]]
    assert "child substantive answer" in texts
    assert texts == ["child prompt", "child substantive answer", "child terse reply"]


def test_session_resume_deferred_history_acknowledges_and_reuses(monkeypatch):
    history_started = threading.Event()
    release_history = threading.Event()
    build_started = threading.Event()
    history_calls = []
    auto_continue_calls = []
    ancestor = {"role": "assistant", "content": "ancestor"}
    loaded = {"role": "user", "content": "loaded"}

    class FakeDB:
        def get_session(self, target):
            return {"id": target, "message_count": 1200}

        def resolve_resume_session_id(self, target):
            return target

        def reopen_session(self, target):
            assert target == "large-session"

        def get_resume_conversations(self, target):
            history_calls.append(("resume", target))
            history_started.set()
            assert release_history.wait(timeout=2.0)
            return [loaded], [ancestor, loaded]

        def get_ancestor_display_prefix(self, target):
            history_calls.append(("prefix", target))
            return [ancestor]

    monkeypatch.setattr(server, "_get_db", lambda: FakeDB())
    monkeypatch.setattr(server, "_enable_gateway_prompts", lambda: None)
    monkeypatch.setattr(server, "_schedule_session_cap_enforcement", lambda: None)
    monkeypatch.setattr(
        server,
        "_start_agent_build",
        lambda _sid, _session: build_started.set(),
    )
    monkeypatch.setattr(
        server,
        "_maybe_schedule_auto_continue",
        lambda sid, session, stored_id: auto_continue_calls.append(
            (sid, session, stored_id)
        ),
    )

    try:
        first = server._methods["session.resume"](
            "r1",
            {
                "session_id": "large-session",
                "source": "desktop",
                "defer_history": True,
            },
        )

        assert first["result"]["hydrating"] is True
        assert first["result"]["messages"] == []
        assert first["result"]["message_count"] == 1200
        assert history_started.wait(timeout=1.0)

        second = server._methods["session.resume"](
            "r2",
            {"session_id": "large-session", "defer_history": True},
        )
        assert second["result"]["session_id"] == first["result"]["session_id"]
        assert second["result"]["hydrating"] is True
        assert second["result"]["messages"] == []

        release_history.set()
        sid = first["result"]["session_id"]
        assert server._sessions[sid]["resume_history_ready"].wait(timeout=1.0)
        assert build_started.wait(timeout=1.0)
        assert history_calls == [
            ("resume", "large-session"),
            ("prefix", "large-session"),
        ]
        assert server._sessions[sid]["history"] == [loaded]
        assert server._sessions[sid]["display_history_prefix"] == [ancestor]
        assert server._sessions[sid]["resume_message_count"] == 2
        assert auto_continue_calls == [(sid, server._sessions[sid], "large-session")]
    finally:
        release_history.set()
        for sid, session in list(server._sessions.items()):
            if session.get("session_key") == "large-session":
                lease = session.get("active_session_lease")
                if lease is not None:
                    lease.release()
                server._sessions.pop(sid, None)


def test_session_resume_deferred_history_failure_can_retry(monkeypatch):
    first_released = threading.Event()
    build_started = threading.Event()
    attempts = 0

    class FakeDB:
        def get_session(self, target):
            return {"id": target, "message_count": 1}

        def resolve_resume_session_id(self, target):
            return target

        def reopen_session(self, _target):
            pass

        def get_resume_conversations(self, _target):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                first_released.set()
                raise RuntimeError("sqlite read failed")
            loaded = [{"role": "user", "content": "retry loaded"}]
            return loaded, loaded

        def get_ancestor_display_prefix(self, _target):
            return []

    monkeypatch.setattr(server, "_get_db", lambda: FakeDB())
    monkeypatch.setattr(
        server,
        "_claim_active_session_slot",
        lambda *_args, **_kwargs: pytest.fail(
            "resume must not claim a session slot before the first prompt"
        ),
    )
    monkeypatch.setattr(server, "_enable_gateway_prompts", lambda: None)
    monkeypatch.setattr(server, "_schedule_session_cap_enforcement", lambda: None)
    monkeypatch.setattr(
        server,
        "_start_agent_build",
        lambda _sid, _session: build_started.set(),
    )

    try:
        first = server._methods["session.resume"](
            "r1",
            {"session_id": "retry-session", "defer_history": True},
        )
        first_sid = first["result"]["session_id"]
        assert first_released.wait(timeout=1.0)
        assert first_sid not in server._sessions

        second = server._methods["session.resume"](
            "r2",
            {"session_id": "retry-session", "defer_history": True},
        )
        second_sid = second["result"]["session_id"]
        assert second_sid != first_sid
        assert server._sessions[second_sid]["resume_history_ready"].wait(timeout=1.0)
        assert build_started.wait(timeout=1.0)
    finally:
        for sid, session in list(server._sessions.items()):
            if session.get("session_key") == "retry-session":
                lease = session.get("active_session_lease")
                if lease is not None:
                    lease.release()
                server._sessions.pop(sid, None)


def test_session_resume_deferred_history_close_cancels_build(monkeypatch):
    history_started = threading.Event()
    release_history = threading.Event()
    build_started = threading.Event()

    class FakeDB:
        def get_session(self, target):
            return {"id": target, "message_count": 1}

        def resolve_resume_session_id(self, target):
            return target

        def reopen_session(self, _target):
            pass

        def get_resume_conversations(self, _target):
            history_started.set()
            assert release_history.wait(timeout=2.0)
            loaded = [{"role": "user", "content": "late"}]
            return loaded, loaded

        def get_ancestor_display_prefix(self, _target):
            return []

    monkeypatch.setattr(server, "_get_db", lambda: FakeDB())
    monkeypatch.setattr(server, "_enable_gateway_prompts", lambda: None)
    monkeypatch.setattr(server, "_schedule_session_cap_enforcement", lambda: None)
    monkeypatch.setattr(
        server,
        "_start_agent_build",
        lambda _sid, _session: build_started.set(),
    )

    response = {}
    try:
        response = server._methods["session.resume"](
            "r1",
            {"session_id": "cancel-session", "defer_history": True},
        )
        sid = response["result"]["session_id"]
        session = server._sessions[sid]
        assert history_started.wait(timeout=1.0)

        assert server._close_session_by_id(sid, end_reason="tui_close") is True
        assert session["resume_history_ready"].is_set()
        assert session["resume_history_error"] == "session resume cancelled"

        release_history.set()
        time.sleep(0.05)
        assert not build_started.is_set()
        assert sid not in server._sessions
    finally:
        release_history.set()
        server._sessions.pop(response.get("result", {}).get("session_id", ""), None)


def test_session_resume_follows_compression_tip(monkeypatch, tmp_path):
    """Resuming a rotated-out parent id must load the continuation's messages.

    Regression for the desktop "I came back and the reply isn't there" report:
    auto-compression ends the live session and forks a continuation child, so a
    resume on the parent id (the desktop's routed id when the chat was opened
    before it rotated) used to reload the pre-compression transcript and drop
    the response generated after compression. session.resume must follow the
    compression tip via resolve_resume_session_id.
    """
    from hermes_state import SessionDB

    db = SessionDB(db_path=tmp_path / "state.db")
    base = int(time.time()) - 10_000
    db.create_session("parent_root", source="tui")
    db.append_message(
        "parent_root", role="user", content="pre-compression turn",
        timestamp=base + 10,
    )
    db.end_session("parent_root", "compression")
    db.create_session("cont_tip", source="tui", parent_session_id="parent_root")
    db.append_message(
        "cont_tip", role="assistant", content="post-compression reply",
        timestamp=base + 110,
    )
    conn = db._conn
    assert conn is not None
    conn.execute(
        "UPDATE sessions SET started_at = ?, ended_at = ? WHERE id = 'parent_root'",
        (base, base + 50),
    )
    conn.execute("UPDATE sessions SET started_at = ? WHERE id = 'cont_tip'", (base + 100,))
    conn.commit()

    captured = {}

    def fake_make_agent(sid, key, session_id=None, session_db=None, **kwargs):
        # Record only the FIRST (synchronous, eager) build. A stray background
        # build leaked from an earlier test's deferred resume could otherwise
        # overwrite this with its own session_id and corrupt the assertion.
        captured.setdefault("agent_session_id", session_id)
        return types.SimpleNamespace(model="test", provider="test")

    monkeypatch.setattr(server, "_get_db", lambda: db)
    monkeypatch.setattr(server, "_enable_gateway_prompts", lambda: None)
    monkeypatch.setattr(server, "_set_session_context", lambda target, cwd=None: [])
    monkeypatch.setattr(server, "_clear_session_context", lambda tokens: None)
    monkeypatch.setattr(server, "_make_agent", fake_make_agent)
    monkeypatch.setattr(
        server, "_session_info", lambda agent, *a: {"model": "test", "tools": {}, "skills": {}}
    )
    monkeypatch.setattr(
        server, "_init_session", lambda sid, key, agent, history, cols=80, **_kwargs: None
    )

    try:
        # eager_build: this asserts the synchronously-built agent binds to the
        # resolved tip (captured["agent_session_id"]); the compression-tip
        # resolution itself runs before the build and is mode-agnostic.
        resp = server.handle_request(
            {"id": "1", "method": "session.resume", "params": {"session_id": "parent_root", "eager_build": True}}
        )
    finally:
        db.close()

    # The agent must bind to the continuation tip, and the returned transcript
    # must include the post-compression reply (which lives only in the tip).
    assert resp["result"]["session_key"] == "cont_tip"
    assert captured["agent_session_id"] == "cont_tip"
    texts = [m.get("text") for m in resp["result"]["messages"]]
    assert "post-compression reply" in texts


def test_session_resume_passes_stored_runtime_to_agent(monkeypatch):
    captured = {}

    class FakeDB:
        def get_session(self, target):
            return {
                "id": target,
                "model": "gpt-5.4",
                "billing_provider": "openai-codex",
                "model_config": '{"reasoning_config":{"enabled":true,"effort":"high"},"service_tier":"priority","base_url":"https://custom.example/v1","api_mode":"chat_completions"}',
            }

        def reopen_session(self, target):
            pass

        def get_resume_conversations(self, session_id):
            return (
                self.get_messages_as_conversation(session_id, repair_alternation=True),
                self.get_messages_as_conversation(session_id, include_ancestors=True),
            )

        def get_ancestor_display_prefix(self, _sid):
            return []

        def get_messages_as_conversation(self, target, include_ancestors=False, repair_alternation=False, **_kwargs):
            return [{"role": "user", "content": "hello"}]

    def fake_make_agent(sid, key, session_id=None, session_db=None, **kwargs):
        captured.update(kwargs)
        return types.SimpleNamespace(model="gpt-5.4", provider="openai-codex")

    monkeypatch.setattr(server, "_get_db", lambda: FakeDB())
    monkeypatch.setattr(server, "_enable_gateway_prompts", lambda: None)
    monkeypatch.setattr(server, "_set_session_context", lambda target, cwd=None: [])
    monkeypatch.setattr(server, "_clear_session_context", lambda tokens: None)
    monkeypatch.setattr(server, "_make_agent", fake_make_agent)
    monkeypatch.setattr(server, "_session_info", lambda agent, *a: {"model": agent.model, "provider": agent.provider})

    def fake_init_session(sid, key, agent, history, cols=80, **_kwargs):
        server._sessions[sid] = {"agent": agent, "session_key": key}

    monkeypatch.setattr(server, "_init_session", fake_init_session)

    # eager_build: this asserts the synchronous build contract (stored runtime
    # overrides reach _make_agent, info comes from _session_info). The deferred
    # default restores the same overrides via _start_agent_build off-thread.
    resp = server.handle_request(
        {"id": "1", "method": "session.resume", "params": {"session_id": "stored-session", "eager_build": True}}
    )

    assert captured["model_override"] == {
        "model": "gpt-5.4",
        "provider": "openai-codex",
        "base_url": "https://custom.example/v1",
        "api_mode": "chat_completions",
    }
    assert captured["provider_override"] == "openai-codex"
    assert captured["reasoning_config_override"] == {"enabled": True, "effort": "high"}
    assert captured["service_tier_override"] == "priority"
    runtime_sid = resp["result"]["session_id"]
    assert server._sessions[runtime_sid]["model_override"] == captured["model_override"]


def test_session_resume_profile_uses_profile_db_cwd(monkeypatch, tmp_path):
    target = "stored-profile-session"
    launch_cwd = tmp_path / "launch"
    profile_cwd = tmp_path / "worker"
    profile_home = tmp_path / "profiles" / "worker"
    launch_cwd.mkdir()
    profile_cwd.mkdir()
    profile_home.mkdir(parents=True)
    captured = {}

    class ProfileDB:
        def get_session(self, _target):
            return {"id": target, "cwd": str(profile_cwd)}

        def get_session_by_title(self, _target):
            return None

        def reopen_session(self, _target):
            captured["reopened"] = _target

        def get_resume_conversations(self, session_id):
            return (
                self.get_messages_as_conversation(session_id, repair_alternation=True),
                self.get_messages_as_conversation(session_id, include_ancestors=True),
            )

        def get_ancestor_display_prefix(self, _sid):
            return []

        def get_messages_as_conversation(self, _target, include_ancestors=False, repair_alternation=False, **_kwargs):
            return [{"role": "user", "content": "hello"}]

        def update_session_cwd(self, *_args):
            raise AssertionError("profile row already has cwd")

    class LaunchDB:
        def get_session(self, _target):
            return {"id": target, "cwd": str(launch_cwd)}

        def update_session_cwd(self, *_args):
            captured["launch_update"] = True

    profile_db = ProfileDB()
    launch_db = LaunchDB()

    class FakeWorker:
        def __init__(self, *_args, **_kwargs):
            pass

        def close(self):
            pass

    def fake_make_agent(sid, key, session_id=None, session_db=None, **kwargs):
        captured["agent_db"] = session_db
        captured["agent_cwd"] = kwargs.get("cwd_override")
        return types.SimpleNamespace(model="test/model")

    monkeypatch.setenv("TERMINAL_CWD", str(launch_cwd))
    monkeypatch.setattr(server, "_profile_home", lambda _profile: profile_home)
    monkeypatch.setattr("hermes_state_registry.acquire", lambda db_path=None: profile_db)
    monkeypatch.setattr(server, "_get_db", lambda: launch_db)
    monkeypatch.setattr(server, "_enable_gateway_prompts", lambda: None)
    monkeypatch.setattr(
        server,
        "_set_session_context",
        lambda target, cwd=None: captured.setdefault("context_cwd", cwd) or [],
    )
    monkeypatch.setattr(server, "_clear_session_context", lambda tokens: None)
    monkeypatch.setattr(server, "_make_agent", fake_make_agent)
    monkeypatch.setattr(server, "_SlashWorker", FakeWorker)
    monkeypatch.setattr(server, "_wire_callbacks", lambda _sid: None)
    monkeypatch.setattr(server, "_emit", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        server,
        "_session_info",
        lambda _agent, session=None: {"cwd": session.get("cwd") if session else ""},
    )

    import tools.approval as approval

    monkeypatch.setattr(approval, "register_gateway_notify", lambda key, cb: None)
    monkeypatch.setattr(approval, "load_permanent_allowlist", lambda: None)

    try:
        # eager_build: asserts the synchronous build receives the profile's db
        # (the deferred default builds with the same db via _start_agent_build).
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.resume",
                "params": {"session_id": target, "profile": "worker", "eager_build": True},
            }
        )

        assert "error" not in resp
        sid = resp["result"]["session_id"]
        assert captured["agent_db"] is profile_db
        assert captured["context_cwd"] == str(profile_cwd)
        assert captured["agent_cwd"] == str(profile_cwd)
        assert server._sessions[sid]["cwd"] == str(profile_cwd)
        assert resp["result"]["info"]["cwd"] == str(profile_cwd)
        assert "launch_update" not in captured
    finally:
        server._sessions.clear()


def test_session_cwd_set_profile_session_updates_profile_db(monkeypatch, tmp_path):
    target = "stored-profile-session"
    profile_home = tmp_path / "profiles" / "worker"
    profile_home.mkdir(parents=True)
    new_cwd = tmp_path / "new-workspace"
    new_cwd.mkdir()
    captured = {}

    class ProfileDB:
        def update_session_cwd(self, session_id, cwd, git_branch=None, git_repo_root=None):
            captured["profile_update"] = (session_id, cwd)

        def close(self):
            captured["profile_closed"] = True

    class LaunchDB:
        def update_session_cwd(self, *_args):
            captured["launch_update"] = True

    profile_db = ProfileDB()

    import tools.terminal_tool_lifecycle as terminal_tool_lifecycle

    monkeypatch.setattr("hermes_state_registry.acquire", lambda db_path=None: profile_db)
    monkeypatch.setattr(server, "_get_db", lambda: LaunchDB())
    monkeypatch.setattr(terminal_tool_lifecycle, "cleanup_vm", lambda _key: None)
    monkeypatch.setattr(server, "_register_session_cwd", lambda _session: None)

    session = {"session_key": target, "profile_home": str(profile_home)}
    assert server._set_session_cwd(session, str(new_cwd)) == str(new_cwd)
    assert session["cwd"] == str(new_cwd)
    assert session["explicit_cwd"] is True
    assert captured["profile_update"] == (target, str(new_cwd))
    assert captured["profile_closed"] is True
    assert "launch_update" not in captured


def test_stored_session_runtime_overrides_skips_bare_billing_provider(monkeypatch):
    """A bare billing bucket ("custom"/"auto") must not be restored as the provider
    identity on resume. A custom endpoint that never used `/model` persists only
    `billing_provider="custom"`; restoring that broke `session.resume` with "No LLM provider
    configured" (agent_init treats it as non-routable). ``"openrouter"`` is NOT a bare bucket
    — it is a fully routable provider; see #57588. A real provider, or an explicit
    `model_config.provider`, is still restored.
    """
    # Bare "custom" bucket, no explicit model_config.provider: no provider override restored.
    ov = server._stored_session_runtime_overrides({"model": "my-model", "billing_provider": "custom"})
    assert "provider_override" not in ov
    assert ov["model_override"]["provider"] is None

    for bare in ("auto", "custom"):
        ov = server._stored_session_runtime_overrides({"model": "m", "billing_provider": bare})
        assert "provider_override" not in ov

    # A real provider in billing_provider is still restored.
    ov = server._stored_session_runtime_overrides({"model": "m", "billing_provider": "anthropic"})
    assert ov["provider_override"] == "anthropic"
    assert ov["model_override"]["provider"] == "anthropic"

    # An explicit ROUTABLE provider in model_config wins over the bare billing
    # bucket. It must actually resolve in the registry — a stale/renamed
    # provider is dropped (see TestStaleProviderNameFallsBack).
    cfg = {
        "custom_providers": [
            {
                "name": "myendpoint",
                "base_url": "https://myendpoint.invalid/v1",
                "api_key": "sk-test",
                "model": "m",
            }
        ]
    }
    import hermes_cli.runtime_provider as rp

    monkeypatch.setattr(rp, "load_config", lambda: cfg)
    monkeypatch.setattr("hermes_cli.config.load_config", lambda: cfg)
    ov = server._stored_session_runtime_overrides(
        {"model": "m", "billing_provider": "custom", "model_config": {"provider": "custom:myendpoint"}}
    )
    assert ov["provider_override"] == "custom:myendpoint"
    assert ov["model_override"]["provider"] == "custom:myendpoint"


def test_stored_session_runtime_overrides_restores_explicit_normal_tier():
    overrides = server._stored_session_runtime_overrides(
        {
            "model": "gpt-5.4",
            "model_config": {"service_tier": "normal"},
        }
    )

    assert "service_tier_override" in overrides
    assert overrides["service_tier_override"] == ""


def test_openrouter_session_resume_restores_provider():
    """OpenRouter is a fully routable provider — sessions that used OpenRouter must
    restore the "openrouter" provider override on resume, not fall through to whatever
    the current global model is.  (#57588)
    """
    # OpenRouter session with no explicit model_config.provider (the common case
    # for sessions that never used /model): billing_provider="openrouter" should
    # be restored as the provider override.
    ov = server._stored_session_runtime_overrides(
        {"model": "anthropic/claude-opus-4.8", "billing_provider": "openrouter"}
    )
    assert ov["provider_override"] == "openrouter"
    assert ov["model_override"]["provider"] == "openrouter"
    assert ov["model_override"]["model"] == "anthropic/claude-opus-4.8"

    # When an explicit model_config.provider exists, it takes precedence over
    # billing_provider (this path was already correct).
    ov = server._stored_session_runtime_overrides(
        {
            "model": "anthropic/claude-opus-4.8",
            "billing_provider": "openrouter",
            "model_config": {"provider": "openrouter", "base_url": "https://openrouter.ai/api/v1"},
        }
    )
    assert ov["provider_override"] == "openrouter"


def test_persist_live_session_runtime_preserves_resume_metadata(monkeypatch):
    updates = {}

    class FakeDB:
        def get_session(self, session_id):
            assert session_id == "stored-session"
            return {"model_config": '{"_branched_from":"root"}'}

        def update_session_meta(self, session_id, model_config_json, model=None):
            updates["meta"] = (session_id, json.loads(model_config_json), model)

    agent = types.SimpleNamespace(
        model="gpt-5.4",
        provider="openai-codex",
        base_url="https://custom.example/v1",
        api_mode="chat_completions",
        reasoning_config={"enabled": True, "effort": "high"},
        service_tier="priority",
        _session_db=FakeDB(),
    )

    server._persist_live_session_runtime({"agent": agent, "session_key": "stored-session"})

    assert "model" not in updates
    assert updates["meta"] == (
        "stored-session",
        {
            "_branched_from": "root",
            "model": "gpt-5.4",
            "provider": "openai-codex",
            "base_url": "https://custom.example/v1",
            "api_mode": "chat_completions",
            "reasoning_config": {"enabled": True, "effort": "high"},
            "service_tier": "priority",
        },
        "gpt-5.4",
    )


def test_persist_live_session_runtime_preserves_explicit_normal_tier():
    updates = {}

    class FakeDB:
        def get_session(self, _session_id):
            return {"model_config": '{"service_tier":"priority"}'}

        def update_session_meta(self, _session_id, model_config_json, model=None):
            updates["config"] = json.loads(model_config_json)

    agent = types.SimpleNamespace(
        model="gpt-5.4",
        provider="openai-codex",
        base_url=None,
        api_mode=None,
        reasoning_config=None,
        service_tier="",
        _session_db=FakeDB(),
    )

    server._persist_live_session_runtime(
        {
            "agent": agent,
            "session_key": "stored-session",
            "create_service_tier_override": "",
        }
    )

    assert updates["config"]["service_tier"] == "normal"


def test_status_callback_emits_kind_and_text():
    with patch("tui_gateway.server._emit") as emit:
        cb = server._agent_cbs("sid")["status_callback"]
        cb("context_pressure", "85% to compaction")

    emit.assert_called_once_with(
        "status.update",
        "sid",
        {"kind": "context_pressure", "text": "85% to compaction"},
    )


def test_status_callback_accepts_single_message_argument():
    with patch("tui_gateway.server._emit") as emit:
        cb = server._agent_cbs("sid")["status_callback"]
        cb("thinking...")

    emit.assert_called_once_with(
        "status.update",
        "sid",
        {"kind": "status", "text": "thinking..."},
    )


def test_resolve_model_uses_inference_model_env(monkeypatch):
    monkeypatch.delenv("HERMES_MODEL", raising=False)
    monkeypatch.setenv("HERMES_INFERENCE_MODEL", " anthropic/claude-sonnet-4.6\n")

    assert server._resolve_model() == "anthropic/claude-sonnet-4.6"


def test_resolve_model_strips_config_model(monkeypatch):
    monkeypatch.delenv("HERMES_MODEL", raising=False)
    monkeypatch.delenv("HERMES_INFERENCE_MODEL", raising=False)
    monkeypatch.setattr(
        server, "_load_cfg", lambda: {"model": {"default": " nous/hermes-test "}}
    )

    assert server._resolve_model() == "nous/hermes-test"


def test_config_sync_switches_unpinned_session(monkeypatch):
    _patch_config_model(monkeypatch, "new/model", provider="nous")
    session = _sync_test_session(config_model_seen=("old/model", "nous"))
    calls = []
    monkeypatch.setattr(
        server,
        "_apply_model_switch",
        lambda sid, sess, raw, **kw: calls.append((sid, raw, kw)),
    )

    server._sync_agent_model_with_config("sid", session)

    assert calls == [
        (
            "sid",
            "new/model --provider nous",
            {
                "confirm_expensive_model": True,
                "pin_session_override": False,
                "persist_override": False,
            },
        )
    ]
    assert session["config_model_seen"] == ("new/model", "nous")
