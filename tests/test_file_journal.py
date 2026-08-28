import os
import tempfile
from pathlib import Path
import pytest
from agent.file_safety import FileJournalManager


def test_file_journal_lifecycle_and_rollback(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_home = Path(tmpdir) / ".hermes"
        tmp_home.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("HERMES_HOME", str(tmp_home))

        workspace = Path(tmpdir) / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)

        session_id = "test-session-123"

        # 1. Test file creation in Turn 0
        file_a = workspace / "test_a.txt"
        FileJournalManager.record_before_write(session_id, 0, str(file_a))
        file_a.write_text("line 1\nline 2\n", encoding="utf-8")
        entry_0 = FileJournalManager.record_after_write(session_id, 0, str(file_a), action="create")

        assert entry_0 is not None
        assert entry_0["turn_index"] == 0
        assert entry_0["action"] == "create"
        assert "+line 1" in entry_0["diff"]

        # 2. Test file modification in Turn 1
        FileJournalManager.record_before_write(session_id, 1, str(file_a))
        file_a.write_text("line 1\nline 2 modified\nline 3\n", encoding="utf-8")
        entry_1 = FileJournalManager.record_after_write(session_id, 1, str(file_a), action="modify")

        assert entry_1 is not None
        assert entry_1["turn_index"] == 1
        assert "-line 2" in entry_1["diff"]
        assert "+line 2 modified" in entry_1["diff"]

        # 3. Test get_session_journal
        journal = FileJournalManager.get_session_journal(session_id)
        assert len(journal) == 2
        assert journal[0]["turn_index"] == 0
        assert journal[1]["turn_index"] == 1

        # 4. Test rollback Turn 1
        res_1 = FileJournalManager.rollback_turn(session_id, 1)
        assert res_1["success"] is True
        assert file_a.read_text(encoding="utf-8") == "line 1\nline 2\n"

        # 5. Test rollback Turn 0 (should remove created file)
        res_0 = FileJournalManager.rollback_turn(session_id, 0)
        assert res_0["success"] is True
        assert not file_a.exists()
