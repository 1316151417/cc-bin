# cc-bin

> [English](README.md)

<p align="center">
  <img src="display.png" width="50%" />
</p>

两个 ~40 行的 Zsh 脚本，用于切换或隔离 [Claude Code](https://claude.ai/code) 的 LLM 提供商。零依赖，无魔法 — 只有关联数组和 heredoc。

[Anthropic](https://api.anthropic.com)、[智谱](https://open.bigmodel.cn)、[MiniMax](https://minimax.chat)、[DeepSeek](https://deepseek.com)、[Mimo](https://mimoml.com) 都提供 Anthropic 兼容的 API。这两个脚本帮你管理它们。

## 为什么是两个脚本？

官方 `cc-switch` 太重了。`ccs` 做同样的事只要 ~40 行。

运行中切换全局提供商会中断活跃会话，且所有会话共享同一个提供商的并发限制。`ccp` 解决了这个问题 — 每次调用通过 `--settings` 使用独立配置，全局配置不受影响。

## 用法

```bash
# 切换全局提供商
ccs <an|zp|mm|ds|mimo>

# 单次启动（从环境变量读取凭证，不改全局配置）
ccp [an|zp|mm|ds|mimo] [claude options...]
```

## 提供商

| 键 | 提供商 | Sonnet | Opus | Haiku |
|-----|----------|--------|------|-------|
| an  | Anthropic | claude-sonnet-4-6 | claude-opus-4-6 | claude-haiku-4-5 |
| zp  | 智谱    | GLM-5.1 | GLM-5.1 | GLM-4.5-Air |
| mm  | MiniMax  | MiniMax-M2.7 | MiniMax-M2.7 | MiniMax-M2.7 |
| ds  | DeepSeek | deepseek-v4-pro | deepseek-v4-pro | deepseek-v4-flash |
| mimo | Mimo    | mimo-v2.5-pro | mimo-v2.5-pro | mimo-v2.5-pro |

## 安装

```bash
# 1. 克隆
git clone https://github.com/<your-username>/cc-bin.git ~/cc-bin

# 2. 添加到 ~/.zshrc 的 PATH
export PATH="$HOME/cc-bin:$PATH"

# 3. 在 ~/.zshrc 中设置凭证（只填你用到的）
export ANTHROPIC_BASE_URL="https://api.anthropic.com"
export ANTHROPIC_API_KEY="你的密钥"
export DEEPSEEK_BASE_URL="https://api.deepseek.com"
export DEEPSEEK_API_KEY="你的密钥"
# ... 其他同理

source ~/.zshrc
```

API 地址 = `BASE_URL` + `/anthropic`。

## License

MIT
