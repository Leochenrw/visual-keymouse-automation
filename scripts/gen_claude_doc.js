const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat, HeadingLevel, BorderStyle,
  WidthType, ShadingType, VerticalAlign, PageNumber, PageBreak
} = require('docx');
const fs = require('fs');

const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };
const headerShading = { fill: "D5E8F0", type: ShadingType.CLEAR };

function h1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 320, after: 160 }, children: [new TextRun(text)] });
}
function h2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120 }, children: [new TextRun(text)] });
}
function h3(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 200, after: 100 }, children: [new TextRun(text)] });
}
function p(text, opts = {}) {
  return new Paragraph({ spacing: { after: 120 }, children: [new TextRun({ text, ...opts })] });
}
function pMixed(runs) {
  return new Paragraph({ spacing: { after: 120 }, children: runs });
}
function code(text) {
  return new Paragraph({
    spacing: { before: 80, after: 80 },
    indent: { left: 360 },
    shading: { fill: "F5F5F5", type: ShadingType.CLEAR },
    children: [new TextRun({ text, font: "Courier New", size: 18, color: "C7254E" })]
  });
}
function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullet-list", level: 0 },
    spacing: { after: 80 },
    children: [new TextRun(text)]
  });
}
function blankLine() {
  return new Paragraph({ children: [new TextRun("")] });
}

function makeTable(headers, rows, colWidths) {
  const total = colWidths.reduce((a, b) => a + b, 0);
  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map((h, i) => new TableCell({
      borders: cellBorders,
      width: { size: colWidths[i], type: WidthType.DXA },
      shading: headerShading,
      verticalAlign: VerticalAlign.CENTER,
      children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: h, bold: true, size: 20 })]
      })]
    }))
  });
  const dataRows = rows.map(row => new TableRow({
    children: row.map((cell, i) => new TableCell({
      borders: cellBorders,
      width: { size: colWidths[i], type: WidthType.DXA },
      children: [new Paragraph({ spacing: { before: 60, after: 60 }, children: [new TextRun({ text: cell, size: 20 })] })]
    }))
  }));
  return new Table({ columnWidths: colWidths, margins: { top: 80, bottom: 80, left: 150, right: 150 }, rows: [headerRow, ...dataRows] });
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, color: "1F4E79", font: "Arial" },
        paragraph: { spacing: { before: 320, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, color: "2E75B6", font: "Arial" },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, color: "404040", font: "Arial" },
        paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 2 } },
    ]
  },
  numbering: {
    config: [
      { reference: "bullet-list",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }
    ]
  },
  sections: [{
    properties: { page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    headers: {
      default: new Header({ children: [new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: "Claude Code 命令手册", color: "666666", size: 18 })]
      })] })
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ text: "第 ", color: "888888", size: 18 }),
          new TextRun({ children: [PageNumber.CURRENT], color: "888888", size: 18 }),
          new TextRun({ text: " 页", color: "888888", size: 18 })
        ]
      })] })
    },
    children: [
      // 标题页
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 1440, after: 480 },
        children: [new TextRun({ text: "Claude Code 命令手册", bold: true, size: 60, color: "1F4E79", font: "Arial" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 240 },
        children: [new TextRun({ text: "新手完整中文参考文档", size: 28, color: "555555" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 120 },
        children: [new TextRun({ text: "适用版本：Claude Code（claude-sonnet-4-6）", size: 20, color: "888888" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 120 },
        children: [new TextRun({ text: "文档生成日期：2026-03-20", size: 20, color: "888888" })]
      }),
      new Paragraph({ children: [new PageBreak()] }),

      // 一、简介
      h1("一、简介"),
      p("Claude Code 是 Anthropic 官方推出的 AI 编程助手 CLI 工具，直接在终端中运行，无需浏览器界面。"),
      blankLine(),
      p("启动方式：", { bold: true }),
      code("claude          # 进入交互式对话模式"),
      code('claude "问题"   # 直接执行一个问题后退出'),
      blankLine(),

      // 二、斜杠命令
      h1("二、斜杠命令（在对话中输入）"),
      p("斜杠命令在交互模式下输入，以 / 开头，直接在对话框中使用。"),
      blankLine(),

      h2("2.1 会话与导航"),
      makeTable(
        ["命令", "作用", "使用场景"],
        [
          ["/help", "显示所有可用命令和快捷键", "忘记命令时查阅"],
          ["/clear", "清空对话历史，重置上下文", "上下文满了，或想重新开始一个独立任务"],
          ["/compact", "压缩对话历史以节省上下文空间", "对话很长但不想完全清空时"],
          ["/resume", "恢复上一次的对话会话", "关闭后重新接上之前的任务"],
          ["/exit 或 /quit", "退出 Claude Code", "结束使用"],
        ],
        [1800, 3000, 4560]
      ),
      blankLine(),
      pMixed([
        new TextRun({ text: "/clear vs /compact 区别：", bold: true }),
      ]),
      bullet("/clear：完全清空历史，相当于全新开始"),
      bullet("/compact：保留摘要，上下文减少但任务连续性更好"),
      blankLine(),

      h2("2.2 记忆与配置"),
      makeTable(
        ["命令", "作用", "使用场景"],
        [
          ["/memory", "查看和编辑 Claude 的记忆文件（CLAUDE.md）", "查看或修改项目说明、用户偏好"],
          ["/config", "查看或修改 Claude Code 配置", "调整模型、权限、行为设置"],
          ["/model", "切换使用的模型（如 opus、sonnet、haiku）", "需要更强能力或更快速度时切换"],
          ["/permissions", "查看当前会话的工具权限", "了解哪些操作被允许/禁止"],
        ],
        [1800, 3000, 4560]
      ),
      blankLine(),
      p("模型速度与能力对比：", { bold: true }),
      bullet("claude-opus-4-6：最强，适合复杂任务，速度较慢"),
      bullet("claude-sonnet-4-6：均衡，日常首选"),
      bullet("claude-haiku-4-5：最快最省，适合简单任务"),
      blankLine(),

      h2("2.3 代码与 Git 工作流"),
      makeTable(
        ["命令", "作用", "使用场景"],
        [
          ["/init", "分析代码库，自动生成 CLAUDE.md 项目文档", "新项目初次使用 Claude Code（只需一次）"],
          ["/commit", "自动生成 commit 信息并提交代码", "写完代码想快速提交时"],
          ["/pr_comments", "获取并显示 GitHub PR 的评论", "Code Review 时查看 PR 反馈"],
        ],
        [1800, 3000, 4560]
      ),
      blankLine(),

      h2("2.4 诊断与账户"),
      makeTable(
        ["命令", "作用", "使用场景"],
        [
          ["/doctor", "检查安装健康状态、依赖、配置", "出现异常时排查问题"],
          ["/status", "显示当前会话状态（模型、上下文、费用）", "监控 token 使用情况"],
          ["/cost", "显示本次会话的 token 用量和预估费用", "费用追踪"],
          ["/login", "登录 Anthropic 账户", "首次使用或重新认证"],
          ["/logout", "登出 Anthropic 账户", "切换账户时"],
          ["/bug", "直接向 Anthropic 提交 Bug 反馈", "遇到 Claude Code 本身的问题"],
          ["/release-notes", "查看最新版本的更新日志", "了解新功能时"],
        ],
        [1800, 3000, 4560]
      ),
      blankLine(),

      h2("2.5 界面与编辑器"),
      makeTable(
        ["命令", "作用", "使用场景"],
        [
          ["/terminal-setup", "配置终端集成（shell hooks、自动补全）", "初次安装时设置终端环境"],
          ["/vim", "切换 vim 键位模式", "习惯 vim 操作的用户"],
          ["/fast", "切换到更快（低延迟）的模式", "速度比质量更重要时"],
        ],
        [1800, 3000, 4560]
      ),
      blankLine(),

      // 三、CLI 启动参数
      new Paragraph({ children: [new PageBreak()] }),
      h1("三、CLI 启动参数"),
      p("在终端启动 claude 时可附加的参数："),
      blankLine(),

      h2("3.1 常用参数"),
      makeTable(
        ["参数", "简写", "作用", "示例"],
        [
          ["--print", "-p", "非交互模式，直接输出结果后退出", 'claude -p "解释这个错误"'],
          ["--model", "-m", "指定使用的模型", "claude --model claude-opus-4-6"],
          ["--continue", "-c", "继续最近一次对话", "claude -c"],
          ["--resume", "", "通过 ID 恢复指定历史会话", "claude --resume abc123"],
          ["--output-format", "", "设置输出格式：text/json/stream-json", "claude -p \"...\" --output-format json"],
          ["--version", "", "显示当前版本号", "claude --version"],
          ["--help", "-h", "显示所有可用参数", "claude --help"],
          ["--verbose", "", "开启详细调试输出", "claude --verbose"],
        ],
        [1800, 900, 2700, 3960]
      ),
      blankLine(),

      h2("3.2 权限与工具控制"),
      makeTable(
        ["参数", "作用"],
        [
          ["--allowedTools", "只允许使用指定工具，如：--allowedTools Bash,Read"],
          ["--disallowedTools", "禁止使用指定工具，如：--disallowedTools Bash"],
          ["--no-tools", "禁用所有工具（纯对话模式）"],
          ["--add-dir", "扩展允许读写的目录范围"],
          ["--dangerously-skip-permissions", "跳过所有权限提示（仅限 CI/沙箱环境！慎用）"],
        ],
        [2880, 6480]
      ),
      blankLine(),

      h2("3.3 高级参数"),
      makeTable(
        ["参数", "作用"],
        [
          ["--max-turns", "限制 AI 自主操作的最大轮数（用于自动化脚本）"],
          ["--system-prompt", "覆盖或追加系统提示词"],
          ["--append-system-prompt", "在系统提示词后追加内容"],
          ["--mcp-config", "指定自定义的 MCP 配置文件路径"],
        ],
        [2880, 6480]
      ),
      blankLine(),

      // 四、键盘快捷键
      new Paragraph({ children: [new PageBreak()] }),
      h1("四、键盘快捷键（交互模式）"),
      blankLine(),

      h2("4.1 输入与编辑"),
      makeTable(
        ["快捷键", "作用"],
        [
          ["Enter", "发送消息"],
          ["Shift + Enter", "换行（输入多行内容）"],
          ["↑ / ↓ 方向键", "浏览历史消息"],
          ["Ctrl + A", "光标移到行首"],
          ["Ctrl + E", "光标移到行尾"],
          ["Ctrl + K", "删除光标到行尾的内容"],
          ["Ctrl + U", "删除整行"],
          ["Ctrl + W", "删除光标前的一个单词"],
          ["Ctrl + L", "清屏（不清空对话历史）"],
        ],
        [2880, 6480]
      ),
      blankLine(),

      h2("4.2 会话控制"),
      makeTable(
        ["快捷键", "作用"],
        [
          ["Ctrl + C", "取消当前输入，或中断正在执行的任务"],
          ["Ctrl + D", "退出 Claude Code"],
          ["Escape", "取消当前输入"],
        ],
        [2880, 6480]
      ),
      blankLine(),

      h2("4.3 执行过程中"),
      makeTable(
        ["快捷键", "作用"],
        [
          ["Ctrl + C", "中断当前 AI 任务（会弹出选项：停止 / 继续）"],
        ],
        [2880, 6480]
      ),
      blankLine(),

      // 五、实用场景示例
      new Paragraph({ children: [new PageBreak()] }),
      h1("五、实用场景示例"),
      blankLine(),

      h2("5.1 非交互模式（脚本/管道）"),
      code("# 直接执行一个问题"),
      code('claude -p "解释 Python 的 GIL 机制"'),
      blankLine(),
      code("# 读取文件内容让 Claude 分析"),
      code('cat error.log | claude -p "分析这个错误日志"'),
      blankLine(),
      code("# JSON 格式输出（便于脚本处理）"),
      code('claude -p "列出这个目录的文件" --output-format json'),
      blankLine(),

      h2("5.2 继续上次对话"),
      code("# 继续最近一次对话"),
      code("claude -c"),
      blankLine(),
      code("# 继续指定 ID 的历史会话"),
      code("claude --resume <session-id>"),
      blankLine(),

      h2("5.3 限制权限运行"),
      code("# 只允许读文件，不允许写"),
      code("claude --allowedTools Read,Glob"),
      blankLine(),
      code("# 不允许执行 Bash 命令"),
      code("claude --disallowedTools Bash"),
      blankLine(),

      h2("5.4 CI/CD 自动化"),
      code("# 在 CI 环境中自动化运行（跳过权限提示）"),
      code('claude -p "运行测试并修复失败的用例" \\'),
      code("  --dangerously-skip-permissions \\"),
      code("  --max-turns 20"),
      blankLine(),

      // 六、CLAUDE.md
      new Paragraph({ children: [new PageBreak()] }),
      h1("六、CLAUDE.md — 项目记忆文件"),
      p("CLAUDE.md 是 Claude Code 的项目说明书，每次对话自动读取，是 Claude 了解项目的核心来源。"),
      blankLine(),
      makeTable(
        ["操作", "命令/方式"],
        [
          ["初次创建", "/init（只需一次）"],
          ["查看/编辑", "/memory 或直接编辑文件"],
          ["存放位置", "项目根目录 CLAUDE.md"],
        ],
        [2880, 6480]
      ),
      blankLine(),
      p("建议写入的内容：", { bold: true }),
      bullet("项目概述和技术栈"),
      bullet("常用命令（运行/测试/构建）"),
      bullet("代码规范和约定"),
      bullet("重要注意事项（如线程安全、特殊路径等）"),
      blankLine(),

      // 七、自定义斜杠命令
      h1("七、自定义斜杠命令"),
      p("你可以在 .claude/commands/ 目录下创建自己的斜杠命令，文件内容即为命令执行时的提示词："),
      blankLine(),
      code(".claude/"),
      code("└── commands/"),
      code("    ├── my-command.md    # 对应 /my-command"),
      code("    └── deploy.md        # 对应 /deploy"),
      blankLine(),

      // 八、快速参考卡
      new Paragraph({ children: [new PageBreak()] }),
      h1("八、快速参考卡"),
      blankLine(),
      h2("常用命令速查"),
      makeTable(
        ["命令", "作用"],
        [
          ["/help", "查看帮助"],
          ["/clear", "清空对话"],
          ["/compact", "压缩对话"],
          ["/init", "初始化项目文档"],
          ["/commit", "自动提交代码"],
          ["/status", "查看状态和费用"],
          ["/doctor", "诊断问题"],
          ["/model", "切换模型"],
          ["/memory", "查看记忆文件"],
        ],
        [2880, 6480]
      ),
      blankLine(),
      h2("键盘快捷键速查"),
      makeTable(
        ["快捷键", "作用"],
        [
          ["Ctrl + C", "中断/取消"],
          ["Ctrl + D", "退出"],
          ["Shift + Enter", "换行输入"],
          ["↑↓ 方向键", "浏览历史"],
          ["Ctrl + L", "清屏"],
        ],
        [2880, 6480]
      ),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("Claude_Code_命令手册.docx", buffer);
  console.log("文档已生成：Claude_Code_命令手册.docx");
});
