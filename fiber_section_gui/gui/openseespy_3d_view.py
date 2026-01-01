#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenSeesPy三维坐标系可视化组件
提供节点、单元的三维可视化和交互功能
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QAction, QLabel, QFrame
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QIcon

# 导入OpenSeesPy控制器
from fiber_section_gui.openseespy_modeling.openseespy_controller import OpenSeesPyController
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle, FancyBboxPatch
from matplotlib.colors import ListedColormap
import random

# 设置matplotlib支持中文
plt.rcParams['font.sans-serif'] = ['SimHei']  
plt.rcParams['axes.unicode_minus'] = False  


class Node3D:
    """三维节点类"""
    def __init__(self, node_id: int, x: float, y: float, z: float, active: bool = True):
        self.id = node_id
        self.x = x
        self.y = y  
        self.z = z
        self.active = active  # 是否激活
        self.selected = False  # 是否被选中
        self.info = {}  # 额外信息
        
    def get_position(self) -> Tuple[float, float, float]:
        """获取节点位置"""
        return (self.x, self.y, self.z)
        
    def set_position(self, x: float, y: float, z: float):
        """设置节点位置"""
        self.x = x
        self.y = y
        self.z = z


class Element3D:
    """三维单元类"""
    def __init__(self, element_id: int, node_i: int, node_j: int, element_type: str = "Beam", active: bool = True):
        self.id = element_id
        self.node_i = node_i
        self.node_j = node_j
        self.type = element_type
        self.active = active
        self.selected = False
        self.color = self._get_color_for_type()
        self.info = {}  # 额外信息
        
    def _get_color_for_type(self) -> str:
        """根据单元类型获取颜色"""
        color_map = {
            'Beam': 'blue',
            'Column': 'red', 
            'Brace': 'green',
            'Shell': 'orange',
            'Solid': 'purple',
            'Link': 'cyan',
            'Spring': 'magenta',
            'Truss': 'brown',
            'Frame': 'pink'
        }
        return color_map.get(self.type, 'gray')  # 默认灰色
        
    def get_connected_nodes(self) -> Tuple[int, int]:
        """获取连接的节点ID"""
        return (self.node_i, self.node_j)


class OpenSeesPy3DView(QWidget):
    """OpenSeesPy三维可视化视图"""
    
    # 信号定义
    node_clicked = pyqtSignal(int)  # 节点点击信号
    element_clicked = pyqtSignal(int)  # 单元点击信号
    view_changed = pyqtSignal()  # 视图变化信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 数据存储
        self.nodes: Dict[int, Node3D] = {}
        self.elements: Dict[int, Element3D] = {}
        self.next_node_id = 1
        self.next_element_id = 1
        
        # 视图状态
        self.show_nodes = True
        self.show_elements = True
        self.show_grid = True
        self.selected_node_ids = set()
        self.selected_element_ids = set()
        
        # 创建界面
        self._create_ui()
        
        # 初始化3D视图
        self._init_3d_plot()
        
        # 连接信号
        self._connect_signals()
        
        # 定时刷新
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_view)
        self.refresh_timer.start(100)  # 每100ms刷新一次
        
    def _create_ui(self):
        """创建用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建工具栏
        self._create_toolbar()
        layout.addWidget(self.toolbar)
        
        # 创建matplotlib画布
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.figure.add_subplot(111, projection='3d')
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # 状态栏
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel)
        status_layout = QHBoxLayout(status_frame)
        
        self.status_label = QLabel("就绪")
        self.coord_label = QLabel("坐标: (0, 0, 0)")
        self.selection_label = QLabel("选中: 0个节点, 0个单元")
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.coord_label)
        status_layout.addStretch()
        status_layout.addWidget(self.selection_label)
        
        layout.addWidget(status_frame)
        
    def _create_toolbar(self):
        """创建工具栏"""
        self.toolbar = QToolBar("3D视图工具栏")
        self.toolbar.setIconSize(QSize(16, 16))
        
        # 显示控制
        self.show_nodes_action = QAction("显示节点", self)
        self.show_nodes_action.setCheckable(True)
        self.show_nodes_action.setChecked(True)
        self.show_nodes_action.triggered.connect(self._toggle_nodes)
        
        self.show_elements_action = QAction("显示单元", self)  
        self.show_elements_action.setCheckable(True)
        self.show_elements_action.setChecked(True)
        self.show_elements_action.triggered.connect(self._toggle_elements)
        
        self.show_grid_action = QAction("显示网格", self)
        self.show_grid_action.setCheckable(True)
        self.show_grid_action.setChecked(True)
        self.show_grid_action.triggered.connect(self._toggle_grid)
        
        # 视图控制
        self.reset_view_action = QAction("重置视图", self)
        self.reset_view_action.triggered.connect(self._reset_view)
        
        self.fit_view_action = QAction("适应视图", self)
        self.fit_view_action.triggered.connect(self._fit_view)
        
        # 选择控制
        self.clear_selection_action = QAction("清除选择", self)
        self.clear_selection_action.triggered.connect(self._clear_selection)
        
        # 添加到工具栏
        self.toolbar.addAction(self.show_nodes_action)
        self.toolbar.addAction(self.show_elements_action)
        self.toolbar.addAction(self.show_grid_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.reset_view_action)
        self.toolbar.addAction(self.fit_view_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.clear_selection_action)
        
    def _init_3d_plot(self):
        """初始化3D绘图"""
        # 设置坐标轴
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        self.ax.set_title('OpenSeesPy三维模型视图')
        
        # 设置视角
        self.ax.view_init(elev=20, azim=45)
        
        # 设置网格
        self.ax.grid(True, alpha=0.3)
        
        # 初始化绘图元素
        self.node_scatter = None
        self.node_texts = []
        self.element_lines = []
        
        # 绘制坐标系
        self._draw_coordinate_system()
        
        # 初始刷新
        self.refresh_view()
        
    def _draw_coordinate_system(self):
        """绘制坐标系"""
        # X轴 (红色)
        self.ax.quiver(0, 0, 0, 2, 0, 0, color='red', arrow_length_ratio=0.1, alpha=0.7)
        # Y轴 (绿色)  
        self.ax.quiver(0, 0, 0, 0, 2, 0, color='green', arrow_length_ratio=0.1, alpha=0.7)
        # Z轴 (蓝色)
        self.ax.quiver(0, 0, 0, 0, 0, 2, color='blue', arrow_length_ratio=0.1, alpha=0.7)
        
        # 添加坐标轴标签
        self.ax.text(2.2, 0, 0, 'X', color='red', fontsize=12, weight='bold')
        self.ax.text(0, 2.2, 0, 'Y', color='green', fontsize=12, weight='bold')
        self.ax.text(0, 0, 2.2, 'Z', color='blue', fontsize=12, weight='bold')
        
    def _connect_signals(self):
        """连接信号"""
        # 鼠标事件
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_move)
        self.canvas.mpl_connect('pick_event', self._on_pick)
        
    def _on_mouse_move(self, event):
        """鼠标移动事件"""
        # 检查是否在视图区域内
        if not self._is_mouse_in_view(event):
            self._update_coord_label_out_of_view()
            return
            
        if event.xdata is not None and event.ydata is not None:
            # 获取坐标并更新显示
            x, y, z = self._get_mouse_coordinates(event)
            self._update_coord_label(x, y, z)
            
            # 检查悬停信息
            self._check_hover_info(x, y, z)
            
    def _is_mouse_in_view(self, event) -> bool:
        """检查鼠标是否在3D视图区域内"""
        return event.inaxes == self.ax
        
    def _update_coord_label_out_of_view(self):
        """更新坐标标签为视图外状态"""
        self.coord_label.setText("坐标: 视图外")
        
    def _get_mouse_coordinates(self, event) -> Tuple[float, float, float]:
        """获取鼠标坐标"""
        # 获取最近的z值（简化处理，使用0）
        x, y, z = event.xdata, event.ydata, 0
        return x, y, z
        
    def _update_coord_label(self, x: float, y: float, z: float):
        """更新坐标标签"""
        self.coord_label.setText(f"坐标: ({x:.2f}, {y:.2f}, {z:.2f})")
            
    def _calculate_distance_to_node(self, node, x: float, y: float, z: float) -> float:
        """计算点到节点的距离"""
        return ((node.x - x)**2 + (node.y - y)**2 + (node.z - z)**2)**0.5
    
    def _check_hover_info(self, x: float, y: float, z: float):
        """检查悬停信息"""
        min_distance = float('inf')
        hover_info = ""
        
        # 检查最近的节点
        hover_info = self._find_closest_node(x, y, z, min_distance)
        
        # 检查最近的单元
        if not hover_info:
            hover_info = self._find_closest_element(x, y, z, min_distance)
                        
        if hover_info:
            self.status_label.setText(hover_info)
        else:
            self.status_label.setText("就绪")
            
    def _find_closest_node(self, x: float, y: float, z: float, min_distance: float) -> str:
        """查找最近的节点并返回悬停信息"""
        for node_id, node in self.nodes.items():
            if node.active:
                distance = self._calculate_distance_to_node(node, x, y, z)
                if distance < min_distance and distance < 0.5:  # 距离阈值
                    min_distance = distance
                    status = "激活" if node.active else "钝化"
                    selected = "选中" if node.selected else ""
                    return f"节点N{node_id} | 坐标:({node.x:.2f},{node.y:.2f},{node.z:.2f}) | {status} {selected}"
        return ""
        
    def _find_closest_element(self, x: float, y: float, z: float, min_distance: float) -> str:
        """查找最近的单元并返回悬停信息"""
        for element_id, element in self.elements.items():
            if element.active:
                node_i = self.nodes.get(element.node_i)
                node_j = self.nodes.get(element.node_j)
                
                if node_i and node_j:
                    # 计算点到线段的最短距离（简化处理）
                    distance_to_line = self._distance_to_line(x, y, z, 
                                                            node_i.x, node_i.y, node_i.z,
                                                            node_j.x, node_j.y, node_j.z)
                    if distance_to_line < min_distance and distance_to_line < 0.3:
                        min_distance = distance_to_line
                        status = "激活" if element.active else "钝化"
                        selected = "选中" if element.selected else ""
                        return f"单元E{element_id} | 类型:{element.type} | 节点{element.node_i}-{element.node_j} | {status} {selected}"
        return ""
            
    def _distance_to_line(self, px: float, py: float, pz: float, 
                         x1: float, y1: float, z1: float,
                         x2: float, y2: float, z2: float) -> float:
        """计算点到线段的最短距离"""
        # 向量计算
        dx = x2 - x1
        dy = y2 - y1  
        dz = z2 - z1
        
        if dx == dy == dz == 0:
            return ((px - x1)**2 + (py - y1)**2 + (pz - z1)**2)**0.5
            
        # 参数t
        t = ((px - x1)*dx + (py - y1)*dy + (pz - z1)*dz) / (dx*dx + dy*dy + dz*dz)
        t = max(0, min(1, t))  # 限制在线段范围内
        
        # 最近点
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        proj_z = z1 + t * dz
        
        # 返回距离
        return ((px - proj_x)**2 + (py - proj_y)**2 + (pz - proj_z)**2)**0.5
            
    def _on_pick(self, event):
        """鼠标点击事件"""
        if event.name == 'pick_event':
            if hasattr(event, 'artist') and event.artist:
                # 检查是否点击了节点
                if event.artist in self.node_scatter.get_children():
                    self._handle_node_pick(event)
                # 检查是否点击了单元
                elif event.artist in self.element_lines:
                    self._handle_element_pick(event)
                    
    def _handle_node_pick(self, event):
        """处理节点点击事件"""
        ind = event.ind[0] if len(event.ind) > 0 else None
        if ind is not None and ind < len(self.nodes):
            node_id = list(self.nodes.keys())[ind]
            self._toggle_node_selection(node_id)
            
    def _handle_element_pick(self, event):
        """处理单元点击事件"""
        line_index = self.element_lines.index(event.artist)
        if line_index < len(self.elements):
            element_id = list(self.elements.keys())[line_index]
            self._toggle_element_selection(element_id)
                        
    def _toggle_nodes(self):
        """切换节点显示"""
        self.show_nodes = not self.show_nodes
        self.show_nodes_action.setChecked(self.show_nodes)
        self.refresh_view()
        
    def _toggle_elements(self):
        """切换单元显示"""
        self.show_elements = not self.show_elements
        self.show_elements_action.setChecked(self.show_elements)
        self.refresh_view()
        
    def _toggle_grid(self):
        """切换网格显示"""
        self.show_grid = not self.show_grid
        self.show_grid_action.setChecked(self.show_grid)
        self._update_grid_visibility()
        self.refresh_view()
        
    def _update_grid_visibility(self):
        """更新网格可见性"""
        if hasattr(self.ax, 'xaxis') and hasattr(self.ax, 'yaxis'):
            for line in self.ax.xaxis.get_gridlines() + self.ax.yaxis.get_gridlines():
                line.set_visible(self.show_grid)
            for line in self.ax.zaxis.get_gridlines():
                line.set_visible(self.show_grid)
                
    def _reset_view(self):
        """重置视图"""
        self.ax.view_init(elev=20, azim=45)
        self.canvas.draw()
        
    def _fit_view(self):
        """适应视图"""
        # 验证是否有节点数据
        if not self._validate_nodes_exist():
            return
            
        # 计算包围盒和中心点
        bbox = self._calculate_bounding_box()
        center, ranges = self._calculate_center_and_ranges(bbox)
        
        # 设置坐标轴限制
        self._set_axis_limits(center, ranges)
        
        # 刷新画布
        self.canvas.draw()
        
    def _validate_nodes_exist(self) -> bool:
        """验证是否存在节点"""
        return bool(self.nodes)
        
    def _calculate_bounding_box(self) -> Tuple[List[float], List[float], List[float]]:
        """计算节点包围盒"""
        xs = [node.x for node in self.nodes.values()]
        ys = [node.y for node in self.nodes.values()]  
        zs = [node.z for node in self.nodes.values()]
        return xs, ys, zs
        
    def _calculate_center_and_ranges(self, bbox: Tuple[List[float], List[float], List[float]]) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """计算中心点和范围"""
        xs, ys, zs = bbox
        
        # 计算中心点
        x_center = (max(xs) + min(xs)) / 2
        y_center = (max(ys) + min(ys)) / 2
        z_center = (max(zs) + min(zs)) / 2
        center = (x_center, y_center, z_center)
        
        # 计算各维度范围
        x_range = max(xs) - min(xs)
        y_range = max(ys) - min(ys)
        z_range = max(zs) - min(zs)
        ranges = (x_range, y_range, z_range)
        
        return center, ranges
        
    def _set_axis_limits(self, center: Tuple[float, float, float], ranges: Tuple[float, float, float]):
        """设置坐标轴范围"""
        x_center, y_center, z_center = center
        x_range, y_range, z_range = ranges
        
        # 确定最大范围（至少1.0以避免视图过小）
        max_range = max(x_range, y_range, z_range, 1.0)
        
        # 设置坐标轴限制
        half_range = max_range / 2
        self.ax.set_xlim(x_center - half_range, x_center + half_range)
        self.ax.set_ylim(y_center - half_range, y_center + half_range)
        self.ax.set_zlim(z_center - half_range, z_center + half_range)
        
    def _clear_selection(self):
        """清除选择"""
        self.selected_node_ids.clear()
        self.selected_element_ids.clear()
        for node in self.nodes.values():
            node.selected = False
        for element in self.elements.values():
            element.selected = False
        self._update_selection_info()
        self.refresh_view()
        
    def _toggle_node_selection(self, node_id: int):
        """切换节点选择状态"""
        if node_id in self.selected_node_ids:
            self.selected_node_ids.remove(node_id)
            if node_id in self.nodes:
                self.nodes[node_id].selected = False
        else:
            self.selected_node_ids.add(node_id)
            if node_id in self.nodes:
                self.nodes[node_id].selected = True
                
        self._update_selection_info()
        self.refresh_view()
        
    def _toggle_element_selection(self, element_id: int):
        """切换单元选择状态"""
        if element_id in self.selected_element_ids:
            self.selected_element_ids.remove(element_id)
            if element_id in self.elements:
                self.elements[element_id].selected = False
        else:
            self.selected_element_ids.add(element_id)
            if element_id in self.elements:
                self.elements[element_id].selected = True
                
        self._update_selection_info()
        self.refresh_view()
        
    def _update_selection_info(self):
        """更新选择信息显示"""
        self.selection_label.setText(f"选中: {len(self.selected_node_ids)}个节点, {len(self.selected_element_ids)}个单元")
        
    def add_node(self, x: float, y: float, z: float, node_id: Optional[int] = None, active: bool = True) -> int:
        """添加节点"""
        if node_id is None:
            node_id = self.next_node_id
            self.next_node_id += 1
            
        node = Node3D(node_id, x, y, z, active)
        self.nodes[node_id] = node
        
        # 发送信号
        self.view_changed.emit()
        
        return node_id
        
    def add_element(self, node_i: int, node_j: int, element_type: str = "Beam", element_id: Optional[int] = None, active: bool = True) -> int:
        """添加单元"""
        if node_i not in self.nodes or node_j not in self.nodes:
            return -1
            
        if element_id is None:
            element_id = self.next_element_id
            self.next_element_id += 1
            
        element = Element3D(element_id, node_i, node_j, element_type, active)
        self.elements[element_id] = element
        
        # 发送信号
        self.view_changed.emit()
        
        return element_id
        
    def remove_node(self, node_id: int) -> bool:
        """删除节点"""
        if node_id in self.nodes:
            # 删除相关单元
            to_remove = [eid for eid, elem in self.elements.items() 
                        if elem.node_i == node_id or elem.node_j == node_id]
            for eid in to_remove:
                del self.elements[eid]
                
            del self.nodes[node_id]
            self.selected_node_ids.discard(node_id)
            
            self.view_changed.emit()
            return True
        return False
        
    def remove_element(self, element_id: int) -> bool:
        """删除单元"""
        if element_id in self.elements:
            del self.elements[element_id]
            self.selected_element_ids.discard(element_id)
            
            self.view_changed.emit()
            return True
        return False
        
    def set_node_active(self, node_id: int, active: bool):
        """设置节点激活状态"""
        if node_id in self.nodes:
            self.nodes[node_id].active = active
            self.view_changed.emit()
            
    def set_element_active(self, element_id: int, active: bool):
        """设置单元激活状态"""
        if element_id in self.elements:
            self.elements[element_id].active = active
            self.view_changed.emit()
            
    def get_node_info(self, node_id: int) -> Optional[Dict]:
        """获取节点信息"""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            return {
                'id': node.id,
                'x': node.x,
                'y': node.y,
                'z': node.z,
                'active': node.active,
                'selected': node.selected
            }
        return None
        
    def get_element_info(self, element_id: int) -> Optional[Dict]:
        """获取单元信息"""
        if element_id in self.elements:
            element = self.elements[element_id]
            return {
                'id': element.id,
                'node_i': element.node_i,
                'node_j': element.node_j,
                'type': element.type,
                'active': element.active,
                'selected': element.selected,
                'color': element.color
            }
        return None
        
    def get_all_nodes(self) -> Dict[int, Dict]:
        """获取所有节点信息"""
        return {nid: self.get_node_info(nid) for nid in self.nodes}
        
    def get_all_elements(self) -> Dict[int, Dict]:
        """获取所有单元信息"""
        return {eid: self.get_element_info(eid) for eid in self.elements}
        
    def clear_all(self):
        """清空所有数据"""
        self.nodes.clear()
        self.elements.clear()
        self.selected_node_ids.clear()
        self.selected_element_ids.clear()
        self.next_node_id = 1
        self.next_element_id = 1
        self.view_changed.emit()
        
    def refresh_view(self):
        """刷新视图"""
        self._update_plot()
        self.canvas.draw()
        
    def _update_plot(self):
        """更新绘图"""
        # 清除现有绘图
        self._clear_plot()
        
        # 重新设置坐标轴
        self._setup_axis_properties()
        
        # 重新绘制坐标系
        self._draw_coordinate_system()
        
        # 绘制节点和单元
        self._draw_plot_elements()
        
        # 更新网格可见性
        self._update_grid_visibility()
        
    def _clear_plot(self):
        """清除现有绘图"""
        self.ax.clear()
        
    def _setup_axis_properties(self):
        """设置坐标轴属性"""
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y') 
        self.ax.set_zlabel('Z')
        self.ax.set_title('OpenSeesPy三维模型视图')
        self.ax.grid(True, alpha=0.3)
        
    def _draw_plot_elements(self):
        """绘制所有绘图元素"""
        # 绘制节点
        if self.show_nodes:
            self._draw_nodes()
            
        # 绘制单元
        if self.show_elements:
            self._draw_elements()
        
    def _prepare_node_data(self) -> tuple:
        """准备节点数据"""
        node_ids = []
        node_xs = []
        node_ys = []
        node_zs = []
        node_colors = []
        node_sizes = []
        
        for node_id, node in self.nodes.items():
            if node.active:  # 只显示激活的节点
                node_ids.append(node_id)
                node_xs.append(node.x)
                node_ys.append(node.y)
                node_zs.append(node.z)
                
                # 节点颜色和大小
                if node.selected:
                    node_colors.append('red')
                    node_sizes.append(150)  # 选中节点更大
                else:
                    node_colors.append('blue')
                    node_sizes.append(80)
                    
        return node_ids, node_xs, node_ys, node_zs, node_colors, node_sizes
    
    def _draw_nodes(self):
        """绘制节点"""
        if not self.nodes:
            return
            
        # 准备节点数据
        node_data = self._prepare_node_data()
        node_ids, node_xs, node_ys, node_zs, node_colors, node_sizes = node_data
                    
        if node_xs:
            # 绘制节点散点
            self.node_scatter = self.ax.scatter(node_xs, node_ys, node_zs, 
                                              c=node_colors, s=node_sizes, 
                                              alpha=0.8, picker=True)
            
            # 添加节点标签
            self._add_node_labels(node_ids, node_xs, node_ys, node_zs)
            
    def _add_node_labels(self, node_ids, node_xs, node_ys, node_zs):
        """添加节点标签"""
        for i, node_id in enumerate(node_ids):
            self.ax.text(node_xs[i], node_ys[i], node_zs[i], 
                       f'N{node_id}', fontsize=8, 
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7))
                           
    def _draw_elements(self):
        """绘制所有单元"""
        if not self.elements:
            return
            
        for element_id, element in self.elements.items():
            if element.active:  # 只显示激活的单元
                self._draw_single_element(element_id, element)
                
    def _draw_single_element(self, element_id: int, element: Element3D):
        """绘制单个单元"""
        # 获取节点位置
        node_i = self.nodes.get(element.node_i)
        node_j = self.nodes.get(element.node_j)
        
        if node_i and node_j:
            # 准备坐标数据
            x_coords, y_coords, z_coords = self._prepare_element_coords(node_i, node_j)
            
            # 获取样式参数
            color, linewidth = self._get_element_style(element)
            
            # 绘制单元线
            line = self._draw_element_line(x_coords, y_coords, z_coords, color, linewidth)
            self.element_lines.append(line)
            
            # 添加单元标签
            mid_x, mid_y, mid_z = self._calculate_element_center(node_i, node_j)
            self._add_element_label(element_id, mid_x, mid_y, mid_z)
            
    def _prepare_element_coords(self, node_i: Node3D, node_j: Node3D) -> Tuple[List[float], List[float], List[float]]:
        """准备单元坐标数据"""
        x_coords = [node_i.x, node_j.x]
        y_coords = [node_i.y, node_j.y]
        z_coords = [node_i.z, node_j.z]
        return x_coords, y_coords, z_coords
        
    def _get_element_style(self, element: Element3D) -> Tuple[str, int]:
        """获取单元样式参数"""
        color = element.color
        linewidth = 2  # 默认线宽
        
        if element.selected:
            color = 'red'
            linewidth = 4  # 选中状态使用更粗的线
            
        return color, linewidth
        
    def _draw_element_line(self, x_coords: List[float], y_coords: List[float], 
                          z_coords: List[float], color: str, linewidth: int):
        """绘制单元线"""
        return self.ax.plot(x_coords, y_coords, z_coords, 
                          color=color, linewidth=linewidth, 
                          picker=True)[0]
                          
    def _calculate_element_center(self, node_i: Node3D, node_j: Node3D) -> Tuple[float, float, float]:
        """计算单元中心点"""
        mid_x = (node_i.x + node_j.x) / 2
        mid_y = (node_i.y + node_j.y) / 2
        mid_z = (node_i.z + node_j.z) / 2
        return mid_x, mid_y, mid_z
        
    def _add_element_label(self, element_id: int, x: float, y: float, z: float):
        """添加单元标签"""
        self.ax.text(x, y, z, 
                   f'E{element_id}', fontsize=8,
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.7))
                               
    def set_status(self, message: str):
        """设置状态信息"""
        self.status_label.setText(message)
        
    def update_from_controller(self, controller: OpenSeesPyController):
        """从控制器更新模型数据"""
        # 清除现有数据
        self.clear_all()
        
        # 添加节点数据
        self._import_nodes_from_controller(controller)
        
        # 添加单元数据
        self._import_elements_from_controller(controller)
        
        # 刷新视图并更新状态
        self._finalize_controller_update()
        
    def _import_nodes_from_controller(self, controller: OpenSeesPyController):
        """从控制器导入节点数据"""
        nodes = controller.get_all_nodes()
        for node in nodes:
            self.add_node(
                x=node.x,
                y=node.y,
                z=node.z,
                node_id=node.id,
                active=True  # 默认激活状态
            )
            
    def _import_elements_from_controller(self, controller: OpenSeesPyController):
        """从控制器导入单元数据"""
        elements = controller.get_all_elements()
        for element in elements:
            if self._validate_element_for_import(element):
                self._add_element_from_controller(element)
                
    def _validate_element_for_import(self, element) -> bool:
        """验证单元是否可以导入"""
        return len(element.node_ids) >= 2  # 确保至少有两个节点
        
    def _add_element_from_controller(self, element):
        """从控制器添加单个单元"""
        self.add_element(
            node_i=element.node_ids[0],
            node_j=element.node_ids[1],
            element_type=element.type,
            element_id=element.id,
            active=True  # 默认激活状态
        )
        
    def _finalize_controller_update(self):
        """完成控制器更新"""
        self.refresh_view()
        self.set_status("已从控制器更新模型数据")
        
    def _get_element_type_colors(self) -> Dict[str, str]:
        """获取单元类型对应的颜色"""
        color_map = {
            'Beam': 'blue',
            'Column': 'red', 
            'Brace': 'green',
            'Shell': 'orange',
            'Solid': 'purple',
            'Link': 'cyan',
            'Spring': 'magenta'
        }
        return color_map
        
    def _assign_colors_by_type(self):
        """根据单元类型分配颜色"""
        color_map = self._get_element_type_colors()
        
        for element in self.elements.values():
            # 如果是已知类型，使用对应的颜色
            if element.type in color_map:
                element.color = color_map[element.type]
            else:
                # 未知类型使用随机颜色
                colors = ['brown', 'pink', 'gray', 'olive', 'teal', 'navy']
                element.color = random.choice(colors)