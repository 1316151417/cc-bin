#!/usr/bin/env zsh

set -euo pipefail

source "${0:A:h}/lib/providers.zsh"

case "${1:-}" in
  --list) list_providers; exit 0 ;;
  --help|-h)
    echo "Usage: ccp <${(j:|:)provider_order}> [claude options...] | --list"
    exit 0 ;;
  --) shift; exec claude "$@" ;;
  ""|-*) exec claude "$@" ;;
esac

load_provider "$1"
shift

umask 077
settings_file=$(mktemp "${TMPDIR:-/tmp}/ccp-settings.XXXXXX")
trap 'rm -f -- "$settings_file"' EXIT
# Let Claude finish handling terminal signals before EXIT removes its settings.
trap ':' INT TERM HUP
render_provider_settings > "$settings_file"

echo "Use $sonnet/$opus/$haiku"
# These overrides belong only to the child; inherited Anthropic settings cannot win.
# Keep the wrapper alive so its EXIT trap removes the credential file on completion.
ANTHROPIC_BASE_URL="$base_url" \
ANTHROPIC_API_KEY="$auth_key" \
ANTHROPIC_AUTH_TOKEN="$auth_token" \
ANTHROPIC_MODEL="$sonnet" \
ANTHROPIC_DEFAULT_SONNET_MODEL="$sonnet" \
ANTHROPIC_DEFAULT_OPUS_MODEL="$opus" \
ANTHROPIC_DEFAULT_HAIKU_MODEL="$haiku" \
claude --settings "$settings_file" "$@"
