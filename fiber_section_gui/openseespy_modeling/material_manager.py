# -*- coding: utf-8 -*-
"""
材料管理模块
用于通过OpenSeesPy交互的方式创建和管理各种材料
支持弹性材料、塑性材料、纤维材料等多种类型
"""

import openseespy.opensees as ops
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QInputDialog, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, QTextEdit, QLabel, QTabWidget
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import uuid


class Material:
    """材料基类"""
    
    def __init__(self, material_id: int, name: str, material_type: str):
        self.id = material_id
        self.name = name
        self.type = material_type
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.tags = []
        self.user_data = {}
        
    def generate_opensees_code(self) -> str:
        """生成OpenSeesPy材料创建代码"""
        raise NotImplementedError("子类必须实现此方法")
        
    def validate_parameters(self) -> Tuple[bool, str]:
        """验证材料参数"""
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
            self.id = data['id']
            self.name = data['name']
            self.type = data['type']
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
        return f"{self.type}({self.id}): {self.name}"


class ElasticMaterial(Material):
    """弹性材料"""
    
    def __init__(self, material_id: int, name: str, E: float, nu: float = 0.0, rho: float = 0.0):
        super().__init__(material_id, name, "Elastic")
        self.E = E  # 弹性模量
        self.nu = nu  # 泊松比
        self.rho = rho  # 密度
        
    def validate_parameters(self) -> Tuple[bool, str]:
        """验证弹性材料参数"""
        if self.E <= 0:
            return False, "弹性模量必须为正数"
        if not (-1 < self.nu < 0.5):
            return False, "泊松比必须在(-1, 0.5)范围内"
        if self.rho < 0:
            return False, "密度不能为负数"
        return True, ""
        
    def generate_opensees_code(self) -> str:
        """生成OpenSeesPy弹性材料代码"""
        return f"ops.uniaxialMaterial('Elastic', {self.id}, {self.E}, {self.nu}, {self.rho})  # {self.name}"
        
    def to_dict(self) -> Dict:
        data = super().to_dict()
        data.update({
            'E': self.E,
            'nu': self.nu,
            'rho': self.rho
        })
        return data
        
    def from_dict(self, data: Dict) -> bool:
        if not super().from_dict(data):
            return False
        try:
            self.E = data['E']
            self.nu = data.get('nu', 0.0)
            self.rho = data.get('rho', 0.0)
            return True
        except Exception:
            return False


class SteelMaterial(Material):
    """钢材材料"""
    
    def __init__(self, material_id: int, name: str, fy: float, E: float, b: float = 0.0, 
                 R0: float = 20.0, cR1: float = 0.925, cR2: float = 0.15):
        super().__init__(material_id, name, "Steel")
        self.fy = fy  # 屈服强度
        self.E = E    # 弹性模量
        self.b = b    # 强化系数
        self.R0 = R0  # 过渡参数1
        self.cR1 = cR1  # 过渡参数2
        self.cR2 = cR2  # 过渡参数3
        
    def validate_parameters(self) -> Tuple[bool, str]:
        """验证钢材材料参数"""
        if self.fy <= 0:
            return False, "屈服强度必须为正数"
        if self.E <= 0:
            return False, "弹性模量必须为正数"
        if self.b < 0:
            return False, "强化系数不能为负数"
        return True, ""
        
    def generate_opensees_code(self) -> str:
        """生成OpenSeesPy钢材材料代码"""
        return f"ops.uniaxialMaterial('Steel02', {self.id}, {self.fy}, {self.E}, {self.b}, {self.R0}, {self.cR1}, {self.cR2})  # {self.name}"
        
    def to_dict(self) -> Dict:
        data = super().to_dict()
        data.update({
            'fy': self.fy,
            'E': self.E,
            'b': self.b,
            'R0': self.R0,
            'cR1': self.cR1,
            'cR2': self.cR2
        })
        return data
        
    def from_dict(self, data: Dict) -> bool:
        if not super().from_dict(data):
            return False
        try:
            self.fy = data['fy']
            self.E = data['E']
            self.b = data.get('b', 0.0)
            self.R0 = data.get('R0', 20.0)
            self.cR1 = data.get('cR1', 0.925)
            self.cR2 = data.get('cR2', 0.15)
            return True
        except Exception:
            return False


class ConcreteMaterial(Material):
    """混凝土材料"""
    
    def __init__(self, material_id: int, name: str, fc: float, epsc0: float = -0.002, 
                 epscu: float = -0.006, ft: float = 0.0, etu: float = 0.0):
        super().__init__(material_id, name, "Concrete")
        self.fc = fc  # 抗压强度
        self.epsc0 = epsc0  # 峰值应变
        self.epscu = epscu  # 极限应变
        self.ft = ft  # 抗拉强度
        self.etu = etu  # 极限拉应变
        
    def validate_parameters(self) -> Tuple[bool, str]:
        """验证混凝土材料参数"""
        if self.fc >= 0:
            return False, "抗压强度必须为负数"
        if self.epsc0 >= 0:
            return False, "峰值应变必须为负数"
        if self.epscu > self.epsc0:
            return False, "极限应变应小于峰值应变"
        return True, ""
        
    def generate_opensees_code(self) -> str:
        """生成OpenSeesPy混凝土材料代码"""
        return f"ops.uniaxialMaterial('Concrete01', {self.id}, {self.fc}, {self.epsc0}, {self.epscu}, {self.ft}, {self.etu})  # {self.name}"
        
    def to_dict(self) -> Dict:
        data = super().to_dict()
        data.update({
            'fc': self.fc,
            'epsc0': self.epsc0,
            'epscu': self.epscu,
            'ft': self.ft,
            'etu': self.etu
        })
        return data
        
    def from_dict(self, data: Dict) -> bool:
        if not super().from_dict(data):
            return False
        try:
            self.fc = data['fc']
            self.epsc0 = data.get('epsc0', -0.002)
            self.epscu = data.get('epscu', -0.006)
            self.ft = data.get('ft', 0.0)
            self.etu = data.get('etu', 0.0)
            return True
        except Exception:
            return False


class Steel02Material(Material):
    """Steel02材料 - 钢筋材料"""
    
    def __init__(self, material_id: int, name: str, Fy: float = None, E0: float = None, b: float = None,
                 fy: float = None, E: float = None,  # 兼容旧参数名
                 *params, a1: Optional[float] = None, a2: float = 1.0, 
                 a3: Optional[float] = None, a4: float = 1.0, sigInit: float = 0.0, **other_params):
        super().__init__(material_id, name, "Steel02")
        
        # 兼容性处理：支持fy/Fy和E0/E参数名
        if Fy is not None:
            self.Fy = Fy
        elif fy is not None:
            self.Fy = fy
        else:
            raise ValueError("必须提供屈服强度参数Fy或fy")
            
        if E0 is not None:
            self.E0 = E0
        elif E is not None:
            self.E0 = E
        else:
            raise ValueError("必须提供弹性模量参数E0或E")
            
        if b is not None:
            self.b = b
        else:
            raise ValueError("必须提供强化系数参数b")
            
        self.params = list(params) if params else []  # 其他参数
        self.a1 = a1 if a1 is not None else a2 * self.Fy / self.E0  # 自动计算a1
        self.a2 = a2
        self.a3 = a3 if a3 is not None else a4 * self.Fy / self.E0  # 自动计算a3
        self.a4 = a4
        self.sigInit = sigInit  # 初始应力
        
    def validate_parameters(self) -> Tuple[bool, str]:
        """验证Steel02材料参数"""
        if self.Fy <= 0:
            return False, "屈服强度Fy必须为正数"
        if self.E0 <= 0:
            return False, "初始弹性模量E0必须为正数"
        if self.b < 0:
            return False, "强化系数b不能为负数"
        if not (-1e6 <= self.sigInit <= 1e6):
            return False, "初始应力sigInit超出合理范围"
        return True, ""
        
    def generate_opensees_code(self) -> str:
        """生成OpenSeesPy Steel02材料代码"""
        params_str = ', '.join(map(str, self.params)) if self.params else ''
        if params_str:
            params_str = ', ' + params_str
            
        return f"ops.uniaxialMaterial('Steel02', {self.id}, {self.Fy}, {self.E0}, {self.b}{params_str}, a1={self.a1}, a2={self.a2}, a3={self.a3}, a4={self.a4}, sigInit={self.sigInit})  # {self.name}"
        
    def to_dict(self) -> Dict:
        data = super().to_dict()
        data.update({
            'Fy': self.Fy,
            'E0': self.E0,
            'b': self.b,
            'params': self.params,
            'a1': self.a1,
            'a2': self.a2,
            'a3': self.a3,
            'a4': self.a4,
            'sigInit': self.sigInit
        })
        return data
        
    def from_dict(self, data: Dict) -> bool:
        if not super().from_dict(data):
            return False
        try:
            self.Fy = data['Fy']
            self.E0 = data['E0']
            self.b = data['b']
            self.params = data.get('params', [])
            self.a1 = data.get('a1')
            self.a2 = data.get('a2', 1.0)
            self.a3 = data.get('a3')
            self.a4 = data.get('a4', 1.0)
            self.sigInit = data.get('sigInit', 0.0)
            
            # 自动计算a1和a3如果未设置
            if self.a1 is None:
                self.a1 = self.a2 * self.Fy / self.E0
            if self.a3 is None:
                self.a3 = self.a4 * self.Fy / self.E0
                
            return True
        except Exception:
            return False


class Concrete02Material(Material):
    """Concrete02材料 - 混凝土材料"""
    
    def __init__(self, material_id: int, name: str, fc: float, epsc0: float, 
                 epscu: float, ft: float, etu: float, 
                 Ec: Optional[float] = None, beta: float = 0.1):
        super().__init__(material_id, name, "Concrete02")
        self.fc = fc  # 抗压强度（负值）
        self.epsc0 = epsc0  # 峰值压应变
        self.epscu = epscu  # 极限压应变
        self.ft = ft  # 抗拉强度
        self.etu = etu  # 极限拉应变
        self.Ec = Ec if Ec is not None else abs(fc) / abs(epsc0) * 0.7  # 默认弹性模量
        self.beta = beta  # 退化参数
        
    def validate_parameters(self) -> Tuple[bool, str]:
        """验证Concrete02材料参数"""
        if self.fc >= 0:
            return False, "抗压强度fc必须为负数"
        if self.epsc0 >= 0:
            return False, "峰值应变epsc0必须为负数"
        if self.epscu > self.epsc0:
            return False, "极限应变epscu应小于峰值应变epsc0"
        if self.Ec <= 0:
            return False, "弹性模量Ec必须为正数"
        if not (0 <= self.beta <= 1):
            return False, "退化参数beta应在0-1范围内"
        return True, ""
        
    def generate_opensees_code(self) -> str:
        """生成OpenSeesPy Concrete02材料代码"""
        return f"ops.uniaxialMaterial('Concrete02', {self.id}, {self.fc}, {self.epsc0}, {self.epscu}, {self.ft}, {self.etu}, {self.Ec}, {self.beta})  # {self.name}"
        
    def to_dict(self) -> Dict:
        data = super().to_dict()
        data.update({
            'fc': self.fc,
            'epsc0': self.epsc0,
            'epscu': self.epscu,
            'ft': self.ft,
            'etu': self.etu,
            'Ec': self.Ec,
            'beta': self.beta
        })
        return data
        
    def from_dict(self, data: Dict) -> bool:
        if not super().from_dict(data):
            return False
        try:
            self.fc = data['fc']
            self.epsc0 = data['epsc0']
            self.epscu = data['epscu']
            self.ft = data['ft']
            self.etu = data['etu']
            self.Ec = data.get('Ec')
            self.beta = data.get('beta', 0.1)
            
            # 自动计算Ec如果未设置
            if self.Ec is None:
                self.Ec = abs(self.fc) / abs(self.epsc0) * 0.7
                
            return True
        except Exception:
            return False


class Concrete04Material(Material):
    """Concrete04材料 - 混凝土Popovics材料"""
    
    def __init__(self, material_id: int, name: str, fc: float, epsc0: float, 
                 Ec: Optional[float] = None, ft: float = 0.0, etu: float = 0.0,
                 beta: float = 0.1, es: float = 2.0):
        super().__init__(material_id, name, "Concrete04")
        self.fc = fc  # 抗压强度（负值）
        self.epsc0 = epsc0  # 峰值压应变
        self.Ec = Ec if Ec is not None else abs(fc) / abs(epsc0) * 0.7  # 弹性模量
        self.ft = ft  # 抗拉强度
        self.etu = etu  # 极限拉应变
        self.beta = beta  # 退化参数
        self.es = es  # 压应变软化参数
        
    def validate_parameters(self) -> Tuple[bool, str]:
        """验证Concrete04材料参数"""
        if self.fc >= 0:
            return False, "抗压强度fc必须为负数"
        if self.epsc0 >= 0:
            return False, "峰值应变epsc0必须为负数"
        if self.Ec <= 0:
            return False, "弹性模量Ec必须为正数"
        if not (0 <= self.beta <= 1):
            return False, "退化参数beta应在0-1范围内"
        if self.es < 0:
            return False, "压应变软化参数es不能为负数"
        return True, ""
        
    def generate_opensees_code(self) -> str:
        """生成OpenSeesPy Concrete04材料代码"""
        return f"ops.uniaxialMaterial('Concrete04', {self.id}, {self.fc}, {self.epsc0}, {self.Ec}, {self.ft}, {self.etu}, {self.beta}, {self.es})  # {self.name}"
        
    def to_dict(self) -> Dict:
        data = super().to_dict()
        data.update({
            'fc': self.fc,
            'epsc0': self.epsc0,
            'Ec': self.Ec,
            'ft': self.ft,
            'etu': self.etu,
            'beta': self.beta,
            'es': self.es
        })
        return data
        
    def from_dict(self, data: Dict) -> bool:
        if not super().from_dict(data):
            return False
        try:
            self.fc = data['fc']
            self.epsc0 = data['epsc0']
            self.Ec = data.get('Ec')
            self.ft = data.get('ft', 0.0)
            self.etu = data.get('etu', 0.0)
            self.beta = data.get('beta', 0.1)
            self.es = data.get('es', 2.0)
            
            # 自动计算Ec如果未设置
            if self.Ec is None:
                self.Ec = abs(self.fc) / abs(self.epsc0) * 0.7
                
            return True
        except Exception:
            return False


class MaterialManager(QObject):
    """材料管理类"""
    
    # 信号定义
    material_added = pyqtSignal(Material)  # 材料添加信号
    material_updated = pyqtSignal(Material)  # 材料更新信号
    material_deleted = pyqtSignal(int)  # 材料删除信号
    materials_cleared = pyqtSignal()  # 清空所有材料信号
    materials_changed = pyqtSignal()  # 材料数据变化信号
    
    def __init__(self):
        super().__init__()
        self.materials: Dict[int, Material] = {}  # 材料字典
        
        # 材料类型注册表 - 更新为具体材料类型
        self._material_types = {
            'Elastic': ElasticMaterial,
            'Steel02': Steel02Material,
            'Concrete02': Concrete02Material,
            'Concrete04': Concrete04Material,
            'Steel': SteelMaterial,  # 保留兼容性
            'Concrete': ConcreteMaterial  # 保留兼容性
        }
        
    def register_material_type(self, type_name: str, material_class):
        """注册新的材料类型"""
        self._material_types[type_name] = material_class
        
    def get_material_types(self) -> List[str]:
        """获取所有支持的材料类型"""
        return list(self._material_types.keys())
        
    def create_material(self, material_type: str, name: str, material_id: Optional[int] = None, **kwargs) -> Tuple[bool, str, Optional[Material]]:
        """
        创建材料
        
        Args:
            material_type: 材料类型
            name: 材料名称
            material_id: 材料ID（可选，如果未提供则自动分配）
            **kwargs: 材料参数
            
        Returns:
            Tuple[bool, str, Material]: (是否成功, 错误信息, 材料对象)
        """
        # 支持大小写不敏感的匹配
        normalized_type = material_type
        matched_type = None
        
        for registered_type in self._material_types.keys():
            if registered_type.lower() == material_type.lower():
                matched_type = registered_type
                break
        
        if matched_type is None:
            return False, f"不支持的材料类型: {material_type}", None
            
        material_class = self._material_types[matched_type]
        
        # 如果用户提供了material_id，使用用户指定的ID，否则使用自动分配的ID
        if material_id is not None:
            if material_id in self.materials:
                return False, f"材料ID {material_id} 已存在", None
            final_material_id = material_id
        else:
            # 自动分配ID：找到下一个可用ID
            if not self.materials:
                final_material_id = 1
            else:
                max_id = max(self.materials.keys())
                final_material_id = max_id + 1
        
        try:
            # 创建材料对象
            material = material_class(final_material_id, name, **kwargs)
            
            # 验证参数
            is_valid, error_msg = material.validate_parameters()
            if not is_valid:
                return False, error_msg, None
                
            # 添加材料
            self.materials[final_material_id] = material
            
            # 材料已成功添加
            
            # 发送信号
            self.material_added.emit(material)
            
            return True, "", material
            
        except Exception as e:
            return False, f"创建材料失败: {str(e)}", None
            
    def get_material(self, material_id: int) -> Optional[Material]:
        """获取材料"""
        return self.materials.get(material_id)
        
    def update_material(self, material_id: int, **kwargs) -> Tuple[bool, str]:
        """更新材料"""
        material = self.materials.get(material_id)
        if not material:
            return False, f"材料 {material_id} 不存在"
            
        # 保存原始参数用于回滚
        original_data = material.to_dict()
        
        try:
            # 更新参数
            for key, value in kwargs.items():
                if hasattr(material, key):
                    setattr(material, key, value)
                    
            material.updated_at = datetime.now()
            
            # 验证更新后的参数
            is_valid, error_msg = material.validate_parameters()
            if not is_valid:
                # 回滚更新
                material.from_dict(original_data)
                return False, error_msg
                
            # 发送信号
            self.material_updated.emit(material)
            
            return True, ""
            
        except Exception as e:
            # 回滚更新
            material.from_dict(original_data)
            return False, f"更新材料失败: {str(e)}"
            
    def delete_material(self, material_id: int) -> bool:
        """删除材料"""
        if material_id in self.materials:
            del self.materials[material_id]
            self.material_deleted.emit(material_id)
            return True
        return False
        
    def get_all_materials(self) -> List[Material]:
        """获取所有材料"""
        return list(self.materials.values())
        
    def get_all_material_ids(self) -> List[int]:
        """获取所有材料ID"""
        return list(self.materials.keys())
        
    def get_materials_by_type(self, material_type: str) -> List[Material]:
        """根据类型获取材料"""
        return [mat for mat in self.materials.values() if mat.type == material_type]
        
    def clear_all_materials(self):
        """清空所有材料"""
        self.materials.clear()
        self.materials_cleared.emit()
        
    def export_materials_to_python(self) -> str:
        """导出材料创建代码"""
        if not self.materials:
            return "# 无材料数据"
            
        code_lines = [
            "\n# 材料定义",
            "print('正在创建材料...')"
        ]
        
        for material in sorted(self.materials.values(), key=lambda m: m.id):
            code_lines.append(material.generate_opensees_code())
            
        return "\n".join(code_lines)
        
    def create_material_interactive_dialog(self, parent=None) -> Optional[Material]:
        """创建材料交互式对话框"""
        dialog = MaterialCreationDialog(self, parent)
        if dialog.exec_() == QDialog.Accepted:
            return dialog.get_created_material()
        return None
        
    def get_material_count(self) -> int:
        """获取材料数量"""
        return len(self.materials)
        
    def get_material_statistics(self) -> Dict:
        """获取材料统计信息"""
        if not self.materials:
            return {'total': 0}
            
        materials = list(self.materials.values())
        type_counts = {}
        
        for material in materials:
            type_counts[material.type] = type_counts.get(material.type, 0) + 1
            
        return {
            'total': len(materials),
            'types': type_counts,
            'latest_created': max(materials, key=lambda m: m.created_at).created_at if materials else None
        }
        
    def validate_all_materials(self) -> Tuple[bool, List[str]]:
        """验证所有材料"""
        errors = []
        for material in self.materials.values():
            is_valid, error_msg = material.validate_parameters()
            if not is_valid:
                errors.append(f"材料{material.id}({material.name}): {error_msg}")
                
        return len(errors) == 0, errors


class MaterialCreationDialog(QDialog):
    """材料创建对话框"""
    
    def __init__(self, material_manager: MaterialManager, parent=None):
        super().__init__(parent)
        self.material_manager = material_manager
        self.created_material = None
        self.setWindowTitle("创建新材料")
        self.setModal(True)
        self.resize(500, 400)
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # 基本信息标签页
        self.setup_basic_tab()
        
        # 弹性材料标签页
        self.setup_elastic_tab()
        
        # 钢材标签页
        self.setup_steel_tab()
        
        # 混凝土标签页
        self.setup_concrete_tab()
        
        # 按钮
        button_layout = QHBoxLayout()
        self.create_btn = QPushButton("创建")
        self.cancel_btn = QPushButton("取消")
        button_layout.addWidget(self.create_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        # 连接信号
        self.create_btn.clicked.connect(self.create_material)
        self.cancel_btn.clicked.connect(self.reject)
        
    def setup_basic_tab(self):
        """设置基本信息标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        form_layout = QFormLayout()
        
        # 材料类型
        self.type_combo = QComboBox()
        self.type_combo.addItems(self.material_manager.get_material_types())
        form_layout.addRow("材料类型:", self.type_combo)
        
        # 材料名称
        self.name_edit = QLineEdit()
        form_layout.addRow("材料名称:", self.name_edit)
        
        layout.addLayout(form_layout)
        
        # 代码预览
        self.code_preview = QTextEdit()
        self.code_preview.setReadOnly(True)
        self.code_preview.setMaximumHeight(150)
        layout.addWidget(QLabel("代码预览:"))
        layout.addWidget(self.code_preview)
        
        self.tab_widget.addTab(widget, "基本信息")
        
        # 连接信号
        self.type_combo.currentTextChanged.connect(self.update_code_preview)
        self.name_edit.textChanged.connect(self.update_code_preview)
        
        self.update_code_preview()
        
    def setup_elastic_tab(self):
        """设置弹性材料标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        form_layout = QFormLayout()
        
        # 弹性模量
        self.elastic_E = QDoubleSpinBox()
        self.elastic_E.setRange(0.0, 1e15)
        self.elastic_E.setValue(200000.0)
        form_layout.addRow("弹性模量 E:", self.elastic_E)
        
        # 泊松比
        self.elastic_nu = QDoubleSpinBox()
        self.elastic_nu.setRange(-0.99, 0.49)
        self.elastic_nu.setValue(0.3)
        form_layout.addRow("泊松比 ν:", self.elastic_nu)
        
        # 密度
        self.elastic_rho = QDoubleSpinBox()
        self.elastic_rho.setRange(0.0, 10000.0)
        self.elastic_rho.setValue(7850.0)
        form_layout.addRow("密度 ρ:", self.elastic_rho)
        
        layout.addLayout(form_layout)
        self.tab_widget.addTab(widget, "弹性材料")
        
    def setup_steel_tab(self):
        """设置钢材标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        form_layout = QFormLayout()
        
        # 屈服强度
        self.steel_fy = QDoubleSpinBox()
        self.steel_fy.setRange(0.0, 10000.0)
        self.steel_fy.setValue(355.0)
        form_layout.addRow("屈服强度 fy:", self.steel_fy)
        
        # 弹性模量
        self.steel_E = QDoubleSpinBox()
        self.steel_E.setRange(0.0, 1e15)
        self.steel_E.setValue(200000.0)
        form_layout.addRow("弹性模量 E:", self.steel_E)
        
        # 强化系数
        self.steel_b = QDoubleSpinBox()
        self.steel_b.setRange(0.0, 1.0)
        self.steel_b.setValue(0.01)
        form_layout.addRow("强化系数 b:", self.steel_b)
        
        layout.addLayout(form_layout)
        self.tab_widget.addTab(widget, "钢材")
        
    def setup_concrete_tab(self):
        """设置混凝土标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        form_layout = QFormLayout()
        
        # 抗压强度
        self.concrete_fc = QDoubleSpinBox()
        self.concrete_fc.setRange(-1000.0, 0.0)
        self.concrete_fc.setValue(-30.0)
        form_layout.addRow("抗压强度 fc:", self.concrete_fc)
        
        # 峰值应变
        self.concrete_epsc0 = QDoubleSpinBox()
        self.concrete_epsc0.setRange(-1.0, 0.0)
        self.concrete_epsc0.setValue(-0.002)
        form_layout.addRow("峰值应变:", self.concrete_epsc0)
        
        # 极限应变
        self.concrete_epscu = QDoubleSpinBox()
        self.concrete_epscu.setRange(-1.0, 0.0)
        self.concrete_epscu.setValue(-0.006)
        form_layout.addRow("极限应变:", self.concrete_epscu)
        
        layout.addLayout(form_layout)
        self.tab_widget.addTab(widget, "混凝土")
        
    def update_code_preview(self):
        """更新代码预览"""
        material_type = self.type_combo.currentText()
        name = self.name_edit.text() or "新材料"
        
        # 根据材料类型生成预览代码
        if material_type == "Elastic":
            E = self.elastic_E.value()
            nu = self.elastic_nu.value()
            rho = self.elastic_rho.value()
            code = f"ops.uniaxialMaterial('Elastic', <ID>, {E}, {nu}, {rho})  # {name}"
            
        elif material_type == "Steel":
            fy = self.steel_fy.value()
            E = self.steel_E.value()
            b = self.steel_b.value()
            code = f"ops.uniaxialMaterial('Steel02', <ID>, {fy}, {E}, {b})  # {name}"
            
        elif material_type == "Concrete":
            fc = self.concrete_fc.value()
            epsc0 = self.concrete_epsc0.value()
            epscu = self.concrete_epscu.value()
            code = f"ops.uniaxialMaterial('Concrete01', <ID>, {fc}, {epsc0}, {epscu})  # {name}"
            
        else:
            code = f"# {material_type} 材料代码"
            
        self.code_preview.setPlainText(code)
        
    def create_material(self):
        """创建材料"""
        material_type = self.type_combo.currentText()
        name = self.name_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "警告", "请输入材料名称")
            return
            
        # 根据材料类型收集参数
        if material_type == "Elastic":
            kwargs = {
                'E': self.elastic_E.value(),
                'nu': self.elastic_nu.value(),
                'rho': self.elastic_rho.value()
            }
        elif material_type == "Steel":
            kwargs = {
                'fy': self.steel_fy.value(),
                'E': self.steel_E.value(),
                'b': self.steel_b.value()
            }
        elif material_type == "Concrete":
            kwargs = {
                'fc': self.concrete_fc.value(),
                'epsc0': self.concrete_epsc0.value(),
                'epscu': self.concrete_epscu.value()
            }
        else:
            QMessageBox.warning(self, "警告", f"不支持的材料类型: {material_type}")
            return
            
        # 创建材料
        success, error_msg, material = self.material_manager.create_material(material_type, name, **kwargs)
        
        if success:
            self.created_material = material
            self.accept()
        else:
            QMessageBox.critical(self, "错误", f"创建材料失败:\n{error_msg}")
            
    def get_created_material(self) -> Optional[Material]:
        """获取创建的材料"""
        return self.created_material