"""
Branch Select Dialog - For selecting condition branches when running to a node
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QRadioButton, QButtonGroup, QScrollArea,
    QWidget, QFrame
)
from PyQt5.QtCore import Qt


class BranchSelectDialog(QDialog):
    """Branch selection dialog for conditions"""

    def __init__(self, parent, conditions_on_path):
        """
        Args:
            parent: Parent window
            conditions_on_path: Condition nodes on the path
                [
                    {"node_id": "n1", "node_title": "Condition", "expression": "$found == True"},
                    ...
                ]
        """
        super().__init__(parent)
        self.conditions_on_path = conditions_on_path
        self.branch_choices = {}  # {node_id: port_index}
        self.button_groups = {}

        self.setWindowTitle("Select Condition Branch - Run to Here")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

        self._init_ui()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Info text
        info_label = QLabel(
            "Condition nodes detected on path. Select which branch to take.\n"
            "Default is Yes branch.\n"
        )
        info_label.setStyleSheet("color: #666; font-size: 12px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # No conditions
        if not self.conditions_on_path:
            no_condition_label = QLabel("No condition nodes on path.")
            no_condition_label.setStyleSheet("color: #999; font-style: italic;")
            no_condition_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(no_condition_label)
        else:
            # Create scroll area
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)

            scroll_content = QWidget()
            scroll_layout = QVBoxLayout(scroll_content)
            scroll_layout.setSpacing(15)
            scroll_layout.setAlignment(Qt.AlignTop)

            # Create group for each condition
            for condition in self.conditions_on_path:
                group = self._create_condition_group(condition)
                scroll_layout.addWidget(group)

            scroll.setWidget(scroll_content)
            layout.addWidget(scroll)

        # Button area
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.ok_btn = QPushButton("OK")
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self._on_ok)
        button_layout.addWidget(self.ok_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def _create_condition_group(self, condition):
        """Create selection group for a condition node"""
        node_id = condition['node_id']
        expression = condition.get('expression', '')

        group = QGroupBox(f"{condition['node_title']}")
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

        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        # Show condition expression
        if expression:
            expr_label = QLabel(f"Condition: {expression}")
            expr_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
            expr_label.setWordWrap(True)
            layout.addWidget(expr_label)

        # Create button group
        btn_group = QButtonGroup(self)
        self.button_groups[node_id] = btn_group

        # Yes branch (port 0)
        true_radio = QRadioButton("Yes (True branch)")
        true_radio.setChecked(True)  # Default
        btn_group.addButton(true_radio, 0)
        layout.addWidget(true_radio)

        # No branch (port 1)
        false_radio = QRadioButton("No (False branch)")
        btn_group.addButton(false_radio, 1)
        layout.addWidget(false_radio)

        return group

    def _on_ok(self):
        """OK button clicked"""
        self.branch_choices = self._collect_choices()
        self.accept()

    def _collect_choices(self):
        """Collect all selections"""
        choices = {}
        for node_id, btn_group in self.button_groups.items():
            selected_id = btn_group.checkedId()
            if selected_id >= 0:
                choices[node_id] = selected_id
        return choices

    def get_branch_choices(self):
        """Get branch selection result"""
        return self.branch_choices

    @staticmethod
    def get_choices(parent, conditions_on_path):
        """Static method to show dialog and return result
        Returns:
            (accepted, branch_choices): Whether confirmed, branch choice dict
        """
        if not conditions_on_path:
            return True, {}

        dialog = BranchSelectDialog(parent, conditions_on_path)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            return True, dialog.get_branch_choices()
        else:
            return False, {}


def find_conditions_on_path(engine, start_node_id, target_node_id):
    """
    Find all condition nodes on path from start to target

    Args:
        engine: WorkflowEngine instance
        start_node_id: Start node ID
        target_node_id: Target node ID

    Returns:
        List[dict]: Condition nodes on path
    """
    conditions = []
    visited = set()

    def find_path(current_id, target_id, path):
        if current_id == target_id:
            return path + [current_id]

        if current_id in visited:
            return None

        visited.add(current_id)

        # Find all connections from current node
        for conn in engine.connections:
            if conn.get('from') == current_id:
                next_id = conn.get('to')
                if next_id:
                    result = find_path(next_id, target_id, path + [current_id])
                    if result:
                        return result

        return None

    path = find_path(start_node_id, target_node_id, [])

    if path:
        for node_id in path:
            node = engine.nodes.get(node_id)
            if node and node['type'] == 'condition':
                params = node.get('params', {})
                expression = ''
                if 'condition' in params:
                    cond_def = params['condition']
                    if isinstance(cond_def, dict):
                        expression = cond_def.get('value', cond_def.get('default', ''))
                    else:
                        expression = str(cond_def)

                conditions.append({
                    'node_id': node_id,
                    'node_title': node.get('title', node_id),
                    'expression': expression
                })

    return conditions
