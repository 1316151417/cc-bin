# cc-bin

> [English](README.md)

一个轻量级的 Claude Code 提供商管理工具 — 两个简短的 Zsh 脚本，让你轻松切换或隔离不同的 LLM 提供商。

使用 [Claude Code](https://claude.ai/code) 时，你并不局限于 Anthropic 的模型。**Anthropic**、**智谱（GLM）**、**MiniMax**、**DeepSeek**、**Mimo** 等提供商都提供了 Anthropic 兼容的 API。这个项目用两个简单的脚本帮你管理这些提供商。

## 脚本

### `ccs` — 全局切换提供商

通过更新 `~/.claude/settings.json`，将 Claude Code 永久切换到指定的提供商。

```bash
ccs <an|zp|mm|ds|mimo>
```

**做了什么：**
- 备份现有的 `settings.json` 为 `settings.json.bak`
- 写入新的 settings 文件，包含所选提供商的 API 地址、密钥和模型映射
- 后续所有 `claude` 调用都将使用该提供商

### `ccp` — 单次调用指定提供商（会话隔离）

通过环境变量读取凭证，使用指定提供商启动一次 `claude`，**不修改**全局配置。如果不指定提供商，则默认使用 `~/.claude/settings.json`。

```bash
ccp [an|zp|mm|ds|mimo] [claude options...]
```

**做了什么：**
- 指定提供商时，从环境变量读取 `<PREFIX>_BASE_URL` 和 `<PREFIX>_API_KEY`，写入临时 settings 文件 `.claude/settings-<provider>.json`，并以 `--settings` 参数启动 `claude`
- 不指定提供商时，直接透传参数给 `claude`，使用默认的 `~/.claude/settings.json`
- 两种情况下全局配置均保持不变 — 其他会话不受任何影响

## 解决了什么问题？

### 1. `ccs` — 比 `cc-switch` 更轻量的替代方案

官方的 `cc-switch` 实现较重。`ccs` 只有 **~40 行 Zsh 脚本**，只做一件事：把正确的提供商配置写入 `settings.json`。零依赖、零复杂度 — 仅用 bash/zsh 关联数组和 heredoc 完成。

### 2. `ccp` — 利用 `--settings` 实现会话隔离

直接切换全局提供商会中断正在运行的 Claude Code 会话，并且所有会话会共享同一个提供商的并发限制。

`ccp` 利用 Claude Code 的 `--settings` 标记来解决这些问题：
- 全局提供商配置不受影响 — 已有会话不会被打断
- 每个会话可以使用不同的提供商，绕过单一提供商的并发限制
- 整个实现同样是 **~40 行 Zsh 脚本**

## 提供商与模型映射

| 键  | 提供商   | Sonnet | Opus | Haiku |
|-----|---------|--------|------|-------|
| an  | Anthropic | claude-sonnet-4-6 | claude-opus-4-6 | claude-haiku-4-5 |
| zp  | 智谱     | GLM-5.1 | GLM-5.1 | GLM-4.5-Air |
| mm  | MiniMax | MiniMax-M2.7 | MiniMax-M2.7 | MiniMax-M2.7 |
| ds  | DeepSeek | deepseek-v4-pro | deepseek-v4-pro | deepseek-v4-flash |
| mimo | Mimo   | mimo-v2.5-pro | mimo-v2.5-pro | mimo-v2.5-pro |

## 环境变量

两个脚本都从环境变量读取凭证：

```bash
export ANTHROPIC_BASE_URL="https://api.anthropic.com"
export ANTHROPIC_API_KEY="你的密钥"

export ZHIPU_BASE_URL="https://open.bigmodel.cn/api/paas/v4"
export ZHIPU_API_KEY="你的密钥"

export MINIMAX_BASE_URL="https://api.minimax.chat/v1"
export MINIMAX_API_KEY="你的密钥"

export DEEPSEEK_BASE_URL="https://api.deepseek.com"
export DEEPSEEK_API_KEY="你的密钥"

export MIMO_BASE_URL="https://api.mimoml.com"
export MIMO_API_KEY="你的密钥"
```

API 地址由 BASE_URL 拼接 `/anthropic` 组成。

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/<your-username>/cc-bin.git ~/cc-bin
```

### 2. 添加到 PATH

在 `~/.zshrc` 中添加这一行：

```bash
export PATH="$HOME/cc-bin:$PATH"
```

然后重新加载：

```bash
source ~/.zshrc
```

### 3. 设置凭证

将你的提供商凭证添加到 `~/.zshrc`（或你使用的 shell 配置文件）：

```bash
export DEEPSEEK_BASE_URL="https://api.deepseek.com"
export DEEPSEEK_API_KEY="sk-..."
# ... 其他提供商同理
```

### 4. 试一试

```bash
# 全局切换到 DeepSeek
ccs ds

# 或者单次使用 MiniMax 启动一个会话
ccp mm
```

## License

MIT
