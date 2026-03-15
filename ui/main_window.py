"""
主窗口 - 应用程序主容器
"""
from PyQt5.QtWidgets import (
    QMainWindow, QDockWidget, QToolBar, QStatusBar,
    QAction, QMessageBox, QFileDialog, QWidget, QVBoxLayout
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence, QIcon

from .node_library import NodeLibraryPanel
from .node_canvas import NodeCanvas
from .properties_panel import PropertiesPanel
from .log_panel import LogPanel
from engine import WorkflowEngine


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("可视化键鼠自动化编辑器")
        self.setGeometry(100, 100, 1400, 900)

        # 当前工作流文件路径
        self.current_file = None
        self.is_modified = False

        # 创建执行引擎
        self.workflow_engine = WorkflowEngine()

        # 初始化UI（必须先初始化，才能连接信号）
        self._init_ui()
        self._init_menu()
        self._init_toolbar()
        self._init_statusbar()
        self._init_shortcuts()

        # 连接信号（在UI初始化之后）
        self._connect_engine_signals()

        # 更新状态
        self._update_title()
        self._update_status()

    def _init_ui(self):
        """初始化用户界面"""
        # 创建中央节点画布
        self.canvas = NodeCanvas(self)
        self.setCentralWidget(self.canvas)

        # 创建左侧面板 - 节点库
        self.node_library = NodeLibraryPanel(self)
        self.left_dock = QDockWidget("节点库", self)
        self.left_dock.setWidget(self.node_library)
        self.left_dock.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.left_dock)

        # 创建右侧面板 - 属性面板
        self.properties_panel = PropertiesPanel(self)
        self.right_dock = QDockWidget("属性", self)
        self.right_dock.setWidget(self.properties_panel)
        self.right_dock.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.RightDockWidgetArea, self.right_dock)

        # 设置属性面板宽度限制
        self.right_dock.setMinimumWidth(280)
        self.right_dock.setMaximumWidth(450)

        # 创建底部面板 - 日志输出
        self.log_panel = LogPanel(self)
        self.bottom_dock = QDockWidget("日志", self)
        self.bottom_dock.setWidget(self.log_panel)
        self.bottom_dock.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.bottom_dock)

        # 连接信号
        self.canvas.node_selected.connect(self._on_node_selected)
        self.canvas.canvas_changed.connect(self._on_canvas_changed)
        self.node_library.node_dragged.connect(self._on_node_dragged)
        self.properties_panel.params_changed.connect(self._on_params_changed)

    def _connect_engine_signals(self):
        """连接执行引擎信号"""
        self.workflow_engine.execution_started.connect(
            lambda: self.log_panel.log_info('工作流开始执行'))
        self.workflow_engine.execution_stopped.connect(self._on_execution_stopped)
        self.workflow_engine.node_started.connect(
            lambda nid, ntype: self.log_panel.log_info(f'执行节点: {ntype}'))
        self.workflow_engine.execution_error.connect(
            lambda nid, err: self.log_panel.log_error(f'节点 {nid} 错误: {err}'))
        self.workflow_engine.log_message.connect(
            lambda level, msg: self._on_engine_log(level, msg))

        # 连接画布执行可视化
        self.canvas.connect_engine_signals(self.workflow_engine)

    def _on_engine_log(self, level, message):
        """处理执行引擎日志"""
        if level == 'error':
            self.log_panel.log_error(message)
        elif level == 'warning':
            self.log_panel.log_warning(message)
        elif level == 'success':
            self.log_panel.log_success(message)
        else:
            self.log_panel.log_info(message)

    def _init_menu(self):
        """初始化菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        new_action = QAction("新建(&N)", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._on_new)
        file_menu.addAction(new_action)

        open_action = QAction("打开(&O)...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._on_open)
        file_menu.addAction(open_action)

        save_action = QAction("保存(&S)", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)

        save_as_action = QAction("另存为(&A)...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self._on_save_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")

        undo_action = QAction("撤销(&U)", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self._on_undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("重做(&R)", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(self._on_redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        delete_action = QAction("删除(&D)", self)
        delete_action.setShortcut(QKeySequence.Delete)
        delete_action.triggered.connect(self._on_delete)
        edit_menu.addAction(delete_action)

        select_all_action = QAction("全选(&A)", self)
        select_all_action.setShortcut(QKeySequence.SelectAll)
        select_all_action.triggered.connect(self._on_select_all)
        edit_menu.addAction(select_all_action)

        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")

        toggle_library = QAction("节点库(&L)", self)
        toggle_library.setCheckable(True)
        toggle_library.setChecked(True)
        toggle_library.triggered.connect(lambda: self.left_dock.setVisible(not self.left_dock.isVisible()))
        view_menu.addAction(toggle_library)

        toggle_properties = QAction("属性面板(&P)", self)
        toggle_properties.setCheckable(True)
        toggle_properties.setChecked(True)
        toggle_properties.triggered.connect(lambda: self.right_dock.setVisible(not self.right_dock.isVisible()))
        view_menu.addAction(toggle_properties)

        toggle_log = QAction("日志面板(&G)", self)
        toggle_log.setCheckable(True)
        toggle_log.setChecked(True)
        toggle_log.triggered.connect(lambda: self.bottom_dock.setVisible(not self.bottom_dock.isVisible()))
        view_menu.addAction(toggle_log)

        # 运行菜单
        run_menu = menubar.addMenu("运行(&R)")

        run_action = QAction("运行(&R)", self)
        run_action.setShortcut("F5")
        run_action.triggered.connect(self._on_run)
        run_menu.addAction(run_action)

        stop_action = QAction("停止(&S)", self)
        stop_action.setShortcut("F6")
        stop_action.triggered.connect(self._on_stop)
        run_menu.addAction(stop_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _init_toolbar(self):
        """初始化工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # 新建
        new_action = QAction("🗑️ 新建", self)
        new_action.setToolTip("新建工作流 (Ctrl+N)")
        new_action.triggered.connect(self._on_new)
        toolbar.addAction(new_action)

        # 打开
        open_action = QAction("📂 打开", self)
        open_action.setToolTip("打开工作流 (Ctrl+O)")
        open_action.triggered.connect(self._on_open)
        toolbar.addAction(open_action)

        # 保存
        save_action = QAction("💾 保存", self)
        save_action.setToolTip("保存工作流 (Ctrl+S)")
        save_action.triggered.connect(self._on_save)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # 运行
        self.run_action = QAction("▶️ 运行", self)
        self.run_action.setToolTip("运行工作流 (F5)")
        self.run_action.triggered.connect(self._on_run)
        toolbar.addAction(self.run_action)

        # 停止
        self.stop_action = QAction("⏹️ 停止", self)
        self.stop_action.setToolTip("停止执行 (F6)")
        self.stop_action.setEnabled(False)
        self.stop_action.triggered.connect(self._on_stop)
        toolbar.addAction(self.stop_action)

        toolbar.addSeparator()

        # 撤销/重做
        undo_action = QAction("↩️ 撤销", self)
        undo_action.setToolTip("撤销 (Ctrl+Z)")
        undo_action.triggered.connect(self._on_undo)
        toolbar.addAction(undo_action)

        redo_action = QAction("↪️ 重做", self)
        redo_action.setToolTip("重做 (Ctrl+Y)")
        redo_action.triggered.connect(self._on_redo)
        toolbar.addAction(redo_action)

    def _init_statusbar(self):
        """初始化状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        # 状态标签
        self.status_label = self.statusbar.showMessage("就绪")

        # 文件信息
        self.file_label = self.statusbar.showMessage("未命名")

        # 节点统计
        self.stats_label = self.statusbar.showMessage("节点: 0")

    def _init_shortcuts(self):
        """初始化额外的快捷键"""
        pass

    def _update_title(self):
        """更新窗口标题"""
        title = "可视化键鼠自动化编辑器"
        if self.current_file:
            import os
            filename = os.path.basename(self.current_file)
            title = f"{filename} - {title}"
        if self.is_modified:
            title = f"*{title}"
        self.setWindowTitle(title)

    def _update_status(self):
        """更新状态栏信息"""
        node_count = len(self.canvas.nodes) if hasattr(self.canvas, 'nodes') else 0
        self.statusbar.showMessage(f"就绪 | 节点数: {node_count}", 0)

    def _on_node_selected(self, node_data):
        """节点被选中"""
        self.properties_panel.set_node(node_data)

    def _on_canvas_changed(self):
        """画布内容变化"""
        self.is_modified = True
        self._update_title()
        self._update_status()

    def _on_node_dragged(self, node_type, node_data):
        """节点从库中拖拽"""
        # 这里处理拖拽创建节点的逻辑
        self.log_panel.log_info(f"准备添加节点: {node_type}")

    def _on_params_changed(self, node_data):
        """节点参数被修改"""
        # 更新画布中的节点参数
        node_id = node_data.get('id')
        if node_id and node_id in self.canvas.nodes:
            self.canvas.nodes[node_id].params = node_data.get('params', {})
            self.canvas.canvas_changed.emit()
            self.log_panel.log_info(f"节点 {node_data.get('title')} 参数已更新")

    def _on_new(self):
        """新建工作流"""
        if self.is_modified:
            reply = QMessageBox.question(
                self, "确认",
                "当前工作流有未保存的更改，是否保存？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if reply == QMessageBox.Save:
                self._on_save()
            elif reply == QMessageBox.Cancel:
                return

        self.canvas.clear_canvas()
        self.current_file = None
        self.is_modified = False
        self._update_title()
        self.log_panel.log_info("新建工作流")

    def _on_open(self):
        """打开工作流"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开工作流", "", "JSON文件 (*.json);;所有文件 (*.*)"
        )
        if file_path:
            self._load_from_file(file_path)

    def _load_from_file(self, file_path):
        """从文件加载"""
        import json
        import copy
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)

            self.log_panel.log_info(f"加载文件: {file_path}, 节点数: {len(workflow_data.get('nodes', []))}")

            # 清空当前画布
            self.canvas.clear_canvas()

            # 加载节点
            from .node_library import NodeLibraryPanel
            library = NodeLibraryPanel()

            node_id_map = {}  # 用于映射旧ID到新ID

            for node_data in workflow_data.get('nodes', []):
                node_type = node_data.get('type')
                self.log_panel.log_info(f"  加载节点: type={node_type}, title={node_data.get('title')}")
                node_def = library.get_node_definition(node_type)

                if node_def:
                    # 深拷贝节点定义，避免修改原始定义
                    node_def_copy = copy.deepcopy(node_def)

                    # 更新参数值
                    saved_params = node_data.get('params', {})
                    for key, param_data in saved_params.items():
                        if key in node_def_copy['params']:
                            # 支持两种格式：1) 完整参数结构 2) 仅值
                            if isinstance(param_data, dict) and 'value' in param_data:
                                node_def_copy['params'][key]['value'] = param_data['value']
                            else:
                                node_def_copy['params'][key]['value'] = param_data

                    # 创建节点
                    x = node_data.get('x', 0)
                    y = node_data.get('y', 0)
                    new_node = self.canvas.add_node(node_def_copy, x + 80, y + 40)
                    node_id_map[node_data.get('id')] = new_node.node_id
                else:
                    self.log_panel.log_warning(f"  未找到节点类型定义: {node_type}")

            # 加载连线
            for conn_data in workflow_data.get('connections', []):
                from_id = conn_data.get('from')
                to_id = conn_data.get('to')
                from_port_idx = conn_data.get('from_port', 0)
                to_port_idx = conn_data.get('to_port', 0)

                # 获取映射后的新ID
                new_from_id = node_id_map.get(from_id)
                new_to_id = node_id_map.get(to_id)

                if new_from_id and new_to_id:
                    from_node = self.canvas.nodes.get(new_from_id)
                    to_node = self.canvas.nodes.get(new_to_id)

                    if from_node and to_node:
                        # 获取对应端口的输出/输入端口
                        from_port = None
                        to_port = None

                        # 获取输出端口（支持多端口）
                        if hasattr(from_node, 'output_ports') and from_port_idx < len(from_node.output_ports):
                            from_port = from_node.output_ports[from_port_idx]
                        elif from_port_idx == 0 and hasattr(from_node, 'output_port'):
                            from_port = from_node.output_port

                        # 获取输入端口（支持多端口）
                        if hasattr(to_node, 'input_ports') and to_port_idx < len(to_node.input_ports):
                            to_port = to_node.input_ports[to_port_idx]
                        elif to_port_idx == 0 and hasattr(to_node, 'input_port'):
                            to_port = to_node.input_port

                        if from_port and to_port:
                            # 创建连线
                            from .node_canvas import ConnectionItem
                            conn = ConnectionItem(
                                from_port, to_port,
                                start_port_index=from_port_idx,
                                end_port_index=to_port_idx
                            )
                            conn.update_path()
                            self.canvas.scene.addItem(conn)
                            self.canvas.connections.append(conn)

                            # 添加到端口的连接列表
                            if hasattr(from_port, 'connections'):
                                from_port.connections.append(conn)
                            if hasattr(to_port, 'connections'):
                                to_port.connections.append(conn)

            self.current_file = file_path
            self.is_modified = False
            self._update_title()
            self.log_panel.log_info(f"打开文件: {file_path}")

        except Exception as e:
            self.log_panel.log_error(f"加载失败: {e}")
            QMessageBox.critical(self, "错误", f"加载失败: {e}")

    def _on_save(self):
        """保存工作流"""
        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self._on_save_as()

    def _on_save_as(self):
        """另存为"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存工作流", "", "JSON文件 (*.json);;所有文件 (*.*)"
        )
        if file_path:
            self.current_file = file_path
            self._save_to_file(file_path)

    def _save_to_file(self, file_path):
        """保存到文件"""
        import json
        try:
            workflow_data = self.canvas.get_workflow_data()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(workflow_data, f, ensure_ascii=False, indent=2)
            self.is_modified = False
            self._update_title()
            self.log_panel.log_info(f"保存成功: {file_path}")
        except Exception as e:
            self.log_panel.log_error(f"保存失败: {e}")
            QMessageBox.critical(self, "错误", f"保存失败: {e}")

    def _on_undo(self):
        """撤销"""
        self.canvas.undo()

    def _on_redo(self):
        """重做"""
        self.canvas.redo()

    def _on_delete(self):
        """删除选中"""
        self.canvas.delete_selected()

    def _on_select_all(self):
        """全选"""
        self.canvas.select_all()

    def _on_run(self):
        """运行工作流"""
        # 加载当前工作流
        workflow_data = self.canvas.get_workflow_data()
        nodes = workflow_data.get('nodes', [])
        connections = workflow_data.get('connections', [])

        self.log_panel.log_info(f'运行工作流: {len(nodes)} 个节点, {len(connections)} 条连线')
        for node in nodes:
            self.log_panel.log_info(f"  节点: type={node.get('type')}, title={node.get('title')}")

        if not nodes:
            self.log_panel.log_warning('工作流为空，无法执行')
            return

        self.workflow_engine.load_workflow(workflow_data)
        self.workflow_engine.start()
        self.run_action.setEnabled(False)
        self.stop_action.setEnabled(True)

    def _on_stop(self):
        """停止执行"""
        self.workflow_engine.stop()
        # UI 状态更新由 _on_execution_stopped 处理

    def _on_execution_stopped(self):
        """执行停止后的处理（正常结束或手动停止）"""
        self.log_panel.log_info('工作流执行停止')
        self.run_action.setEnabled(True)
        self.stop_action.setEnabled(False)

    def _on_about(self):
        """关于对话框"""
        QMessageBox.about(
            self,
            "关于",
            "<h2>可视化键鼠自动化编辑器</h2>"
            "<p>版本: 0.1.0</p>"
            "<p>基于 PyQt5 开发的节点式自动化工具</p>"
        )

    def closeEvent(self, event):
        """关闭事件"""
        if self.is_modified:
            reply = QMessageBox.question(
                self, "确认",
                "当前工作流有未保存的更改，是否保存？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if reply == QMessageBox.Save:
                self._on_save()
                if self.is_modified:  # 保存失败或取消
                    event.ignore()
                    return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
        event.accept()
