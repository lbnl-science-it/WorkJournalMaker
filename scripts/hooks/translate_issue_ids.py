#!/usr/bin/env python3
# ABOUTME: Translates chainlink issue IDs to GitHub issue numbers in commit messages.
# ABOUTME: Reads .chainlink/github-sync.json to build the chainlink→GitHub mapping.

import json
import re
import subprocess
import sys
from pathlib import Path

ISSUE_REF = re.compile(r"#(\d+)")


def load_mapping(sync_json_path):
    """Build a chainlink_id → github_number map from github-sync.json."""
    try:
        data = json.loads(Path(sync_json_path).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

    mapping = {}

    for gh_num_str, entry in data.get("issues", {}).items():
        try:
            mapping[entry["chainlink_id"]] = int(gh_num_str)
        except (KeyError, ValueError, TypeError):
            continue

    for cl_id_str, entry in data.get("exported", {}).items():
        try:
            mapping[int(cl_id_str)] = entry["gh_number"]
        except (KeyError, ValueError, TypeError):
            continue

    return mapping


def translate_message(message, mapping):
    """Replace #N references where N is a known chainlink ID with the GitHub number."""
    replacements = []

    def replacer(match):
        n = int(match.group(1))
        if n in mapping:
            replacements.append((n, mapping[n]))
            return f"#{mapping[n]}"
        return match.group(0)

    translated = ISSUE_REF.sub(replacer, message)
    return translated, replacements


def main(commit_msg_file, repo_root=None):
    """Read commit message, translate chainlink IDs, write back."""
    if repo_root is None:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True
        )
        repo_root = result.stdout.strip()

    sync_path = Path(repo_root) / ".chainlink" / "github-sync.json"
    mapping = load_mapping(sync_path)

    msg_path = Path(commit_msg_file)
    original = msg_path.read_text()

    translated, replacements = translate_message(original, mapping)

    if replacements:
        for cl_id, gh_num in replacements:
            print(f"commit-msg hook: #{cl_id} → #{gh_num}", file=sys.stderr)
        msg_path.write_text(translated)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
