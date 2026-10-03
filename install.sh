#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 0 ]]; then
  printf '%s\n' 'Usage: bash /path/to/cc-bin/install.sh (install or update from a local checkout)' >&2
  exit 1
fi
for dependency in zsh claude; do
  if ! command -v "$dependency" >/dev/null; then
    printf 'Missing dependency: %s\n' "$dependency" >&2
    exit 1
  fi
done

bin_dir="$HOME/cc-bin"
plugin_dir="$HOME/.claude/skills/cc-bin-provider"
zshrc="$HOME/.zshrc"
path_line='export PATH="$HOME/cc-bin:$PATH"'
if [[ -e "$bin_dir/.git" ]]; then
  printf '%s\n' 'Move the source checkout out of ~/cc-bin first; this directory is reserved for ccs and ccp.' >&2
  exit 1
fi
for target in "$bin_dir/ccs" "$bin_dir/ccp" "$zshrc"; do
  if [[ -d "$target" ]]; then
    printf 'Expected a file, found a directory: %s\n' "$target" >&2
    exit 1
  fi
done

staging=$(mktemp -d "${TMPDIR:-/tmp}/cc-bin-install.XXXXXX")
trap 'rm -rf -- "$staging"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

source_dir=""
if [[ -n "${BASH_SOURCE[0]:-}" ]]; then
  source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
fi
if [[ -z "$source_dir" || ! -f "$source_dir/ccs" || ! -f "$source_dir/ccp" ]]; then
  curl -fsSL https://codeload.github.com/1316151417/cc-bin/tar.gz/refs/heads/main -o "$staging/source.tar.gz"
  tar -xzf "$staging/source.tar.gz" -C "$staging"
  source_dir="$staging/cc-bin-main"
fi
if [[ ! -f "$source_dir/lib/providers.zsh" || ! -f "$source_dir/cc-bin-plugin/.claude-plugin/plugin.json" ]]; then
  printf '%s\n' 'The source package is missing Provider definitions or the plugin.' >&2
  exit 1
fi

# Only replace our own installed directory, or migrate the former source symlink.
if [[ -L "$plugin_dir" ]]; then
  linked_source=$(readlink "$plugin_dir")
  if [[ "$linked_source" != "$source_dir/cc-bin-plugin" && "$linked_source" != "$HOME/cc-bin/cc-bin-plugin" ]]; then
    printf '%s\n' 'Plugin path is an unrelated symlink; it was not overwritten.' >&2
    exit 1
  fi
elif [[ -e "$plugin_dir" ]] && [[ ! -d "$plugin_dir" || ! -f "$plugin_dir/.cc-bin-managed" ]]; then
  printf '%s\n' 'Plugin directory already exists and is not managed by this installer; it was not overwritten.' >&2
  exit 1
fi

# Embed the shared definitions so installed commands need no source checkout or lib/.
for name in ccs ccp; do
  embedded=0
  while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ "$line" == 'source "${0:A:h}/lib/providers.zsh"' ]]; then
      cat "$source_dir/lib/providers.zsh"
      embedded=1
    else
      printf '%s\n' "$line"
    fi
  done < "$source_dir/$name" > "$staging/$name"
  if [[ "$embedded" != 1 ]]; then
    printf 'Could not bundle Provider definitions into %s.\n' "$name" >&2
    exit 1
  fi
  zsh -n "$staging/$name"
  chmod 755 "$staging/$name"
done
mkdir -p "$staging/plugin/.claude-plugin"
cp "$source_dir/cc-bin-plugin/.claude-plugin/plugin.json" "$staging/plugin/.claude-plugin/"
cp -R "$source_dir/cc-bin-plugin/hooks" "$staging/plugin/"
printf '%s\n' 'cc-bin installer' > "$staging/plugin/.cc-bin-managed"
if ! claude plugin validate --strict "$staging/plugin" </dev/null > "$staging/validation.log" 2>&1; then
  printf '%s\n' 'Plugin validation failed; the installed version was not changed.' >&2
  cat "$staging/validation.log" >&2
  exit 1
fi

mkdir -p "$bin_dir" "$(dirname -- "$plugin_dir")"
if [[ -e "$plugin_dir" || -L "$plugin_dir" ]]; then
  mv -- "$plugin_dir" "$staging/previous-plugin"
fi
if ! mv -- "$staging/plugin" "$plugin_dir"; then
  if [[ -e "$staging/previous-plugin" || -L "$staging/previous-plugin" ]]; then
    mv -- "$staging/previous-plugin" "$plugin_dir"
  fi
  exit 1
fi
for name in ccs ccp; do
  mv -f -- "$staging/$name" "$bin_dir/$name"
done

if [[ ! -f "$zshrc" ]] || ! grep -Fxq -- "$path_line" "$zshrc"; then
  printf '\n%s\n' "$path_line" >> "$zshrc"
  printf '%s\n' 'PATH added to ~/.zshrc; open a new terminal.'
fi
printf '%s\n' '✓ cc-bin ready: ccp, ccs, cc-bin-plugin.'
printf '%s\n' 'Open a new fullscreen Claude Code session and enter /provider.'
