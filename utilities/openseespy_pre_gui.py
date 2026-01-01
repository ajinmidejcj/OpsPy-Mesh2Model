#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 将当前脚本的目录添加到sys.path中，以便能够导入项目模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
fiber_section_gui_dir = os.path.join(parent_dir, 'fiber_section_gui')
sys.path.insert(0, fiber_section_gui_dir)

# 导入必要的模块
from geometry.shapes import Rectangle, Circle
import numpy as np

# 创建一个模拟的扭转刚度计算函数（与control_panel.py中的实现相同）
def calculate_gj(shapes):
    """计算扭转刚度
    对于简单截面，GJ = G * J，其中G是剪切模量，J是扭转常数
    这里使用简化的计算方法
    """
    # 获取所有形状的边界框
    min_y, max_y = float('inf'), float('-inf')
    min_z, max_z = float('inf'), float('-inf')
    
    for shape in shapes:
        if hasattr(shape.geometry, 'bounds'):
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
        return 0
    
    # 计算截面尺寸
    height = max_z - min_z
    width = max_y - min_y
    
    # 简化的扭转常数计算（仅适用于简单矩形截面）
    # 对于复杂截面，应使用更精确的方法
    area = width * height
    
    # 假设剪切模量G为1.0（实际应用中应根据材料确定）
    G = 1.0
    
    # 使用简化的扭转常数公式 J = k * area²
    # 其中k是形状因子，对于矩形k≈0.141
    k = 0.141
    J = k * area ** 2
    
    # 扭转刚度 GJ = G * J
    GJ = G * J
    
    return GJ

# 创建一个模拟的纤维和网格检查函数（与canvas.py中的实现相同）
def filter_mesh_elements(mesh, active_shapes):
    """筛选与激活形状相关的网格元素"""
    if not mesh or not active_shapes:
        return []
    
    # 收集所有激活纤维对应的单元ID
    active_element_ids = set()
    
    # 假设纤维对象有一个active属性和一个id属性
    for fiber in mesh.get('fibers', []):
        if fiber.get('active', True):  # 默认纤维是激活的
            # 检查纤维是否在激活形状内
            point = (fiber.get('y', 0), fiber.get('z', 0))
            in_active_shape = False
            for shape in active_shapes:
                if shape.is_point_inside(point):
                    in_active_shape = True
                    break
            if in_active_shape:
                # 假设纤维索引与单元索引一致（纤维ID-1 = 单元索引）
                active_element_ids.add(fiber.get('id', 1) - 1)
    
    # 只返回与激活形状相关的网格元素
    mesh_elements = mesh.get('elements', [])
    return [mesh_elements[i] for i in range(len(mesh_elements)) if i in active_element_ids]

# 创建两个测试形状
print("创建测试形状...")
rect = Rectangle(1, 0, 0, 2, 4, 0, '#FF0000')
circle = Circle(2, 3, 3, 2, '#00FF00')

# 模拟激活形状
active_shapes = [rect, circle]

# 测试扭转刚度计算
print("测试扭转刚度计算...")
gj = calculate_gj(active_shapes)
print(f"扭转刚度计算结果: {gj:.4f}")

# 测试网格筛选
print("测试网格筛选...")
# 创建一个简单的网格示例
mesh_example = {
    'fibers': [
        {'id': 1, 'y': 0, 'z': 0, 'active': True},  # 在矩形内
        {'id': 2, 'y': 3, 'z': 3, 'active': True},  # 在圆内
        {'id': 3, 'y': -2, 'z': -2, 'active': True}  # 不在任何形状内
    ],
    'elements': [
        [0, 1, 2],  # 元素1
        [1, 2, 3],  # 元素2
        [2, 3, 4]   # 元素3
    ]
}

# 测试筛选函数
filtered_elements = filter_mesh_elements(mesh_example, active_shapes)
print(f"原始元素数量: {len(mesh_example['elements'])}")
print(f"筛选后的元素数量: {len(filtered_elements)}")
print(f"筛选后的元素: {filtered_elements}")

print("\n测试完成!")