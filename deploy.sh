#!/usr/bin/env bash
# Push the site to GitHub. The token is read from a file outside the repo and
# is never written into the repository, logged, or committed.
#
#   ./deploy.sh                  uses ~/.deploy-token
#   GITHUB_TOKEN=xxx ./deploy.sh uses the token from the environment instead
#
# The token needs: repo (classic) or Contents: Read and write (fine-grained).
set -euo pipefail

REPO_URL="https://github.com/elitebotstudios-dot/elitebotstudios-.git"
TOKEN_FILE="${HOME}/.deploy-token"

if [ -z "${GITHUB_TOKEN:-}" ]; then
  if [ -f "$TOKEN_FILE" ]; then
    GITHUB_TOKEN="$(tr -d '\n\r' < "$TOKEN_FILE")"
  else
    echo "No token. Either create ${TOKEN_FILE} (mode 600) or run:" >&2
    echo "  GITHUB_TOKEN=xxx ./deploy.sh" >&2
    exit 1
  fi
fi
export GITHUB_TOKEN

# The origin remote is not stored in this workspace's snapshot, so re-add it if
# it has gone missing rather than failing with a confusing git error.
if ! git remote get-url origin >/dev/null 2>&1; then
  echo "→ restoring the origin remote…"
  git remote add origin "$REPO_URL"
fi

ASKPASS="$(mktemp)"
trap 'rm -f "$ASKPASS"' EXIT
# git prompts for a username, then a password. GitHub accepts any non-empty
# username with the token as the password.
cat > "$ASKPASS" <<'EOS'
#!/bin/sh
case "$1" in
  *sername*) printf %s x-access-token ;;
  *)         printf %s "$GITHUB_TOKEN" ;;
esac
EOS
chmod 700 "$ASKPASS"

echo "→ fetching…"
GIT_ASKPASS="$ASKPASS" GIT_TERMINAL_PROMPT=0 git -c credential.helper= \
  fetch origin main --quiet

BEHIND="$(git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)"
AHEAD="$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)"
echo "   $AHEAD to push, $BEHIND to pull"

if [ "$BEHIND" != "0" ]; then
  echo "→ remote has commits we do not have; fast-forwarding…"
  git merge --ff-only origin/main
fi

if [ "$AHEAD" = "0" ] && [ "$BEHIND" = "0" ]; then
  echo "→ nothing to push. Production is already at $(git rev-parse --short HEAD)"
  exit 0
fi

echo "→ pushing main…"
GIT_ASKPASS="$ASKPASS" GIT_TERMINAL_PROMPT=0 git -c credential.helper= \
  push origin main

echo "→ pushed $(git rev-parse --short HEAD). Vercel builds from main."
echo
echo "If no deployment appears within a few minutes, the Hobby-plan author check"
echo "blocked it. Fix with an empty commit by the Vercel-authorised account:"
echo
echo "  git commit --allow-empty -q -m 'chore: trigger deployment' \\"
echo "    --author='elitebotstudios-dot <317663787+elitebotstudios-dot@users.noreply.github.com>'"
echo "  ./deploy.sh"
