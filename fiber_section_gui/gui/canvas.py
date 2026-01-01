from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import mplcursors
import numpy as np

class Canvas(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        
        # 创建matplotlib画布
        self.figure = Figure()
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        
        # 创建导航工具栏
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # 布局
        layout = QVBoxLayout(self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 初始化绘图
        self._init_plot()
        
        # 连接信号
        self._connect_signals()
        
        # 跟踪当前选中的纤维ID列表
        self.current_selected_fiber_ids = []
    
    def _init_plot(self):
        # 设置坐标轴
        self.axes.set_aspect('equal')
        self.axes.grid(True)
        self.axes.set_xlabel('y')
        self.axes.set_ylabel('z')
        self.axes.set_title('纤维截面网格')
        
        # 添加实时坐标显示
        self.coord_text = self.axes.text(0.05, 0.95, '', transform=self.axes.transAxes, 
                                        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    def _connect_signals(self):
        # 鼠标移动事件，显示实时坐标
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_move)
        
        # 鼠标点击事件，用于选择纤维
        self.canvas.mpl_connect('button_press_event', self._on_mouse_click)
        
        # 连接数据管理器的纤维选中信号
        self.data_manager.fiber_selected.connect(self._on_fiber_selected)
    
    def _on_mouse_move(self, event):
        if event.inaxes:
            x, y = event.xdata, event.ydata
            self.coord_text.set_text(f'坐标: ({x:.3f}, {y:.3f})')
            self.canvas.draw_idle()
    
    def _on_mouse_click(self, event):
        if event.inaxes:
            x, y = event.xdata, event.ydata
            
            # 检查是否点击了纤维
            current_section = self.data_manager.get_current_section()
            fibers = []
            
            if current_section.mesh and current_section.mesh.fibers:
                fibers = current_section.mesh.fibers
            elif current_section.fibers:
                fibers = current_section.fibers
                
            if fibers:
                # 找到最近的纤维
                closest_fiber = None
                min_distance = float('inf')
                
                for fiber in fibers:
                    distance = np.sqrt((fiber.y - x)**2 + (fiber.z - y)**2)
                    if distance < min_distance:
                        min_distance = distance
                        closest_fiber = fiber
                
                if closest_fiber and min_distance < 0.1:  # 设置点击阈值
                    # 切换选中状态
                    if closest_fiber.id in self.current_selected_fiber_ids:
                        # 取消选中
                        self.current_selected_fiber_ids.remove(closest_fiber.id)
                        if not self.current_selected_fiber_ids:
                            self._clear_highlight()
                            # 通知数据管理器取消选中
                            self.data_manager.fiber_selected.emit(None)
                        else:
                            # 高亮剩余选中的纤维
                            selected_fibers = [fiber for fiber in fibers if fiber.id in self.current_selected_fiber_ids]
                            self._highlight_fiber(selected_fibers)
                    else:
                        # 选中新纤维
                        self.current_selected_fiber_ids.append(closest_fiber.id)
                        # 高亮选中的纤维
                        selected_fibers = [fiber for fiber in fibers if fiber.id in self.current_selected_fiber_ids]
                        self._highlight_fiber(selected_fibers)
                        # 通知数据管理器纤维被选中
                        self.data_manager.fiber_selected.emit(closest_fiber.id)
    
    def _clear_highlight(self):
        # 清除所有高亮
        collections_to_remove = []
        for scatter in self.axes.collections:
            if hasattr(scatter, 'is_highlight') and scatter.is_highlight:
                collections_to_remove.append(scatter)
        
        for scatter in collections_to_remove:
            scatter.remove()
        
        self.canvas.draw_idle()
    
    def _highlight_fiber(self, fibers):
        # 清除之前的高亮
        self._clear_highlight()
        
        # 绘制高亮圆
        for fiber in fibers:
            highlight = self.axes.scatter(fiber.y, fiber.z, s=100, facecolor='none', edgecolor='red', linewidth=2)
            highlight.is_highlight = True
        self.canvas.draw_idle()
    
    def _on_fiber_selected(self, fiber_ids):
        """处理纤维选中信号，在视图中高亮显示对应的纤维"""
        if fiber_ids is None or not fiber_ids:
            # 取消选中
            self._clear_highlight()
            self.current_selected_fiber_ids = []
        else:
            # 确保fiber_ids是一个列表
            if not isinstance(fiber_ids, list):
                fiber_ids = [fiber_ids]
            
            self.current_selected_fiber_ids = fiber_ids
            current_section = self.data_manager.get_current_section()
            fibers_to_highlight = []
            
            if current_section and current_section.mesh and current_section.mesh.fibers:
                # 找到对应的纤维
                for fiber in current_section.mesh.fibers:
                    if fiber.id in fiber_ids:
                        fibers_to_highlight.append(fiber)
            elif current_section and current_section.fibers:
                # 兼容旧的纤维存储方式
                for fiber in current_section.fibers:
                    if fiber.id in fiber_ids:
                        fibers_to_highlight.append(fiber)
            
            if fibers_to_highlight:
                self._highlight_fiber(fibers_to_highlight)
    
    def draw_shapes(self, shapes, immediate=False):
        # 清除之前的形状
        # 遍历所有补丁，移除标记为形状的补丁
        patches_to_remove = []
        for patch in self.axes.patches:
            if hasattr(patch, 'is_shape') and patch.is_shape:
                patches_to_remove.append(patch)
        
        # 使用补丁对象的remove方法将其从轴中移除
        for patch in patches_to_remove:
            patch.remove()
        
        # 绘制新形状
        for shape in shapes:
            if shape.is_active:
                patch = shape.draw(self.axes)
                patch.is_shape = True
        
        # 立即刷新或延迟刷新
        if immediate:
            self.canvas.draw()
        else:
            self.canvas.draw_idle()
    
    def draw_mesh(self, mesh, active_shapes=None, immediate=False):
        # 清除之前的网格
        lines_to_remove = []
        for line in self.axes.lines:
            if hasattr(line, 'is_mesh') and line.is_mesh:
                lines_to_remove.append(line)
        
        # 使用线对象的remove方法将其从轴中移除
        for line in lines_to_remove:
            line.remove()
        
        # 如果没有纤维或没有激活的纤维，不绘制网格
        if not mesh.fibers:
            if immediate:
                self.canvas.draw()
            else:
                self.canvas.draw_idle()
            return
        
        # 收集所有激活纤维对应的单元ID
        active_element_ids = set()
        
        # 如果提供了激活形状列表，只考虑与这些形状相关的纤维
        if active_shapes:
            for fiber in mesh.fibers:
                if fiber.active:
                    # 检查纤维是否在激活形状内
                    point = (fiber.y, fiber.z)
                    in_active_shape = False
                    for shape in active_shapes:
                        if shape.is_point_inside(point):
                            in_active_shape = True
                            break
                    if in_active_shape:
                        # 假设纤维索引与单元索引一致（纤维ID-1 = 单元索引）
                        active_element_ids.add(fiber.id - 1)
        else:
            # 如果没有提供形状列表，只使用激活的纤维
            for fiber in mesh.fibers:
                if fiber.active:
                    active_element_ids.add(fiber.id - 1)
        
        # 绘制激活的网格元素
        for i, element in enumerate(mesh.elements):
            if i in active_element_ids:
                # 获取单元节点坐标
                vertices = [mesh.nodes[node_idx] for node_idx in element]
                x = [v[0] for v in vertices]
                y = [v[1] for v in vertices]
                
                # 根据节点数量判断单元类型并绘制
                if len(element) == 3:
                    # 三角形单元
                    line, = self.axes.plot(x + [x[0]], y + [y[0]], 'k-', linewidth=0.5)
                    line.is_mesh = True
                elif len(element) == 4:
                    # 四边形单元
                    # 添加最后一个点到第一个点形成闭合四边形
                    line, = self.axes.plot(x + [x[0]], y + [y[0]], 'k-', linewidth=0.5)
                    line.is_mesh = True
                else:
                    # 其他类型的单元（理论上不应该出现）
                    line, = self.axes.plot(x + [x[0]], y + [y[0]], 'r-', linewidth=0.5)
                    line.is_mesh = True
                    print(f"警告：发现未知类型的单元，包含{len(element)}个节点")
        
        # 立即刷新或延迟刷新
        if immediate:
            self.canvas.draw()
        else:
            self.canvas.draw_idle()
    
    def draw_fibers(self, fibers, immediate=False):
        # 清除之前的纤维
        collections_to_remove = []
        for scatter in self.axes.collections:
            if hasattr(scatter, 'is_fiber') and scatter.is_fiber:
                collections_to_remove.append(scatter)
        
        # 使用集合对象的remove方法将其从轴中移除
        for scatter in collections_to_remove:
            scatter.remove()
        
        # 按材料分组纤维（只包括激活的纤维）
        material_fibers = {}
        for fiber in fibers:
            if fiber.active:  # 只绘制激活的纤维
                if fiber.material_id not in material_fibers:
                    material_fibers[fiber.material_id] = []
                material_fibers[fiber.material_id].append(fiber)
        
        # 获取材料颜色
        material_library = self.data_manager.material_library
        
        # 绘制纤维
        for material_id, fiber_list in material_fibers.items():
            material = material_library.get_material_by_id(material_id)
            color = material.color if material else 'gray'
            
            y = [fiber.y for fiber in fiber_list]
            z = [fiber.z for fiber in fiber_list]
            
            scatter = self.axes.scatter(y, z, s=10, c=color, alpha=0.8)
            scatter.is_fiber = True
        
        # 添加纤维悬停提示
        cursor = mplcursors.cursor(self.axes.collections[-len(material_fibers):], hover=True)
        
        # 创建纤维索引映射
        fiber_map = {}
        collection_idx = 0
        for material_id, fiber_list in material_fibers.items():
            for fiber_idx, fiber in enumerate(fiber_list):
                fiber_map[(collection_idx, fiber_idx)] = fiber
            collection_idx += 1
        
        @cursor.connect("add")
        def on_add(sel):
            coll_idx = list(self.axes.collections).index(sel.artist)
            # 找到这个集合在material_fibers中的索引
            material_idx = coll_idx - (len(self.axes.collections) - len(material_fibers))
            if material_idx >= 0 and material_idx < len(material_fibers):
                fiber_idx = sel.index
                if (material_idx, fiber_idx) in fiber_map:
                    fiber = fiber_map[(material_idx, fiber_idx)]
                    sel.annotation.set_text(f'纤维 ID: {fiber.id}\n坐标: ({fiber.y:.3f}, {fiber.z:.3f})\n面积: {fiber.area:.6f}\n材料: {fiber.material_id}')
        
        # 立即刷新或延迟刷新
        if immediate:
            self.canvas.draw()
        else:
            self.canvas.draw_idle()
    
    def reset_view(self):
        self.axes.relim()
        self.axes.autoscale_view()
        self.canvas.draw_idle()
    
    def zoom_in(self):
        # 放大视图
        current_xlim = self.axes.get_xlim()
        current_ylim = self.axes.get_ylim()
        
        # 计算新的范围（放大2倍）
        new_xlim = [
            current_xlim[0] + (current_xlim[1] - current_xlim[0]) * 0.25,
            current_xlim[1] - (current_xlim[1] - current_xlim[0]) * 0.25
        ]
        new_ylim = [
            current_ylim[0] + (current_ylim[1] - current_ylim[0]) * 0.25,
            current_ylim[1] - (current_ylim[1] - current_ylim[0]) * 0.25
        ]
        
        self.axes.set_xlim(new_xlim)
        self.axes.set_ylim(new_ylim)
        self.canvas.draw_idle()
    
    def zoom_out(self):
        # 缩小视图
        current_xlim = self.axes.get_xlim()
        current_ylim = self.axes.get_ylim()
        
        # 计算新的范围（缩小2倍）
        new_xlim = [
            current_xlim[0] - (current_xlim[1] - current_xlim[0]) * 0.5,
            current_xlim[1] + (current_xlim[1] - current_xlim[0]) * 0.5
        ]
        new_ylim = [
            current_ylim[0] - (current_ylim[1] - current_ylim[0]) * 0.5,
            current_ylim[1] + (current_ylim[1] - current_ylim[0]) * 0.5
        ]
        
        self.axes.set_xlim(new_xlim)
        self.axes.set_ylim(new_ylim)
        self.canvas.draw_idle()
    
    def enable_pan(self):
        # 启用平移模式
        self.toolbar.pan()
        self.canvas.draw_idle()
    
    def clear(self):
        """清除画布上的所有内容"""
        # 清除所有形状
        patches_to_remove = []
        for patch in self.axes.patches:
            if hasattr(patch, 'is_shape') and patch.is_shape:
                patches_to_remove.append(patch)
        
        for patch in patches_to_remove:
            patch.remove()
        
        # 清除所有网格和高亮
        lines_to_remove = []
        for line in self.axes.lines:
            if hasattr(line, 'is_mesh') or hasattr(line, 'is_highlight'):
                lines_to_remove.append(line)
        
        for line in lines_to_remove:
            line.remove()
        
        # 清除所有纤维
        collections_to_remove = []
        for scatter in self.axes.collections:
            if hasattr(scatter, 'is_fiber') and scatter.is_fiber:
                collections_to_remove.append(scatter)
        
        for scatter in collections_to_remove:
            scatter.remove()
        
        self.canvas.draw_idle()
