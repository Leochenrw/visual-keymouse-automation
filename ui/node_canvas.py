"""
节点画布 - 核心编辑区域，显示和操作节点图
"""
from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem,
    QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsTextItem,
    QMenu, QAction, QInputDialog, QMessageBox, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QRectF, QPointF, QLineF
from PyQt5.QtGui import QColor, QPen, QBrush, QFont, QPainterPath, QTransform, QKeyEvent
import json
import uuid


class PortItem(QGraphicsEllipseItem):
    """端口图形项"""

    def __init__(self, x, y, radius, is_input, parent_node=None, port_index=0):
        super().__init__(x - radius, y - radius, radius * 2, radius * 2)
        if parent_node:
            self.setParentItem(parent_node)
        self.is_input = is_input
        self.parent_node = parent_node
        self.radius = radius
        self.port_index = port_index
        self.connections = []  # 支持多连接
        self.connection = None  # 兼容旧代码

        # 设置样式
        self.setBrush(QBrush(QColor("#FFFFFF")))
        self.setPen(QPen(QColor("#333333"), 2))
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor("#2196F3")))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(QColor("#FFFFFF")))
        super().hoverLeaveEvent(event)


class NodeItem(QGraphicsRectItem):
    """节点图形项"""

    def __init__(self, node_id, node_type, title, color, params, x=0, y=0, ports_config=None):
        super().__init__(0, 0, 160, 80)

        self.node_id = node_id
        self.node_type = node_type
        self.title = title
        self.params = params
        self.header_color = QColor(color)
        self.ports_config = ports_config or {"inputs": 1, "outputs": 1}

        # 根据端口数量调整高度
        max_ports = max(self.ports_config.get("inputs", 1), self.ports_config.get("outputs", 1))
        if max_ports > 1:
            new_height = 60 + max_ports * 25
            self.setRect(0, 0, 160, new_height)

        # 设置位置
        self.setPos(x, y)

        # 设置可选项和可移动
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        # 设置外观
        self.setBrush(QBrush(QColor("#F5F5F5")))
        self.setPen(QPen(QColor("#CCCCCC"), 1))
        self.setAcceptHoverEvents(True)

        # 创建内部组件
        self._create_header()
        self._create_ports()

        # 执行状态
        self.execution_state = 'default'  # default, running, success, error
        self._default_pen = QPen(QColor("#CCCCCC"), 1)
        self._selected_pen = QPen(QColor("#2196F3"), 2)
        self._running_pen = QPen(QColor("#2196F3"), 3)
        self._success_pen = QPen(QColor("#4CAF50"), 3)
        self._error_pen = QPen(QColor("#F44336"), 3)

        # 成功状态恢复定时器
        self._success_timer = None

    def set_execution_state(self, state):
        """设置执行状态: default, running, success, error"""
        self.execution_state = state

        # 取消之前的成功状态定时器
        if self._success_timer:
            self._success_timer.stop()
            self._success_timer = None

        if state == 'running':
            self.setPen(self._running_pen)
        elif state == 'success':
            self.setPen(self._success_pen)
            # 800ms后恢复默认状态
            from PyQt5.QtCore import QTimer
            self._success_timer = QTimer()
            self._success_timer.singleShot(800, lambda: self.set_execution_state('default'))
        elif state == 'error':
            self.setPen(self._error_pen)
        else:  # default
            if self.isSelected():
                self.setPen(self._selected_pen)
            else:
                self.setPen(self._default_pen)

    def set_title(self, new_title):
        """设置节点标题"""
        self.title = new_title
        self.title_text.setPlainText(new_title)

    def _update_border_for_selection(self):
        """根据选中状态更新边框（考虑执行状态优先级）"""
        if self.execution_state == 'default':
            if self.isSelected():
                self.setPen(self._selected_pen)
            else:
                self.setPen(self._default_pen)

    def _create_header(self):
        """创建节点头部"""
        header_height = 28

        # 头部背景
        self.header = QGraphicsRectItem(0, 0, self.rect().width(), header_height)
        self.header.setParentItem(self)
        self.header.setBrush(QBrush(self.header_color))
        self.header.setPen(QPen(Qt.NoPen))

        # 标题文字
        self.title_text = QGraphicsTextItem()
        self.title_text.setParentItem(self)
        self.title_text.setPlainText(self.title)
        self.title_text.setDefaultTextColor(Qt.white)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.title_text.setFont(font)
        self.title_text.setPos(8, 4)

    def _create_ports(self):
        """创建端口"""
        port_radius = 6
        header_height = 28
        body_start = header_height + 10
        body_height = self.rect().height() - header_height - 20

        # 输入端口
        self.input_ports = []
        num_inputs = self.ports_config.get("inputs", 1)
        if num_inputs == 1:
            port_y = self.rect().height() / 2
            port = PortItem(0, port_y, port_radius, True, parent_node=self, port_index=0)
            port.setParentItem(self)
            self.input_ports.append(port)
            self.input_port = port  # 兼容旧代码
        else:
            for i in range(num_inputs):
                port_y = body_start + (body_height / num_inputs) * (i + 0.5)
                port = PortItem(0, port_y, port_radius, True, parent_node=self, port_index=i)
                port.setParentItem(self)
                self.input_ports.append(port)
            self.input_port = self.input_ports[0] if self.input_ports else None

        # 输出端口
        self.output_ports = []
        num_outputs = self.ports_config.get("outputs", 1)
        if num_outputs == 1:
            port_y = self.rect().height() / 2
            port = PortItem(self.rect().width(), port_y, port_radius, False, parent_node=self, port_index=0)
            port.setParentItem(self)
            self.output_ports.append(port)
            self.output_port = port  # 兼容旧代码
        else:
            # 根据节点类型设置标签
            labels = []
            if self.node_type == "condition":
                labels = ["是", "否"]
            elif self.node_type == "loop":
                labels = ["循环", "结束"]
            elif self.node_type == "if_image":
                labels = ["找到", "未找到"]
            elif self.node_type == "async_listener":
                labels = ["触发后"]

            for i in range(num_outputs):
                port_y = body_start + (body_height / num_outputs) * (i + 0.5)
                port = PortItem(self.rect().width(), port_y, port_radius, False, parent_node=self, port_index=i)
                port.setParentItem(self)
                self.output_ports.append(port)

                # 添加端口标签
                if i < len(labels):
                    label = QGraphicsTextItem()
                    label.setParentItem(self)
                    label.setPlainText(labels[i])
                    label.setDefaultTextColor(QColor("#666666"))
                    font = QFont()
                    font.setPointSize(8)
                    label.setFont(font)
                    label.setPos(self.rect().width() - 35, port_y - 10)

            self.output_port = self.output_ports[0] if self.output_ports else None

    def hoverEnterEvent(self, event):
        # 只有在默认状态下才显示悬停效果
        if self.execution_state == 'default' and not self.isSelected():
            self.setPen(QPen(QColor("#2196F3"), 2))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        # 只有在默认状态下才恢复边框
        if self.execution_state == 'default':
            if self.isSelected():
                self.setPen(self._selected_pen)
            else:
                self.setPen(self._default_pen)
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            # 只有在默认状态下才根据选中状态改变边框
            if self.execution_state == 'default':
                if value:
                    self.setPen(self._selected_pen)
                else:
                    self.setPen(self._default_pen)
        elif change == QGraphicsItem.ItemPositionChange:
            # 位置变化时更新连线
            if hasattr(self, 'scene') and self.scene():
                for item in self.scene().items():
                    if isinstance(item, ConnectionItem):
                        item.update_path()
        return super().itemChange(change, value)


class ConnectionItem(QGraphicsPathItem):
    """连线图形项"""

    def __init__(self, start_port, end_port=None, end_pos=None,
                 start_port_index=0, end_port_index=0):
        super().__init__()

        self.start_port = start_port
        self.end_port = end_port
        self.end_pos = end_pos
        self.start_port_index = start_port_index
        self.end_port_index = end_port_index

        # 设置样式
        self.default_pen = QPen(QColor("#888888"), 2)
        self.selected_pen = QPen(QColor("#2196F3"), 3)
        self.setPen(self.default_pen)
        self.setZValue(-1)

        # 允许选中
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, event):
        if not self.isSelected():
            self.setPen(QPen(QColor("#666666"), 3))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if self.isSelected():
            self.setPen(self.selected_pen)
        else:
            self.setPen(self.default_pen)
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            if value:
                self.setPen(self.selected_pen)
            else:
                self.setPen(self.default_pen)
        return super().itemChange(change, value)

    def update_path(self):
        """更新连线路径"""
        if self.start_port:
            start_pos = self.start_port.sceneBoundingRect().center()

            if self.end_port:
                end_pos = self.end_port.sceneBoundingRect().center()
            elif self.end_pos:
                end_pos = self.end_pos
            else:
                return

            # 创建贝塞尔曲线
            path = QPainterPath()
            path.moveTo(start_pos)

            # 控制点
            ctrl_dist = abs(end_pos.x() - start_pos.x()) / 2
            ctrl1 = QPointF(start_pos.x() + ctrl_dist, start_pos.y())
            ctrl2 = QPointF(end_pos.x() - ctrl_dist, end_pos.y())

            path.cubicTo(ctrl1, ctrl2, end_pos)
            self.setPath(path)


class NodeCanvas(QGraphicsView):
    """节点画布视图"""

    node_selected = pyqtSignal(dict)
    canvas_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # 创建场景
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(-5000, -5000, 10000, 10000)
        self.setScene(self.scene)

        # 节点和连线存储
        self.nodes = {}
        self.connections = []

        # 视图设置
        from PyQt5.QtGui import QPainter
        self.setRenderHints(
            self.renderHints() |
            QPainter.Antialiasing |
            QPainter.SmoothPixmapTransform
        )
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)

        # 背景设置
        self.setBackgroundBrush(QBrush(QColor("#2D2D30")))

        # 拖拽相关
        self._pan_mode = False
        self._pan_start_pos = None
        self._drag_connection = None

        # 缩放
        self._zoom = 1.0
        self._zoom_min = 0.25
        self._zoom_max = 4.0

        # 撤销重做
        self._history = []
        self._history_index = -1
        self._restoring = False
        self._dragging_node = None
        self._drag_start_pos = None
        self._batch_depth = 0

        # 接受拖拽
        self.setAcceptDrops(True)

        # 推入初始空状态
        self._push_history()

    def drawBackground(self, painter, rect):
        """绘制背景网格"""
        super().drawBackground(painter, rect)

        # 绘制网格
        grid_size = 20
        grid_color = QColor("#3C3C3C")

        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)

        pen = QPen(grid_color, 1)
        painter.setPen(pen)

        # 绘制竖线
        x = left
        while x < rect.right():
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += grid_size

        # 绘制横线
        y = top
        while y < rect.bottom():
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += grid_size

    def dragEnterEvent(self, event):
        """拖拽进入"""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        """拖拽移动"""
        event.acceptProposedAction()

    def dropEvent(self, event):
        """放置事件"""
        if event.mimeData().hasText():
            try:
                node_data = json.loads(event.mimeData().text())
                pos = self.mapToScene(event.pos())
                self.add_node(node_data, pos.x(), pos.y())
                event.acceptProposedAction()
            except Exception as e:
                print(f"创建节点失败: {e}")

    def add_node(self, node_data, x, y, node_id=None):
        """添加节点"""
        node_id = node_id or str(uuid.uuid4())[:8]

        node = NodeItem(
            node_id=node_id,
            node_type=node_data['type'],
            title=node_data.get('name', node_data.get('title', '')),
            color=node_data.get('color', '#607D8B'),
            params=node_data.get('params', {}),
            x=x - 80,  # 居中
            y=y - 40,
            ports_config=node_data.get('ports', {'inputs': 1, 'outputs': 1})
        )

        self.scene.addItem(node)
        self.nodes[node_id] = node

        # 选中并通知
        node.setSelected(True)
        self._on_selection_changed()
        self.canvas_changed.emit()
        self._push_history()

        return node

    def mousePressEvent(self, event):
        """鼠标按下"""
        if event.button() == Qt.MiddleButton:
            # 中键平移
            self._pan_mode = True
            self._pan_start_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        elif event.button() == Qt.LeftButton:
            # 检查是否点击了端口（遍历所有命中项，避免标签遮挡端口的问题）
            items = self.items(event.pos())
            port_item = next((i for i in items if isinstance(i, PortItem)), None)
            item = port_item or (items[0] if items else None)
            if port_item:
                self._start_connection(port_item, event.pos())
                event.accept()
            else:
                # 点击空白处时清除错误高亮状态
                if item is None:
                    self.clear_execution_highlights()
                # 记录节点拖拽起始位置（用于撤销）
                node_item = next((i for i in items if isinstance(i, NodeItem)), None)
                if node_item:
                    self._dragging_node = node_item
                    self._drag_start_pos = node_item.pos()
                else:
                    self._dragging_node = None
                    self._drag_start_pos = None
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """鼠标移动"""
        if self._pan_mode:
            # 平移画布
            delta = event.pos() - self._pan_start_pos
            self._pan_start_pos = event.pos()

            h_bar = self.horizontalScrollBar()
            v_bar = self.verticalScrollBar()
            h_bar.setValue(h_bar.value() - delta.x())
            v_bar.setValue(v_bar.value() - delta.y())
            event.accept()
        elif self._drag_connection:
            # 更新临时连线
            scene_pos = self.mapToScene(event.pos())
            self._drag_connection.end_pos = scene_pos
            self._drag_connection.update_path()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """鼠标释放"""
        if event.button() == Qt.MiddleButton and self._pan_mode:
            self._pan_mode = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        elif event.button() == Qt.LeftButton and self._drag_connection:
            # 完成连线
            self._finish_connection(event.pos())
            event.accept()
        else:
            super().mouseReleaseEvent(event)

        # 更新选择
        self._on_selection_changed()

        # 检测节点是否被移动，推入历史
        if self._dragging_node is not None:
            if self._dragging_node.pos() != self._drag_start_pos:
                self._push_history()
            self._dragging_node = None
            self._drag_start_pos = None

    def wheelEvent(self, event):
        """滚轮缩放"""
        delta = event.angleDelta().y()
        zoom_factor = 1.1 if delta > 0 else 0.9

        new_zoom = self._zoom * zoom_factor
        if self._zoom_min <= new_zoom <= self._zoom_max:
            self._zoom = new_zoom
            self.scale(zoom_factor, zoom_factor)

    def _start_connection(self, port, pos):
        """开始创建连线"""
        port_index = getattr(port, 'port_index', 0)
        self._drag_connection = ConnectionItem(
            port, end_pos=self.mapToScene(pos),
            start_port_index=port_index
        )
        self.scene.addItem(self._drag_connection)

    def _finish_connection(self, pos):
        """完成连线"""
        if not self._drag_connection:
            return

        # 查找目标端口
        item = self.itemAt(pos)
        if isinstance(item, PortItem) and item != self._drag_connection.start_port:
            # 检查是否是输入输出配对
            if item.is_input != self._drag_connection.start_port.is_input:
                start_port = self._drag_connection.start_port
                end_port = item

                # 确保输入端口是end_port
                if not start_port.is_input and end_port.is_input:
                    pass  # 输出到输入，正确
                elif start_port.is_input and not end_port.is_input:
                    start_port, end_port = end_port, start_port  # 交换
                else:
                    # 取消连线
                    self.scene.removeItem(self._drag_connection)
                    self._drag_connection = None
                    return

                # 检查输入端口是否已存在连接（输入端口只能有一个连接）
                if end_port.is_input:
                    for conn in self.connections:
                        if conn.end_port == end_port:
                            # 输入端口已连接，先删除旧连线
                            self.scene.removeItem(conn)
                            self.connections.remove(conn)
                            break

                # 记录端口索引
                start_port_index = getattr(start_port, 'port_index', 0)
                end_port_index = getattr(end_port, 'port_index', 0)

                # 创建正式连线
                self._drag_connection.start_port = start_port
                self._drag_connection.end_port = end_port
                self._drag_connection.start_port_index = start_port_index
                self._drag_connection.end_port_index = end_port_index
                self._drag_connection.update_path()
                self.connections.append(self._drag_connection)

                # 添加到端口的连接列表
                if hasattr(start_port, 'connections'):
                    start_port.connections.append(self._drag_connection)
                if hasattr(end_port, 'connections'):
                    end_port.connections.append(self._drag_connection)

                self.canvas_changed.emit()
                self._push_history()
                self._drag_connection = None
                return

        # 取消连线
        self.scene.removeItem(self._drag_connection)
        self._drag_connection = None

    def delete_connection(self, connection):
        """删除连线"""
        if connection in self.connections:
            self.connections.remove(connection)
        self.scene.removeItem(connection)
        self.canvas_changed.emit()
        self._push_history()

    def get_node_connections(self, node):
        """获取节点的所有连线"""
        node_connections = []
        for conn in self.connections:
            if (conn.start_port and conn.start_port.parent_node == node) or \
               (conn.end_port and conn.end_port.parent_node == node):
                node_connections.append(conn)
        return node_connections

    def _on_selection_changed(self):
        """选择变化"""
        selected = self.scene.selectedItems()
        if selected and isinstance(selected[0], NodeItem):
            node = selected[0]
            self.node_selected.emit({
                'id': node.node_id,
                'type': node.node_type,
                'title': node.title,
                'params': node.params
            })
        else:
            self.node_selected.emit({})

    def contextMenuEvent(self, event):
        """右键菜单"""
        menu = QMenu(self)

        # 获取点击位置的项
        item = self.itemAt(event.pos())

        if item:
            # 删除选项
            if isinstance(item, (NodeItem, ConnectionItem)):
                delete_action = menu.addAction("删除")
                delete_action.setShortcut("Delete")
                delete_action.triggered.connect(lambda: self._delete_item(item))
                menu.addSeparator()

            # 测试相关选项 - 只在点击节点时显示
            if isinstance(item, NodeItem):
                menu.addSeparator()

                # 模式B：运行到此处
                run_to_here = menu.addAction("▶ 运行到此处")
                run_to_here.triggered.connect(lambda: self._run_to_node(item.node_id))

                # 模式A：测试此节点
                test_node = menu.addAction("🧪 测试此节点")
                test_node.triggered.connect(lambda: self._test_single_node(item.node_id))

                # 查看上次结果（如果有）
                if self.has_test_result(item.node_id):
                    view_result = menu.addAction("👁 查看测试结果")
                    view_result.triggered.connect(lambda: self._view_test_result(item.node_id))

                menu.addSeparator()

        # 添加节点子菜单
        add_menu = menu.addMenu("添加节点")

        # 获取节点类型
        from .node_library import NodeLibraryPanel
        library = NodeLibraryPanel(self.parent())

        for category, nodes in library.node_types.items():
            cat_menu = add_menu.addMenu(f"{library._get_category_icon(category)} {category}")
            for node in nodes:
                action = cat_menu.addAction(f"{node['icon']} {node['name']}")
                action.triggered.connect(lambda checked, n=node: self._add_node_at_mouse(n, event.pos()))

        menu.addSeparator()

        # 其他操作
        select_all_action = menu.addAction("全选")
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.select_all)

        if self.scene.selectedItems():
            delete_selected = menu.addAction("删除选中")
            delete_selected.setShortcut("Delete")
            delete_selected.triggered.connect(self.delete_selected)

        menu.addSeparator()

        clear_action = menu.addAction("清空画布")
        clear_action.triggered.connect(self.clear_canvas)

        menu.exec_(event.globalPos())

    def _delete_item(self, item):
        """删除单个项"""
        if isinstance(item, ConnectionItem):
            self.delete_connection(item)
        elif isinstance(item, NodeItem):
            self._delete_node(item)

    def _delete_node(self, item):
        """删除节点及其相关连线"""
        self._batch_depth += 1
        # 删除相关连线
        connections_to_remove = []
        for conn in self.connections:
            if conn.start_port and conn.start_port.parent_node == item:
                connections_to_remove.append(conn)
            elif conn.end_port and conn.end_port.parent_node == item:
                connections_to_remove.append(conn)
        for conn in connections_to_remove:
            self.delete_connection(conn)
        # 删除节点
        del self.nodes[item.node_id]
        self.scene.removeItem(item)
        self._batch_depth -= 1
        self.canvas_changed.emit()
        self._push_history()

    def _add_node_at_mouse(self, node_data, pos):
        """在鼠标位置添加节点"""
        scene_pos = self.mapToScene(pos)
        self.add_node(node_data, scene_pos.x(), scene_pos.y())

    def clear_canvas(self):
        """清空画布"""
        self.scene.clear()
        self.nodes.clear()
        self.connections.clear()
        self.canvas_changed.emit()
        self._push_history()

    def select_all(self):
        """全选节点"""
        for node in self.nodes.values():
            node.setSelected(True)

    def delete_selected(self):
        """删除选中"""
        self._batch_depth += 1
        # 先删除选中的连线
        for item in list(self.scene.selectedItems()):
            if isinstance(item, ConnectionItem):
                self.delete_connection(item)

        # 再删除选中的节点
        for item in list(self.scene.selectedItems()):
            if isinstance(item, NodeItem):
                self._delete_node(item)

        self._batch_depth -= 1
        self.canvas_changed.emit()
        self._push_history()

    def _push_history(self):
        """推入当前画布状态到历史栈"""
        if self._restoring or self._batch_depth > 0:
            return
        import copy
        snapshot = copy.deepcopy(self.get_workflow_data())
        # 截断 redo 分支
        self._history = self._history[:self._history_index + 1]
        self._history.append(snapshot)
        self._history_index = len(self._history) - 1
        # 限制历史记录上限（50 步）
        if len(self._history) > 50:
            self._history = self._history[-50:]
            self._history_index = len(self._history) - 1

    def _find_port(self, node, port_index, is_output):
        """在节点子项中查找指定端口"""
        for item in node.childItems():
            if (isinstance(item, PortItem)
                    and getattr(item, 'port_index', 0) == port_index
                    and item.is_input == (not is_output)):
                return item
        return None

    def load_workflow_data(self, data):
        """从快照恢复画布（专供撤销/重做使用）"""
        import copy
        from .node_library import NodeLibraryPanel
        library = NodeLibraryPanel()

        self.clear_canvas()

        for node_data in data.get('nodes', []):
            node_type = node_data.get('type')
            node_def = library.get_node_definition(node_type)
            if node_def:
                node_def_copy = copy.deepcopy(node_def)
                node_def_copy['name'] = node_data.get('title', node_def_copy.get('name', ''))
                node_def_copy['params'] = copy.deepcopy(node_data.get('params', {}))
                if 'ports' in node_data:
                    node_def_copy['ports'] = node_data['ports']
                self.add_node(
                    node_def_copy,
                    node_data['x'] + 80,
                    node_data['y'] + 40,
                    node_id=node_data['id']
                )

        for conn_data in data.get('connections', []):
            from_node = self.nodes.get(conn_data['from'])
            to_node = self.nodes.get(conn_data['to'])
            if not (from_node and to_node):
                continue
            from_port = self._find_port(from_node, conn_data['from_port'], is_output=True)
            to_port = self._find_port(to_node, conn_data['to_port'], is_output=False)
            if from_port and to_port:
                conn = ConnectionItem(from_port, to_port,
                                      start_port_index=conn_data['from_port'])
                conn.end_port_index = conn_data['to_port']
                conn.update_path()
                self.scene.addItem(conn)
                self.connections.append(conn)
                from_port.connections.append(conn)
                to_port.connections.append(conn)

        self._on_selection_changed()
        self.canvas_changed.emit()

    def undo(self):
        """撤销"""
        if self._history_index > 0:
            self._history_index -= 1
            self._restoring = True
            self.load_workflow_data(self._history[self._history_index])
            self._restoring = False

    def redo(self):
        """重做"""
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self._restoring = True
            self.load_workflow_data(self._history[self._history_index])
            self._restoring = False

    def connect_engine_signals(self, engine):
        """连接引擎信号以显示执行状态"""
        engine.node_started.connect(self.on_node_started)
        engine.node_finished.connect(self.on_node_finished)
        engine.execution_error.connect(self.on_node_error)
        engine.execution_started.connect(self.clear_execution_highlights)
        self.engine = engine  # 保存引擎引用

    def _test_single_node(self, node_id):
        """测试单个节点（模式A）"""
        if not hasattr(self, 'engine') or not self.engine:
            QMessageBox.warning(self, "错误", "执行引擎未连接")
            return

        # 获取上游节点输出定义
        upstream_outputs = self.engine.get_upstream_outputs(node_id)

        # 显示Mock数据对话框
        from .mock_data_dialog import MockDataDialog
        accepted, mock_data = MockDataDialog.get_mock_variables(
            self, node_id, upstream_outputs
        )

        if not accepted:
            return

        # 在新线程中执行单节点测试
        import threading
        test_thread = threading.Thread(
            target=self._run_single_node_test,
            args=(node_id, mock_data)
        )
        test_thread.start()

    def _run_single_node_test(self, node_id, mock_data):
        """在线程中运行单节点测试"""
        try:
            self.engine.test_single_node(node_id, mock_data)
        except Exception as e:
            from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
            QMetaObject.invokeMethod(
                self, "_show_test_error",
                Qt.QueuedConnection,
                Q_ARG(str, str(e))
            )

    @pyqtSlot(str)
    def _show_test_error(self, error_message):
        """显示测试错误"""
        QMessageBox.warning(self, "测试失败", f"节点测试失败:\n{error_message}")

    def _run_to_node(self, node_id):
        """从起点运行到当前节点（模式B）"""
        if not hasattr(self, 'engine') or not self.engine:
            QMessageBox.warning(self, "错误", "执行引擎未连接")
            return

        # 检查是否有起始节点
        start_nodes = self.engine._find_start_nodes()
        if not start_nodes:
            QMessageBox.warning(self, "错误", "工作流中没有起始节点")
            return

        # 查找路径上的条件节点
        conditions = []
        for start_node in start_nodes:
            from .branch_select_dialog import find_conditions_on_path
            path_conditions = find_conditions_on_path(
                self.engine, start_node['id'], node_id
            )
            conditions.extend(path_conditions)

        # 去重
        seen = set()
        unique_conditions = []
        for cond in conditions:
            if cond['node_id'] not in seen:
                seen.add(cond['node_id'])
                unique_conditions.append(cond)

        # 显示分支选择对话框
        branch_choices = {}
        if unique_conditions:
            from .branch_select_dialog import BranchSelectDialog
            accepted, branch_choices = BranchSelectDialog.get_choices(
                self, unique_conditions
            )
            if not accepted:
                return

        # 运行到目标节点
        self.engine.run_to_node(node_id, branch_choices)

    def has_test_result(self, node_id):
        """检查是否有测试结果"""
        if hasattr(self, 'engine') and self.engine:
            return self.engine.has_test_result(node_id)
        return False

    def _view_test_result(self, node_id):
        """查看测试结果"""
        if not hasattr(self, 'engine') or not self.engine:
            return

        snapshot = self.engine.get_test_snapshot(node_id)
        if not snapshot:
            QMessageBox.information(self, "测试结果", "没有保存的测试结果")
            return

        import time
        variables = snapshot.get('variables', {})
        timestamp = snapshot.get('timestamp', 0)
        time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))

        # 格式化变量显示
        var_text = "\n".join([
            f"  ${name} = {value}"
            for name, value in variables.items()
            if not name.startswith('__')  # 排除内部变量
        ]) or "  (无变量)"

        QMessageBox.information(
            self,
            f"测试结果 - {node_id}",
            f"<b>测试时间:</b> {time_str}<br><br>"
            f"<b>输出变量:</b><br>{var_text}"
        )

    def on_node_started(self, node_id, node_type):
        """节点开始执行"""
        # 先清除所有节点的执行状态（避免多个节点同时显示执行中）
        for node in self.nodes.values():
            if node.execution_state == 'running':
                node.set_execution_state('default')

        # 设置当前节点为执行中
        if node_id in self.nodes:
            self.nodes[node_id].set_execution_state('running')

    def on_node_finished(self, node_id, node_type, result):
        """节点执行完成"""
        if node_id in self.nodes:
            self.nodes[node_id].set_execution_state('success')

    def on_node_error(self, node_id, error_message):
        """节点执行出错"""
        if node_id in self.nodes:
            self.nodes[node_id].set_execution_state('error')

    def clear_execution_highlights(self):
        """清除所有执行高亮状态"""
        for node in self.nodes.values():
            node.set_execution_state('default')

    def get_workflow_data(self):
        """获取工作流数据"""
        nodes_data = []
        for node_id, node in self.nodes.items():
            node_data = {
                'id': node_id,
                'type': node.node_type,
                'title': node.title,
                'x': node.pos().x(),
                'y': node.pos().y(),
                'params': node.params
            }
            # 添加端口配置
            if hasattr(node, 'ports_config') and node.ports_config:
                node_data['ports'] = node.ports_config
            nodes_data.append(node_data)

        connections_data = []
        for conn in self.connections:
            if conn.end_port:
                connections_data.append({
                    'from': conn.start_port.parent_node.node_id,
                    'to': conn.end_port.parent_node.node_id,
                    'from_port': getattr(conn, 'start_port_index', 0),
                    'to_port': getattr(conn, 'end_port_index', 0)
                })

        return {
            'nodes': nodes_data,
            'connections': connections_data
        }
