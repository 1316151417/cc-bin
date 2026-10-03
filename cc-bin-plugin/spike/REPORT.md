# Claude Code 2.1.288 Provider Spike

> 历史记录：本报告针对最初的“仅 Session、禁止修改全局配置”要求。当前 MVP 已按新需求改为调用 `ccs` 修改全局 settings.json，见根目录 README；下面的停止结论不适用于当前实现。

研究日期：2026-10-03（Asia/Shanghai）。

## 结论与决策

**Claude Code 2.1.288 当前 Mod API 不支持满足本项目约束的 session 内动态 Provider 切换。选择方案 C，停止核心实现。**

可以改写下一次模型请求的 `model`，可以保存插件的 Session 状态，也可以使用官方 UI 注册命令和绘制选择器。但是没有原生 Session Provider setter，也没有对引擎原有请求开放 `baseURL` / `apiKey` 覆盖的入口。

`$.env.set()` 是实际存在的 API，但它直接修改 Claude 宿主进程的 `process.env`，后续 Bash、MCP 和其他子进程会继承。独立操作系统进程的环境写入通常不会影响其父进程或兄弟进程；然而这里的写入确实越过插件自己的运行环境，作用于宿主进程，不能保证所要求的“只存在于当前 Session，结束即销毁”的 Provider 生命周期。将其包装成 Session Provider API 不符合本项目要求。本 Spike 没有执行该环境写入。

也不能据此断言所有 Provider 都被固定在引擎启动时。安装版本的环境 getter 会重新读取 `process.env`，Anthropic 客户端构造会使用环境中的 base URL。阻碍是**已公开的 API 作用域和请求覆盖能力**，不是一个未经验证的“启动时固定”假设。

## 证据身份

| 项目 | 核对对象 |
| --- | --- |
| 本地 CLI | `~/.local/bin/claude` → `~/.local/share/claude/versions/2.1.288` |
| `claude --version --verbose` | `2.1.288`；commit `17fe1eb736e5b1433d6ca86a1db334cec8520450` |
| 本地二进制 SHA-256 | `bbe93063f7a0879a1021b2891e5c9354e5b3b98433e32efe6750f7710afed750` |
| 当前版本的类型来源 | 实际加载临时 Mod 后，引擎自动生成 `.claude-plugin/types/claude-code/index.d.ts`；首行明确为 `Written by Claude Code 2.1.288` |
| 官方示例仓库 | `anthropics/claude-code`，核对时 commit `1c229fcd1e1e4e452e29a8f116b45fe4cfe2c528` |

官方仓库当时的公共 `mods/types/claude-code.d.ts` 标注 **2.1.277**，不能冒充 2.1.288 的类型。报告中的能力判断使用本地 2.1.288 生成类型和实际请求；官方示例用于核对注册方式和 UI 使用方式。

本地精确证据：

- [types.txt](evidence/types.txt)：引擎生成类型的原始行号与完整文件哈希。
- [runtime.txt](evidence/runtime.txt)：安装二进制中短源码摘录及原始字节偏移。压缩符号仅用于审计，插件没有调用这些内部函数。
- [results.json](evidence/results.json)：实际 Claude 请求和 hook 计数，不保存凭证值、请求正文、系统提示或用户配置内容。

工作目录中已有的完整 [2.1.288 类型快照](evidence/claude-code-2.1.288.d.ts)、[另一份请求探针结果](evidence/request-probe.json) 和 [带标题的源码摘录](evidence/runtime-excerpts.md) 也予以保留；本报告的复现入口是 `run.py`，其直接产出为上述 `results.json` 与 `types.txt`。

## API 能力逐项核对

### Session、Provider 与状态

2.1.288 的 `EngineInterface.session` 提供 `model()`、会话读取、发送、追加、压缩等方法；没有 Provider setter，也没有模型 setter。`session.model()` 的实现最终读取已绑定会话的 model。

`EngineInterface.state` 提供 Session 内的插件状态，支持版本和条件写入。它保存的是插件命名空间中的数据，不是引擎请求的 Provider 配置。`provider: Origin` 等类型字段表示插件／引擎事件的定义者，不是 DeepSeek、GLM 等 LLM 服务的连接信息。

依据：生成类型原始 2530–2711、3169–3214 行，以及二进制操作／事件表和 `session.model` 实现。

### LLM 请求 hook

**真实入口是 `turn.step`。** 它在一个 turn 内的每次模型请求发送前执行，底层发送请求。公开输入为：

```ts
type TurnStepInput = {
  turnId: string;
  index: number;
  model: string;
  effort?: 'low' | 'medium' | 'high' | 'xhigh' | 'max' | number;
  messageCount: number;
  agentId?: string;
};
```

其中 `model`、`effort` 可改写，其余字段受保护。这里没有 URL、凭证、请求级环境或完整已解析的请求体。

安装引擎把 hook 输入转回模型调用选项时，只取改写后的 `model`、`effort`；其余选项从原模型调用保留。额外注入 `baseURL` / `apiKey` 即使通过插件验证器，也不会被该发送逻辑采用。真实请求已验证这一点。

模型改写仍受组织模型允许策略约束；继续被截断的 thinking 等特殊路径可能保留原模型。因此也不能把一次普通请求成功改写 model 表述为所有请求路径均无条件可改写。

`model.complete`、`model.classify`、`model.fork` 是插件主动发起辅助模型调用的 API。`model.complete` 使用会话自己的客户端与凭证，并非所有主对话请求都会经过这个 hook。

`http.fetch` 是插件的 HTTP API 调用入口，主对话引擎的 Anthropic 客户端使用自己的 fetch 链。在主对话实际请求中，该 hook 计数为 0。

依据：生成类型原始 2383–2415、5788–5845、12618–12668 行；`runtime.txt` 中 step → options、客户端构造和辅助调用实现；`results.json`。

### Prompt / request 生命周期

`prompt.submit` 处理提交的提示；`turn.start` 标记 turn 开始；`prompt.context`、`prompt.compose` 处理上下文与系统提示。`PromptComposeInput.model` 明确为 pinned，仅用于知道提示为哪个模型生成。

`turn.step` 是请求级发送入口；`turn.complete` 是 turn 结束。改写提示内容、系统提示或返回流不等于改变该请求的客户端和凭证。

Streaming hook 可以不调用 `next`，而自行返回模型响应。这表示插件接管响应生成，不表示可以把原引擎的完整请求交给另一套客户端。输入没有完整的 system/tools/request body；重新实现请求构造、流转换、缓存、重试等行为超出这个极小 MVP，也不能作为已存在的原生 Provider 覆盖 API。

### Environment 动态覆盖

`env.get` / `env.set` hook 拦截插件对这两个 API 的调用。引擎读 `process.env` 或自身环境 getter 时，不自动经过插件的 `env.get`。

实际尝试 hook `ANTHROPIC_BASE_URL` 和 `ANTHROPIC_API_KEY`，在主对话请求过程中计数都是 0。原客户端仍使用初始 URL 和占位 key。

`env.set` 的本地实现直接为 `process.env[e.name] = e.value`，而非 Session 内 overlay。没有公开 API 用来把整组 Provider URL、凭证、模型别名作为请求级原子事务提交。临时设置再恢复仍有同进程请求／子进程继承的作用域问题，不提供本项目需要的隔离保证。

### 内置 `/model`

本地命令实现会检查模型可用性，经过 `PreModelSwitch` 决策，再更新 main loop 模型。模型应用 helper 在需要持久化时调用 `bat`；`bat` 对 `userSettings` 写入 `model`。

本地 inline `/model` 命令把 `!isNonInteractiveSession` 传作持久化参数：交互场景会尝试保存新会话默认值，headless 路径可以仅影响当前会话。因此不能直接调用交互 `/model` 并假定 settings.json 一定不会被修改；本 Spike 没有运行 `/model`。

该实现也没有提供 Base URL 或凭证切换 API。MVP 若只需要模型改写，可以使用 `turn.step`；这仍无法完成 Provider 切换。

## 官方 Mods 阅读依据

均固定到核对时的官方 commit，便于后续审计：

- [mods/README.md](https://github.com/anthropics/claude-code/blob/1c229fcd1e1e4e452e29a8f116b45fe4cfe2c528/mods/README.md)：`register(on, options)` 和 function hook 的整体机制、测试方式、early access 边界。
- [mods/diff/hooks/hooks.json](https://github.com/anthropics/claude-code/blob/1c229fcd1e1e4e452e29a8f116b45fe4cfe2c528/mods/diff/hooks/hooks.json)：`modules` 如何声明 hooks 模块。
- [mods/diff/hooks/register.ts](https://github.com/anthropics/claude-code/blob/1c229fcd1e1e4e452e29a8f116b45fe4cfe2c528/mods/diff/hooks/register.ts)：`session.start` 注册命令，`command.run` 处理命令，`ui.open` / `ui.render` 使用官方 pane API，fullscreen 从命令 presentation 获取。
- [mods/agents-md/hooks/register.ts](https://github.com/anthropics/claude-code/blob/1c229fcd1e1e4e452e29a8f116b45fe4cfe2c528/mods/agents-md/hooks/register.ts)：`prompt.context` 与 `tool.call` 的 middleware 使用，不是 LLM transport 拦截。

本地 2.1.288 类型还确认 terminal 的 `$.ui.resolve(e)` 提供 `Select`，选项与 `onSelect` 由引擎处理键盘事件。Picker 可以用官方 UI 做，但本阶段没有实现，以免形成无法真正切 Provider 的产品原型。

## 真实引擎实验

运行：

```sh
python3 spike/run.py
```

实验不是 mock 一个想象中的 Mod API。脚本启动实际安装的 Claude Code，加载真实 Mod，让其主对话发送到本地 Anthropic 兼容 Mock API。

过程：初始客户端指向 A、初始 model 为 `spike-initial-model`；hook 改写 model 为 `spike-rewritten-model` 并额外注入 B 的 URL、替换占位 key。同时计数 `env.get`、`http.fetch`、`model.complete`、`turn.step`。

| 实际观测 | 结果 |
| --- | --- |
| 插件验证／真实加载 | 成功；生成 2.1.288 类型 |
| Claude 请求结果 | `SPIKE_OK`，退出码 0 |
| A 收到主对话请求 | 1 次，`/v1/messages?beta=true` |
| A 收到的 model | `spike-rewritten-model` |
| A 使用初始占位 key | 是 |
| A 使用替换占位 key | 否 |
| B 收到请求 | 0 次 |
| `turn.step` hook | 1 次 |
| `env.get` / `http.fetch` / `model.complete` hook | 均 0 次 |
| 原 settings.json 内容和 mtime | 未改变 |

配置安全检查记录于 `results.json`。原 settings.json 只读取用于计算哈希，不输出其内容；测试凭证为硬编码的无效占位字符串，真实 API Key 未进入代码、日志或 UI。

## 验收边界与后续触发条件

这次完成的是 **Spike**，实验是 headless 主对话的真实引擎请求。fullscreen UI API 已阅读，但 fullscreen Picker、DeepSeek → GLM 连续切换、并行 Session A/B 的真实 Provider 切换均未验收。没有核心实现，因此没有可运行的 Provider MVP、配置发现和配置错误处理流程，也没有虚假的切换成功提示。

没有改变 `cc-bin`；其 `ccp` 的启动时独立配置方案不能证明运行中的 Mod 切换能力。

只有后续版本明确提供 Session Provider 原子 setter，或者发送原请求前开放请求级 URL／凭证覆盖，才重新开展 MVP。届时再实现 Provider 文件发现、官方 `Select` Picker、Session 状态、原子失败恢复，并执行用户要求的单／多 Session 实际 Provider 验收。
