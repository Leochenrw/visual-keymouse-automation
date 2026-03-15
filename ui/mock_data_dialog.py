"""
Mock数据配置对话框 - 用于单节点测试时配置输入数据
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QCheckBox,
    QSpinBox, QDoubleSpinBox, QComboBox, QScrollArea,
    QWidget, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
import random


class MockDataDialog(QDialog):
    """Mock数据配置对话框"""

    def __init__(self, parent, target_node_id, upstream_outputs, existing_values=None):
        """
        Args:
            parent: 父窗口
            target_node_id: 目标节点ID
            upstream_outputs: 上游节点的输出定义列表
                [
                    {"node_id": "n1", "node_title": "找图", "node_type": "find_image", "outputs": {"find_x": {...}, ...}},
                    ...
                ]
            existing_values: 已存在的值，用于回填
        """
        super().__init__(parent)
        self.target_node_id = target_node_id
        self.upstream_outputs = upstream_outputs
        self.existing_values = existing_values or {}
        self.mock_data = {}
        self.widgets = {}

        self.setWindowTitle("配置Mock数据 - 单节点测试")
        self.setMinimumWidth(450)
        self.setMinimumHeight(400)

        self._init_ui()
        self._load_existing_values()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 说明文字
        info_label = QLabel("配置前置节点的输出数据，用于测试当前节点。\n")
        info_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(info_label)

        # 如果没有上游输出
        if not self.upstream_outputs:
            no_data_label = QLabel("该节点没有前置依赖，无需配置Mock数据。")
            no_data_label.setStyleSheet("color: #999; font-style: italic;")
            no_data_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(no_data_label)
        else:
            # 创建滚动区域
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)

            scroll_content = QWidget()
            scroll_layout = QVBoxLayout(scroll_content)
            scroll_layout.setSpacing(15)
            scroll_layout.setAlignment(Qt.AlignTop)

            # 为每个上游节点创建分组
            for upstream in self.upstream_outputs:
                group = self._create_node_group(upstream)
                scroll_layout.addWidget(group)

            scroll.setWidget(scroll_content)
            layout.addWidget(scroll)

        # 按钮区域
        button_layout = QHBoxLayout()

        # 自动生成按钮
        self.auto_gen_btn = QPushButton("🎲 自动生成Mock数据")
        self.auto_gen_btn.setToolTip("根据变量类型自动生成随机值")
        self.auto_gen_btn.clicked.connect(self._auto_generate)
        button_layout.addWidget(self.auto_gen_btn)

        button_layout.addStretch()

        # 确定和取消按钮
        self.ok_btn = QPushButton("确定")
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self._on_ok)
        button_layout.addWidget(self.ok_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def _create_node_group(self, upstream):
        """为单个上游节点创建输入组"""
        group = QGroupBox(f"{upstream['node_title']} ({upstream['node_type']})")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        form_layout = QFormLayout(group)
        form_layout.setSpacing(8)

        node_id = upstream['node_id']

        for var_name, var_def in upstream['outputs'].items():
            widget = self._create_variable_widget(var_name, var_def)
            form_layout.addRow(f"{var_def['label']} (${var_name}):", widget)
            self.widgets[f"{node_id}.{var_name}"] = {
                'widget': widget,
                'type': var_def['type'],
                'node_id': node_id,
                'var_name': var_name
            }

        return group

    def _create_variable_widget(self, var_name, var_def):
        """根据变量类型创建对应的输入控件"""
        var_type = var_def['type']

        if var_type == 'int':
            widget = QSpinBox()
            widget.setRange(-999999, 999999)
            widget.setValue(0)
        elif var_type == 'float':
            widget = QDoubleSpinBox()
            widget.setRange(-999999.99, 999999.99)
            widget.setDecimals(4)
            widget.setValue(0.0)
        elif var_type == 'bool':
            widget = QComboBox()
            widget.addItem("True", True)
            widget.addItem("False", False)
        elif var_type == 'string':
            widget = QLineEdit()
            widget.setPlaceholderText(f"输入{var_def['label']}...")
        else:
            widget = QLineEdit()
            widget.setPlaceholderText(f"输入{var_def['label']}...")

        return widget

    def _load_existing_values(self):
        """加载已存在的值"""
        for key, widget_info in self.widgets.items():
            value = self.existing_values.get(key)
            if value is None:
                continue

            widget = widget_info['widget']
            var_type = widget_info['type']

            if var_type == 'int':
                widget.setValue(int(value))
            elif var_type == 'float':
                widget.setValue(float(value))
            elif var_type == 'bool':
                index = 0 if value else 1
                widget.setCurrentIndex(index)
            elif var_type == 'string':
                widget.setText(str(value))
            else:
                widget.setText(str(value))

    def _auto_generate(self):
        """自动生成Mock数据"""
        for key, widget_info in self.widgets.items():
            widget = widget_info['widget']
            var_type = widget_info['type']

            if var_type == 'int':
                # 生成随机坐标或计数
                if 'x' in widget_info['var_name'].lower():
                    value = random.randint(100, 1800)
                elif 'y' in widget_info['var_name'].lower():
                    value = random.randint(100, 900)
                else:
                    value = random.randint(1, 100)
                widget.setValue(value)

            elif var_type == 'float':
                # 生成随机置信度
                if 'confidence' in widget_info['var_name'].lower():
                    value = round(random.uniform(0.8, 0.99), 4)
                else:
                    value = round(random.uniform(0, 100), 4)
                widget.setValue(value)

            elif var_type == 'bool':
                # 随机选择
                value = random.choice([True, False])
                widget.setCurrentIndex(0 if value else 1)

            elif var_type == 'string':
                # 生成示例字符串
                if 'hotkey' in widget_info['var_name'].lower():
                    value = "F6"
                elif 'key' in widget_info['var_name'].lower():
                    value = random.choice(['enter', 'space', 'tab', 'esc'])
                elif 'text' in widget_info['var_name'].lower():
                    value = "示例文本"
                elif 'expression' in widget_info['var_name'].lower():
                    value = "$found == True"
                elif 'loop' in widget_info['var_name'].lower():
                    value = "i"
                else:
                    value = f"mock_{widget_info['var_name']}"
                widget.setText(value)

    def _on_ok(self):
        """确定按钮点击"""
        self.mock_data = self._collect_values()
        self.accept()

    def _collect_values(self):
        """收集所有输入值"""
        values = {}

        for key, widget_info in self.widgets.items():
            widget = widget_info['widget']
            var_type = widget_info['type']
            var_name = widget_info['var_name']

            if var_type == 'int':
                value = widget.value()
            elif var_type == 'float':
                value = widget.value()
            elif var_type == 'bool':
                value = widget.currentData()
            elif var_type == 'string':
                value = widget.text()
            else:
                value = widget.text()

            # 使用变量名作为key，方便节点使用
            values[var_name] = value

        return values

    def get_mock_data(self):
        """获取配置的Mock数据"""
        return self.mock_data

    @staticmethod
    def get_mock_variables(parent, target_node_id, upstream_outputs, existing_values=None):
        """静态方法，显示对话框并返回结果
        Returns:
            (accepted, mock_data): 是否确认，Mock数据字典
        """
        dialog = MockDataDialog(parent, target_node_id, upstream_outputs, existing_values)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            return True, dialog.get_mock_data()
        else:
            return False, {}
