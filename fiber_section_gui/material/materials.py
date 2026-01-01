#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class Material:
    """材料类"""
    def __init__(self, material_id, name="材料", E=2.1e11, fy=400e6, fu=600e6, color='#FF0000'):
        self.id = material_id
        self.name = name
        self.E = E  # 弹性模量
        self.fy = fy  # 屈服强度
        self.fu = fu  # 极限强度
        self.color = color
        
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'E': self.E,
            'fy': self.fy,
            'fu': self.fu,
            'color': self.color
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建材料"""
        return cls(
            data['id'],
            data['name'],
            data['E'],
            data['fy'],
            data['fu'],
            data['color']
        )


class MaterialLibrary:
    """材料库类"""
    def __init__(self):
        self.materials = []
        self.current_material_id = 1
        
        # 初始化默认材料
        self._init_default_materials()
    
    def _init_default_materials(self):
        """初始化默认材料"""
        # 混凝土
        concrete = Material(
            self.current_material_id,
            "混凝土",
            E=34.5e9,
            fy=28.5e6,
            fu=35e6,
            color='#8B7355'
        )
        self.materials.append(concrete)
        self.current_material_id += 1
        
        # 钢筋
        steel = Material(
            self.current_material_id,
            "钢筋",
            E=2.1e11,
            fy=400e6,
            fu=600e6,
            color='#000000'
        )
        self.materials.append(steel)
        self.current_material_id += 1
    
    def add_material(self, name, E, fy, fu, color='#FF0000'):
        """添加新材料"""
        material = Material(
            self.current_material_id,
            name,
            E,
            fy,
            fu,
            color
        )
        self.materials.append(material)
        self.current_material_id += 1
        return material
    
    def remove_material(self, material_id):
        """删除材料"""
        for i, material in enumerate(self.materials):
            if material.id == material_id:
                del self.materials[i]
                return True
        return False
    
    def get_material_by_id(self, material_id):
        """根据ID获取材料"""
        for material in self.materials:
            if material.id == material_id:
                return material
        return None
    
    def get_material_by_name(self, name):
        """根据名称获取材料"""
        for material in self.materials:
            if material.name == name:
                return material
        return None
    
    def get_all_materials(self):
        """获取所有材料"""
        return self.materials
    
    def to_dict(self):
        """转换为字典"""
        return {
            'materials': [material.to_dict() for material in self.materials],
            'current_material_id': self.current_material_id
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建材料库"""
        library = cls()
        library.materials = []
        library.current_material_id = data['current_material_id']
        
        for material_data in data['materials']:
            material = Material.from_dict(material_data)
            library.materials.append(material)
        
        return library
