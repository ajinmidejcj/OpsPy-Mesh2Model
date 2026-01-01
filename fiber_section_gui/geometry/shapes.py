#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from shapely.geometry import Polygon, Point, LineString
from shapely.affinity import rotate, translate


class Shape:
    def __init__(self, shape_id, color):
        self.id = shape_id
        self.material_id = None  # 材料ID初始化为None，在网格生成后赋予
        self.color = color
        self.vertices = None
        self.geometry = None
        self.active = True
        self.creation_time = None
        self.mesh_size = None  # 网格尺寸，None表示使用全局网格尺寸
        self.mesh_type = 'triangular'  # 网格类型，'triangular'或'quadrilateral'
    
    @property
    def is_active(self):
        return self.active

    def get_shapely_geometry(self):
        return self.geometry

    def is_point_inside(self, point):
        return self.geometry.contains(Point(point))

    def get_center(self):
        return list(self.geometry.centroid.coords)[0]

    def move(self, dx, dy):
        self.geometry = translate(self.geometry, dx, dy)
        self._update_vertices()

    def rotate(self, angle, origin='center'):
        if origin == 'center':
            origin = self.get_center()
        self.geometry = rotate(self.geometry, angle, origin=origin)
        self._update_vertices()

    def _update_vertices(self):
        # 更新顶点列表
        if hasattr(self.geometry, 'exterior'):
            self.vertices = list(self.geometry.exterior.coords)
        elif hasattr(self.geometry, 'coords'):
            self.vertices = list(self.geometry.coords)
    
    def draw(self, axes):
        """绘制形状"""
        import matplotlib.pyplot as plt
        
        if hasattr(self.geometry, 'exterior'):
            # 多边形
            coords = list(self.geometry.exterior.coords)
            x, y = zip(*coords)
            patch = axes.fill(x, y, color=self.color, alpha=0.3, edgecolor=self.color, linewidth=1)
        elif hasattr(self.geometry, 'coords'):
            # 线或点
            coords = list(self.geometry.coords)
            x, y = zip(*coords)
            patch = axes.plot(x, y, color=self.color, linewidth=2)
        
        return patch[0]

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.__class__.__name__,
            'material_id': self.material_id,
            'color': self.color,
            'vertices': self.vertices,
            'active': self.active,
            'mesh_size': self.mesh_size,
            'mesh_type': self.mesh_type
        }

    @classmethod
    def from_dict(cls, data):
        # 基类方法，子类需要重写
        shape = cls(data['id'], data['color'])
        shape.vertices = data['vertices']
        shape.material_id = data.get('material_id', None)
        shape.active = data.get('active', True)
        shape.mesh_size = data.get('mesh_size', None)
        shape.mesh_type = data.get('mesh_type', 'triangular')
        return shape


class Rectangle(Shape):
    def __init__(self, shape_id, center_y, center_z, width, height, rotation=0, color='#FF0000'):
        super().__init__(shape_id, color)
        self.center_y = center_y
        self.center_z = center_z
        self.width = width
        self.height = height
        self.rotation = rotation
        self.vertices = self._generate_vertices()
        self.geometry = self._create_geometry()

    def _generate_vertices(self):
        # 生成矩形顶点
        half_w = self.width / 2
        half_h = self.height / 2
        vertices = [
            (self.center_y - half_w, self.center_z - half_h),
            (self.center_y + half_w, self.center_z - half_h),
            (self.center_y + half_w, self.center_z + half_h),
            (self.center_y - half_w, self.center_z + half_h),
            (self.center_y - half_w, self.center_z - half_h)
        ]
        return vertices

    def _create_geometry(self):
        # 创建shapely几何对象
        polygon = Polygon(self.vertices[:-1])  # 去掉最后一个重复点
        if self.rotation != 0:
            polygon = rotate(polygon, self.rotation, origin=(self.center_y, self.center_z))
        return polygon

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            'center_y': self.center_y,
            'center_z': self.center_z,
            'width': self.width,
            'height': self.height,
            'rotation': self.rotation
        })
        return base_dict

    @classmethod
    def from_dict(cls, data):
        rectangle = cls(
            data['id'],
            data['center_y'],
            data['center_z'],
            data['width'],
            data['height'],
            data['rotation'],
            data['color']
        )
        rectangle.material_id = data.get('material_id', None)
        rectangle.mesh_size = data.get('mesh_size', None)
        return rectangle


class Circle(Shape):
    def __init__(self, shape_id, center_y, center_z, radius, color='#00FF00', n_points=40):
        super().__init__(shape_id, color)
        self.center_y = center_y
        self.center_z = center_z
        self.radius = radius
        self.n_points = n_points
        self.vertices = self._generate_vertices()
        self.geometry = self._create_geometry()

    def _generate_vertices(self):
        # 生成圆形顶点
        angles = np.linspace(0, 2 * np.pi, self.n_points, endpoint=False)
        vertices = []
        for angle in angles:
            y = self.center_y + self.radius * np.cos(angle)
            z = self.center_z + self.radius * np.sin(angle)
            vertices.append((y, z))
        vertices.append(vertices[0])  # 闭合
        return vertices

    def _create_geometry(self):
        return Polygon(self.vertices[:-1])

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            'center_y': self.center_y,
            'center_z': self.center_z,
            'radius': self.radius,
            'n_points': self.n_points
        })
        return base_dict

    @classmethod
    def from_dict(cls, data):
        circle = cls(
            data['id'],
            data['center_y'],
            data['center_z'],
            data['radius'],
            data['color'],
            data.get('n_points', 40)
        )
        circle.material_id = data.get('material_id', None)
        circle.mesh_size = data.get('mesh_size', None)
        return circle


class Ring(Shape):
    def __init__(self, shape_id, center_y, center_z, inner_radius, outer_radius, color='#0000FF', n_points=40):
        super().__init__(shape_id, color)
        self.center_y = center_y
        self.center_z = center_z
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.n_points = n_points
        self.vertices = self._generate_vertices()
        self.geometry = self._create_geometry()

    def _generate_vertices(self):
        # 生成环形顶点（外圆和内圆）
        angles = np.linspace(0, 2 * np.pi, self.n_points, endpoint=False)
        outer_vertices = []
        inner_vertices = []
        
        for angle in angles:
            # 外圆顶点
            y_outer = self.center_y + self.outer_radius * np.cos(angle)
            z_outer = self.center_z + self.outer_radius * np.sin(angle)
            outer_vertices.append((y_outer, z_outer))
            
            # 内圆顶点（反向）
            y_inner = self.center_y + self.inner_radius * np.cos(angle)
            z_inner = self.center_z + self.inner_radius * np.sin(angle)
            inner_vertices.insert(0, (y_inner, z_inner))
        
        # 合并外圆和内圆顶点形成环形
        vertices = outer_vertices + [outer_vertices[0]] + inner_vertices + [inner_vertices[0]]
        return vertices

    def _create_geometry(self):
        # 创建环形的shapely几何对象
        outer_circle = Point(self.center_y, self.center_z).buffer(self.outer_radius)
        inner_circle = Point(self.center_y, self.center_z).buffer(self.inner_radius)
        return outer_circle.difference(inner_circle)

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            'center_y': self.center_y,
            'center_z': self.center_z,
            'inner_radius': self.inner_radius,
            'outer_radius': self.outer_radius,
            'n_points': self.n_points
        })
        return base_dict

    @classmethod
    def from_dict(cls, data):
        ring = cls(
            data['id'],
            data['center_y'],
            data['center_z'],
            data['inner_radius'],
            data['outer_radius'],
            data['color'],
            data.get('n_points', 40)
        )
        ring.material_id = data.get('material_id', None)
        ring.mesh_size = data.get('mesh_size', None)
        return ring


class PolygonShape(Shape):
    def __init__(self, shape_id, vertices, color='#FFFF00'):
        super().__init__(shape_id, color)
        self.vertices = vertices
        self.geometry = self._create_geometry()

    def _create_geometry(self):
        # 确保多边形是闭合的
        if not self.vertices:
            # 如果没有顶点，返回一个默认的矩形多边形
            return Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        
        if self.vertices[0] != self.vertices[-1]:
            self.vertices.append(self.vertices[0])
        return Polygon(self.vertices[:-1])

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({
            'vertices': self.vertices
        })
        return base_dict

    @classmethod
    def from_dict(cls, data):
        polygon = cls(
            data['id'],
            data['vertices'],
            data['color']
        )
        polygon.material_id = data.get('material_id', None)
        polygon.mesh_size = data.get('mesh_size', None)
        return polygon


def create_shape_from_dict(data):
    """从字典创建形状对象"""
    shape_type = data['type']
    if shape_type == 'Rectangle':
        return Rectangle.from_dict(data)
    elif shape_type == 'Circle':
        return Circle.from_dict(data)
    elif shape_type == 'Ring':
        return Ring.from_dict(data)
    elif shape_type == 'PolygonShape':
        return PolygonShape.from_dict(data)
    else:
        raise ValueError(f"Unknown shape type: {shape_type}")
