"""Exercise Bash installation, standalone commands and native Mod autoload in a temporary HOME."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

from cli_integration import fingerprint

ROOT = Path(__file__).resolve().parents[1]
PATH_LINE = 'export PATH="$HOME/cc-bin:$PATH"'


def assert_install_output(result, path_added=False):
    expected = [
        '✓ cc-bin ready: ccp, ccs, cc-bin-plugin.',
        'Open a new fullscreen Claude Code session and enter /provider.',
    ]
    if path_added:
        expected.insert(0, 'PATH added to ~/.zshrc; open a new terminal.')
    assert result.stdout.splitlines() == expected, "Successful install output was not concise"
    assert not result.stderr, "Successful install printed diagnostics"


def run(argv, env, cwd, success=True, input=None):
    result = subprocess.run(argv, env=env, cwd=cwd, input=input, capture_output=True, text=True, timeout=30)
    assert (result.returncode == 0) == success, f"Unexpected status for {argv[0]} (output withheld)"
    return result


def main():
    claude = shutil.which("claude")
    zsh = shutil.which("zsh")
    bash = shutil.which("bash")
    assert claude and zsh and bash, "Claude Code, Zsh and Bash are required"
    real_files = [Path.home() / ".zshrc", Path.home() / ".claude/settings.json"]
    before = [fingerprint(path) for path in real_files]
    try:
        with tempfile.TemporaryDirectory(prefix="cc-bin-install-test-") as directory:
            work = Path(directory)
            fixture = work / "source checkout"
            fixture.mkdir()
            for relative in ("install.sh", "lib/ccs", "lib/ccp", "lib/providers.zsh",
                             "cc-bin-plugin/.claude-plugin/plugin.json", "cc-bin-plugin/hooks/hooks.json",
                             "cc-bin-plugin/hooks/register.tsx"):
                target = fixture / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, target)
            source_before = {str(p.relative_to(fixture)): fingerprint(p) for p in fixture.rglob('*') if p.is_file()}

            def environment(home):
                home.mkdir(exist_ok=True)
                return {"HOME": str(home), "CLAUDE_CONFIG_DIR": str(home / ".claude"),
                        "PATH": f"{Path(claude).parent}:{os.defpath}"}

            def install(home, success=True):
                return run([bash, str(fixture / "install.sh")], environment(home), home, success)

            def update_source(tag, version):
                for name in ('lib/ccs', 'lib/ccp', 'lib/providers.zsh'):
                    path = fixture / name
                    path.write_text(path.read_text() + f'\n# {tag}\n')
                manifest = fixture / 'cc-bin-plugin/.claude-plugin/plugin.json'
                data = json.loads(manifest.read_text())
                data['version'] = version
                manifest.write_text(json.dumps(data))
                hooks_dir = fixture / 'cc-bin-plugin/hooks'
                module = hooks_dir / json.loads((hooks_dir / 'hooks.json').read_text())['modules'][0]
                module.write_text(module.read_text() + f'\n// {tag}\n')

            def assert_updated(home, tag, version):
                for name in ('ccs', 'ccp'):
                    installed = (home / 'cc-bin' / name).read_text()
                    assert installed.count(f'# {tag}') == 2, f'{name} or shared Provider definitions were not updated'
                plugin = home / '.claude/skills/cc-bin-provider'
                assert json.loads((plugin / '.claude-plugin/plugin.json').read_text())['version'] == version
                source_hooks = fixture / 'cc-bin-plugin/hooks'
                source_files = {str(p.relative_to(source_hooks)): p.read_bytes() for p in source_hooks.rglob('*') if p.is_file()}
                installed_files = {str(p.relative_to(plugin / 'hooks')): p.read_bytes() for p in (plugin / 'hooks').rglob('*') if p.is_file()}
                assert installed_files == source_files, 'Plugin runtime files were not fully updated'

            home = work / "user"
            env = environment(home)
            rc = home / ".zshrc"
            original_rc = 'printf "sourced\\n" >> "$HOME/rc-sources"'  # No final newline.
            rc.write_text(original_rc)
            assert_install_output(install(home), path_added=True)
            bin_dir = home / "cc-bin"
            plugin = home / ".claude/skills/cc-bin-provider"
            assert sorted(p.name for p in bin_dir.iterdir()) == ["ccp", "ccs"]
            assert all(p.is_file() and not p.is_symlink() and os.access(p, os.X_OK) for p in bin_dir.iterdir())
            assert plugin.is_dir() and not plugin.is_symlink(), "Plugin depends on source checkout"
            assert rc.read_text() == original_rc + "\n" + PATH_LINE + "\n"
            assert not (home / "rc-sources").exists(), "Bash installer sourced the user's Zsh configuration"
            assert not (home / ".claude/settings.json").exists(), "Installer wrote global settings"
            assert source_before == {str(p.relative_to(fixture)): fingerprint(p) for p in fixture.rglob('*') if p.is_file()}

            # A new normal Zsh shell sees PATH; installation does not claim to modify its parent.
            result = run([zsh, "-ic", "command -v ccs; command -v ccp"], env, home)
            assert str(bin_dir / "ccs") in result.stdout and str(bin_dir / "ccp") in result.stdout
            assert (home / "rc-sources").read_text() == "sourced\n"

            # Remove the source from its original location, then test the installed commands.
            hidden_source = work / "moved source"
            fixture.rename(hidden_source)
            run([sys.executable, str(ROOT / "tests/cli_integration.py"), str(bin_dir)], env, home)
            plugins = json.loads(run([claude, "plugin", "list", "--json"], env, home).stdout)
            assert any(p["id"] == "cc-bin-provider@skills-dir" and p["enabled"] for p in plugins)
            probe_env = env | {"ANTHROPIC_BASE_URL": "http://127.0.0.1:9", "ANTHROPIC_API_KEY": "dummy-probe",
                               "DISABLE_AUTOUPDATER": "1"}
            probe = run([claude, "-p", "/provider"], probe_env, home)
            assert "requires Claude Code fullscreen terminal mode" in probe.stdout, "Installed Mod did not auto-load"
            hidden_source.rename(fixture)

            saved_rc = fingerprint(rc)
            assert_install_output(install(home))
            assert fingerprint(rc) == saved_rc, "Repeat install edited .zshrc"
            assert (home / "rc-sources").read_text() == "sourced\n"
            manifest = fixture / "cc-bin-plugin/.claude-plugin/plugin.json"
            update_source('local update fixture', '0.2.1')
            hooks = fixture / 'cc-bin-plugin/hooks/hooks.json'
            data = json.loads(hooks.read_text())
            data['modules'] = ['./extra/register.tsx']
            hooks.write_text(json.dumps(data))
            extra = fixture / 'cc-bin-plugin/hooks/extra/register.tsx'
            extra.parent.mkdir()
            (fixture / 'cc-bin-plugin/hooks/register.tsx').rename(extra)
            (plugin / 'hooks/stale.ts').write_text('// obsolete installed module\n')
            assert_install_output(install(home))
            assert_updated(home, 'local update fixture', '0.2.1')
            assert 'requires Claude Code fullscreen terminal mode' in run([claude, '-p', '/provider'], probe_env, home).stdout, 'Updated Mod did not auto-load'
            assert fingerprint(rc) == saved_rc
            assert sorted(p.name for p in bin_dir.iterdir()) == ["ccp", "ccs"]

            # Pipe-to-Bash mode downloads/extracts a package; fake only the network, not the installer.
            archive = work / "source.tar.gz"
            def package_source():
                with tarfile.open(archive, "w:gz") as tar:
                    tar.add(fixture, arcname="cc-bin-main")
            package_source()
            fake_bin = work / "fake-bin"
            fake_bin.mkdir()
            curl = fake_bin / "curl"
            curl.write_text('''#!/bin/sh
while [ "$#" -gt 0 ]; do
  case "$1" in -o) shift; destination="$1" ;; esac
  shift
done
cp "$TEST_ARCHIVE" "$destination"
''')
            curl.chmod(0o700)
            remote_home = work / "remote-user"
            remote_env = environment(remote_home) | {"PATH": f"{fake_bin}:{env['PATH']}", "TEST_ARCHIVE": str(archive)}
            assert_install_output(run([bash], remote_env, remote_home, input=(ROOT / "install.sh").read_text()), path_added=True)
            assert_updated(remote_home, 'local update fixture', '0.2.1')
            assert sorted(p.name for p in (remote_home / "cc-bin").iterdir()) == ["ccp", "ccs"]
            assert (remote_home / ".zshrc").read_text().count(PATH_LINE) == 1
            assert not (remote_home / "cc-bin/.git").exists()

            remote_rc = fingerprint(remote_home / '.zshrc')
            update_source('remote update fixture', '0.2.2')
            package_source()
            assert_install_output(run([bash], remote_env, remote_home, input=(ROOT / "install.sh").read_text()))
            assert_updated(remote_home, 'remote update fixture', '0.2.2')
            assert fingerprint(remote_home / '.zshrc') == remote_rc, 'Remote update edited .zshrc'

            occupied = work / "old-checkout"
            environment(occupied)
            (occupied / "cc-bin/.git").mkdir(parents=True)
            install(occupied, success=False)
            assert (occupied / "cc-bin/.git").is_dir()
            assert not (occupied / ".zshrc").exists()

            conflict = work / "plugin-conflict"
            environment(conflict)
            existing = conflict / ".claude/skills/cc-bin-provider"
            existing.mkdir(parents=True)
            (existing / "keep").write_text("preserve plugin")
            install(conflict, success=False)
            assert (existing / "keep").read_text() == "preserve plugin"
            assert not (conflict / "cc-bin").exists()
            assert not (conflict / ".zshrc").exists()

            legacy = work / "legacy-symlink"
            environment(legacy)
            old_link = legacy / ".claude/skills/cc-bin-provider"
            old_link.parent.mkdir(parents=True)
            old_link.symlink_to(legacy / "cc-bin/cc-bin-plugin", target_is_directory=True)
            install(legacy)
            assert old_link.is_dir() and not old_link.is_symlink()

            # Invalid downloaded/local plugin must leave the previously installed version untouched.
            installed_paths = [bin_dir / 'ccs', bin_dir / 'ccp', *[p for p in plugin.rglob('*') if p.is_file()]]
            config_before = {str(p): fingerprint(p) for p in installed_paths}
            manifest.write_text("not json")
            failed = install(home, success=False)
            assert 'Plugin validation failed' in failed.stderr and 'plugin.json' in failed.stderr, 'Validation failure hid diagnostics'
            assert not failed.stdout, 'Failed install printed success output'
            assert config_before == {str(p): fingerprint(p) for p in installed_paths}, 'Failed validation changed an installed component'
            assert fingerprint(rc) == saved_rc
    finally:
        assert [fingerprint(path) for path in real_files] == before, "Real .zshrc or settings changed"
    print("PASS: concise output, local/remote updates of ccs/ccp/shared presets/all plugin hooks, stale file removal, Mod autoload, PATH deduplication and failure safety; real config unchanged.")


if __name__ == "__main__":
    main()
