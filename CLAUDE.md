# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repo provides helper scripts and a fullscreen plugin for switching Claude Code between LLM providers via their Anthropic-compatible APIs.

## Scripts

- **`lib/ccs`** — Replaces the global Claude Code config (`~/.claude/settings.json`) with a provider preset and saves the previous file as `settings.json.bak`.
- **`lib/ccp`** — Launches `claude` with a per-invocation provider setting. Creates a private settings file in the system temporary directory and removes it when Claude exits; leaves global settings unchanged.
- **`/provider`** — Fullscreen plugin picker; discovers available providers with `ccs --list` and switches with `ccs <provider>`.

## Provider configuration

`lib/providers.zsh` is the shared source for provider IDs, credential prefixes, endpoints, model mappings and settings generation. `ccs --help` and `ccp --help` list supported arguments; `README.md` documents the API Key variables. The installer embeds the definitions into standalone commands.

Root-level visible files are `README.md`, `install.sh` and `CLAUDE.md`. Keep command sources in `lib/`, plugin sources in `cc-bin-plugin/`, tests in `tests/` and screenshots in `docs/images/`. Installed commands remain at `~/cc-bin/ccs` and `~/cc-bin/ccp`.

Provider discovery uses nonblank API Keys. Endpoints are built in; BASE_URL environment variables are ignored. Use an API suffix in IDs and picker labels only to distinguish an API entry from the same provider's Coding Plan entry.

## .claude/ directory

- `.claude/settings.local.json` — Local permissions (allowed git commands). Managed manually.
- `.claude/settings-<provider>.json` — Legacy files created by older `ccp` versions in the script's source directory. Current commands use system temporary files instead. Remove legacy files only when they are no longer referenced manually or by running sessions.
