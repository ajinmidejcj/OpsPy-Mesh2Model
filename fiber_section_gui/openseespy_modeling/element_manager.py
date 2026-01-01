# -*- coding: utf-8 -*-
"""
单元管理模块
用于创建和管理各种有限元单元
支持多种单元类型和Excel/CSV批量导入
"""

import openseespy.opensees as ops
import pandas as pd
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, QTextEdit, QLabel, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
import uuid
import openpyxl


class Element:
    """单元基类"""
    
    def __init__(self, element_id: int, element_type: str, node_ids: List[int]):
        self.id = element_id
        self.type = element_type
        self.node_ids = node_ids
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.tags = []
        self.user_data = {}
        
    def get_required_node_count(self) -> int:
        """获取所需节点数量"""
        raise NotImplementedError("子类必须实现此方法")
        
    def get_required_parameters(self) -> List[str]:
        """获取所需参数列表"""
        raise NotImplementedError("子类必须实现此方法")
        
    def validate_parameters(self) -> Tuple[bool, str]:
        """验证单元参数"""
        raise NotImplementedError("子类必须实现此方法")
        
    def generate_opensees_code(self) -> str:
        """生成OpenSeesPy单元创建代码"""
        raise NotImplementedError("子类必须实现此方法")
        
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'type': self.type,
            'node_ids': self.node_ids,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'tags': self.tags,
            'user_data': self.user_data
        }
        
    def from_dict(self, data: Dict) -> bool:
        """从字典加载数据"""
        try:
            self.id = data['id']
            self.type = data['type']
            self.node_ids = data['node_ids']
            self.tags = data.get('tags', [])
            self.user_data = data.get('user_data', {})
            
            if 'created_at' in data:
                self.created_at = datetime.fromisoformat(data['created_at'])
            if 'updated_at' in data:
                self.updated_at = datetime.fromisoformat(data['updated_at'])
                
            return True
        except Exception:
            return False
            
    def __str__(self) -> str:
        return f"{self.type}({self.id}): nodes={self.node_ids}"


class ZeroLengthElement(Element):
    """零长度单元"""
    
    def __init__(self, element_id: int, node_ids: List[int], mat_tags: List[int], 
                 dirs: List[int], do_rayleigh: bool = False, r_flag: int = 0,
                 vecx: Optional[List[float]] = None, vecyp: Optional[List[float]] = None):
        super().__init__(element_id, "ZeroLength", node_ids)
        self.mat_tags = mat_tags
        self.dirs = dirs
        self.do_rayleigh = do_rayleigh
        self.r_flag = r_flag
        self.vecx = vecx or [1, 0, 0]
        self.vecyp = vecyp or [0, 1, 0]
        
    def get_required_node_count(self) -> int:
        return 2
        
    def get_required_parameters(self) -> List[str]:
        return ['mat_tags', 'dirs']
        
    def validate_parameters(self) -> Tuple[bool, str]:
        if len(self.node_ids) != 2:
            return False, "零长度单元需要2个节点"
        if len(self.mat_tags) != len(self.dirs):
            return False, "材料标签和方向参数数量不匹配"
        return True, ""
        
    def generate_opensees_code(self) -> str:
        mat_tags_str = ' '.join(map(str, self.mat_tags))
        dirs_str = ' '.join(map(str, self.dirs))
        
        code_line = f"ops.element('zeroLength', {self.id}, {self.node_ids[0]}, {self.node_ids[1]}, '-mat', {mat_tags_str}, '-dir', {dirs_str}"
        
        if self.do_rayleigh:
            code_line += f", '-doRayleigh', {self.r_flag}"
            
        if self.vecx != [1, 0, 0] or self.vecyp != [0, 1, 0]:
            vecx_str = ' '.join(map(str, self.vecx))
            vecyp_str = ' '.join(map(str, self.vecyp))
            code_line += f", '-orient', {vecx_str}, {vecyp_str}"
            
        return code_line + f")  # {self.type}({self.id})"
        
    def to_dict(self) -> Dict:
        data = super().to_dict()
        data.update({
            'mat_tags': self.mat_tags,
            'dirs': self.dirs,
            'do_rayleigh': self.do_rayleigh,
            'r_flag': self.r_flag,
            'vecx': self.vecx,
            'vecyp': self.vecyp
        })
        return data
        
    def from_dict(self, data: Dict) -> bool:
        if not super().from_dict(data):
            return False
        try:
            self.mat_tags = data['mat_tags']
            self.dirs = data['dirs']
            self.do_rayleigh = data.get('do_rayleigh', False)
            self.r_flag = data.get('r_flag', 0)
            self.vecx = data.get('vecx', [1, 0, 0])
            self.vecyp = data.get('vecyp', [0, 1, 0])
            return True
        except Exception:
            return False


class TwoNodeLinkElement(Element):
    """双节点连接单元"""
    
    def __init__(self, element_id: int, node_ids: List[int], mat_tags: List[int], 
                 dirs: List[int], vecx: Optional[List[float]] = None, 
                 vecyp: Optional[List[float]] = None, p_delta: Optional[List[float]] = None,
                 shear_dist: Optional[List[float]] = None, do_rayleigh: bool = False, 
                 mass: float = 0.0):
        super().__init__(element_id, "TwoNodeLink", node_ids)
        self.mat_tags = mat_tags
        self.dirs = dirs
        self.vecx = vecx or [1, 0, 0]
        self.vecyp = vecyp or [0, 1, 0]
        self.p_delta = p_delta or []
        self.shear_dist = shear_dist or []
        self.do_rayleigh = do_rayleigh
        self.mass = mass
        
    def get_required_node_count(self) -> int:
        return 2
        
    def get_required_parameters(self) -> List[str]:
        return ['mat_tags', 'dirs']
        
    def validate_parameters(self) -> Tuple[bool, str]:
        if len(self.node_ids) != 2:
            return False, "双节点连接单元需要2个节点"
        if len(self.mat_tags) != len(self.dirs):
            return False, "材料标签和方向参数数量不匹配"
        return True, ""
        
    def generate_opensees_code(self) -> str:
        mat_tags_str = ' '.join(map(str, self.mat_tags))
        dirs_str = ' '.join(map(str, self.dirs))
        
        code_line = f"ops.element('twoNodeLink', {self.id}, {self.node_ids[0]}, {self.node_ids[1]}, '-mat', {mat_tags_str}, '-dir', {dirs_str}"
        
        if self.vecx != [1, 0, 0] or self.vecyp != [0, 1, 0]:
            vecx_str = ' '.join(map(str, self.vecx))
            vecyp_str = ' '.join(map(str, self.vecyp))
            code_line += f", '-orient', {vecx_str}, {vecyp_str}"
            
        if self.p_delta:
            p_delta_str = ' '.join(map(str, self.p_delta))
            code_line += f", '-pDelta', {p_delta_str}"
            
        if self.shear_dist:
            shear_dist_str = ' '.join(map(str, self.shear_dist))
            code_line += f", '-shearDist', {shear_dist_str}"
            
        if self.do_rayleigh:
            code_line += ", '-doRayleigh'"
            
        if self.mass != 0.0:
            code_line += f", '-mass', {self.mass}"
            
        return code_line + f")  # {self.type}({self.id})"
        
    def to_dict(self) -> Dict:
        data = super().to_dict()
        data.update({
            'mat_tags': self.mat_tags,
            'dirs': self.dirs,
            'vecx': self.vecx,
            'vecyp': self.vecyp,
            'p_delta': self.p_delta,
            'shear_dist': self.shear_dist,
            'do_rayleigh': self.do_rayleigh,
            'mass': self.mass
        })
        return data
        
    def from_dict(self, data: Dict) -> bool:
        if not super().from_dict(data):
            return False
        try:
            self.mat_tags = data['mat_tags']
            self.dirs = data['dirs']
            self.vecx = data.get('vecx', [1, 0, 0])
            self.vecyp = data.get('vecyp', [0, 1, 0])
            self.p_delta = data.get('p_delta', [])
            self.shear_dist = data.get('shear_dist', [])
            self.do_rayleigh = data.get('do_rayleigh', False)
            self.mass = data.get('mass', 0.0)
            return True
        except Exception:
            return False


class TrussElement(Element):
    """桁架单元"""
    
    def __init__(self, element_id: int, node_ids: List[int], A: float, mat_tag: int, 
                 rho: float = 0.0, c_mass: bool = False, do_rayleigh: bool = False):
        super().__init__(element_id, "Truss", node_ids)
        self.A = A  # 截面积
        self.mat_tag = mat_tag  # 材料标签
        self.rho = rho  # 密度
        self.c_mass = c_mass  # 一致质量矩阵
        self.do_rayleigh = do_rayleigh  # 瑞利阻尼
        
    def get_required_node_count(self) -> int:
        return 2
        
    def get_required_parameters(self) -> List[str]:
        return ['A', 'mat_tag']
        
    def validate_parameters(self) -> Tuple[bool, str]:
        if len(self.node_ids) != 2:
            return False, "桁架单元需要2个节点"
        if self.A <= 0:
            return False, "截面积必须为正数"
        if self.mat_tag <= 0:
            return False, "材料标签必须为正数"
        return True, ""
        
    def generate_opensees_code(self) -> str:
        code_line = f"ops.element('Truss', {self.id}, {self.node_ids[0]}, {self.node_ids[1]}, {self.A}, {self.mat_tag}"
        
        if self.rho != 0.0:
            code_line += f", '-rho', {self.rho}"
            
        if self.c_mass:
            code_line += ", '-cMass'"
            
        if self.do_rayleigh:
            code_line += ", '-doRayleigh'"
            
        return code_line + f")  # {self.type}({self.id})"
        
    def to_dict(self) -> Dict:
        data = super().to_dict()
        data.update({
            'A': self.A,
            'mat_tag': self.mat_tag,
            'rho': self.rho,
            'c_mass': self.c_mass,
            'do_rayleigh': self.do_rayleigh
        })
        return data
        
    def from_dict(self, data: Dict) -> bool:
        if not super().from_dict(data):
            return False
        try:
            self.A = data['A']
            self.mat_tag = data['mat_tag']
            self.rho = data.get('rho', 0.0)
            self.c_mass = data.get('c_mass', False)
            self.do_rayleigh = data.get('do_rayleigh', False)
            return True
        except Exception:
            return False


class ElasticBeamColumnElement(Element):
    """弹性梁柱单元"""
    
    def __init__(self, element_id: int, node_ids: List[int], Area: float, E_mod: float, 
                 Iz: float, transf_tag: int, mass: float = 0.0, c_mass: bool = False, 
                 release_code: Optional[int] = None):
        super().__init__(element_id, "ElasticBeamColumn", node_ids)
        self.Area = Area  # 截面积
        self.E_mod = E_mod  # 弹性模量
        self.Iz = Iz  # 惯性矩
        self.transf_tag = transf_tag  # 坐标变换标签
        self.mass = mass  # 质量
        self.c_mass = c_mass  # 一致质量矩阵
        self.release_code = release_code  # 释放代码
        
    def get_required_node_count(self) -> int:
        return 2
        
    def get_required_parameters(self) -> List[str]:
        return ['Area', 'E_mod', 'Iz', 'transf_tag']
        
    def validate_parameters(self) -> Tuple[bool, str]:
        if len(self.node_ids) != 2:
            return False, "弹性梁柱单元需要2个节点"
        if self.Area <= 0:
            return False, "截面积必须为正数"
        if self.E_mod <= 0:
            return False, "弹性模量必须为正数"
        if self.Iz <= 0:
            return False, "惯性矩必须为正数"
        if self.transf_tag <= 0:
            return False, "坐标变换标签必须为正数"
        return True, ""
        
    def generate_opensees_code(self) -> str:
        code_line = f"ops.element('elasticBeamColumn', {self.id}, {self.node_ids[0]}, {self.node_ids[1]}, {self.Area}, {self.E_mod}, {self.Iz}, {self.transf_tag}"
        
        if self.mass != 0.0:
            code_line += f", '-mass', {self.mass}"
            
        if self.c_mass:
            code_line += ", '-cMass'"
            
        if self.release_code is not None:
            code_line += f", '-release', {self.release_code}"
            
        return code_line + f")  # {self.type}({self.id})"
        
    def to_dict(self) -> Dict:
        data = super().to_dict()
        data.update({
            'Area': self.Area,
            'E_mod': self.E_mod,
            'Iz': self.Iz,
            'transf_tag': self.transf_tag,
            'mass': self.mass,
            'c_mass': self.c_mass,
            'release_code': self.release_code
        })
        return data
        
    def from_dict(self, data: Dict) -> bool:
        if not super().from_dict(data):
            return False
        try:
            self.Area = data['Area']
            self.E_mod = data['E_mod']
            self.Iz = data['Iz']
            self.transf_tag = data['transf_tag']
            self.mass = data.get('mass', 0.0)
            self.c_mass = data.get('c_mass', False)
            self.release_code = data.get('release_code')
            return True
        except Exception:
            return False


class DispBeamColumnElement(Element):
    """位移梁柱单元"""
    
    def __init__(self, element_id: int, node_ids: List[int], transf_tag: int, 
                 integration_tag: int, c_mass: bool = False, mass: float = 0.0):
        super().__init__(element_id, "DispBeamColumn", node_ids)
        self.transf_tag = transf_tag  # 坐标变换标签
        self.integration_tag = integration_tag  # 积分点标签
        self.c_mass = c_mass  # 一致质量矩阵
        self.mass = mass  # 质量
        
    def get_required_node_count(self) -> int:
        return 2
        
    def get_required_parameters(self) -> List[str]:
        return ['transf_tag', 'integration_tag']
        
    def validate_parameters(self) -> Tuple[bool, str]:
        if len(self.node_ids) != 2:
            return False, "位移梁柱单元需要2个节点"
        if self.transf_tag <= 0:
            return False, "坐标变换标签必须为正数"
        if self.integration_tag <= 0:
            return False, "积分点标签必须为正数"
        return True, ""
        
    def generate_opensees_code(self) -> str:
        code_line = f"ops.element('dispBeamColumn', {self.id}, {self.node_ids[0]}, {self.node_ids[1]}, {self.transf_tag}, {self.integration_tag}, '-cMass'"
        
        if self.mass != 0.0:
            code_line += f", '-mass', {self.mass}"
            
        return code_line + f")  # {self.type}({self.id})"
        
    def to_dict(self) -> Dict:
        data = super().to_dict()
        data.update({
            'transf_tag': self.transf_tag,
            'integration_tag': self.integration_tag,
            'c_mass': self.c_mass,
            'mass': self.mass
        })
        return data
        
    def from_dict(self, data: Dict) -> bool:
        if not super().from_dict(data):
            return False
        try:
            self.transf_tag = data['transf_tag']
            self.integration_tag = data['integration_tag']
            self.c_mass = data.get('c_mass', False)
            self.mass = data.get('mass', 0.0)
            return True
        except Exception:
            return False


class ForceBeamColumnElement(Element):
    """力梁柱单元"""
    
    def __init__(self, element_id: int, node_ids: List[int], transf_tag: int, 
                 integration_tag: int, max_iter: int = 10, tol: float = 1e-12, 
                 mass: float = 0.0):
        super().__init__(element_id, "ForceBeamColumn", node_ids)
        self.transf_tag = transf_tag  # 坐标变换标签
        self.integration_tag = integration_tag  # 积分点标签
        self.max_iter = max_iter  # 最大迭代次数
        self.tol = tol  # 容差
        self.mass = mass  # 质量
        
    def get_required_node_count(self) -> int:
        return 2
        
    def get_required_parameters(self) -> List[str]:
        return ['transf_tag', 'integration_tag']
        
    def validate_parameters(self) -> Tuple[bool, str]:
        if len(self.node_ids) != 2:
            return False, "力梁柱单元需要2个节点"
        if self.transf_tag <= 0:
            return False, "坐标变换标签必须为正数"
        if self.integration_tag <= 0:
            return False, "积分点标签必须为正数"
        if self.max_iter <= 0:
            return False, "最大迭代次数必须为正数"
        if self.tol <= 0:
            return False, "容差必须为正数"
        return True, ""
        
    def generate_opensees_code(self) -> str:
        code_line = f"ops.element('forceBeamColumn', {self.id}, {self.node_ids[0]}, {self.node_ids[1]}, {self.transf_tag}, {self.integration_tag}, '-iter', {self.max_iter}, {self.tol}"
        
        if self.mass != 0.0:
            code_line += f", '-mass', {self.mass}"
            
        return code_line + f")  # {self.type}({self.id})"
        
    def to_dict(self) -> Dict:
        data = super().to_dict()
        data.update({
            'transf_tag': self.transf_tag,
            'integration_tag': self.integration_tag,
            'max_iter': self.max_iter,
            'tol': self.tol,
            'mass': self.mass
        })
        return data
        
    def from_dict(self, data: Dict) -> bool:
        if not super().from_dict(data):
            return False
        try:
            self.transf_tag = data['transf_tag']
            self.integration_tag = data['integration_tag']
            self.max_iter = data.get('max_iter', 10)
            self.tol = data.get('tol', 1e-12)
            self.mass = data.get('mass', 0.0)
            return True
        except Exception:
            return False


class ElementManager(QObject):
    """单元管理类"""
    
    # 信号定义
    element_added = pyqtSignal(Element)  # 单元添加信号
    element_updated = pyqtSignal(Element)  # 单元更新信号
    element_deleted = pyqtSignal(int)  # 单元删除信号
    elements_cleared = pyqtSignal()  # 清空所有单元信号
    elements_changed = pyqtSignal()  # 单元数据变化信号
    
    def __init__(self):
        super().__init__()
        self.elements: Dict[int, Element] = {}  # 单元字典
        self._next_element_id = 1  # 下一个可用的单元ID
        
        # 单元类型注册表
        self._element_types = {
            'ZeroLength': ZeroLengthElement,
            'TwoNodeLink': TwoNodeLinkElement,
            'Truss': TrussElement,
            'ElasticBeamColumn': ElasticBeamColumnElement,
            'DispBeamColumn': DispBeamColumnElement,
            'ForceBeamColumn': ForceBeamColumnElement
        }
        
    def register_element_type(self, type_name: str, element_class):
        """注册新的单元类型"""
        self._element_types[type_name] = element_class
        
    def get_element_types(self) -> List[str]:
        """获取所有支持的单元类型"""
        return list(self._element_types.keys())
        
    def create_element(self, element_type: str, **kwargs) -> Tuple[bool, str, Optional[Element]]:
        """
        创建单元
        
        Args:
            element_type: 单元类型
            **kwargs: 单元参数
            
        Returns:
            Tuple[bool, str, Element]: (是否成功, 错误信息, 单元对象)
        """
        if element_type not in self._element_types:
            return False, f"不支持的单元类型: {element_type}", None
            
        element_class = self._element_types[element_type]
        
        # 检查是否提供了element_id，如果没有则使用自动分配
        element_id = kwargs.get('element_id', self._next_element_id)
        
        # 检查element_id是否已经存在
        if element_id in self.elements:
            return False, f"单元ID {element_id} 已存在", None
        
        try:
            # 从kwargs中移除element_id，因为它会作为位置参数传递给构造函数
            kwargs.pop('element_id', None)
            
            # 创建单元对象
            element = element_class(element_id, **kwargs)
            
            # 验证参数
            is_valid, error_msg = element.validate_parameters()
            if not is_valid:
                return False, error_msg, None
                
            # 添加单元
            self.elements[element_id] = element
            
            # 更新自动分配的ID（如果使用了自动分配）
            if element_id >= self._next_element_id:
                self._next_element_id = element_id + 1
            
            # 发送信号
            self.element_added.emit(element)
            
            return True, "", element
            
        except Exception as e:
            return False, f"创建单元失败: {str(e)}", None
            
    def get_element(self, element_id: int) -> Optional[Element]:
        """获取单元"""
        return self.elements.get(element_id)
        
    def update_element(self, element_id: int, **kwargs) -> Tuple[bool, str]:
        """更新单元"""
        element = self.elements.get(element_id)
        if not element:
            return False, f"单元 {element_id} 不存在"
            
        # 保存原始参数用于回滚
        original_data = element.to_dict()
        
        try:
            # 更新参数
            for key, value in kwargs.items():
                if hasattr(element, key):
                    setattr(element, key, value)
                    
            element.updated_at = datetime.now()
            
            # 验证更新后的参数
            is_valid, error_msg = element.validate_parameters()
            if not is_valid:
                # 回滚更新
                element.from_dict(original_data)
                return False, error_msg
                
            # 发送信号
            self.element_updated.emit(element)
            
            return True, ""
            
        except Exception as e:
            # 回滚更新
            element.from_dict(original_data)
            return False, f"更新单元失败: {str(e)}"
            
    def delete_element(self, element_id: int) -> bool:
        """删除单元"""
        if element_id in self.elements:
            del self.elements[element_id]
            self.element_deleted.emit(element_id)
            return True
        return False
        
    def get_all_elements(self) -> List[Element]:
        """获取所有单元"""
        return list(self.elements.values())
        
    def get_all_element_ids(self) -> List[int]:
        """获取所有单元ID"""
        return list(self.elements.keys())
        
    def get_elements_by_type(self, element_type: str) -> List[Element]:
        """根据类型获取单元"""
        return [elem for elem in self.elements.values() if elem.type == element_type]
        
    def clear_all_elements(self):
        """清空所有单元"""
        self.elements.clear()
        self.elements_cleared.emit()
        
    def export_elements_to_python(self) -> str:
        """导出单元创建代码"""
        if not self.elements:
            return "# 无单元数据"
            
        code_lines = [
            "\n# 单元创建",
            "print('正在创建单元...')"
        ]
        
        for element in sorted(self.elements.values(), key=lambda e: e.id):
            code_lines.append(element.generate_opensees_code())
            
        return "\n".join(code_lines)
        
    def import_elements_from_csv(self, file_path: str, element_type: str) -> Tuple[bool, str, int]:
        """
        从CSV文件批量导入单元
        
        Args:
            file_path: CSV文件路径
            element_type: 单元类型
            
        Returns:
            Tuple[bool, str, int]: (是否成功, 错误信息, 成功导入数量)
        """
        try:
            df = pd.read_csv(file_path)
            
            # 检查必要的列
            required_cols = ['id', 'node1', 'node2']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return False, f"缺少必要列: {missing_cols}", 0
                
            success_count = 0
            error_messages = []
            
            for index, row in df.iterrows():
                try:
                    element_id = int(row['id'])
                    node1 = int(row['node1'])
                    node2 = int(row['node2'])
                    
                    # 根据单元类型处理参数
                    if element_type == 'ZeroLength':
                        mat_tags = [int(x) for x in str(row.get('mat_tags', '')).split(',') if x.strip()]
                        dirs = [int(x) for x in str(row.get('dirs', '')).split(',') if x.strip()]
                        kwargs = {
                            'node_ids': [node1, node2],
                            'mat_tags': mat_tags,
                            'dirs': dirs
                        }
                    elif element_type == 'Truss':
                        A = float(row['A'])
                        mat_tag = int(row['mat_tag'])
                        kwargs = {
                            'node_ids': [node1, node2],
                            'A': A,
                            'mat_tag': mat_tag
                        }
                    elif element_type == 'ElasticBeamColumn':
                        Area = float(row['Area'])
                        E_mod = float(row['E_mod'])
                        Iz = float(row['Iz'])
                        transf_tag = int(row['transf_tag'])
                        kwargs = {
                            'node_ids': [node1, node2],
                            'Area': Area,
                            'E_mod': E_mod,
                            'Iz': Iz,
                            'transf_tag': transf_tag
                        }
                    else:
                        # 其他类型需要更多参数
                        continue
                        
                    success, error = self.create_element(element_type, **kwargs)
                    if success:
                        success_count += 1
                    else:
                        error_messages.append(f"第{index+1}行: {error}")
                        
                except (ValueError, TypeError) as e:
                    error_messages.append(f"第{index+1}行: 数据格式错误 - {str(e)}")
                    
            if error_messages:
                error_msg = f"部分单元导入失败:\n" + "\n".join(error_messages[:10])
                if len(error_messages) > 10:
                    error_msg += f"\n... 还有{len(error_messages)-10}个错误"
            else:
                error_msg = ""
                
            return len(error_messages) == 0, error_msg, success_count
            
        except Exception as e:
            return False, f"读取CSV文件失败: {str(e)}", 0

    def import_elements_from_multisheet_file(self, file_path: str) -> Tuple[bool, str, Dict[str, int]]:
        """
        从多页文件批量导入所有单元
        
        Args:
            file_path: 文件路径（支持.xlsx, .xls, .csv）
            
        Returns:
            Tuple[bool, str, Dict[str, int]]: (是否成功, 错误信息, 各类型导入数量统计)
        """
        try:
            # 根据文件扩展名确定读取方式
            if file_path.lower().endswith('.csv'):
                # 单页CSV文件，尝试从文件名或内容推断类型
                return self._import_from_single_csv(file_path)
            else:
                # Excel文件，可能有多页
                return self._import_from_excel_multisheet(file_path)
                
        except Exception as e:
            return False, f"读取文件失败: {str(e)}", {}

    def _import_from_single_csv(self, file_path: str) -> Tuple[bool, str, Dict[str, int]]:
        """从单页CSV文件导入，尝试推断单元类型"""
        try:
            df = pd.read_csv(file_path)
            if df.empty:
                return False, "CSV文件为空", {}
            
            # 尝试推断单元类型
            element_type = self._infer_element_type_from_columns(df.columns)
            if not element_type:
                return False, "无法从CSV列推断单元类型", {}
            
            # 调用现有的单类型导入方法
            success, error_msg, count = self.import_elements_from_csv(file_path, element_type)
            stats = {element_type: count} if success else {element_type: 0}
            
            return success, error_msg, stats
            
        except Exception as e:
            return False, f"读取CSV文件失败: {str(e)}", {}

    def _import_from_excel_multisheet(self, file_path: str) -> Tuple[bool, str, Dict[str, int]]:
        """从多页Excel文件导入所有单元"""
        try:
            # 读取所有工作表
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            if not sheet_names:
                return False, "Excel文件没有工作表", {}
            
            total_stats = {}
            all_errors = []
            overall_success = True
            
            for sheet_name in sheet_names:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    if df.empty:
                        continue
                    
                    # 尝试从工作表名称推断单元类型
                    element_type = self._infer_element_type_from_sheet_name(sheet_name)
                    if not element_type:
                        # 尝试从列推断
                        element_type = self._infer_element_type_from_columns(df.columns)
                    
                    if not element_type:
                        all_errors.append(f"工作表 '{sheet_name}': 无法推断单元类型")
                        overall_success = False
                        continue
                    
                    # 临时保存工作表为CSV进行导入
                    temp_csv = f"temp_{sheet_name}_{uuid.uuid4().hex[:8]}.csv"
                    try:
                        df.to_csv(temp_csv, index=False)
                        success, error_msg, count = self.import_elements_from_csv(temp_csv, element_type)
                        
                        total_stats[element_type] = total_stats.get(element_type, 0) + count
                        
                        if not success:
                            all_errors.append(f"工作表 '{sheet_name}': {error_msg}")
                            overall_success = False
                            
                    finally:
                        # 清理临时文件
                        import os
                        if os.path.exists(temp_csv):
                            os.remove(temp_csv)
                            
                except Exception as e:
                    all_errors.append(f"工作表 '{sheet_name}': 处理失败 - {str(e)}")
                    overall_success = False
            
            # 汇总错误信息
            error_msg = ""
            if all_errors:
                error_msg = "部分工作表导入失败:\n" + "\n".join(all_errors[:10])
                if len(all_errors) > 10:
                    error_msg += f"\n... 还有{len(all_errors)-10}个错误"
            
            return overall_success, error_msg, total_stats
            
        except Exception as e:
            return False, f"读取Excel文件失败: {str(e)}", {}

    def _infer_element_type_from_sheet_name(self, sheet_name: str) -> Optional[str]:
        """从工作表名称推断单元类型"""
        sheet_lower = sheet_name.lower()
        
        type_mapping = {
            'zerolength': 'ZeroLength',
            'twonodelink': 'TwoNodeLink', 
            'truss': 'Truss',
            'elasticbeamcolumn': 'ElasticBeamColumn',
            'elastic': 'ElasticBeamColumn',
            'dispbeamcolumn': 'DispBeamColumn',
            'displacement': 'DispBeamColumn',
            'forcebeamcolumn': 'ForceBeamColumn',
            'force': 'ForceBeamColumn'
        }
        
        for key, element_type in type_mapping.items():
            if key in sheet_lower:
                return element_type
        
        return None

    def _infer_element_type_from_columns(self, columns: List[str]) -> Optional[str]:
        """从列名推断单元类型"""
        columns_lower = [col.lower() for col in columns]
        
        # ZeroLength类型特征
        if 'mat_tags' in columns_lower and 'dirs' in columns_lower:
            return 'ZeroLength'
        
        # Truss类型特征
        if 'a' in columns_lower and 'mat_tag' in columns_lower and 'area' not in columns_lower:
            return 'Truss'
        
        # ElasticBeamColumn类型特征
        if all(col in columns_lower for col in ['area', 'e_mod', 'iz', 'transf_tag']):
            return 'ElasticBeamColumn'
        
        # DispBeamColumn类型特征
        if 'transf_tag' in columns_lower and 'integration_tag' in columns_lower and 'a' not in columns_lower:
            return 'DispBeamColumn'
        
        # ForceBeamColumn类型特征
        if 'transf_tag' in columns_lower and 'integration_tag' in columns_lower and 'max_iter' in columns_lower:
            return 'ForceBeamColumn'
        
        return None
            
    def import_from_excel(self, file_path: str, element_type: str) -> Tuple[bool, str, int]:
        """
        从Excel文件批量导入单元
        
        Args:
            file_path: Excel文件路径
            element_type: 单元类型
            
        Returns:
            Tuple[bool, str, int]: (是否成功, 错误信息, 成功导入数量)
        """
        try:
            df = pd.read_excel(file_path)
            
            # 检查必要的列
            required_cols = ['id', 'node1', 'node2']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return False, f"缺少必要列: {missing_cols}", 0
                
            success_count = 0
            error_messages = []
            
            for index, row in df.iterrows():
                try:
                    element_id = int(row['id'])
                    node1 = int(row['node1'])
                    node2 = int(row['node2'])
                    
                    # 根据单元类型处理参数
                    if element_type == 'ZeroLength':
                        mat_tags = [int(x) for x in str(row.get('mat_tags', '')).split(',') if x.strip()]
                        dirs = [int(x) for x in str(row.get('dirs', '')).split(',') if x.strip()]
                        kwargs = {
                            'node_ids': [node1, node2],
                            'mat_tags': mat_tags,
                            'dirs': dirs
                        }
                    elif element_type == 'Truss':
                        A = float(row['A'])
                        mat_tag = int(row['mat_tag'])
                        kwargs = {
                            'node_ids': [node1, node2],
                            'A': A,
                            'mat_tag': mat_tag
                        }
                    elif element_type == 'ElasticBeamColumn':
                        Area = float(row['Area'])
                        E_mod = float(row['E_mod'])
                        Iz = float(row['Iz'])
                        transf_tag = int(row['transf_tag'])
                        kwargs = {
                            'node_ids': [node1, node2],
                            'Area': Area,
                            'E_mod': E_mod,
                            'Iz': Iz,
                            'transf_tag': transf_tag
                        }
                    else:
                        # 其他类型需要更多参数
                        error_messages.append(f"第{index+1}行: 不支持的单元类型 {element_type}")
                        continue
                        
                    success, error = self.create_element(element_type, **kwargs)
                    if success:
                        success_count += 1
                    else:
                        error_messages.append(f"第{index+1}行: {error}")
                        
                except (ValueError, TypeError) as e:
                    error_messages.append(f"第{index+1}行: 数据格式错误 - {str(e)}")
                    
            if error_messages:
                error_msg = f"部分单元导入失败:\n" + "\n".join(error_messages[:10])
                if len(error_messages) > 10:
                    error_msg += f"\n... 还有{len(error_messages)-10}个错误"
            else:
                error_msg = ""
                
            return len(error_messages) == 0, error_msg, success_count
            
        except Exception as e:
            return False, f"读取Excel文件失败: {str(e)}", 0
            
    def export_elements_to_csv(self, file_path: str, element_type: str) -> bool:
        """导出单元到CSV文件"""
        try:
            elements = self.get_elements_by_type(element_type)
            if not elements:
                return False
                
            data = []
            for element in elements:
                row = {
                    'id': element.id,
                    'node1': element.node_ids[0],
                    'node2': element.node_ids[1]
                }
                
                # 根据单元类型添加特定参数
                if element_type == 'ZeroLength':
                    row['mat_tags'] = ','.join(map(str, element.mat_tags))
                    row['dirs'] = ','.join(map(str, element.dirs))
                elif element_type == 'Truss':
                    row['A'] = element.A
                    row['mat_tag'] = element.mat_tag
                elif element_type == 'ElasticBeamColumn':
                    row['Area'] = element.Area
                    row['E_mod'] = element.E_mod
                    row['Iz'] = element.Iz
                    row['transf_tag'] = element.transf_tag
                    
                data.append(row)
                
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False)
            return True
            
        except Exception:
            return False

    def export_elements_to_multisheet_file(self, file_path: str, export_types: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        导出所有单元到多页文件
        
        Args:
            file_path: 文件路径
            export_types: 要导出的单元类型列表，None表示导出所有类型
            
        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        try:
            if export_types is None:
                export_types = self.get_element_types()
            
            # 准备数据字典
            sheets_data = {}
            
            for element_type in export_types:
                elements = self.get_elements_by_type(element_type)
                if not elements:
                    continue
                    
                data = []
                for element in elements:
                    row = {
                        'id': element.id,
                        'node1': element.node_ids[0],
                        'node2': element.node_ids[1]
                    }
                    
                    # 根据单元类型添加特定参数
                    if element_type == 'ZeroLength':
                        row.update({
                            'mat_tags': ','.join(map(str, element.mat_tags)),
                            'dirs': ','.join(map(str, element.dirs)),
                            'do_rayleigh': element.do_rayleigh,
                            'r_flag': element.r_flag,
                            'vecx': ','.join(map(str, element.vecx)),
                            'vecyp': ','.join(map(str, element.vecyp))
                        })
                    elif element_type == 'TwoNodeLink':
                        row.update({
                            'mat_tags': ','.join(map(str, element.mat_tags)),
                            'dirs': ','.join(map(str, element.dirs)),
                            'vecx': ','.join(map(str, element.vecx)),
                            'vecyp': ','.join(map(str, element.vecyp)),
                            'p_delta': ','.join(map(str, element.p_delta)) if element.p_delta else '',
                            'shear_dist': ','.join(map(str, element.shear_dist)) if element.shear_dist else '',
                            'do_rayleigh': element.do_rayleigh,
                            'mass': element.mass
                        })
                    elif element_type == 'Truss':
                        row.update({
                            'A': element.A,
                            'mat_tag': element.mat_tag,
                            'rho': element.rho,
                            'c_mass': element.c_mass,
                            'do_rayleigh': element.do_rayleigh
                        })
                    elif element_type == 'ElasticBeamColumn':
                        row.update({
                            'Area': element.Area,
                            'E_mod': element.E_mod,
                            'Iz': element.Iz,
                            'transf_tag': element.transf_tag,
                            'mass': element.mass,
                            'c_mass': element.c_mass,
                            'release_code': element.release_code if element.release_code is not None else ''
                        })
                    elif element_type == 'DispBeamColumn':
                        row.update({
                            'transf_tag': element.transf_tag,
                            'integration_tag': element.integration_tag,
                            'c_mass': element.c_mass,
                            'mass': element.mass
                        })
                    elif element_type == 'ForceBeamColumn':
                        row.update({
                            'transf_tag': element.transf_tag,
                            'integration_tag': element.integration_tag,
                            'max_iter': element.max_iter,
                            'tol': element.tol,
                            'mass': element.mass
                        })
                        
                    data.append(row)
                
                if data:
                    sheets_data[element_type] = pd.DataFrame(data)
            
            if not sheets_data:
                return False, "没有可导出的单元数据"
            
            # 根据文件扩展名选择导出方式
            if file_path.lower().endswith('.csv'):
                return self._export_to_multisheet_csv(file_path, sheets_data)
            else:
                return self._export_to_excel(file_path, sheets_data)
                
        except Exception as e:
            return False, f"导出失败: {str(e)}"

    def _export_to_excel(self, file_path: str, sheets_data: Dict[str, pd.DataFrame]) -> Tuple[bool, str]:
        """导出到Excel文件"""
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                for sheet_name, df in sheets_data.items():
                    # 工作表名称限制为31字符（Excel限制）
                    safe_sheet_name = sheet_name[:31] if len(sheet_name) > 31 else sheet_name
                    df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
            return True, ""
        except Exception as e:
            return False, f"Excel导出失败: {str(e)}"

    def _export_to_multisheet_csv(self, file_path: str, sheets_data: Dict[str, pd.DataFrame]) -> Tuple[bool, str]:
        """导出到多页CSV文件"""
        try:
            # 为每个工作表创建单独的CSV文件
            base_path = file_path.replace('.csv', '')
            created_files = []
            
            for sheet_name, df in sheets_data.items():
                csv_file = f"{base_path}_{sheet_name}.csv"
                df.to_csv(csv_file, index=False)
                created_files.append(csv_file)
            
            # 创建主索引文件
            index_data = []
            for i, (sheet_name, df) in enumerate(sheets_data.items()):
                index_data.append({
                    'sheet_index': i + 1,
                    'sheet_name': sheet_name,
                    'element_count': len(df),
                    'csv_file': f"{base_path}_{sheet_name}.csv"
                })
            
            index_df = pd.DataFrame(index_data)
            index_file = f"{base_path}_index.csv"
            index_df.to_csv(index_file, index=False)
            created_files.append(index_file)
            
            return True, f"已创建多页CSV文件: {', '.join(created_files)}"
        except Exception as e:
            return False, f"CSV导出失败: {str(e)}"

    def create_element_template(self, file_path: str, element_types: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        创建单元模板文件
        
        Args:
            file_path: 模板文件路径
            element_types: 要创建模板的单元类型列表，None表示创建所有类型
            
        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        try:
            if element_types is None:
                element_types = self.get_element_types()
            
            templates_data = {}
            
            for element_type in element_types:
                template_df = self._create_element_template_df(element_type)
                if template_df is not None:
                    templates_data[element_type] = template_df
            
            if not templates_data:
                return False, "没有可创建的模板"
            
            # 根据文件扩展名选择导出方式
            if file_path.lower().endswith('.csv'):
                return self._export_to_multisheet_csv(file_path, templates_data)
            else:
                return self._export_to_excel(file_path, templates_data)
                
        except Exception as e:
            return False, f"创建模板失败: {str(e)}"

    def _create_element_template_df(self, element_type: str) -> Optional[pd.DataFrame]:
        """为指定单元类型创建模板DataFrame"""
        try:
            # 基础列
            base_columns = ['id', 'node1', 'node2']
            
            # 根据单元类型添加特定列
            if element_type == 'ZeroLength':
                columns = base_columns + ['mat_tags', 'dirs', 'do_rayleigh', 'r_flag', 'vecx', 'vecyp']
                sample_data = [{
                    'id': 1,
                    'node1': 1,
                    'node2': 2,
                    'mat_tags': '1,2,3',
                    'dirs': '1,2,3',
                    'do_rayleigh': False,
                    'r_flag': 0,
                    'vecx': '1,0,0',
                    'vecyp': '0,1,0'
                }]
            elif element_type == 'TwoNodeLink':
                columns = base_columns + ['mat_tags', 'dirs', 'vecx', 'vecyp', 'p_delta', 'shear_dist', 'do_rayleigh', 'mass']
                sample_data = [{
                    'id': 1,
                    'node1': 1,
                    'node2': 2,
                    'mat_tags': '1,2',
                    'dirs': '1,2',
                    'vecx': '1,0,0',
                    'vecyp': '0,1,0',
                    'p_delta': '',
                    'shear_dist': '',
                    'do_rayleigh': False,
                    'mass': 0.0
                }]
            elif element_type == 'Truss':
                columns = base_columns + ['A', 'mat_tag', 'rho', 'c_mass', 'do_rayleigh']
                sample_data = [{
                    'id': 1,
                    'node1': 1,
                    'node2': 2,
                    'A': 1.0,
                    'mat_tag': 1,
                    'rho': 0.0,
                    'c_mass': False,
                    'do_rayleigh': False
                }]
            elif element_type == 'ElasticBeamColumn':
                columns = base_columns + ['Area', 'E_mod', 'Iz', 'transf_tag', 'mass', 'c_mass', 'release_code']
                sample_data = [{
                    'id': 1,
                    'node1': 1,
                    'node2': 2,
                    'Area': 1.0,
                    'E_mod': 2.1e11,
                    'Iz': 1e-6,
                    'transf_tag': 1,
                    'mass': 0.0,
                    'c_mass': False,
                    'release_code': ''
                }]
            elif element_type == 'DispBeamColumn':
                columns = base_columns + ['transf_tag', 'integration_tag', 'c_mass', 'mass']
                sample_data = [{
                    'id': 1,
                    'node1': 1,
                    'node2': 2,
                    'transf_tag': 1,
                    'integration_tag': 1,
                    'c_mass': False,
                    'mass': 0.0
                }]
            elif element_type == 'ForceBeamColumn':
                columns = base_columns + ['transf_tag', 'integration_tag', 'max_iter', 'tol', 'mass']
                sample_data = [{
                    'id': 1,
                    'node1': 1,
                    'node2': 2,
                    'transf_tag': 1,
                    'integration_tag': 1,
                    'max_iter': 10,
                    'tol': 1e-12,
                    'mass': 0.0
                }]
            else:
                return None
            
            return pd.DataFrame(sample_data, columns=columns)
            
        except Exception:
            return None
            
    def get_element_count(self) -> int:
        """获取单元数量"""
        return len(self.elements)
        
    def get_element_statistics(self) -> Dict:
        """获取单元统计信息"""
        if not self.elements:
            return {'total': 0}
            
        elements = list(self.elements.values())
        type_counts = {}
        
        for element in elements:
            type_counts[element.type] = type_counts.get(element.type, 0) + 1
            
        return {
            'total': len(elements),
            'types': type_counts,
            'latest_created': max(elements, key=lambda e: e.created_at).created_at if elements else None
        }
        
    def validate_all_elements(self) -> Tuple[bool, List[str]]:
        """验证所有单元"""
        errors = []
        for element in self.elements.values():
            is_valid, error_msg = element.validate_parameters()
            if not is_valid:
                errors.append(f"单元{element.id}({element.type}): {error_msg}")
                
        return len(errors) == 0, errors