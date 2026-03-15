"""
图片测试控件 - 用于找图节点的测试功能
"""
import cv2
import numpy as np
import pyautogui
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QColor


class ImageTestWorker(QThread):
    """图片测试工作线程"""

    test_finished = pyqtSignal(bool, int, int, float)  # 是否找到, x, y, 置信度
    test_error = pyqtSignal(str)

    def __init__(self, image_path, threshold=0.8, region=None):
        super().__init__()
        self.image_path = image_path
        self.threshold = threshold
        self.region = region or [0, 0, 1920, 1080]
        self._is_running = True

    def run(self):
        """执行找图测试"""
        try:
            if not self.image_path:
                self.test_error.emit("图片路径为空")
                return

            # 读取模板图片（支持中文路径）
            try:
                # 使用 np.fromfile 读取文件字节，支持中文路径
                file_bytes = np.fromfile(self.image_path, dtype=np.uint8)
                template = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                if template is None:
                    self.test_error.emit(f"无法解码图片: {self.image_path}")
                    return
            except Exception as e:
                self.test_error.emit(f"读取图片失败: {e}")
                return

            # 截图
            screenshot = pyautogui.screenshot(region=self.region)
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # 模板匹配
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= self.threshold:
                # 计算中心点坐标（相对于屏幕）
                x = max_loc[0] + template.shape[1] // 2 + self.region[0]
                y = max_loc[1] + template.shape[0] // 2 + self.region[1]
                self.test_finished.emit(True, x, y, max_val)
            else:
                self.test_finished.emit(False, 0, 0, max_val)

        except Exception as e:
            self.test_error.emit(str(e))

    def stop(self):
        """停止测试"""
        self._is_running = False


class ImageTestWidget(QWidget):
    """图片测试控件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_path = ""
        self.threshold = 0.8
        self.region = [0, 0, 1920, 1080]
        self.test_worker = None
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 测试按钮
        self.test_btn = QPushButton("测试找图")
        self.test_btn.setToolTip("点击测试是否能找到图片")
        self.test_btn.clicked.connect(self._on_test)
        layout.addWidget(self.test_btn)

        # 测试结果标签
        self.result_label = QLabel("")
        self.result_label.setStyleSheet("color: gray;")
        layout.addWidget(self.result_label)

        layout.addStretch()

    def set_params(self, image_path, threshold=0.8, region=None):
        """设置参数"""
        self.image_path = image_path
        self.threshold = threshold
        if region:
            self.region = region

    def _on_test(self):
        """点击测试按钮"""
        if not self.image_path:
            QMessageBox.warning(self, "警告", "请先设置图片路径")
            return

        # 禁用按钮
        self.test_btn.setEnabled(False)
        self.test_btn.setText("测试中...")
        self.result_label.setText("正在查找...")
        self.result_label.setStyleSheet("color: gray;")

        # 启动测试线程
        self.test_worker = ImageTestWorker(
            self.image_path,
            self.threshold,
            self.region
        )
        self.test_worker.test_finished.connect(self._on_test_finished)
        self.test_worker.test_error.connect(self._on_test_error)
        self.test_worker.start()

    def _on_test_finished(self, found, x, y, confidence):
        """测试完成"""
        self.test_btn.setEnabled(True)
        self.test_btn.setText("测试找图")

        if found:
            self.result_label.setText(f"找到! 置信度: {confidence:.2%}")
            self.result_label.setStyleSheet("color: green; font-weight: bold;")

            # 移动鼠标到目标位置
            try:
                pyautogui.moveTo(x, y, duration=0.5)
                QMessageBox.information(
                    self,
                    "测试成功",
                    f"找到图片!\n位置: ({x}, {y})\n置信度: {confidence:.2%}\n\n鼠标已移动到目标位置。"
                )
            except Exception as e:
                QMessageBox.warning(self, "移动鼠标失败", f"找到图片但无法移动鼠标: {e}")
        else:
            self.result_label.setText(f"未找到 (置信度: {confidence:.2%})")
            self.result_label.setStyleSheet("color: red;")
            QMessageBox.information(
                self,
                "测试失败",
                f"未找到图片\n最高置信度: {confidence:.2%}\n阈值: {self.threshold}"
            )

    def _on_test_error(self, error_msg):
        """测试出错"""
        self.test_btn.setEnabled(True)
        self.test_btn.setText("测试找图")
        self.result_label.setText(f"错误: {error_msg}")
        self.result_label.setStyleSheet("color: red;")
        QMessageBox.critical(self, "测试错误", f"找图测试出错:\n{error_msg}")
