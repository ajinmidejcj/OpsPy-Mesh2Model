# -*- coding: utf-8 -*-
"""
模型设置模块
用于设置有限元模型的基本参数，如自由度、维度等
"""

import openseespy.opensees as ops
from PyQt5.QtCore import QObject, pyqtSignal
from typing import Dict, List, Optional, Tuple


class DOF:
    """自由度枚举"""
    UX = 1  # X方向平动
    UY = 2  # Y方向平动
    UZ = 3  # Z方向平动
    RX = 4  # X方向转动
    RY = 5  # Y方向转动
    RZ = 6  # Z方向转动

    # 常用组合
    DOF_3D_6 = [UX, UY, UZ, RX, RY, RZ]  # 三维六自由度
    DOF_2D_3 = [UX, UY, RZ]  # 二维三自由度
    DOF_3D_TRANSLATION = [UX, UY, UZ]  # 仅三维平动
    DOF_2D_TRANSLATION = [UX, UY]  # 仅二维平动


class ModelSettings(QObject):
    """模型设置类"""
    
    # 信号定义
    model_changed = pyqtSignal()  # 模型设置改变信号
    dof_changed = pyqtSignal(list)  # 自由度改变信号
    
    def __init__(self):
        super().__init__()
        self.ndm = 3  # 空间维度 (2D: 2, 3D: 3)
        self.ndf = 6  # 自由度数量
        self.dof_list = DOF.DOF_3D_6  # 自由度列表
        self.model_name = "DefaultModel"  # 模型名称
        self.description = ""  # 模型描述
        self.created_at = None  # 创建时间
        self.updated_at = None  # 更新时间
        
    def set_model_dimension(self, ndm: int) -> bool:
        """
        设置模型维度
        
        Args:
            ndm: 空间维度 (2D: 2, 3D: 3)
            
        Returns:
            bool: 设置是否成功
        """
        if ndm not in [2, 3]:
            return False
            
        self.ndm = ndm
        # 根据维度自动调整默认自由度
        if ndm == 2:
            self.ndf = 3
            self.dof_list = DOF.DOF_2D_3
        else:
            self.ndf = 6
            self.dof_list = DOF.DOF_3D_6
            
        self.model_changed.emit()
        return True
        
    def set_dof_list(self, dof_list: List[int]) -> bool:
        """
        设置自定义自由度列表
        
        Args:
            dof_list: 自由度列表
            
        Returns:
            bool: 设置是否成功
        """
        if not dof_list or not all(isinstance(dof, int) and 1 <= dof <= 6 for dof in dof_list):
            return False
            
        self.dof_list = sorted(dof_list)  # 排序确保一致性
        self.ndf = len(self.dof_list)
        
        # 根据自由度数量推断维度
        if self.ndf <= 3:
            self.ndm = 2
        else:
            self.ndm = 3
            
        self.dof_changed.emit(self.dof_list)
        self.model_changed.emit()
        return True
        
    def set_dof_to_3d_6(self) -> bool:
        """设置为三维六自由度"""
        return self.set_dof_list(DOF.DOF_3D_6)
        
    def set_dof_to_2d_3(self) -> bool:
        """设置为二维三自由度"""
        return self.set_dof_list(DOF.DOF_2D_3)
        
    def set_dof_to_3d_translation(self) -> bool:
        """设置为仅三维平动"""
        return self.set_dof_list(DOF.DOF_3D_TRANSLATION)
        
    def set_dof_to_2d_translation(self) -> bool:
        """设置为仅二维平动"""
        return self.set_dof_list(DOF.DOF_2D_TRANSLATION)
        
    def get_dof_description(self, dof: int) -> str:
        """获取自由度描述"""
        descriptions = {
            DOF.UX: "X方向平动",
            DOF.UY: "Y方向平动", 
            DOF.UZ: "Z方向平动",
            DOF.RX: "X方向转动",
            DOF.RY: "Y方向转动",
            DOF.RZ: "Z方向转动"
        }
        return descriptions.get(dof, f"未知自由度({dof})")
        
    def get_dof_list_description(self) -> str:
        """获取自由度列表描述"""
        if not self.dof_list:
            return "无"
            
        descriptions = [self.get_dof_description(dof) for dof in self.dof_list]
        return ", ".join(descriptions)
        
    def get_ndf_value(self) -> int:
        """获取自由度数量"""
        return self.ndf
        
    def get_ndm_value(self) -> int:
        """获取空间维度"""
        return self.ndm
        
    def is_3d_model(self) -> bool:
        """是否为三维模型"""
        return self.ndm == 3
        
    def is_2d_model(self) -> bool:
        """是否为二维模型"""
        return self.ndm == 2
        
    def has_rotation_dof(self) -> bool:
        """是否包含转动自由度"""
        return any(dof >= 4 for dof in self.dof_list)
        
    def validate_node_data(self, node_data: Dict) -> Tuple[bool, str]:
        """
        验证节点数据是否符合当前模型设置
        
        Args:
            node_data: 节点数据字典 {'id': int, 'x': float, 'y': float, 'z': float, 'mass': list}
            
        Returns:
            Tuple[bool, str]: (验证结果, 错误信息)
        """
        # 检查坐标数量
        required_coords = self.ndm
        provided_coords = 0
        
        if 'x' in node_data:
            provided_coords += 1
        if 'y' in node_data:
            provided_coords += 1  
        if 'z' in node_data and self.ndm == 3:
            provided_coords += 1
            
        if provided_coords != required_coords:
            return False, f"坐标数量不匹配: 需要{required_coords}个坐标，提供{provided_coords}个"
            
        # 检查质量数据
        if 'mass' in node_data:
            mass_list = node_data['mass']
            if not isinstance(mass_list, list) or len(mass_list) != self.ndf:
                return False, f"质量数据长度不匹配: 需要{self.ndf}个质量分量，提供{len(mass_list)}个"
                
        return True, ""
        
    def generate_opensees_code(self) -> str:
        """生成OpenSeesPy模型设置代码"""
        code_lines = [
            "# 模型维度设置",
            f"ops.wipe()  # 清空模型",
            f"ops.model('basic', '-ndm', {self.ndm}, '-ndf', {self.ndf})  # 设置模型维度: {self.ndm}D, 自由度: {self.ndf}"
        ]
        
        if self.model_name != "DefaultModel":
            code_lines.append(f"# 模型名称: {self.model_name}")
            
        if self.description:
            code_lines.append(f"# 模型描述: {self.description}")
            
        return "\n".join(code_lines)
        
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'ndm': self.ndm,
            'ndf': self.ndf,
            'dof_list': self.dof_list,
            'model_name': self.model_name,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
    def from_dict(self, data: Dict) -> bool:
        """从字典加载数据"""
        try:
            self.ndm = data.get('ndm', 3)
            self.ndf = data.get('ndf', 6)
            self.dof_list = data.get('dof_list', DOF.DOF_3D_6)
            self.model_name = data.get('model_name', 'DefaultModel')
            self.description = data.get('description', '')
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')
            return True
        except Exception:
            return False
            
    def __str__(self) -> str:
        return f"Model(ndm={self.ndm}, ndf={self.ndf}, name='{self.model_name}')"
        
    def __repr__(self) -> str:
        return f"ModelSettings(ndm={self.ndm}, ndf={self.ndf}, dof={self.dof_list})"