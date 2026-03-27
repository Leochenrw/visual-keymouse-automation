"""
可拖拽坐标捕获按钮

用法：
1. 按住按钮拖拽到目标位置
2. 松开鼠标，捕获当前坐标
3. 通过信号将坐标传回父组件
"""
from PyQt5.QtWidgets import QPushButton, QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QMimeData
from PyQt5.QtGui import QCursor, QDrag, QPixmap, QPainter, QColor, QPen


class CoordinateDragButton(QPushButton):
    """可拖拽的坐标捕获按钮"""

    coordinate_captured = pyqtSignal(int, int)  # 发射捕获的 x, y 坐标

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.setCursor(Qt.CrossCursor)
        self.setToolTip("按住拖拽到目标位置，松开捕获坐标")
        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                border: 1px solid #388E3C;
                border-radius: 3px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #388E3C;
            }
        """)
        self.setText("+")
        self.dragging = False
        self.drag_start_pos = None

    def mousePressEvent(self, event):
        """鼠标按下 - 开始拖拽"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_start_pos = event.pos()
            self.setDown(True)
            # 改变光标为十字准星
            QApplication.setOverrideCursor(Qt.CrossCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """鼠标移动 - 启动拖拽"""
        if self.dragging and (event.pos() - self.drag_start_pos).manhattanLength() > 3:
            # 创建拖拽对象
            drag = QDrag(self)
            mime_data = QMimeData()
            drag.setMimeData(mime_data)

            # 创建拖拽时的预览图像（简单的十字准星）
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawLine(16, 8, 16, 24)
            painter.drawLine(8, 16, 24, 16)
            painter.end()
            drag.setPixmap(pixmap)
            drag.setHotSpot(pixmap.rect().center())

            # 执行拖拽
            drag.exec_(Qt.CopyAction)

            # 拖拽结束，捕获坐标
            self._capture_coordinate()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """鼠标释放 - 捕获坐标"""
        if event.button() == Qt.LeftButton and self.dragging:
            self.dragging = False
            self.setDown(False)
            QApplication.restoreOverrideCursor()
            # 如果拖拽距离很短，认为是点击而非拖拽，也捕获坐标
            if (event.pos() - self.drag_start_pos).manhattanLength() <= 3:
                self._capture_coordinate()
        super().mouseReleaseEvent(event)

    def _capture_coordinate(self):
        """捕获当前鼠标坐标"""
        # 使用 QTimer.singleShot 延迟获取，确保鼠标已释放
        QTimer.singleShot(50, self._do_capture)

    def _do_capture(self):
        """实际执行坐标捕获"""
        try:
            # 获取全局鼠标位置
            pos = QCursor.pos()
            x, y = pos.x(), pos.y()
            # 发射信号
            self.coordinate_captured.emit(x, y)
        except Exception as e:
            print(f"捕获坐标失败: {e}")
