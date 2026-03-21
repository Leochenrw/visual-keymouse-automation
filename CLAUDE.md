# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**可视化键鼠自动化编辑器** - 基于 PyQt5 的节点编辑器，用于创建和执行键盘/鼠标自动化工作流。

## 运行

```bash
python main.py
pip install PyQt5 pyautogui opencv-python numpy
```

## 架构

UI 与执行引擎完全分离：

```
main.py
├── ui/MainWindow          # 主容器、菜单、工具栏、停靠窗口
│   ├── NodeCanvas         # 节点编辑图形场景（QGraphicsView）
│   ├── NodeLibraryPanel   # 可拖拽节点面板（含搜索）
│   ├── PropertiesPanel    # 节点参数动态表单
│   ├── LogPanel           # 执行日志
│   ├── TutorialTooltip    # 新手引导弹窗（可拖拽，位置持久化）
│   ├── MockDataDialog     # 单节点测试 Mock 数据配置
│   └── BranchSelectDialog # "运行到此处"时的条件分支选择
└── engine/WorkflowEngine  # 工作流执行引擎（独立线程）
    └── ListenerContext    # 异步监听线程（独立监控屏幕）
```

### 关键文件及职责

| 文件 | 职责 |
|------|------|
| `ui/main_window.py` | 菜单、工具栏、文件 I/O（JSON）、引擎信号连接、教程步骤定义 |
| `ui/node_canvas.py` | 图形项（NodeItem、PortItem、ConnectionItem）、鼠标/键盘事件 |
| `ui/node_library.py` | 节点类型定义、参数结构、节点输出变量定义（`NODE_OUTPUTS`）|
| `ui/properties_panel.py` | 参数类型到 Qt 控件的映射、单节点测试入口 |
| `ui/screenshot_tool.py` | 全屏截图及区域选择，保存到 `pic/` |
| `ui/image_test_widget.py` | 后台线程测试 find_image 功能 |
| `ui/mock_data_dialog.py` | Mock 数据配置对话框（用于单节点测试） |
| `ui/branch_select_dialog.py` | 条件分支选择对话框 + `find_conditions_on_path()` 路径分析 |
| `ui/tutorial_tooltip.py` | 新手引导弹窗组件（DotIndicator + TutorialTooltip） |
| `engine/workflow_engine.py` | 节点执行、线程管理、变量存储、测试/调试功能 |

### 节点类型

定义在 `ui/node_library.py` 的 `node_types` 字典，执行逻辑在 `engine/workflow_engine.py` 的 `_action_<type>()` 方法中。

**触发**：`start_manual`、`start_hotkey`、`async_listener`（异步监听，独立线程监控屏幕）

**动作**：`mouse_move`（支持 `$变量` 坐标）、`mouse_click`（支持随机偏移）、`key_press`、`key_input`、`delay`

**图像**：
- `if_image`：集成的找图+条件节点，2个输出端口（找到/未找到），可选自动移动和点击
- `find_color`：找色节点

**逻辑**：`condition`（2输出：是/否）、`loop`（count=0 为无限循环）、`break`、`continue`

### 执行引擎特性

- `WorkflowEngine.test_node(node_id, mock_variables)` - 单节点测试，注入 Mock 变量运行单个节点
- `WorkflowEngine.run_to_node(target_node_id, branch_choices)` - 运行到指定节点（调试用）
- `ListenerContext` - 异步监听线程，触发时可暂停主流程执行子流程（`action_on_main: pause/stop`）
- 变量替换：参数值中的 `$var_name` 在执行时从 `engine.variables` 替换
- 循环变量：`$__loop_i__`（从0）、`$__loop_i_1__`（从1），防止用户变量冲突
- 条件表达式通过 AST 安全解析（非 `eval`）

### 数据流

1. 用户从 NodeLibraryPanel 拖拽节点到 NodeCanvas
2. 从输出端口拖拽到输入端口建立连接
3. F5 运行：MainWindow 调用 `get_workflow_data()` 序列化画布为 JSON
4. WorkflowEngine 加载并按拓扑顺序执行
5. 引擎通过信号更新 UI（线程安全）

### 参数类型

属性面板支持的参数类型（`ui/properties_panel.py`）：

| 类型 | 控件 | 备注 |
|------|------|------|
| `string` | QLineEdit | |
| `int` | QSpinBox | 支持 min/max |
| `float` | QDoubleSpinBox | |
| `select` | QComboBox | options 列表 |
| `boolean` | QCheckBox | |
| `file` | 文本框+浏览 | `image_path` 参数名额外显示截图和测试找图按钮 |
| `color` | 文本框+颜色选择器 | |
| `region` | 4个 QSpinBox | X、Y、宽、高 |

### 文件格式（工作流 JSON）

```json
{
  "nodes": [{"id": "uuid", "type": "mouse_click", "title": "鼠标点击", "x": 100, "y": 200,
              "params": {"button": {"type": "select", "default": "left", "value": "right"}},
              "ports": {"inputs": 1, "outputs": 1}}],
  "connections": [{"from": "node_id_1", "to": "node_id_2", "from_port": 0, "to_port": 0}]
}
```

工作流文件保存在 `scripts/` 目录，截图保存在 `pic/` 目录（运行时自动创建）。

## 常见开发任务

**添加新节点类型：**
1. 在 `ui/node_library.py` 的 `node_types` 字典中添加节点定义（含参数和端口数）
2. 在 `NODE_OUTPUTS` 中添加该节点的输出变量定义（用于 Mock 数据和变量提示）
3. 在 `engine/workflow_engine.py` 的 `_execute_node()` 中添加分发，并实现 `_action_<type>()` 方法

**添加新参数类型：**
1. `ui/properties_panel.py` 的 `_create_param_widget()` 添加处理分支
2. `_get_widget_value()` 添加值提取逻辑

## 重要注意事项

- 引擎在独立线程中运行，UI 更新必须通过信号/槽机制
- 图片文件支持中文路径：使用 `np.fromfile()` + `cv2.imdecode()` 读取
- 图像匹配使用 OpenCV TM_CCOEFF_NORMED 算法
- `async_listener` 节点会启动独立监听线程，工作流停止时需确保监听线程也停止
- 撤销/重做功能目前是占位符（NodeCanvas 中有 TODO）
- 教程步骤定义在 `ui/main_window.py` 的 `TUTORIAL_STEPS` 列表中
