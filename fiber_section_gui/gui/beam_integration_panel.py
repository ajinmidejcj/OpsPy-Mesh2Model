# -*- coding: utf-8 -*-
"""
beamIntegration GUI面板模块
用于在GUI中创建和管理梁单元积分方案
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
                            QPushButton, QListWidget, QListWidgetItem, QMessageBox,
                            QTextEdit, QComboBox, QDialog, QDialogButtonBox, QInputDialog, QLineEdit,
                            QSpinBox, QFormLayout, QTabWidget)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont, QColor
from typing import Dict, Optional, Any

from fiber_section_gui.openseespy_modeling.beam_integration_manager import BeamIntegrationManager, BeamIntegration


class BeamIntegrationPanel(QWidget):
    """beamIntegration面板"""
    
    # 信号定义
    integration_changed = pyqtSignal()  # 积分方案变化信号
    
    def __init__(self, beam_integration_manager: BeamIntegrationManager):
        super().__init__()
        self.beam_integration_manager = beam_integration_manager
        self.init_ui()
        
        # 连接信号
        self.beam_integration_manager.integrations_changed.connect(self.refresh_integration_list)
        
    def init_ui(self):
        """初始化用户界面"""
        self.setLayout(QVBoxLayout())
        
        # 标题
        title_label = QLabel("beamIntegration 管理器")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.layout().addWidget(title_label)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        self.layout().addWidget(self.tab_widget)
        
        # 积分方案管理标签页
        self._create_integration_management_tab()
        
        # 统计信息标签页
        self._create_statistics_tab()
        
    def _create_integration_management_tab(self):
        """创建积分方案管理标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 控制按钮组
        control_group = QGroupBox("积分方案控制")
        control_layout = QHBoxLayout(control_group)
        
        self.create_btn = QPushButton("创建积分方案")
        self.create_btn.clicked.connect(self.create_integration)
        
        self.edit_btn = QPushButton("编辑积分方案")
        self.edit_btn.clicked.connect(self.edit_integration)
        self.edit_btn.setEnabled(False)
        
        self.delete_btn = QPushButton("删除积分方案")
        self.delete_btn.clicked.connect(self.delete_integration)
        self.delete_btn.setEnabled(False)
        
        self.clear_btn = QPushButton("清空所有")
        self.clear_btn.clicked.connect(self.clear_all_integrations)
        
        control_layout.addWidget(self.create_btn)
        control_layout.addWidget(self.edit_btn)
        control_layout.addWidget(self.delete_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.clear_btn)
        
        layout.addWidget(control_group)
        
        # 积分方案列表
        list_group = QGroupBox("积分方案列表")
        list_layout = QVBoxLayout(list_group)
        
        self.integration_list = QListWidget()
        self.integration_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.integration_list.itemDoubleClicked.connect(self.edit_integration)
        list_layout.addWidget(self.integration_list)
        
        layout.addWidget(list_group)
        
        # 详细信息显示
        detail_group = QGroupBox("详细信息")
        detail_layout = QVBoxLayout(detail_group)
        
        self.detail_text = QTextEdit()
        self.detail_text.setMaximumHeight(150)
        self.detail_text.setReadOnly(True)
        detail_layout.addWidget(self.detail_text)
        
        layout.addWidget(detail_group)
        
        self.tab_widget.addTab(tab, "积分方案管理")
        
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
        
    def refresh_integration_list(self):
        """刷新积分方案列表"""
        self.integration_list.clear()
        
        integrations = self.beam_integration_manager.get_all_integrations()
        
        for integration_id, integration in integrations.items():
            item = QListWidgetItem()
            item.setText(f"[{integration_id}] {integration.name} ({integration.type})")
            item.setData(Qt.UserRole, integration_id)
            
            # 根据类型设置颜色
            if integration.type == 'Lobatto':
                item.setForeground(QColor("blue"))
            elif integration.type == 'NewtonCotes':
                item.setForeground(QColor("green"))
                
            self.integration_list.addItem(item)
            
        self.refresh_statistics()
        
    def refresh_statistics(self):
        """刷新统计信息"""
        integrations = self.beam_integration_manager.get_all_integrations()
        
        if not integrations:
            stats_text = "暂无积分方案数据"
        else:
            # 统计信息
            total_count = len(integrations)
            type_count = {}
            
            for integration in integrations.values():
                type_count[integration.type] = type_count.get(integration.type, 0) + 1
                
            stats_lines = [
                f"总积分方案数量: {total_count}",
                "",
                "按类型分布:"
            ]
            
            for integration_type, count in type_count.items():
                stats_lines.append(f"  {integration_type}: {count}个")
                
            stats_text = "\n".join(stats_lines)
            
        self.stats_text.setPlainText(stats_text)
        
    def on_selection_changed(self):
        """选择变化处理"""
        current_item = self.integration_list.currentItem()
        has_selection = current_item is not None
        
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        
        if has_selection:
            integration_id = current_item.data(Qt.UserRole)
            self.show_integration_details(integration_id)
        else:
            self.detail_text.clear()
            
    def show_integration_details(self, integration_id: int):
        """显示积分方案详细信息"""
        integration = self.beam_integration_manager.get_integration(integration_id)
        
        if integration:
            details = [
                f"ID: {integration.id}",
                f"名称: {integration.name}",
                f"类型: {integration.type}",
                f"截面标签: {integration.secTag}",
                f"积分点数量: {integration.n}",
                f"创建时间: {integration.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"更新时间: {integration.updated_at.strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "OpenSeesPy代码:",
                integration.generate_opensees_code()
            ]
            
            self.detail_text.setPlainText("\n".join(details))
            
    def create_integration(self):
        """创建积分方案"""
        # 获取积分类型
        integration_type, ok = QInputDialog.getItem(
            self, "创建积分方案", "选择积分类型:",
            ["Lobatto", "NewtonCotes"], 0, False
        )
        if not ok or not integration_type:
            return
            
        # 获取积分方案名称
        name, ok = QInputDialog.getText(
            self, "创建积分方案", "输入积分方案名称:",
            QLineEdit.Normal, f"{integration_type}_Integration"
        )
        if not ok or not name:
            return
            
        # 获取积分方案ID
        integration_id_str, ok = QInputDialog.getText(
            self, "创建积分方案", "输入积分方案ID (留空自动分配):",
            QLineEdit.Normal, ""
        )
        integration_id = None
        if ok and integration_id_str.strip():
            try:
                integration_id = int(integration_id_str.strip())
            except ValueError:
                QMessageBox.warning(self, "错误", "积分方案ID必须是数字")
                return
                
        # 获取截面标签
        sec_tag, ok = QInputDialog.getInt(
            self, "创建积分方案", "截面标签:", 1, 1, 999, 1
        )
        if not ok:
            return
            
        # 获取积分点数量
        n_points, ok = QInputDialog.getInt(
            self, "创建积分方案", "积分点数量:", 6, 2, 20, 1
        )
        if not ok:
            return
            
        # 创建积分方案
        params = {
            'secTag': sec_tag,
            'n': n_points
        }
        
        success, message, integration = self.beam_integration_manager.create_integration(
            integration_type, name, integration_id, **params
        )
        
        if success:
            QMessageBox.information(self, "成功", f"积分方案创建成功!\n{message}")
            self.integration_changed.emit()
            self.refresh_integration_list()
        else:
            QMessageBox.critical(self, "错误", f"创建积分方案失败:\n{message}")
            
    def edit_integration(self):
        """编辑积分方案"""
        current_item = self.integration_list.currentItem()
        if not current_item:
            return
            
        integration_id = current_item.data(Qt.UserRole)
        integration = self.beam_integration_manager.get_integration(integration_id)
        
        if not integration:
            QMessageBox.warning(self, "错误", "找不到指定的积分方案")
            return
            
        # 创建编辑对话框
        dialog = IntegrationEditDialog(self, integration)
        if dialog.exec_() == QDialog.Accepted:
            self.integration_changed.emit()
            self.refresh_integration_list()
            
    def delete_integration(self):
        """删除积分方案"""
        current_item = self.integration_list.currentItem()
        if not current_item:
            return
            
        integration_id = current_item.data(Qt.UserRole)
        integration = self.beam_integration_manager.get_integration(integration_id)
        
        if not integration:
            return
            
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除积分方案 '{integration.name}' 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = self.beam_integration_manager.delete_integration(integration_id)
            
            if success:
                QMessageBox.information(self, "成功", message)
                self.integration_changed.emit()
                self.refresh_integration_list()
            else:
                QMessageBox.critical(self, "错误", message)
                
    def clear_all_integrations(self):
        """清空所有积分方案"""
        if self.beam_integration_manager.get_all_integrations():
            reply = QMessageBox.question(
                self, "确认清空", 
                "确定要清空所有积分方案吗？此操作不可撤销！",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                success, message = self.beam_integration_manager.clear_all_integrations()
                
                if success:
                    QMessageBox.information(self, "成功", message)
                    self.integration_changed.emit()
                    self.refresh_integration_list()
                else:
                    QMessageBox.critical(self, "错误", message)
        else:
            QMessageBox.information(self, "提示", "没有积分方案需要清空")
            
    def get_selected_integration(self) -> Optional[BeamIntegration]:
        """获取当前选中的积分方案"""
        current_item = self.integration_list.currentItem()
        if current_item:
            integration_id = current_item.data(Qt.UserRole)
            return self.beam_integration_manager.get_integration(integration_id)
        return None


class IntegrationEditDialog(QDialog):
    """积分方案编辑对话框"""
    
    def __init__(self, parent, integration: BeamIntegration):
        super().__init__(parent)
        self.integration = integration
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle(f"编辑积分方案 - {self.integration.name}")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # 表单布局
        form_layout = QFormLayout()
        
        # 名称
        self.name_edit = QLineEdit(self.integration.name)
        form_layout.addRow("名称:", self.name_edit)
        
        # 类型（只读）
        type_layout = QHBoxLayout()
        self.type_label = QLabel(self.integration.type)
        self.type_label.setStyleSheet("color: blue; font-weight: bold;")
        type_layout.addWidget(self.type_label)
        type_layout.addStretch()
        form_layout.addRow("类型:", type_layout)
        
        # 截面标签
        self.sec_tag_spin = QSpinBox()
        self.sec_tag_spin.setRange(1, 999)
        self.sec_tag_spin.setValue(self.integration.secTag)
        form_layout.addRow("截面标签:", self.sec_tag_spin)
        
        # 积分点数量
        self.n_spin = QSpinBox()
        self.n_spin.setRange(2, 20)
        self.n_spin.setValue(self.integration.n)
        form_layout.addRow("积分点数量:", self.n_spin)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def accept(self):
        """确认编辑"""
        # 验证输入
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "错误", "名称不能为空")
            return
            
        # 更新积分方案
        integration_id = self.integration.id
        success, message = self.integration.manager.update_integration(
            integration_id,
            name=name,
            secTag=self.sec_tag_spin.value(),
            n=self.n_spin.value()
        )
        
        if success:
            super().accept()
        else:
            QMessageBox.critical(self, "错误", message)