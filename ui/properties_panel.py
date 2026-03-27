"""
属性面板 - 显示和编辑选中节点的参数
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QPushButton,
    QGroupBox, QFormLayout, QScrollArea, QFileDialog, QColorDialog,
    QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from .screenshot_tool import ScreenshotWidget
from .image_test_widget import ImageTestWidget
from .coordinate_drag_button import CoordinateDragButton


class PropertiesPanel(QWidget):
    """属性面板"""

    params_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_node = None
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        # 内容容器
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setSpacing(15)

        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)

        # 默认显示
        self._show_empty_state()


    def _show_empty_state(self):
        """显示空状态"""
        self._clear_content()

        label = QLabel("选择一个节点以编辑其属性")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: gray; margin-top: 50px;")
        self.content_layout.addWidget(label)

    def _clear_content(self):
        """清除内容"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def set_node(self, node_data):
        """设置当前节点"""
        if not node_data or not node_data.get('id'):
            self.current_node = None
            self._show_empty_state()
            return

        self.current_node = node_data
        self._build_form()

    def _build_form(self):
        """构建参数表单"""
        self._clear_content()

        if not self.current_node:
            return

        # 节点类型标题
        type_label = QLabel(f"<b>{self.current_node.get('title', '未知节点')}</b>")
        type_label.setStyleSheet("font-size: 14px; padding: 5px 0;")
        self.content_layout.addWidget(type_label)

        type_info = QLabel(f"类型: {self.current_node.get('type', 'unknown')}")
        type_info.setStyleSheet("color: gray; font-size: 11px;")
        self.content_layout.addWidget(type_info)

        self.content_layout.addSpacing(10)

        # 节点重命名输入框
        rename_group = QGroupBox("节点名称")
        rename_layout = QFormLayout(rename_group)
        self.title_input = QLineEdit()
        self.title_input.setText(self.current_node.get('title', ''))
        self.title_input.setPlaceholderText("输入节点名称")
        self.title_input.editingFinished.connect(self._on_title_changed)
        rename_layout.addRow("名称:", self.title_input)
        self.content_layout.addWidget(rename_group)

        self.content_layout.addSpacing(5)

        # 参数表单
        params = self.current_node.get('params', {})
        node_type = self.current_node.get('type', '')
        if params:
            form_group = QGroupBox("参数")
            form_layout = QFormLayout(form_group)
            form_layout.setSpacing(10)

            # 预处理：找出成对的坐标参数
            processed = set()
            for param_name, param_def in params.items():
                if param_name in processed:
                    continue

                # 检测 x/y 成对出现的情况
                if param_name == 'x' and 'y' in params:
                    widget = self._create_combined_coord_widget(
                        params['x'], params['y']
                    )
                    form_layout.addRow("坐标:", widget)
                    processed.add('x')
                    processed.add('y')
                elif param_name == 'y' and 'x' in params:
                    # y 已经在 x 的处理中创建了，跳过
                    continue
                else:
                    widget = self._create_param_widget(param_name, param_def)
                    if widget:
                        form_layout.addRow(param_def.get('label', param_name), widget)

            # 条件节点添加语法提示
            if node_type == 'condition':
                hint_label = QLabel("支持: $变量 == 值、$变量 > 数字、$found == True")
                hint_label.setStyleSheet("color: gray; font-size: 11px; margin-top: 5px;")
                form_layout.addRow("", hint_label)

            self.content_layout.addWidget(form_group)

            # 找图分支节点添加测试按钮和变量提示
            if node_type in ('if_image', 'async_listener'):
                self._add_find_image_test(params)
            if node_type == 'if_image':
                self._add_output_vars_hint('if_image')

        else:
            no_params = QLabel("(此节点无参数)")
            no_params.setStyleSheet("color: gray; font-style: italic;")
            self.content_layout.addWidget(no_params)

        # 应用按钮
        self.content_layout.addStretch()

        apply_btn = QPushButton("应用更改")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        apply_btn.clicked.connect(self._on_apply)
        self.content_layout.addWidget(apply_btn)

    def _create_param_widget(self, param_name, param_def):
        """创建参数控件"""
        param_type = param_def.get('type', 'string')
        # 优先使用已保存的value，否则使用default
        # 防御性处理：如果value是字典，说明数据格式错误，使用default
        raw_value = param_def.get('value')
        if raw_value is not None and not isinstance(raw_value, dict):
            default_value = raw_value
        else:
            default_value = param_def.get('default', '')

        if param_type == 'string':
            # 检查是否为坐标参数（x 或 y），即使是 string 类型也添加拖拽按钮
            if param_name in ('x', 'y'):
                return self._create_coord_widget(param_name, param_def, default_value, string_mode=True)

            widget = QLineEdit()
            widget.setText(str(default_value))
            widget.setProperty('param_name', param_name)
            widget.textChanged.connect(self._on_param_changed)
            return widget

        elif param_type == 'int':
            # 检查是否为坐标参数（x 或 y），需要添加拖拽按钮
            if param_name in ('x', 'y'):
                return self._create_coord_widget(param_name, param_def, default_value)

            # 检查是否为可选参数（允许为空）
            is_optional = param_def.get('optional', False)
            if is_optional:
                # 可选int使用带特殊值处理的LineEdit
                widget = QLineEdit()
                # 防御性处理：只设置有效的整数值，不设置字典
                if default_value is not None and isinstance(default_value, (int, str)):
                    try:
                        # 如果是字符串，尝试转换为int验证
                        if isinstance(default_value, str):
                            int(default_value)
                        widget.setText(str(default_value))
                    except (ValueError, TypeError):
                        pass  # 无效值，不设置文本
                widget.setPlaceholderText("未设置")
                widget.setProperty('param_name', param_name)
                widget.setProperty('param_type', 'optional_int')
                # 添加验证器只允许整数或空
                from PyQt5.QtGui import QIntValidator
                validator = QIntValidator(param_def.get('min', -999999), param_def.get('max', 999999))
                widget.setValidator(validator)
                widget.textChanged.connect(self._on_param_changed)
                return widget
            else:
                widget = QSpinBox()
                widget.setRange(param_def.get('min', -999999), param_def.get('max', 999999))
                widget.setValue(int(default_value) if default_value is not None else 0)
                widget.setProperty('param_name', param_name)
                widget.valueChanged.connect(self._on_param_changed)
                return widget

        elif param_type == 'float':
            widget = QDoubleSpinBox()
            widget.setRange(param_def.get('min', -999999.0), param_def.get('max', 999999.0))
            widget.setSingleStep(0.01)
            widget.setDecimals(2)
            widget.setValue(float(default_value))
            widget.setProperty('param_name', param_name)
            widget.valueChanged.connect(self._on_param_changed)
            return widget

        elif param_type == 'select':
            widget = QComboBox()
            widget.addItems(param_def.get('options', []))
            if default_value in param_def.get('options', []):
                widget.setCurrentText(default_value)
            widget.setProperty('param_name', param_name)
            widget.currentTextChanged.connect(self._on_param_changed)
            return widget

        elif param_type == 'boolean':
            widget = QCheckBox()
            widget.setChecked(bool(default_value))
            widget.setProperty('param_name', param_name)
            widget.stateChanged.connect(self._on_param_changed)
            return widget

        elif param_type == 'file':
            # 对于找图节点的图片路径，使用带截图功能的控件
            if param_name == 'image_path':
                widget = ScreenshotWidget(default_path=str(default_value))
                widget.path_edit.setProperty('param_name', param_name)
                widget.path_edit.setProperty('param_type', 'file')
                # 连接截图完成信号，自动应用更改
                widget.path_changed.connect(lambda path: self._auto_apply_param(param_name, path))
                # 也连接文本变化信号
                widget.path_edit.textChanged.connect(lambda: self._auto_apply_param(param_name, widget.text()))
                return widget
            else:
                widget = QWidget()
                layout = QHBoxLayout(widget)
                layout.setContentsMargins(0, 0, 0, 0)

                line_edit = QLineEdit()
                line_edit.setText(str(default_value))
                line_edit.setProperty('param_name', param_name)
                layout.addWidget(line_edit)

                browse_btn = QPushButton("浏览...")
                browse_btn.clicked.connect(lambda: self._browse_file(line_edit))
                layout.addWidget(browse_btn)

                return widget

        elif param_type == 'color':
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)

            line_edit = QLineEdit()
            line_edit.setText(str(default_value))
            line_edit.setProperty('param_name', param_name)
            layout.addWidget(line_edit)

            color_btn = QPushButton("选择...")
            color_btn.clicked.connect(lambda: self._choose_color(line_edit))
            layout.addWidget(color_btn)

            return widget

        elif param_type == 'region':
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(5)

            # X, Y, Width, Height
            coords = default_value if isinstance(default_value, list) else [0, 0, 1920, 1080]

            for i, label in enumerate(['X', 'Y', '宽', '高']):
                row = QHBoxLayout()
                row.addWidget(QLabel(f"{label}:"))
                spin = QSpinBox()
                spin.setRange(0, 99999)
                spin.setValue(coords[i] if i < len(coords) else 0)
                spin.setProperty('param_name', param_name)
                spin.setProperty('coord_index', i)
                row.addWidget(spin)
                layout.addLayout(row)

            return widget

        return None

    def _create_coord_widget(self, param_name, param_def, default_value, string_mode=False):
        """创建带拖拽按钮的坐标输入控件

        Args:
            param_name: 参数名 (x 或 y)
            param_def: 参数定义
            default_value: 默认值
            string_mode: 是否为字符串模式（支持变量如 $find_x）
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        if string_mode:
            # 字符串模式：使用 QLineEdit 支持变量
            line_edit = QLineEdit()
            line_edit.setText(str(default_value) if default_value is not None else "0")
            line_edit.setProperty('param_name', param_name)
            line_edit.textChanged.connect(self._on_param_changed)
            layout.addWidget(line_edit)

            # 创建拖拽按钮
            drag_btn = CoordinateDragButton()
            drag_btn.setProperty('target_param', param_name)
            # 连接信号到输入框的 setText
            drag_btn.coordinate_captured.connect(
                lambda x, y, p=param_name, le=line_edit: le.setText(str(x if p == 'x' else y))
            )
            layout.addWidget(drag_btn)
        else:
            # 数字模式：使用 QSpinBox
            spin_box = QSpinBox()
            spin_box.setRange(param_def.get('min', -999999), param_def.get('max', 999999))
            spin_box.setValue(int(default_value) if default_value is not None else 0)
            spin_box.setProperty('param_name', param_name)
            spin_box.valueChanged.connect(self._on_param_changed)
            layout.addWidget(spin_box)

            # 创建拖拽按钮
            drag_btn = CoordinateDragButton()
            drag_btn.setProperty('target_param', param_name)
            # 连接信号到输入框的 setValue
            drag_btn.coordinate_captured.connect(
                lambda x, y, p=param_name, s=spin_box: s.setValue(x if p == 'x' else y)
            )
            layout.addWidget(drag_btn)

        return widget

    def _create_combined_coord_widget(self, x_def, y_def):
        """创建合并的X/Y坐标控件，一个拖拽按钮同时设置XY"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 判断是 string 类型（mouse_move）还是 int 类型（mouse_click）
        x_type = x_def.get('type', 'int')
        y_type = y_def.get('type', 'int')

        # 获取默认值
        x_value = x_def.get('value')
        if x_value is None or isinstance(x_value, dict):
            x_value = x_def.get('default', '0' if x_type == 'string' else 0)

        y_value = y_def.get('value')
        if y_value is None or isinstance(y_value, dict):
            y_value = y_def.get('default', '0' if y_type == 'string' else 0)

        # X 标签和输入框
        x_label = QLabel("X:")
        layout.addWidget(x_label)

        if x_type == 'string':
            self.x_input = QLineEdit()
            self.x_input.setText(str(x_value))
            self.x_input.setProperty('param_name', 'x')
            self.x_input.textChanged.connect(self._on_param_changed)
            layout.addWidget(self.x_input)
        else:
            self.x_input = QSpinBox()
            self.x_input.setRange(x_def.get('min', -999999), x_def.get('max', 999999))
            if x_value is not None:
                self.x_input.setValue(int(x_value))
            self.x_input.setProperty('param_name', 'x')
            self.x_input.valueChanged.connect(self._on_param_changed)
            layout.addWidget(self.x_input)

        # Y 标签和输入框
        y_label = QLabel("Y:")
        layout.addWidget(y_label)

        if y_type == 'string':
            self.y_input = QLineEdit()
            self.y_input.setText(str(y_value))
            self.y_input.setProperty('param_name', 'y')
            self.y_input.textChanged.connect(self._on_param_changed)
            layout.addWidget(self.y_input)
        else:
            self.y_input = QSpinBox()
            self.y_input.setRange(y_def.get('min', -999999), y_def.get('max', 999999))
            if y_value is not None:
                self.y_input.setValue(int(y_value))
            self.y_input.setProperty('param_name', 'y')
            self.y_input.valueChanged.connect(self._on_param_changed)
            layout.addWidget(self.y_input)

        # 拖拽按钮（同时设置XY）
        drag_btn = CoordinateDragButton()
        drag_btn.setToolTip("按住拖拽到目标位置，松开同时捕获X和Y坐标")
        drag_btn.coordinate_captured.connect(
            lambda x, y: self._on_combined_coord_captured(x, y)
        )
        layout.addWidget(drag_btn)

        return widget

    def _on_combined_coord_captured(self, x, y):
        """处理合并坐标捕获"""
        if hasattr(self, 'x_input') and hasattr(self, 'y_input'):
            if isinstance(self.x_input, QLineEdit):
                self.x_input.setText(str(x))
            else:
                self.x_input.setValue(x)

            if isinstance(self.y_input, QLineEdit):
                self.y_input.setText(str(y))
            else:
                self.y_input.setValue(y)

    def _browse_file(self, line_edit):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "",
            "图片文件 (*.png *.jpg *.bmp);;所有文件 (*.*)"
        )
        if file_path:
            line_edit.setText(file_path)

    def _choose_color(self, line_edit):
        """选择颜色"""
        color = QColorDialog.getColor()
        if color.isValid():
            line_edit.setText(color.name())

    def _on_param_changed(self):
        """参数变化"""
        # 可以在这里添加实时更新逻辑
        pass

    def _auto_apply_param(self, param_name, value):
        """自动应用参数更改（用于截图路径等需要实时保存的场景）"""
        if not self.current_node:
            return

        params = self.current_node.get('params', {})
        if param_name in params:
            params[param_name]['value'] = value
            self.params_changed.emit(self.current_node)

    def _collect_param_values(self):
        """收集所有参数值"""
        if not self.current_node:
            return {}

        params = self.current_node.get('params', {})
        new_values = {}

        # 遍历表单中的所有控件
        for param_name, param_def in params.items():
            param_type = param_def.get('type', 'string')
            value = self._get_widget_value(param_name, param_type)
            if value is not None:
                new_values[param_name] = value

        return new_values

    def _get_widget_value(self, param_name, param_type):
        """获取控件值"""
        # 处理 region 类型
        if param_type == 'region':
            return self._get_region_value()

        # 特殊处理组合坐标控件中的 x 和 y
        if param_name in ('x', 'y'):
            # 查找组合控件中的输入框
            if hasattr(self, 'x_input') and hasattr(self, 'y_input'):
                if param_name == 'x':
                    if isinstance(self.x_input, QLineEdit):
                        return self.x_input.text().strip()
                    else:
                        return self.x_input.value()
                else:  # y
                    if isinstance(self.y_input, QLineEdit):
                        return self.y_input.text().strip()
                    else:
                        return self.y_input.value()

        # 特殊处理坐标参数 (x, y) - 它们可能在 QWidget 容器内（旧版兼容）
        if param_name in ('x', 'y'):
            # 查找 QWidget 容器
            for child in self.content_widget.findChildren(QWidget):
                if child.property('param_name') == param_name:
                    # 在容器内查找 QLineEdit 或 QSpinBox
                    for inner_child in child.findChildren(QWidget):
                        if isinstance(inner_child, QLineEdit):
                            text = inner_child.text().strip()
                            if param_type == 'int':
                                return int(text) if text else None
                            return text
                        elif isinstance(inner_child, QSpinBox):
                            return inner_child.value()
                    break

        # 查找对应的控件
        for child in self.content_widget.findChildren(QWidget):
            if child.property('param_name') == param_name:
                if isinstance(child, QLineEdit):
                    text = child.text().strip()
                    # 处理可选int类型 - 从控件属性判断
                    if child.property('param_type') == 'optional_int':
                        # 防御性处理：如果文本看起来像字典，返回None
                        if text.startswith('{') and text.endswith('}'):
                            return None
                        return int(text) if text else None
                    return text
                elif isinstance(child, QSpinBox):
                    return child.value()
                elif isinstance(child, QDoubleSpinBox):
                    return child.value()
                elif isinstance(child, QComboBox):
                    return child.currentText()
                elif isinstance(child, QCheckBox):
                    return child.isChecked()

        # 特殊处理截图控件
        for child in self.content_widget.findChildren(ScreenshotWidget):
            if child.path_edit.property('param_name') == param_name:
                return child.text()

        return None

    def _on_apply(self):
        """应用更改"""
        if not self.current_node:
            return

        # 收集参数值
        new_values = self._collect_param_values()

        # 更新节点数据
        params = self.current_node.get('params', {})
        for param_name, value in new_values.items():
            if param_name in params:
                params[param_name]['value'] = value

        self.params_changed.emit(self.current_node)
        QMessageBox.information(self, "成功", "参数已应用")

    def _on_title_changed(self):
        """节点名称改变"""
        if not self.current_node:
            return

        new_title = self.title_input.text().strip()
        if not new_title:
            new_title = self.current_node.get('title', '未命名节点')
            self.title_input.setText(new_title)
            return

        # 更新节点数据中的标题
        old_title = self.current_node.get('title', '')
        if new_title != old_title:
            self.current_node['title'] = new_title
            # 更新节点类型标题显示
            self.params_changed.emit(self.current_node)

    def _add_find_image_test(self, params):
        """添加找图测试按钮"""
        test_group = QGroupBox("测试")
        test_layout = QVBoxLayout(test_group)

        # 创建测试控件
        self.image_test_widget = ImageTestWidget()

        # 从参数定义中获取值 (优先使用 value，否则使用 default)
        image_path_def = params.get('image_path', {})
        image_path = image_path_def.get('value') if image_path_def.get('value') is not None else image_path_def.get('default', '')
        threshold_def = params.get('threshold', {})
        threshold = threshold_def.get('value') if threshold_def.get('value') is not None else threshold_def.get('default', 0.8)
        region_def = params.get('region', {})
        region = region_def.get('value') if region_def.get('value') is not None else region_def.get('default', [0, 0, 1920, 1080])

        self.image_test_widget.set_params(image_path, threshold, region)
        test_layout.addWidget(self.image_test_widget)

        # 连接测试按钮点击事件，动态获取最新参数值
        self.image_test_widget.test_btn.clicked.disconnect(self.image_test_widget._on_test)
        self.image_test_widget.test_btn.clicked.connect(self._on_test_with_current_params)

        self.content_layout.addWidget(test_group)

    def _on_test_with_current_params(self):
        """使用当前界面参数值进行测试"""
        # 动态收集当前参数值 - 基本参数
        image_path = self._get_widget_value('image_path', 'file') or ''
        threshold = self._get_widget_value('threshold', 'float') or 0.8
        region = self._get_region_value() or [0, 0, 1920, 1080]

        # 收集高级参数
        offset_x = self._get_widget_value('offset_x', 'int') or 0
        offset_y = self._get_widget_value('offset_y', 'int') or 0
        random_offset = self._get_widget_value('random_offset', 'int') or 0
        auto_move = self._get_widget_value('auto_move', 'boolean') or False
        auto_click = self._get_widget_value('auto_click', 'boolean') or False
        click_button = self._get_widget_value('click_button', 'select') or 'left'
        click_delay = self._get_widget_value('click_delay', 'int') or 0

        # 更新测试控件基本参数
        self.image_test_widget.set_params(image_path, threshold, region)
        # 设置高级参数
        self.image_test_widget.set_advanced_params(
            offset_x=offset_x,
            offset_y=offset_y,
            random_offset=random_offset,
            auto_move=auto_move,
            auto_click=auto_click,
            click_button=click_button,
            click_delay=click_delay
        )
        # 执行测试
        self.image_test_widget._on_test()

    def _get_region_value(self):
        """获取区域参数值"""
        coords = []
        for i in range(4):
            for child in self.content_widget.findChildren(QSpinBox):
                if child.property('param_name') == 'region' and child.property('coord_index') == i:
                    coords.append(child.value())
                    break
        return coords if len(coords) == 4 else None

    def _add_output_vars_hint(self, node_type):
        """添加输出变量提示"""
        if node_type == 'if_image':
            group = QGroupBox("输出变量")
            layout = QVBoxLayout()

            vars_text = """
            <b>找到图片时：</b><br>
            • $find_x - 图片中心X坐标<br>
            • $find_y - 图片中心Y坐标<br>
            • $found = True<br>
            • $confidence - 匹配置信度<br><br>
            <b>未找到时：</b><br>
            • $found = False<br>
            • $confidence - 最高匹配置信度
            """

            label = QLabel(vars_text)
            label.setWordWrap(True)
            label.setStyleSheet("QLabel { color: #666; font-size: 12px; }")
            layout.addWidget(label)
            group.setLayout(layout)
            self.content_layout.addWidget(group)
