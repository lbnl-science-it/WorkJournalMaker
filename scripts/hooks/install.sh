#!/usr/bin/env bash
# ABOUTME: Installs tracked git hooks by creating symlinks in .git/hooks/.
# ABOUTME: Safe to run multiple times (symlinks are idempotent via -sf).

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HOOKS_SRC="$REPO_ROOT/scripts/hooks"
HOOKS_DST="$REPO_ROOT/.git/hooks"

ln -sf "$HOOKS_SRC/commit-msg" "$HOOKS_DST/commit-msg"
echo "Installed commit-msg hook → scripts/hooks/commit-msg"
