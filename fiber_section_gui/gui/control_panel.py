from PyQt5.QtWidgets import (QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QLineEdit, QPushButton, QComboBox, QDoubleSpinBox,
                             QListWidget, QListWidgetItem, QCheckBox, QSpinBox, QMenu,
                             QInputDialog, QMessageBox, QDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

class ControlPanel(QWidget):
    # 定义信号
    section_switched = pyqtSignal()
    shapes_updated = pyqtSignal()
    canvas_refresh = pyqtSignal()  # 新增画布刷新信号
    fiber_list_refresh = pyqtSignal()  # 新增纤维列表刷新信号
    shape_list_refresh = pyqtSignal()  # 新增形状列表刷新信号
    
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        
        # 创建标签页
        self.tabs = QTabWidget()
        
        # 创建各个标签页
        self.geometry_tab = GeometryTab(data_manager)
        self.mesh_tab = MeshTab(data_manager)
        self.material_tab = MaterialTab(data_manager)
        self.section_tab = SectionTab(data_manager, self)
        self.history_tab = HistoryTab(data_manager)
        self.shape_fiber_tab = ShapeFiberTab(data_manager, self)
        
        # 添加标签页
        self.tabs.addTab(self.geometry_tab, "几何形状")
        self.tabs.addTab(self.mesh_tab, "网格参数")
        self.tabs.addTab(self.material_tab, "材料属性")
        self.tabs.addTab(self.section_tab, "截面设置")
        self.tabs.addTab(self.shape_fiber_tab, "形状/纤维管理")
        self.tabs.addTab(self.history_tab, "操作历史")
        
        # 创建底部按钮
        self.btn_add_shape = QPushButton("添加形状")
        self.btn_generate_mesh = QPushButton("生成网格")
        self.btn_export_section = QPushButton("导出截面")
        
        # 创建网格类型选择
        self.mesh_type_selector = QComboBox()
        self.mesh_type_selector.addItems(["三角形网格", "四边形网格"])
        self.mesh_type_selector.setCurrentText("三角形网格")
        self.mesh_type_selector.setToolTip("选择生成网格的类型")
        
        # 创建网格尺寸输入
        self.mesh_size_input = QDoubleSpinBox()
        self.mesh_size_input.setValue(0.1)
        self.mesh_size_input.setMinimum(0.01)
        self.mesh_size_input.setMaximum(10.0)
        self.mesh_size_input.setDecimals(3)
        self.mesh_size_input.setToolTip("设置全局网格尺寸")
        
        # 布局
        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)
        
        # 底部按钮和网格参数布局
        button_layout = QHBoxLayout()
        
        # 左侧：形状和导出按钮
        left_layout = QHBoxLayout()
        left_layout.addWidget(self.btn_add_shape)
        left_layout.addWidget(self.btn_export_section)
        
        # 中间：网格生成按钮
        center_layout = QHBoxLayout()
        center_layout.addWidget(self.btn_generate_mesh)
        
        # 右侧：网格参数
        right_layout = QHBoxLayout()
        right_layout.addWidget(QLabel("网格类型:"))
        right_layout.addWidget(self.mesh_type_selector)
        right_layout.addWidget(QLabel("网格尺寸:"))
        right_layout.addWidget(self.mesh_size_input)
        
        # 添加间距
        left_layout.addStretch()
        right_layout.addStretch()
        
        button_layout.addLayout(left_layout)
        button_layout.addLayout(center_layout)
        button_layout.addLayout(right_layout)
        
        layout.addLayout(button_layout)
        layout.setContentsMargins(5, 5, 5, 5)

class GeometryTab(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        
        # 创建形状选择下拉框
        self.shape_type = QComboBox()
        self.shape_type.addItems(["矩形", "圆形", "环形", "多边形"])
        
        # 创建参数输入区域
        self.params_group = QGroupBox("形状参数")
        self.params_group.setLayout(QVBoxLayout())  # 先设置空布局
        
        # 根据形状类型显示不同的参数输入
        self.shape_type.currentTextChanged.connect(self._update_params_group)
        
        # 布局
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("形状类型:"))
        layout.addWidget(self.shape_type)
        layout.addWidget(self.params_group)
        
        # 初始化参数输入
        self._update_params_group()
    
    def _update_params_group(self):
        # 清除当前参数组内容
        layout = self.params_group.layout()
        
        # 清除所有子控件
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            if child.layout():
                self._clear_layout(child.layout())
        
        # 根据形状类型创建参数输入
        shape_type = self.shape_type.currentText()
        
        if shape_type == "矩形":
            self._create_rectangle_params()
        elif shape_type == "圆形":
            self._create_circle_params()
        elif shape_type == "环形":
            self._create_ring_params()
        elif shape_type == "多边形":
            self._create_polygon_params()
    
    def _clear_layout(self, layout):
        """递归清除布局中的所有控件"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            if child.layout():
                self._clear_layout(child.layout())
    
    def _create_rectangle_params(self):
        layout = self.params_group.layout()
        
        # 中心坐标
        coord_layout = QHBoxLayout()
        coord_layout.addWidget(QLabel("中心 y:"))
        self.center_y = QDoubleSpinBox()
        self.center_y.setValue(0.0)
        coord_layout.addWidget(self.center_y)
        
        coord_layout.addWidget(QLabel("中心 z:"))
        self.center_z = QDoubleSpinBox()
        self.center_z.setValue(0.0)
        coord_layout.addWidget(self.center_z)
        layout.addLayout(coord_layout)
        
        # 宽高
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("宽度:"))
        self.width = QDoubleSpinBox()
        self.width.setValue(1.0)
        self.width.setMinimum(0.1)
        size_layout.addWidget(self.width)
        
        size_layout.addWidget(QLabel("高度:"))
        self.height = QDoubleSpinBox()
        self.height.setValue(1.0)
        self.height.setMinimum(0.1)
        size_layout.addWidget(self.height)
        layout.addLayout(size_layout)
        
        # 旋转角度
        layout.addWidget(QLabel("旋转角度:"))
        self.rotation = QDoubleSpinBox()
        self.rotation.setValue(0.0)
        self.rotation.setRange(0.0, 360.0)
        layout.addWidget(self.rotation)
    
    def _create_circle_params(self):
        layout = self.params_group.layout()
        
        # 圆心坐标
        coord_layout = QHBoxLayout()
        coord_layout.addWidget(QLabel("圆心 y:"))
        self.circle_center_y = QDoubleSpinBox()
        self.circle_center_y.setValue(0.0)
        coord_layout.addWidget(self.circle_center_y)
        
        coord_layout.addWidget(QLabel("圆心 z:"))
        self.circle_center_z = QDoubleSpinBox()
        self.circle_center_z.setValue(0.0)
        coord_layout.addWidget(self.circle_center_z)
        layout.addLayout(coord_layout)
        
        # 半径
        layout.addWidget(QLabel("半径:"))
        self.circle_radius = QDoubleSpinBox()
        self.circle_radius.setValue(0.5)
        self.circle_radius.setMinimum(0.1)
        layout.addWidget(self.circle_radius)
    
    def _create_ring_params(self):
        layout = self.params_group.layout()
        
        # 圆心坐标
        coord_layout = QHBoxLayout()
        coord_layout.addWidget(QLabel("圆心 y:"))
        self.ring_center_y = QDoubleSpinBox()
        self.ring_center_y.setValue(0.0)
        coord_layout.addWidget(self.ring_center_y)
        
        coord_layout.addWidget(QLabel("圆心 z:"))
        self.ring_center_z = QDoubleSpinBox()
        self.ring_center_z.setValue(0.0)
        coord_layout.addWidget(self.ring_center_z)
        layout.addLayout(coord_layout)
        
        # 半径
        radius_layout = QHBoxLayout()
        radius_layout.addWidget(QLabel("内径:"))
        self.ring_inner_radius = QDoubleSpinBox()
        self.ring_inner_radius.setValue(0.3)
        self.ring_inner_radius.setMinimum(0.1)
        radius_layout.addWidget(self.ring_inner_radius)
        
        radius_layout.addWidget(QLabel("外径:"))
        self.ring_outer_radius = QDoubleSpinBox()
        self.ring_outer_radius.setValue(0.5)
        self.ring_outer_radius.setMinimum(0.2)
        radius_layout.addWidget(self.ring_outer_radius)
        layout.addLayout(radius_layout)
    
    def _create_polygon_params(self):
        layout = self.params_group.layout()
        
        # 顶点坐标输入
        layout.addWidget(QLabel("顶点坐标 (y,z 格式，用分号分隔):"))
        self.vertices = QLineEdit()
        self.vertices.setPlaceholderText("例如: 0,0; 1,0; 1,1; 0,1")
        layout.addWidget(self.vertices)
    
    def get_shape_params(self):
        shape_type = self.shape_type.currentText()
        params = {}
        
        if shape_type == "矩形":
            params = {
                "center_y": self.center_y.value(),
                "center_z": self.center_z.value(),
                "width": self.width.value(),
                "height": self.height.value(),
                "rotation": self.rotation.value()
            }
        elif shape_type == "圆形":
            params = {
                "center_y": self.circle_center_y.value(),
                "center_z": self.circle_center_z.value(),
                "radius": self.circle_radius.value()
            }
        elif shape_type == "环形":
            params = {
                "center_y": self.ring_center_y.value(),
                "center_z": self.ring_center_z.value(),
                "inner_radius": self.ring_inner_radius.value(),
                "outer_radius": self.ring_outer_radius.value()
            }
        elif shape_type == "多边形":
            vertices_text = self.vertices.text()
            vertices = []
            if vertices_text:
                for vertex_str in vertices_text.split(';'):
                    vertex = vertex_str.strip().split(',')
                    if len(vertex) == 2:
                        try:
                            y = float(vertex[0].strip())
                            z = float(vertex[1].strip())
                            vertices.append((y, z))
                        except ValueError:
                            pass
            
            # 确保至少有3个顶点来形成多边形
            if len(vertices) < 3:
                vertices = [(0, 0), (1, 0), (1, 1), (0, 1)]  # 默认矩形
            
            params = {
                "vertices": vertices
            }
        
        return params

class MeshTab(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        
        # 创建网格参数输入
        self.global_mesh_size = QDoubleSpinBox()
        self.global_mesh_size.setValue(0.1)
        self.global_mesh_size.setMinimum(0.01)
        
        # 创建网格类型选择
        self.mesh_type = QComboBox()
        self.mesh_type.addItems(["三角形网格", "四边形网格"])
        self.mesh_type.setCurrentText("三角形网格")  # 默认选择三角形网格
        
        # 布局
        layout = QVBoxLayout(self)
        
        # 网格类型选择
        layout.addWidget(QLabel("网格类型:"))
        layout.addWidget(self.mesh_type)
        layout.addWidget(QLabel("选择要生成的网格类型"))
        
        layout.addWidget(QLabel("全局网格尺寸:"))
        layout.addWidget(self.global_mesh_size)
        layout.addWidget(QLabel("网格越小，划分越细，但计算时间越长"))

class MaterialTab(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        
        # 创建材料列表
        self.material_list = QListWidget()
        
        # 创建材料属性输入
        self.material_id = QSpinBox()
        self.material_id.setValue(1)
        self.material_id.setMinimum(1)
        
        self.material_name = QLineEdit("默认材料")
        
        self.elastic_modulus = QDoubleSpinBox()
        self.elastic_modulus.setValue(1.0)
        self.elastic_modulus.setMinimum(0.01)
        
        self.color = QLineEdit("#FF0000")
        
        # 创建按钮
        self.btn_add_material = QPushButton("添加材料")
        self.btn_edit_material = QPushButton("编辑材料")
        self.btn_delete_material = QPushButton("删除材料")
        
        # 布局
        layout = QVBoxLayout(self)
        
        # 材料列表
        layout.addWidget(QLabel("材料库:"))
        layout.addWidget(self.material_list)
        
        # 材料属性
        props_group = QGroupBox("材料属性")
        props_layout = QVBoxLayout(props_group)
        
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("材料ID:"))
        id_layout.addWidget(self.material_id)
        props_layout.addLayout(id_layout)
        
        props_layout.addWidget(QLabel("材料名称:"))
        props_layout.addWidget(self.material_name)
        
        props_layout.addWidget(QLabel("弹性模量:"))
        props_layout.addWidget(self.elastic_modulus)
        
        props_layout.addWidget(QLabel("颜色 (HEX):"))
        props_layout.addWidget(self.color)
        
        layout.addWidget(props_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_add_material)
        button_layout.addWidget(self.btn_edit_material)
        button_layout.addWidget(self.btn_delete_material)
        layout.addLayout(button_layout)
        
        # 连接信号
        self.btn_add_material.clicked.connect(self._on_add_material)
        self.btn_edit_material.clicked.connect(self._on_edit_material)
        self.btn_delete_material.clicked.connect(self._on_delete_material)
        
        # 初始化材料列表
        self._update_material_list()
    
    def _update_material_list(self):
        self.material_list.clear()
        material_library = self.data_manager.material_library
        
        for material in material_library.materials:
            item = QListWidgetItem(f"ID: {material.id} - {material.name} (颜色: {material.color})")
            item.setData(Qt.UserRole, material.id)
            self.material_list.addItem(item)
    
    def _on_add_material(self):
        material_id = self.material_id.value()
        name = self.material_name.text()
        elastic_modulus = self.elastic_modulus.value()
        color = self.color.text()
        
        material_library = self.data_manager.material_library
        material_library.add_material(material_id, name, elastic_modulus, color)
        
        self._update_material_list()
    
    def _on_edit_material(self):
        selected_item = self.material_list.currentItem()
        if not selected_item:
            return
        
        material_id = selected_item.data(Qt.UserRole)
        name = self.material_name.text()
        elastic_modulus = self.elastic_modulus.value()
        color = self.color.text()
        
        material_library = self.data_manager.material_library
        material_library.update_material(material_id, name, elastic_modulus, color)
        
        self._update_material_list()
    
    def _on_delete_material(self):
        selected_item = self.material_list.currentItem()
        if not selected_item:
            return
        
        material_id = selected_item.data(Qt.UserRole)
        
        material_library = self.data_manager.material_library
        material_library.delete_material(material_id)
        
        self._update_material_list()

class SectionTab(QWidget):
    def __init__(self, data_manager, control_panel):
        super().__init__()
        self.data_manager = data_manager
        self.control_panel = control_panel
        
        # 创建截面设置
        self.section_id = QSpinBox()
        self.section_id.setValue(1)
        self.section_id.setMinimum(1)
        
        self.GJ = QDoubleSpinBox()
        self.GJ.setValue(1.0)
        self.GJ.setMinimum(0.01)
        self.GJ.setDecimals(4)  # 增加小数位数
        self.GJ.setRange(0.0, 1000000.0)  # 增加范围上限
        
        # 创建截面列表
        self.section_list = QListWidget()
        
        # 创建按钮
        self.btn_add_section = QPushButton("添加截面")
        self.btn_switch_section = QPushButton("切换截面")
        self.btn_calc_gj = QPushButton("计算扭转刚度")  # 新增计算扭转刚度按钮
        
        # 布局
        layout = QVBoxLayout(self)
        
        # 截面列表
        layout.addWidget(QLabel("截面列表:"))
        layout.addWidget(self.section_list)
        
        # 截面设置
        settings_group = QGroupBox("截面设置")
        settings_layout = QVBoxLayout(settings_group)
        
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("截面ID:"))
        id_layout.addWidget(self.section_id)
        settings_layout.addLayout(id_layout)
        
        settings_layout.addWidget(QLabel("扭转刚度 GJ:"))
        gj_layout = QHBoxLayout()
        gj_layout.addWidget(self.GJ)
        gj_layout.addWidget(self.btn_calc_gj)
        settings_layout.addLayout(gj_layout)
        
        layout.addWidget(settings_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_add_section)
        button_layout.addWidget(self.btn_switch_section)
        layout.addLayout(button_layout)
        
        # 连接信号
        self.btn_add_section.clicked.connect(self._on_add_section)
        self.btn_switch_section.clicked.connect(self._on_switch_section)
        self.btn_calc_gj.clicked.connect(self._on_calc_gj)  # 连接计算扭转刚度按钮
        
        # 初始化截面列表
        self._update_section_list()
    
    def _update_section_list(self):
        self.section_list.clear()
        sections = self.data_manager.get_sections()
        
        for section in sections:
            item = QListWidgetItem(f"截面 {section.id}: {section.name}")
            item.setData(Qt.UserRole, section.id)
            self.section_list.addItem(item)
    
    def _on_add_section(self):
        section_name = f"截面 {self.section_id.value()}"
        self.data_manager.create_section(section_name)
        self._update_section_list()
    
    def _on_switch_section(self):
        # 先保存当前截面的GJ值
        self._save_gj_value()
        
        selected_item = self.section_list.currentItem()
        if not selected_item:
            return
        
        section_id = selected_item.data(Qt.UserRole)
        self.data_manager.set_current_section(section_id)
        
        # 更新GJ显示值
        current_section = self.data_manager.get_current_section()
        if current_section:
            self.GJ.setValue(current_section.GJ)
        
        # 发出截面切换信号
        self.control_panel.section_switched.emit()
    
    def _save_gj_value(self):
        """保存当前截面的GJ值"""
        current_section = self.data_manager.get_current_section()
        if current_section:
            current_section.GJ = self.GJ.value()
    
    def _on_calc_gj(self):
        """计算当前截面的扭转刚度"""
        current_section = self.data_manager.get_current_section()
        if current_section:
            # 获取激活的形状
            active_shapes = current_section.get_active_shapes()
            if not active_shapes:
                QMessageBox.warning(self, "警告", "没有激活的形状，无法计算扭转刚度")
                return
            
            # 计算扭转刚度
            gj_value = self._calculate_gj(active_shapes)
            if gj_value > 0:
                self.GJ.setValue(gj_value)
                self._save_gj_value()
                QMessageBox.information(self, "成功", f"扭转刚度已自动计算: {gj_value:.4f}")
            else:
                QMessageBox.warning(self, "警告", "计算扭转刚度失败")
    
    def _calculate_gj(self, shapes):
        """计算扭转刚度
        对于简单截面，GJ = G * J，其中G是剪切模量，J是扭转常数
        这里使用简化的计算方法
        """
        import numpy as np
        
        # 对于矩形截面，扭转常数J = k * a * b³，其中a和b是矩形边长，k取决于a/b
        # 这里简化为取最大外接矩形的面积
        
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



    def _update_fiber_display(self):
        """更新纤维列表显示 - 委托给_update_fiber_list方法"""
        self._update_fiber_list()

class HistoryTab(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        
        # 创建操作历史列表
        self.history_list = QListWidget()
        
        # 创建按钮
        self.btn_undo = QPushButton("撤销")
        self.btn_redo = QPushButton("重做")
        
        # 布局
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("操作历史:"))
        layout.addWidget(self.history_list)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_undo)
        button_layout.addWidget(self.btn_redo)
        layout.addLayout(button_layout)
        
        # 连接信号
        self.btn_undo.clicked.connect(self._on_undo)
        self.btn_redo.clicked.connect(self._on_redo)
        self.data_manager.history_changed.connect(self._update_history_list)
        
        # 初始化历史列表
        self._update_history_list()
    
    def _on_undo(self):
        self.data_manager.undo()
    
    def _on_redo(self):
        self.data_manager.redo()
    
    def _update_history_list(self):
        """更新操作历史列表"""
        self.history_list.clear()
        
        # 添加撤销栈
        for i, operation in enumerate(reversed(self.data_manager.undo_stack)):
            item = QListWidgetItem(f"撤销 #{i+1}: {operation.description} ({operation.timestamp.strftime('%H:%M:%S')})")
            self.history_list.addItem(item)
        
        # 添加重做栈
        for i, operation in enumerate(reversed(self.data_manager.redo_stack)):
            item = QListWidgetItem(f"重做 #{i+1}: {operation.description} ({operation.timestamp.strftime('%H:%M:%S')})")
            item.setForeground(Qt.gray)
            self.history_list.addItem(item)

# 圆形纤维对话框类
class LineCircleFiberDialog(QDialog):
    """直线圆形纤维添加对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加直线圆形纤维")
        self.setModal(True)
        self.resize(400, 500)
        
        # 创建输入控件
        self._create_widgets()
        self._create_layout()
    
    def _create_widgets(self):
        """创建输入控件"""
        # 起点坐标
        self.start_y_input = QDoubleSpinBox()
        self.start_y_input.setRange(-1000, 1000)
        self.start_y_input.setDecimals(3)
        self.start_y_input.setValue(0.0)
        
        self.start_z_input = QDoubleSpinBox()
        self.start_z_input.setRange(-1000, 1000)
        self.start_z_input.setDecimals(3)
        self.start_z_input.setValue(0.0)
        
        # 终点坐标
        self.end_y_input = QDoubleSpinBox()
        self.end_y_input.setRange(-1000, 1000)
        self.end_y_input.setDecimals(3)
        self.end_y_input.setValue(10.0)
        
        self.end_z_input = QDoubleSpinBox()
        self.end_z_input.setRange(-1000, 1000)
        self.end_z_input.setDecimals(3)
        self.end_z_input.setValue(0.0)
        
        # 纤维参数
        self.radius_input = QDoubleSpinBox()
        self.radius_input.setRange(0.001, 100)
        self.radius_input.setDecimals(4)
        self.radius_input.setValue(0.1)
        
        self.num_fibers_input = QSpinBox()
        self.num_fibers_input.setRange(1, 1000)
        self.num_fibers_input.setValue(5)
        
        self.fiber_area_input = QDoubleSpinBox()
        self.fiber_area_input.setRange(0.0001, 10000)
        self.fiber_area_input.setDecimals(6)
        self.fiber_area_input.setValue(0.0314)
        
        self.material_id_input = QSpinBox()
        self.material_id_input.setRange(1, 100)
        self.material_id_input.setValue(1)
    
    def _create_layout(self):
        """创建布局"""
        layout = QVBoxLayout(self)
        
        # 起点坐标
        start_group = QGroupBox("起点坐标")
        start_layout = QHBoxLayout(start_group)
        start_layout.addWidget(QLabel("Y坐标:"))
        start_layout.addWidget(self.start_y_input)
        start_layout.addWidget(QLabel("Z坐标:"))
        start_layout.addWidget(self.start_z_input)
        layout.addWidget(start_group)
        
        # 终点坐标
        end_group = QGroupBox("终点坐标")
        end_layout = QHBoxLayout(end_group)
        end_layout.addWidget(QLabel("Y坐标:"))
        end_layout.addWidget(self.end_y_input)
        end_layout.addWidget(QLabel("Z坐标:"))
        end_layout.addWidget(self.end_z_input)
        layout.addWidget(end_group)
        
        # 纤维参数
        fiber_group = QGroupBox("纤维参数")
        fiber_layout = QVBoxLayout(fiber_group)
        
        # 半径和数量
        radius_layout = QHBoxLayout()
        radius_layout.addWidget(QLabel("半径:"))
        radius_layout.addWidget(self.radius_input)
        radius_layout.addWidget(QLabel("数量:"))
        radius_layout.addWidget(self.num_fibers_input)
        fiber_layout.addLayout(radius_layout)
        
        # 面积和材料
        area_layout = QHBoxLayout()
        area_layout.addWidget(QLabel("面积:"))
        area_layout.addWidget(self.fiber_area_input)
        area_layout.addWidget(QLabel("材料ID:"))
        area_layout.addWidget(self.material_id_input)
        fiber_layout.addLayout(area_layout)
        
        layout.addWidget(fiber_group)
        
        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_values(self):
        """获取输入值"""
        return {
            'start_y': self.start_y_input.value(),
            'start_z': self.start_z_input.value(),
            'end_y': self.end_y_input.value(),
            'end_z': self.end_z_input.value(),
            'radius': self.radius_input.value(),
            'num_fibers': self.num_fibers_input.value(),
            'fiber_area': self.fiber_area_input.value(),
            'material_id': self.material_id_input.value()
        }

class RadialCircleFiberDialog(QDialog):
    """径向圆形纤维添加对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加径向圆形纤维")
        self.setModal(True)
        self.resize(400, 450)
        
        # 创建输入控件
        self._create_widgets()
        self._create_layout()
    
    def _create_widgets(self):
        """创建输入控件"""
        # 圆心坐标
        self.center_y_input = QDoubleSpinBox()
        self.center_y_input.setRange(-1000, 1000)
        self.center_y_input.setDecimals(3)
        self.center_y_input.setValue(0.0)
        
        self.center_z_input = QDoubleSpinBox()
        self.center_z_input.setRange(-1000, 1000)
        self.center_z_input.setDecimals(3)
        self.center_z_input.setValue(0.0)
        
        # 纤维参数
        self.radius_input = QDoubleSpinBox()
        self.radius_input.setRange(0.001, 100)
        self.radius_input.setDecimals(3)
        self.radius_input.setValue(2.0)
        
        self.num_fibers_input = QSpinBox()
        self.num_fibers_input.setRange(1, 1000)
        self.num_fibers_input.setValue(8)
        
        self.fiber_area_input = QDoubleSpinBox()
        self.fiber_area_input.setRange(0.0001, 10000)
        self.fiber_area_input.setDecimals(6)
        self.fiber_area_input.setValue(0.0314)
        
        self.material_id_input = QSpinBox()
        self.material_id_input.setRange(1, 100)
        self.material_id_input.setValue(1)
        
        # 角度参数
        self.start_angle_input = QDoubleSpinBox()
        self.start_angle_input.setRange(0, 360)
        self.start_angle_input.setDecimals(1)
        self.start_angle_input.setValue(0.0)
        
        self.end_angle_input = QDoubleSpinBox()
        self.end_angle_input.setRange(0, 360)
        self.end_angle_input.setDecimals(1)
        self.end_angle_input.setValue(360.0)
    
    def _create_layout(self):
        """创建布局"""
        layout = QVBoxLayout(self)
        
        # 圆心坐标
        center_group = QGroupBox("圆心坐标")
        center_layout = QHBoxLayout(center_group)
        center_layout.addWidget(QLabel("Y坐标:"))
        center_layout.addWidget(self.center_y_input)
        center_layout.addWidget(QLabel("Z坐标:"))
        center_layout.addWidget(self.center_z_input)
        layout.addWidget(center_group)
        
        # 纤维参数
        fiber_group = QGroupBox("纤维参数")
        fiber_layout = QVBoxLayout(fiber_group)
        
        # 半径和数量
        radius_layout = QHBoxLayout()
        radius_layout.addWidget(QLabel("半径:"))
        radius_layout.addWidget(self.radius_input)
        radius_layout.addWidget(QLabel("数量:"))
        radius_layout.addWidget(self.num_fibers_input)
        fiber_layout.addLayout(radius_layout)
        
        # 面积和材料
        area_layout = QHBoxLayout()
        area_layout.addWidget(QLabel("面积:"))
        area_layout.addWidget(self.fiber_area_input)
        area_layout.addWidget(QLabel("材料ID:"))
        area_layout.addWidget(self.material_id_input)
        fiber_layout.addLayout(area_layout)
        
        layout.addWidget(fiber_group)
        
        # 角度参数
        angle_group = QGroupBox("角度范围")
        angle_layout = QHBoxLayout(angle_group)
        angle_layout.addWidget(QLabel("起始角度:"))
        angle_layout.addWidget(self.start_angle_input)
        angle_layout.addWidget(QLabel("终止角度:"))
        angle_layout.addWidget(self.end_angle_input)
        layout.addWidget(angle_group)
        
        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_values(self):
        """获取输入值"""
        return {
            'center_y': self.center_y_input.value(),
            'center_z': self.center_z_input.value(),
            'radius': self.radius_input.value(),
            'num_fibers': self.num_fibers_input.value(),
            'fiber_area': self.fiber_area_input.value(),
            'material_id': self.material_id_input.value(),
            'start_angle': self.start_angle_input.value(),
            'end_angle': self.end_angle_input.value()
        }


class ShapeFiberTab(QWidget):
    """形状和纤维管理标签页"""
    def __init__(self, data_manager, control_panel):
        super().__init__()
        self.data_manager = data_manager
        self.control_panel = control_panel
        
        # 创建形状列表
        self.shape_list = QListWidget()
        self.shape_list.setSelectionMode(QListWidget.ExtendedSelection)
        
        # 创建纤维列表
        self.fiber_list = QListWidget()
        self.fiber_list.setSelectionMode(QListWidget.ExtendedSelection)
        
        # 创建按钮
        self.btn_refresh = QPushButton("刷新列表")
        self.btn_edit_shape = QPushButton("编辑选中形状")
        self.btn_delete_shape = QPushButton("删除选中形状")
        self.btn_delete_fiber = QPushButton("删除选中纤维")
        
        # 圆形纤维添加按钮
        self.btn_add_line_circle_fiber = QPushButton("添加直线圆形纤维")
        self.btn_add_radial_circle_fiber = QPushButton("添加径向圆形纤维")
        
        # 布局
        layout = QVBoxLayout(self)
        
        # 形状管理
        shape_group = QGroupBox("形状管理")
        shape_layout = QVBoxLayout(shape_group)
        shape_layout.addWidget(QLabel("形状列表 (勾选表示激活):"))
        shape_layout.addWidget(self.shape_list)
        
        shape_button_layout = QHBoxLayout()
        shape_button_layout.addWidget(self.btn_refresh)
        shape_button_layout.addWidget(self.btn_edit_shape)
        shape_button_layout.addWidget(self.btn_delete_shape)
        shape_layout.addLayout(shape_button_layout)
        
        layout.addWidget(shape_group)
        
        # 纤维管理
        fiber_group = QGroupBox("纤维管理")
        fiber_layout = QVBoxLayout(fiber_group)
        fiber_layout.addWidget(QLabel("纤维列表 (勾选表示激活):"))
        fiber_layout.addWidget(self.fiber_list)
        
        fiber_button_layout = QHBoxLayout()
        fiber_button_layout.addWidget(self.btn_delete_fiber)
        fiber_button_layout.addWidget(self.btn_add_line_circle_fiber)
        fiber_button_layout.addWidget(self.btn_add_radial_circle_fiber)
        fiber_layout.addLayout(fiber_button_layout)
        
        layout.addWidget(fiber_group)
        
        # 连接信号
        self.btn_refresh.clicked.connect(self._update_lists)
        self.btn_edit_shape.clicked.connect(self._on_edit_shape)
        self.btn_delete_shape.clicked.connect(self._on_delete_shape)
        self.btn_delete_fiber.clicked.connect(self._on_delete_fiber)
        self.btn_add_line_circle_fiber.clicked.connect(self._on_add_line_circle_fiber)
        self.btn_add_radial_circle_fiber.clicked.connect(self._on_add_radial_circle_fiber)
        self.shape_list.itemChanged.connect(self._on_shape_item_changed)
        self.fiber_list.itemChanged.connect(self._on_fiber_item_changed)
        self.fiber_list.itemClicked.connect(self._on_fiber_item_clicked)
        self.data_manager.fiber_selected.connect(self._on_fiber_selected)
        
        # 初始化列表
        self._update_lists()
        
        # 连接刷新信号
        self.control_panel.fiber_list_refresh.connect(self._update_fiber_list)
        self.control_panel.shape_list_refresh.connect(self._update_shape_list)
    
    def _update_lists(self):
        """更新形状和纤维列表"""
        self._update_shape_list()
        self._update_fiber_list()
    
    def _update_shape_list(self):
        """更新形状列表显示"""
        self.shape_list.clear()
        
        # 获取当前截面的形状列表
        current_section = self.data_manager.get_current_section()
        if not current_section:
            return
        
        # 添加形状项
        for shape in current_section.get_shapes():
            item = QListWidgetItem(f"形状 {shape.id}: {shape.__class__.__name__}")
            item.setData(Qt.UserRole, shape.id)
            
            # 设置勾选状态
            if shape.active:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            
            # 设置颜色
            color = shape.color
            item.setForeground(QColor(color))
            
            # 添加到列表
            self.shape_list.addItem(item)
        
        # 刷新canvas
        self.control_panel.section_switched.emit()
    
    def _update_fiber_list(self):
        """更新纤维列表显示"""
        self.fiber_list.clear()
        
        current_section = self.data_manager.get_current_section()
        if not current_section:
            return
        
        # 获取所有纤维：手动纤维（section.fibers） + 网格纤维（section.mesh.fibers）
        all_fibers = []
        
        # 首先添加section.fibers中的手动纤维
        if current_section.fibers:
            all_fibers.extend(current_section.fibers)
        
        # 然后添加网格纤维（避免重复）
        if current_section.mesh and current_section.mesh.fibers:
            # 获取已存在纤维的ID集合
            existing_fiber_ids = {fiber.id for fiber in all_fibers}
            
            # 只添加不重复的网格纤维
            for fiber in current_section.mesh.fibers:
                if fiber.id not in existing_fiber_ids:
                    all_fibers.append(fiber)
        
        # 按纤维ID排序显示
        all_fibers.sort(key=lambda f: f.id)
        
        # 显示所有纤维
        for fiber in all_fibers:
            # 判断纤维类型并添加标识
            if fiber.id >= 2000 and fiber.id < 3000:
                fiber_type = "线性纤维"
            elif fiber.id >= 3000 and fiber.id < 4000:
                fiber_type = "径向纤维"
            else:
                fiber_type = "网格纤维"
            
            item = QListWidgetItem(f"纤维 {fiber.id}: ({fiber.y:.3f}, {fiber.z:.3f}) 面积: {fiber.area:.6f} [{fiber_type}] (材料: {fiber.material_id})")
            item.setData(Qt.UserRole, fiber.id)
            item.setCheckState(Qt.Checked if fiber.active else Qt.Unchecked)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            self.fiber_list.addItem(item)
    
    def _on_edit_shape(self):
        """编辑选中的形状"""
        selected_items = self.shape_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "编辑形状", "请先选中要编辑的形状")
            return
        
        # 获取第一个选中的形状
        item = selected_items[0]
        shape_id = item.data(Qt.UserRole)
        
        current_section = self.data_manager.get_current_section()
        if current_section:
            shape = current_section.get_shape_by_id(shape_id)
            if shape:
                # 打开形状编辑对话框
                dialog = ShapeEditDialog(shape, self)
                if dialog.exec_() == QDialog.Accepted:
                    # 更新形状列表显示
                    self._update_shape_list()
                    # 刷新画布
                    self.control_panel.section_switched.emit()

    def _on_shape_item_changed(self, item):
        """形状列表项状态改变时的处理"""
        shape_id = item.data(Qt.UserRole)
        is_active = (item.checkState() == Qt.Checked)
        
        current_section = self.data_manager.get_current_section()
        if current_section:
            shape = current_section.get_shape_by_id(shape_id)
            if shape:
                shape.active = is_active
                # 刷新画布和形状列表
                self.control_panel.section_switched.emit()
                self.control_panel.shape_list_refresh.emit()
    
    def _on_fiber_item_changed(self, item):
        """纤维列表项状态改变时的处理"""
        fiber_id = item.data(Qt.UserRole)
        is_active = (item.checkState() == Qt.Checked)
        
        current_section = self.data_manager.get_current_section()
        if not current_section:
            return
        
        # 先在手动纤维中查找
        fiber = None
        if current_section.fibers:
            fiber = next((f for f in current_section.fibers if f.id == fiber_id), None)
        
        # 如果在手动纤维中没找到，再在网格纤维中查找
        if not fiber and current_section.mesh:
            fiber = current_section.mesh.get_fiber_by_id(fiber_id)
        
        if fiber:
            fiber.active = is_active
            # 更新纤维列表显示
            self._update_fiber_display()
            # 刷新画布和纤维列表
            self.control_panel.canvas_refresh.emit()
            self.control_panel.fiber_list_refresh.emit()
    
    def _on_delete_shape(self):
        """删除选中的形状"""
        selected_items = self.shape_list.selectedItems()
        if not selected_items:
            return
        
        current_section = self.data_manager.get_current_section()
        if current_section:
            for item in selected_items:
                shape_id = item.data(Qt.UserRole)
                self.data_manager.delete_shape(current_section.id, shape_id)
        
        self._update_shape_list()
        # 刷新画布和列表
        self.control_panel.section_switched.emit()
        self.control_panel.shape_list_refresh.emit()
    
    def _on_delete_fiber(self):
        """删除选中的纤维"""
        selected_items = self.fiber_list.selectedItems()
        if not selected_items:
            return
        
        current_section = self.data_manager.get_current_section()
        if current_section and current_section.mesh and current_section.mesh.fibers:
            fiber_ids_to_delete = [item.data(Qt.UserRole) for item in selected_items]
            
            # 删除网格纤维列表中的纤维
            current_section.mesh.fibers = [fiber for fiber in current_section.mesh.fibers if fiber.id not in fiber_ids_to_delete]
            # 同步更新section.fibers列表，确保两者一致
            current_section.fibers = current_section.mesh.fibers[:]
        
        self._update_fiber_list()
        # 刷新画布和列表
        self.control_panel.canvas_refresh.emit()
        self.control_panel.fiber_list_refresh.emit()
    
    def contextMenuEvent(self, event):
        """右键菜单事件处理"""
        # 检查右键点击位置是否在形状列表中
        shape_pos = self.shape_list.mapFromGlobal(event.globalPos())
        shape_item = self.shape_list.itemAt(shape_pos)
        if shape_item:
            self._show_shape_context_menu(event.globalPos(), shape_item)
            return
        
        # 检查右键点击位置是否在纤维列表中
        fiber_pos = self.fiber_list.mapFromGlobal(event.globalPos())
        fiber_item = self.fiber_list.itemAt(fiber_pos)
        if fiber_item:
            self._show_fiber_context_menu(event.globalPos(), fiber_item)
    
    def _show_shape_context_menu(self, pos, shape_item):
        """显示形状右键菜单"""
        menu = QMenu(self)
        
        # 设置网格尺寸菜单项
        set_mesh_size_action = menu.addAction("设置网格尺寸")
        set_mesh_size_action.triggered.connect(lambda: self._set_shape_mesh_size(shape_item))
        
        # 分配材料菜单项
        assign_material_action = menu.addAction("分配材料")
        assign_material_action.triggered.connect(lambda: self._assign_shape_material(shape_item))
        
        menu.exec_(pos)
    
    def _set_shape_mesh_size(self, shape_item):
        """设置形状的网格尺寸"""
        shape_id = shape_item.data(Qt.UserRole)
        current_section = self.data_manager.get_current_section()
        
        if current_section:
            shape = current_section.get_shape_by_id(shape_id)
            if shape:
                # 获取当前网格尺寸
                current_size = shape.mesh_size if shape.mesh_size is not None else 0.1
                
                # 显示输入对话框
                mesh_size, ok = QInputDialog.getDouble(
                    self, 
                    "设置网格尺寸", 
                    f"请输入形状 {shape.id} 的网格尺寸:",
                    value=current_size,
                    min=0.001,
                    max=10.0,
                    decimals=3
                )
                
                if ok:
                    shape.mesh_size = mesh_size
                    # 更新形状列表显示
                    self._update_shape_list()
                    # 刷新画布
                    self.control_panel.section_switched.emit()
    
    def _assign_shape_material(self, shape_item):
        """为形状分配材料"""
        shape_id = shape_item.data(Qt.UserRole)
        current_section = self.data_manager.get_current_section()
        
        if current_section:
            shape = current_section.get_shape_by_id(shape_id)
            if shape:
                # 获取当前材料ID
                current_material_id = shape.material_id if shape.material_id is not None else 1
                
                # 显示输入对话框
                material_id, ok = QInputDialog.getInt(
                    self, 
                    "分配材料", 
                    f"请输入形状 {shape.id} 的材料ID:",
                    value=current_material_id,
                    min=1,
                    max=1000
                )
                
                if ok:
                    shape.material_id = material_id
                    # 更新形状列表显示
                    self._update_shape_list()
                    # 刷新画布
                    self.control_panel.section_switched.emit()
    
    def _show_fiber_context_menu(self, pos, fiber_item):
        """显示纤维右键菜单"""
        menu = QMenu(self)
        
        # 分配材料菜单项
        assign_material_action = menu.addAction("分配材料")
        # 获取所有选中的纤维项
        selected_items = self.fiber_list.selectedItems()
        assign_material_action.triggered.connect(lambda: self._assign_fiber_material(selected_items))
        
        # 激活/钝化菜单项
        if selected_items:
            # 检查第一个选中纤维的激活状态，决定菜单项文本
            first_fiber_id = selected_items[0].data(Qt.UserRole)
            current_section = self.data_manager.get_current_section()
            fiber = current_section.mesh.get_fiber_by_id(first_fiber_id) if current_section and current_section.mesh else None
            if fiber:
                if fiber.active:
                    deactivate_action = menu.addAction("钝化选中纤维")
                    deactivate_action.triggered.connect(lambda checked, items=selected_items: self._toggle_fiber_active(items, False))
                else:
                    activate_action = menu.addAction("激活选中纤维")
                    activate_action.triggered.connect(lambda checked, items=selected_items: self._toggle_fiber_active(items, True))
        
        menu.exec_(pos)
    
    def _assign_fiber_material(self, fiber_items):
        """为纤维分配材料"""
        if not fiber_items:
            return
            
        current_section = self.data_manager.get_current_section()
        if current_section and current_section.mesh:
            # 获取第一个纤维的当前材料ID作为默认值
            first_fiber_id = fiber_items[0].data(Qt.UserRole)
            first_fiber = current_section.mesh.get_fiber_by_id(first_fiber_id)
            current_material_id = first_fiber.material_id if first_fiber and first_fiber.material_id is not None else 1
            
            # 显示输入对话框
            material_id, ok = QInputDialog.getInt(
                self, 
                "分配材料", 
                f"请输入材料ID (将应用到 {len(fiber_items)} 个选中的纤维):",
                value=current_material_id,
                min=1,
                max=1000
            )
            
            if ok:
                # 为所有选中的纤维分配材料
                for item in fiber_items:
                    fiber_id = item.data(Qt.UserRole)
                    fiber = current_section.mesh.get_fiber_by_id(fiber_id)
                    if fiber:
                        fiber.material_id = material_id
                # 更新纤维列表显示
                self._update_fiber_list()
                # 刷新画布和纤维列表
                self.control_panel.canvas_refresh.emit()
                self.control_panel.fiber_list_refresh.emit()
    
    def _on_fiber_item_clicked(self, item):
        """处理纤维列表条目点击事件，选中视图中对应的纤维"""
        # 获取所有选中的纤维ID
        selected_items = self.fiber_list.selectedItems()
        fiber_ids = [item.data(Qt.UserRole) for item in selected_items]
        # 通过数据管理器通知画布高亮显示选中的纤维
        self.data_manager.fiber_selected.emit(fiber_ids)
    
    def _on_fiber_selected(self, fiber_ids):
        """处理纤维选中信号，同步选中右侧栏中的纤维条目"""
        self.fiber_list.clearSelection()
        
        if fiber_ids is not None:
            # 确保fiber_ids是一个列表
            if not isinstance(fiber_ids, list):
                fiber_ids = [fiber_ids]
            
            for i in range(self.fiber_list.count()):
                item = self.fiber_list.item(i)
                if item.data(Qt.UserRole) in fiber_ids:
                    item.setSelected(True)

    def _toggle_fiber_active(self, fiber_items, activate=True):
        """切换纤维的激活状态"""
        try:
            for item in fiber_items:
                fiber_id = item.data(Qt.UserRole)
                if fiber_id is not None:
                    # 获取当前截面
                    current_section = self.data_manager.get_current_section()
                    if current_section and current_section.fibers:
                        # 查找对应的纤维
                        fiber = current_section.get_fiber_by_id(fiber_id)
                        if fiber:
                            if activate:
                                fiber.activate()
                            else:
                                fiber.deactivate()
                            
                            # 更新显示
                            self._update_fiber_display()
            
            # 刷新画布和纤维列表
            self.control_panel.canvas_refresh.emit()
            self.control_panel.fiber_list_refresh.emit()
            
            # 发出纤维选择信号以同步显示
            self.control_panel.fiber_selected.emit([])
            
        except Exception as e:
            print(f"切换纤维激活状态时出错: {e}")
            import traceback
            traceback.print_exc()

    def _on_add_line_circle_fiber(self):
        """添加直线圆形纤维"""
        dialog = LineCircleFiberDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.get_values()
            
            # 生成直线圆形纤维
            try:
                from utilities.circle_fiber_generator import CircleFiberGenerator
                fibers = CircleFiberGenerator.generate_line_circular_fibers(
                    start_y=values['start_y'],
                    start_z=values['start_z'],
                    end_y=values['end_y'],
                    end_z=values['end_z'],
                    radius=values['radius'],
                    num_fibers=values['num_fibers'],
                    fiber_area=values['fiber_area'],
                    material_id=values['material_id']
                )
                
                # 获取当前截面，如果不存在则创建新截面
                current_section = self.data_manager.get_current_section()
                if not current_section:
                    # 如果没有当前截面，创建一个默认截面
                    self.data_manager.create_section("纤维截面")
                    current_section = self.data_manager.get_current_section()
                
                if current_section:
                    # 更新纤维ID（避免重复）
                    current_fiber_count = len(current_section.fibers) if current_section.fibers else 0
                    for i, fiber in enumerate(fibers):
                        fiber.id = current_fiber_count + i + 1
                    
                    # 添加到截面纤维列表（确保同步）
                    if current_section.fibers is None:
                        current_section.fibers = []
                    
                    # 只添加到网格纤维列表，section.fibers 应该从 mesh.fibers 同步
                    if current_section.mesh and current_section.mesh.fibers:
                        current_section.mesh.fibers.extend(fibers)
                        # 同步更新 section.fibers 列表
                        current_section.fibers = current_section.mesh.fibers[:]
                    elif current_section.mesh:
                        current_section.mesh.fibers = fibers[:]
                        # 同步更新 section.fibers 列表
                        current_section.fibers = current_section.mesh.fibers[:]
                    else:
                        # 如果没有网格，直接添加到section.fibers
                        current_section.fibers.extend(fibers)
                    
                    # 更新纤维列表显示
                    self._update_fiber_list()
                    
                    # 刷新画布
                    self.control_panel.section_switched.emit()
                    self.control_panel.fiber_list_refresh.emit()
                    
                    QMessageBox.information(self, "成功", f"成功添加了 {len(fibers)} 个直线圆形纤维")
                else:
                    QMessageBox.warning(self, "警告", "创建截面失败，请重试")
                    
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加直线圆形纤维失败: {str(e)}")
    
    def _on_add_radial_circle_fiber(self):
        """添加径向圆形纤维"""
        dialog = RadialCircleFiberDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.get_values()
            
            # 生成径向圆形纤维
            try:
                from utilities.circle_fiber_generator import CircleFiberGenerator
                fibers = CircleFiberGenerator.generate_radial_circular_fibers(
                    center_y=values['center_y'],
                    center_z=values['center_z'],
                    radius=values['radius'],
                    num_fibers=values['num_fibers'],
                    fiber_area=values['fiber_area'],
                    material_id=values['material_id'],
                    start_angle=values['start_angle'],
                    end_angle=values['end_angle']
                )
                
                # 获取当前截面，如果不存在则创建新截面
                current_section = self.data_manager.get_current_section()
                if not current_section:
                    # 如果没有当前截面，创建一个默认截面
                    self.data_manager.create_section("纤维截面")
                    current_section = self.data_manager.get_current_section()
                
                if current_section:
                    # 更新纤维ID（避免重复）
                    current_fiber_count = len(current_section.fibers) if current_section.fibers else 0
                    for i, fiber in enumerate(fibers):
                        fiber.id = current_fiber_count + i + 1
                    
                    # 添加到截面纤维列表（确保同步）
                    if current_section.fibers is None:
                        current_section.fibers = []
                    
                    # 只添加到网格纤维列表，section.fibers 应该从 mesh.fibers 同步
                    if current_section.mesh and current_section.mesh.fibers:
                        current_section.mesh.fibers.extend(fibers)
                        # 同步更新 section.fibers 列表
                        current_section.fibers = current_section.mesh.fibers[:]
                    elif current_section.mesh:
                        current_section.mesh.fibers = fibers[:]
                        # 同步更新 section.fibers 列表
                        current_section.fibers = current_section.mesh.fibers[:]
                    else:
                        # 如果没有网格，直接添加到section.fibers
                        current_section.fibers.extend(fibers)
                    
                    # 更新纤维列表显示
                    self._update_fiber_list()
                    
                    # 刷新画布
                    self.control_panel.section_switched.emit()
                    self.control_panel.fiber_list_refresh.emit()
                    
                    QMessageBox.information(self, "成功", f"成功添加了 {len(fibers)} 个径向圆形纤维")
                else:
                    QMessageBox.warning(self, "警告", "创建截面失败，请重试")
                    
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加径向圆形纤维失败: {str(e)}")

    def _update_fiber_display(self):
        """更新纤维列表显示"""
        current_section = self.data_manager.get_current_section()
        if not current_section or not current_section.fibers:
            self.fiber_list.clear()
            return
        
        # 清除现有项目
        self.fiber_list.clear()
        
        # 添加纤维项目
        for fiber in current_section.fibers:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, fiber.id)
            
            # 设置文本显示纤维信息
            status = "激活" if fiber.active else "钝化"
            item.setText(f"纤维{fiber.id}: ({fiber.y:.3f}, {fiber.z:.3f}) - {status}")
            
            # 设置颜色表示激活状态
            if fiber.active:
                item.setBackground(QColor(200, 255, 200))  # 浅绿色
            else:
                item.setBackground(QColor(255, 200, 200))  # 浅红色
            
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if fiber.active else Qt.Unchecked)
            
            self.fiber_list.addItem(item)
        
        # 刷新画布以显示最新的纤维状态
        self.control_panel.canvas_refresh.emit()


class ShapeEditDialog(QDialog):
    """形状编辑对话框"""
    
    def __init__(self, shape, parent=None):
        super().__init__(parent)
        self.shape = shape
        self.setWindowTitle(f"编辑形状 {shape.id}")
        self.setModal(True)
        self.resize(350, 250)
        
        # 创建界面
        self._create_ui()
        
        # 加载当前形状数据
        self._load_shape_data()
    
    def _create_ui(self):
        """创建用户界面"""
        layout = QVBoxLayout(self)
        
        # 形状基本信息组
        info_group = QGroupBox("形状信息")
        info_layout = QVBoxLayout(info_group)
        
        # ID显示（只读）
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("形状ID:"))
        self.lbl_id = QLabel(str(self.shape.id))
        self.lbl_id.setStyleSheet("font-weight: bold;")
        id_layout.addWidget(self.lbl_id)
        id_layout.addStretch()
        info_layout.addLayout(id_layout)
        
        # 形状类型显示（只读）
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("形状类型:"))
        self.lbl_type = QLabel(self.shape.__class__.__name__)
        self.lbl_type.setStyleSheet("font-weight: bold;")
        type_layout.addWidget(self.lbl_type)
        type_layout.addStretch()
        info_layout.addLayout(type_layout)
        
        # 激活状态
        self.chk_active = QCheckBox("激活状态")
        info_layout.addWidget(self.chk_active)
        
        layout.addWidget(info_group)
        
        # 网格设置组
        mesh_group = QGroupBox("网格设置")
        mesh_layout = QVBoxLayout(mesh_group)
        
        # 网格类型选择
        mesh_type_layout = QHBoxLayout()
        mesh_type_layout.addWidget(QLabel("网格类型:"))
        self.cmb_mesh_type = QComboBox()
        self.cmb_mesh_type.addItems(["三角形网格", "四边形网格"])
        mesh_type_layout.addWidget(self.cmb_mesh_type)
        mesh_type_layout.addStretch()
        mesh_layout.addLayout(mesh_type_layout)
        
        # 网格尺寸
        mesh_size_layout = QHBoxLayout()
        mesh_size_layout.addWidget(QLabel("网格尺寸:"))
        self.spn_mesh_size = QDoubleSpinBox()
        self.spn_mesh_size.setRange(0.001, 10.0)
        self.spn_mesh_size.setDecimals(3)
        self.spn_mesh_size.setSuffix(" m")
        self.spn_mesh_size.setValue(0.1)  # 默认值
        self.spn_mesh_size.setSpecialValueText("使用全局网格尺寸")
        mesh_size_layout.addWidget(self.spn_mesh_size)
        mesh_size_layout.addStretch()
        mesh_layout.addLayout(mesh_size_layout)
        
        layout.addWidget(mesh_group)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # 连接信号
        self.cmb_mesh_type.currentTextChanged.connect(self._on_mesh_type_changed)
    
    def _load_shape_data(self):
        """加载当前形状数据到界面"""
        # 设置激活状态
        self.chk_active.setChecked(getattr(self.shape, 'active', True))
        
        # 设置网格类型
        mesh_type = getattr(self.shape, 'mesh_type', 'triangular')
        if mesh_type == 'quadrilateral':
            self.cmb_mesh_type.setCurrentText("四边形网格")
        else:
            self.cmb_mesh_type.setCurrentText("三角形网格")
        
        # 设置网格尺寸
        mesh_size = getattr(self.shape, 'mesh_size', None)
        if mesh_size is not None:
            self.spn_mesh_size.setValue(mesh_size)
        else:
            self.spn_mesh_size.setValue(0.1)  # 显示默认值
    
    def _on_mesh_type_changed(self, text):
        """网格类型改变时的处理"""
        # 更新网格尺寸的提示文本
        if "三角形" in text:
            self.spn_mesh_size.setSuffix(" m")
        else:
            self.spn_mesh_size.setSuffix(" m")
    
    def accept(self):
        """确认保存修改"""
        # 保存激活状态
        self.shape.active = self.chk_active.isChecked()
        
        # 保存网格类型
        mesh_type_text = self.cmb_mesh_type.currentText()
        if "四边形" in mesh_type_text:
            self.shape.mesh_type = 'quadrilateral'
        else:
            self.shape.mesh_type = 'triangular'
        
        # 保存网格尺寸
        mesh_size_value = self.spn_mesh_size.value()
        if abs(mesh_size_value - 0.1) < 0.001:  # 如果是默认值，检查是否应该设为None
            # 检查用户是否想要使用全局设置
            self.shape.mesh_size = None  # 使用全局网格尺寸
        else:
            self.shape.mesh_size = mesh_size_value
        
        print(f"形状 {self.shape.id} 修改完成:")
        print(f"  激活状态: {self.shape.active}")
        print(f"  网格类型: {self.shape.mesh_type}")
        print(f"  网格尺寸: {self.shape.mesh_size}")
        
        super().accept()
