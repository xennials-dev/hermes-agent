"""tui_gateway.server — config.set approval/toggles, setup runtime checks and slash completion.

Split from test_tui_gateway_server.py; shared fixtures and helpers live
in tests/tui_gateway/_server_test_helpers.py.
"""

import json
import os
import threading
import types
from pathlib import Path
import pytest
from tui_gateway import server

from tests.tui_gateway._server_test_helpers import (
    _neuter_agent_prewarm_timer,  # autouse
    _reap_leaked_notification_pollers,  # autouse
    _session,
    _slash_completions,
    _slash_skill_fixtures,
)


def test_config_get_approval_mode_fails_safe_to_manual_for_invalid_explicit_value(
    tmp_path, monkeypatch
):
    import hermes_yaml as yaml

    monkeypatch.setattr(server, "_hermes_home", tmp_path)
    # _load_approval_mode delegates to the canonical resolver in
    # tools.approval, which reads via hermes_cli.config.load_config —
    # that path resolves HERMES_HOME from the environment, not
    # server._hermes_home.
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    (tmp_path / "config.yaml").write_text(
        yaml.safe_dump({"approvals": {"mode": "sometimes"}})
    )

    response = server.handle_request(
        {"id": "1", "method": "config.get", "params": {"key": "approvals.mode"}}
    )
    assert response["result"]["value"] == "manual"


def test_config_get_approval_mode_normalizes_yaml_off(tmp_path, monkeypatch):
    import hermes_yaml as yaml

    monkeypatch.setattr(server, "_hermes_home", tmp_path)
    # See fail-safe test above: the canonical resolver reads via
    # load_config, which resolves HERMES_HOME from the environment.
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    (tmp_path / "config.yaml").write_text(
        yaml.safe_dump({"approvals": {"mode": False}})
    )

    response = server.handle_request(
        {"id": "1", "method": "config.get", "params": {"key": "approvals.mode"}}
    )
    assert response["result"]["value"] == "off"


def test_config_set_approval_mode_persists_three_way_value_and_emits_live_status(
    tmp_path, monkeypatch
):
    import hermes_yaml as yaml

    monkeypatch.setattr(server, "_hermes_home", tmp_path)
    # config.set writes via server._hermes_home, but the post-write
    # session.info emit resolves the effective mode through the canonical
    # tools.approval resolver (load_config → env HERMES_HOME).
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    emitted = []
    monkeypatch.setattr(server, "_emit", lambda *args: emitted.append(args))
    server._sessions["sid"] = {"agent": object(), "session_key": "profile-session"}

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "config.set",
                "params": {"key": "approvals.mode", "value": "manual"},
            }
        )
    finally:
        server._sessions.clear()

    assert resp["result"] == {"key": "approvals.mode", "value": "manual"}
    assert yaml.safe_load((tmp_path / "config.yaml").read_text())["approvals"]["mode"] == "manual"
    assert emitted and emitted[0][0:2] == ("session.info", "sid")
    assert emitted[0][2]["approval_mode"] == "manual"


def test_pet_gallery_quoted_false_enabled_reports_disabled(tmp_path, monkeypatch):
    """display.pet.enabled: "false" (quoted) must report enabled=False.

    The old check was bool(value) — bool('false') is True, so a hand-edited
    quoted YAML value kept the petdex mascot enabled against the operator's
    explicit intent.
    """
    import hermes_yaml as yaml

    monkeypatch.setattr(server, "_hermes_home", tmp_path)
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    (tmp_path / "config.yaml").write_text(
        yaml.safe_dump({"display": {"pet": {"enabled": "false"}}})
    )

    response = server.handle_request(
        {"id": "1", "method": "pet.gallery", "params": {}}
    )
    assert response["result"]["enabled"] is False


def test_pet_info_known_revision_elides_spritesheet(monkeypatch):
    """pet.info with a matching knownRevision must not resend the sheet bytes.

    The spritesheet payload is multi-MB; resending it on every backstop
    refresh stalls the WS write loop (#54730). A caller passing the revision
    it already holds gets metadata plus spritesheetUnchanged instead.
    """

    class _FakePet:
        slug = "codex"
        display_name = "Codex"
        exists = True
        spritesheet = None

    payload = {
        "slug": "codex",
        "displayName": "Codex",
        "mime": "image/png",
        "spritesheetBase64": "A" * 1024,
        "spritesheetRevision": "123:456",
        "frameW": 192,
        "frameH": 208,
        "scale": 0.33,
    }

    monkeypatch.setattr(server, "_pet_active_selection", lambda: (True, _FakePet(), 0.33))
    monkeypatch.setattr(server, "_pet_sprite_payload", lambda pet, *, scale: dict(payload))

    # Matching revision: bytes elided, unchanged marker set.
    resp = server.handle_request(
        {"id": "1", "method": "pet.info", "params": {"knownRevision": "123:456"}}
    )
    assert resp["result"]["enabled"] is True
    assert "spritesheetBase64" not in resp["result"]
    assert resp["result"]["spritesheetUnchanged"] is True
    assert resp["result"]["spritesheetRevision"] == "123:456"

    # Stale revision: full payload still flows.
    resp = server.handle_request(
        {"id": "2", "method": "pet.info", "params": {"knownRevision": "999:999"}}
    )
    assert resp["result"]["spritesheetBase64"] == "A" * 1024
    assert "spritesheetUnchanged" not in resp["result"]

    # No revision (legacy callers): full payload.
    resp = server.handle_request({"id": "3", "method": "pet.info", "params": {}})
    assert resp["result"]["spritesheetBase64"] == "A" * 1024


def test_config_set_approval_mode_rejects_unknown_value():
    resp = server.handle_request(
        {
            "id": "1",
            "method": "config.set",
            "params": {"key": "approvals.mode", "value": "sometimes"},
        }
    )

    assert resp["error"]["code"] == 4002


def test_config_set_yolo_global_scope_honors_explicit_value(tmp_path, monkeypatch):
    """An explicit value pins global approvals.mode regardless of prior state."""
    import hermes_yaml as yaml

    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.safe_dump({"approvals": {"mode": "manual"}}))
    monkeypatch.setattr(server, "_hermes_home", tmp_path)

    resp = server.handle_request(
        {
            "id": "1",
            "method": "config.set",
            "params": {"key": "yolo", "scope": "global", "value": "1"},
        }
    )
    assert resp["result"]["value"] == "1"
    assert yaml.safe_load(cfg_path.read_text())["approvals"]["mode"] == "off"

    # Setting it on again is idempotent — stays off.
    resp_again = server.handle_request(
        {
            "id": "2",
            "method": "config.set",
            "params": {"key": "yolo", "scope": "global", "value": "1"},
        }
    )
    assert resp_again["result"]["value"] == "1"
    assert yaml.safe_load(cfg_path.read_text())["approvals"]["mode"] == "off"


def test_config_set_fast_updates_live_agent_session_scoped(monkeypatch):
    """A session-targeted fast toggle updates the live agent + pins the
    per-session override, and NEVER writes global config — the desktop's
    per-model presets call this on every model pick, and a global write
    flipped the tier for every other session/profile (the "switch one
    session, switches everywhere" class)."""
    writes = []
    emits = []
    agent = types.SimpleNamespace(
        model="openai/gpt-5.4",
        request_overrides={"foo": "bar", "speed": "slow"},
        service_tier=None,
    )
    session = _session(agent=agent)
    server._sessions["sid"] = session

    monkeypatch.setattr(
        server, "_write_config_key", lambda path, value: writes.append((path, value))
    )
    monkeypatch.setattr(server, "_session_info", lambda _agent, *a: {"model": "x"})
    monkeypatch.setattr(server, "_emit", lambda *args: emits.append(args))
    monkeypatch.setattr(
        "hermes_cli.models.resolve_fast_mode_overrides",
        lambda _model_id, **_route: {"service_tier": "priority"},
    )

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "config.set",
                "params": {"session_id": "sid", "key": "fast", "value": "fast"},
            }
        )
        assert resp["result"]["value"] == "fast"
        assert agent.service_tier == "priority"
        assert agent.request_overrides == {
            "foo": "bar",
            "service_tier": "priority",
        }
        assert session["create_service_tier_override"] == "priority"
        assert writes == []
        assert ("session.info", "sid", {"model": "x"}) in emits

        resp_normal = server.handle_request(
            {
                "id": "2",
                "method": "config.set",
                "params": {"session_id": "sid", "key": "fast", "value": "normal"},
            }
        )
        assert resp_normal["result"]["value"] == "normal"
        assert agent.service_tier is None
        assert agent.request_overrides == {"foo": "bar"}
        # "" (not absent) so a rebuild pins normal instead of falling back to
        # the global default.
        assert session["create_service_tier_override"] == ""
        assert writes == []
    finally:
        server._sessions.pop("sid", None)


def test_config_set_fast_status_is_non_mutating(monkeypatch):
    writes = []
    emits = []
    agent = types.SimpleNamespace(service_tier="priority")
    server._sessions["sid"] = _session(agent=agent)

    monkeypatch.setattr(
        server, "_write_config_key", lambda path, value: writes.append((path, value))
    )
    monkeypatch.setattr(server, "_emit", lambda *args: emits.append(args))

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "config.set",
                "params": {"session_id": "sid", "key": "fast", "value": "status"},
            }
        )
        assert resp["result"]["value"] == "fast"
        assert writes == []
        assert emits == []
    finally:
        server._sessions.pop("sid", None)


def test_config_set_fast_rejects_unsupported_model(monkeypatch):
    writes = []
    agent = types.SimpleNamespace(
        model="unsupported-model",
        request_overrides={},
        service_tier=None,
    )
    server._sessions["sid"] = _session(agent=agent)

    monkeypatch.setattr(
        server, "_write_config_key", lambda path, value: writes.append((path, value))
    )
    monkeypatch.setattr(
        "hermes_cli.models.resolve_fast_mode_overrides",
        lambda _model_id, **_route: None,
    )

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "config.set",
                "params": {"session_id": "sid", "key": "fast", "value": "fast"},
            }
        )
        assert resp["error"]["code"] == 4002
        assert agent.service_tier is None
        assert agent.request_overrides == {}
        assert writes == []
    finally:
        server._sessions.pop("sid", None)


def test_config_set_fast_rejects_missing_model(monkeypatch):
    writes = []
    agent = types.SimpleNamespace(
        model="",
        request_overrides={},
        service_tier=None,
    )
    server._sessions["sid"] = _session(agent=agent)

    monkeypatch.setattr(
        server, "_write_config_key", lambda path, value: writes.append((path, value))
    )

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "config.set",
                "params": {"session_id": "sid", "key": "fast", "value": "fast"},
            }
        )
        assert resp["error"]["code"] == 4002
        assert agent.service_tier is None
        assert agent.request_overrides == {}
        assert writes == []
    finally:
        server._sessions.pop("sid", None)


def test_config_busy_get_and_set(monkeypatch):
    writes = []

    monkeypatch.setattr(
        server,
        "_load_cfg",
        lambda: {"display": {"busy_input_mode": "steer"}},
    )
    monkeypatch.setattr(
        server, "_write_config_key", lambda path, value: writes.append((path, value))
    )

    get_resp = server.handle_request(
        {"id": "1", "method": "config.get", "params": {"key": "busy"}}
    )
    assert get_resp["result"]["value"] == "steer"

    set_resp = server.handle_request(
        {
            "id": "2",
            "method": "config.set",
            "params": {"key": "busy", "value": "interrupt"},
        }
    )
    assert set_resp["result"]["value"] == "interrupt"
    assert ("display.busy_input_mode", "interrupt") in writes


def test_config_set_yolo_process_scope_treats_false_like_env_as_disabled(monkeypatch):
    monkeypatch.setenv("HERMES_YOLO_MODE", "false")

    resp = server.handle_request(
        {
            "id": "1",
            "method": "config.set",
            "params": {"key": "yolo"},
        }
    )

    assert resp["result"]["value"] == "1"
    assert os.environ.get("HERMES_YOLO_MODE") == "1"


def test_config_get_statusbar_survives_non_dict_display(monkeypatch):
    monkeypatch.setattr(server, "_load_cfg", lambda: {"display": "broken"})

    resp = server.handle_request(
        {"id": "1", "method": "config.get", "params": {"key": "statusbar"}}
    )

    assert resp["result"]["value"] == "top"


def test_config_get_busy_survives_non_dict_display(monkeypatch):
    monkeypatch.setattr(server, "_load_cfg", lambda: {"display": "broken"})

    resp = server.handle_request(
        {"id": "1", "method": "config.get", "params": {"key": "busy"}}
    )

    assert resp["result"]["value"] == "interrupt"


def test_config_set_statusbar_survives_non_dict_display(tmp_path, monkeypatch):
    import hermes_yaml as yaml

    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.safe_dump({"display": "broken"}))
    monkeypatch.setattr(server, "_hermes_home", tmp_path)

    resp = server.handle_request(
        {
            "id": "1",
            "method": "config.set",
            "params": {"key": "statusbar", "value": "bottom"},
        }
    )

    assert resp["result"]["value"] == "bottom"
    saved = yaml.safe_load(cfg_path.read_text())
    assert saved["display"]["tui_statusbar"] == "bottom"


def test_config_set_details_mode_pins_all_sections(tmp_path, monkeypatch):
    import hermes_yaml as yaml

    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        yaml.safe_dump(
            {"display": {"sections": {"tools": "expanded", "activity": "hidden"}}}
        )
    )
    monkeypatch.setattr(server, "_hermes_home", tmp_path)

    resp = server.handle_request(
        {
            "id": "1",
            "method": "config.set",
            "params": {"key": "details_mode", "value": "collapsed"},
        }
    )

    assert resp["result"] == {"key": "details_mode", "value": "collapsed"}
    saved = yaml.safe_load(cfg_path.read_text())
    assert saved["display"]["details_mode"] == "collapsed"
    assert saved["display"]["sections"] == {
        "thinking": "collapsed",
        "tools": "collapsed",
        "subagents": "collapsed",
        "activity": "collapsed",
    }


def test_config_set_section_writes_per_section_override(tmp_path, monkeypatch):
    import hermes_yaml as yaml

    cfg_path = tmp_path / "config.yaml"
    monkeypatch.setattr(server, "_hermes_home", tmp_path)

    resp = server.handle_request(
        {
            "id": "1",
            "method": "config.set",
            "params": {"key": "details_mode.activity", "value": "hidden"},
        }
    )

    assert resp["result"] == {"key": "details_mode.activity", "value": "hidden"}
    saved = yaml.safe_load(cfg_path.read_text())
    assert saved["display"]["sections"] == {"activity": "hidden"}


def test_config_set_section_clears_override_on_empty_value(tmp_path, monkeypatch):
    import hermes_yaml as yaml

    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        yaml.safe_dump(
            {"display": {"sections": {"activity": "hidden", "tools": "expanded"}}}
        )
    )
    monkeypatch.setattr(server, "_hermes_home", tmp_path)

    resp = server.handle_request(
        {
            "id": "1",
            "method": "config.set",
            "params": {"key": "details_mode.activity", "value": ""},
        }
    )

    assert resp["result"] == {"key": "details_mode.activity", "value": ""}
    saved = yaml.safe_load(cfg_path.read_text())
    assert saved["display"]["sections"] == {"tools": "expanded"}


def test_config_set_section_rejects_unknown_section_or_mode(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "_hermes_home", tmp_path)

    bad_section = server.handle_request(
        {
            "id": "1",
            "method": "config.set",
            "params": {"key": "details_mode.bogus", "value": "hidden"},
        }
    )
    assert bad_section["error"]["code"] == 4002

    bad_mode = server.handle_request(
        {
            "id": "2",
            "method": "config.set",
            "params": {"key": "details_mode.tools", "value": "maximised"},
        }
    )
    assert bad_mode["error"]["code"] == 4002


def test_config_mouse_uses_documented_key_with_legacy_fallback(monkeypatch):
    cfg = {"display": {"tui_mouse": False}}
    writes = []

    monkeypatch.setattr(server, "_load_cfg", lambda: cfg)
    monkeypatch.setattr(
        server, "_write_config_key", lambda path, value: writes.append((path, value))
    )

    get_legacy = server.handle_request(
        {"id": "1", "method": "config.get", "params": {"key": "mouse"}}
    )
    assert get_legacy["result"]["value"] == "off"

    set_toggle = server.handle_request(
        {"id": "2", "method": "config.set", "params": {"key": "mouse"}}
    )
    # /mouse (no arg) toggles between 'all' and 'off'. Starting from
    # tui_mouse: False (→ 'off'), the toggle flips to 'all'.
    assert set_toggle["result"] == {"key": "mouse", "value": "all"}
    assert writes == [("display.mouse_tracking", "all")]

    cfg["display"] = {"mouse_tracking": 0, "tui_mouse": True}
    get_canonical = server.handle_request(
        {"id": "3", "method": "config.get", "params": {"key": "mouse"}}
    )
    assert get_canonical["result"]["value"] == "off"

    cfg["display"] = {"mouse_tracking": None, "tui_mouse": False}
    get_null = server.handle_request(
        {"id": "4", "method": "config.get", "params": {"key": "mouse"}}
    )
    # mouse_tracking present-but-None defers neither to tui_mouse nor to
    # the legacy off bucket: it falls through to the 'all' default.
    assert get_null["result"]["value"] == "all"


def test_config_mouse_accepts_preset_strings_and_aliases(monkeypatch):
    cfg = {"display": {"mouse_tracking": "all"}}
    writes = []

    monkeypatch.setattr(server, "_load_cfg", lambda: cfg)
    monkeypatch.setattr(
        server, "_write_config_key", lambda path, value: writes.append((path, value))
    )

    # Direct preset.
    set_wheel = server.handle_request(
        {
            "id": "1",
            "method": "config.set",
            "params": {"key": "mouse", "value": "wheel"},
        }
    )
    assert set_wheel["result"] == {"key": "mouse", "value": "wheel"}
    assert writes[-1] == ("display.mouse_tracking", "wheel")

    # Alias for buttons.
    set_click = server.handle_request(
        {
            "id": "2",
            "method": "config.set",
            "params": {"key": "mouse", "value": "click"},
        }
    )
    assert set_click["result"] == {"key": "mouse", "value": "buttons"}
    assert writes[-1] == ("display.mouse_tracking", "buttons")

    # Unknown value → 4002.
    bad = server.handle_request(
        {
            "id": "3",
            "method": "config.set",
            "params": {"key": "mouse", "value": "rainbows"},
        }
    )
    assert bad["error"]["code"] == 4002


def test_enable_gateway_prompts_sets_gateway_env(monkeypatch):
    monkeypatch.delenv("HERMES_EXEC_ASK", raising=False)
    monkeypatch.delenv("HERMES_GATEWAY_SESSION", raising=False)
    monkeypatch.delenv("HERMES_INTERACTIVE", raising=False)

    server._enable_gateway_prompts()

    assert server.os.environ["HERMES_GATEWAY_SESSION"] == "1"
    assert server.os.environ["HERMES_EXEC_ASK"] == "1"
    assert server.os.environ["HERMES_INTERACTIVE"] == "1"


def test_setup_status_answers_from_the_bootstrap_record_once_it_exists(monkeypatch):
    """Under ``hermes serve`` the boot bootstrap owns the free-tier identity; ``setup.status`` reports
    its record (blocking for it while it is in flight) instead of re-probing, so a client's first poll
    sees the identity that exists rather than racing the mint."""
    import threading
    from hermes_cli import free_tier_bootstrap as fb
    fb.reset_for_tests()
    monkeypatch.setattr("hermes_cli.main._has_any_provider_configured",
                        lambda **_kw: pytest.fail("setup.status must read the record, not re-probe"))
    release = threading.Event()

    def slow_bootstrap():
        release.wait(5)
        with fb._lock:
            fb._record = fb.SetupRecord(provider_configured=True, inference_provider="nous", free_tier=True,
                                        has_identity=True, other_providers=False)
            fb._done.set()
    with fb._lock:
        fb._started = True
    threading.Thread(target=slow_bootstrap, daemon=True).start()
    try:
        release.set()
        resp = server.handle_request({"id": "1", "method": "setup.status", "params": {}})
        assert resp["result"]["provider_configured"] is True
        assert resp["result"]["ready"] is True and resp["result"]["free_tier"] is True
        assert resp["result"]["inference_provider"] == "nous"
    finally:
        fb.reset_for_tests()


def test_invalid_params_and_unknown_method_name_the_version_skew_fix():
    """The only signal of a TUI/backend version mismatch; the lead phrases stay for clients."""
    resp = server.handle_request({"id": "1", "method": "no.such.method", "params": {}})
    assert resp["error"]["code"] == -32601
    assert resp["error"]["message"].startswith("unknown method: no.such.method")

    resp = server.handle_request(
        {"id": "2", "method": "session.status", "params": {"session_id": "x", "turn_author": "y"}})
    assert resp["error"]["code"] == 4000
    assert resp["error"]["message"].startswith("invalid params for session.status: turn_author")


def test_probe_credentials_emits_exact_empty_key_warning():
    agent = types.SimpleNamespace(api_key="", provider="openrouter")

    warning = server._probe_credentials(agent)
    assert warning and "openrouter" in warning


def test_probe_credentials_allows_keyless_custom_runtime():
    agent = types.SimpleNamespace(api_key="no-key-required", provider="custom")

    assert server._probe_credentials(agent) == ""


def test_setup_runtime_check_rejects_empty_runtime_key(monkeypatch):
    monkeypatch.setattr("hermes_cli.main._has_any_provider_configured", lambda **_kw: True)
    monkeypatch.setattr(server, "_resolve_startup_runtime", lambda: ("openrouter/test-model", None))
    monkeypatch.setattr(
        "hermes_cli.runtime_provider.resolve_runtime_provider",
        lambda requested=None, **_kw: {
            "provider": "openrouter",
            "api_key": "",
            "source": "env/config",
        },
    )

    resp = server.handle_request({"id": "1", "method": "setup.runtime_check", "params": {}})

    result = resp["result"]
    assert result["ok"] is False
    assert (result["provider"], result["model"], result["source"]) == (
        "openrouter", "openrouter/test-model", "env/config"
    )
    assert result["error"]


def test_setup_runtime_check_allows_no_key_custom_runtime(monkeypatch):
    monkeypatch.setattr("hermes_cli.main._has_any_provider_configured", lambda **_kw: True)
    monkeypatch.setattr(
        "hermes_cli.runtime_provider.resolve_runtime_provider",
        lambda requested=None, **_kw: {
            "provider": "custom",
            "api_key": "no-key-required",
            "source": "env/config",
        },
    )

    resp = server.handle_request({"id": "1", "method": "setup.runtime_check", "params": {}})

    assert resp["result"]["ok"] is True
    assert resp["result"]["provider"] == "custom"


def test_setup_runtime_check_rejects_implicit_bedrock_when_unconfigured(monkeypatch):
    monkeypatch.setattr("hermes_cli.main._has_any_provider_configured", lambda **_kw: False)
    monkeypatch.setattr(
        "hermes_cli.runtime_provider.resolve_runtime_provider",
        lambda requested=None, **_kw: {
            "provider": "bedrock",
            "api_key": "aws-sdk",
            "source": "iam-role",
        },
    )

    resp = server.handle_request({"id": "1", "method": "setup.runtime_check", "params": {}})

    assert resp["result"]["ok"] is False
    assert resp["result"]["provider"] == "bedrock"


def test_setup_runtime_check_honors_requested_provider(monkeypatch):
    """Onboarding must be able to validate the provider the user just connected."""
    monkeypatch.setattr("hermes_cli.main._has_any_provider_configured", lambda **_kw: True)

    def fake_resolve(requested=None, **kwargs):
        if requested == "nous":
            return {
                "provider": "nous",
                "api_key": "invoke-jwt",
                "source": "portal",
            }
        return {
            "provider": "anthropic",
            "api_key": "",
            "source": "config",
        }

    monkeypatch.setattr(
        "hermes_cli.runtime_provider.resolve_runtime_provider",
        fake_resolve,
    )

    scoped = server.handle_request(
        {"id": "1", "method": "setup.runtime_check", "params": {"provider": "nous"}}
    )
    assert scoped["result"]["ok"] is True
    assert scoped["result"]["provider"] == "nous"

    default = server.handle_request({"id": "1", "method": "setup.runtime_check", "params": {}})
    assert default["result"]["ok"] is False
    assert default["result"]["provider"] == "anthropic"


def test_setup_runtime_check_agrees_with_session_fallback_chain(monkeypatch):
    """#111775: with the primary blocked and a complete fallback entry, the probe answers what
    ``_make_agent`` would build (fallback provider + model); an explicit ``provider`` stays strict
    so another provider's fallback cannot mask a failed connection."""
    from hermes_cli.auth import AuthError
    monkeypatch.setattr("hermes_cli.main._has_any_provider_configured", lambda **_kw: True)
    monkeypatch.setattr(server, "_resolve_startup_runtime", lambda: ("claude-sonnet-4-5", None))
    monkeypatch.setattr(server, "_load_fallback_model",
                        lambda: [{"provider": "openrouter", "model": "openai/gpt-4.1-mini", "api_key": "sk-or-fb"}])

    def fake_resolve(*, requested=None, target_model=None, explicit_api_key=None, **_kw):
        if requested == "openrouter":
            return {"provider": "openrouter", "api_key": explicit_api_key, "source": "explicit"}
        raise AuthError("No Anthropic credentials found.", provider="anthropic")

    monkeypatch.setattr("hermes_cli.runtime_provider.resolve_runtime_provider", fake_resolve)

    default = server.handle_request({"id": "1", "method": "setup.runtime_check", "params": {}})
    assert default["result"]["ok"] is True
    assert (default["result"]["provider"], default["result"]["model"]) == ("openrouter", "openai/gpt-4.1-mini")

    strict = server.handle_request(
        {"id": "2", "method": "setup.runtime_check", "params": {"provider": "anthropic"}})
    assert strict["result"]["ok"] is False
    assert "Anthropic" in strict["result"]["error"]


def test_setup_runtime_check_reports_target_model_on_credential_failure(monkeypatch):
    """#111775: the probe names the model session creation would use, never ``model: null``."""
    monkeypatch.setattr("hermes_cli.main._has_any_provider_configured", lambda **_kw: True)
    monkeypatch.setattr(server, "_resolve_startup_runtime", lambda: ("z-ai/glm-5.2", None))
    monkeypatch.setattr(
        "hermes_cli.runtime_provider.resolve_runtime_provider",
        lambda *, requested=None, target_model=None: {
            "provider": "zai", "api_key": "", "source": "env/config"
        },
    )

    resp = server.handle_request({"id": "1", "method": "setup.runtime_check", "params": {}})

    assert resp["result"]["ok"] is False
    assert resp["result"]["model"] == "z-ai/glm-5.2"


def test_setup_runtime_check_scopes_launch_profile_in_multiplex_backend(monkeypatch, tmp_path):
    """The launch profile needs a scope too when its Codex route reads an override."""
    from agent import secret_scope
    from tui_gateway import launch_profile_policy

    launch_home = tmp_path / ".hermes"
    launch_home.mkdir()
    monkeypatch.setenv("HERMES_CODEX_BASE_URL", "https://codex.launch.test/v1")
    monkeypatch.setattr(server, "_hermes_home", launch_home)
    monkeypatch.setattr(launch_profile_policy, "_snapshot", None)
    monkeypatch.setattr("hermes_cli.main._has_any_provider_configured", lambda **_kw: True)
    monkeypatch.setattr(server, "_resolve_startup_runtime", lambda: ("gpt-5.3-codex", None))

    def resolve_codex(requested=None, **_kwargs):
        assert requested == "openai-codex"
        return {
            "provider": "openai-codex",
            "api_key": "codex-oauth-token",
            "base_url": secret_scope.get_secret("HERMES_CODEX_BASE_URL"),
            "source": "credential-pool",
        }

    monkeypatch.setattr("hermes_cli.runtime_provider.resolve_runtime_provider", resolve_codex)
    secret_scope.set_multiplex_active(True)
    try:
        response = server.handle_request(
            {"id": "1", "method": "setup.runtime_check", "params": {"provider": "openai-codex"}}
        )
    finally:
        secret_scope.set_multiplex_active(False)

    assert response["result"] == {
        "ok": True,
        "provider": "openai-codex",
        "model": "gpt-5.3-codex",
        "source": "credential-pool",
        "free_tier": False,
    }


def test_setup_readiness_scopes_to_requested_profile(monkeypatch, tmp_path):
    """#94071: the Desktop preflights a freshly created bot on its target
    backend. ``profile`` binds THAT profile's home + .env — launch-process
    credentials must not make an unconfigured bot look ready, and the bot's
    own .env must be what the strict check sees."""
    from agent import secret_scope
    from hermes_constants import get_hermes_home

    bot_home = tmp_path / "profiles" / "bot"
    bot_home.mkdir(parents=True)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-launch-profile-secret-0000")
    monkeypatch.setattr("hermes_cli.profiles.profile_exists", lambda name: name == "bot")
    monkeypatch.setattr(server, "_profile_home", lambda profile: bot_home if profile == "bot" else None)
    seen = {}

    def fake_resolve(requested=None, **kwargs):
        seen["home"] = Path(str(get_hermes_home())).resolve()
        seen["secret"] = secret_scope.get_secret("OPENROUTER_API_KEY")
        return {"provider": "openrouter", "api_key": seen["secret"] or "", "source": "env"}

    monkeypatch.setattr("hermes_cli.runtime_provider.resolve_runtime_provider", fake_resolve)

    secret_scope.set_multiplex_active(True)
    try:
        status = server.handle_request(
            {"id": "1", "method": "setup.status", "params": {"profile": "bot"}}
        )
        assert status["result"] == {"provider_configured": False, "profile": "bot"}

        (bot_home / ".env").write_text("OPENROUTER_API_KEY=sk-or-bot-profile-secret-00001\n")
        status = server.handle_request(
            {"id": "2", "method": "setup.status", "params": {"profile": "bot"}}
        )
        runtime = server.handle_request(
            {"id": "3", "method": "setup.runtime_check", "params": {"profile": "bot"}}
        )
    finally:
        secret_scope.set_multiplex_active(False)

    assert status["result"] == {"provider_configured": True, "profile": "bot"}
    assert runtime["result"]["ok"] is True
    assert runtime["result"]["profile"] == "bot"
    assert seen == {"home": bot_home.resolve(), "secret": "sk-or-bot-profile-secret-00001"}
    assert Path(str(get_hermes_home())).resolve() != bot_home.resolve()


def test_setup_readiness_unknown_profile_never_answers_for_launch_profile(monkeypatch):
    monkeypatch.setattr("hermes_cli.main._has_any_provider_configured", lambda **_kw: True)
    monkeypatch.setattr(
        "hermes_cli.runtime_provider.resolve_runtime_provider",
        lambda requested=None, **kw: {"provider": "openrouter", "api_key": "sk-or-launch-0000000000", "source": "env"},
    )
    monkeypatch.setattr("hermes_cli.profiles.profile_exists", lambda name: False)

    for method in ("setup.status", "setup.runtime_check"):
        resp = server.handle_request({"id": "1", "method": method, "params": {"profile": "ghost"}})
        assert resp["result"]["ok"] is False
        assert resp["result"]["profile"] == "ghost"


def test_complete_slash_returns_plain_string_fields():
    # prompt_toolkit hands us FormattedText (a list subclass) for
    # display/display_meta; the TUI's CompletionItem contract is plain
    # strings, and shipping the raw list trips Ink's row layout into
    # 1-char truncation of the next column (/goal → /goa).
    resp = server.handle_request(
        {"id": "1", "method": "complete.slash", "params": {"text": "/g"}}
    )

    items = resp["result"]["items"]
    goal = next((it for it in items if it["text"] == "goal"), None)
    assert goal is not None
    assert isinstance(goal["display"], str), goal["display"]
    assert isinstance(goal["meta"], str), goal["meta"]
    assert goal["display"] == "/goal"
    for item in items:
        assert isinstance(item["display"], str), item
        assert isinstance(item["meta"], str), item


def test_complete_slash_details_args():
    resp_root = server.handle_request(
        {"id": "0", "method": "complete.slash", "params": {"text": "/details"}}
    )
    resp_section = server.handle_request(
        {"id": "1", "method": "complete.slash", "params": {"text": "/details t"}}
    )
    resp_mode = server.handle_request(
        {
            "id": "2",
            "method": "complete.slash",
            "params": {"text": "/details thinking e"},
        }
    )

    assert resp_root["result"]["replace_from"] == len("/details")
    assert any(item["text"] == " thinking" for item in resp_root["result"]["items"])
    assert any(item["text"] == "thinking" for item in resp_section["result"]["items"])
    assert any(item["text"] == "expanded" for item in resp_mode["result"]["items"])


def test_complete_slash_offers_skills_alongside_commands(monkeypatch):
    """A bare `/` must reach the skills, not just the registry.

    The completer emits every registry command before the first skill, so one
    flat cap spent every row on commands and no skill was reachable at all.
    """
    _slash_skill_fixtures(monkeypatch)

    kinds = {item["kind"] for item in _slash_completions("/")}

    assert kinds == {"command", "skill"}


def test_complete_slash_ranks_skills_by_recorded_usage(monkeypatch):
    """The skills someone actually invokes lead the ones they never opened."""
    _slash_skill_fixtures(monkeypatch)

    skills = [
        item["text"].strip() for item in _slash_completions("/") if item["kind"] == "skill"
    ]

    assert skills[:3] == ["work", "research", "clean"]


def test_complete_slash_prunes_unused_builtins_only_while_browsing(monkeypatch):
    """A bare `/` is browsing and may prune; a typed query is a search.

    A search that hides a match is broken, so the never-opened bundled skill
    disappears from `/` and comes straight back the moment it is typed for.
    """
    _slash_skill_fixtures(monkeypatch)

    browsing = {item["text"].strip() for item in _slash_completions("/")}
    searching = {item["text"].strip() for item in _slash_completions("/unused")}

    assert "unused-bundled" not in browsing
    assert "unused-bundled" in searching


def test_complete_slash_leaves_argument_stages_alone(monkeypatch):
    """Ranking applies to the command token, never to a command's own args.

    `/details c` completes that command's modes; a skill named /clean also
    starts with a `c` and must not be offered as one of them.
    """
    _slash_skill_fixtures(monkeypatch)

    items = _slash_completions("/details c")

    assert [item["text"] for item in items] == ["collapsed", "cycle"]


def test_config_get_reasoning_renders_dict_form_custom_tier(tmp_path, monkeypatch):
    """`agent.reasoning_effort: {enabled: true, effort: thinking}` (a provider's bespoke tier)
    must read back as the tier name, not `str(dict)`."""
    monkeypatch.setattr(server, "_hermes_home", tmp_path)
    (tmp_path / "config.yaml").write_text(
        "agent:\n  reasoning_effort:\n    enabled: true\n    effort: thinking\n", encoding="utf-8"
    )

    resp = server.handle_request({"id": "1", "method": "config.get", "params": {"key": "reasoning"}})

    assert resp["result"]["value"] == "thinking"


def test_config_set_reasoning_updates_live_session_and_agent(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "_hermes_home", tmp_path)
    (tmp_path / "config.yaml").write_text("agent:\n  reasoning_effort: medium\n", encoding="utf-8")
    agent = types.SimpleNamespace(reasoning_config=None)
    server._sessions["sid"] = _session(agent=agent)

    resp_effort = server.handle_request(
        {
            "id": "1",
            "method": "config.set",
            "params": {
                "session_id": "sid",
                "key": "reasoning",
                "value": "low",
            },
        }
    )
    assert resp_effort["result"]["value"] == "low"
    assert agent.reasoning_config == {"enabled": True, "effort": "low"}
    assert server._sessions["sid"]["create_reasoning_override"] == {"enabled": True, "effort": "low"}
    assert server._load_cfg()["agent"]["reasoning_effort"] == "medium"

    resp_status = server.handle_request(
        {
            "id": "5",
            "method": "config.get",
            "params": {"session_id": "sid", "key": "reasoning"},
        }
    )
    assert resp_status["result"]["value"] == "low"

    resp_global_status = server.handle_request(
        {"id": "6", "method": "config.get", "params": {"key": "reasoning"}}
    )
    assert resp_global_status["result"]["value"] == "medium"

    del server._sessions["sid"]["create_reasoning_override"]
    agent.reasoning_config = {"enabled": True, "effort": "high"}
    resp_agent_status = server.handle_request(
        {
            "id": "7",
            "method": "config.get",
            "params": {"session_id": "sid", "key": "reasoning"},
        }
    )
    assert resp_agent_status["result"]["value"] == "high"

    resp_show = server.handle_request(
        {
            "id": "2",
            "method": "config.set",
            "params": {"session_id": "sid", "key": "reasoning", "value": "show"},
        }
    )
    assert resp_show["result"]["value"] == "show"
    assert server._sessions["sid"]["show_reasoning"] is True
    assert server._load_cfg()["display"]["sections"]["thinking"] == "expanded"

    resp_hide = server.handle_request(
        {
            "id": "3",
            "method": "config.set",
            "params": {"session_id": "sid", "key": "reasoning", "value": "hide"},
        }
    )
    assert resp_hide["result"]["value"] == "hide"
    assert server._sessions["sid"]["show_reasoning"] is False
    assert server._load_cfg()["display"]["sections"]["thinking"] == "hidden"

    # /reasoning full | clamp — parity with the classic CLI reasoning_full
    # toggle. In the TUI these map to the thinking section's expand/collapse
    # rendering (no fixed 10-line recap exists here).
    resp_full = server.handle_request(
        {
            "id": "4",
            "method": "config.set",
            "params": {"session_id": "sid", "key": "reasoning", "value": "full"},
        }
    )
    assert resp_full["result"]["value"] == "full"
    cfg_full = server._load_cfg()
    assert cfg_full["display"]["reasoning_full"] is True
    assert cfg_full["display"]["sections"]["thinking"] == "expanded"

    resp_clamp = server.handle_request(
        {
            "id": "5",
            "method": "config.set",
            "params": {"session_id": "sid", "key": "reasoning", "value": "clamp"},
        }
    )
    assert resp_clamp["result"]["value"] == "clamp"
    cfg_clamp = server._load_cfg()
    assert cfg_clamp["display"]["reasoning_full"] is False
    assert cfg_clamp["display"]["sections"]["thinking"] == "collapsed"


def test_config_set_reasoning_global_scope_clears_session_override(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "_hermes_home", tmp_path)
    (tmp_path / "config.yaml").write_text("agent:\n  reasoning_effort: medium\n", encoding="utf-8")
    agent = types.SimpleNamespace(reasoning_config=None)
    server._sessions["sid"] = _session(agent=agent)
    server._sessions["sid"]["create_reasoning_override"] = {"enabled": True, "effort": "low"}

    resp = server.handle_request(
        {
            "id": "1",
            "method": "config.set",
            "params": {
                "session_id": "sid",
                "key": "reasoning",
                "value": "high",
                "scope": "global",
            },
        }
    )

    assert resp["result"]["value"] == "high"
    assert server._load_cfg()["agent"]["reasoning_effort"] == "high"
    assert "create_reasoning_override" not in server._sessions["sid"]

    status = server.handle_request(
        {"id": "2", "method": "config.get", "params": {"session_id": "sid", "key": "reasoning"}}
    )
    assert status["result"]["value"] == "high"


def test_config_set_verbose_updates_session_mode_and_agent(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "_hermes_home", tmp_path)
    agent = types.SimpleNamespace(verbose_logging=False)
    server._sessions["sid"] = _session(agent=agent)

    resp = server.handle_request(
        {
            "id": "1",
            "method": "config.set",
            "params": {"session_id": "sid", "key": "verbose", "value": "cycle"},
        }
    )

    assert resp["result"]["value"] == "verbose"
    assert server._sessions["sid"]["tool_progress_mode"] == "verbose"
    assert agent.verbose_logging is True


def test_config_set_model_waits_for_lazy_agent_before_switch(monkeypatch):
    """A model switch against a lazy-created live session must apply to the
    real agent, not just process env, before the prompt is dispatched.
    """

    agent_ready = threading.Event()
    agent = types.SimpleNamespace(model="old/model", provider="old-provider")
    session = _session(agent=agent)
    session["agent"] = None
    session["agent_ready"] = agent_ready
    server._sessions["sid"] = session
    calls = []

    def fake_start(sid, target):
        calls.append(("start", sid))
        target["agent"] = agent
        agent_ready.set()

    def fake_apply(sid, target, raw, **kwargs):
        calls.append(("apply", sid, target.get("agent"), raw))
        if target.get("agent") is not agent:
            raise AssertionError("model switch ran before lazy agent was ready")
        return {"value": "new/model", "warning": ""}

    monkeypatch.setattr(server, "_start_agent_build", fake_start)
    monkeypatch.setattr(server, "_apply_model_switch", fake_apply)

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "config.set",
                "params": {"session_id": "sid", "key": "model", "value": "new/model"},
            }
        )

        assert resp["result"]["value"] == "new/model"
        assert calls == [("start", "sid"), ("apply", "sid", agent, "new/model")]
    finally:
        server._sessions.pop("sid", None)


def test_config_set_model_requires_confirmation_for_expensive_model(monkeypatch):
    class _Agent:
        provider = "openrouter"
        model = "old/model"
        base_url = ""
        api_key = "sk-or"
        switched = False

        def switch_model(self, **_kwargs):
            self.switched = True

    result = types.SimpleNamespace(
        success=True,
        new_model="openai/gpt-5.5-pro",
        target_provider="openrouter",
        api_key="sk-or",
        base_url="https://openrouter.ai/api/v1",
        api_mode="chat_completions",
        warning_message="",
        model_info=types.SimpleNamespace(
            has_cost_data=lambda: True,
            cost_input=25.0,
            cost_output=125.0,
        ),
    )

    agent = _Agent()
    server._sessions["sid"] = _session(agent=agent)
    monkeypatch.setattr(
        "hermes_cli.model_switch.switch_model", lambda **_kwargs: result
    )
    monkeypatch.setattr(server, "_restart_slash_worker", lambda sid, session: None)
    monkeypatch.setattr(server, "_emit", lambda *args, **kwargs: None)

    resp = server.handle_request(
        {
            "id": "1",
            "method": "config.set",
            "params": {
                "session_id": "sid",
                "key": "model",
                "value": "openai/gpt-5.5-pro --provider openrouter",
            },
        }
    )

    assert resp["result"]["confirm_required"] is True
    assert agent.switched is False

    confirmed = server.handle_request(
        {
            "id": "2",
            "method": "config.set",
            "params": {
                "session_id": "sid",
                "key": "model",
                "value": "openai/gpt-5.5-pro --provider openrouter",
                "confirm_expensive_model": True,
            },
        }
    )

    assert confirmed["result"]["confirm_required"] is False
    assert confirmed["result"]["value"] == "openai/gpt-5.5-pro"
    assert agent.switched is True


def test_config_set_model_global_persists(monkeypatch):
    class _Agent:
        provider = "openrouter"
        model = "old/model"
        base_url = ""
        api_key = "sk-old"

        def switch_model(self, **kwargs):
            return None

    result = types.SimpleNamespace(
        success=True,
        new_model="anthropic/claude-sonnet-4.6",
        target_provider="anthropic",
        api_key="sk-new",
        base_url="https://api.anthropic.com",
        api_mode="anthropic_messages",
        warning_message="",
    )
    seen = {}
    saved_values = {}

    def _switch_model(**kwargs):
        seen.update(kwargs)
        return result

    server._sessions["sid"] = _session(agent=_Agent())
    monkeypatch.setattr("hermes_cli.model_switch.switch_model", _switch_model)
    monkeypatch.setattr(server, "_restart_slash_worker", lambda sid, session: None)
    monkeypatch.setattr(server, "_emit", lambda *args, **kwargs: None)
    # persist_model_selection uses targeted per-key writes (#48305) so it
    # preserves sibling model.* keys instead of rewriting the whole block.
    monkeypatch.setattr("utils.atomic_roundtrip_yaml_update", lambda path, key, value: saved_values.__setitem__(key, value))

    resp = server.handle_request(
        {
            "id": "1",
            "method": "config.set",
            "params": {
                "session_id": "sid",
                "key": "model",
                "value": "anthropic/claude-sonnet-4.6 --global",
            },
        }
    )

    assert resp["result"]["value"] == "anthropic/claude-sonnet-4.6"
    assert seen["is_global"] is True
    assert saved_values["model.default"] == "anthropic/claude-sonnet-4.6"
    assert saved_values["model.provider"] == "anthropic"
    assert saved_values["model.base_url"] == "https://api.anthropic.com"


def test_config_set_model_explicit_provider_skips_broken_default_init(monkeypatch):
    seen = {"build": 0, "wait": 0, "requested": []}
    session = _session()
    session["agent"] = None
    server._sessions["sid"] = session
    monkeypatch.setattr(server, "_load_cfg", lambda: {"model": {"default": "broken/model", "provider": "openrouter"}})
    monkeypatch.setattr(server, "_start_agent_build", lambda *_args: seen.__setitem__("build", seen["build"] + 1))
    monkeypatch.setattr(server, "_wait_agent", lambda *_args: seen.__setitem__("wait", seen["wait"] + 1))
    monkeypatch.setattr(server, "_emit", lambda *args, **kwargs: None)
    monkeypatch.setattr(server, "_restart_slash_worker", lambda *args, **kwargs: None)

    def fake_runtime_provider(*, requested=None, target_model=None, **_kwargs):
        seen["requested"].append((requested, target_model))
        if requested is None:
            raise RuntimeError("broken default provider should not be initialized")
        if requested == "anthropic":
            return {
                "api_key": "sk-anthropic",
                "api_mode": "anthropic_messages",
                "base_url": "https://api.anthropic.com",
            }
        raise RuntimeError(f"unexpected provider {requested}")

    monkeypatch.setattr("hermes_cli.runtime_provider.resolve_runtime_provider", fake_runtime_provider)

    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "config.set",
                "params": {
                    "session_id": "sid",
                    "key": "model",
                    "value": "claude-sonnet-4.6 --provider anthropic",
                },
            }
        )

        assert resp["result"]["value"] == "claude-sonnet-4-6"
        assert seen["build"] == 0
        assert seen["wait"] == 0
        assert seen["requested"] == [("anthropic", "claude-sonnet-4.6")]
        assert session["model_override"]["provider"] == "anthropic"
        assert session["model_override"]["model"] == "claude-sonnet-4-6"
    finally:
        server._sessions.pop("sid", None)


@pytest.mark.parametrize(
    ("provider_flag", "failure_text"),
    [
        (" --provider custom:new-provider", "Unknown provider 'removed-provider'"),
        ("", ""),
    ],
)
def test_config_set_model_recovers_failed_profile_resume_after_build_completes(
    monkeypatch, tmp_path, provider_flag, failure_text
):
    """Recovery waits for the real failed build and uses its owning profile.

    Both the failed and replacement generations cross the real deferred-build
    boundary. Provider resolution is the only model-switch leaf replaced.
    """
    from agent.secret_scope import current_secret_scope
    from hermes_constants import get_hermes_home

    launch_url = "https://launch.example/v1"
    profile_url = "https://profile.example/v1"
    launch_home = tmp_path / "launch"
    profile_home = tmp_path / "profiles" / "work"
    launch_home.mkdir()
    profile_home.mkdir(parents=True)
    (launch_home / "config.yaml").write_text(
        "model:\n"
        "  default: launch/model\n"
        "  provider: custom:new-provider\n"
        "providers:\n"
        "  new-provider:\n"
        f"    base_url: {launch_url}\n"
        "    key_env: LAUNCH_API_KEY\n",
        encoding="utf-8",
    )
    (launch_home / ".env").write_text(
        "LAUNCH_API_KEY=launch-secret\n", encoding="utf-8"
    )
    (profile_home / "config.yaml").write_text(
        "model:\n"
        "  default: old/model\n"
        "  provider: custom:new-provider\n"
        "providers:\n"
        "  new-provider:\n"
        f"    base_url: {profile_url}\n"
        "    key_env: PROFILE_API_KEY\n",
        encoding="utf-8",
    )
    (profile_home / ".env").write_text(
        "PROFILE_API_KEY=profile-secret\n", encoding="utf-8"
    )
    monkeypatch.setenv("HERMES_HOME", str(launch_home))
    monkeypatch.delenv("HERMES_MODEL", raising=False)
    monkeypatch.delenv("HERMES_INFERENCE_MODEL", raising=False)

    class ControlledReady:
        def __init__(self):
            self._event = threading.Event()
            self.wait_entered = threading.Event()

        def wait(self, timeout=None):
            self.wait_entered.set()
            return self._event.wait(timeout)

        def is_set(self):
            return self._event.is_set()

        def set(self):
            self._event.set()

    old_ready = ControlledReady()
    reasoning = {"effort": "high"}
    old_override = {"model": "old/model", "provider": "removed-provider"}
    session = _session(
        agent_ready=old_ready,
        agent_error=None,
        model_override=old_override,
        resume_runtime_overrides={
            "model_override": old_override,
            "provider_override": "removed-provider",
            "reasoning_config_override": reasoning,
        },
        profile_home=str(profile_home),
    )
    session["agent"] = None
    server._sessions["sid"] = session
    old_finally_entered = threading.Event()
    release_old_finally = threading.Event()
    switch_called = threading.Event()
    seen = {"switch": None, "build": None, "persisted": []}
    make_calls = 0

    def fake_switch_model(**kwargs):
        provider = kwargs["user_providers"]["new-provider"]
        secrets = dict(current_secret_scope() or {})
        api_key = secrets[provider["key_env"]]
        seen["switch"] = {
            "home": get_hermes_home(),
            "secrets": secrets,
            "base_url": provider["base_url"],
            "api_key": api_key,
            "current_provider": kwargs["current_provider"],
            "current_api_key": kwargs["current_api_key"],
        }
        switch_called.set()
        return types.SimpleNamespace(
            success=True,
            new_model="new/model",
            target_provider="custom:new-provider",
            api_key=api_key,
            base_url=provider["base_url"],
            api_mode="chat_completions",
            warning_message="",
            model_info=None,
            error_message="",
        )

    class FakeDb:
        def __init__(self, *_args, **_kwargs):
            pass

        def get_session(self, _key):
            return {"model_config": {}}

        def update_session_meta(self, key, model_config, model):
            seen["persisted"].append(
                {
                    "key": key,
                    "model": model,
                    "config": json.loads(model_config),
                }
            )

        def close(self):
            pass

    def fake_make_agent(_sid, _key, **kwargs):
        nonlocal make_calls
        make_calls += 1
        if make_calls == 1:
            raise RuntimeError(failure_text)
        override = kwargs["model_override"]
        seen["build"] = {
            "home": get_hermes_home(),
            "secrets": dict(current_secret_scope() or {}),
            "overrides": kwargs,
        }
        return types.SimpleNamespace(
            model=override["model"],
            provider="custom",
            base_url=override["base_url"],
            api_key=override["api_key"],
            api_mode=override["api_mode"],
            reasoning_config=kwargs.get("reasoning_config_override"),
            service_tier=None,
            _session_db=kwargs.get("session_db"),
        )

    real_transfer = server._transfer_db_to_agent

    def barrier_transfer(agent, db):
        if agent is None and not old_finally_entered.is_set():
            old_finally_entered.set()
            assert release_old_finally.wait(timeout=10)
        return real_transfer(agent, db)

    monkeypatch.setattr("hermes_cli.model_switch.switch_model", fake_switch_model)
    monkeypatch.setattr(
        "hermes_cli.model_selection_guards.combined_selection_warning",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr("hermes_state_registry.acquire", FakeDb)
    monkeypatch.setattr(server, "_make_agent", fake_make_agent)
    monkeypatch.setattr(server, "_transfer_db_to_agent", barrier_transfer)
    monkeypatch.setattr(
        "tui_gateway.entry.ensure_mcp_discovery_started", lambda: None
    )
    monkeypatch.setattr(server, "_wire_callbacks", lambda _sid: None)
    monkeypatch.setattr(server, "_start_notification_poller", lambda *a, **k: None)
    monkeypatch.setattr(server, "_notify_session_boundary", lambda *a, **k: None)
    monkeypatch.setattr(server, "_session_info", lambda *a, **k: {})
    monkeypatch.setattr(server, "_probe_config_health", lambda *_args: None)
    monkeypatch.setattr(server, "_schedule_mcp_late_refresh", lambda *a, **k: None)
    monkeypatch.setattr(server, "_emit", lambda *a, **k: None)

    response = {}

    def run_request():
        try:
            response["value"] = server.handle_request(
                {
                    "id": "1",
                    "method": "config.set",
                    "params": {
                        "session_id": "sid",
                        "key": "model",
                        "value": f"new/model{provider_flag}",
                    },
                }
            )
        except BaseException as exc:
            response["error"] = exc

    request_thread = threading.Thread(target=run_request)
    old_build_thread = None
    try:
        server._start_agent_build("sid", session)
        old_build_thread = session["_agent_build_thread"]
        assert old_finally_entered.wait(timeout=10)
        assert session["agent_error"] == failure_text
        assert not old_ready.is_set()

        request_thread.start()
        assert old_ready.wait_entered.wait(timeout=2), (
            "model recovery did not wait for the failed build generation"
        )
        assert not switch_called.is_set()
        release_old_finally.set()
        request_thread.join(timeout=10)

        assert not request_thread.is_alive()
        assert "error" not in response
        assert response["value"]["result"]["value"] == "new/model"
        assert make_calls == 2
        assert seen["switch"] == {
            "home": profile_home,
            "secrets": {"PROFILE_API_KEY": "profile-secret"},
            "base_url": profile_url,
            "api_key": "profile-secret",
            "current_provider": (
                "custom:new-provider" if provider_flag else "custom"
            ),
            "current_api_key": "profile-secret" if not provider_flag else "",
        }
        assert seen["build"]["home"] == profile_home
        assert seen["build"]["secrets"] == {
            "PROFILE_API_KEY": "profile-secret"
        }
        overrides = seen["build"]["overrides"]
        assert overrides["model_override"] == session["model_override"]
        assert overrides["provider_override"] == "custom:new-provider"
        assert overrides["reasoning_config_override"] == reasoning
        assert session["agent_error"] is None
        assert session["agent"].model == "new/model"
        assert session["agent"].base_url == profile_url
        assert session["agent"].api_key == "profile-secret"
        assert seen["persisted"] == [
            {
                "key": "session-key",
                "model": "new/model",
                "config": {
                    "model": "new/model",
                    "provider": "custom:new-provider",
                    "base_url": profile_url,
                    "api_mode": "chat_completions",
                    "reasoning_config": reasoning,
                },
            }
        ]
    finally:
        release_old_finally.set()
        old_ready.set()
        request_thread.join(timeout=10)
        if old_build_thread is not None:
            old_build_thread.join(timeout=10)
        new_build_thread = session.get("_agent_build_thread")
        if new_build_thread is not None:
            new_build_thread.join(timeout=10)
        server._sessions.pop("sid", None)
