# Shared by ccs and ccp: credential prefix, endpoint, Sonnet, Opus, Haiku.
# Full Anthropic-compatible endpoints; BASE_URL environment variables are ignored.
declare -A PROVIDERS=(
  [an]="ANTHROPIC https://api.anthropic.com claude-sonnet-5-5 claude-opus-5-5 claude-haiku-4-5-20251001"
  [zp]="ZHIPU https://open.bigmodel.cn/api/anthropic GLM-5.3 GLM-5.3 GLM-5.3-Flash"
  [ds]="DEEPSEEK https://api.deepseek.com/anthropic deepseek-flash deepseek-flash deepseek-flash"
  [mm]="MINIMAX https://api.minimax.cn/anthropic MiniMax-M3 MiniMax-M3 MiniMax-M3"
  [mm-api]="MINIMAX_PAYGO https://api.minimax.cn/anthropic MiniMax-M3 MiniMax-M3 MiniMax-M3"
  [mimo]="MIMO https://token-plan-cn.xiaomimimo.com/anthropic mimo-v2.6-pro mimo-v2.6-pro mimo-v2.6-flash"
  [mimo-api]="MIMO_PAYGO https://api.xiaomimimo.com/anthropic mimo-v2.6-pro mimo-v2.6-pro mimo-v2.6-flash"
)
provider_order=(an zp ds mm mm-api mimo mimo-api)

# Only stable IDs leave the process, never credentials.
list_providers() {
  local provider prefix base_url sonnet opus haiku key_var api_key separator=""
  printf '['
  for provider in "${provider_order[@]}"; do
    read -r prefix base_url sonnet opus haiku <<< "${PROVIDERS[$provider]}"
    key_var="${prefix}_API_KEY"
    api_key="${(P)key_var:-}"
    if [[ -n "${api_key//[[:space:]]/}" ]]; then
      printf '%s"%s"' "$separator" "$provider"
      separator=","
    fi
  done
  printf ']\n'
}

load_provider() {
  local key="${1:-}" prefix key_var api_key
  if [[ -z "${PROVIDERS[$key]:-}" ]]; then
    print -u2 -- "Supported providers: ${(j:|:)provider_order}"
    return 1
  fi
  read -r prefix base_url sonnet opus haiku <<< "${PROVIDERS[$key]}"
  key_var="${prefix}_API_KEY"
  api_key="${(P)key_var:-}"
  if [[ -z "${api_key//[[:space:]]/}" ]]; then
    print -u2 -- "Missing $key_var. Export it before switching."
    return 1
  fi
  if [[ "$api_key" == *[[:cntrl:]]* ]]; then
    print -u2 -- 'Provider configuration contains invalid control characters.'
    return 1
  fi
  auth_key=""
  auth_token=""
  if [[ "$key" == an ]]; then
    auth_key="$api_key"
  else
    auth_token="$api_key"
  fi
}

# The caller redirects this to a private file. Keep the original values for child env.
render_provider_settings() {
  local json_key="$auth_key" json_token="$auth_token"
  json_key="${json_key//\\/\\\\}"
  json_key="${json_key//\"/\\\"}"
  json_token="${json_token//\\/\\\\}"
  json_token="${json_token//\"/\\\"}"
  cat <<EOF
{
  "env": {
    "ANTHROPIC_BASE_URL": "$base_url",
    "ANTHROPIC_API_KEY": "$json_key",
    "ANTHROPIC_AUTH_TOKEN": "$json_token",
    "API_TIMEOUT_MS": "3000000",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": 1,
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "$sonnet",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "$opus",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "$haiku"
  },
  "tui": "fullscreen"
}
EOF
}
