#!/usr/bin/env zsh

set -euo pipefail

# 提供商配置：prefix sonnet opus haiku
declare -A PROVIDERS=(
  [zp]="ZHIPU GLM-5.1 GLM-5.1 GLM-4.5-Air"
  [mm]="MINIMAX MiniMax-M2.7 MiniMax-M2.7 MiniMax-M2.7"
  [ds]="DEEPSEEK deepseek-v4-pro deepseek-v4-pro deepseek-v4-flash"
  [mimo]="MIMO mimo-v2.5-pro mimo-v2.5-pro mimo-v2.5-pro"
)

# 解析参数
provider=""
passthrough=()
if [[ $# -gt 0 && -n "${PROVIDERS[$1]:-}" ]]; then
  provider="$1"; shift
fi
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: ccp <${(kj:|:)PROVIDERS}> [claude options...]"; exit 0
fi
passthrough=("$@")

if [[ -n "$provider" ]]; then
  read -r prefix sonnet opus haiku <<< "${PROVIDERS[$provider]}"
  base_var="${prefix}_BASE_URL"
  key_var="${prefix}_API_KEY"
  base_url="${(P)base_var:?Error: $base_var not set}/anthropic"
  api_key="${(P)key_var:?Error: $key_var not set}"

  settings_file="${0:A:h}/.claude/settings-${provider}.json"
  mkdir -p "${settings_file:h}"
  printf '{"env":{"ANTHROPIC_BASE_URL":"%s","ANTHROPIC_AUTH_TOKEN":"%s","ANTHROPIC_DEFAULT_SONNET_MODEL":"%s","ANTHROPIC_DEFAULT_OPUS_MODEL":"%s","ANTHROPIC_DEFAULT_HAIKU_MODEL":"%s"}}\n' \
    "$base_url" "$api_key" "$sonnet" "$opus" "$haiku" > "$settings_file"

  set -- "--settings" "$settings_file" "${passthrough[@]}"
else
  set -- "${passthrough[@]}"
fi

[[ -n "$provider" ]] && echo "Use $sonnet/$opus/$haiku"
exec claude "$@"
