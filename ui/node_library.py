"""
节点库面板 - 显示可用节点列表，支持拖拽创建
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTreeWidget, QTreeWidgetItem, QPushButton, QMenu
)
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData, QByteArray
from PyQt5.QtGui import QColor, QBrush, QFont, QPixmap, QPainter
import json


# 节点输出定义 - 用于Mock数据生成
NODE_OUTPUTS = {
    "find_color": {
        "color_x": {"type": "int", "label": "找到颜色的X坐标"},
        "color_y": {"type": "int", "label": "找到颜色的Y坐标"},
        "found": {"type": "bool", "label": "是否找到"}
    },
    "condition": {
        "condition_met": {"type": "bool", "label": "条件结果"},
        "expression": {"type": "string", "label": "条件表达式"}
    },
    "loop": {
        "count": {"type": "int", "label": "循环次数"},
        "loop_var": {"type": "string", "label": "循环变量名"}
    },
    "mouse_move": {
        "x": {"type": "int", "label": "X坐标"},
        "y": {"type": "int", "label": "Y坐标"}
    },
    "mouse_click": {
        "button": {"type": "string", "label": "点击按钮"}
    },
    "key_press": {
        "key": {"type": "string", "label": "按键"}
    },
    "key_input": {
        "text": {"type": "string", "label": "输入文本"}
    },
    "delay": {
        "milliseconds": {"type": "int", "label": "延迟毫秒"}
    },
    "start_manual": {
        "started": {"type": "bool", "label": "是否已启动"}
    },
    "start_hotkey": {
        "hotkey": {"type": "string", "label": "热键"}
    },
    "break": {
        "break": {"type": "bool", "label": "是否跳出"}
    },
    "continue": {
        "continue": {"type": "bool", "label": "是否继续"}
    },
    "if_image": {
        "found": {"type": "bool", "label": "是否找到"},
        "find_x": {"type": "int", "label": "找到图片的X坐标"},
        "find_y": {"type": "int", "label": "找到图片的Y坐标"},
        "confidence": {"type": "float", "label": "匹配置信度"}
    }
}


def get_node_outputs(node_type):
    """获取节点类型的输出定义"""
    return NODE_OUTPUTS.get(node_type, {})


class DraggableTreeWidget(QTreeWidget):
    """支持自定义拖拽数据的树控件"""

    def mimeData(self, items):
        """自定义MIME数据"""
        mime_data = QMimeData()

        if items:
            item = items[0]
            node_data = item.data(0, Qt.UserRole)
            if node_data:
                mime_data.setText(json.dumps(node_data))

        return mime_data


class NodeLibraryPanel(QWidget):
    """节点库面板"""

    # 信号: 节点被拖拽
    node_dragged = pyqtSignal(str, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_node_types()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 搜索框
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索节点...")
        self.search_edit.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_edit)

        # 清除按钮
        clear_btn = QPushButton("×")
        clear_btn.setFixedSize(24, 24)
        clear_btn.setToolTip("清除搜索")
        clear_btn.clicked.connect(self._on_clear_search)
        search_layout.addWidget(clear_btn)

        layout.addLayout(search_layout)

        # 节点树
        self.tree = DraggableTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(15)
        self.tree.setAnimated(True)
        self.tree.setDragEnabled(True)
        self.tree.setDragDropMode(QTreeWidget.DragOnly)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)

        layout.addWidget(self.tree)

        # 底部信息
        self.info_label = QLabel("拖拽节点到画布")
        self.info_label.setStyleSheet("color: gray; font-size: 11px;")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

    def _load_node_types(self):
        """加载节点类型定义"""
        self.node_types = {
            "触发": [
                {
                    "type": "start_manual",
                    "name": "手动启动",
                    "icon": "▶️",
                    "desc": "用户点击运行按钮开始执行",
                    "color": "#2196F3",
                    "params": {}
                },
                {
                    "type": "start_hotkey",
                    "name": "热键启动",
                    "icon": "⌨️",
                    "desc": "按下指定热键启动流程",
                    "color": "#2196F3",
                    "params": {
                        "hotkey": {"type": "string", "default": "F6", "label": "热键"}
                    }
                },
                {
                    "type": "async_listener",
                    "name": "异步监听",
                    "icon": "👁️",
                    "desc": "并行监控屏幕，检测到图片或颜色时触发，可暂停或停止主流程",
                    "color": "#E91E63",
                    "ports": {"inputs": 0, "outputs": 1},
                    "params": {
                        "listen_type": {"type": "select", "default": "image", "label": "监听类型", "options": ["image", "color"]},
                        "image_path": {"type": "file", "default": "", "label": "图片路径（image类型）"},
                        "threshold": {"type": "float", "default": 0.8, "label": "匹配阈值", "min": 0.0, "max": 1.0},
                        "color": {"type": "color", "default": "#FF0000", "label": "目标颜色（color类型）"},
                        "color_tolerance": {"type": "int", "default": 10, "label": "颜色容差", "min": 0, "max": 255},
                        "region": {"type": "region", "default": [0, 0, 1920, 1080], "label": "监听区域"},
                        "interval": {"type": "int", "default": 500, "label": "检测间隔(毫秒)", "min": 50, "max": 10000},
                        "action_on_main": {"type": "select", "default": "pause", "label": "触发时对主流程的操作", "options": ["pause", "stop"]},
                        "cooldown": {"type": "int", "default": 2000, "label": "触发后冷却(毫秒)", "min": 0, "max": 60000}
                    }
                }
            ],
            "动作": [
                {
                    "type": "mouse_move",
                    "name": "鼠标移动",
                    "icon": "🖱️",
                    "desc": "移动鼠标到指定坐标",
                    "color": "#4CAF50",
                    "params": {
                        "x": {"type": "string", "default": "0", "label": "X坐标", "desc": "支持数字或变量如 $find_x"},
                        "y": {"type": "string", "default": "0", "label": "Y坐标", "desc": "支持数字或变量如 $find_y"}
                    }
                },
                {
                    "type": "mouse_click",
                    "name": "鼠标点击",
                    "icon": "🖱️",
                    "desc": "模拟鼠标点击",
                    "color": "#4CAF50",
                    "params": {
                        "button": {"type": "select", "default": "left", "label": "按钮", "options": ["left", "right", "middle"]},
                        "x": {"type": "int", "default": None, "label": "X坐标(空表示当前位置)", "optional": True},
                        "y": {"type": "int", "default": None, "label": "Y坐标(空表示当前位置)", "optional": True},
                        "random_offset": {"type": "int", "default": 0, "label": "随机偏移范围", "min": 0, "max": 100, "desc": "在坐标周围随机偏移的像素范围，0表示不偏移"}
                    }
                },
                {
                    "type": "key_press",
                    "name": "键盘按键",
                    "icon": "⌨️",
                    "desc": "模拟按下单个按键",
                    "color": "#4CAF50",
                    "params": {
                        "key": {"type": "string", "default": "enter", "label": "按键"}
                    }
                },
                {
                    "type": "key_input",
                    "name": "键盘输入",
                    "icon": "⌨️",
                    "desc": "模拟输入文本",
                    "color": "#4CAF50",
                    "params": {
                        "text": {"type": "string", "default": "", "label": "文本"}
                    }
                },
                {
                    "type": "delay",
                    "name": "延时",
                    "icon": "⏱️",
                    "desc": "等待指定时间",
                    "color": "#4CAF50",
                    "params": {
                        "milliseconds": {"type": "int", "default": 1000, "label": "毫秒"}
                    }
                }
            ],
            "图像": [
                {
                    "type": "if_image",
                    "name": "找图分支",
                    "icon": "🖼️",
                    "desc": "查找图片并根据结果分支，找到后输出坐标变量$find_x/$find_y和$found",
                    "color": "#FF9800",
                    "params": {
                        "image_path": {"type": "file", "default": "", "label": "图片路径"},
                        "threshold": {"type": "float", "default": 0.8, "label": "相似度阈值", "min": 0.0, "max": 1.0},
                        "region": {"type": "region", "default": [0, 0, 1920, 1080], "label": "查找区域"},
                        "true_label": {"type": "string", "default": "找到", "label": "找到分支标签"},
                        "false_label": {"type": "string", "default": "未找到", "label": "未找到分支标签"},
                        "auto_move": {"type": "boolean", "default": True, "label": "找到后自动移动鼠标"},
                        "offset_x": {"type": "int", "default": 0, "label": "X偏移"},
                        "offset_y": {"type": "int", "default": 0, "label": "Y偏移"},
                        "random_offset": {"type": "int", "default": 7, "min": 0, "max": 100, "label": "随机偏移范围"},
                        "auto_click": {"type": "boolean", "default": True, "label": "找到后自动点击"},
                        "click_button": {"type": "select", "default": "left", "label": "点击按钮", "options": ["left", "right", "double"]},
                        "click_delay": {"type": "int", "default": 0, "min": 0, "label": "点击前延时(毫秒)"}
                    },
                    "ports": {
                        "inputs": 1,
                        "outputs": 2
                    }
                },
                {
                    "type": "find_color",
                    "name": "找色",
                    "icon": "🎨",
                    "desc": "在指定区域查找颜色",
                    "color": "#9C27B0",
                    "params": {
                        "color": {"type": "color", "default": "#FF0000", "label": "颜色"},
                        "tolerance": {"type": "int", "default": 10, "label": "容差"},
                        "region": {"type": "region", "default": [0, 0, 1920, 1080], "label": "查找区域"}
                    }
                }
            ],
            "逻辑": [
                {
                    "type": "condition",
                    "name": "条件判断",
                    "icon": "🔀",
                    "desc": "根据条件执行不同分支，支持变量和比较运算符",
                    "color": "#FF9800",
                    "params": {
                        "condition": {"type": "string", "default": "$found == True", "label": "条件表达式", "desc": "例如: $found == True, $count > 5, $x <= 100"},
                        "true_label": {"type": "string", "default": "是", "label": "真分支标签"},
                        "false_label": {"type": "string", "default": "否", "label": "假分支标签"}
                    },
                    "ports": {
                        "inputs": 1,
                        "outputs": 2
                    }
                },
                {
                    "type": "loop",
                    "name": "循环",
                    "icon": "🔄",
                    "desc": "重复执行循环体内的节点",
                    "color": "#FF9800",
                    "params": {
                        "count": {"type": "int", "default": 3, "min": 0, "max": 9999, "label": "循环次数（0=无限）"},
                        "loop_var": {"type": "string", "default": "i", "label": "循环变量名", "desc": "可在循环体内使用 $i, $i+1 等"}
                    },
                    "ports": {
                        "inputs": 1,
                        "outputs": 2
                    }
                },
                {
                    "type": "break",
                    "name": "跳出循环",
                    "icon": "⏏️",
                    "desc": "立即退出当前循环",
                    "color": "#FF5722",
                    "params": {},
                    "ports": {
                        "inputs": 1,
                        "outputs": 1
                    }
                },
                {
                    "type": "continue",
                    "name": "继续循环",
                    "icon": "⏭️",
                    "desc": "跳过当前迭代，进入下一次循环",
                    "color": "#FF5722",
                    "params": {},
                    "ports": {
                        "inputs": 1,
                        "outputs": 1
                    }
                },
            ]
        }

        self._build_tree()

    def _build_tree(self):
        """构建节点树"""
        self.tree.clear()

        for category, nodes in self.node_types.items():
            # 创建分类项
            category_item = QTreeWidgetItem(self.tree)
            category_item.setText(0, f"{self._get_category_icon(category)} {category}")
            category_item.setFlags(category_item.flags() & ~Qt.ItemIsDragEnabled)

            # 设置分类字体
            font = QFont()
            font.setBold(True)
            category_item.setFont(0, font)

            # 创建节点项
            for node in nodes:
                node_item = QTreeWidgetItem(category_item)
                node_item.setText(0, f"{node['icon']} {node['name']}")
                node_item.setToolTip(0, node['desc'])
                node_item.setData(0, Qt.UserRole, node)

                # 设置颜色指示
                color = QColor(node['color'])
                node_item.setBackground(0, QBrush(color.lighter(180)))

            # 展开分类
            category_item.setExpanded(True)

    def _get_category_icon(self, category):
        """获取分类图标"""
        icons = {
            "触发": "⚡",
            "动作": "⚙️",
            "图像": "🖼️",
            "逻辑": "🔀"
        }
        return icons.get(category, "📦")

    def _on_search(self, text):
        """搜索过滤"""
        text = text.lower()

        for i in range(self.tree.topLevelItemCount()):
            category_item = self.tree.topLevelItem(i)
            has_visible_child = False

            for j in range(category_item.childCount()):
                node_item = category_item.child(j)
                node_data = node_item.data(0, Qt.UserRole)

                if text in node_data['name'].lower() or text in node_data['desc'].lower():
                    node_item.setHidden(False)
                    has_visible_child = True
                else:
                    node_item.setHidden(True)

            category_item.setHidden(not has_visible_child)

    def _on_clear_search(self):
        """清除搜索"""
        self.search_edit.clear()
        for i in range(self.tree.topLevelItemCount()):
            category_item = self.tree.topLevelItem(i)
            category_item.setHidden(False)
            for j in range(category_item.childCount()):
                category_item.child(j).setHidden(False)

    def _on_item_double_clicked(self, item):
        """双击节点项"""
        node_data = item.data(0, Qt.UserRole)
        if node_data:
            self.node_dragged.emit(node_data['type'], node_data)

    def _on_context_menu(self, position):
        """右键菜单"""
        item = self.tree.itemAt(position)
        if not item:
            return

        node_data = item.data(0, Qt.UserRole)
        if not node_data:
            return

        menu = QMenu()

        add_action = menu.addAction(f"添加到画布")
        add_action.triggered.connect(lambda: self.node_dragged.emit(node_data['type'], node_data))

        menu.addSeparator()

        info_action = menu.addAction("节点信息")
        info_action.triggered.connect(lambda: self._show_node_info(node_data))

        menu.exec_(self.tree.viewport().mapToGlobal(position))

    def _show_node_info(self, node_data):
        """显示节点信息"""
        from PyQt5.QtWidgets import QMessageBox

        params_text = "\n".join([
            f"  • {p['label']} ({p['type']})"
            for p in node_data['params'].values()
        ]) or "  (无参数)"

        QMessageBox.information(
            self,
            f"节点信息 - {node_data['name']}",
            f"<b>{node_data['icon']} {node_data['name']}</b><br>"
            f"<br>"
            f"<b>描述:</b> {node_data['desc']}<br>"
            f"<br>"
            f"<b>参数:</b><br>{params_text}"
        )

    def get_node_definition(self, node_type):
        """获取节点定义"""
        for category, nodes in self.node_types.items():
            for node in nodes:
                if node['type'] == node_type:
                    return node
        return None
