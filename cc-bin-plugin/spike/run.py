#!/usr/bin/env python3
"""Reproduce the 2.1.288 Provider API spike using two loopback Mock APIs.

No real credentials or Provider configs are read. Claude uses a temporary
config directory, an empty working directory, and placeholder credentials.
Only credential comparisons (booleans), model IDs, paths and hook counts are
recorded. The original settings file is hashed, never printed or written.
"""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


HERE = Path(__file__).resolve().parent
EXPECTED_VERSION = "2.1.288"
INITIAL_KEY = "spike-initial-placeholder"
REPLACEMENT_KEY = "spike-replacement-placeholder"


def fingerprint(path):
    if not path.exists():
        return {"exists": False}
    return {
        "exists": True,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "mtime_ns": path.stat().st_mtime_ns,
    }


class MockAPI(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def reply(self, data, content_type="application/json"):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self.reply(b'{"data":[],"has_more":false}')

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        body = json.loads(raw)
        self.server.records.append({
            "path": self.path,
            "model": body.get("model"),
            "uses_initial_key": self.headers.get("x-api-key") == INITIAL_KEY,
            "uses_replacement_key": self.headers.get("x-api-key") == REPLACEMENT_KEY,
        })
        if "count_tokens" in self.path:
            self.reply(b'{"input_tokens":10}')
            return
        message = {
            "id": "msg_spike", "type": "message", "role": "assistant",
            "model": body.get("model"), "content": [],
            "stop_reason": None, "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 0},
        }
        if not body.get("stream"):
            message.update(
                content=[{"type": "text", "text": "SPIKE_OK"}],
                stop_reason="end_turn",
                usage={"input_tokens": 10, "output_tokens": 3},
            )
            self.reply(json.dumps(message).encode())
            return
        events = [
            ("message_start", {"type": "message_start", "message": message}),
            ("content_block_start", {"type": "content_block_start", "index": 0,
                                     "content_block": {"type": "text", "text": ""}}),
            ("content_block_delta", {"type": "content_block_delta", "index": 0,
                                     "delta": {"type": "text_delta", "text": "SPIKE_OK"}}),
            ("content_block_stop", {"type": "content_block_stop", "index": 0}),
            ("message_delta", {"type": "message_delta",
                               "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                               "usage": {"output_tokens": 3}}),
            ("message_stop", {"type": "message_stop"}),
        ]
        data = "".join(
            f"event: {name}\ndata: {json.dumps(value)}\n\n"
            for name, value in events
        ).encode()
        self.reply(data, "text/event-stream")


def isolated_env(config):
    blocked = ("ANTHROPIC_", "CLAUDE_", "AWS_", "GOOGLE_", "AZURE_")
    env = {key: value for key, value in os.environ.items()
           if not key.upper().startswith(blocked)
           and key.upper() not in {"HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"}}
    env.update(CLAUDE_CONFIG_DIR=str(config), API_TIMEOUT_MS="5000",
               NO_PROXY="127.0.0.1,localhost", no_proxy="127.0.0.1,localhost")
    return env


def save_type_excerpts(types_file):
    text = types_file.read_text()
    lines = text.splitlines()
    sections = [
        (1, 13), (2383, 2415), (2530, 2711), (3169, 3214),
        (3370, 3408), (5788, 5845), (7783, 7821), (12566, 12668),
        (9800, 9842),
    ]
    # Fixed ranges belong to 2.1.288 only; refuse use against another version.
    assert lines[0] == f"// Written by Claude Code {EXPECTED_VERSION}."
    out = ["Exact excerpts of engine-generated declarations (not hand-written types).",
           "Source: .claude-plugin/types/claude-code/index.d.ts",
           "Full file SHA-256: " + hashlib.sha256(text.encode()).hexdigest()]
    for start, end in sections:
        out.extend(["", f"--- original lines {start}-{end} ---"])
        out.extend(f"{number}: {lines[number - 1]}" for number in range(start, end + 1))
    (HERE / "evidence" / "types.txt").write_text("\n".join(out) + "\n")


def main():
    claude = shutil.which("claude")
    if not claude:
        raise RuntimeError("claude executable not found")
    version = subprocess.check_output([claude, "--version", "--verbose"], text=True)
    if not version.startswith(EXPECTED_VERSION + " "):
        raise RuntimeError("This spike is pinned to Claude Code 2.1.288")
    settings = Path.home() / ".claude" / "settings.json"
    before = fingerprint(settings)
    servers = {}
    result = None
    try:
        with tempfile.TemporaryDirectory(prefix="cc-provider-spike-") as tmp:
            root = Path(tmp)
            plugin, config, work = root / "probe", root / "config", root / "work"
            for path in (plugin / ".claude-plugin", plugin / "hooks", config, work):
                path.mkdir(parents=True)
            urls = {}
            for label in ("A", "B"):
                server = ThreadingHTTPServer(("127.0.0.1", 0), MockAPI)
                server.records = []
                servers[label] = server
                urls[label] = f"http://127.0.0.1:{server.server_port}"
                threading.Thread(target=server.serve_forever, daemon=True).start()
            (plugin / ".claude-plugin/plugin.json").write_text(json.dumps({
                "name": "provider-live-spike", "version": "0.0.0",
                "description": "Local transport capability spike",
                "author": {"name": "cc-bin-plugin"},
            }))
            (plugin / "hooks/hooks.json").write_text('{"modules":["./probe.ts"]}')
            counts = plugin / "counts.json"
            source = (HERE / "probe.ts").read_text()
            source = source.replace("__REPLACEMENT_URL__", json.dumps(urls["B"]))
            source = source.replace("__COUNTS_PATH__", json.dumps(str(counts)))
            (plugin / "hooks/probe.ts").write_text(source)
            env = isolated_env(config)
            validated = subprocess.run(
                [claude, "plugin", "validate", "--json", str(plugin)],
                env=env, cwd=work, text=True, capture_output=True, timeout=20,
            )
            assert json.loads(validated.stdout)["success"], "Probe validation failed"
            env.update(ANTHROPIC_API_KEY=INITIAL_KEY, ANTHROPIC_BASE_URL=urls["A"])
            run = subprocess.run([
                claude, "--setting-sources", "", "--settings", "{}",
                "--plugin-dir", str(plugin), "--model", "spike-initial-model",
                "--tools", "", "--system-prompt", "Reply SPIKE_OK.",
                "--no-session-persistence", "-p", "test local transport",
            ], env=env, cwd=work, text=True, capture_output=True, timeout=30)
            hooks = json.loads(counts.read_text()) if counts.exists() else None
            types_file = plugin / ".claude-plugin/types/claude-code/index.d.ts"
            (HERE / "evidence").mkdir(exist_ok=True)
            save_type_excerpts(types_file)
            requests = {key: server.records for key, server in servers.items()}
            passed = (
                run.returncode == 0 and run.stdout.strip() == "SPIKE_OK"
                and hooks == {"envReads": 0, "httpCalls": 0, "completions": 0, "steps": 1}
                and len(requests["A"]) == 1 and not requests["B"]
                and requests["A"][0]["model"] == "spike-rewritten-model"
                and requests["A"][0]["uses_initial_key"]
                and not requests["A"][0]["uses_replacement_key"]
            )
            result = {
                "version": version.strip(), "binary_sha256": fingerprint(Path(claude).resolve())["sha256"],
                "probe_validated": True, "exit_code": run.returncode,
                "reply_matches": run.stdout.strip() == "SPIKE_OK",
                "hook_counts": hooks, "requests": requests,
                "observed_expected_limitation": passed,
                "settings_before": before,
            }
    finally:
        for server in servers.values():
            server.shutdown()
            server.server_close()
        after = fingerprint(settings)
        if result is not None:
            result.update(settings_after=after, settings_unchanged=before == after)
            (HERE / "evidence" / "results.json").write_text(json.dumps(result, indent=2) + "\n")
        if before != after:
            raise RuntimeError("User settings changed during spike; investigate concurrent writes")
    if not result or not result["observed_expected_limitation"]:
        raise RuntimeError("Spike differed from the documented result; inspect evidence/results.json")
    print("PASS: model rewritten; Provider URL/key unchanged; request hooks bypassed; settings unchanged.")
    print("Evidence: spike/evidence/results.json and spike/evidence/types.txt")


if __name__ == "__main__":
    main()
