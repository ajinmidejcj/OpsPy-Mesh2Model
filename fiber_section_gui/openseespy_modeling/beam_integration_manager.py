# -*- coding: utf-8 -*-
"""
beamIntegration管理模块
用于通过OpenSeesPy交互的方式创建和管理梁单元积分方案
支持Lobatto、NewtonCotes等积分方法
"""

import openseespy.opensees as ops
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QInputDialog, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, QTextEdit, QLabel, QTabWidget
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import uuid


class BeamIntegration:
    """beamIntegration基类"""
    
    def __init__(self, integration_id: int, name: str, integration_type: str):
        self.id = integration_id
        self.name = name
        self.type = integration_type
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.tags = []
        self.user_data = {}
        
    def generate_opensees_code(self) -> str:
        """生成OpenSeesPy beamIntegration创建代码"""
        raise NotImplementedError("子类必须实现此方法")
        
    def validate_parameters(self) -> Tuple[bool, str]:
        """验证积分参数"""
        raise NotImplementedError("子类必须实现此方法")
        
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'tags': self.tags,
            'user_data': self.user_data
        }
        
    def from_dict(self, data: Dict) -> bool:
        """从字典加载数据"""
        try:
            self.id = data.get('id', self.id)
            self.name = data.get('name', self.name)
            self.type = data.get('type', self.type)
            self.tags = data.get('tags', [])
            self.user_data = data.get('user_data', {})
            return True
        except Exception:
            return False


class LobattoIntegration(BeamIntegration):
    """Lobatto积分方案"""
    
    def __init__(self, integration_id: int, name: str, secTag: int, n: int):
        super().__init__(integration_id, name, 'Lobatto')
        self.secTag = secTag  # 截面标签
        self.n = n  # 积分点数量
        
    def validate_parameters(self) -> Tuple[bool, str]:
        """验证Lobatto积分参数"""
        if self.secTag <= 0:
            return False, "截面标签必须为正整数"
        if self.n < 2:
            return False, "积分点数量必须至少为2"
        if self.n > 20:
            return False, "积分点数量不能超过20"
        return True, "参数验证通过"
        
    def generate_opensees_code(self) -> str:
        """生成Lobatto积分OpenSeesPy代码"""
        return f"beamIntegration('Lobatto', {self.id}, {self.secTag}, {self.n})  # {self.name}"


class NewtonCotesIntegration(BeamIntegration):
    """NewtonCotes积分方案"""
    
    def __init__(self, integration_id: int, name: str, secTag: int, n: int):
        super().__init__(integration_id, name, 'NewtonCotes')
        self.secTag = secTag  # 截面标签
        self.n = n  # 积分点数量
        
    def validate_parameters(self) -> Tuple[bool, str]:
        """验证NewtonCotes积分参数"""
        if self.secTag <= 0:
            return False, "截面标签必须为正整数"
        if self.n < 2:
            return False, "积分点数量必须至少为2"
        if self.n > 20:
            return False, "积分点数量不能超过20"
        return True, "参数验证通过"
        
    def generate_opensees_code(self) -> str:
        """生成NewtonCotes积分OpenSeesPy代码"""
        return f"beamIntegration('NewtonCotes', {self.id}, {self.secTag}, {self.n})  # {self.name}"


class BeamIntegrationManager(QObject):
    """beamIntegration管理器"""
    
    # 信号定义
    integration_added = pyqtSignal(object)  # 积分方案添加信号
    integration_updated = pyqtSignal(object)  # 积分方案更新信号
    integration_deleted = pyqtSignal(int)  # 积分方案删除信号
    integrations_cleared = pyqtSignal()  # 清空所有积分方案信号
    integrations_changed = pyqtSignal()  # 积分方案数据变化信号
    
    def __init__(self):
        super().__init__()
        self.integrations: Dict[int, BeamIntegration] = {}  # 积分方案字典
        self._next_id = 1  # 下一个可用的ID
        
        # 积分类型注册表
        self._integration_types = {
            'Lobatto': LobattoIntegration,
            'NewtonCotes': NewtonCotesIntegration
        }
        
    def create_integration(self, integration_type: str, name: str, integration_id: Optional[int] = None, **kwargs) -> Tuple[bool, str, Optional[BeamIntegration]]:
        """
        创建beamIntegration
        
        Args:
            integration_type: 积分类型 ('Lobatto', 'NewtonCotes')
            name: 积分方案名称
            integration_id: 积分方案ID（可选，如果未提供则自动分配）
            **kwargs: 积分参数
            
        Returns:
            Tuple[bool, str, BeamIntegration]: (是否成功, 错误信息, 积分方案对象)
        """
        if integration_type not in self._integration_types:
            return False, f"不支持的积分类型: {integration_type}", None
            
        integration_class = self._integration_types[integration_type]
        
        # 如果没有提供ID，自动分配
        if integration_id is None:
            integration_id = self._get_next_id()
        
        # 检查ID是否已存在
        if integration_id in self.integrations:
            return False, f"积分方案ID {integration_id} 已存在", None
            
        try:
            # 创建积分方案对象
            integration = integration_class(integration_id, name, **kwargs)
            
            # 验证参数
            valid, message = integration.validate_parameters()
            if not valid:
                return False, message, None
                
            # 添加到管理器
            self.integrations[integration_id] = integration
            
            # 发射信号
            self.integration_added.emit(integration)
            self.integrations_changed.emit()
            
            return True, "积分方案创建成功", integration
            
        except Exception as e:
            return False, f"创建积分方案失败: {str(e)}", None
            
    def _get_next_id(self) -> int:
        """获取下一个可用的ID"""
        while self._next_id in self.integrations:
            self._next_id += 1
        return self._next_id
        
    def get_integration(self, integration_id: int) -> Optional[BeamIntegration]:
        """获取指定ID的积分方案"""
        return self.integrations.get(integration_id)
        
    def get_all_integrations(self) -> Dict[int, BeamIntegration]:
        """获取所有积分方案"""
        return self.integrations.copy()
        
    def update_integration(self, integration_id: int, **kwargs) -> Tuple[bool, str]:
        """更新积分方案"""
        if integration_id not in self.integrations:
            return False, f"积分方案ID {integration_id} 不存在"
            
        integration = self.integrations[integration_id]
        original_type = integration.type
        
        # 如果类型发生变化，需要重新创建对象
        if 'integration_type' in kwargs and kwargs['integration_type'] != original_type:
            new_type = kwargs.pop('integration_type')
            new_name = kwargs.pop('name', integration.name)
            
            # 创建新的积分方案
            success, message, new_integration = self.create_integration(
                new_type, new_name, integration_id, **kwargs
            )
            
            if success:
                # 删除旧的
                del self.integrations[integration_id]
                
                # 发射信号
                self.integration_updated.emit(new_integration)
                self.integrations_changed.emit()
                
                return True, "积分方案更新成功"
            else:
                return False, message
        else:
            # 更新现有对象的属性
            try:
                for key, value in kwargs.items():
                    if hasattr(integration, key):
                        setattr(integration, key, value)
                        
                # 更新修改时间
                integration.updated_at = datetime.now()
                
                # 验证更新后的参数
                valid, message = integration.validate_parameters()
                if not valid:
                    return False, message
                    
                # 发射信号
                self.integration_updated.emit(integration)
                self.integrations_changed.emit()
                
                return True, "积分方案更新成功"
                
            except Exception as e:
                return False, f"更新积分方案失败: {str(e)}"
                
    def delete_integration(self, integration_id: int) -> Tuple[bool, str]:
        """删除积分方案"""
        if integration_id not in self.integrations:
            return False, f"积分方案ID {integration_id} 不存在"
            
        try:
            del self.integrations[integration_id]
            
            # 发射信号
            self.integration_deleted.emit(integration_id)
            self.integrations_changed.emit()
            
            return True, "积分方案删除成功"
            
        except Exception as e:
            return False, f"删除积分方案失败: {str(e)}"
            
    def clear_all_integrations(self) -> Tuple[bool, str]:
        """清空所有积分方案"""
        try:
            self.integrations.clear()
            
            # 发射信号
            self.integrations_cleared.emit()
            self.integrations_changed.emit()
            
            return True, "所有积分方案已清空"
            
        except Exception as e:
            return False, f"清空积分方案失败: {str(e)}"
            
    def get_integrations_by_type(self, integration_type: str) -> List[BeamIntegration]:
        """根据类型获取积分方案"""
        return [integration for integration in self.integrations.values() 
                if integration.type == integration_type]
                
    def get_available_types(self) -> List[str]:
        """获取可用的积分类型"""
        return list(self._integration_types.keys())
        
    def export_to_dict(self) -> Dict:
        """导出所有数据为字典"""
        return {
            'integrations': {str(k): v.to_dict() for k, v in self.integrations.items()},
            'next_id': self._next_id
        }
        
    def import_from_dict(self, data: Dict) -> Tuple[bool, str]:
        """从字典导入数据"""
        try:
            self.clear_all_integrations()
            
            integrations_data = data.get('integrations', {})
            for integration_id_str, integration_data in integrations_data.items():
                integration_id = int(integration_id_str)
                integration_type = integration_data.get('type')
                
                if integration_type in self._integration_types:
                    integration_class = self._integration_types[integration_type]
                    
                    # 创建临时对象来获取默认参数
                    temp_integration = integration_class(1, "temp", **integration_data.get('user_data', {}))
                    
                    # 从数据恢复
                    if temp_integration.from_dict(integration_data):
                        self.integrations[integration_id] = temp_integration
                        
            # 更新下一个ID
            if self.integrations:
                self._next_id = max(self.integrations.keys()) + 1
            else:
                self._next_id = 1
                
            # 发射信号
            self.integrations_changed.emit()
            
            return True, "数据导入成功"
            
        except Exception as e:
            return False, f"数据导入失败: {str(e)}"