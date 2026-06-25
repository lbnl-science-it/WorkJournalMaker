# ABOUTME: Tests for the commit-msg hook's chainlink-to-GitHub issue ID translation.
# ABOUTME: Covers mapping loading, message translation, and the main orchestrator.

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "hooks"))
from translate_issue_ids import load_mapping, translate_message, main


SAMPLE_SYNC = {
    "repo": "lbnl-science-it/WorkJournalMaker",
    "issues": {
        "106": {"chainlink_id": 7, "updated_at": "2026-04-22T18:49:48Z", "comment_count": 0},
        "101": {"chainlink_id": 12, "updated_at": "2026-04-22T18:49:38Z", "comment_count": 0},
        "152": {"chainlink_id": 38, "updated_at": "2026-06-23T00:33:41Z", "comment_count": 0},
    },
    "exported": {
        "35": {"gh_number": 145, "gh_url": "https://github.com/example/issues/145"},
        "34": {"gh_number": 146, "gh_url": "https://github.com/example/issues/146"},
    },
}


class TestLoadMapping:
    def test_loads_issues_section(self, tmp_path):
        sync_file = tmp_path / "github-sync.json"
        data = {"repo": "test", "issues": {"106": {"chainlink_id": 7}}, "exported": {}}
        sync_file.write_text(json.dumps(data))

        mapping = load_mapping(sync_file)
        assert mapping[7] == 106

    def test_loads_exported_section(self, tmp_path):
        sync_file = tmp_path / "github-sync.json"
        data = {"repo": "test", "issues": {}, "exported": {"35": {"gh_number": 145}}}
        sync_file.write_text(json.dumps(data))

        mapping = load_mapping(sync_file)
        assert mapping[35] == 145

    def test_loads_both_sections_combined(self, tmp_path):
        sync_file = tmp_path / "github-sync.json"
        sync_file.write_text(json.dumps(SAMPLE_SYNC))

        mapping = load_mapping(sync_file)
        assert mapping[7] == 106
        assert mapping[12] == 101
        assert mapping[38] == 152
        assert mapping[35] == 145
        assert mapping[34] == 146

    def test_returns_empty_dict_when_file_missing(self, tmp_path):
        missing = tmp_path / "nonexistent.json"
        mapping = load_mapping(missing)
        assert mapping == {}

    def test_returns_empty_dict_on_malformed_json(self, tmp_path):
        sync_file = tmp_path / "github-sync.json"
        sync_file.write_text("{not valid json")

        mapping = load_mapping(sync_file)
        assert mapping == {}

    def test_returns_empty_dict_on_unexpected_structure(self, tmp_path):
        sync_file = tmp_path / "github-sync.json"
        sync_file.write_text(json.dumps({"unexpected": "structure"}))

        mapping = load_mapping(sync_file)
        assert mapping == {}

    def test_handles_empty_issues_and_exported(self, tmp_path):
        sync_file = tmp_path / "github-sync.json"
        data = {"repo": "test", "issues": {}, "exported": {}}
        sync_file.write_text(json.dumps(data))

        mapping = load_mapping(sync_file)
        assert mapping == {}


class TestTranslateMessage:
    def test_replaces_known_id_in_subject_parens(self):
        mapping = {7: 106}
        result, replacements = translate_message("fix: gate debug pages (#7)", mapping)
        assert result == "fix: gate debug pages (#106)"
        assert replacements == [(7, 106)]

    def test_replaces_known_id_in_closes_syntax(self):
        mapping = {12: 101}
        result, _ = translate_message("Closes #12", mapping)
        assert result == "Closes #101"

    def test_leaves_unknown_id_untouched(self):
        mapping = {7: 106}
        result, replacements = translate_message("Fixes #999", mapping)
        assert result == "Fixes #999"
        assert replacements == []

    def test_empty_message_returns_empty(self):
        result, replacements = translate_message("", {7: 106})
        assert result == ""
        assert replacements == []

    def test_no_hash_refs_returns_unchanged(self):
        msg = "refactor: clean up logging"
        result, replacements = translate_message(msg, {7: 106})
        assert result == msg
        assert replacements == []

    def test_multiple_refs_in_one_message(self):
        mapping = {7: 106, 12: 101}
        msg = "fix: issues (#7, #12)"
        result, replacements = translate_message(msg, mapping)
        assert result == "fix: issues (#106, #101)"
        assert (7, 106) in replacements
        assert (12, 101) in replacements

    def test_mix_of_known_and_unknown_ids(self):
        mapping = {7: 106}
        msg = "fix: issues (#7, #999)"
        result, replacements = translate_message(msg, mapping)
        assert result == "fix: issues (#106, #999)"
        assert replacements == [(7, 106)]

    def test_idempotent_second_pass(self):
        mapping = {7: 106, 35: 145}
        msg = "fix: close bug (#7)"
        translated, _ = translate_message(msg, mapping)
        assert translated == "fix: close bug (#106)"

        second_pass, replacements = translate_message(translated, mapping)
        assert second_pass == translated
        assert replacements == []

    def test_returns_replacement_list_with_duplicates(self):
        mapping = {7: 106}
        msg = "Closes #7, also refs #7"
        result, replacements = translate_message(msg, mapping)
        assert result == "Closes #106, also refs #106"
        assert replacements == [(7, 106), (7, 106)]


class TestMain:
    def _write_sync_file(self, repo_root, data=None):
        chainlink_dir = repo_root / ".chainlink"
        chainlink_dir.mkdir(exist_ok=True)
        sync_file = chainlink_dir / "github-sync.json"
        sync_file.write_text(json.dumps(data or SAMPLE_SYNC))

    def test_rewrites_commit_msg_file(self, tmp_path):
        self._write_sync_file(tmp_path)
        msg_file = tmp_path / "COMMIT_EDITMSG"
        msg_file.write_text("fix: gate debug pages (#7)")

        exit_code = main(str(msg_file), repo_root=str(tmp_path))

        assert exit_code == 0
        assert msg_file.read_text() == "fix: gate debug pages (#106)"

    def test_no_modification_when_no_mapping_file(self, tmp_path):
        msg_file = tmp_path / "COMMIT_EDITMSG"
        original = "fix: something (#7)"
        msg_file.write_text(original)

        exit_code = main(str(msg_file), repo_root=str(tmp_path))

        assert exit_code == 0
        assert msg_file.read_text() == original

    def test_prints_translation_to_stderr(self, tmp_path, capsys):
        self._write_sync_file(tmp_path)
        msg_file = tmp_path / "COMMIT_EDITMSG"
        msg_file.write_text("Closes #7")

        main(str(msg_file), repo_root=str(tmp_path))

        captured = capsys.readouterr()
        assert "#7" in captured.err
        assert "#106" in captured.err

    def test_returns_zero_on_success(self, tmp_path):
        self._write_sync_file(tmp_path)
        msg_file = tmp_path / "COMMIT_EDITMSG"
        msg_file.write_text("no refs here")

        assert main(str(msg_file), repo_root=str(tmp_path)) == 0

    def test_handles_empty_commit_message(self, tmp_path):
        self._write_sync_file(tmp_path)
        msg_file = tmp_path / "COMMIT_EDITMSG"
        msg_file.write_text("")

        exit_code = main(str(msg_file), repo_root=str(tmp_path))

        assert exit_code == 0
        assert msg_file.read_text() == ""
