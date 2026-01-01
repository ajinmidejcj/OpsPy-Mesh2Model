#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import copy
import sys
import os
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal

# 修复导入路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from geometry.shapes import Shape, create_shape_from_dict
from meshing.mesh import Mesh, Fiber
from material.materials import MaterialLibrary, Material


class Operation:
    """操作基类，用于撤销/重做"""
    def __init__(self):
        self.timestamp = datetime.now()
        self.description = ""

    def execute(self):
        """执行操作"""
        pass

    def undo(self):
        """撤销操作"""
        pass


class OperationAddShape(Operation):
    def __init__(self, section_id, shape):
        super().__init__()
        self.section_id = section_id
        self.shape = shape
        self.description = f"添加形状 {shape.__class__.__name__} (ID: {shape.id})"

    def execute(self, data_manager):
        section = data_manager.get_section_by_id(self.section_id)
        if section:
            section.add_shape(self.shape)

    def undo(self, data_manager):
        section = data_manager.get_section_by_id(self.section_id)
        if section:
            section.remove_shape(self.shape.id)


class OperationDeleteShape(Operation):
    def __init__(self, section_id, shape):
        super().__init__()
        self.section_id = section_id
        self.shape = shape
        self.description = f"删除形状 {shape.__class__.__name__} (ID: {shape.id})"

    def execute(self, data_manager):
        section = data_manager.get_section_by_id(self.section_id)
        if section:
            section.remove_shape(self.shape.id)

    def undo(self, data_manager):
        section = data_manager.get_section_by_id(self.section_id)
        if section:
            section.add_shape(self.shape)


class OperationGenerateMesh(Operation):
    def __init__(self, section_id, old_mesh, new_mesh):
        super().__init__()
        self.section_id = section_id
        self.old_mesh = old_mesh
        self.new_mesh = new_mesh
        self.old_fibers = None  # 保存撤销时的纤维数据
        self.description = "生成网格"

    def execute(self, data_manager):
        section = data_manager.get_section_by_id(self.section_id)
        if section:
            # 保存执行前的纤维数据（用于撤销）
            self.old_fibers = section.fibers[:] if section.fibers else []
            
            section.set_mesh(self.new_mesh)
            
            # 保存现有的手动添加的纤维（如径向和直线纤维）
            existing_fibers = section.fibers[:] if section.fibers else []
            
            # 从网格生成纤维
            if self.new_mesh:
                active_shapes = section.get_active_shapes()
                new_mesh_fibers = self.new_mesh.generate_fibers(active_shapes)
            else:
                new_mesh_fibers = []
            
            # 合并纤维：保留现有纤维，添加新的网格纤维
            merged_fibers = existing_fibers[:]  # 复制现有纤维
            
            # 获取现有纤维的ID集合，用于避免重复
            existing_fiber_ids = {fiber.id for fiber in existing_fibers}
            
            # 添加新的网格纤维（ID不重复的）
            for fiber in new_mesh_fibers:
                if fiber.id not in existing_fiber_ids:
                    merged_fibers.append(fiber)
            
            # 设置合并后的纤维列表
            section.set_fibers(merged_fibers)
            
            # 重要：将网格纤维设置回网格对象，确保代码导出能获取到纤维信息
            self.new_mesh.fibers = new_mesh_fibers

    def undo(self, data_manager):
        section = data_manager.get_section_by_id(self.section_id)
        if section:
            section.set_mesh(self.old_mesh)
            
            # 撤销时恢复执行前的纤维数据
            if self.old_fibers is not None:
                section.set_fibers(self.old_fibers)
            elif self.old_mesh:
                # 如果没有保存的纤维数据，则从旧网格恢复
                old_mesh_fibers = self.old_mesh.fibers if hasattr(self.old_mesh, 'fibers') else []
                section.set_fibers(old_mesh_fibers)
            else:
                section.set_fibers([])
            
            # 撤销时也要恢复旧网格的纤维信息
            if self.old_mesh and hasattr(self.old_mesh, 'fibers'):
                self.old_mesh.fibers = self.old_fibers if self.old_fibers else []


class SectionData:
    """截面数据类，存储单个截面的所有数据"""
    def __init__(self, section_id, name="Section"):
        self.id = section_id
        self.name = name
        self.shapes = []  # 形状列表
        self.mesh = None  # 网格数据
        self.fibers = []  # 纤维列表
        self.GJ = 0.0  # 扭转刚度
        self.created_time = datetime.now()
        self.updated_time = datetime.now()

    def create_shape(self, shape_type, params):
        """根据类型和参数创建形状对象，但不添加到列表"""
        from geometry.shapes import Rectangle, Circle, Ring, PolygonShape
        shape_id = len(self.shapes) + 1
        color = self._get_shape_color(shape_id)
        
        if shape_type == "矩形":
            shape = Rectangle(
                shape_id,
                params["center_y"],
                params["center_z"],
                params["width"],
                params["height"],
                params.get("rotation", 0),
                color
            )
        elif shape_type == "圆形":
            shape = Circle(
                shape_id,
                params["center_y"],
                params["center_z"],
                params["radius"],
                color
            )
        elif shape_type == "环形":
            shape = Ring(
                shape_id,
                params["center_y"],
                params["center_z"],
                params["inner_radius"],
                params["outer_radius"],
                color
            )
        elif shape_type == "多边形":
            shape = PolygonShape(
                shape_id,
                params["vertices"],
                color
            )
        else:
            return None
        
        # 设置默认网格类型
        shape.mesh_type = 'triangular'  # 默认使用三角形网格
        
        return shape
    
    def add_shape(self, shape):
        """添加形状对象到列表"""
        self.shapes.append(shape)
        self.updated_time = datetime.now()
        return shape
    
    def _get_shape_color(self, shape_id):
        """获取形状颜色"""
        colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF', '#800000', '#008000', '#000080', '#808000']
        return colors[shape_id % len(colors)]

    def remove_shape(self, shape_id):
        """删除形状"""
        for i, shape in enumerate(self.shapes):
            if shape.id == shape_id:
                del self.shapes[i]
                self.updated_time = datetime.now()
                return True
        return False

    def get_shape_by_id(self, shape_id):
        """根据ID获取形状"""
        for shape in self.shapes:
            if shape.id == shape_id:
                return shape
        return None

    def get_active_shapes(self):
        """获取所有激活的形状"""
        return [shape for shape in self.shapes if shape.active]
    
    def get_shapes(self):
        """获取所有形状"""
        return self.shapes

    def set_mesh(self, mesh):
        """设置网格"""
        self.mesh = mesh
        self.updated_time = datetime.now()

    def set_fibers(self, fibers):
        """设置纤维"""
        self.fibers = fibers
        self.updated_time = datetime.now()

    def get_fiber_by_id(self, fiber_id):
        """根据ID获取纤维"""
        if self.mesh:
            return self.mesh.get_fiber_by_id(fiber_id)
        return None

    def get_opensees_section_command(self):
        """生成OpenSeesPy截面命令"""
        commands = []
        commands.append(f"section('Fiber', {self.id}, '-GJ', {self.GJ})")
        
        # 生成纤维命令
        fibers_to_use = []
        if self.mesh and self.mesh.fibers:
            fibers_to_use = self.mesh.fibers
        else:
            fibers_to_use = self.fibers
            
        for fiber in fibers_to_use:
            if fiber.active:
                commands.append(f"fiber({fiber.y}, {fiber.z}, {fiber.area}, {fiber.material_id})")
        
        return "\n".join(commands)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'shapes': [shape.to_dict() for shape in self.shapes],
            'mesh': self.mesh.to_dict() if self.mesh else None,
            'GJ': self.GJ,
            'created_time': self.created_time.isoformat(),
            'updated_time': self.updated_time.isoformat()
        }

    @classmethod
    def from_dict(cls, data):
        """从字典创建"""
        section = cls(data['id'], data['name'])
        section.GJ = data['GJ']
        section.created_time = datetime.fromisoformat(data['created_time'])
        section.updated_time = datetime.fromisoformat(data['updated_time'])
        
        # 加载形状
        for shape_data in data['shapes']:
            shape = create_shape_from_dict(shape_data)
            section.add_shape(shape)
        
        # 加载网格
        if data['mesh']:
            section.mesh = Mesh.from_dict(data['mesh'])
            section.fibers = section.mesh.fibers
        
        return section


class DataManager(QObject):
    """数据管理器类，管理整个项目的数据"""
    fiber_selected = pyqtSignal(object)  # 纤维选中信号
    history_changed = pyqtSignal()  # 操作历史变化信号
    
    def __init__(self):
        super().__init__()
        self.sections = []  # 截面列表
        self.current_section_id = None  # 当前选中的截面ID
        self.material_library = MaterialLibrary()  # 材料库
        
        # 操作历史
        self.undo_stack = []
        self.redo_stack = []
        
        # 初始化
        self._init_default_section()

    def _init_default_section(self):
        """初始化默认截面"""
        section = SectionData(1, "Section 1")
        self.sections.append(section)
        self.current_section_id = section.id

    def create_section(self, name="Section"):
        """创建新截面"""
        # 生成新的截面ID
        new_id = 1
        if self.sections:
            new_id = max(section.id for section in self.sections) + 1
        
        section = SectionData(new_id, name)
        self.sections.append(section)
        self.current_section_id = new_id
        
        return section

    def get_section_by_id(self, section_id):
        """根据ID获取截面"""
        for section in self.sections:
            if section.id == section_id:
                return section
        return None

    def get_current_section(self):
        """获取当前选中的截面"""
        if self.current_section_id:
            return self.get_section_by_id(self.current_section_id)
        return None

    def set_current_section(self, section_id):
        """设置当前选中的截面"""
        section = self.get_section_by_id(section_id)
        if section:
            self.current_section_id = section_id
            return True
        return False

    def delete_section(self, section_id):
        """删除截面"""
        for i, section in enumerate(self.sections):
            if section.id == section_id:
                del self.sections[i]
                # 如果删除的是当前截面，切换到第一个截面
                if self.current_section_id == section_id:
                    if self.sections:
                        self.current_section_id = self.sections[0].id
                    else:
                        self.current_section_id = None
                return True
        return False

    def add_shape(self, section_id, shape):
        """添加形状到截面"""
        operation = OperationAddShape(section_id, shape)
        operation.execute(self)
        self.undo_stack.append(operation)
        self.redo_stack.clear()
        self.history_changed.emit()

    def delete_shape(self, section_id, shape_id):
        """从截面删除形状"""
        section = self.get_section_by_id(section_id)
        if section:
            shape = section.get_shape_by_id(shape_id)
            if shape:
                operation = OperationDeleteShape(section_id, shape)
                operation.execute(self)
                self.undo_stack.append(operation)
                self.redo_stack.clear()
                self.history_changed.emit()
                return True
        return False

    def generate_mesh(self, section_id, mesh):
        """生成网格"""
        section = self.get_section_by_id(section_id)
        if section:
            old_mesh = section.mesh
            operation = OperationGenerateMesh(section_id, old_mesh, mesh)
            operation.execute(self)
            self.undo_stack.append(operation)
            self.redo_stack.clear()
            self.history_changed.emit()
            return True
        return False

    def undo(self):
        """撤销操作"""
        if self.undo_stack:
            operation = self.undo_stack.pop()
            operation.undo(self)
            self.redo_stack.append(operation)
            self.history_changed.emit()
            return operation.description
        return None

    def redo(self):
        """重做操作"""
        if self.redo_stack:
            operation = self.redo_stack.pop()
            operation.execute(self)
            self.undo_stack.append(operation)
            self.history_changed.emit()
            return operation.description
        return None

    def save_project(self, file_path):
        """保存项目"""
        data = {
            'sections': [section.to_dict() for section in self.sections],
            'current_section_id': self.current_section_id,
            'material_library': self.material_library.to_dict(),
            'version': '1.0',
            'save_time': datetime.now().isoformat()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_project(self, file_path):
        """加载项目"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 清空当前数据
        self.sections = []
        self.undo_stack.clear()
        self.redo_stack.clear()
        
        # 加载截面
        for section_data in data['sections']:
            section = SectionData.from_dict(section_data)
            self.sections.append(section)
        
        # 设置当前截面
        self.current_section_id = data.get('current_section_id')
        
        # 加载材料库
        if 'material_library' in data:
            self.material_library = MaterialLibrary.from_dict(data['material_library'])

    def get_sections(self):
        """获取所有截面"""
        return self.sections
        
    def export_opensees_commands(self, file_path):
        """导出所有截面的OpenSees命令"""
        commands = []
        for section in self.sections:
            commands.append(f"# Section {section.id}: {section.name}")
            commands.append(section.get_opensees_section_command())
            commands.append("")  # 空行分隔
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(commands))
