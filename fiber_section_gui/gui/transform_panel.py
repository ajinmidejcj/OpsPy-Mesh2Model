#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
坐标系变换管理面板
"""

import sys
import os
from typing import Optional

# PyQt5导入
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
                             QPushButton, QListWidget, QListWidgetItem, QMessageBox,
                             QTextEdit, QComboBox, QDialog, QDialogButtonBox, QInputDialog, QLineEdit)


class TransformPanel(QWidget):
    """坐标系变换管理面板"""
    
    # 信号定义
    transform_changed = pyqtSignal()  # 变换变化信号
    
    def __init__(self, transform_manager, parent=None):
        super().__init__(parent)
        self.transform_manager = transform_manager
        self.setup_ui()
        
        # 连接信号
        self.transform_manager.transforms_changed.connect(self.refresh_transform_list)
        self.refresh_transform_list()
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("坐标系变换管理")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 按钮组
        self.setup_button_group(layout)
        
        # 变换列表
        self.setup_transform_list(layout)
        
        # 详细信息
        self.setup_details_group(layout)
        
        # 代码预览
        self.setup_code_preview(layout)
        
    def setup_button_group(self, parent_layout):
        """设置按钮组"""
        button_group = QGroupBox("操作")
        button_layout = QHBoxLayout(button_group)
        
        self.btn_create_transform = QPushButton("创建变换")
        self.btn_edit_transform = QPushButton("编辑变换")
        self.btn_delete_transform = QPushButton("删除变换")
        self.btn_clear_all = QPushButton("清空所有")
        
        button_layout.addWidget(self.btn_create_transform)
        button_layout.addWidget(self.btn_edit_transform)
        button_layout.addWidget(self.btn_delete_transform)
        button_layout.addWidget(self.btn_clear_all)
        
        # 连接信号
        self.btn_create_transform.clicked.connect(self.create_transform)
        self.btn_edit_transform.clicked.connect(self.edit_transform)
        self.btn_delete_transform.clicked.connect(self.delete_transform)
        self.btn_clear_all.clicked.connect(self.clear_all_transforms)
        
        parent_layout.addWidget(button_group)
        
    def setup_transform_list(self, parent_layout):
        """设置变换列表"""
        list_group = QGroupBox("坐标系变换列表")
        list_layout = QVBoxLayout(list_group)
        
        list_layout.addWidget(QLabel("已创建的坐标系变换:"))
        
        self.transform_list = QListWidget()
        self.transform_list.setMaximumHeight(150)
        self.transform_list.itemSelectionChanged.connect(self.on_transform_selection_changed)
        list_layout.addWidget(self.transform_list)
        
        parent_layout.addWidget(list_group)
        
    def setup_details_group(self, parent_layout):
        """设置详细信息组"""
        details_group = QGroupBox("变换详细信息")
        details_layout = QVBoxLayout(details_group)
        
        # 基本信息
        info_layout = QHBoxLayout()
        
        self.lbl_transform_id = QLabel("ID: -")
        self.lbl_transform_name = QLabel("名称: -")
        self.lbl_transform_type = QLabel("类型: -")
        
        info_layout.addWidget(self.lbl_transform_id)
        info_layout.addWidget(self.lbl_transform_name)
        info_layout.addWidget(self.lbl_transform_type)
        info_layout.addStretch()
        
        details_layout.addLayout(info_layout)
        
        # 参数信息
        self.lbl_transform_params = QLabel("参数: -")
        details_layout.addWidget(self.lbl_transform_params)
        
        parent_layout.addWidget(details_group)
        
    def setup_code_preview(self, parent_layout):
        """设置代码预览"""
        code_group = QGroupBox("OpenSeesPy代码")
        code_layout = QVBoxLayout(code_group)
        
        code_layout.addWidget(QLabel("生成的OpenSeesPy代码:"))
        
        self.code_preview = QTextEdit()
        self.code_preview.setReadOnly(True)
        self.code_preview.setMaximumHeight(200)
        code_layout.addWidget(self.code_preview)
        
        # 复制按钮
        copy_layout = QHBoxLayout()
        copy_layout.addStretch()
        self.btn_copy_code = QPushButton("复制代码")
        self.btn_copy_code.clicked.connect(self.copy_code)
        copy_layout.addWidget(self.btn_copy_code)
        
        code_layout.addLayout(copy_layout)
        
        parent_layout.addWidget(code_group)
        
    def refresh_transform_list(self):
        """刷新变换列表"""
        self.transform_list.clear()
        
        # 获取所有变换并按ID排序
        transforms_dict = self.transform_manager.get_all_transforms()
        transforms = sorted(transforms_dict.values(), key=lambda x: x.id)
        
        for transform in transforms:
            item_text = f"ID {transform.id}: {transform.name} ({transform.type})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, transform.id)
            self.transform_list.addItem(item)
        
        # 更新代码预览
        self.update_code_preview()
        
        # 如果有选中的项，重新选择
        current_item = self.transform_list.currentItem()
        if current_item:
            self.on_transform_selection_changed()
        
    def on_transform_selection_changed(self):
        """变换选择改变"""
        current_item = self.transform_list.currentItem()
        if not current_item:
            self.clear_transform_details()
            return
            
        transform_id = current_item.data(Qt.UserRole)
        transform = self.transform_manager.get_transform(transform_id)
        
        if transform:
            self.display_transform_details(transform)
            
    def display_transform_details(self, transform):
        """显示变换详细信息"""
        self.lbl_transform_id.setText(f"ID: {transform.id}")
        self.lbl_transform_name.setText(f"名称: {transform.name}")
        self.lbl_transform_type.setText(f"类型: {transform.type}")
        
        # 生成参数描述
        if hasattr(transform, 'vecxz'):
            vecxz_str = f"[{', '.join(map(str, transform.vecxz))}]"
            params_text = f"vecxz: {vecxz_str}"
            
            if hasattr(transform, 'use_jnt_offset') and transform.use_jnt_offset:
                if hasattr(transform, 'dI') and hasattr(transform, 'dJ'):
                    dI_str = f"[{', '.join(map(str, transform.dI))}]"
                    dJ_str = f"[{', '.join(map(str, transform.dJ))}]"
                    params_text += f", dI: {dI_str}, dJ: {dJ_str}"
            
            self.lbl_transform_params.setText(f"参数: {params_text}")
        else:
            self.lbl_transform_params.setText("参数: -")
            
    def clear_transform_details(self):
        """清空变换详细信息"""
        self.lbl_transform_id.setText("ID: -")
        self.lbl_transform_name.setText("名称: -")
        self.lbl_transform_type.setText("类型: -")
        self.lbl_transform_params.setText("参数: -")
        
    def update_code_preview(self):
        """更新代码预览"""
        # 获取所有变换的代码
        code = self.transform_manager.generate_all_transform_code()
        
        if code:
            self.code_preview.setPlainText(code)
        else:
            self.code_preview.setPlainText("# 暂无坐标系变换")
            
    def create_transform(self):
        """创建变换 - 使用简化的输入方式"""
        from PyQt5.QtWidgets import QInputDialog, QLineEdit
        
        # 获取变换类型
        transform_type, ok = QInputDialog.getItem(
            self, "创建坐标系变换", "选择变换类型:",
            ["Linear", "PDelta", "Corotational"], 0, False
        )
        if not ok or not transform_type:
            return
            
        # 获取变换名称
        name, ok = QInputDialog.getText(
            self, "创建坐标系变换", "输入变换名称:",
            QLineEdit.Normal, f"{transform_type}_Transform"
        )
        if not ok or not name:
            return
            
        # 获取变换ID
        transform_id_str, ok = QInputDialog.getText(
            self, "创建坐标系变换", "输入变换ID (留空自动分配):",
            QLineEdit.Normal, ""
        )
        transform_id = None
        if ok and transform_id_str.strip():
            try:
                transform_id = int(transform_id_str.strip())
            except ValueError:
                QMessageBox.warning(self, "错误", "变换ID必须是数字")
                return
                
        # 获取方向向量
        vec_x, ok = QInputDialog.getDouble(self, "创建坐标系变换", "方向向量 X:", 0.0, -1000, 1000, 3)
        if not ok:
            return
        vec_y, ok = QInputDialog.getDouble(self, "创建坐标系变换", "方向向量 Y:", 1.0, -1000, 1000, 3)
        if not ok:
            return
        vec_z, ok = QInputDialog.getDouble(self, "创建坐标系变换", "方向向量 Z:", 0.0, -1000, 1000, 3)
        if not ok:
            return
            
        # 对于Linear和PDelta，询问是否使用关节偏移
        use_jnt_offset = False
        dI = [0.0, 0.0, 0.0]
        dJ = [0.0, 0.0, 0.0]
        
        if transform_type in ["Linear", "PDelta"]:
            use_jnt_offset_choice, ok = QInputDialog.getItem(
                self, "关节偏移", "是否使用关节偏移?",
                ["否", "是"], 0, False
            )
            if not ok or not use_jnt_offset_choice:
                return
            use_jnt_offset = use_jnt_offset_choice == "是"
            
            if use_jnt_offset:
                # 获取节点I偏移
                di_x, ok = QInputDialog.getDouble(self, "节点I偏移", "节点I偏移 X:", 0.0, -100, 100, 3)
                if not ok:
                    return
                di_y, ok = QInputDialog.getDouble(self, "节点I偏移", "节点I偏移 Y:", 0.0, -100, 100, 3)
                if not ok:
                    return
                di_z, ok = QInputDialog.getDouble(self, "节点I偏移", "节点I偏移 Z:", 0.0, -100, 100, 3)
                if not ok:
                    return
                dI = [di_x, di_y, di_z]
                
                # 获取节点J偏移
                dj_x, ok = QInputDialog.getDouble(self, "节点J偏移", "节点J偏移 X:", 0.0, -100, 100, 3)
                if not ok:
                    return
                dj_y, ok = QInputDialog.getDouble(self, "节点J偏移", "节点J偏移 Y:", 0.0, -100, 100, 3)
                if not ok:
                    return
                dj_z, ok = QInputDialog.getDouble(self, "节点J偏移", "节点J偏移 Z:", 0.0, -100, 100, 3)
                if not ok:
                    return
                dJ = [dj_x, dj_y, dj_z]
        
        # 创建变换参数
        params = {
            'vecxz': [vec_x, vec_y, vec_z],
            'use_jnt_offset': use_jnt_offset,
            'dI': dI,
            'dJ': dJ
        }
        
        # 创建变换
        success, message, transform = self.transform_manager.create_transform(
            transform_type, name, transform_id, **params
        )
        
        if success:
            QMessageBox.information(self, "成功", f"坐标系变换创建成功!\n{message}")
            self.transform_changed.emit()
            self.refresh_transform_list()
        else:
            QMessageBox.critical(self, "错误", f"创建变换失败:\n{message}")
                
    def edit_transform(self):
        """编辑变换"""
        current_item = self.transform_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请选择一个要编辑的变换")
            return
            
        transform_id = current_item.data(Qt.UserRole)
        QMessageBox.information(self, "提示", "编辑功能待实现")
        
    def delete_transform(self):
        """删除变换"""
        current_item = self.transform_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请选择一个要删除的变换")
            return
            
        transform_id = current_item.data(Qt.UserRole)
        transform = self.transform_manager.get_transform(transform_id)
        
        if not transform:
            return
            
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除变换 '{transform.name}' 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.transform_manager.delete_transform(transform_id):
                self.transform_changed.emit()
                self.refresh_transform_list()
            else:
                QMessageBox.critical(self, "错误", "删除变换失败")
                
    def clear_all_transforms(self):
        """清空所有变换"""
        if not self.transform_manager.get_all_transforms():
            QMessageBox.information(self, "提示", "没有要清空的变换")
            return
            
        # 确认清空
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要删除所有坐标系变换吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.transform_manager.clear_all_transforms()
            self.transform_changed.emit()
            self.refresh_transform_list()
            
    def copy_code(self):
        """复制代码到剪贴板"""
        code = self.code_preview.toPlainText()
        if code and code.strip():
            clipboard = self.parent().clipboard() if self.parent() else None
            if clipboard:
                clipboard.setText(code)
                QMessageBox.information(self, "提示", "代码已复制到剪贴板")
            else:
                QMessageBox.warning(self, "警告", "无法访问剪贴板")
        else:
            QMessageBox.information(self, "提示", "没有代码可复制")