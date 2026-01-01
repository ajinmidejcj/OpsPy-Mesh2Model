#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
圆形纤维生成器
提供两种新的圆形纤维添加方式：
1. 起点终点圆形纤维：一列钢筋纤维沿指定路径分布
2. 圆形截面钢筋纤维：在指定圆心周围径向分布
"""

import sys
import os

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import math
import numpy as np
from typing import List, Tuple, Optional
from fiber_section_gui.meshing.mesh import Fiber

class CircleFiberGenerator:
    """圆形纤维生成器"""
    
    @staticmethod
    def generate_line_circular_fibers(
        start_y: float, start_z: float,  # 起点坐标
        end_y: float, end_z: float,      # 终点坐标  
        radius: float,                   # 圆形纤维半径
        num_fibers: int,                 # 纤维数量
        fiber_area: float,               # 纤维面积
        material_id: int = 1             # 材料ID
    ) -> List[Fiber]:
        """
        生成沿直线路径分布的圆形纤维（一列钢筋）
        
        Args:
            start_y, start_z: 起点坐标
            end_y, end_z: 终点坐标
            radius: 圆形纤维半径
            num_fibers: 纤维数量
            fiber_area: 纤维面积
            material_id: 材料ID
            
        Returns:
            List[Fiber]: 生成的纤维列表
        """
        fibers = []
        
        # 计算直线的方向向量
        dy = end_y - start_y
        dz = end_z - start_z
        line_length = math.sqrt(dy**2 + dz**2)
        
        if line_length == 0:
            # 起点和终点相同，退化为单个点
            fiber = Fiber(1, start_y, start_z, fiber_area, material_id)
            fibers.append(fiber)
            return fibers
        
        # 归一化方向向量
        direction_y = dy / line_length
        direction_z = dz / line_length
        
        # 生成沿直线分布的纤维
        for i in range(num_fibers):
            # 均匀分布在直线上
            t = i / (num_fibers - 1) if num_fibers > 1 else 0.5
            
            # 计算纤维中心点坐标
            center_y = start_y + t * dy
            center_z = start_z + t * dz
            
            # 计算纤维面积（圆形面积）
            if fiber_area <= 0:
                actual_fiber_area = math.pi * radius**2
            else:
                actual_fiber_area = fiber_area
            
            # 创建纤维
            fiber = Fiber(i + 1, center_y, center_z, actual_fiber_area, material_id)
            fibers.append(fiber)
        
        return fibers
    
    @staticmethod
    def generate_radial_circular_fibers(
        center_y: float, center_z: float,  # 圆心坐标
        radius: float,                     # 圆形纤维半径
        num_fibers: int,                   # 纤维数量
        fiber_area: float,                 # 纤维面积
        material_id: int = 1,              # 材料ID
        start_angle: float = 0.0,          # 起始角度（度）
        end_angle: float = 360.0           # 结束角度（度）
    ) -> List[Fiber]:
        """
        生成径向分布的圆形纤维（圆形截面钢筋）
        
        Args:
            center_y, center_z: 圆心坐标
            radius: 圆形纤维半径
            num_fibers: 纤维数量
            fiber_area: 纤维面积
            material_id: 材料ID
            start_angle: 起始角度（度）
            end_angle: 结束角度（度）
            
        Returns:
            List[Fiber]: 生成的纤维列表
        """
        fibers = []
        
        # 计算角度范围
        angle_range = end_angle - start_angle
        if angle_range <= 0:
            angle_range = 360.0
        
        # 生成径向分布的纤维
        for i in range(num_fibers):
            # 均匀分布在角度范围内
            angle_ratio = i / num_fibers if num_fibers > 0 else 0
            angle_deg = start_angle + angle_ratio * angle_range
            angle_rad = math.radians(angle_deg)
            
            # 计算纤维中心点坐标
            fiber_y = center_y + radius * math.cos(angle_rad)
            fiber_z = center_z + radius * math.sin(angle_rad)
            
            # 计算纤维面积（圆形面积）
            if fiber_area <= 0:
                actual_fiber_area = math.pi * radius**2
            else:
                actual_fiber_area = fiber_area
            
            # 创建纤维
            fiber = Fiber(i + 1, fiber_y, fiber_z, actual_fiber_area, material_id)
            fibers.append(fiber)
        
        return fibers
    
    @staticmethod
    def generate_circular_fiber_ring(
        center_y: float, center_z: float,     # 圆心坐标
        ring_radius: float,                   # 圆环半径
        fiber_radius: float,                  # 单个纤维半径
        num_fibers: int,                      # 纤维数量
        fiber_area: Optional[float] = None,   # 纤维面积（可选）
        material_id: int = 1,                 # 材料ID
        start_angle: float = 0.0,             # 起始角度（度）
        end_angle: float = 360.0              # 结束角度（度）
    ) -> List[Fiber]:
        """
        生成圆环形状的纤维分布
        
        Args:
            center_y, center_z: 圆心坐标
            ring_radius: 圆环半径
            fiber_radius: 单个纤维半径
            num_fibers: 纤维数量
            fiber_area: 纤维面积（如果为None则自动计算）
            material_id: 材料ID
            start_angle: 起始角度（度）
            end_angle: 结束角度（度）
            
        Returns:
            List[Fiber]: 生成的纤维列表
        """
        return CircleFiberGenerator.generate_radial_circular_fibers(
            center_y, center_z, ring_radius, num_fibers,
            fiber_area if fiber_area else math.pi * fiber_radius**2,
            material_id, start_angle, end_angle
        )

# 测试函数
def test_circle_fiber_generator():
    """测试圆形纤维生成器"""
    print("=== 测试圆形纤维生成器 ===")
    
    # 测试1: 直线圆形纤维
    print("\n1. 测试直线圆形纤维生成...")
    line_fibers = CircleFiberGenerator.generate_line_circular_fibers(
        start_y=0, start_z=0,
        end_y=10, end_z=5,
        radius=0.1,
        num_fibers=5,
        fiber_area=0.0314,  # pi * 0.1^2
        material_id=1
    )
    
    print(f"   生成了 {len(line_fibers)} 个直线分布的圆形纤维")
    for fiber in line_fibers[:3]:  # 显示前3个
        print(f"   纤维{fiber.id}: 位置({fiber.y:.2f}, {fiber.z:.2f}), 面积{fiber.area:.4f}")
    
    # 测试2: 径向圆形纤维
    print("\n2. 测试径向圆形纤维生成...")
    radial_fibers = CircleFiberGenerator.generate_radial_circular_fibers(
        center_y=5, center_z=5,
        radius=3.0,
        num_fibers=8,
        fiber_area=0.0314,
        material_id=2
    )
    
    print(f"   生成了 {len(radial_fibers)} 个径向分布的圆形纤维")
    for fiber in radial_fibers[:4]:  # 显示前4个
        print(f"   纤维{fiber.id}: 位置({fiber.y:.2f}, {fiber.z:.2f}), 面积{fiber.area:.4f}")
    
    # 测试3: 圆环纤维
    print("\n3. 测试圆环纤维生成...")
    ring_fibers = CircleFiberGenerator.generate_circular_fiber_ring(
        center_y=0, center_z=0,
        ring_radius=2.0,
        fiber_radius=0.05,
        num_fibers=12,
        material_id=3,
        start_angle=45,
        end_angle=315
    )
    
    print(f"   生成了 {len(ring_fibers)} 个圆环分布的纤维")
    for fiber in ring_fibers[:3]:  # 显示前3个
        print(f"   纤维{fiber.id}: 位置({fiber.y:.2f}, {fiber.z:.2f}), 面积{fiber.area:.4f}")
    
    print("\n=== 圆形纤维生成器测试完成 ===")

if __name__ == "__main__":
    test_circle_fiber_generator()