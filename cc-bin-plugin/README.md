# cc-bin-plugin

Claude Code **2.1.288** fullscreen Mod。输入 `/provider`，使用官方 Select 选择已配置 API Key 的 Provider，调用 `ccs` 写入全局设置。成功后显示 `✓ Provider switched to …`，后续请求使用新配置，无需重启。

## 安装 / 更新

准备 Bash、Zsh、curl、tar 和 Claude Code 2.1.288，执行：

```bash
curl -fsSL https://raw.githubusercontent.com/1316151417/cc-bin/main/install.sh | bash
```

已有本地 cc-bin 源码时，在仓库根目录执行 `bash install.sh` 即可安装当前版本。两种方式均可重复执行以更新，不需要 `source`。

安装器把插件运行文件复制到 `~/.claude/skills/cc-bin-provider/`，把两个独立命令 `ccs`、`ccp` 安装到 `~/cc-bin/`。源码目录可以移动；安装后的插件和命令不依赖源码位置。

PATH 行仅在缺失时追加到 `~/.zshrc`，新增后打开新终端即可使用。安装或更新后，新开 Claude Code 会话会自动加载插件，无需 `--plugin-dir`。

## 使用

按 [Provider 配置表](../README.md#provider-配置) export 所需 Key，并确保 `ccs` 在 PATH 中，再新开 fullscreen 会话：

```zsh
ccs --list
claude --settings '{"tui":"fullscreen"}'
```

输入 `/provider`，方向键选择、Enter 切换、Esc 关闭。可用 `claude plugin list` 查看安装结果，插件 ID 为 `cc-bin-provider@skills-dir`。

列表由 `ccs --list` 返回：只看非空 API Key，忽略 BASE_URL。MiniMax、MiMo 默认 Coding Plan，按量 API 入口带 `-api` 后缀并标注「（API）」；智谱、Anthropic（`an`）、DeepSeek（`ds`）各只有一个入口，名称和缩写不加 API 标记。只设置 `ZHIPU_API_KEY` 时，只显示「智谱」。Key 必须在启动 Claude 前 export，插件不读取 `.zshrc`。

## 行为与限制

- `/provider` 复用 `ccs <缩写>`，整体替换 `~/.claude/settings.json`，备份到 `settings.json.bak`；多个使用全局配置的进程可能一起受影响。
- 无 Key、ccs 不可用、列表非法、切换失败或 UI 无法打开时显示错误，可重试；不显示凭证和原始进程输出。配置生成或备份失败时保留原配置。
- Anthropic API Key 在首次打开菜单时保存在插件内存，供之后切回；不写额外凭证文件。
- 成功提示表示配置已写入。请在当前请求结束后切换；`ccp`、自定义配置目录及其他 Provider/model 覆盖可能优先于全局文件。

## 验证

在 cc-bin 根目录运行：

```sh
python3 tests/cli_integration.py
python3 tests/install_integration.py
claude plugin validate --strict --json ./cc-bin-plugin
claude plugin test ./cc-bin-plugin
```

Mod 测试覆盖官方 Select、七项入口、错误重试与脱敏；安装测试验证真实 Claude 能自动发现插件并注册 `/provider`。真实 Provider 请求未测试；此前隔离环境的 fullscreen 启动被 Anthropic 连通性检查（HTTP 403）阻止，实际键盘交互及远端路由尚未验收。

参考官方 [Mods](https://github.com/anthropics/claude-code/tree/main/mods)。`spike/` 保留早期研究记录，不参与运行。
