# -*- coding: utf-8 -*-
"""
节点管理模块
用于管理有限元模型的节点创建、编辑和验证
支持单个节点创建和Excel/CSV批量导入
"""

import openseespy.opensees as ops
import pandas as pd
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from PyQt5.QtWidgets import QMessageBox
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
import uuid
import openpyxl


class Node:
    """节点类"""
    
    def __init__(self, node_id: int, x: float, y: float, z: float = 0.0, 
                 mass: Optional[List[float]] = None, name: str = ""):
        self.id = node_id
        self.x = x
        self.y = y
        self.z = z
        self.mass = mass or [0.0] * 6  # 默认6个质量分量
        self.name = name
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.tags = []  # 标签，用于分组管理
        self.user_data = {}  # 用户自定义数据
        
    def get_coordinates(self, ndm: int) -> List[float]:
        """获取坐标列表"""
        coords = [self.x, self.y]
        if ndm == 3:
            coords.append(self.z)
        return coords
        
    def set_coordinates(self, x: float, y: float, z: float = 0.0):
        """设置坐标"""
        self.x = x
        self.y = y
        self.z = z
        self.updated_at = datetime.now()
        
    def set_mass(self, mass: List[float]):
        """设置质量"""
        self.mass = mass
        self.updated_at = datetime.now()
        
    def is_valid(self, ndm: int = 3, ndf: int = 6) -> Tuple[bool, str]:
        """验证节点数据有效性"""
        # 检查ID
        if not isinstance(self.id, int) or self.id <= 0:
            return False, f"节点ID必须为正整数"
            
        # 检查坐标
        if not all(isinstance(coord, (int, float)) for coord in [self.x, self.y, self.z]):
            return False, "坐标必须为数值"
            
        if ndm == 2 and self.z != 0:
            return False, "2D模型中Z坐标必须为0"
            
        # 检查质量
        if len(self.mass) != ndf:
            return False, f"质量数据长度必须为{ndf}"
            
        if not all(isinstance(m, (int, float)) for m in self.mass):
            return False, "质量数据必须为数值"
            
        return True, ""
        
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'z': self.z,
            'mass': self.mass,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'tags': self.tags,
            'user_data': self.user_data
        }
        
    def from_dict(self, data: Dict) -> bool:
        """从字典加载数据"""
        try:
            self.id = data['id']
            self.x = data['x']
            self.y = data['y']
            self.z = data.get('z', 0.0)
            self.mass = data.get('mass', [0.0] * 6)
            self.name = data.get('name', '')
            self.tags = data.get('tags', [])
            self.user_data = data.get('user_data', {})
            
            # 处理时间戳
            if 'created_at' in data:
                self.created_at = datetime.fromisoformat(data['created_at'])
            if 'updated_at' in data:
                self.updated_at = datetime.fromisoformat(data['updated_at'])
                
            return True
        except Exception:
            return False
            
    def __str__(self) -> str:
        return f"Node({self.id}): ({self.x}, {self.y}, {self.z})"
        
    def __repr__(self) -> str:
        return f"Node(id={self.id}, x={self.x}, y={self.y}, z={self.z}, mass={self.mass})"


class NodeManager(QObject):
    """节点管理类"""
    
    # 信号定义
    node_added = pyqtSignal(Node)  # 节点添加信号
    node_updated = pyqtSignal(Node)  # 节点更新信号
    node_deleted = pyqtSignal(int)  # 节点删除信号
    nodes_cleared = pyqtSignal()  # 清空所有节点信号
    nodes_changed = pyqtSignal()  # 节点数据变化信号
    node_validation_error = pyqtSignal(str)  # 节点验证错误信号
    
    def __init__(self, model_settings=None):
        super().__init__()
        self.nodes: Dict[int, Node] = {}  # 节点字典
        self.model_settings = model_settings  # 模型设置引用
        self._next_node_id = 1  # 下一个可用的节点ID
        self._node_groups = {}  # 节点分组
        
    def set_model_settings(self, model_settings):
        """设置模型设置"""
        self.model_settings = model_settings
        
    def create_node(self, node_id: int, x: float, y: float, z: float = 0.0,
                   mass: Optional[List[float]] = None, name: str = "") -> Tuple[bool, str]:
        """
        创建单个节点
        
        Args:
            node_id: 节点ID
            x, y, z: 坐标
            mass: 质量列表
            name: 节点名称
            
        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        # 验证模型设置
        if not self.model_settings:
            return False, "未设置模型参数"
            
        # 创建节点
        node = Node(node_id, x, y, z, mass, name)
        
        # 验证节点
        is_valid, error_msg = node.is_valid(self.model_settings.ndm, self.model_settings.ndf)
        if not is_valid:
            return False, error_msg
            
        # 检查ID冲突
        if node_id in self.nodes:
            return False, f"节点ID {node_id} 已存在"
            
        # 添加节点
        self.nodes[node_id] = node
        self._next_node_id = max(self._next_node_id, node_id + 1)
        
        # 发送信号
        self.node_added.emit(node)
        
        return True, ""
        
    def get_node(self, node_id: int) -> Optional[Node]:
        """获取节点"""
        return self.nodes.get(node_id)
        
    def update_node(self, node_id: int, x: Optional[float] = None, 
                   y: Optional[float] = None, z: Optional[float] = None,
                   mass: Optional[List[float]] = None, name: Optional[str] = None) -> Tuple[bool, str]:
        """更新节点"""
        node = self.nodes.get(node_id)
        if not node:
            return False, f"节点 {node_id} 不存在"
            
        # 更新坐标
        if x is not None:
            node.x = x
        if y is not None:
            node.y = y
        if z is not None:
            node.z = z
        if mass is not None:
            node.set_mass(mass)
        if name is not None:
            node.name = name
            
        node.updated_at = datetime.now()
        
        # 验证更新后的节点
        is_valid, error_msg = node.is_valid(self.model_settings.ndm, self.model_settings.ndf)
        if not is_valid:
            # 回滚更新
            return False, error_msg
            
        # 发送信号
        self.node_updated.emit(node)
        
        return True, ""
        
    def delete_node(self, node_id: int) -> bool:
        """删除节点"""
        if node_id in self.nodes:
            del self.nodes[node_id]
            self.node_deleted.emit(node_id)
            return True
        return False
        
    def get_all_nodes(self) -> List[Node]:
        """获取所有节点"""
        return list(self.nodes.values())
        
    def get_all_node_ids(self) -> List[int]:
        """获取所有节点ID"""
        return list(self.nodes.keys())
        
    def get_nodes_by_tag(self, tag: str) -> List[Node]:
        """根据标签获取节点"""
        return [node for node in self.nodes.values() if tag in node.tags]
        
    def add_tag_to_node(self, node_id: int, tag: str) -> bool:
        """为节点添加标签"""
        node = self.nodes.get(node_id)
        if node and tag not in node.tags:
            node.tags.append(tag)
            self.node_updated.emit(node)
            return True
        return False
        
    def remove_tag_from_node(self, node_id: int, tag: str) -> bool:
        """从节点移除标签"""
        node = self.nodes.get(node_id)
        if node and tag in node.tags:
            node.tags.remove(tag)
            self.node_updated.emit(node)
            return True
        return False
        
    def clear_all_nodes(self):
        """清空所有节点"""
        self.nodes.clear()
        self.nodes_cleared.emit()
        
    def import_from_csv(self, file_path: str, 
                       id_col: str = 'id', x_col: str = 'x', 
                       y_col: str = 'y', z_col: str = 'z') -> Tuple[bool, str, int]:
        """
        从CSV文件批量导入节点
        
        Args:
            file_path: CSV文件路径
            id_col, x_col, y_col, z_col: 列名
            
        Returns:
            Tuple[bool, str, int]: (是否成功, 错误信息, 成功导入数量)
        """
        try:
            df = pd.read_csv(file_path)
            
            # 检查必要的列是否存在
            required_cols = [id_col, x_col, y_col]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return False, f"缺少必要列: {missing_cols}", 0
                
            success_count = 0
            error_messages = []
            
            for index, row in df.iterrows():
                try:
                    node_id = int(row[id_col])
                    x = float(row[x_col])
                    y = float(row[y_col])
                    z = float(row.get(z_col, 0.0))
                    
                    success, error = self.create_node(node_id, x, y, z)
                    if success:
                        success_count += 1
                    else:
                        error_messages.append(f"第{index+1}行: {error}")
                        
                except (ValueError, TypeError) as e:
                    error_messages.append(f"第{index+1}行: 数据格式错误 - {str(e)}")
                    
            if error_messages:
                error_msg = f"部分节点导入失败:\n" + "\n".join(error_messages[:10])
                if len(error_messages) > 10:
                    error_msg += f"\n... 还有{len(error_messages)-10}个错误"
            else:
                error_msg = ""
                
            return len(error_messages) == 0, error_msg, success_count
            
        except Exception as e:
            return False, f"读取CSV文件失败: {str(e)}", 0
            
    def import_from_excel(self, file_path: str, 
                         id_col: str = 'id', x_col: str = 'x', 
                         y_col: str = 'y', z_col: str = 'z',
                         mass_col: str = 'mass') -> Tuple[bool, str, int]:
        """
        从Excel文件批量导入节点
        
        Args:
            file_path: Excel文件路径
            id_col, x_col, y_col, z_col, mass_col: 列名
            
        Returns:
            Tuple[bool, str, int]: (是否成功, 错误信息, 成功导入数量)
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 检查必要的列是否存在
            required_cols = [id_col, x_col, y_col]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return False, f"缺少必要列: {missing_cols}", 0
                
            success_count = 0
            error_messages = []
            
            for index, row in df.iterrows():
                try:
                    node_id = int(row[id_col])
                    x = float(row[x_col])
                    y = float(row[y_col])
                    z = float(row.get(z_col, 0.0))
                    
                    # 处理质量列
                    mass = None
                    if mass_col in df.columns and pd.notna(row[mass_col]):
                        try:
                            if isinstance(row[mass_col], str):
                                # 如果是字符串，按逗号分割
                                mass = [float(m) for m in row[mass_col].split(',')]
                            else:
                                # 如果是单个数值，转换为列表
                                mass = [float(row[mass_col])] * 6
                        except (ValueError, TypeError):
                            mass = None
                    
                    if mass is None:
                        mass = [0.0] * 6
                    
                    success, error = self.create_node(node_id, x, y, z, mass)
                    if success:
                        success_count += 1
                    else:
                        error_messages.append(f"第{index+1}行: {error}")
                        
                except (ValueError, TypeError) as e:
                    error_messages.append(f"第{index+1}行: 数据格式错误 - {str(e)}")
                    
            if error_messages:
                error_msg = f"部分节点导入失败:\n" + "\n".join(error_messages[:10])
                if len(error_messages) > 10:
                    error_msg += f"\n... 还有{len(error_messages)-10}个错误"
            else:
                error_msg = ""
                
            return len(error_messages) == 0, error_msg, success_count
            
        except Exception as e:
            return False, f"读取Excel文件失败: {str(e)}", 0
            
    def export_to_csv(self, file_path: str) -> bool:
        """导出节点到CSV文件"""
        try:
            data = []
            for node in self.get_all_nodes():
                data.append({
                    'id': node.id,
                    'x': node.x,
                    'y': node.y,
                    'z': node.z,
                    'mass': ','.join(map(str, node.mass)),
                    'name': node.name
                })
                
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False)
            return True
            
        except Exception:
            return False
            
    def generate_opensees_code(self) -> str:
        """生成OpenSeesPy节点创建代码"""
        if not self.nodes:
            return "# 无节点数据"
            
        code_lines = [
            "\n# 节点创建",
            "print('正在创建节点...')"
        ]
        
        for node in sorted(self.nodes.values(), key=lambda n: n.id):
            coords = node.get_coordinates(self.model_settings.ndm)
            mass_str = ' '.join(map(str, node.mass[:self.model_settings.ndf]))
            
            code_line = f"ops.node({node.id}, {coords[0]}, {coords[1]}"
            if self.model_settings.ndm == 3:
                code_line += f", {coords[2]}"
            code_line += f", '-mass', {mass_str})"
            
            if node.name:
                code_line += f"  # {node.name}"
                
            code_lines.append(code_line)
            
        return "\n".join(code_lines)
        
    def get_node_count(self) -> int:
        """获取节点数量"""
        return len(self.nodes)
        
    def get_node_statistics(self) -> Dict:
        """获取节点统计信息"""
        if not self.nodes:
            return {'total': 0}
            
        nodes = list(self.nodes.values())
        coords_x = [n.x for n in nodes]
        coords_y = [n.y for n in nodes]
        coords_z = [n.z for n in nodes]
        
        return {
            'total': len(nodes),
            'coordinate_ranges': {
                'x': {'min': min(coords_x), 'max': max(coords_x)},
                'y': {'min': min(coords_y), 'max': max(coords_y)},
                'z': {'min': min(coords_z), 'max': max(coords_z)} if self.model_settings and self.model_settings.ndm == 3 else {'min': 0, 'max': 0}
            },
            'groups': len(self._node_groups),
            'tags': len(set(tag for node in nodes for tag in node.tags))
        }
        
    def validate_all_nodes(self) -> Tuple[bool, List[str]]:
        """验证所有节点"""
        if not self.model_settings:
            return False, ["未设置模型参数"]
            
        errors = []
        for node in self.nodes.values():
            is_valid, error_msg = node.is_valid(self.model_settings.ndm, self.model_settings.ndf)
            if not is_valid:
                errors.append(f"节点{node.id}: {error_msg}")
                
        return len(errors) == 0, errors