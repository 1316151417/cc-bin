# cc-bin

> [中文说明](README-CN.md)

A lightweight Claude Code provider management tool — two tiny Zsh scripts that let you switch between or isolate LLM providers effortlessly.

## What is this?

When using [Claude Code](https://claude.ai/code), you're not limited to Anthropic's models. Providers like **Zhipu (GLM)**, **MiniMax**, **DeepSeek**, and **Mimo** expose Anthropic-compatible APIs. This project gives you two simple scripts to manage these providers.

## Scripts

### `ccs` — Provider Switch (global)

Permanently switches Claude Code to use a specific provider by updating `~/.claude/settings.json`.

```bash
ccs <zp|mm|ds|mimo>
```

**What it does:**
- Backs up your existing `settings.json` to `settings.json.bak`
- Writes a new settings file with the chosen provider's API endpoint, API key, and model mapping
- All subsequent `claude` invocations will use this provider

### `ccp` — Provider Per-Invocation (isolated)

Launches `claude` with a specific provider **without** touching your global config. If no provider flag is given, falls back to `~/.claude/settings.json`.

```bash
ccp [zp|mm|ds|mimo] [claude options...]
```

**What it does:**
- When a provider is specified, writes a temporary settings file to `.claude/settings-<provider>.json` and launches `claude` with `--settings` pointing to that file
- When called without a provider flag, simply passes through to `claude` using your default `~/.claude/settings.json`
- Your global config remains untouched in either case — other sessions are unaffected

## Problems Solved

### 1. `ccs` — A lighter alternative to `cc-switch`

The official `cc-switch` carries a fair amount of baggage. `ccs` is a **~40-line Zsh script** that does exactly one thing: write the right provider into `settings.json`. No dependencies, no complexity — just a bash/zsh associative array and a heredoc.

### 2. `ccp` — Session isolation with `--settings`

Switching your global provider mid-session would disrupt any active Claude Code conversations and tie all sessions to a single provider's concurrency limits.

`ccp` solves this by leveraging Claude Code's `--settings` flag. Each invocation gets its own settings file, so:
- Your global provider stays unchanged — active sessions are never interrupted
- Each session can use a different provider, bypassing concurrency limits on any single one
- The whole thing is another **~40 lines of Zsh**

## Provider-to-Model Mapping

| Key | Provider | Sonnet | Opus | Haiku |
|-----|----------|--------|------|-------|
| zp  | Zhipu    | GLM-5.1 | GLM-5.1 | GLM-4.5-Air |
| mm  | MiniMax  | MiniMax-M2.7 | MiniMax-M2.7 | MiniMax-M2.7 |
| ds  | DeepSeek | deepseek-v4-pro | deepseek-v4-pro | deepseek-v4-flash |
| mimo | Mimo    | mimo-v2.5-pro | mimo-v2.5-pro | mimo-v2.5-pro |

## Environment Variables

Both scripts read credentials from environment variables:

```bash
export ZHIPU_BASE_URL="https://open.bigmodel.cn/api/paas/v4"
export ZHIPU_API_KEY="your-key-here"

export MINIMAX_BASE_URL="https://api.minimax.chat/v1"
export MINIMAX_API_KEY="your-key-here"

export DEEPSEEK_BASE_URL="https://api.deepseek.com"
export DEEPSEEK_API_KEY="your-key-here"

export MIMO_BASE_URL="https://api.mimoml.com"
export MIMO_API_KEY="your-key-here"
```

The API endpoint is formed by appending `/anthropic` to the base URL.

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/cc-bin.git ~/cc-bin
```

### 2. Add to PATH

Add this line to your `~/.zshrc`:

```bash
export PATH="$HOME/cc-bin:$PATH"
```

Then reload:

```bash
source ~/.zshrc
```

### 3. Set credentials

Add your provider credentials to `~/.zshrc` (or any shell config you source):

```bash
export DEEPSEEK_BASE_URL="https://api.deepseek.com"
export DEEPSEEK_API_KEY="sk-..."
# ... repeat for other providers
```

### 4. Give it a try

```bash
# Switch globally to DeepSeek
ccs ds

# ...or fire up a one-off session with MiniMax
ccp mm
```

## License

MIT
