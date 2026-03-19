"""
TutorialTooltip - 新手引导弹窗组件
"""
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QWidget, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QSettings
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush


class DotIndicator(QWidget):
    """步骤圆点指示器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._total = 1
        self._current = 0
        self.setFixedHeight(16)

    def set_state(self, current: int, total: int):
        self._current = current
        self._total = total
        dot_width = max(total * 20, 20)
        self.setFixedWidth(dot_width)
        self.update()

    def paintEvent(self, event):
        if self._total <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        dot_r = 5
        spacing = 14
        total_w = self._total * spacing - (spacing - dot_r * 2)
        x = (self.width() - total_w) / 2
        y = self.height() / 2

        for i in range(self._total):
            if i == self._current:
                painter.setBrush(QBrush(QColor("#4A9EFF")))
            else:
                painter.setBrush(QBrush(QColor("#555566")))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(x), int(y - dot_r), dot_r * 2, dot_r * 2)
            x += spacing


class TutorialTooltip(QFrame):
    """新手引导步骤弹窗"""

    next_requested = pyqtSignal()
    prev_requested = pyqtSignal()
    skip_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self._drag_pos = None
        self._current_step = 0
        self._total_steps = 1

        self._build_ui()
        self._apply_style()
        self._restore_position()

    def _build_ui(self):
        self.setFixedWidth(380)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        # 顶部：步骤标签
        self.step_label = QLabel("步骤 1 / 1")
        self.step_label.setObjectName("stepLabel")

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("separator")

        # 标题
        self.title_label = QLabel("标题")
        self.title_label.setObjectName("titleLabel")
        self.title_label.setWordWrap(True)

        # 说明文字
        self.desc_label = QLabel("描述")
        self.desc_label.setObjectName("descLabel")
        self.desc_label.setWordWrap(True)
        self.desc_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        # 圆点指示器（居中）
        dot_row = QHBoxLayout()
        dot_row.setContentsMargins(0, 4, 0, 4)
        self.dot_indicator = DotIndicator()
        dot_row.addStretch()
        dot_row.addWidget(self.dot_indicator)
        dot_row.addStretch()

        # 按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.prev_btn = QPushButton("上一步")
        self.prev_btn.setObjectName("prevBtn")
        self.prev_btn.setFixedHeight(30)
        self.prev_btn.clicked.connect(self.prev_requested)

        self.skip_btn = QPushButton("跳过教程")
        self.skip_btn.setObjectName("skipBtn")
        self.skip_btn.setFixedHeight(30)
        self.skip_btn.clicked.connect(self.skip_requested)

        self.next_btn = QPushButton("下一步 →")
        self.next_btn.setObjectName("nextBtn")
        self.next_btn.setFixedHeight(30)
        self.next_btn.clicked.connect(self.next_requested)

        btn_row.addWidget(self.prev_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.skip_btn)
        btn_row.addWidget(self.next_btn)

        root.addWidget(self.step_label)
        root.addWidget(sep)
        root.addWidget(self.title_label)
        root.addWidget(self.desc_label)
        root.addLayout(dot_row)
        root.addLayout(btn_row)

    def _apply_style(self):
        self.setStyleSheet("""
            TutorialTooltip {
                background-color: #2B2B3B;
                border: 1px solid #4A4A6A;
                border-radius: 8px;
            }
            QLabel#stepLabel {
                color: #8888AA;
                font-size: 12px;
            }
            QFrame#separator {
                background-color: #3D3D55;
                max-height: 1px;
                border: none;
            }
            QLabel#titleLabel {
                color: #E0E0F0;
                font-size: 14px;
                font-weight: bold;
            }
            QLabel#descLabel {
                color: #B0B0C8;
                font-size: 13px;
                line-height: 1.5;
            }
            QPushButton {
                border-radius: 4px;
                padding: 0 12px;
                font-size: 13px;
            }
            QPushButton#prevBtn {
                background-color: #3A3A55;
                color: #B0B0C8;
                border: 1px solid #4A4A6A;
            }
            QPushButton#prevBtn:hover {
                background-color: #44445F;
            }
            QPushButton#prevBtn:disabled {
                color: #555566;
                background-color: #2E2E45;
                border-color: #3A3A55;
            }
            QPushButton#skipBtn {
                background-color: transparent;
                color: #777799;
                border: none;
            }
            QPushButton#skipBtn:hover {
                color: #9999BB;
            }
            QPushButton#nextBtn {
                background-color: #4A9EFF;
                color: #FFFFFF;
                border: none;
            }
            QPushButton#nextBtn:hover {
                background-color: #5AAEFF;
            }
            QPushButton#nextBtn:disabled {
                background-color: #33558A;
                color: #7799BB;
            }
        """)

    # ── 拖拽支持 ──────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self._save_position()

    # ── 位置记忆 ──────────────────────────────────────────────
    def _save_position(self):
        s = QSettings("LgWudi", "TutorialTooltip")
        s.setValue("pos", self.pos())

    def _restore_position(self):
        s = QSettings("LgWudi", "TutorialTooltip")
        pos = s.value("pos")
        if pos and isinstance(pos, QPoint):
            self.move(pos)

    def place_default(self, parent_geometry):
        """将弹窗放置在父窗口右下角（默认位置）"""
        margin = 20
        x = parent_geometry.right() - self.width() - margin
        y = parent_geometry.bottom() - self.height() - margin - 40  # 留出任务栏
        self.move(x, y)

    # ── 对外接口 ──────────────────────────────────────────────
    def set_step(self, step_index: int, total: int, title: str, description: str):
        """更新显示内容"""
        self._current_step = step_index
        self._total_steps = total

        self.step_label.setText(f"步骤 {step_index + 1} / {total}")
        self.title_label.setText(title)
        self.desc_label.setText(description)

        self.dot_indicator.set_state(step_index, total)

        # 第一步时禁用上一步
        self.prev_btn.setEnabled(step_index > 0)
        # 最后一步时改变下一步文字
        if step_index >= total - 1:
            self.next_btn.setText("完成 ✓")
        else:
            self.next_btn.setText("下一步 →")

        self.adjustSize()
