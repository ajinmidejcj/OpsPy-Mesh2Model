# -*- coding: utf-8 -*-
"""
fix边界条件管理模块
用于通过OpenSeesPy交互的方式创建和管理节点约束
支持多自由度约束，1为约束，0为释放
"""

import openseespy.opensees as ops
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QInputDialog, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, QTextEdit, QLabel, QTabWidget
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import uuid


class FixBoundary:
    """fix边界条件基类"""
    
    def __init__(self, node_tag: int, name: str, constr_values: List[int], model_dim: int = 3):
        self.node_tag = node_tag
        self.name = name
        self.constr_values = constr_values  # 约束值列表
        self.model_dim = model_dim  # 模型维度
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.tags = []
        self.user_data = {}
        
    def generate_opensees_code(self) -> str:
        """生成OpenSeesPy fix边界条件代码"""
        constr_str = ', '.join(map(str, self.constr_values))
        return f"fix({self.node_tag}, {constr_str})  # {self.name}"
        
    def validate_parameters(self) -> Tuple[bool, str]:
        """验证边界条件参数"""
        if self.node_tag < 0:
            return False, "节点标签必须为非负整数"
            
        expected_dof = 6 if self.model_dim == 3 else 3
        if len(self.constr_values) != expected_dof:
            return False, f"约束值数量必须为{expected_dof}个（对应{model_dim}D模型的自由度数量）"
            
        for i, value in enumerate(self.constr_values):
            if value not in [0, 1]:
                return False, f"约束值必须是0或1，第{i+1}个值无效"
                
        return True, "参数验证通过"
        
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'node_tag': self.node_tag,
            'name': self.name,
            'constr_values': self.constr_values,
            'model_dim': self.model_dim,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'tags': self.tags,
            'user_data': self.user_data
        }
        
    def from_dict(self, data: Dict) -> bool:
        """从字典加载数据"""
        try:
            self.node_tag = data.get('node_tag', self.node_tag)
            self.name = data.get('name', self.name)
            self.constr_values = data.get('constr_values', self.constr_values)
            self.model_dim = data.get('model_dim', self.model_dim)
            self.tags = data.get('tags', [])
            self.user_data = data.get('user_data', {})
            return True
        except Exception:
            return False
            
    def get_dof_names(self) -> List[str]:
        """获取自由度名称列表"""
        if self.model_dim == 3:
            return ['Ux', 'Uy', 'Uz', 'Rx', 'Ry', 'Rz']  # 3D: 6个自由度
        else:
            return ['Ux', 'Uy', 'Rz']  # 2D: 3个自由度
            
    def get_constraint_summary(self) -> str:
        """获取约束摘要"""
        dof_names = self.get_dof_names()
        constraints = []
        
        for i, (dof_name, value) in enumerate(zip(dof_names, self.constr_values)):
            if value == 1:
                constraints.append(f"{dof_name}(约束)")
            else:
                constraints.append(f"{dof_name}(释放)")
                
        return ", ".join(constraints)


class FixBoundaryManager(QObject):
    """fix边界条件管理器"""
    
    # 信号定义
    boundary_added = pyqtSignal(object)  # 边界条件添加信号
    boundary_updated = pyqtSignal(object)  # 边界条件更新信号
    boundary_deleted = pyqtSignal(int)  # 边界条件删除信号
    boundaries_cleared = pyqtSignal()  # 清空所有边界条件信号
    boundaries_changed = pyqtSignal()  # 边界条件数据变化信号
    
    def __init__(self):
        super().__init__()
        self.boundaries: Dict[int, FixBoundary] = {}  # 边界条件字典，以node_tag为键
        self.model_dim = 3  # 默认3D模型
        
    def set_model_dimension(self, dim: int):
        """设置模型维度"""
        if dim in [2, 3]:
            self.model_dim = dim
            
    def create_boundary(self, node_tag: int, name: str, constr_values: Optional[List[int]] = None) -> Tuple[bool, str, Optional[FixBoundary]]:
        """
        创建fix边界条件
        
        Args:
            node_tag: 节点标签
            name: 边界条件名称
            constr_values: 约束值列表（可选，如果未提供则创建默认约束）
            
        Returns:
            Tuple[bool, str, FixBoundary]: (是否成功, 错误信息, 边界条件对象)
        """
        # 检查节点标签是否已存在
        if node_tag in self.boundaries:
            return False, f"节点标签 {node_tag} 已存在边界条件", None
            
        # 如果没有提供约束值，创建默认约束
        if constr_values is None:
            constr_values = [1] * (6 if self.model_dim == 3 else 3)  # 默认约束所有自由度
            
        try:
            # 创建边界条件对象
            boundary = FixBoundary(node_tag, name, constr_values, self.model_dim)
            
            # 验证参数
            valid, message = boundary.validate_parameters()
            if not valid:
                return False, message, None
                
            # 添加到管理器
            self.boundaries[node_tag] = boundary
            
            # 发射信号
            self.boundary_added.emit(boundary)
            self.boundaries_changed.emit()
            
            return True, "边界条件创建成功", boundary
            
        except Exception as e:
            return False, f"创建边界条件失败: {str(e)}", None
            
    def get_boundary(self, node_tag: int) -> Optional[FixBoundary]:
        """获取指定节点标签的边界条件"""
        return self.boundaries.get(node_tag)
        
    def get_all_boundaries(self) -> Dict[int, FixBoundary]:
        """获取所有边界条件"""
        return self.boundaries.copy()
        
    def update_boundary(self, node_tag: int, **kwargs) -> Tuple[bool, str]:
        """更新边界条件"""
        if node_tag not in self.boundaries:
            return False, f"节点标签 {node_tag} 不存在边界条件"
            
        boundary = self.boundaries[node_tag]
        
        try:
            # 更新属性
            for key, value in kwargs.items():
                if hasattr(boundary, key):
                    setattr(boundary, key, value)
                    
            # 更新修改时间
            boundary.updated_at = datetime.now()
            
            # 验证更新后的参数
            valid, message = boundary.validate_parameters()
            if not valid:
                return False, message
                
            # 发射信号
            self.boundary_updated.emit(boundary)
            self.boundaries_changed.emit()
            
            return True, "边界条件更新成功"
            
        except Exception as e:
            return False, f"更新边界条件失败: {str(e)}"
            
    def delete_boundary(self, node_tag: int) -> Tuple[bool, str]:
        """删除边界条件"""
        if node_tag not in self.boundaries:
            return False, f"节点标签 {node_tag} 不存在边界条件"
            
        try:
            del self.boundaries[node_tag]
            
            # 发射信号
            self.boundary_deleted.emit(node_tag)
            self.boundaries_changed.emit()
            
            return True, "边界条件删除成功"
            
        except Exception as e:
            return False, f"删除边界条件失败: {str(e)}"
            
    def clear_all_boundaries(self) -> Tuple[bool, str]:
        """清空所有边界条件"""
        try:
            self.boundaries.clear()
            
            # 发射信号
            self.boundaries_cleared.emit()
            self.boundaries_changed.emit()
            
            return True, "所有边界条件已清空"
            
        except Exception as e:
            return False, f"清空边界条件失败: {str(e)}"
            
    def get_boundaries_by_node_tags(self, node_tags: List[int]) -> List[FixBoundary]:
        """根据节点标签列表获取边界条件"""
        return [self.boundaries[node_tag] for node_tag in node_tags if node_tag in self.boundaries]
        
    def get_constraint_statistics(self) -> Dict[str, Any]:
        """获取约束统计信息"""
        if not self.boundaries:
            return {'total_boundaries': 0, 'constrained_dofs': 0, 'released_dofs': 0}
            
        total_boundaries = len(self.boundaries)
        constrained_dofs = 0
        released_dofs = 0
        
        for boundary in self.boundaries.values():
            for value in boundary.constr_values:
                if value == 1:
                    constrained_dofs += 1
                else:
                    released_dofs += 1
                    
        return {
            'total_boundaries': total_boundaries,
            'constrained_dofs': constrained_dofs,
            'released_dofs': released_dofs,
            'model_dimension': self.model_dim
        }
        
    def create_common_boundary_patterns(self) -> Dict[str, List[int]]:
        """创建常见的约束模式"""
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
            
    def export_to_dict(self) -> Dict:
        """导出所有数据为字典"""
        return {
            'boundaries': {str(k): v.to_dict() for k, v in self.boundaries.items()},
            'model_dim': self.model_dim
        }
        
    def import_from_dict(self, data: Dict) -> Tuple[bool, str]:
        """从字典导入数据"""
        try:
            self.clear_all_boundaries()
            
            # 设置模型维度
            self.model_dim = data.get('model_dim', 3)
            
            boundaries_data = data.get('boundaries', {})
            for node_tag_str, boundary_data in boundaries_data.items():
                node_tag = int(node_tag_str)
                
                # 创建边界条件对象
                boundary = FixBoundary(1, "temp", [1, 1, 1], self.model_dim)
                
                # 从数据恢复
                if boundary.from_dict(boundary_data):
                    self.boundaries[node_tag] = boundary
                    
            # 发射信号
            self.boundaries_changed.emit()
            
            return True, "数据导入成功"
            
        except Exception as e:
            return False, f"数据导入失败: {str(e)}"