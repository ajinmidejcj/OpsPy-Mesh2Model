#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
坐标系变换管理器
处理梁单元的坐标系变换，包括Linear、PDelta、Corotational变换
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

# PyQt5导入
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
                           QLineEdit, QPushButton, QComboBox, QDoubleSpinBox, 
                           QCheckBox, QSpinBox, QMessageBox, QDialog, QDialogButtonBox)


class Transform:
    """坐标系变换基类"""
    
    def __init__(self, transform_id: int, name: str, transform_type: str):
        self.id = transform_id
        self.name = name
        self.type = transform_type
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.user_data = {}
        
    def generate_opensees_code(self) -> str:
        """生成OpenSeesPy变换创建代码"""
        raise NotImplementedError("子类必须实现此方法")
        
    def validate_parameters(self) -> Tuple[bool, str]:
        """验证参数"""
        return True, "参数验证通过"


class LinearTransform(Transform):
    """线性变换"""
    
    def __init__(self, transform_id: int, name: str, vecxz: List[float], 
                 use_jnt_offset: bool = False, dI: Optional[List[float]] = None, 
                 dJ: Optional[List[float]] = None):
        super().__init__(transform_id, name, "Linear")
        self.vecxz = vecxz  # XZ平面方向向量 [x, z] 或 [x, y, z]
        self.use_jnt_offset = use_jnt_offset  # 是否使用节点偏移
        self.dI = dI if dI else [0.0, 0.0, 0.0]  # 节点I偏移
        self.dJ = dJ if dJ else [0.0, 0.0, 0.0]  # 节点J偏移
        
    def validate_parameters(self) -> Tuple[bool, str]:
        """验证线性变换参数"""
        if len(self.vecxz) not in [2, 3]:
            return False, "vecxz必须是2D [x,z] 或3D [x,y,z] 向量"
        if any(not isinstance(v, (int, float)) for v in self.vecxz):
            return False, "vecxz分量必须是数字"
        if self.use_jnt_offset:
            if len(self.dI) != 3 or len(self.dJ) != 3:
                return False, "dI和dJ必须是3D向量"
            if any(not isinstance(v, (int, float)) for v in self.dI + self.dJ):
                return False, "偏移分量必须是数字"
        return True, "参数验证通过"
        
    def generate_opensees_code(self) -> str:
        """生成线性变换OpenSeesPy代码"""
        vecxz_str = ', '.join(map(str, self.vecxz))
        
        if self.use_jnt_offset:
            dI_str = ', '.join(map(str, self.dI))
            dJ_str = ', '.join(map(str, self.dJ))
            return f"geomTransf('Linear', {self.id}, {vecxz_str}, '-jntOffset', {dI_str}, {dJ_str})"
        else:
            return f"geomTransf('Linear', {self.id}, {vecxz_str})"


class PDeltaTransform(Transform):
    """P-Δ效应变换"""
    
    def __init__(self, transform_id: int, name: str, vecxz: List[float],
                 use_jnt_offset: bool = False, dI: Optional[List[float]] = None,
                 dJ: Optional[List[float]] = None):
        super().__init__(transform_id, name, "PDelta")
        self.vecxz = vecxz
        self.use_jnt_offset = use_jnt_offset
        self.dI = dI if dI else [0.0, 0.0, 0.0]
        self.dJ = dJ if dJ else [0.0, 0.0, 0.0]
        
    def validate_parameters(self) -> Tuple[bool, str]:
        """验证P-Δ变换参数"""
        if len(self.vecxz) not in [2, 3]:
            return False, "vecxz必须是2D [x,z] 或3D [x,y,z] 向量"
        if any(not isinstance(v, (int, float)) for v in self.vecxz):
            return False, "vecxz分量必须是数字"
        if self.use_jnt_offset:
            if len(self.dI) != 3 or len(self.dJ) != 3:
                return False, "dI和dJ必须是3D向量"
            if any(not isinstance(v, (int, float)) for v in self.dI + self.dJ):
                return False, "偏移分量必须是数字"
        return True, "参数验证通过"
        
    def generate_opensees_code(self) -> str:
        """生成P-Δ变换OpenSeesPy代码"""
        vecxz_str = ', '.join(map(str, self.vecxz))
        
        if self.use_jnt_offset:
            dI_str = ', '.join(map(str, self.dI))
            dJ_str = ', '.join(map(str, self.dJ))
            return f"geomTransf('PDelta', {self.id}, {vecxz_str}, '-jntOffset', {dI_str}, {dJ_str})"
        else:
            return f"geomTransf('PDelta', {self.id}, {vecxz_str})"


class CorotationalTransform(Transform):
    """共同旋转变换"""
    
    def __init__(self, transform_id: int, name: str, vecxz: List[float]):
        super().__init__(transform_id, name, "Corotational")
        self.vecxz = vecxz
        
    def validate_parameters(self) -> Tuple[bool, str]:
        """验证共同旋转变换参数"""
        if len(self.vecxz) not in [2, 3]:
            return False, "vecxz必须是2D [x,z] 或3D [x,y,z] 向量"
        if any(not isinstance(v, (int, float)) for v in self.vecxz):
            return False, "vecxz分量必须是数字"
        return True, "参数验证通过"
        
    def generate_opensees_code(self) -> str:
        """生成共同旋转变换OpenSeesPy代码"""
        vecxz_str = ', '.join(map(str, self.vecxz))
        return f"geomTransf('Corotational', {self.id}, {vecxz_str})"


class TransformManager(QObject):
    """坐标系变换管理器"""
    
    # 信号定义
    transform_added = pyqtSignal(object)  # 变换添加信号
    transform_updated = pyqtSignal(object)  # 变换更新信号
    transform_deleted = pyqtSignal(int)  # 变换删除信号
    transforms_cleared = pyqtSignal()  # 清空所有变换信号
    transforms_changed = pyqtSignal()  # 变换数据变化信号
    
    def __init__(self):
        super().__init__()
        self.transforms: Dict[int, Transform] = {}  # 变换字典
        
        # 变换类型注册表
        self._transform_types = {
            'Linear': LinearTransform,
            'PDelta': PDeltaTransform,
            'Corotational': CorotationalTransform
        }
        
    def create_transform(self, transform_type: str, name: str, transform_id: Optional[int] = None, **kwargs) -> Tuple[bool, str, Optional[Transform]]:
        """
        创建坐标系变换
        
        Args:
            transform_type: 变换类型 ('Linear', 'PDelta', 'Corotational')
            name: 变换名称
            transform_id: 变换ID（可选，如果未提供则自动分配）
            **kwargs: 变换参数
            
        Returns:
            Tuple[bool, str, Transform]: (是否成功, 错误信息, 变换对象)
        """
        if transform_type not in self._transform_types:
            return False, f"不支持的变换类型: {transform_type}", None
            
        transform_class = self._transform_types[transform_type]
        
        # 如果用户提供了transform_id，使用用户指定的ID，否则使用自动分配的ID
        if transform_id is not None:
            if transform_id in self.transforms:
                return False, f"变换ID {transform_id} 已存在", None
            final_transform_id = transform_id
        else:
            # 自动分配ID：找到下一个可用ID
            if not self.transforms:
                final_transform_id = 1
            else:
                max_id = max(self.transforms.keys())
                final_transform_id = max_id + 1
        
        try:
            # 根据变换类型过滤不支持的参数
            filtered_kwargs = kwargs.copy()
            if transform_type == 'Corotational':
                # Corotational变换不支持jntOffset相关参数
                filtered_kwargs.pop('use_jnt_offset', None)
                filtered_kwargs.pop('dI', None)
                filtered_kwargs.pop('dJ', None)
            
            # 创建变换对象
            transform = transform_class(final_transform_id, name, **filtered_kwargs)
            
            # 验证参数
            valid, msg = transform.validate_parameters()
            if not valid:
                return False, f"参数验证失败: {msg}", None
            
            # 添加到管理器
            self.transforms[final_transform_id] = transform
            
            # 发出信号
            self.transform_added.emit(transform)
            self.transforms_changed.emit()
            
            return True, "变换创建成功", transform
            
        except Exception as e:
            return False, f"创建变换失败: {str(e)}", None
    
    def get_transform(self, transform_id: int) -> Optional[Transform]:
        """获取变换对象"""
        return self.transforms.get(transform_id)
        
    def update_transform(self, transform_id: int, **kwargs) -> Tuple[bool, str]:
        """更新变换参数"""
        if transform_id not in self.transforms:
            return False, f"变换ID {transform_id} 不存在"
            
        transform = self.transforms[transform_id]
        
        try:
            # 更新参数
            for key, value in kwargs.items():
                if hasattr(transform, key):
                    setattr(transform, key, value)
                else:
                    return False, f"变换对象没有属性: {key}"
            
            # 更新修改时间
            transform.updated_at = datetime.now()
            
            # 验证参数
            valid, msg = transform.validate_parameters()
            if not valid:
                return False, f"参数验证失败: {msg}"
            
            # 发出信号
            self.transform_updated.emit(transform)
            self.transforms_changed.emit()
            
            return True, "变换更新成功"
            
        except Exception as e:
            return False, f"更新变换失败: {str(e)}"
    
    def delete_transform(self, transform_id: int) -> bool:
        """删除变换"""
        if transform_id in self.transforms:
            del self.transforms[transform_id]
            self.transform_deleted.emit(transform_id)
            self.transforms_changed.emit()
            return True
        return False
    
    def get_all_transforms(self) -> Dict[int, Transform]:
        """获取所有变换"""
        return self.transforms.copy()
        
    def get_all_transform_ids(self) -> List[int]:
        """获取所有变换ID"""
        return sorted(self.transforms.keys())
    
    def get_transforms_by_type(self, transform_type: str) -> List[Transform]:
        """根据类型获取变换"""
        return [t for t in self.transforms.values() if t.type == transform_type]
    
    def clear_all_transforms(self) -> bool:
        """清空所有变换"""
        if self.transforms:
            self.transforms.clear()
            self.transforms_cleared.emit()
            self.transforms_changed.emit()
            return True
        return False
    
    def generate_all_transform_code(self) -> str:
        """生成所有变换的OpenSeesPy代码"""
        if not self.transforms:
            return ""
        
        code_lines = []
        code_lines.append("# 坐标系变换")
        
        # 按ID排序生成代码
        for transform_id in sorted(self.transforms.keys()):
            transform = self.transforms[transform_id]
            code_lines.append(transform.generate_opensees_code())
        
        return '\n'.join(code_lines)
    
    def get_transform_count(self) -> int:
        """获取变换数量"""
        return len(self.transforms)
        
    def get_transform_statistics(self) -> Dict:
        """获取变换统计信息"""
        if not self.transforms:
            return {'total': 0}
            
        transforms = list(self.transforms.values())
        type_counts = {}
        
        for transform in transforms:
            type_counts[transform.type] = type_counts.get(transform.type, 0) + 1
            
        return {
            'total': len(transforms),
            'types': type_counts
        }
    
    def validate_all_transforms(self) -> Tuple[bool, List[str]]:
        """验证所有变换"""
        errors = []
        
        for transform_id, transform in self.transforms.items():
            valid, error_msg = transform.validate_parameters()
            if not valid:
                errors.append(f"变换 {transform_id} ({transform.name}): {error_msg}")
                
        return len(errors) == 0, errors