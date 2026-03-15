# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 提供在此代码库中工作的指导。

## 项目概述

这是一个**可视化键鼠自动化编辑器** - 基于 PyQt5 的节点编辑器，用于创建和执行键盘/鼠标自动化工作流。

## 运行应用

```bash
python main.py
```

## 依赖项

项目需要以下依赖：
- PyQt5
- pyautogui（用于输入模拟）
- opencv-python (cv2)（用于图像匹配）
- numpy

安装命令：
```bash
pip install PyQt5 pyautogui opencv-python numpy
```

## 架构

### 高层结构

应用采用 UI 与执行引擎分离的架构：

```
main.py
├── ui/MainWindow          # 主容器、菜单、工具栏、停靠窗口
│   ├── NodeCanvas         # 节点编辑的图形场景
│   ├── NodeLibraryPanel   # 可拖拽的节点面板
│   ├── PropertiesPanel    # 节点参数编辑器
│   └── LogPanel           # 执行日志输出
└── engine/WorkflowEngine  # 工作流执行引擎
```

### 核心组件

**NodeCanvas** (`ui/node_canvas.py`)：
- 基于 QGraphicsView 的画布，带网格背景
- 处理节点创建、拖拽、选择
- 通过 PortItem 管理节点间的连接（边）
- 支持缩放（鼠标滚轮）、平移（中键拖拽）
- 节点数据结构：`{id, type, title, x, y, params, ports}`
- 连接数据结构：`{from: node_id, to: node_id, from_port: index, to_port: index}`

**WorkflowEngine** (`engine/workflow_engine.py`)：
- 在独立线程中运行工作流
- 发射信号：`execution_started/stopped/paused/resumed`、`node_started/finished`、`execution_error`、`log_message`
- 基于连接顺序执行节点
- 执行期间支持暂停/恢复/停止
- 变量存储，用于节点间数据传递（如 find_image 的 `find_x`、`find_y`）

**节点类型**（定义在 `ui/node_library.py`）：
- **触发**：`start_manual`（手动启动）、`start_hotkey`（热键启动）
- **动作**：`mouse_move`（鼠标移动）、`mouse_click`（鼠标点击）、`key_press`（按键）、`key_input`（键盘输入）、`delay`（延时）
- **图像**：`find_image`（OpenCV 模板匹配）、`find_color`（找色）
- **逻辑**：`condition`（条件判断，2输出端口：是/否）、`loop`（循环，2输出端口：循环/结束）、`break`（跳出循环）、`continue`（继续循环）

### 数据流

1. 用户从 NodeLibraryPanel 拖拽节点到 NodeCanvas
2. 用户从输出端口拖拽到输入端口连接节点
3. 运行（F5）时，MainWindow 通过 `get_workflow_data()` 将画布序列化为 JSON
4. WorkflowEngine 加载数据并按拓扑顺序执行节点
5. 引擎发射信号更新 LogPanel 和 UI 状态

### 关键文件及职责

| 文件 | 职责 |
|------|------|
| `ui/main_window.py` | 菜单、工具栏、停靠窗口管理、文件 I/O（JSON）、引擎信号连接 |
| `ui/node_canvas.py` | 图形项（NodeItem、PortItem、ConnectionItem）、鼠标/键盘事件、撤销/重做（TODO） |
| `ui/node_library.py` | 节点类型定义及参数结构、可搜索的树形控件 |
| `ui/properties_panel.py` | 基于参数类型动态生成表单（string/int/float/select/file/color/region） |
| `ui/screenshot_tool.py` | 全屏截图及区域选择，保存到 `pic/` 文件夹 |
| `ui/image_test_widget.py` | 在后台线程中测试 find_image 功能 |
| `engine/workflow_engine.py` | 节点执行实现、线程管理 |

### 参数类型

属性面板支持以下参数类型：
- `string`：QLineEdit 文本框
- `int`：QSpinBox 整数框（带 min/max）
- `float`：QDoubleSpinBox 浮点数框
- `select`：QComboBox 下拉框
- `boolean`：QCheckBox 复选框
- `file`：文本框 + 浏览按钮（`image_path` 特殊处理，带截图按钮）
- `color`：文本框 + 颜色选择器
- `region`：四个数字框（X、Y、宽度、高度）

### 文件格式

工作流保存为 JSON 格式，结构如下：
```json
{
  "nodes": [
    {
      "id": "uuid",
      "type": "mouse_click",
      "title": "鼠标点击",
      "x": 100,
      "y": 200,
      "params": {
        "button": {"type": "select", "default": "left", "label": "按钮", "value": "right"}
      },
      "ports": {"inputs": 1, "outputs": 1}
    }
  ],
  "connections": [
    {"from": "node_id_1", "to": "node_id_2", "from_port": 0, "to_port": 0}
  ]
}
```

### 图像资源

截图保存到 `pic/` 文件夹。属性面板中的 ScreenshotWidget 提供：
- 现有图片的文件浏览器
- 截图按钮（最小化应用并允许区域选择）
- 多显示器支持

## 常见开发任务

**添加新节点类型：**
1. 在 `ui/node_library.py` 的 `node_types` 字典中添加节点定义
2. 在 `engine/workflow_engine.py` 的 `_execute_node()` 方法中实现执行逻辑
3. 添加动作方法，命名模式为 `_action_<节点类型>()`

**添加新参数类型：**
1. 在 `ui/properties_panel.py` 的 `_create_param_widget()` 中添加处理分支
2. 在 `_get_widget_value()` 中添加值提取逻辑
3. 在 `_collect_param_values()` 中处理新类型

**测试图像匹配：**
- 在画布中选择 find_image 节点
- 属性面板会显示"测试找图"按钮
- 点击测试 - 如果找到图片，鼠标会移动到找到的位置

## 重要注意事项

- 引擎在独立线程中运行 - UI 更新必须使用信号/槽机制
- 撤销/重做功能目前是占位符（NodeCanvas 中有 TODO 注释）
- `pic/` 文件夹在运行时会自动创建，用于保存截图
- 图像匹配使用 OpenCV 模板匹配（TM_CCOEFF_NORMED）
- 图片文件支持中文路径，使用 `np.fromfile()` + `cv2.imdecode()` 读取
- 循环变量使用特殊命名：`$__loop_i__`（从0开始）、`$__loop_i_1__`（从1开始），避免与用户变量冲突
- 条件表达式支持变量引用（如 `$found == True`），通过 AST 检查确保安全性
