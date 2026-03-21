# Claude Code 命令手册

> 适合新手的完整中文参考文档

---

## 一、简介

**Claude Code** 是 Anthropic 官方推出的 AI 编程助手 CLI 工具，直接在终端中运行。

**启动方式：**
```bash
claude          # 进入交互式对话模式
claude "问题"   # 直接执行一个问题后退出
```

---

## 二、斜杠命令（在对话中输入）

斜杠命令在交互模式下输入，以 `/` 开头。

### 2.1 会话与导航

| 命令 | 作用 | 使用场景 |
|------|------|----------|
| `/help` | 显示所有可用命令和快捷键 | 忘记命令时查阅 |
| `/clear` | 清空对话历史，重置上下文 | 上下文满了，或想重新开始一个独立任务 |
| `/compact` | 压缩对话历史以节省上下文空间 | 对话很长但不想完全清空时 |
| `/resume` | 恢复上一次的对话会话 | 关闭后重新接上之前的任务 |
| `/exit` 或 `/quit` | 退出 Claude Code | 结束使用 |

> **`/clear` vs `/compact` 区别：**
> - `/clear`：完全清空历史，相当于全新开始
> - `/compact`：保留摘要，上下文减少但任务连续性更好

---

### 2.2 记忆与配置

| 命令 | 作用 | 使用场景 |
|------|------|----------|
| `/memory` | 查看和编辑 Claude 的记忆文件（CLAUDE.md） | 查看或修改项目说明、用户偏好 |
| `/config` | 查看或修改 Claude Code 配置 | 调整模型、权限、行为设置 |
| `/model` | 切换使用的模型（如 opus、sonnet、haiku） | 需要更强能力或更快速度时切换 |
| `/permissions` | 查看当前会话的工具权限 | 了解哪些操作被允许/禁止 |

> **模型速度与能力对比：**
> - `claude-opus-4-6`：最强，适合复杂任务
> - `claude-sonnet-4-6`：均衡，日常首选
> - `claude-haiku-4-5`：最快最省，适合简单任务

---

### 2.3 代码与 Git 工作流

| 命令 | 作用 | 使用场景 |
|------|------|----------|
| `/init` | 分析代码库，自动生成 `CLAUDE.md` 项目文档 | 新项目初次使用 Claude Code 时（只需执行一次） |
| `/commit` | 自动生成 commit 信息并提交代码 | 写完代码想快速提交时 |
| `/pr_comments` | 获取并显示 GitHub PR 的评论 | Code Review 时查看 PR 反馈 |

---

### 2.4 诊断与账户

| 命令 | 作用 | 使用场景 |
|------|------|----------|
| `/doctor` | 检查安装健康状态、依赖、配置 | 出现异常时排查问题 |
| `/status` | 显示当前会话状态（模型、上下文用量、费用） | 监控 token 使用情况 |
| `/cost` | 显示本次会话的 token 用量和预估费用 | 费用追踪 |
| `/login` | 登录 Anthropic 账户 | 首次使用或重新认证 |
| `/logout` | 登出 Anthropic 账户 | 切换账户时 |
| `/bug` | 直接向 Anthropic 提交 Bug 反馈 | 遇到 Claude Code 本身的问题 |
| `/release-notes` | 查看最新版本的更新日志 | 了解新功能时 |

---

### 2.5 界面与编辑器

| 命令 | 作用 | 使用场景 |
|------|------|----------|
| `/terminal-setup` | 配置终端集成（shell hooks、自动补全） | 初次安装时设置终端环境 |
| `/vim` | 切换 vim 键位模式 | 习惯 vim 操作的用户 |
| `/fast` | 切换到更快（低延迟）的模式 | 速度比质量更重要时 |

---

## 三、CLI 启动参数

在终端启动 `claude` 时可附加的参数：

### 3.1 常用参数

| 参数 | 简写 | 作用 | 示例 |
|------|------|------|------|
| `--print` | `-p` | 非交互模式，直接输出结果后退出 | `claude -p "解释这个错误"` |
| `--model` | `-m` | 指定使用的模型 | `claude --model claude-opus-4-6` |
| `--continue` | `-c` | 继续最近一次对话 | `claude -c` |
| `--resume` | | 通过 ID 恢复指定的历史会话 | `claude --resume abc123` |
| `--output-format` | | 设置输出格式：`text`/`json`/`stream-json` | `claude -p "..." --output-format json` |
| `--version` | | 显示当前版本号 | `claude --version` |
| `--help` | `-h` | 显示所有可用参数 | `claude --help` |
| `--verbose` | | 开启详细调试输出 | `claude --verbose` |

### 3.2 权限与工具控制

| 参数 | 作用 | 示例 |
|------|------|------|
| `--allowedTools` | 只允许使用指定工具 | `--allowedTools Bash,Read` |
| `--disallowedTools` | 禁止使用指定工具 | `--disallowedTools Bash` |
| `--no-tools` | 禁用所有工具（纯对话模式） | `claude --no-tools` |
| `--add-dir` | 扩展允许读写的目录范围 | `--add-dir /home/user/data` |
| `--dangerously-skip-permissions` | 跳过所有权限提示（仅限 CI/沙箱环境！） | 慎用 |

### 3.3 高级参数

| 参数 | 作用 |
|------|------|
| `--max-turns` | 限制 AI 自主操作的最大轮数（用于自动化脚本） |
| `--system-prompt` | 覆盖或追加系统提示词 |
| `--append-system-prompt` | 在系统提示词后追加内容 |
| `--mcp-config` | 指定自定义的 MCP 配置文件路径 |

---

## 四、键盘快捷键（交互模式）

### 4.1 输入与编辑

| 快捷键 | 作用 |
|--------|------|
| `Enter` | 发送消息 |
| `Shift + Enter` | 换行（输入多行内容） |
| `↑ / ↓` 方向键 | 浏览历史消息 |
| `Ctrl + A` | 光标移到行首 |
| `Ctrl + E` | 光标移到行尾 |
| `Ctrl + K` | 删除光标到行尾的内容 |
| `Ctrl + U` | 删除整行 |
| `Ctrl + W` | 删除光标前的一个单词 |
| `Ctrl + L` | 清屏（不清空对话历史） |

### 4.2 会话控制

| 快捷键 | 作用 |
|--------|------|
| `Ctrl + C` | 取消当前输入，或中断正在执行的任务 |
| `Ctrl + D` | 退出 Claude Code |
| `Escape` | 取消当前输入 |

### 4.3 执行过程中

| 快捷键 | 作用 |
|--------|------|
| `Ctrl + C` | 中断当前 AI 任务（会弹出选项：停止/继续） |

---

## 五、实用场景示例

### 5.1 非交互模式（脚本/管道）

```bash
# 直接执行一个问题
claude -p "解释 Python 的 GIL 机制"

# 读取文件内容让 Claude 分析
cat error.log | claude -p "分析这个错误日志"

# JSON 格式输出（便于脚本处理）
claude -p "列出这个目录的文件" --output-format json

# 修复代码后自动退出
claude -p "修复 main.py 中的语法错误"
```

### 5.2 继续上次对话

```bash
# 继续最近一次对话
claude -c

# 继续指定 ID 的历史会话
claude --resume <session-id>
```

### 5.3 限制权限运行

```bash
# 只允许读文件，不允许写
claude --allowedTools Read,Glob

# 不允许执行 Bash 命令
claude --disallowedTools Bash
```

### 5.4 CI/CD 自动化

```bash
# 在 CI 环境中自动化运行（跳过权限提示）
claude -p "运行测试并修复失败的用例" \
  --dangerously-skip-permissions \
  --max-turns 20
```

---

## 六、CLAUDE.md — 项目记忆文件

`CLAUDE.md` 是 Claude Code 的**项目说明书**，每次对话自动读取。

| 操作 | 命令/方式 |
|------|-----------|
| 初次创建 | `/init`（只需一次） |
| 查看/编辑 | `/memory` 或直接编辑文件 |
| 存放位置 | 项目根目录 `CLAUDE.md` |

**建议写入的内容：**
- 项目概述和技术栈
- 常用命令（运行/测试/构建）
- 代码规范和约定
- 重要注意事项

---

## 七、自定义斜杠命令

你可以在 `.claude/commands/` 目录下创建自己的斜杠命令：

```
.claude/
└── commands/
    ├── my-command.md    # 对应 /my-command
    └── deploy.md        # 对应 /deploy
```

文件内容即为命令执行时的提示词。

---

## 八、快速参考卡

```
常用命令速查：
  /help          查看帮助
  /clear         清空对话
  /compact       压缩对话
  /init          初始化项目文档
  /commit        自动提交代码
  /status        查看状态和费用
  /doctor        诊断问题
  /model         切换模型
  /memory        查看记忆文件

键盘快捷键：
  Ctrl+C         中断/取消
  Ctrl+D         退出
  Shift+Enter    换行输入
  ↑↓ 方向键      浏览历史
```

---

*文档生成日期：2026-03-20*
*适用版本：Claude Code（claude-sonnet-4-6）*
