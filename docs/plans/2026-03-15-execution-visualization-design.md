# 执行可视化设计文档

**日期**: 2026-03-15
**主题**: 节点执行可视化（方案1：简单高亮）

## 目标

在执行工作流时，在画布上直观显示当前正在执行的节点、执行成功/失败的状态，让用户能够"看到"工作流的执行过程。

## 设计概述

利用引擎已有的信号机制，在画布节点上显示执行状态：
- **正在执行**: 亮蓝色边框 (#2196F3)，宽度 3px
- **执行成功**: 绿色边框 (#4CAF50)，持续 800ms 后恢复
- **执行失败**: 红色边框 (#F44336)，保持直到下次执行或用户点击

## 架构

```
WorkflowEngine (信号发射)
    ├── node_started(node_id, node_type) → NodeCanvas.on_node_started()
    ├── node_finished(node_id, node_type, result) → NodeCanvas.on_node_finished()
    └── execution_error(node_id, error_message) → NodeCanvas.on_node_error()

NodeCanvas (信号接收与分发)
    └── NodeItem.set_execution_state(state)

NodeItem (视觉渲染)
    └── 根据状态更新边框颜色和宽度
```

## 状态定义

| 状态 | 常量 | 边框颜色 | 边框宽度 | 持续时间 |
|------|------|----------|----------|----------|
| 默认 | `STATE_DEFAULT` | #CCCCCC (灰色) 或 #2196F3 (选中时) | 1px 或 2px | 常态 |
| 执行中 | `STATE_RUNNING` | #2196F3 (蓝色) | 3px | 直到节点完成 |
| 成功 | `STATE_SUCCESS` | #4CAF50 (绿色) | 3px | 800ms |
| 失败 | `STATE_ERROR` | #F44336 (红色) | 3px | 持续到重置 |

## 组件修改

### 1. NodeItem (ui/node_canvas.py)

新增方法:
- `set_execution_state(state: str)` - 设置执行状态并更新外观
- `_update_border_color()` - 根据当前状态更新边框

状态优先级: 失败 > 执行中 > 成功 > 默认

### 2. NodeCanvas (ui/node_canvas.py)

新增方法:
- `connect_engine_signals(engine)` - 连接引擎信号
- `on_node_started(node_id, node_type)` - 节点开始执行
- `on_node_finished(node_id, node_type, result)` - 节点执行完成
- `on_node_error(node_id, error_message)` - 节点执行出错
- `clear_execution_highlights()` - 清除所有执行高亮

### 3. MainWindow (ui/main_window.py)

在 `_connect_engine_signals()` 中添加:
```python
self.canvas.connect_engine_signals(self.workflow_engine)
```

## 边界情况处理

1. **节点被删除时正在执行**: 在设置状态前检查节点是否仍存在
2. **快速连续执行**: 确保同一时间只有一个节点显示"执行中"状态
3. **失败状态重置**: 开始新执行或点击画布时清除红色高亮
4. **选中与执行状态共存**: 执行状态的边框宽度更宽(3px vs 2px)，优先显示

## 实现步骤

1. 在 `NodeItem` 中添加状态管理和视觉更新
2. 在 `NodeCanvas` 中添加信号处理逻辑
3. 在 `MainWindow` 中连接信号
4. 测试各种执行场景

## 扩展可能

- 添加脉冲动画效果（使用 QGraphicsItemAnimation 或手动定时器）
- 在节点内显示执行耗时
- 显示执行结果的小图标（如找图成功显示 ✓）
