#!/usr/bin/env bash
# =============================================================
# deploy_sync.sh
# -------------------------------------------------------------
# Commits the latest data/jobs.json (and any other tracked
# changes) and force-pushes to the connected GitHub remote so
# Cloudflare Pages automatically redeploys.
#
# Intended trigger: n8n Execute Command node on the Mac Mini.
# Usage:  bash /path/to/deploy_sync.sh  [optional commit message]
# =============================================================

set -euo pipefail

# ── Resolve repo root (parent of the scripts/ directory) ────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

# ── Config ──────────────────────────────────────────────────
MAIN_BRANCH="${DEPLOY_BRANCH:-main}"
REMOTE="${DEPLOY_REMOTE:-origin}"
COMMIT_MSG="${1:-sync: update jobs.json $(date -u '+%Y-%m-%dT%H:%M:%SZ')}"

# ── Safety checks ──────────────────────────────────────────
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "❌ ERROR: ${REPO_ROOT} is not a git repository."
  echo "   Run: git init && git remote add origin <your-repo-url>"
  exit 1
fi

if ! git ls-remote --exit-code "${REMOTE}" &>/dev/null; then
  echo "❌ ERROR: No remote '${REMOTE}' reachable."
  echo "   Configure with: git remote add origin <url>"
  exit 1
fi

# ── Stage & commit ─────────────────────────────────────────
git add -A

# Skip commit if nothing changed
if git diff --cached --quiet; then
  echo "ℹ️  No changes to commit. Exiting."
  exit 0
fi

git commit -m "${COMMIT_MSG}"
echo "✅ Committed: ${COMMIT_MSG}"

# ── Push ───────────────────────────────────────────────────
# Use --force-with-lease so we never silently overwrite
# someone else's legitimate push.
git push "${REMOTE}" "HEAD:${MAIN_BRANCH}" --force-with-lease
echo "🚀 Pushed to ${REMOTE}/${MAIN_BRANCH} — Cloudflare Pages will deploy shortly."
