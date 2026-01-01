# -*- coding: utf-8 -*-
"""
fix边界条件GUI面板模块
用于在GUI中创建和管理节点约束边界条件
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
                            QPushButton, QListWidget, QListWidgetItem, QMessageBox,
                            QTextEdit, QComboBox, QDialog, QDialogButtonBox, QInputDialog, QLineEdit,
                            QSpinBox, QFormLayout, QTabWidget, QCheckBox)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont, QColor
from typing import Dict, Optional, Any, List

from fiber_section_gui.openseespy_modeling.fix_boundary_manager import FixBoundaryManager, FixBoundary


class FixBoundaryPanel(QWidget):
    """fix边界条件面板"""
    
    # 信号定义
    boundary_changed = pyqtSignal()  # 边界条件变化信号
    
    def __init__(self, fix_boundary_manager: FixBoundaryManager):
        super().__init__()
        self.fix_boundary_manager = fix_boundary_manager
        self.init_ui()
        
        # 连接信号
        self.fix_boundary_manager.boundaries_changed.connect(self.refresh_boundary_list)
        
    def init_ui(self):
        """初始化用户界面"""
        self.setLayout(QVBoxLayout())
        
        # 标题
        title_label = QLabel("fix边界条件管理器")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.layout().addWidget(title_label)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        self.layout().addWidget(self.tab_widget)
        
        # 边界条件管理标签页
        self._create_boundary_management_tab()
        
        # 统计信息标签页
        self._create_statistics_tab()
        
    def _create_boundary_management_tab(self):
        """创建边界条件管理标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 控制按钮组
        control_group = QGroupBox("边界条件控制")
        control_layout = QHBoxLayout(control_group)
        
        self.create_btn = QPushButton("创建边界条件")
        self.create_btn.clicked.connect(self.create_boundary)
        
        self.edit_btn = QPushButton("编辑边界条件")
        self.edit_btn.clicked.connect(self.edit_boundary)
        self.edit_btn.setEnabled(False)
        
        self.delete_btn = QPushButton("删除边界条件")
        self.delete_btn.clicked.connect(self.delete_boundary)
        self.delete_btn.setEnabled(False)
        
        self.clear_btn = QPushButton("清空所有")
        self.clear_btn.clicked.connect(self.clear_all_boundaries)
        
        control_layout.addWidget(self.create_btn)
        control_layout.addWidget(self.edit_btn)
        control_layout.addWidget(self.delete_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.clear_btn)
        
        layout.addWidget(control_group)
        
        # 边界条件列表
        list_group = QGroupBox("边界条件列表")
        list_layout = QVBoxLayout(list_group)
        
        self.boundary_list = QListWidget()
        self.boundary_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.boundary_list.itemDoubleClicked.connect(self.edit_boundary)
        list_layout.addWidget(self.boundary_list)
        
        layout.addWidget(list_group)
        
        # 详细信息显示
        detail_group = QGroupBox("详细信息")
        detail_layout = QVBoxLayout(detail_group)
        
        self.detail_text = QTextEdit()
        self.detail_text.setMaximumHeight(150)
        self.detail_text.setReadOnly(True)
        detail_layout.addWidget(self.detail_text)
        
        layout.addWidget(detail_group)
        
        self.tab_widget.addTab(tab, "边界条件管理")
        
    def _create_statistics_tab(self):
        """创建统计信息标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 统计信息显示
        stats_group = QGroupBox("统计信息")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        stats_layout.addWidget(self.stats_text)
        
        layout.addWidget(stats_group)
        
        self.tab_widget.addTab(tab, "统计信息")
        
        # 刷新统计信息
        self.refresh_statistics()
        
    def refresh_boundary_list(self):
        """刷新边界条件列表"""
        self.boundary_list.clear()
        
        boundaries = self.fix_boundary_manager.get_all_boundaries()
        
        for node_tag, boundary in boundaries.items():
            item = QListWidgetItem()
            item.setText(f"[节点{node_tag}] {boundary.name}")
            item.setData(Qt.UserRole, node_tag)
            
            # 根据约束程度设置颜色
            constraint_count = sum(boundary.constr_values)
            if constraint_count == len(boundary.constr_values):  # 全约束
                item.setForeground(QColor("red"))
            elif constraint_count == 0:  # 全释放
                item.setForeground(QColor("gray"))
            else:  # 部分约束
                item.setForeground(QColor("blue"))
                
            self.boundary_list.addItem(item)
            
        self.refresh_statistics()
        
    def refresh_statistics(self):
        """刷新统计信息"""
        boundaries = self.fix_boundary_manager.get_all_boundaries()
        
        if not boundaries:
            stats_text = "暂无边界条件数据"
        else:
            # 统计信息
            stats = self.fix_boundary_manager.get_constraint_statistics()
            
            stats_lines = [
                f"总边界条件数量: {stats['total_boundaries']}",
                f"约束自由度总数: {stats['constrained_dofs']}",
                f"释放自由度总数: {stats['released_dofs']}",
                f"模型维度: {stats['model_dimension']}D",
                "",
                "节点约束详情:"
            ]
            
            for node_tag, boundary in boundaries.items():
                constraint_summary = boundary.get_constraint_summary()
                stats_lines.append(f"  节点{node_tag}: {constraint_summary}")
                
            stats_text = "\n".join(stats_lines)
            
        self.stats_text.setPlainText(stats_text)
        
    def on_selection_changed(self):
        """选择变化处理"""
        current_item = self.boundary_list.currentItem()
        has_selection = current_item is not None
        
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        
        if has_selection:
            node_tag = current_item.data(Qt.UserRole)
            self.show_boundary_details(node_tag)
        else:
            self.detail_text.clear()
            
    def show_boundary_details(self, node_tag: int):
        """显示边界条件详细信息"""
        boundary = self.fix_boundary_manager.get_boundary(node_tag)
        
        if boundary:
            details = [
                f"节点标签: {boundary.node_tag}",
                f"名称: {boundary.name}",
                f"模型维度: {boundary.model_dim}D",
                f"约束值: {boundary.constr_values}",
                f"约束详情: {boundary.get_constraint_summary()}",
                f"创建时间: {boundary.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"更新时间: {boundary.updated_at.strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "OpenSeesPy代码:",
                boundary.generate_opensees_code()
            ]
            
            self.detail_text.setPlainText("\n".join(details))
            
    def create_boundary(self):
        """创建边界条件"""
        # 获取节点标签
        node_tag, ok = QInputDialog.getInt(
            self, "创建边界条件", "节点标签:", 1, 0, 999, 1
        )
        if not ok:
            return
            
        # 获取边界条件名称
        name, ok = QInputDialog.getText(
            self, "创建边界条件", "输入边界条件名称:",
            QLineEdit.Normal, f"Boundary_Node{node_tag}"
        )
        if not ok or not name:
            return
            
        # 创建约束编辑对话框
        dialog = ConstraintEditDialog(self, self.fix_boundary_manager.model_dim)
        if dialog.exec_() == QDialog.Accepted:
            constr_values = dialog.get_constraint_values()
            
            # 创建边界条件
            success, message, boundary = self.fix_boundary_manager.create_boundary(
                node_tag, name, constr_values
            )
            
            if success:
                QMessageBox.information(self, "成功", f"边界条件创建成功!\n{message}")
                self.boundary_changed.emit()
                self.refresh_boundary_list()
            else:
                QMessageBox.critical(self, "错误", f"创建边界条件失败:\n{message}")
                
    def edit_boundary(self):
        """编辑边界条件"""
        current_item = self.boundary_list.currentItem()
        if not current_item:
            return
            
        node_tag = current_item.data(Qt.UserRole)
        boundary = self.fix_boundary_manager.get_boundary(node_tag)
        
        if not boundary:
            QMessageBox.warning(self, "错误", "找不到指定的边界条件")
            return
            
        # 创建编辑对话框
        dialog = BoundaryEditDialog(self, boundary)
        if dialog.exec_() == QDialog.Accepted:
            self.boundary_changed.emit()
            self.refresh_boundary_list()
            
    def delete_boundary(self):
        """删除边界条件"""
        current_item = self.boundary_list.currentItem()
        if not current_item:
            return
            
        node_tag = current_item.data(Qt.UserRole)
        boundary = self.fix_boundary_manager.get_boundary(node_tag)
        
        if not boundary:
            return
            
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除节点 {node_tag} 的边界条件 '{boundary.name}' 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = self.fix_boundary_manager.delete_boundary(node_tag)
            
            if success:
                QMessageBox.information(self, "成功", message)
                self.boundary_changed.emit()
                self.refresh_boundary_list()
            else:
                QMessageBox.critical(self, "错误", message)
                
    def clear_all_boundaries(self):
        """清空所有边界条件"""
        if self.fix_boundary_manager.get_all_boundaries():
            reply = QMessageBox.question(
                self, "确认清空", 
                "确定要清空所有边界条件吗？此操作不可撤销！",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                success, message = self.fix_boundary_manager.clear_all_boundaries()
                
                if success:
                    QMessageBox.information(self, "成功", message)
                    self.boundary_changed.emit()
                    self.refresh_boundary_list()
                else:
                    QMessageBox.critical(self, "错误", message)
        else:
            QMessageBox.information(self, "提示", "没有边界条件需要清空")
            
    def get_selected_boundary(self) -> Optional[FixBoundary]:
        """获取当前选中的边界条件"""
        current_item = self.boundary_list.currentItem()
        if current_item:
            node_tag = current_item.data(Qt.UserRole)
            return self.fix_boundary_manager.get_boundary(node_tag)
        return None


class ConstraintEditDialog(QDialog):
    """约束编辑对话框"""
    
    def __init__(self, parent, model_dim: int = 3):
        super().__init__(parent)
        self.model_dim = model_dim
        self.constraint_values = []
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("编辑约束条件")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # 约束编辑区域
        constraint_group = QGroupBox("自由度约束")
        constraint_layout = QVBoxLayout(constraint_group)
        
        self.constraint_checkboxes = []
        
        if self.model_dim == 3:
            dof_names = ['Ux', 'Uy', 'Uz', 'Rx', 'Ry', 'Rz']
        else:
            dof_names = ['Ux', 'Uy', 'Rz']
            
        for i, dof_name in enumerate(dof_names):
            checkbox = QCheckBox(f"{dof_name} (1=约束, 0=释放)")
            checkbox.setChecked(True)  # 默认约束
            self.constraint_checkboxes.append(checkbox)
            constraint_layout.addWidget(checkbox)
            
        layout.addWidget(constraint_group)
        
        # 常用约束模式
        pattern_group = QGroupBox("常用约束模式")
        pattern_layout = QVBoxLayout(pattern_group)
        
        self.pattern_combo = QComboBox()
        patterns = self.get_common_patterns()
        for pattern_name in patterns.keys():
            self.pattern_combo.addItem(pattern_name)
        self.pattern_combo.currentTextChanged.connect(self.apply_pattern)
        
        pattern_layout.addWidget(QLabel("选择常用模式:"))
        pattern_layout.addWidget(self.pattern_combo)
        layout.addWidget(pattern_group)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def get_common_patterns(self) -> Dict[str, List[int]]:
        """获取常用约束模式"""
        if self.model_dim == 3:
            return {
                '固定约束': [1, 1, 1, 1, 1, 1],  # 所有自由度约束
                '铰支约束': [1, 1, 1, 0, 0, 0],  # 约束平动，释放转动
                '滚动支座': [0, 1, 0, 0, 0, 0],  # 只约束Uy
                '固定铰支': [1, 1, 0, 0, 0, 0],  # 约束Ux, Uy, 释放其他
                '定向约束': [1, 1, 0, 0, 0, 1],  # 约束Ux, Uy, Rz
                '释放所有': [0, 0, 0, 0, 0, 0]   # 释放所有自由度
            }
        else:
            return {
                '固定约束': [1, 1, 1],  # 所有自由度约束
                '铰支约束': [1, 1, 0],  # 约束平动，释放转动
                '滚动支座': [0, 1, 0],  # 只约束Uy
                '释放所有': [0, 0, 0]   # 释放所有自由度
            }
            
    def apply_pattern(self, pattern_name: str):
        """应用约束模式"""
        patterns = self.get_common_patterns()
        if pattern_name in patterns:
            pattern = patterns[pattern_name]
            for i, checkbox in enumerate(self.constraint_checkboxes):
                if i < len(pattern):
                    checkbox.setChecked(bool(pattern[i]))
                    
    def get_constraint_values(self) -> List[int]:
        """获取约束值列表"""
        return [1 if checkbox.isChecked() else 0 for checkbox in self.constraint_checkboxes]


class BoundaryEditDialog(QDialog):
    """边界条件编辑对话框"""
    
    def __init__(self, parent, boundary: FixBoundary):
        super().__init__(parent)
        self.boundary = boundary
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle(f"编辑边界条件 - {self.boundary.name}")
        self.setModal(True)
        self.resize(400, 350)
        
        layout = QVBoxLayout(self)
        
        # 基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)
        
        # 节点标签（只读）
        self.node_tag_label = QLabel(str(self.boundary.node_tag))
        self.node_tag_label.setStyleSheet("color: blue; font-weight: bold;")
        basic_layout.addRow("节点标签:", self.node_tag_label)
        
        # 名称
        self.name_edit = QLineEdit(self.boundary.name)
        basic_layout.addRow("名称:", self.name_edit)
        
        layout.addWidget(basic_group)
        
        # 约束编辑
        constraint_group = QGroupBox("自由度约束")
        constraint_layout = QVBoxLayout(constraint_group)
        
        self.constraint_checkboxes = []
        
        dof_names = self.boundary.get_dof_names()
        for i, (dof_name, value) in enumerate(zip(dof_names, self.boundary.constr_values)):
            checkbox = QCheckBox(f"{dof_name} (1=约束, 0=释放)")
            checkbox.setChecked(bool(value))
            self.constraint_checkboxes.append(checkbox)
            constraint_layout.addWidget(checkbox)
            
        layout.addWidget(constraint_group)
        
        # 常用约束模式
        pattern_group = QGroupBox("常用约束模式")
        pattern_layout = QVBoxLayout(pattern_group)
        
        self.pattern_combo = QComboBox()
        patterns = self.boundary.manager.get_constraint_patterns() if hasattr(self.boundary.manager, 'get_constraint_patterns') else {
            '固定约束': [1] * len(self.boundary.constr_values),
            '释放所有': [0] * len(self.boundary.constr_values)
        }
        for pattern_name in patterns.keys():
            self.pattern_combo.addItem(pattern_name)
        self.pattern_combo.currentTextChanged.connect(self.apply_pattern)
        
        pattern_layout.addWidget(QLabel("选择常用模式:"))
        pattern_layout.addWidget(self.pattern_combo)
        layout.addWidget(pattern_group)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def apply_pattern(self, pattern_name: str):
        """应用约束模式"""
        if hasattr(self.boundary.manager, 'create_common_boundary_patterns'):
            patterns = self.boundary.manager.create_common_boundary_patterns()
        else:
            patterns = {
                '固定约束': [1] * len(self.boundary.constr_values),
                '释放所有': [0] * len(self.boundary.constr_values)
            }
            
        if pattern_name in patterns:
            pattern = patterns[pattern_name]
            for i, checkbox in enumerate(self.constraint_checkboxes):
                if i < len(pattern):
                    checkbox.setChecked(bool(pattern[i]))
                    
    def accept(self):
        """确认编辑"""
        # 验证输入
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "错误", "名称不能为空")
            return
            
        # 获取约束值
        constr_values = [1 if checkbox.isChecked() else 0 for checkbox in self.constraint_checkboxes]
        
        # 更新边界条件
        node_tag = self.boundary.node_tag
        success, message = self.fix_boundary_manager.update_boundary(
            node_tag,
            name=name,
            constr_values=constr_values
        )
        
        if success:
            super().accept()
        else:
            QMessageBox.critical(self, "错误", message)