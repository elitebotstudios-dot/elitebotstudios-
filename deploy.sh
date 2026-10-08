#!/usr/bin/env bash
# Push the site to GitHub without ever writing the token to disk.
#
#   1. Create a token at https://github.com/settings/tokens
#      Scope needed: repo  (classic), or Contents: Read and write (fine-grained)
#   2. Run:
#        GITHUB_TOKEN=<your-token> ./deploy.sh
#
# The token is read from the environment, used for this one push, and the
# temporary askpass helper is removed on exit. Nothing is logged.
set -euo pipefail

if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "GITHUB_TOKEN is not set. Run:  GITHUB_TOKEN=xxx ./deploy.sh" >&2
  exit 1
fi

ASKPASS="$(mktemp)"
trap 'rm -f "$ASKPASS"' EXIT
# git asks for a username first, then a password. GitHub wants any non-empty
# username with the token as the password, so answer each prompt correctly.
cat > "$ASKPASS" <<'EOS'
#!/bin/sh
case "$1" in
  *sername*) printf %s x-access-token ;;
  *)         printf %s "$GITHUB_TOKEN" ;;
esac
EOS
chmod 700 "$ASKPASS"

echo "→ pushing main…"
GIT_ASKPASS="$ASKPASS" \
GIT_TERMINAL_PROMPT=0 \
  git -c credential.helper= \
      push origin main

echo "→ pushed. Vercel will build from main."
echo
echo "If the deployment does not appear within a couple of minutes, the Hobby-plan"
echo "author check has blocked it. Fix with an empty deploy-trigger commit by the"
echo "Vercel-authorised account:"
echo
echo "  git commit --allow-empty -m 'chore: trigger deployment' \\"
echo "    --author='elitebotstudios-dot <317663787+elitebotstudios-dot@users.noreply.github.com>'"
echo "  GITHUB_TOKEN=<token> ./deploy.sh"
