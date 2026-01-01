#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from shapely.geometry import Polygon, Point
from sectionproperties.pre.geometry import Geometry, CompoundGeometry
from sectionproperties.analysis.section import Section


class Mesh:
    def __init__(self, mesh_id):
        self.id = mesh_id
        self.nodes = []  # 节点坐标 [(y1, z1), (y2, z2), ...]
        self.elements = []  # 单元节点索引 [(n1, n2, n3), ...]
        self.element_materials = []  # 单元材料ID [mat_id1, mat_id2, ...]
        self.fibers = []  # 纤维列表

    def add_node(self, y, z):
        self.nodes.append((y, z))
        return len(self.nodes) - 1  # 返回节点ID

    def add_element(self, node_ids, material_id):
        self.elements.append(node_ids)
        self.element_materials.append(material_id)
        return len(self.elements) - 1  # 返回单元ID

    def generate_fibers(self, shapes):
        """从网格单元生成纤维"""
        self.fibers = []
        fiber_id = 1
        
        for i, element in enumerate(self.elements):
            # 获取单元节点坐标
            node_coords = [self.nodes[node_id] for node_id in element]
            
            # 创建单元多边形
            element_polygon = Polygon(node_coords)
            
            # 计算单元面积
            area = element_polygon.area
            
            # 计算单元重心（纤维坐标）
            centroid = element_polygon.centroid
            y, z = centroid.x, centroid.y  # 注意shapely的坐标是(x,y)，而我们的是(y,z)
            
            # 确定纤维材料
            # 首先检查单元重心属于哪个激活的形状
            material_id = 1  # 默认材料
            for shape in shapes:
                if shape.is_active and shape.is_point_inside((y, z)):
                    if shape.material_id is not None:
                        material_id = shape.material_id
                    break
            
            # 创建纤维
            fiber = Fiber(fiber_id, y, z, area, material_id)
            self.fibers.append(fiber)
            fiber_id += 1
        
        return self.fibers

    def get_fiber_by_id(self, fiber_id):
        for fiber in self.fibers:
            if fiber.id == fiber_id:
                return fiber
        return None

    def get_fibers_by_material(self, material_id):
        return [fiber for fiber in self.fibers if fiber.material_id == material_id]

    def to_dict(self):
        return {
            'id': self.id,
            'nodes': self.nodes,
            'elements': self.elements,
            'element_materials': self.element_materials,
            'fibers': [fiber.to_dict() for fiber in self.fibers]
        }

    @classmethod
    def from_dict(cls, data):
        mesh = cls(data['id'])
        mesh.nodes = data['nodes']
        mesh.elements = data['elements']
        mesh.element_materials = data['element_materials']
        mesh.fibers = [Fiber.from_dict(fiber_data) for fiber_data in data['fibers']]
        return mesh


class Fiber:
    def __init__(self, fiber_id, y, z, area, material_id):
        self.id = fiber_id
        self.y = y
        self.z = z
        self.area = area
        self.material_id = material_id
        self.active = True

    def update_material(self, material_id):
        self.material_id = material_id

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def to_dict(self):
        return {
            'id': self.id,
            'y': self.y,
            'z': self.z,
            'area': self.area,
            'material_id': self.material_id,
            'active': self.active
        }

    @classmethod
    def from_dict(cls, data):
        fiber = cls(
            data['id'],
            data['y'],
            data['z'],
            data['area'],
            data['material_id']
        )
        fiber.active = data.get('active', True)
        return fiber


class MeshGenerator:
    def __init__(self):
        self.current_mesh_id = 1

    def generate_mesh(self, shapes, global_mesh_size=0.1):
        """从多个形状生成网格，支持混合网格类型
        
        Args:
            shapes: 几何形状列表
            global_mesh_size: 全局网格大小
        """
        if not shapes:
            return None

        # 创建合并的网格对象
        merged_mesh = Mesh(self.current_mesh_id)
        self.current_mesh_id += 1
        node_offset = 0  # 节点偏移量，用于合并多个形状的网格

        # 按形状分别生成网格
        for shape in shapes:
            if hasattr(shape, 'active') and shape.active:
                # 获取该形状的网格类型和尺寸
                mesh_type = getattr(shape, 'mesh_type', 'triangular')
                mesh_size = getattr(shape, 'mesh_size', global_mesh_size)
                
                print(f"为形状{shape.id}生成{mesh_type}网格...")
                
                # 根据网格类型生成网格
                if mesh_type == 'quadrilateral':
                    shape_mesh = self._generate_quad_mesh([shape], mesh_size)
                else:
                    shape_mesh = self._generate_tri_mesh([shape], mesh_size)
                
                if shape_mesh:
                    # 合并网格
                    # 添加节点（应用偏移量）
                    node_mapping = {}  # 旧节点ID -> 新节点ID
                    for old_node_id, (y, z) in enumerate(shape_mesh.nodes):
                        new_node_id = merged_mesh.add_node(y, z)
                        node_mapping[old_node_id] = new_node_id
                    
                    # 添加单元（重新映射节点ID）
                    for element in shape_mesh.elements:
                        mapped_element = [node_mapping[old_id] for old_id in element]
                        merged_mesh.add_element(mapped_element, shape.material_id or 1)
                    
                    print(f"形状{shape.id}网格合并完成: {len(shape_mesh.nodes)}个节点, {len(shape_mesh.elements)}个单元")
        
        print(f"混合网格生成完成: 总共{len(merged_mesh.nodes)}个节点, {len(merged_mesh.elements)}个单元")
        return merged_mesh

    def _generate_tri_mesh(self, shapes, mesh_size):
        """生成三角形网格"""
        # 确保mesh_size是有效值
        if mesh_size is None:
            mesh_size = 0.1  # 使用默认值
        
        # 确保mesh_size是浮点类型
        try:
            mesh_size = float(mesh_size)
        except (ValueError, TypeError):
            mesh_size = 0.1  # 如果转换失败，使用默认值
            
        print(f"三角形网格尺寸: {mesh_size}")
        
        # 创建sectionproperties的Geometry对象列表
        geometries = []
        for shape in shapes:
            if hasattr(shape, 'geometry') and shape.active:
                # 转换为sectionproperties的Geometry对象
                # 注意：shapely的坐标是(x,y)，而我们使用的是(y,z)
                # 需要转换坐标：(y,z) -> (x,y) 用于sectionproperties
                if hasattr(shape.geometry, 'exterior'):
                    # 多边形（包括带孔的多边形）
                    exterior_coords = [(z, y) for y, z in shape.geometry.exterior.coords]
                    
                    # 处理内部孔洞
                    interior_coords_list = []
                    if hasattr(shape.geometry, 'interiors'):
                        for interior in shape.geometry.interiors:
                            interior_coords = [(z, y) for y, z in interior.coords]
                            interior_coords_list.append(interior_coords)
                    
                    # 创建多边形（可能带孔）
                    if interior_coords_list:
                        geom = Geometry(Polygon(exterior_coords, interior_coords_list))
                    else:
                        geom = Geometry(Polygon(exterior_coords))
                    
                    geometries.append(geom)
                elif hasattr(shape.geometry, 'coords'):
                    # 线或点
                    coords = [(z, y) for y, z in shape.geometry.coords]
                    if len(coords) > 2:
                        geom = Geometry(Polygon(coords))
                        geometries.append(geom)

        if not geometries:
            return None

        # 合并所有几何形状
        if len(geometries) == 1:
            compound_geometry = geometries[0]
        else:
            compound_geometry = geometries[0]
            for geom in geometries[1:]:
                compound_geometry += geom

        try:
            # 生成网格
            print(f"开始生成三角形网格...")
            compound_geometry.create_mesh(mesh_sizes=mesh_size)
            print(f"create_mesh调用成功")
            print(f"创建Section对象...")
            section = Section(compound_geometry)
            print(f"Section对象创建成功")
            
        except Exception as e:
            print(f"三角形网格生成错误: {e}")
            import traceback
            traceback.print_exc()
            return None

        # 创建Mesh对象
        mesh = Mesh(self.current_mesh_id)
        self.current_mesh_id += 1

        # 添加节点
        print(f"开始提取节点...")
        if isinstance(section.mesh, dict):
            # 处理mesh是字典的情况
            print(f"mesh是字典类型，检查字典键: {list(section.mesh.keys())}")
            if 'vertices' in section.mesh:
                print(f"mesh字典包含vertices键")
                mesh_vertices = section.mesh['vertices']
                print(f"mesh_vertices类型: {type(mesh_vertices)}")
                print(f"mesh_vertices数量: {len(mesh_vertices)}")
                for i, vertex in enumerate(mesh_vertices):
                    # 处理numpy数组和列表/元组类型的顶点
                    if hasattr(vertex, '__getitem__') and len(vertex) >= 2:
                        # 转换坐标: (x,y) -> (y,z)
                        x, y = vertex[0], vertex[1]
                        mesh.add_node(y, x)
                    else:
                        print(f"无法识别顶点格式: {vertex}")
        elif hasattr(section, 'nodes'):
            # sectionproperties的Section对象结构
            for node in section.nodes:
                # 转换回(y,z)坐标
                mesh.add_node(node.y, node.x)
        elif hasattr(section.mesh, 'nodes'):
            # 检查section.mesh是否有nodes属性
            for node in section.mesh.nodes:
                if hasattr(node, 'x') and hasattr(node, 'y'):
                    mesh.add_node(node.y, node.x)
                elif hasattr(node, 'coords'):
                    mesh.add_node(node.coords[1], node.coords[0])

        print(f"节点提取完成，共{len(mesh.nodes)}个节点")

        # 添加单元
        print(f"开始提取单元...")
        if isinstance(section.mesh, dict):
            # 处理mesh是字典的情况
            if 'triangles' in section.mesh:
                print(f"mesh字典包含triangles键")
                mesh_triangles = section.mesh['triangles']
                print(f"mesh_triangles类型: {type(mesh_triangles)}")
                print(f"mesh_triangles数量: {len(mesh_triangles)}")
                for triangle in mesh_triangles:
                    # 处理numpy数组和列表/元组类型的单元
                    if hasattr(triangle, '__getitem__') and len(triangle) >= 3:
                        # 提取节点ID
                        node_ids = triangle[:3]
                        # 将numpy数组转换为列表，确保兼容性
                        if hasattr(node_ids, 'tolist'):
                            node_ids = node_ids.tolist()
                        mesh.add_element(node_ids, 1)  # 默认材料，后续会在generate_fibers中更新
                    else:
                        print(f"无法识别三角形单元格式: {triangle}")
        elif hasattr(section, 'elements'):
            # sectionproperties的Section对象结构
            for element in section.elements:
                if hasattr(element, 'node_ids'):
                    node_ids = element.node_ids
                elif hasattr(element, 'nodes'):
                    node_ids = list(element.nodes)
                else:
                    continue
                mesh.add_element(node_ids, 1)  # 默认材料，后续会在generate_fibers中更新
        elif hasattr(section.mesh, 'elements'):
            # 检查section.mesh是否有elements属性
            for element in section.mesh.elements:
                if hasattr(element, 'nodes'):
                    node_ids = list(element.nodes)
                else:
                    continue
                mesh.add_element(node_ids, 1)  # 默认材料，后续会在generate_fibers中更新

        print(f"三角形单元提取完成，共{len(mesh.elements)}个单元")

        return mesh

    def _generate_quad_mesh(self, shapes, mesh_size):
        """生成四边形网格"""
        # 确保mesh_size是有效值
        if mesh_size is None:
            mesh_size = 0.1  # 使用默认值
        
        # 确保mesh_size是浮点类型
        try:
            mesh_size = float(mesh_size)
        except (ValueError, TypeError):
            mesh_size = 0.1  # 如果转换失败，使用默认值
            
        print(f"四边形网格尺寸: {mesh_size}")
        
        if not shapes:
            return None

        mesh = Mesh(self.current_mesh_id)
        self.current_mesh_id += 1

        # 获取激活形状的边界框
        min_y, max_y = float('inf'), float('-inf')
        min_z, max_z = float('inf'), float('-inf')

        active_shapes = []
        for shape in shapes:
            if hasattr(shape, 'active') and shape.active:
                active_shapes.append(shape)
                # 获取形状的边界框
                if hasattr(shape, 'geometry') and hasattr(shape.geometry, 'bounds'):
                    bounds = shape.geometry.bounds
                    min_y = min(min_y, bounds[0])
                    min_z = min(min_z, bounds[1])
                    max_y = max(max_y, bounds[2])
                    max_z = max(max_z, bounds[3])
                elif hasattr(shape, 'vertices'):
                    for vertex in shape.vertices:
                        y, z = vertex
                        min_y = min(min_y, y)
                        min_z = min(min_z, z)
                        max_y = max(max_y, y)
                        max_z = max(max_z, z)

        if min_y == float('inf'):
            return None

        # 计算网格数量
        height = max_z - min_z
        width = max_y - min_y
        
        # 根据网格大小计算网格数量
        num_y = max(2, int(width / mesh_size))
        num_z = max(2, int(height / mesh_size))
        
        print(f"生成四边形网格: {num_y} x {num_z}")

        # 生成节点
        node_grid = []  # 存储节点ID的二维数组
        for i in range(num_z + 1):
            row = []
            for j in range(num_y + 1):
                y = min_y + j * width / num_y
                z = min_z + i * height / num_z
                node_id = mesh.add_node(y, z)
                row.append(node_id)
            node_grid.append(row)

        # 生成四边形单元
        for i in range(num_z):
            for j in range(num_y):
                # 获取四个角点的节点ID
                n1 = node_grid[i][j]           # 左下
                n2 = node_grid[i][j + 1]       # 右下
                n3 = node_grid[i + 1][j + 1]   # 右上
                n4 = node_grid[i + 1][j]       # 左上
                
                # 检查四个节点是否都在激活形状内
                point1 = mesh.nodes[n1]
                point2 = mesh.nodes[n2]
                point3 = mesh.nodes[n3]
                point4 = mesh.nodes[n4]
                
                # 检查所有四个角点是否在激活区域内（包括边界）
                inside_count = 0
                for point in [point1, point2, point3, point4]:
                    point_y, point_z = point
                    for shape in active_shapes:
                        # 使用within或touches来包含边界
                        if (hasattr(shape, 'geometry') and 
                            (shape.geometry.contains(Point(point_y, point_z)) or
                             shape.geometry.touches(Point(point_y, point_z)))):
                            inside_count += 1
                            break
                
                # 如果有3个或4个点在激活区域内，添加四边形单元
                if inside_count >= 3:
                    # 使用四边形单元 [n1, n2, n3, n4]
                    mesh.add_element([n1, n2, n3, n4], 1)

        print(f"四边形单元生成完成，共{len(mesh.elements)}个单元")

        return mesh

    def generate_fibers_from_mesh(self, mesh, shapes):
        """从网格生成纤维"""
        return mesh.generate_fibers(shapes)
