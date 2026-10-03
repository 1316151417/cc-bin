# cc-bin

为 Claude Code 切换 Provider：只需配置 API Key，内置服务地址和模型映射。

- `ccs`：切换全局 Provider，运行中的 Claude Code 后续请求使用新配置。
- `ccp`：指定 Provider 启动 Claude Code，使用独立配置，不修改全局设置。
- `/provider`：fullscreen 内用官方 Select 选择 Provider，复用 `ccs`。

## 安装 / 更新

需要 Bash、Zsh 和 Claude Code **2.1.288**。在线安装还需要 curl、tar；无需 npm install。

```bash
curl -fsSL https://raw.githubusercontent.com/1316151417/cc-bin/main/install.sh | bash
```

在本地源码目录安装当前版本：

```bash
bash install.sh
```

两种方式都会安装 `ccs`、`ccp` 和插件，重复执行时三个组件都会重新生成并更新，包括共享 Provider 定义和插件的全部 hooks 文件；旧插件中已移除的文件也会清理。在线命令获取最新版本；本地命令安装当前工作区内容，不修改或更新源码。

成功时只显示完成提示和会话启动提示，首次添加 PATH 时额外提醒打开新终端；校验失败时显示详细诊断，并保留已安装版本。

安装位置：

- `~/cc-bin/ccs`、`~/cc-bin/ccp`：两个独立可执行文件，包含所需 Provider 定义。
- `~/.claude/skills/cc-bin-provider/`：插件运行文件，Claude Code 自动加载。

源码可以放在 `~/IdeaProjects/cc-bin` 等任意目录；`~/cc-bin` 用于安装命令，不存放源码仓库。安装结果不依赖源码目录，插件也不需要 `--plugin-dir`。

安装器会在 `~/.zshrc` 缺少以下行时追加，已有则跳过：

```zsh
export PATH="$HOME/cc-bin:$PATH"
```

安装使用普通 Bash，无需 `source`。新增 PATH 后打开一个新终端即可生效；安装或更新插件后新开 Claude Code 会话。

## Provider 配置

```zsh
export ZHIPU_API_KEY="你的 Key"
ccs --list
```

将需要的 Key export 到启动 Claude 的终端环境即可。`ccs`、`ccp` 和选择器共用以下入口，**只根据非空 API Key 判断可用性，忽略 BASE_URL 环境变量**。

| 缩写 | Provider | API Key 环境变量 |
| --- | --- | --- |
| `an` | Anthropic | `ANTHROPIC_API_KEY` |
| `zp` | 智谱 | `ZHIPU_API_KEY` |
| `ds` | DeepSeek | `DEEPSEEK_API_KEY` |
| `mm` | MiniMax | `MINIMAX_API_KEY` |
| `mm-api` | MiniMax（API） | `MINIMAX_PAYGO_API_KEY` |
| `mimo` | MiMo | `MIMO_API_KEY` |
| `mimo-api` | MiMo（API） | `MIMO_PAYGO_API_KEY` |

MiniMax、MiMo 无后缀默认 Coding Plan，按量 API 使用 `-api` 和对应的按量 Key；智谱不拆分套餐/API。Anthropic、DeepSeek 仅提供 API 入口，不支持 OpenAI。MiniMax 默认中国站，MiMo 套餐默认中国集群。只有同一厂商同时提供 Coding Plan 和按量 API 两种入口时，按量入口才标注「（API）」并使用 `-api` 后缀。

## 使用

```sh
ccs mm                  # 全局切换到 MiniMax Coding Plan
ccp mm-api              # 仅本次启动使用 MiniMax API
ccp zp --model opus     # 透传 Claude 参数
ccs --list              # 只读 JSON 列表；ccp --list 同样支持
```

在 fullscreen 中使用选择器：

```sh
claude --settings '{"tui":"fullscreen"}'
# 进入 Claude 后输入 /provider
```

只显示配置了 Key 的选项；方向键选择，Enter 切换，Esc 关闭。详见 [插件说明](cc-bin-plugin/README.md)。

`ccs` 和 `/provider` **整体替换** `~/.claude/settings.json`，上一份保存在 `settings.json.bak`，其他使用全局配置的进程也可能受影响。

`ccp` 每次启动生成权限为 0600 的独立临时配置，退出后清理，不在项目或源码的 `.claude/` 中生成文件。需要不同 Provider 并行运行时使用 `ccp`。通过 `ccp` 或其他 Provider/model 覆盖配置启动时，`/provider` 的全局切换可能无法覆盖本次启动配置。

旧版留下的 `settings-zp.json`、`settings-ds.json`、`settings-mm.json`、`settings-mimo.json` 可在确认没有手动引用或运行中的旧会话后删除；`settings.local.json` 是项目本地配置，应保留。

## 验证

```sh
python3 tests/cli_integration.py
python3 tests/install_integration.py
claude plugin validate --strict --json ./cc-bin-plugin
claude plugin test ./cc-bin-plugin
```

测试使用临时用户目录，覆盖 CLI 切换、并行启动、安装更新、PATH 去重及插件自动加载，不修改真实 `.zshrc` 或全局配置。真实 Provider 请求尚未验收。

## License

MIT
