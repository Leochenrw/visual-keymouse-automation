"""
日志面板 - 显示执行日志和输出信息
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QComboBox, QLabel, QLineEdit, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime
from PyQt5.QtGui import QColor, QTextCharFormat, QTextCursor, QFont


class LogPanel(QWidget):
    """日志面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._max_lines = 1000  # 最大保留行数

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        # 日志级别过滤
        self.level_filter = QComboBox()
        self.level_filter.addItems(["全部", "信息", "成功", "警告", "错误", "调试"])
        self.level_filter.currentTextChanged.connect(self._on_filter_changed)
        toolbar.addWidget(QLabel("级别:"))
        toolbar.addWidget(self.level_filter)

        # 搜索
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索日志...")
        self.search_edit.textChanged.connect(self._on_search)
        toolbar.addWidget(self.search_edit)

        toolbar.addStretch()

        # 自动滚动
        self.auto_scroll = QCheckBox("自动滚动")
        self.auto_scroll.setChecked(True)
        toolbar.addWidget(self.auto_scroll)

        # 清除按钮
        clear_btn = QPushButton("清除")
        clear_btn.clicked.connect(self.clear)
        toolbar.addWidget(clear_btn)

        # 复制按钮
        copy_btn = QPushButton("复制")
        copy_btn.clicked.connect(self._copy_logs)
        toolbar.addWidget(copy_btn)

        layout.addLayout(toolbar)

        # 日志显示区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #3C3C3C;
                padding: 5px;
            }
        """)
        layout.addWidget(self.log_text)

        # 统计信息
        self.stats_label = QLabel("日志: 0 条")
        self.stats_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.stats_label)

    def _get_timestamp(self):
        """获取时间戳"""
        return QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss.zzz")[:-1]

    def _insert_log(self, level, message, color):
        """插入日志"""
        timestamp = self._get_timestamp()

        # 创建格式
        format = QTextCharFormat()
        format.setForeground(QColor(color))

        # 插入文本
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)

        # 插入时间戳
        cursor.insertText(f"[{timestamp}] ", format)

        # 插入级别标签
        level_format = QTextCharFormat()
        level_format.setForeground(QColor(color))
        level_format.setFontWeight(QFont.Bold)
        cursor.insertText(f"[{level}] ", level_format)

        # 插入消息
        cursor.insertText(f"{message}\n", format)

        # 自动滚动
        if self.auto_scroll.isChecked():
            self.log_text.setTextCursor(cursor)
            self.log_text.ensureCursorVisible()

        # 限制行数
        self._trim_logs()

        # 更新统计
        self._update_stats()

    def _trim_logs(self):
        """修剪日志行数"""
        doc = self.log_text.document()
        if doc.lineCount() > self._max_lines:
            cursor = QTextCursor(doc)
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(
                QTextCursor.Down,
                QTextCursor.KeepAnchor,
                doc.lineCount() - self._max_lines
            )
            cursor.removeSelectedText()

    def _update_stats(self):
        """更新统计"""
        count = self.log_text.document().lineCount() - 1
        self.stats_label.setText(f"日志: {count} 条")

    def log_info(self, message):
        """记录信息日志"""
        self._insert_log("INFO", message, "#D4D4D4")

    def log_success(self, message):
        """记录成功日志"""
        self._insert_log("SUCCESS", message, "#4CAF50")

    def log_warning(self, message):
        """记录警告日志"""
        self._insert_log("WARN", message, "#FFC107")

    def log_error(self, message):
        """记录错误日志"""
        self._insert_log("ERROR", message, "#F44336")

    def log_debug(self, message):
        """记录调试日志"""
        self._insert_log("DEBUG", message, "#9E9E9E")

    def clear(self):
        """清空日志"""
        self.log_text.clear()
        self._update_stats()

    def _copy_logs(self):
        """复制日志到剪贴板"""
        from PyQt5.QtWidgets import QApplication
        QApplication.clipboard().setText(self.log_text.toPlainText())

    def _on_filter_changed(self, level):
        """过滤级别变化"""
        # 简化实现：重新显示所有日志
        # 实际应该根据级别过滤显示
        pass

    def _on_search(self, text):
        """搜索日志"""
        if not text:
            return

        # 查找文本
        cursor = self.log_text.document().find(text)
        if not cursor.isNull():
            self.log_text.setTextCursor(cursor)
            self.log_text.ensureCursorVisible()
