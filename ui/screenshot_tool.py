"""
截图工具 - 支持区域截图
"""
import os
import time
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QApplication, QPushButton, QLabel, QVBoxLayout,
    QFileDialog, QMessageBox, QHBoxLayout, QLineEdit, QInputDialog
)
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QCursor, QPixmap, QScreen


def get_pic_folder():
    """获取pic文件夹路径（在项目根目录下）"""
    # 尝试多种方式找到项目根目录
    current_file = os.path.abspath(__file__)
    # ui/screenshot_tool.py -> 上级目录 -> 项目根目录
    project_root = os.path.dirname(os.path.dirname(current_file))
    pic_folder = os.path.join(project_root, 'pic')
    os.makedirs(pic_folder, exist_ok=True)
    return pic_folder


class ScreenshotSelector(QWidget):
    """截图选择器 - 全屏遮罩，框选区域"""

    screenshot_taken = pyqtSignal(str)  # 信号：截图完成，返回文件路径

    def __init__(self, save_path=None):
        super().__init__()
        self.save_path = save_path or get_pic_folder()
        os.makedirs(self.save_path, exist_ok=True)

        self.begin_pos = None
        self.end_pos = None
        self.is_drawing = False

        # 获取所有屏幕和虚拟桌面大小
        self.screens = QApplication.screens()
        self.virtual_rect = QRect()
        for screen in self.screens:
            self.virtual_rect = self.virtual_rect.united(screen.geometry())

        # 设置窗口覆盖整个虚拟桌面
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(self.virtual_rect)
        self.setCursor(QCursor(Qt.CrossCursor))

        # 半透明背景
        self.overlay_color = QColor(0, 0, 0, 100)  # 黑色半透明
        self.select_color = QColor(255, 255, 255, 50)  # 选择区域
        self.border_color = QColor(255, 0, 0, 255)  # 红色边框

        # 捕获所有屏幕
        self.full_screenshot = self._capture_all_screens()

    def _capture_all_screens(self):
        """捕获所有屏幕的拼接图像"""
        # 计算虚拟桌面总大小
        virtual_rect = QRect()
        for screen in self.screens:
            virtual_rect = virtual_rect.united(screen.geometry())

        # 创建大画布
        pixmap = QPixmap(virtual_rect.size())
        pixmap.fill(Qt.transparent)

        # 在每个屏幕位置绘制截图
        painter = QPainter(pixmap)
        for screen in self.screens:
            screen_pixmap = screen.grabWindow(0)
            geo = screen.geometry()
            painter.drawPixmap(geo.x() - virtual_rect.x(),
                              geo.y() - virtual_rect.y(),
                              screen_pixmap)
        painter.end()

        return pixmap

    def paintEvent(self, event):
        """绘制遮罩和选择框"""
        painter = QPainter(self)

        # 绘制半透明遮罩
        painter.fillRect(self.rect(), self.overlay_color)

        if self.is_drawing and self.begin_pos and self.end_pos:
            # 计算选择区域
            rect = QRect(self.begin_pos, self.end_pos).normalized()

            # 绘制选择区域（高亮）
            painter.fillRect(rect, self.select_color)

            # 绘制边框
            pen = QPen(self.border_color, 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(rect)

            # 显示尺寸信息
            size_text = f"{rect.width()} x {rect.height()}"
            painter.setPen(Qt.white)
            painter.drawText(rect.topLeft() + QPoint(5, -5), size_text)

        painter.end()

    def mousePressEvent(self, event):
        """鼠标按下 - 开始选择"""
        if event.button() == Qt.LeftButton:
            self.begin_pos = event.pos()
            self.end_pos = event.pos()
            self.is_drawing = True
            self.update()

    def mouseMoveEvent(self, event):
        """鼠标移动 - 更新选择区域"""
        if self.is_drawing:
            self.end_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        """鼠标释放 - 完成截图"""
        if event.button() == Qt.LeftButton and self.is_drawing:
            self.end_pos = event.pos()
            self.is_drawing = False
            self.take_screenshot()

    def keyPressEvent(self, event):
        """按键事件 - ESC取消"""
        if event.key() == Qt.Key_Escape:
            self.close()

    def take_screenshot(self):
        """执行截图"""
        if not self.begin_pos or not self.end_pos:
            self.close()
            return

        # 计算截图区域
        rect = QRect(self.begin_pos, self.end_pos).normalized()

        if rect.width() < 10 or rect.height() < 10:
            QMessageBox.warning(self, "截图失败", "选择的区域太小")
            self.close()
            return

        # 从全屏截图中裁剪
        self._screenshot = self.full_screenshot.copy(rect)
        self._rect = rect

        # 弹出命名对话框
        self._show_name_dialog()

    def _show_name_dialog(self):
        """显示命名对话框"""
        # 生成默认文件名（带时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"screenshot_{timestamp}"

        # 弹出输入对话框
        name, ok = QInputDialog.getText(
            self,
            "截图命名",
            "请输入截图名称（不需要扩展名）：",
            QLineEdit.Normal,
            default_name
        )

        if ok and name:
            # 清理文件名，移除非法字符
            name = self._sanitize_filename(name)
            if not name:
                name = default_name
            filename = f"{name}.png"
        elif not ok:
            # 用户取消，关闭截图选择器
            self.close()
            return
        else:
            # 用户输入为空，使用默认名
            filename = f"{default_name}.png"

        filepath = os.path.join(self.save_path, filename)

        # 检查文件是否已存在
        if os.path.exists(filepath):
            reply = QMessageBox.question(
                self,
                "文件已存在",
                f"文件 '{filename}' 已存在，是否覆盖？",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if reply == QMessageBox.No:
                # 重新命名
                self._show_name_dialog()
                return
            elif reply == QMessageBox.Cancel:
                self.close()
                return

        # 保存
        if self._screenshot.save(filepath):
            self.screenshot_taken.emit(filepath)
            QMessageBox.information(self, "截图成功", f"已保存: {filename}\n路径: {self.save_path}")
        else:
            QMessageBox.critical(self, "截图失败", "保存文件失败")

        self.close()

    def _sanitize_filename(self, filename):
        """清理文件名，移除非法字符"""
        # Windows 非法字符: \ / : * ? " < > |
        illegal_chars = '\\/:*?"<>|'
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        return filename.strip()


class ScreenshotButton(QPushButton):
    """截图按钮 - 嵌入属性面板使用"""

    screenshot_taken = pyqtSignal(str)  # 截图完成信号

    def __init__(self, parent=None, save_path=None):
        super().__init__("截图", parent)
        self.save_path = save_path or get_pic_folder()
        self.clicked.connect(self.start_screenshot)
        self.setToolTip(f"点击后框选截图区域\n保存位置: {self.save_path}")

    def start_screenshot(self):
        """开始截图"""
        # 隐藏主窗口
        main_window = self.window()
        main_window.hide()

        # 延迟一点确保窗口隐藏
        QApplication.processEvents()
        time.sleep(0.3)

        # 创建截图选择器
        self.selector = ScreenshotSelector(self.save_path)
        self.selector.screenshot_taken.connect(self._on_screenshot_done)
        self.selector.show()

    def _on_screenshot_done(self, filepath):
        """截图完成"""
        self.screenshot_taken.emit(filepath)
        # 恢复主窗口
        self.window().show()


class ScreenshotWidget(QWidget):
    """截图控件 - 包含文件路径和截图按钮"""

    path_changed = pyqtSignal(str)

    def __init__(self, parent=None, default_path=""):
        super().__init__(parent)
        self._init_ui(default_path)

    def _init_ui(self, default_path):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 文件路径输入
        self.path_edit = QLineEdit()
        self.path_edit.setText(default_path)
        self.path_edit.setPlaceholderText("图片路径...")
        layout.addWidget(self.path_edit)

        # 浏览按钮
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.setMinimumWidth(60)
        self.browse_btn.clicked.connect(self._browse_file)
        layout.addWidget(self.browse_btn)

        # 截图按钮
        self.screenshot_btn = ScreenshotButton(self)
        self.screenshot_btn.setMinimumWidth(50)
        self.screenshot_btn.screenshot_taken.connect(self._on_screenshot)
        layout.addWidget(self.screenshot_btn)

    def _browse_file(self):
        """浏览文件"""
        # 默认打开 pic 文件夹
        pic_folder = get_pic_folder()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", pic_folder,
            "图片文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*.*)"
        )
        if file_path:
            self.path_edit.setText(file_path)
            self.path_changed.emit(file_path)

    def _on_screenshot(self, filepath):
        """截图完成"""
        self.path_edit.setText(filepath)
        self.path_changed.emit(filepath)

    def text(self):
        """获取路径文本"""
        return self.path_edit.text()

    def setText(self, text):
        """设置路径文本"""
        self.path_edit.setText(text)
