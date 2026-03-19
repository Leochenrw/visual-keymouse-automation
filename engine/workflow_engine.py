"""
工作流执行引擎 - 支持条件分支和循环
"""
import time
import threading
import re
from PyQt5.QtCore import QObject, pyqtSignal


class WorkflowEngine(QObject):
    """工作流执行引擎"""

    # 信号
    execution_started = pyqtSignal()
    execution_stopped = pyqtSignal()
    execution_paused = pyqtSignal()
    execution_resumed = pyqtSignal()
    node_started = pyqtSignal(str, str)  # node_id, node_type
    node_finished = pyqtSignal(str, str, object)  # node_id, node_type, result
    execution_error = pyqtSignal(str, str)  # node_id, error_message
    log_message = pyqtSignal(str, str)  # level, message

    def __init__(self):
        super().__init__()
        self.workflow_data = None
        self.nodes = {}
        self.connections = []
        self.variables = {}
        self.is_running = False
        self.is_paused = False
        self.current_node_id = None
        self.stop_requested = False
        self.execution_thread = None

        # 循环控制状态
        self._loop_stack = []  # 循环栈，用于跟踪嵌套循环
        self._break_requested = False
        self._continue_requested = False

        # 测试快照管理
        self.test_snapshots = {}  # {node_id: {"variables": {...}, "timestamp": ...}}
        self._test_mode = False  # 测试模式标志
        self._test_target_node_id = None  # 单节点测试的目标节点
        self._branch_choices = {}  # 分支选择 {node_id: port_index}

        # 禁用 PyAutoGUI 的 fail-safe（允许鼠标移动到屏幕角落）
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
        except ImportError:
            pass

    def load_workflow(self, workflow_data):
        """加载工作流"""
        self.workflow_data = workflow_data
        nodes_list = workflow_data.get('nodes', [])
        self.nodes = {n['id']: n for n in nodes_list}
        self.connections = workflow_data.get('connections', [])
        self.variables = {}
        self._loop_stack = []
        self._break_requested = False
        self._continue_requested = False

        # 调试信息
        node_types = [n.get('type') for n in nodes_list]
        start_nodes = [t for t in node_types if t and t.startswith('start_')]
        self.log_message.emit('info', f'工作流已加载: {len(nodes_list)} 个节点, 起始节点: {len(start_nodes)} 个')
        self.log_message.emit('info', f'节点类型: {node_types}')

    def start(self):
        """开始执行"""
        if self.is_running:
            return

        if not self.workflow_data:
            self.log_message.emit('error', '没有加载工作流')
            return

        self.is_running = True
        self.is_paused = False
        self.stop_requested = False
        self._break_requested = False
        self._continue_requested = False
        self._loop_stack = []
        self.execution_started.emit()
        self.log_message.emit('info', '开始执行工作流')

        # 在新线程中执行
        self.execution_thread = threading.Thread(target=self._execute_workflow)
        self.execution_thread.start()

    def stop(self):
        """停止执行"""
        if not self.is_running:
            return
        self.stop_requested = True
        self.log_message.emit('info', '请求停止执行')

    def pause(self):
        """暂停执行"""
        if self.is_running and not self.is_paused:
            self.is_paused = True
            self.execution_paused.emit()
            self.log_message.emit('info', '执行已暂停')

    def resume(self):
        """恢复执行"""
        if self.is_running and self.is_paused:
            self.is_paused = False
            self.execution_resumed.emit()
            self.log_message.emit('info', '执行已恢复')

    def _execute_workflow(self):
        """执行工作流主逻辑"""
        try:
            # 找到起始节点
            start_nodes = self._find_start_nodes()
            if not start_nodes:
                self.log_message.emit('error', '没有找到起始节点')
                self._finish_execution()
                return

            # 从每个起始节点开始执行
            for start_node in start_nodes:
                if self.stop_requested:
                    break
                self._execute_node_chain(start_node)

        except Exception as e:
            self.log_message.emit('error', f'执行出错: {e}')
            self.execution_error.emit('', str(e))
        finally:
            self._finish_execution()

    def _execute_node_chain(self, start_node, exit_nodes=None):
        """
        执行节点链
        exit_nodes: 遇到这些节点时停止执行（用于循环体边界）
        """
        current_node = start_node
        exit_nodes = exit_nodes or set()

        while current_node and not self.stop_requested:
            # 检查是否到达退出节点
            if current_node['id'] in exit_nodes:
                break

            # 检查暂停
            while self.is_paused and not self.stop_requested:
                time.sleep(0.1)

            if self.stop_requested:
                break

            # 执行当前节点
            node_id = current_node['id']
            node_type = current_node['type']
            self.current_node_id = node_id
            self.node_started.emit(node_id, node_type)

            try:
                result = self._execute_node(current_node)
                self.node_finished.emit(node_id, node_type, result)

                # 处理 break 节点
                if node_type == 'break':
                    if self._loop_stack:
                        self._break_requested = True
                        self.log_message.emit('info', '执行跳出循环')
                    else:
                        self.log_message.emit('warning', 'break 节点不在循环内')
                    break

                # 处理 continue 节点
                if node_type == 'continue':
                    if self._loop_stack:
                        self._continue_requested = True
                        self.log_message.emit('info', '执行继续循环')
                    else:
                        self.log_message.emit('warning', 'continue 节点不在循环内')
                    break

                # 处理条件节点 - 根据条件选择分支
                if node_type == 'condition':
                    next_node = self._get_condition_next_node(current_node, result)
                    current_node = next_node
                    continue

                # 处理图片判断节点 - 根据找图结果选择分支
                if node_type == 'if_image':
                    next_node = self._get_if_image_next_node(current_node, result)
                    current_node = next_node
                    continue

                # 处理循环节点
                if node_type == 'loop':
                    self._execute_loop_node(current_node, exit_nodes)
                    # 循环结束后，找到循环节点的"结束"出口继续执行
                    next_node = self._find_next_node_from_port(node_id, port_index=1)
                    current_node = next_node
                    continue

            except Exception as e:
                self.log_message.emit('error', f'节点 {current_node.get("title", node_id)} 执行失败: {e}')
                self.execution_error.emit(node_id, str(e))
                break

            # 找到下一个节点（默认从第0个输出口）
            current_node = self._find_next_node(node_id)

    def _execute_node(self, node):
        """执行单个节点"""
        node_type = node['type']
        params = node.get('params', {})

        # 获取参数值
        param_values = {}
        for key, param_def in params.items():
            # 防御性处理：如果 param_def 不是字典，直接使用该值
            if not isinstance(param_def, dict):
                param_values[key] = param_def
                continue
            value = param_def.get('value', param_def.get('default'))
            # 防御性处理：如果值仍然是字典，尝试提取其中的值
            if isinstance(value, dict):
                value = value.get('value', value.get('default'))
            # 处理变量引用
            if isinstance(value, str) and value.startswith('$'):
                var_name = value[1:]
                resolved_value = self.variables.get(var_name)
                if resolved_value is None:
                    self.log_message.emit('warning', f'变量 ${var_name} 未定义，保持原值 "{value}"')
                    # 保持原值，让后续处理决定如何处理
                else:
                    self.log_message.emit('debug', f'变量解析: ${var_name} = {resolved_value}')
                    value = resolved_value
            param_values[key] = value

        # 特殊节点不显示执行日志（由专门的方法处理）
        if node_type not in ['condition', 'loop', 'break', 'continue', 'if_image']:
            self.log_message.emit('info', f'执行节点: {node.get("title", node_type)}')

        # 根据节点类型执行
        if node_type == 'start_manual':
            return self._action_start_manual()
        elif node_type == 'start_hotkey':
            return self._action_start_hotkey(param_values)
        elif node_type == 'mouse_move':
            return self._action_mouse_move(param_values)
        elif node_type == 'mouse_click':
            return self._action_mouse_click(param_values)
        elif node_type == 'key_press':
            return self._action_key_press(param_values)
        elif node_type == 'key_input':
            return self._action_key_input(param_values)
        elif node_type == 'delay':
            return self._action_delay(param_values)
        elif node_type == 'find_color':
            return self._action_find_color(param_values)
        elif node_type == 'condition':
            return self._action_condition(param_values)
        elif node_type == 'loop':
            return self._action_loop(param_values)
        elif node_type == 'break':
            return {'break': True}
        elif node_type == 'continue':
            return {'continue': True}
        elif node_type == 'if_image':
            return self._action_if_image(param_values)
        else:
            self.log_message.emit('warning', f'未知节点类型: {node_type}')
            return None

    def _find_start_nodes(self):
        """找到所有起始节点"""
        start_nodes = []
        for node in self.nodes.values():
            if node['type'].startswith('start_'):
                start_nodes.append(node)
        return start_nodes

    def _find_next_node(self, current_node_id, port_index=0):
        """找到从指定节点第port_index个输出口连接的下一个节点"""
        for conn in self.connections:
            if conn.get('from') == current_node_id:
                # 检查端口索引
                conn_port = conn.get('from_port', 0)
                if conn_port == port_index:
                    next_node_id = conn.get('to')
                    return self.nodes.get(next_node_id)
        return None

    def _find_next_node_from_port(self, node_id, port_index=0):
        """找到从指定端口连接的下一个节点"""
        for conn in self.connections:
            if conn.get('from') == node_id and conn.get('from_port', 0) == port_index:
                next_node_id = conn.get('to')
                return self.nodes.get(next_node_id)
        return None

    def _find_loop_body_end(self, loop_node_id):
        """
        找到循环体的结束位置
        策略：找到从循环节点"循环"出口连接的所有节点，直到没有后续节点或遇到特定节点
        """
        body_nodes = set()
        to_visit = [self._find_next_node_from_port(loop_node_id, port_index=0)]

        while to_visit:
            node = to_visit.pop(0)
            if not node or node['id'] in body_nodes:
                continue

            body_nodes.add(node['id'])

            # 如果遇到其他条件或循环节点，也包含它们的出口
            next_default = self._find_next_node(node['id'], port_index=0)
            if next_default and next_default['id'] != loop_node_id:
                to_visit.append(next_default)

        return body_nodes

    def _execute_loop_node(self, loop_node, parent_exit_nodes):
        """执行循环节点"""
        params = loop_node.get('params', {})
        count = 0

        # 获取循环次数
        for key, param_def in params.items():
            if key == 'count':
                count = int(param_def.get('value', param_def.get('default', 3)))
                break

        loop_var = 'i'
        for key, param_def in params.items():
            if key == 'loop_var':
                loop_var = param_def.get('value', param_def.get('default', 'i'))
                break

        # 找到循环体起始节点（从"循环"出口，端口0）
        body_start = self._find_next_node_from_port(loop_node['id'], port_index=0)
        if not body_start:
            self.log_message.emit('warning', '循环节点没有连接循环体')
            return

        # 构建循环体结束边界（包括从"结束"出口连接的节点）
        exit_nodes = set(parent_exit_nodes) if parent_exit_nodes else set()
        # 找到循环"结束"出口连接的节点，也作为边界
        end_exit_node = self._find_next_node_from_port(loop_node['id'], port_index=1)
        if end_exit_node:
            exit_nodes.add(end_exit_node['id'])

        # 推入循环栈
        self._loop_stack.append({
            'node_id': loop_node['id'],
            'count': count,
            'current': 0
        })

        try:
            for i in range(count):
                if self.stop_requested:
                    break

                # 设置循环变量（使用特殊前缀避免与用户变量冲突）
                self.variables[f'__loop_{loop_var}__'] = i
                self.variables[f'__loop_{loop_var}_1__'] = i + 1  # 支持 $i+1 的简便写法

                self.log_message.emit('info', f'循环第 {i+1}/{count} 次迭代')

                # 重置控制标志
                self._break_requested = False
                self._continue_requested = False

                # 更新循环栈当前计数
                self._loop_stack[-1]['current'] = i + 1

                # 执行循环体
                self._execute_node_chain(body_start, exit_nodes)

                # 检查 break
                if self._break_requested:
                    self._break_requested = False
                    self.log_message.emit('info', '循环被跳出')
                    break

                # continue 会自动继续下一次迭代
                if self._continue_requested:
                    self._continue_requested = False
                    continue

        finally:
            # 弹出循环栈
            if self._loop_stack:
                self._loop_stack.pop()
            # 清理循环变量
            loop_var_key = f'__loop_{loop_var}__'
            loop_var_1_key = f'__loop_{loop_var}_1__'
            if loop_var_key in self.variables:
                del self.variables[loop_var_key]
            if loop_var_1_key in self.variables:
                del self.variables[loop_var_1_key]

    def _get_condition_next_node(self, condition_node, result):
        """根据条件结果选择下一个节点"""
        condition_met = result.get('condition_met', False)

        # condition_met 为 True 时走端口 0（是/True分支）
        # condition_met 为 False 时走端口 1（否/False分支）
        port_index = 0 if condition_met else 1
        next_node = self._find_next_node_from_port(condition_node['id'], port_index)

        branch_name = "是" if condition_met else "否"
        self.log_message.emit('info', f'条件判断结果: {branch_name}')

        return next_node

    def _get_if_image_next_node(self, if_image_node, result):
        """根据图片判断结果选择下一个节点"""
        found = result.get('found', False)

        # found 为 True 时走端口 0（找到分支）
        # found 为 False 时走端口 1（未找到分支）
        port_index = 0 if found else 1
        next_node = self._find_next_node_from_port(if_image_node['id'], port_index)

        # 获取分支标签
        params = if_image_node.get('params', {})
        true_label = params.get('true_label', {}).get('value', '找到') if isinstance(params.get('true_label'), dict) else params.get('true_label', '找到')
        false_label = params.get('false_label', {}).get('value', '未找到') if isinstance(params.get('false_label'), dict) else params.get('false_label', '未找到')
        branch_name = true_label if found else false_label

        self.log_message.emit('info', f'图片判断结果: {branch_name}')

        return next_node

    def _evaluate_condition(self, expression):
        """
        评估条件表达式
        支持: ==, !=, <, >, <=, >=, and, or, not, in
        支持变量引用: $variable
        """
        if not expression:
            return True

        expression = expression.strip()

        # 处理变量替换（支持普通变量和循环变量）
        def replace_var(match):
            var_name = match.group(1)
            # 先查找普通变量
            value = self.variables.get(var_name)
            # 再查找循环变量（带特殊前缀）
            if value is None:
                value = self.variables.get(f'__loop_{var_name}__', match.group(0))
            # 如果值是字符串，需要加引号
            if isinstance(value, str):
                return repr(value)
            return str(value)

        # 替换 $variable 格式的变量
        expr = re.sub(r'\$(\w+)', replace_var, expression)

        # 处理 True/False 字符串
        expr = expr.replace('true', 'True').replace('false', 'False')

        # 安全评估 - 使用更严格的限制
        try:
            # 编译表达式以检查只允许特定操作
            compiled = compile(expr, '<string>', 'eval')

            # 检查 AST 节点类型，只允许安全的操作
            import ast
            allowed_nodes = (
                ast.Expression, ast.BoolOp, ast.BinOp, ast.UnaryOp,
                ast.Compare, ast.Load, ast.NameConstant, ast.Num,
                ast.Str, ast.Tuple, ast.List, ast.Dict, ast.Name,
                ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
                ast.And, ast.Or, ast.Not, ast.In, ast.NotIn, ast.Is, ast.IsNot,
                ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow
            )
            for node in ast.walk(ast.parse(expr, mode='eval')):
                if not isinstance(node, allowed_nodes):
                    self.log_message.emit('warning', f'条件表达式包含不允许的操作: {type(node).__name__}')
                    return False

            # 使用 eval 但限制可用的内置函数
            result = eval(compiled, {"__builtins__": {}}, {
                'True': True, 'False': False, 'None': None
            })
            return bool(result)
        except Exception as e:
            self.log_message.emit('warning', f'条件表达式 "{expression}" 解析失败: {e}')
            return False

    def _finish_execution(self):
        """完成执行"""
        self.is_running = False
        self.is_paused = False
        self.current_node_id = None
        self._loop_stack = []
        self._break_requested = False
        self._continue_requested = False
        self.execution_stopped.emit()
        self.log_message.emit('info', '执行完成')

    # ===== 动作实现 =====

    def _action_start_manual(self):
        """手动启动"""
        return {'started': True}

    def _action_start_hotkey(self, params):
        """热键启动"""
        hotkey = params.get('hotkey', 'F6')
        return {'hotkey': hotkey}

    def _action_condition(self, params):
        """条件判断"""
        expression = params.get('condition', '')

        # 支持从参数结构中获取值
        if isinstance(expression, dict):
            expression = expression.get('value', expression.get('default', ''))

        condition_met = self._evaluate_condition(expression)

        return {'condition_met': condition_met, 'expression': expression}

    def _action_loop(self, params):
        """循环节点 - 参数解析在 _execute_loop_node 中处理"""
        count = int(params.get('count', 3))
        loop_var = params.get('loop_var', 'i')
        return {'count': count, 'loop_var': loop_var}

    def _action_mouse_move(self, params):
        """鼠标移动"""
        try:
            import pyautogui
            x = params.get('x', 0)
            y = params.get('y', 0)

            # 转换为整数（支持字符串数字和变量解析后的值）
            try:
                x = int(x)
            except (ValueError, TypeError):
                self.log_message.emit('warning', f'X坐标 "{x}" 无效，使用 0')
                x = 0
            try:
                y = int(y)
            except (ValueError, TypeError):
                self.log_message.emit('warning', f'Y坐标 "{y}" 无效，使用 0')
                y = 0

            pyautogui.moveTo(x, y)
            self.log_message.emit('info', f'鼠标移动到 ({x}, {y})')
            return {'x': x, 'y': y}
        except Exception as e:
            raise Exception(f'鼠标移动失败: {e}')

    def _action_mouse_click(self, params):
        """鼠标点击"""
        try:
            import pyautogui
            import random

            button = params.get('button', 'left')
            x = params.get('x')
            y = params.get('y')
            random_offset = params.get('random_offset', 0)

            # 处理坐标
            if x is not None and y is not None:
                x = int(x)
                y = int(y)

                # 添加随机偏移
                if random_offset and random_offset > 0:
                    x += random.randint(-random_offset, random_offset)
                    y += random.randint(-random_offset, random_offset)

                pyautogui.click(x, y, button=button)
            else:
                # 使用当前鼠标位置
                if random_offset and random_offset > 0:
                    # 获取当前位置并添加偏移
                    current_x, current_y = pyautogui.position()
                    x = current_x + random.randint(-random_offset, random_offset)
                    y = current_y + random.randint(-random_offset, random_offset)
                    pyautogui.click(x, y, button=button)
                else:
                    pyautogui.click(button=button)
                    x = None
                    y = None

            return {'button': button, 'x': x, 'y': y}
        except Exception as e:
            raise Exception(f'鼠标点击失败: {e}')

    def _action_key_press(self, params):
        """键盘按键"""
        try:
            import pyautogui
            key = params.get('key', 'enter')
            pyautogui.press(key)
            return {'key': key}
        except Exception as e:
            raise Exception(f'按键失败: {e}')

    def _action_key_input(self, params):
        """键盘输入"""
        try:
            import pyautogui
            text = params.get('text', '')
            pyautogui.typewrite(text)
            return {'text': text}
        except Exception as e:
            raise Exception(f'输入失败: {e}')

    def _action_delay(self, params):
        """延时"""
        milliseconds = int(params.get('milliseconds', 1000))
        seconds = milliseconds / 1000.0

        # 分段休眠以便响应停止请求
        elapsed = 0
        interval = 0.1
        while elapsed < seconds and not self.stop_requested:
            time.sleep(interval)
            elapsed += interval

        return {'milliseconds': milliseconds}

    def _action_if_image(self, params):
        """图片判断 - 找图并根据结果分支"""
        try:
            import cv2
            import numpy as np
            import pyautogui

            image_path = params.get('image_path', '')
            threshold = float(params.get('threshold', 0.8))
            region = params.get('region', [0, 0, 1920, 1080])

            # 防御性处理：确保 region 是正确的列表格式
            if not isinstance(region, (list, tuple)) or len(region) != 4:
                self.log_message.emit('warning', f'region 参数格式错误: {region}，使用默认值 [0, 0, 1920, 1080]')
                region = [0, 0, 1920, 1080]

            if not image_path:
                raise Exception('图片路径为空')

            # 截图（限定区域）
            screenshot = pyautogui.screenshot(region=region)
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # 读取模板（支持中文路径）
            try:
                file_bytes = np.fromfile(image_path, dtype=np.uint8)
                template = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                if template is None:
                    raise Exception(f'无法解码图片: {image_path}')
            except Exception as e:
                raise Exception(f'读取图片失败: {e}')

            # 模板匹配
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= threshold:
                # 计算中心坐标（相对于屏幕）
                x = max_loc[0] + template.shape[1] // 2 + region[0]
                y = max_loc[1] + template.shape[0] // 2 + region[1]

                # 设置变量
                self.variables['found'] = True
                self.variables['find_x'] = x
                self.variables['find_y'] = y
                self.variables['confidence'] = max_val

                self.log_message.emit('info', f'图片判断: 找到图片 ({x}, {y}), 置信度 {max_val:.3f}')

                # 获取自动移动和点击参数
                auto_move = params.get('auto_move', False)
                offset_x = int(params.get('offset_x', 0))
                offset_y = int(params.get('offset_y', 0))
                auto_click = params.get('auto_click', False)
                click_button = params.get('click_button', 'left')
                click_delay = int(params.get('click_delay', 0))

                target_x = x + offset_x
                target_y = y + offset_y

                # 自动移动鼠标
                if auto_move:
                    pyautogui.moveTo(target_x, target_y)
                    self.log_message.emit('info', f'鼠标移动到 ({target_x}, {target_y})')

                # 自动点击（始终使用目标坐标）
                if auto_click:
                    if click_delay > 0:
                        time.sleep(click_delay / 1000.0)

                    if click_button == 'left':
                        pyautogui.click(target_x, target_y)
                        self.log_message.emit('info', f'执行左键点击 ({target_x}, {target_y})')
                    elif click_button == 'right':
                        pyautogui.rightClick(target_x, target_y)
                        self.log_message.emit('info', f'执行右键点击 ({target_x}, {target_y})')
                    elif click_button == 'double':
                        pyautogui.doubleClick(target_x, target_y)
                        self.log_message.emit('info', f'执行双击 ({target_x}, {target_y})')

                return {'found': True, 'x': x, 'y': y, 'confidence': max_val}
            else:
                self.variables['found'] = False
                self.variables['confidence'] = max_val
                self.log_message.emit('info', f'图片判断: 未找到图片 (最高置信度 {max_val:.3f})')
                return {'found': False, 'confidence': max_val}

        except Exception as e:
            raise Exception(f'图片判断失败: {e}')

    def _action_find_color(self, params):
        """找色"""
        try:
            import cv2
            import numpy as np
            import pyautogui

            color = params.get('color', '#FF0000')
            tolerance = int(params.get('tolerance', 10))
            region = params.get('region', [0, 0, 1920, 1080])

            # 解析颜色
            color = color.lstrip('#')
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)

            # 截图
            screenshot = pyautogui.screenshot(region=region)
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # 创建颜色范围
            lower = np.array([max(0, b - tolerance), max(0, g - tolerance), max(0, r - tolerance)])
            upper = np.array([min(255, b + tolerance), min(255, g + tolerance), min(255, r + tolerance)])

            # 查找颜色
            mask = cv2.inRange(screenshot, lower, upper)
            coords = cv2.findNonZero(mask)

            if coords is not None:
                x = coords[0][0][0] + region[0]
                y = coords[0][0][1] + region[1]
                self.variables['found'] = True
                self.variables['color_x'] = x
                self.variables['color_y'] = y
                return {'found': True, 'x': x, 'y': y}
            else:
                self.variables['found'] = False
                return {'found': False}

        except Exception as e:
            raise Exception(f'找色失败: {e}')

    # ===== 测试功能 =====

    def test_single_node(self, node_id, mock_variables=None):
        """单节点测试
        Args:
            node_id: 要测试的节点ID
            mock_variables: Mock输入变量，替代前置节点的输出
        """
        if self.is_running:
            self.log_message.emit('warning', '工作流正在运行中，无法启动测试')
            return None

        mock_variables = mock_variables or {}

        # 查找节点
        node = self.nodes.get(node_id)
        if not node:
            raise ValueError(f"节点 {node_id} 不存在")

        self._test_mode = True
        self._test_target_node_id = node_id
        self.is_running = True
        self.stop_requested = False
        self.execution_started.emit()

        self.log_message.emit('info', f'开始单节点测试: {node.get("title", node_id)}')

        # 保存原始变量并设置Mock变量
        original_variables = self.variables.copy()
        self.variables = {**original_variables, **mock_variables}

        try:
            self.node_started.emit(node_id, node['type'])
            result = self._execute_node(node)
            self.node_finished.emit(node_id, node['type'], result)

            # 保存测试快照
            self.save_test_snapshot(node_id, self.variables)

            self.log_message.emit('info', f'单节点测试完成: {node.get("title", node_id)}')
            return result
        except Exception as e:
            self.log_message.emit('error', f'单节点测试失败: {e}')
            self.execution_error.emit(node_id, str(e))
            raise
        finally:
            # 恢复原始变量
            self.variables = original_variables
            self._test_mode = False
            self._test_target_node_id = None
            self.is_running = False
            self.execution_stopped.emit()

    def run_to_node(self, target_node_id, branch_choices=None):
        """从起点运行到指定节点
        Args:
            target_node_id: 目标节点ID
            branch_choices: 条件分支选择 {node_id: port_index}
        """
        if self.is_running:
            self.log_message.emit('warning', '工作流正在运行中，无法启动测试')
            return None

        if not self.workflow_data:
            self.log_message.emit('error', '没有加载工作流')
            return None

        self._branch_choices = branch_choices or {}
        self._test_target_node_id = target_node_id

        # 找到能到达目标节点的起始节点
        start_nodes = self._find_start_nodes_for_target(target_node_id)
        if not start_nodes:
            self.log_message.emit('error', '没有找到能到达目标节点的起始节点')
            return None

        self.is_running = True
        self.stop_requested = False
        self._break_requested = False
        self._continue_requested = False
        self._loop_stack = []
        self.execution_started.emit()

        self.log_message.emit('info', f'开始运行到节点: {target_node_id}')

        # 在新线程中执行
        self.execution_thread = threading.Thread(
            target=self._execute_to_target,
            args=(start_nodes, target_node_id)
        )
        self.execution_thread.start()

    def _execute_to_target(self, start_nodes, target_node_id):
        """执行到目标节点"""
        try:
            for start_node in start_nodes:
                if self.stop_requested:
                    break
                self._execute_node_chain_to_target(start_node, target_node_id)
        except Exception as e:
            self.log_message.emit('error', f'执行出错: {e}')
            self.execution_error.emit('', str(e))
        finally:
            self._finish_execution()
            self._test_target_node_id = None
            self._branch_choices = {}

    def _execute_node_chain_to_target(self, start_node, target_node_id, exit_nodes=None):
        """执行节点链直到目标节点"""
        current_node = start_node
        exit_nodes = exit_nodes or set()

        while current_node and not self.stop_requested:
            # 检查是否到达目标节点
            if current_node['id'] == target_node_id:
                self.log_message.emit('info', f'已到达目标节点: {current_node.get("title", target_node_id)}')
                break

            # 检查是否到达退出节点
            if current_node['id'] in exit_nodes:
                break

            # 检查暂停
            while self.is_paused and not self.stop_requested:
                time.sleep(0.1)

            if self.stop_requested:
                break

            # 执行当前节点
            node_id = current_node['id']
            node_type = current_node['type']
            self.current_node_id = node_id
            self.node_started.emit(node_id, node_type)

            try:
                result = self._execute_node(current_node)
                self.node_finished.emit(node_id, node_type, result)

                # 处理 break 节点
                if node_type == 'break':
                    if self._loop_stack:
                        self._break_requested = True
                    break

                # 处理 continue 节点
                if node_type == 'continue':
                    if self._loop_stack:
                        self._continue_requested = True
                    break

                # 处理条件节点 - 根据条件选择分支
                if node_type == 'condition':
                    # 检查是否有用户指定的分支选择
                    if node_id in self._branch_choices:
                        port_index = self._branch_choices[node_id]
                        next_node = self._find_next_node_from_port(node_id, port_index)
                        branch_name = "是" if port_index == 0 else "否"
                        self.log_message.emit('info', f'条件判断(用户选择): {branch_name}')
                    else:
                        next_node = self._get_condition_next_node(current_node, result)
                    current_node = next_node
                    continue

                # 处理图片判断节点 - 根据找图结果选择分支
                if node_type == 'if_image':
                    # 检查是否有用户指定的分支选择
                    if node_id in self._branch_choices:
                        port_index = self._branch_choices[node_id]
                        next_node = self._find_next_node_from_port(node_id, port_index)
                        branch_name = "找到" if port_index == 0 else "未找到"
                        self.log_message.emit('info', f'图片判断(用户选择): {branch_name}')
                    else:
                        next_node = self._get_if_image_next_node(current_node, result)
                    current_node = next_node
                    continue

                # 处理循环节点 - 测试模式下只执行一次
                if node_type == 'loop':
                    self._execute_loop_node_test(current_node, exit_nodes)
                    next_node = self._find_next_node_from_port(node_id, port_index=1)
                    current_node = next_node
                    continue

            except Exception as e:
                self.log_message.emit('error', f'节点 {current_node.get("title", node_id)} 执行失败: {e}')
                self.execution_error.emit(node_id, str(e))
                break

            # 找到下一个节点
            current_node = self._find_next_node(node_id)

    def _execute_loop_node_test(self, loop_node, parent_exit_nodes):
        """测试模式下执行循环节点（只执行一次）"""
        body_start = self._find_next_node_from_port(loop_node['id'], port_index=0)
        if not body_start:
            self.log_message.emit('warning', '循环节点没有连接循环体')
            return

        # 构建循环体结束边界
        exit_nodes = set(parent_exit_nodes) if parent_exit_nodes else set()
        end_exit_node = self._find_next_node_from_port(loop_node['id'], port_index=1)
        if end_exit_node:
            exit_nodes.add(end_exit_node['id'])

        self.log_message.emit('info', '循环节点执行一次后退出（测试模式）')

        # 只执行一次循环体
        self._execute_node_chain_to_target(body_start, self._test_target_node_id, exit_nodes)

    def _find_start_nodes_for_target(self, target_node_id):
        """找到能到达目标节点的起始节点"""
        # 找到所有前置节点
        upstream_nodes = self._get_upstream_nodes(target_node_id)

        # 在前置节点中找到起始节点
        start_nodes = []
        for node_id in upstream_nodes:
            node = self.nodes.get(node_id)
            if node and node['type'].startswith('start_'):
                start_nodes.append(node)

        # 如果目标节点本身就是起始节点
        target_node = self.nodes.get(target_node_id)
        if target_node and target_node['type'].startswith('start_'):
            start_nodes.append(target_node)

        return start_nodes

    def _get_upstream_nodes(self, target_node_id):
        """获取目标节点的所有上游节点（包括自身）"""
        upstream = set()
        to_visit = [target_node_id]

        while to_visit:
            node_id = to_visit.pop(0)
            if node_id in upstream:
                continue
            upstream.add(node_id)

            # 查找所有连接到该节点的节点
            for conn in self.connections:
                if conn.get('to') == node_id:
                    from_node_id = conn.get('from')
                    if from_node_id and from_node_id not in upstream:
                        to_visit.append(from_node_id)

        return upstream

    def save_test_snapshot(self, node_id, variables):
        """保存测试快照"""
        import time
        self.test_snapshots[node_id] = {
            "variables": variables.copy(),
            "timestamp": time.time()
        }

    def get_test_snapshot(self, node_id):
        """获取测试快照"""
        return self.test_snapshots.get(node_id)

    def has_test_result(self, node_id):
        """检查是否有测试结果"""
        return node_id in self.test_snapshots

    def get_upstream_outputs(self, target_node_id):
        """获取目标节点所有上游节点的输出定义
        Returns:
            List[{"node_id": str, "node_title": str, "outputs": dict}]
        """
        from ui.node_library import get_node_outputs

        upstream_ids = self._get_upstream_nodes(target_node_id)
        upstream_outputs = []

        for node_id in upstream_ids:
            if node_id == target_node_id:
                continue
            node = self.nodes.get(node_id)
            if node:
                outputs = get_node_outputs(node['type'])
                if outputs:
                    upstream_outputs.append({
                        "node_id": node_id,
                        "node_title": node.get('title', node_id),
                        "node_type": node['type'],
                        "outputs": outputs
                    })

        return upstream_outputs
