#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
坐标系变换创建对话框
"""

import sys
import os
from typing import Optional, Tuple

# PyQt5导入
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QWidget, QFormLayout, QLabel, QLineEdit, QPushButton,
                             QComboBox, QDoubleSpinBox, QCheckBox, QMessageBox,
                             QTextEdit)


class TransformCreationDialog(QDialog):
    """坐标系变换创建对话框"""
    
    def __init__(self, transform_manager, parent=None):
        super().__init__(parent)
        self.transform_manager = transform_manager
        self.created_transform = None
        self.setWindowTitle("创建新坐标系变换")
        self.setModal(True)
        self.resize(600, 500)
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # 基本信息标签页
        self.setup_basic_tab()
        
        # Linear变换标签页
        self.setup_linear_tab()
        
        # PDelta变换标签页
        self.setup_pdelta_tab()
        
        # Corotational变换标签页
        self.setup_corotational_tab()
        
        # 按钮
        button_layout = QHBoxLayout()
        self.create_btn = QPushButton("创建")
        self.cancel_btn = QPushButton("取消")
        button_layout.addWidget(self.create_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        # 连接信号
        self.create_btn.clicked.connect(self.create_transform)
        self.cancel_btn.clicked.connect(self.reject)
        
    def setup_basic_tab(self):
        """设置基本信息标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        form_layout = QFormLayout()
        
        # 变换类型
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Linear", "PDelta", "Corotational"])
        form_layout.addRow("变换类型:", self.type_combo)
        
        # 变换名称
        self.name_edit = QLineEdit()
        form_layout.addRow("变换名称:", self.name_edit)
        
        layout.addLayout(form_layout)
        
        # 代码预览
        self.code_preview = QTextEdit()
        self.code_preview.setReadOnly(True)
        self.code_preview.setMaximumHeight(200)
        layout.addWidget(QLabel("OpenSeesPy代码预览:"))
        layout.addWidget(self.code_preview)
        
        self.tab_widget.addTab(widget, "基本信息")
        
        # 连接信号
        self.type_combo.currentTextChanged.connect(self.update_code_preview)
        self.name_edit.textChanged.connect(self.update_code_preview)
        
        self.update_code_preview()
        
    def setup_linear_tab(self):
        """设置Linear变换标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # XZ平面方向向量组
        vecxz_group = QWidget()
        vecxz_layout = QFormLayout(vecxz_group)
        
        vecxz_layout.addRow(QLabel("XZ平面方向向量 vecxz:"))
        
        # vecxz分量输入
        self.linear_vecx = QDoubleSpinBox()
        self.linear_vecx.setRange(-1000.0, 1000.0)
        self.linear_vecx.setValue(0.0)
        vecxz_layout.addRow("X分量:", self.linear_vecx)
        
        self.linear_vecy = QDoubleSpinBox()
        self.linear_vecy.setRange(-1000.0, 1000.0)
        self.linear_vecy.setValue(0.0)
        vecxz_layout.addRow("Y分量:", self.linear_vecy)
        
        self.linear_vecz = QDoubleSpinBox()
        self.linear_vecz.setRange(-1000.0, 1000.0)
        self.linear_vecz.setValue(1.0)
        vecxz_layout.addRow("Z分量:", self.linear_vecz)
        
        layout.addWidget(vecxz_group)
        
        # 节点偏移选项
        self.linear_use_offset = QCheckBox("使用节点偏移 (-jntOffset)")
        layout.addWidget(self.linear_use_offset)
        
        # 节点I偏移
        di_group = QWidget()
        di_layout = QFormLayout(di_group)
        di_layout.addRow(QLabel("节点I偏移 dI:"))
        
        self.linear_di_x = QDoubleSpinBox()
        self.linear_di_x.setRange(-1000.0, 1000.0)
        self.linear_di_x.setValue(0.0)
        di_layout.addRow("X偏移:", self.linear_di_x)
        
        self.linear_di_y = QDoubleSpinBox()
        self.linear_di_y.setRange(-1000.0, 1000.0)
        self.linear_di_y.setValue(0.0)
        di_layout.addRow("Y偏移:", self.linear_di_y)
        
        self.linear_di_z = QDoubleSpinBox()
        self.linear_di_z.setRange(-1000.0, 1000.0)
        self.linear_di_z.setValue(0.0)
        di_layout.addRow("Z偏移:", self.linear_di_z)
        
        layout.addWidget(di_group)
        
        # 节点J偏移
        dj_group = QWidget()
        dj_layout = QFormLayout(dj_group)
        dj_layout.addRow(QLabel("节点J偏移 dJ:"))
        
        self.linear_dj_x = QDoubleSpinBox()
        self.linear_dj_x.setRange(-1000.0, 1000.0)
        self.linear_dj_x.setValue(0.0)
        dj_layout.addRow("X偏移:", self.linear_dj_x)
        
        self.linear_dj_y = QDoubleSpinBox()
        self.linear_dj_y.setRange(-1000.0, 1000.0)
        self.linear_dj_y.setValue(0.0)
        dj_layout.addRow("Y偏移:", self.linear_dj_y)
        
        self.linear_dj_z = QDoubleSpinBox()
        self.linear_dj_z.setRange(-1000.0, 1000.0)
        self.linear_dj_z.setValue(0.0)
        dj_layout.addRow("Z偏移:", self.linear_dj_z)
        
        layout.addWidget(dj_group)
        
        self.tab_widget.addTab(widget, "Linear变换")
        
        # 连接信号
        for spinbox in [self.linear_vecx, self.linear_vecy, self.linear_vecz,
                       self.linear_di_x, self.linear_di_y, self.linear_di_z,
                       self.linear_dj_x, self.linear_dj_y, self.linear_dj_z]:
            spinbox.valueChanged.connect(self.update_code_preview)
        
        self.linear_use_offset.stateChanged.connect(self.update_code_preview)
        
    def setup_pdelta_tab(self):
        """设置PDelta变换标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # XZ平面方向向量组
        vecxz_group = QWidget()
        vecxz_layout = QFormLayout(vecxz_group)
        
        vecxz_layout.addRow(QLabel("XZ平面方向向量 vecxz:"))
        
        # vecxz分量输入
        self.pdelta_vecx = QDoubleSpinBox()
        self.pdelta_vecx.setRange(-1000.0, 1000.0)
        self.pdelta_vecx.setValue(0.0)
        vecxz_layout.addRow("X分量:", self.pdelta_vecx)
        
        self.pdelta_vecy = QDoubleSpinBox()
        self.pdelta_vecy.setRange(-1000.0, 1000.0)
        self.pdelta_vecy.setValue(0.0)
        vecxz_layout.addRow("Y分量:", self.pdelta_vecy)
        
        self.pdelta_vecz = QDoubleSpinBox()
        self.pdelta_vecz.setRange(-1000.0, 1000.0)
        self.pdelta_vecz.setValue(1.0)
        vecxz_layout.addRow("Z分量:", self.pdelta_vecz)
        
        layout.addWidget(vecxz_group)
        
        # 节点偏移选项
        self.pdelta_use_offset = QCheckBox("使用节点偏移 (-jntOffset)")
        layout.addWidget(self.pdelta_use_offset)
        
        # 节点I偏移
        di_group = QWidget()
        di_layout = QFormLayout(di_group)
        di_layout.addRow(QLabel("节点I偏移 dI:"))
        
        self.pdelta_di_x = QDoubleSpinBox()
        self.pdelta_di_x.setRange(-1000.0, 1000.0)
        self.pdelta_di_x.setValue(0.0)
        di_layout.addRow("X偏移:", self.pdelta_di_x)
        
        self.pdelta_di_y = QDoubleSpinBox()
        self.pdelta_di_y.setRange(-1000.0, 1000.0)
        self.pdelta_di_y.setValue(0.0)
        di_layout.addRow("Y偏移:", self.pdelta_di_y)
        
        self.pdelta_di_z = QDoubleSpinBox()
        self.pdelta_di_z.setRange(-1000.0, 1000.0)
        self.pdelta_di_z.setValue(0.0)
        di_layout.addRow("Z偏移:", self.pdelta_di_z)
        
        layout.addWidget(di_group)
        
        # 节点J偏移
        dj_group = QWidget()
        dj_layout = QFormLayout(dj_group)
        dj_layout.addRow(QLabel("节点J偏移 dJ:"))
        
        self.pdelta_dj_x = QDoubleSpinBox()
        self.pdelta_dj_x.setRange(-1000.0, 1000.0)
        self.pdelta_dj_x.setValue(0.0)
        dj_layout.addRow("X偏移:", self.pdelta_dj_x)
        
        self.pdelta_dj_y = QDoubleSpinBox()
        self.pdelta_dj_y.setRange(-1000.0, 1000.0)
        self.pdelta_dj_y.setValue(0.0)
        dj_layout.addRow("Y偏移:", self.pdelta_dj_y)
        
        self.pdelta_dj_z = QDoubleSpinBox()
        self.pdelta_dj_z.setRange(-1000.0, 1000.0)
        self.pdelta_dj_z.setValue(0.0)
        dj_layout.addRow("Z偏移:", self.pdelta_dj_z)
        
        layout.addWidget(dj_group)
        
        self.tab_widget.addTab(widget, "PDelta变换")
        
        # 连接信号
        for spinbox in [self.pdelta_vecx, self.pdelta_vecy, self.pdelta_vecz,
                       self.pdelta_di_x, self.pdelta_di_y, self.pdelta_di_z,
                       self.pdelta_dj_x, self.pdelta_dj_y, self.pdelta_dj_z]:
            spinbox.valueChanged.connect(self.update_code_preview)
        
        self.pdelta_use_offset.stateChanged.connect(self.update_code_preview)
        
    def setup_corotational_tab(self):
        """设置Corotational变换标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # XZ平面方向向量组
        vecxz_group = QWidget()
        vecxz_layout = QFormLayout(vecxz_group)
        
        vecxz_layout.addRow(QLabel("XZ平面方向向量 vecxz:"))
        
        # vecxz分量输入
        self.corot_vecx = QDoubleSpinBox()
        self.corot_vecx.setRange(-1000.0, 1000.0)
        self.corot_vecx.setValue(0.0)
        vecxz_layout.addRow("X分量:", self.corot_vecx)
        
        self.corot_vecy = QDoubleSpinBox()
        self.corot_vecy.setRange(-1000.0, 1000.0)
        self.corot_vecy.setValue(0.0)
        vecxz_layout.addRow("Y分量:", self.corot_vecy)
        
        self.corot_vecz = QDoubleSpinBox()
        self.corot_vecz.setRange(-1000.0, 1000.0)
        self.corot_vecz.setValue(1.0)
        vecxz_layout.addRow("Z分量:", self.corot_vecz)
        
        layout.addWidget(vecxz_group)
        
        self.tab_widget.addTab(widget, "Corotational变换")
        
        # 连接信号
        for spinbox in [self.corot_vecx, self.corot_vecy, self.corot_vecz]:
            spinbox.valueChanged.connect(self.update_code_preview)
            
    def update_code_preview(self):
        """更新代码预览"""
        transform_type = self.type_combo.currentText()
        name = self.name_edit.text().strip()
        
        if not name:
            self.code_preview.setPlainText("# 请输入变换名称")
            return
            
        try:
            # 根据变换类型生成预览代码
            if transform_type == "Linear":
                vecxz = [self.linear_vecx.value(), self.linear_vecy.value(), self.linear_vecz.value()]
                use_offset = self.linear_use_offset.isChecked()
                
                vecxz_str = ', '.join(map(str, vecxz))
                
                if use_offset:
                    dI = [self.linear_di_x.value(), self.linear_di_y.value(), self.linear_di_z.value()]
                    dJ = [self.linear_dj_x.value(), self.linear_dj_y.value(), self.linear_dj_z.value()]
                    dI_str = ', '.join(map(str, dI))
                    dJ_str = ', '.join(map(str, dJ))
                    code = f"geomTransf('Linear', <transfTag>, {vecxz_str}, '-jntOffset', {dI_str}, {dJ_str})"
                else:
                    code = f"geomTransf('Linear', <transfTag>, {vecxz_str})"
                    
            elif transform_type == "PDelta":
                vecxz = [self.pdelta_vecx.value(), self.pdelta_vecy.value(), self.pdelta_vecz.value()]
                use_offset = self.pdelta_use_offset.isChecked()
                
                vecxz_str = ', '.join(map(str, vecxz))
                
                if use_offset:
                    dI = [self.pdelta_di_x.value(), self.pdelta_di_y.value(), self.pdelta_di_z.value()]
                    dJ = [self.pdelta_dj_x.value(), self.pdelta_dj_y.value(), self.pdelta_dj_z.value()]
                    dI_str = ', '.join(map(str, dI))
                    dJ_str = ', '.join(map(str, dJ))
                    code = f"geomTransf('PDelta', <transfTag>, {vecxz_str}, '-jntOffset', {dI_str}, {dJ_str})"
                else:
                    code = f"geomTransf('PDelta', <transfTag>, {vecxz_str})"
                    
            elif transform_type == "Corotational":
                vecxz = [self.corot_vecx.value(), self.corot_vecy.value(), self.corot_vecz.value()]
                vecxz_str = ', '.join(map(str, vecxz))
                code = f"geomTransf('Corotational', <transfTag>, {vecxz_str})"
            
            self.code_preview.setPlainText(code)
            
        except Exception as e:
            self.code_preview.setPlainText(f"# 生成代码失败: {str(e)}")
    
    def create_transform(self):
        """创建变换"""
        transform_type = self.type_combo.currentText()
        name = self.name_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "警告", "请输入变换名称")
            return
            
        try:
            # 根据变换类型收集参数
            if transform_type == "Linear":
                vecxz = [self.linear_vecx.value(), self.linear_vecy.value(), self.linear_vecz.value()]
                use_offset = self.linear_use_offset.isChecked()
                
                if use_offset:
                    dI = [self.linear_di_x.value(), self.linear_di_y.value(), self.linear_di_z.value()]
                    dJ = [self.linear_dj_x.value(), self.linear_dj_y.value(), self.linear_dj_z.value()]
                    kwargs = {
                        'vecxz': vecxz,
                        'use_jnt_offset': True,
                        'dI': dI,
                        'dJ': dJ
                    }
                else:
                    kwargs = {
                        'vecxz': vecxz,
                        'use_jnt_offset': False
                    }
                    
            elif transform_type == "PDelta":
                vecxz = [self.pdelta_vecx.value(), self.pdelta_vecy.value(), self.pdelta_vecz.value()]
                use_offset = self.pdelta_use_offset.isChecked()
                
                if use_offset:
                    dI = [self.pdelta_di_x.value(), self.pdelta_di_y.value(), self.pdelta_di_z.value()]
                    dJ = [self.pdelta_dj_x.value(), self.pdelta_dj_y.value(), self.pdelta_dj_z.value()]
                    kwargs = {
                        'vecxz': vecxz,
                        'use_jnt_offset': True,
                        'dI': dI,
                        'dJ': dJ
                    }
                else:
                    kwargs = {
                        'vecxz': vecxz,
                        'use_jnt_offset': False
                    }
                    
            elif transform_type == "Corotational":
                vecxz = [self.corot_vecx.value(), self.corot_vecy.value(), self.corot_vecz.value()]
                kwargs = {
                    'vecxz': vecxz
                }
            
            # 创建变换
            success, msg, transform = self.transform_manager.create_transform(
                transform_type, name, **kwargs
            )
            
            if success:
                self.created_transform = transform
                self.accept()
            else:
                QMessageBox.critical(self, "错误", f"创建变换失败: {msg}")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建变换时发生错误: {str(e)}")
    
    def get_created_transform(self) -> Optional[object]:
        """获取创建的变换对象"""
        return self.created_transform