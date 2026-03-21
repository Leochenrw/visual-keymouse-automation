"""
主窗口 - 应用程序主容器
"""
import os

from PyQt5.QtWidgets import (
    QMainWindow, QDockWidget, QToolBar, QStatusBar,
    QAction, QMessageBox, QFileDialog, QWidget, QVBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence, QIcon

from .node_library import NodeLibraryPanel
from .node_canvas import NodeCanvas
from .properties_panel import PropertiesPanel
from .log_panel import LogPanel
from .tutorial_tooltip import TutorialTooltip
from engine import WorkflowEngine

# 默认脚本目录
_SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
os.makedirs(_SCRIPTS_DIR, exist_ok=True)

# 教程步骤定义
TUTORIAL_STEPS = [
    {
        "title": "欢迎使用",
        "description": "欢迎使用可视化键鼠自动化编辑器！本教程将引导您了解基础操作，帮助您快速上手创建自动化工作流。"
    },
    {
        "title": "节点库",
        "description": "左侧是节点库面板，包含所有可用的节点类型。节点分为触发器、动作、图像和逻辑四大类。"
    },
    {
        "title": "添加节点",
        "description": "从节点库中找到「手动启动」节点，按住鼠标左键拖拽到中央画布区域，然后松开即可创建节点。"
    },
    {
        "title": "连接节点",
        "description": "节点左侧是输入端口，右侧是输出端口。从一个输出端口拖拽连线到另一个输入端口，即可建立执行顺序。"
    },
    {
        "title": "鼠标移动节点",
        "description": "尝试添加一个「鼠标移动」节点。设置目标坐标(X, Y)，运行时鼠标会移动到指定位置。"
    },
    {
        "title": "鼠标点击节点",
        "description": "添加「鼠标点击」节点，选择左键、右键或中键。这是自动化操作中最常用的动作之一。"
    },
    {
        "title": "属性面板",
        "description": "选中节点后，右侧面板会显示该节点的可配置参数。您可以在这里修改节点标题和各种设置。"
    },
    {
        "title": "键盘输入",
        "description": "使用「键盘输入」节点可以模拟文字输入，「按键」节点可以模拟单个按键或组合键如 Ctrl+C。"
    },
    {
        "title": "延时节点",
        "description": "在两个动作之间添加「延时」节点，让工作流暂停指定时间（毫秒），等待界面响应。"
    },
    {
        "title": "图像查找",
        "description": "「找图」节点可以在屏幕上搜索指定图片，如果找到会返回坐标，用于识别界面元素位置。"
    },
    {
        "title": "条件判断节点",
        "description": "「条件」节点有两个输出端口：<br>• <b>端口0（上）</b> = 真分支（条件为是）<br>• <b>端口1（下）</b> = 假分支（条件为否）<br><br>根据条件表达式的结果决定执行哪个分支。"
    },
    {
        "title": "条件表达式语法",
        "description": "条件表达式支持以下语法：<br>• <code>$变量名 == 值</code> - 等于比较<br>• <code>$变量名 > 数字</code> - 大于<br>• <code>$变量名 < 数字</code> - 小于<br>• <code>$变量名 >= 数字</code> - 大于等于<br>• <code>$变量名 != 值</code> - 不等于<br><br>常用示例：<code>$found == True</code>、<code>$count > 5</code>"
    },
    {
        "title": "条件判断实战",
        "description": "典型场景：找图节点 → 条件判断节点<br><br>1. 找图节点搜索界面元素<br>2. 条件表达式设为 <code>$found == True</code><br>3. 真分支连接「鼠标点击」节点（点击图片）<br>4. 假分支可选择「延时」后重试或跳过<br><br>这样只有找到图片才会执行点击操作。"
    },
    {
        "title": "循环节点",
        "description": "「循环」节点有两个输出端口：<br>• <b>端口0（上）</b> = 循环体（重复执行的内容）<br>• <b>端口1（下）</b> = 循环结束后继续<br><br>参数说明：<br>• <b>count</b> - 循环次数<br>• <b>loop_var</b> - 循环变量名（如 i）"
    },
    {
        "title": "循环变量使用",
        "description": "在循环体内可以使用循环变量引用当前迭代次数：<br><br>• <code>$i</code> - 从 0 开始（0, 1, 2, 3...）<br>• <code>$i_1</code> - 从 1 开始（1, 2, 3, 4...）<br><br>示例：设置 loop_var 为 i，循环5次<br>第1次 $i=0, $i_1=1<br>第2次 $i=1, $i_1=2<br>...<br>第5次 $i=4, $i_1=5"
    },
    {
        "title": "break 与 continue",
        "description": "在循环体内可以控制流程：<br><br>• <b>跳出循环 (break)</b> - 立即退出整个循环，从端口1（下）继续执行<br>• <b>继续循环 (continue)</b> - 跳过本次循环剩余内容，进入下一次迭代<br><br><b>注意：</b>这两个节点<b>必须</b>放在循环体内使用，否则执行会报错。"
    },
    {
        "title": "逻辑节点综合应用",
        "description": "组合示例：循环找图直到找到<br><br>1. 「循环」节点（count=10，loop_var=i）<br>2. 循环体连接「找图」节点<br>3. 找图后连接「条件」节点（表达式：<code>$found == True</code>）<br>4. 真分支：「鼠标移动」→「鼠标点击」→「跳出循环」<br>5. 假分支：「延时」500ms → 自然结束（进入下一次循环）<br><br>这样最多尝试10次找图，找到就点击并停止。"
    },
    {
        "title": "运行工作流",
        "description": "按 F5 键或点击工具栏的「运行」按钮开始执行。工作流会在独立线程中运行，不会阻塞界面。"
    },
    {
        "title": "保存与打开",
        "description": "工作流可以保存为 JSON 文件（Ctrl+S），之后可以随时打开（Ctrl+O）继续编辑或运行。"
    },
    {
        "title": "开始使用",
        "description": "恭喜您完成教程！现在您可以开始创建自己的自动化工作流了。遇到问题可随时通过帮助菜单重新查看本教程，或加载示例工作流学习。"
    }
]

# 示例工作流数据
EXAMPLE_WORKFLOWS = {
    "simple_loop": {
        "name": "示例1: 简单循环",
        "description": "循环5次鼠标点击，演示loop基础用法",
        "data": {
            "nodes": [
                {
                    "id": "start_001",
                    "type": "start_manual",
                    "title": "手动启动",
                    "x": 100,
                    "y": 200,
                    "params": {},
                    "ports": {"inputs": 0, "outputs": 1}
                },
                {
                    "id": "loop_001",
                    "type": "loop",
                    "title": "循环5次",
                    "x": 300,
                    "y": 200,
                    "params": {
                        "count": {"type": "int", "default": 5, "label": "循环次数", "value": 5},
                        "loop_var": {"type": "string", "default": "i", "label": "循环变量", "value": "i"}
                    },
                    "ports": {"inputs": 1, "outputs": 2}
                },
                {
                    "id": "click_001",
                    "type": "mouse_click",
                    "title": "鼠标点击",
                    "x": 550,
                    "y": 150,
                    "params": {
                        "button": {"type": "select", "default": "left", "label": "按钮", "value": "left"}
                    },
                    "ports": {"inputs": 1, "outputs": 1}
                },
                {
                    "id": "delay_001",
                    "type": "delay",
                    "title": "延时500ms",
                    "x": 550,
                    "y": 250,
                    "params": {
                        "duration": {"type": "int", "default": 1000, "label": "延时(ms)", "value": 500}
                    },
                    "ports": {"inputs": 1, "outputs": 1}
                },
                {
                    "id": "end_001",
                    "type": "delay",
                    "title": "循环结束",
                    "x": 800,
                    "y": 300,
                    "params": {
                        "duration": {"type": "int", "default": 1000, "label": "延时(ms)", "value": 100}
                    },
                    "ports": {"inputs": 1, "outputs": 1}
                }
            ],
            "connections": [
                {"from": "start_001", "to": "loop_001", "from_port": 0, "to_port": 0},
                {"from": "loop_001", "to": "click_001", "from_port": 0, "to_port": 0},
                {"from": "click_001", "to": "delay_001", "from_port": 0, "to_port": 0},
                {"from": "delay_001", "to": "loop_001", "from_port": 0, "to_port": 0},
                {"from": "loop_001", "to": "end_001", "from_port": 1, "to_port": 0}
            ]
        }
    },
    "condition_demo": {
        "name": "示例2: 条件判断",
        "description": "延时后条件判断，演示condition双出口连法",
        "data": {
            "nodes": [
                {
                    "id": "start_002",
                    "type": "start_manual",
                    "title": "手动启动",
                    "x": 100,
                    "y": 200,
                    "params": {},
                    "ports": {"inputs": 0, "outputs": 1}
                },
                {
                    "id": "delay_002",
                    "type": "delay",
                    "title": "等待2秒",
                    "x": 300,
                    "y": 200,
                    "params": {
                        "duration": {"type": "int", "default": 1000, "label": "延时(ms)", "value": 2000}
                    },
                    "ports": {"inputs": 1, "outputs": 1}
                },
                {
                    "id": "condition_002",
                    "type": "condition",
                    "title": "条件判断",
                    "x": 550,
                    "y": 200,
                    "params": {
                        "expression": {"type": "string", "default": "", "label": "条件表达式", "value": "$count > 3"}
                    },
                    "ports": {"inputs": 1, "outputs": 2}
                },
                {
                    "id": "click_yes",
                    "type": "mouse_click",
                    "title": "是-左键点击",
                    "x": 800,
                    "y": 150,
                    "params": {
                        "button": {"type": "select", "default": "left", "label": "按钮", "value": "left"}
                    },
                    "ports": {"inputs": 1, "outputs": 1}
                },
                {
                    "id": "click_no",
                    "type": "mouse_click",
                    "title": "否-右键点击",
                    "x": 800,
                    "y": 280,
                    "params": {
                        "button": {"type": "select", "default": "left", "label": "按钮", "value": "right"}
                    },
                    "ports": {"inputs": 1, "outputs": 1}
                }
            ],
            "connections": [
                {"from": "start_002", "to": "delay_002", "from_port": 0, "to_port": 0},
                {"from": "delay_002", "to": "condition_002", "from_port": 0, "to_port": 0},
                {"from": "condition_002", "to": "click_yes", "from_port": 0, "to_port": 0},
                {"from": "condition_002", "to": "click_no", "from_port": 1, "to_port": 0}
            ]
        }
    },
    "image_loop_condition": {
        "name": "示例3: 找图+条件+循环",
        "description": "循环找图直到找到为止，综合示例",
        "data": {
            "nodes": [
                {
                    "id": "start_003",
                    "type": "start_manual",
                    "title": "手动启动",
                    "x": 50,
                    "y": 250,
                    "params": {},
                    "ports": {"inputs": 0, "outputs": 1}
                },
                {
                    "id": "loop_003",
                    "type": "loop",
                    "title": "最多找10次",
                    "x": 250,
                    "y": 250,
                    "params": {
                        "count": {"type": "int", "default": 10, "label": "循环次数", "value": 10},
                        "loop_var": {"type": "string", "default": "i", "label": "循环变量", "value": "i"}
                    },
                    "ports": {"inputs": 1, "outputs": 2}
                },
                {
                    "id": "find_img_003",
                    "type": "if_image",
                    "title": "查找目标图片",
                    "x": 500,
                    "y": 200,
                    "params": {
                        "image_path": {"type": "file", "default": "", "label": "图片路径", "value": ""},
                        "threshold": {"type": "float", "default": 0.8, "label": "置信度", "value": 0.8},
                        "region": {"type": "region", "default": [0, 0, 1920, 1080], "label": "搜索区域", "value": [0, 0, 1920, 1080]}
                    },
                    "ports": {"inputs": 1, "outputs": 1}
                },
                {
                    "id": "condition_003",
                    "type": "condition",
                    "title": "找到了？",
                    "x": 750,
                    "y": 200,
                    "params": {
                        "expression": {"type": "string", "default": "", "label": "条件表达式", "value": "$found == True"}
                    },
                    "ports": {"inputs": 1, "outputs": 2}
                },
                {
                    "id": "move_003",
                    "type": "mouse_move",
                    "title": "移动到图片位置",
                    "x": 1000,
                    "y": 120,
                    "params": {
                        "x": {"type": "int", "default": 0, "label": "X坐标", "value": 0, "optional": True},
                        "y": {"type": "int", "default": 0, "label": "Y坐标", "value": 0, "optional": True},
                        "use_var_x": {"type": "string", "default": "", "label": "使用变量X", "value": "$find_x"},
                        "use_var_y": {"type": "string", "default": "", "label": "使用变量Y", "value": "$find_y"}
                    },
                    "ports": {"inputs": 1, "outputs": 1}
                },
                {
                    "id": "click_003",
                    "type": "mouse_click",
                    "title": "点击图片",
                    "x": 1200,
                    "y": 120,
                    "params": {
                        "button": {"type": "select", "default": "left", "label": "按钮", "value": "left"}
                    },
                    "ports": {"inputs": 1, "outputs": 1}
                },
                {
                    "id": "break_003",
                    "type": "break_loop",
                    "title": "找到，退出循环",
                    "x": 1400,
                    "y": 120,
                    "params": {},
                    "ports": {"inputs": 1, "outputs": 1}
                },
                {
                    "id": "delay_retry",
                    "type": "delay",
                    "title": "未找到，等待500ms",
                    "x": 1000,
                    "y": 280,
                    "params": {
                        "duration": {"type": "int", "default": 1000, "label": "延时(ms)", "value": 500}
                    },
                    "ports": {"inputs": 1, "outputs": 1}
                },
                {
                    "id": "continue_003",
                    "type": "continue_loop",
                    "title": "继续下一次循环",
                    "x": 1200,
                    "y": 280,
                    "params": {},
                    "ports": {"inputs": 1, "outputs": 1}
                },
                {
                    "id": "end_003",
                    "type": "delay",
                    "title": "循环结束/完成",
                    "x": 1600,
                    "y": 350,
                    "params": {
                        "duration": {"type": "int", "default": 1000, "label": "延时(ms)", "value": 100}
                    },
                    "ports": {"inputs": 1, "outputs": 1}
                }
            ],
            "connections": [
                {"from": "start_003", "to": "loop_003", "from_port": 0, "to_port": 0},
                {"from": "loop_003", "to": "find_img_003", "from_port": 0, "to_port": 0},
                {"from": "find_img_003", "to": "condition_003", "from_port": 0, "to_port": 0},
                {"from": "condition_003", "to": "move_003", "from_port": 0, "to_port": 0},
                {"from": "move_003", "to": "click_003", "from_port": 0, "to_port": 0},
                {"from": "click_003", "to": "break_003", "from_port": 0, "to_port": 0},
                {"from": "condition_003", "to": "delay_retry", "from_port": 1, "to_port": 0},
                {"from": "delay_retry", "to": "continue_003", "from_port": 0, "to_port": 0},
                {"from": "break_003", "to": "end_003", "from_port": 0, "to_port": 0},
                {"from": "loop_003", "to": "end_003", "from_port": 1, "to_port": 0}
            ]
        }
    }
}


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

        # 教程相关
        self.tutorial_tooltip = None
        self.tutorial_current_step = 0

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

        tutorial_action = QAction("新手引导(&T)", self)
        tutorial_action.setShortcut("F1")
        tutorial_action.triggered.connect(self._on_start_tutorial)
        help_menu.addAction(tutorial_action)

        help_menu.addSeparator()

        # 加载示例工作流子菜单
        examples_menu = help_menu.addMenu("加载示例工作流(&E)")

        example1_action = QAction("示例1: 简单循环", self)
        example1_action.triggered.connect(lambda: self._on_load_example("simple_loop"))
        examples_menu.addAction(example1_action)

        example2_action = QAction("示例2: 条件判断", self)
        example2_action.triggered.connect(lambda: self._on_load_example("condition_demo"))
        examples_menu.addAction(example2_action)

        example3_action = QAction("示例3: 找图+条件+循环", self)
        example3_action.triggered.connect(lambda: self._on_load_example("image_loop_condition"))
        examples_menu.addAction(example3_action)

        help_menu.addSeparator()

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
            node = self.canvas.nodes[node_id]
            node.params = node_data.get('params', {})

            # 更新节点标题（如果发生了变化）
            new_title = node_data.get('title', '')
            if new_title and new_title != node.title:
                node.set_title(new_title)

            self.canvas.canvas_changed.emit()
            self.log_panel.log_info(f"节点 '{new_title}' 参数已更新")

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

        # 新建后重置历史
        self.canvas._history = []
        self.canvas._history_index = -1
        self.canvas._push_history()

    def _on_open(self):
        """打开工作流"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开工作流", _SCRIPTS_DIR, "JSON文件 (*.json);;所有文件 (*.*)"
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

                    # 使用保存的标题（如果有）
                    saved_title = node_data.get('title')
                    if saved_title:
                        node_def_copy['name'] = saved_title

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

            # 以加载后的状态为历史起点，清除旧的历史栈
            self.canvas._history = []
            self.canvas._history_index = -1
            self.canvas._push_history()

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
        default_path = os.path.join(_SCRIPTS_DIR, "未命名.json")
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存工作流", default_path, "JSON文件 (*.json);;所有文件 (*.*)"
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

    def _on_load_example(self, example_id):
        """加载示例工作流"""
        if example_id not in EXAMPLE_WORKFLOWS:
            self.log_panel.log_error(f"未知示例: {example_id}")
            return

        example = EXAMPLE_WORKFLOWS[example_id]

        # 询问是否保存当前工作流
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

        # 清空当前画布并加载示例
        self.canvas.clear_canvas()

        # 使用现有的文件加载逻辑
        workflow_data = example["data"]

        # 加载节点
        from .node_library import NodeLibraryPanel
        library = NodeLibraryPanel()

        node_id_map = {}

        for node_data in workflow_data.get("nodes", []):
            node_type = node_data.get("type")
            node_def = library.get_node_definition(node_type)

            if node_def:
                import copy
                node_def_copy = copy.deepcopy(node_def)

                # 使用示例中的标题
                saved_title = node_data.get("title")
                if saved_title:
                    node_def_copy["name"] = saved_title

                # 更新参数值
                saved_params = node_data.get("params", {})
                for key, param_data in saved_params.items():
                    if key in node_def_copy["params"]:
                        if isinstance(param_data, dict) and "value" in param_data:
                            node_def_copy["params"][key]["value"] = param_data["value"]
                        else:
                            node_def_copy["params"][key]["value"] = param_data

                # 创建节点
                x = node_data.get("x", 0)
                y = node_data.get("y", 0)
                new_node = self.canvas.add_node(node_def_copy, x + 80, y + 40)
                node_id_map[node_data.get("id")] = new_node.node_id
            else:
                self.log_panel.log_warning(f"未找到节点类型定义: {node_type}")

        # 加载连线
        from .node_canvas import ConnectionItem
        for conn_data in workflow_data.get("connections", []):
            from_id = conn_data.get("from")
            to_id = conn_data.get("to")
            from_port_idx = conn_data.get("from_port", 0)
            to_port_idx = conn_data.get("to_port", 0)

            new_from_id = node_id_map.get(from_id)
            new_to_id = node_id_map.get(to_id)

            if new_from_id and new_to_id:
                from_node = self.canvas.nodes.get(new_from_id)
                to_node = self.canvas.nodes.get(new_to_id)

                if from_node and to_node:
                    from_port = None
                    to_port = None

                    if hasattr(from_node, "output_ports") and from_port_idx < len(from_node.output_ports):
                        from_port = from_node.output_ports[from_port_idx]
                    elif from_port_idx == 0 and hasattr(from_node, "output_port"):
                        from_port = from_node.output_port

                    if hasattr(to_node, "input_ports") and to_port_idx < len(to_node.input_ports):
                        to_port = to_node.input_ports[to_port_idx]
                    elif to_port_idx == 0 and hasattr(to_node, "input_port"):
                        to_port = to_node.input_port

                    if from_port and to_port:
                        conn = ConnectionItem(
                            from_port, to_port,
                            start_port_index=from_port_idx,
                            end_port_index=to_port_idx
                        )
                        conn.update_path()
                        self.canvas.scene.addItem(conn)
                        self.canvas.connections.append(conn)

                        if hasattr(from_port, "connections"):
                            from_port.connections.append(conn)
                        if hasattr(to_port, "connections"):
                            to_port.connections.append(conn)

        self.current_file = None
        self.is_modified = True
        self._update_title()
        self.log_panel.log_info(f"已加载示例工作流: {example['name']} - {example['description']}")

        # 以加载后的状态为历史起点
        self.canvas._history = []
        self.canvas._history_index = -1
        self.canvas._push_history()

    # ── 教程相关方法 ──────────────────────────────────────────

    def _on_start_tutorial(self):
        """开始新手引导"""
        self.tutorial_current_step = 0
        self._show_tutorial_step()
        self.log_panel.log_info("开始新手引导教程")

    def _show_tutorial_step(self):
        """显示当前教程步骤"""
        if not TUTORIAL_STEPS:
            return

        # 创建或复用教程弹窗
        if self.tutorial_tooltip is None:
            self.tutorial_tooltip = TutorialTooltip(self)
            self.tutorial_tooltip.next_requested.connect(self._on_tutorial_next)
            self.tutorial_tooltip.prev_requested.connect(self._on_tutorial_prev)
            self.tutorial_tooltip.skip_requested.connect(self._on_tutorial_skip)

        # 更新内容
        step_data = TUTORIAL_STEPS[self.tutorial_current_step]
        self.tutorial_tooltip.set_step(
            self.tutorial_current_step,
            len(TUTORIAL_STEPS),
            step_data["title"],
            step_data["description"]
        )

        # 显示弹窗（使用默认位置）
        if not self.tutorial_tooltip.isVisible():
            self.tutorial_tooltip.place_default(self.geometry())
            self.tutorial_tooltip.show()

    def _on_tutorial_next(self):
        """教程下一步"""
        if self.tutorial_current_step < len(TUTORIAL_STEPS) - 1:
            self.tutorial_current_step += 1
            self._show_tutorial_step()
        else:
            # 最后一步点击完成，关闭教程
            self._on_tutorial_skip()

    def _on_tutorial_prev(self):
        """教程上一步"""
        if self.tutorial_current_step > 0:
            self.tutorial_current_step -= 1
            self._show_tutorial_step()

    def _on_tutorial_skip(self):
        """跳过/关闭教程"""
        if self.tutorial_tooltip:
            self.tutorial_tooltip.close()
            self.tutorial_tooltip = None
        self.log_panel.log_info("退出新手引导")

    def closeEvent(self, event):
        """关闭事件"""
        # 关闭教程弹窗
        if self.tutorial_tooltip:
            self.tutorial_tooltip.close()
            self.tutorial_tooltip = None

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
