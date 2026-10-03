"""Exercise ccs and ccp with dummy credentials and isolated child environments."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time


# alias, credential prefix, default Anthropic-compatible endpoint
PROVIDERS = [
    ("an", "ANTHROPIC", "https://api.anthropic.com"),
    ("zp", "ZHIPU", "https://open.bigmodel.cn/api/anthropic"),
    ("ds", "DEEPSEEK", "https://api.deepseek.com/anthropic"),
    ("mm", "MINIMAX", "https://api.minimax.cn/anthropic"),
    ("mm-api", "MINIMAX_PAYGO", "https://api.minimax.cn/anthropic"),
    ("mimo", "MIMO", "https://token-plan-cn.xiaomimimo.com/anthropic"),
    ("mimo-api", "MIMO_PAYGO", "https://api.xiaomimimo.com/anthropic"),
]


def fingerprint(path):
    if not path.exists():
        return None
    if path.is_dir():
        return "directory", path.stat().st_mtime_ns
    return hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns


def wait_for_files(paths, failure_message):
    deadline = time.monotonic() + 5
    while not all(path.exists() for path in paths):
        assert time.monotonic() < deadline, failure_message
        time.sleep(0.02)


def exercise_ccp(commands_dir, directory):
    launch_home = directory / "launch-home"
    settings = launch_home / ".claude/settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text('{"sentinel":"unchanged"}\n')
    before = fingerprint(settings)
    temporary = directory / "temporary"
    temporary.mkdir()
    fake_bin = directory / "claude-bin"
    fake_bin.mkdir()
    fake_claude = fake_bin / "claude"
    fake_claude.write_text(f"#!{sys.executable}\n" + '''
import json, os, signal, sys, time
from pathlib import Path
if os.environ.get("TEST_IGNORE_INT"):
    signal.signal(signal.SIGINT, lambda *_: None)
args = sys.argv[1:]
record = {"args": args}
if args and args[0] == "--settings":
    settings = Path(args[1])
    record.update(config=json.loads(settings.read_text()), mode=settings.stat().st_mode & 0o777)
    record["env"] = {name: os.environ.get(name) for name in record["config"]["env"]}
    record["model"] = os.environ.get("ANTHROPIC_MODEL")
capture = Path(os.environ["TEST_CAPTURE"])
pending = capture.with_suffix(".pending")
pending.write_text(json.dumps(record))
pending.replace(capture)
if "TEST_RELEASE" in os.environ:
    deadline = time.monotonic() + 10
    while not Path(os.environ["TEST_RELEASE"]).exists():
        if time.monotonic() > deadline:
            sys.exit(99)
        time.sleep(0.02)
sys.exit(int(os.environ.get("TEST_EXIT", "0")))
''')
    fake_claude.chmod(0o700)
    capture = directory / "launch.json"
    child_env = {"HOME": str(launch_home), "PATH": f"{fake_bin}:{os.defpath}",
                 "TMPDIR": str(temporary), "TEST_CAPTURE": str(capture)}
    ccp = str(commands_dir / "ccp")

    def run(args, variables=None, code=0, launched=True):
        capture.unlink(missing_ok=True)
        result = subprocess.run([ccp, *args], env=child_env | (variables or {}),
                                capture_output=True, text=True, timeout=10)
        assert result.returncode == code, "Unexpected ccp status (output withheld)"
        assert "dummy-" not in result.stdout + result.stderr, "ccp echoed credentials"
        assert fingerprint(settings) == before, "ccp changed global settings"
        assert not list(temporary.iterdir()), "ccp temporary credential file leaked"
        if launched:
            return json.loads(capture.read_text())
        assert not capture.exists(), "ccp unexpectedly launched Claude"
        return result

    assert json.loads(run(["--list"], launched=False).stdout) == []
    assert json.loads(run(["--list"], {"OPENAI_API_KEY": "dummy-openai",
                                     "ZHIPU_BASE_URL": "https://unused.invalid"}, launched=False).stdout) == []
    for alias, prefix, endpoint in PROVIDERS:
        credential = {f"{prefix}_API_KEY": f"dummy-{alias}"}
        assert json.loads(run(["--list"], credential, launched=False).stdout) == [alias]
        assert json.loads(run(["--list"], {f"{prefix}_API_KEY": " \t "}, launched=False).stdout) == []
        run([alias], code=1, launched=False)
        stale = {"ANTHROPIC_API_KEY": "dummy-stale-key", "ANTHROPIC_AUTH_TOKEN": "dummy-stale-token",
                 "ANTHROPIC_BASE_URL": "https://stale.invalid", "ANTHROPIC_MODEL": "stale-model",
                 f"{prefix}_BASE_URL": "https://override.invalid"}
        record = run([alias, "-p", "hello world", "--model", "opus"], stale | credential)
        config = record["config"]["env"]
        assert config["ANTHROPIC_BASE_URL"] == endpoint
        key = credential[f"{prefix}_API_KEY"]
        assert config["ANTHROPIC_API_KEY"] == (key if alias == "an" else "")
        assert config["ANTHROPIC_AUTH_TOKEN"] == ("" if alias == "an" else key)
        for name in ("ANTHROPIC_BASE_URL", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
                     "ANTHROPIC_DEFAULT_SONNET_MODEL", "ANTHROPIC_DEFAULT_OPUS_MODEL", "ANTHROPIC_DEFAULT_HAIKU_MODEL"):
            assert record["env"][name] == config[name], "Child inherited a stale Provider value"
        assert record["model"] == config["ANTHROPIC_DEFAULT_SONNET_MODEL"]
        assert record["config"]["tui"] == "fullscreen"
        assert record["mode"] == 0o600
        assert record["args"][2:] == ["-p", "hello world", "--model", "opus"]

    for alias, prefix in (("an", "ANTHROPIC"), ("mm-api", "MINIMAX_PAYGO")):
        unusual_key = 'dummy-"quoted\\key'
        record = run([alias], {f"{prefix}_API_KEY": unusual_key})
        field = "ANTHROPIC_API_KEY" if alias == "an" else "ANTHROPIC_AUTH_TOKEN"
        assert record["config"]["env"][field] == record["env"][field] == unusual_key
    for args, expected in (([], []), (["-p", "hello world"], ["-p", "hello world"]),
                           (["--", "hello world"], ["hello world"])):
        assert run(args)["args"] == expected
    run(["--help"], launched=False)
    for alias in ("an-api", "ds-api", "openai", "mm-plan", "mimo-plan"):
        run([alias], {"OPENAI_API_KEY": "dummy-openai"}, code=1, launched=False)
    for key in (" \t ", "dummy-control\ncharacter"):
        run(["zp"], {"ZHIPU_API_KEY": key}, code=1, launched=False)
    run(["mm-api"], {"MINIMAX_PAYGO_API_KEY": "dummy-mm", "TEST_EXIT": "23"}, code=23)

    # Same provider, two credentials: both settings must coexist until each child exits.
    release = directory / "release"
    captures = [directory / f"parallel-{index}.json" for index in range(2)]
    processes = []
    try:
        for index, target in enumerate(captures):
            env = child_env | {"MINIMAX_API_KEY": f"dummy-parallel-{index}",
                               "TEST_CAPTURE": str(target), "TEST_RELEASE": str(release)}
            processes.append(subprocess.Popen([ccp, "mm"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE))
        wait_for_files(captures, "Concurrent launches did not become ready")
        records = [json.loads(target.read_text()) for target in captures]
        assert records[0]["args"][1] != records[1]["args"][1], "Launches shared a settings file"
        for index, record in enumerate(records):
            config = json.loads(Path(record["args"][1]).read_text())
            assert config["env"]["ANTHROPIC_AUTH_TOKEN"] == f"dummy-parallel-{index}"
        assert fingerprint(settings) == before
    finally:
        release.touch()
        for process in processes:
            stdout, stderr = process.communicate(timeout=10)
            assert process.returncode == 0, "Concurrent ccp failed (output withheld)"
            assert b"dummy-" not in stdout + stderr, "Concurrent ccp echoed credentials"
    assert not list(temporary.iterdir()), "Concurrent credential file leaked"
    assert fingerprint(settings) == before

    # Terminal interruption must clean up, but cancelling a turn must keep the file alive.
    for sig, handles in ((signal.SIGINT, False), (signal.SIGTERM, False),
                         (signal.SIGHUP, False), (signal.SIGINT, True)):
        capture.unlink(missing_ok=True)
        release.unlink(missing_ok=True)
        env = child_env | {"ZHIPU_API_KEY": "dummy-signal", "TEST_RELEASE": str(release),
                           "TEST_IGNORE_INT": "1" if handles else ""}
        process = subprocess.Popen([ccp, "zp"], env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True)
        try:
            wait_for_files([capture], "Signal test did not become ready")
            config_path = Path(json.loads(capture.read_text())["args"][1])
            os.killpg(process.pid, sig)
            if handles:
                time.sleep(0.1)
                assert process.poll() is None, "Wrapper exited while Claude handled Ctrl-C"
                assert config_path.exists(), "Settings removed while Claude still running"
                release.touch()
            stdout, stderr = process.communicate(timeout=5)
            assert process.returncode == (0 if handles else 128 + sig), "Wrong interruption status"
            assert b"dummy-" not in stdout + stderr
            assert not config_path.exists(), "Interrupted credential file leaked"
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.communicate(timeout=5)


def main():
    commands_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "lib"
    ccs = str(commands_dir / "ccs")

    real_settings = Path.home() / ".claude/settings.json"
    real_backup = real_settings.with_suffix(".json.bak")
    before = fingerprint(real_settings), fingerprint(real_backup)
    try:
        with tempfile.TemporaryDirectory(prefix="cc-bin-provider-test-") as directory:
            settings = Path(directory) / ".claude/settings.json"
            backup = settings.with_suffix(".json.bak")
            # Only the spawned ccs sees this directory. No inherited credentials.
            child_env = {"HOME": directory, "PATH": os.defpath}

            def run(alias, variables=None, success=True):
                result = subprocess.run([ccs, alias], env=child_env | (variables or {}),
                                        capture_output=True, text=True, timeout=10)
                assert (result.returncode == 0) == success, f"Unexpected ccs status for {alias} (output withheld)"
                assert "dummy-" not in result.stdout + result.stderr, "Credential echoed"
                return result

            def listed(variables):
                return json.loads(run("--list", variables).stdout)

            # Discovery is read-only, has no BASE_URL requirement, and ignores OpenAI.
            assert listed({}) == []
            assert listed({"OPENAI_API_KEY": "dummy-openai", "ZHIPU_BASE_URL": "https://unused.invalid"}) == []
            for alias, prefix, _ in PROVIDERS:
                assert listed({f"{prefix}_API_KEY": "dummy-key"}) == [alias]
                assert listed({f"{prefix}_API_KEY": " \t "}) == []
            assert not settings.parent.exists(), "Discovery created configuration"

            credentials = {f"{prefix}_API_KEY": f"dummy-{alias}" for alias, prefix, _ in PROVIDERS}
            assert listed(credentials) == [alias for alias, _, _ in PROVIDERS]
            settings.parent.mkdir()
            settings.write_text('{"test_original":true}\n')

            for alias, prefix, endpoint in PROVIDERS:
                previous = settings.read_bytes()
                # Switching back to native must not reuse the last provider URL/token.
                run(alias, credentials | {"ANTHROPIC_BASE_URL": "https://previous.invalid/anthropic",
                                          "ANTHROPIC_AUTH_TOKEN": "dummy-previous"})
                config = json.loads(settings.read_text())
                env = config["env"]
                assert env["ANTHROPIC_BASE_URL"] == endpoint, f"Wrong endpoint for {alias}"
                key = credentials[f"{prefix}_API_KEY"]
                assert env["ANTHROPIC_API_KEY"] == (key if alias == "an" else "")
                assert env["ANTHROPIC_AUTH_TOKEN"] == ("" if alias == "an" else key)
                for family in ("SONNET", "OPUS", "HAIKU"):
                    assert env[f"ANTHROPIC_DEFAULT_{family}_MODEL"]
                assert config["tui"] == "fullscreen"
                assert backup.read_bytes() == previous
                assert settings.stat().st_mode & 0o777 == 0o600
                assert backup.stat().st_mode & 0o777 == 0o600

            # Ignore BASE_URL overrides and JSON-escape credential values.
            unusual_key = 'dummy-"quoted\\key'
            run("ds", {"DEEPSEEK_API_KEY": unusual_key, "DEEPSEEK_BASE_URL": "https://override.invalid/"})
            config = json.loads(settings.read_text())["env"]
            assert config["ANTHROPIC_AUTH_TOKEN"] == unusual_key
            assert config["ANTHROPIC_BASE_URL"] == "https://api.deepseek.com/anthropic"

            def rejected(alias, variables):
                previous = settings.read_bytes(), fingerprint(backup)
                run(alias, variables, success=False)
                assert (settings.read_bytes(), fingerprint(backup)) == previous, "Failure changed configuration"
                assert not list(settings.parent.glob("settings.json.tmp.*")), "Temporary credential file leaked"

            for alias, _, _ in PROVIDERS:
                rejected(alias, {})
            rejected("openai", {"OPENAI_API_KEY": "dummy-openai"})
            for obsolete in ("anthropic", "an-api", "ds-api", "mm-plan", "mimo-plan"):
                rejected(obsolete, credentials)
            rejected("ds", {"DEEPSEEK_API_KEY": " \t "})
            rejected("ds", {"DEEPSEEK_API_KEY": "dummy-control\ncharacter"})

            # Simulate backup failure after generating the replacement; retain the original.
            fake_bin = Path(directory) / "bin"
            fake_bin.mkdir()
            failing_cp = fake_bin / "cp"
            failing_cp.write_text("#!/bin/sh\nexit 23\n")
            failing_cp.chmod(0o700)
            rejected("ds", credentials | {"PATH": f"{fake_bin}:{os.defpath}"})

            backup.unlink()
            backup.mkdir()
            rejected("ds", credentials)
            exercise_ccp(commands_dir, Path(directory))
    finally:
        assert before == (fingerprint(real_settings), fingerprint(real_backup)), "Real settings or backup changed"

    print("PASS: ccs/ccp key discovery, seven presets, auth isolation, JSON escaping, failure safety, concurrent launches and cleanup; real settings and backup unchanged.")


if __name__ == "__main__":
    main()
