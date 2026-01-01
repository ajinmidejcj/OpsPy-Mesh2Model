from typing import Optional, Dict, Any, List
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget,
                             QGroupBox, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
                             QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QFileDialog, QTextEdit, QListWidget,
                             QListWidgetItem, QCheckBox, QScrollArea, QSplitter, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSignal as Signal
from PyQt5.QtGui import QFont
import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, current_dir)

from fiber_section_gui.data.data_manager import DataManager
from fiber_section_gui.openseespy_modeling.openseespy_controller import OpenSeesPyController
from fiber_section_gui.gui.transform_panel import TransformPanel
from fiber_section_gui.gui.beam_integration_panel import BeamIntegrationPanel
from fiber_section_gui.gui.fix_boundary_panel import FixBoundaryPanel


class OpenSeesPyPanel(QWidget):
    """OpenSeesPy建模面板"""
    
    # 信号定义
    model_changed = pyqtSignal()  # 模型数据变化
    export_completed = pyqtSignal(str)  # 导出完成
    
    def __init__(self, data_manager: DataManager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        
        # 初始化OpenSeesPy控制器
        self.controller = OpenSeesPyController(data_manager)
        
        # 记录主窗口引用用于视图更新
        self.main_window = parent
        
        # 创建界面
        self._create_ui()
        
        # 连接信号
        self._connect_signals()
        
        # 初始化显示
        self._update_display()
        
    def _create_ui(self):
        """创建用户界面"""
        main_layout = QVBoxLayout(self)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 模型设置标签页
        self.model_tab = self._create_model_tab()
        self.tab_widget.addTab(self.model_tab, "模型设置")
        
        # 节点管理标签页
        self.nodes_tab = self._create_nodes_tab()
        self.tab_widget.addTab(self.nodes_tab, "节点管理")
        
        # 材料管理标签页
        self.materials_tab = self._create_materials_tab()
        self.tab_widget.addTab(self.materials_tab, "材料管理")
        
        # 坐标系变换标签页
        self.transforms_tab = self._create_transforms_tab()
        self.tab_widget.addTab(self.transforms_tab, "坐标系变换")
        
        # 单元管理标签页
        self.elements_tab = self._create_elements_tab()
        self.tab_widget.addTab(self.elements_tab, "单元管理")
        
        # 截面管理标签页
        self.sections_tab = self._create_sections_tab()
        self.tab_widget.addTab(self.sections_tab, "截面管理")
        
        # beamIntegration标签页
        self.beam_integration_tab = self._create_beam_integration_tab()
        self.tab_widget.addTab(self.beam_integration_tab, "beamIntegration")
        
        # 边界条件标签页
        self.fix_boundary_tab = self._create_fix_boundary_tab()
        self.tab_widget.addTab(self.fix_boundary_tab, "边界条件")
        
        # 代码导出标签页
        self.export_tab = self._create_export_tab()
        self.tab_widget.addTab(self.export_tab, "代码导出")
        
        main_layout.addWidget(self.tab_widget)
        
    def _create_model_tab(self) -> QWidget:
        """创建模型设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 模型维度设置
        dimension_group = QGroupBox("模型维度设置")
        dimension_layout = QVBoxLayout(dimension_group)
        
        self.ndm_combo = QComboBox()
        self.ndm_combo.addItems(["2D (二维)", "3D (三维)"])
        self.ndm_combo.setCurrentText("3D (三维)")
        dimension_layout.addWidget(QLabel("模型维度:"))
        dimension_layout.addWidget(self.ndm_combo)
        
        self.ndf_label = QLabel("自由度数量: 6")
        dimension_layout.addWidget(self.ndf_label)
        
        self.dof_label = QLabel("自由度列表: UX, UY, UZ, RX, RY, RZ")
        dimension_layout.addWidget(self.dof_label)
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        self.btn_apply_settings = QPushButton("应用设置")
        self.btn_reset_model = QPushButton("重置模型")
        btn_layout.addWidget(self.btn_apply_settings)
        btn_layout.addWidget(self.btn_reset_model)
        dimension_layout.addLayout(btn_layout)
        
        layout.addWidget(dimension_group)
        
        # 模型摘要
        summary_group = QGroupBox("模型摘要")
        summary_layout = QVBoxLayout(summary_group)
        
        self.model_summary = QTextEdit()
        self.model_summary.setMaximumHeight(200)
        self.model_summary.setReadOnly(True)
        summary_layout.addWidget(self.model_summary)
        
        btn_layout2 = QHBoxLayout()
        self.btn_refresh_summary = QPushButton("刷新摘要")
        btn_layout2.addWidget(self.btn_refresh_summary)
        summary_layout.addLayout(btn_layout2)
        
        layout.addWidget(summary_group)
        layout.addStretch()
        
        return tab
        
    def _create_nodes_tab(self) -> QWidget:
        """创建节点管理标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 创建节点区域
        create_group = QGroupBox("创建节点")
        create_layout = QGridLayout(create_group)
        
        # 节点ID
        create_layout.addWidget(QLabel("节点ID:"), 0, 0)
        self.node_id_input = QSpinBox()
        self.node_id_input.setMinimum(1)
        self.node_id_input.setMaximum(999999)
        create_layout.addWidget(self.node_id_input, 0, 1)
        
        # 坐标输入
        create_layout.addWidget(QLabel("X坐标:"), 1, 0)
        self.x_input = QDoubleSpinBox()
        self.x_input.setDecimals(3)
        create_layout.addWidget(self.x_input, 1, 1)
        
        create_layout.addWidget(QLabel("Y坐标:"), 1, 2)
        self.y_input = QDoubleSpinBox()
        self.y_input.setDecimals(3)
        create_layout.addWidget(self.y_input, 1, 3)
        
        create_layout.addWidget(QLabel("Z坐标:"), 2, 0)
        self.z_input = QDoubleSpinBox()
        self.z_input.setDecimals(3)
        create_layout.addWidget(self.z_input, 2, 1)
        
        # 质量输入（6个自由度）
        create_layout.addWidget(QLabel("质量(UX):"), 3, 0)
        self.mass_ux_input = QDoubleSpinBox()
        self.mass_ux_input.setDecimals(6)
        self.mass_ux_input.setMinimum(-999999)
        create_layout.addWidget(self.mass_ux_input, 3, 1)
        
        create_layout.addWidget(QLabel("质量(UY):"), 3, 2)
        self.mass_uy_input = QDoubleSpinBox()
        self.mass_uy_input.setDecimals(6)
        self.mass_uy_input.setMinimum(-999999)
        create_layout.addWidget(self.mass_uy_input, 3, 3)
        
        create_layout.addWidget(QLabel("质量(UZ):"), 4, 0)
        self.mass_uz_input = QDoubleSpinBox()
        self.mass_uz_input.setDecimals(6)
        self.mass_uz_input.setMinimum(-999999)
        create_layout.addWidget(self.mass_uz_input, 4, 1)
        
        create_layout.addWidget(QLabel("质量(RX):"), 4, 2)
        self.mass_rx_input = QDoubleSpinBox()
        self.mass_rx_input.setDecimals(6)
        self.mass_rx_input.setMinimum(-999999)
        create_layout.addWidget(self.mass_rx_input, 4, 3)
        
        create_layout.addWidget(QLabel("质量(RY):"), 5, 0)
        self.mass_ry_input = QDoubleSpinBox()
        self.mass_ry_input.setDecimals(6)
        self.mass_ry_input.setMinimum(-999999)
        create_layout.addWidget(self.mass_ry_input, 5, 1)
        
        create_layout.addWidget(QLabel("质量(RZ):"), 5, 2)
        self.mass_rz_input = QDoubleSpinBox()
        self.mass_rz_input.setDecimals(6)
        self.mass_rz_input.setMinimum(-999999)
        create_layout.addWidget(self.mass_rz_input, 5, 3)
        
        self.btn_create_node = QPushButton("创建节点")
        create_layout.addWidget(self.btn_create_node, 6, 0, 1, 4)
        
        layout.addWidget(create_group)
        
        # 批量操作区域
        batch_group = QGroupBox("批量操作")
        batch_layout = QVBoxLayout(batch_group)
        
        btn_layout = QHBoxLayout()
        self.btn_import_csv = QPushButton("从CSV导入")
        self.btn_export_csv = QPushButton("导出CSV")
        self.btn_create_template = QPushButton("创建模板")
        self.btn_clear_nodes = QPushButton("清空所有节点")
        
        btn_layout.addWidget(self.btn_import_csv)
        btn_layout.addWidget(self.btn_export_csv)
        btn_layout.addWidget(self.btn_create_template)
        btn_layout.addWidget(self.btn_clear_nodes)
        batch_layout.addLayout(btn_layout)
        
        layout.addWidget(batch_group)
        
        # 节点列表
        nodes_group = QGroupBox("节点列表")
        nodes_layout = QVBoxLayout(nodes_group)
        
        self.nodes_table = QTableWidget()
        self.nodes_table.setColumnCount(10)
        self.nodes_table.setHorizontalHeaderLabels(["ID", "X", "Y", "Z", "质量_UX", "质量_UY", "质量_UZ", "质量_RX", "质量_RY", "质量_RZ"])
        self.nodes_table.setAlternatingRowColors(True)
        self.nodes_table.horizontalHeader().setStretchLastSection(True)
        self.nodes_table.setEditTriggers(QTableWidget.DoubleClicked)  # 双击编辑
        self.nodes_table.setSelectionBehavior(QTableWidget.SelectRows)
        nodes_layout.addWidget(self.nodes_table)
        
        layout.addWidget(nodes_group)
        
        return tab
        
    def _create_materials_tab(self) -> QWidget:
        """创建材料管理标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 创建材料区域
        create_group = QGroupBox("创建材料")
        create_layout = QGridLayout(create_group)
        
        # 材料类型
        create_layout.addWidget(QLabel("材料类型:"), 0, 0)
        self.material_type_combo = QComboBox()
        self.material_type_combo.addItems(["Steel02", "Concrete02", "Concrete04", "Elastic"])
        create_layout.addWidget(self.material_type_combo, 0, 1)
        
        # 材料名称
        create_layout.addWidget(QLabel("材料名称:"), 1, 0)
        self.material_name_input = QLineEdit()
        create_layout.addWidget(self.material_name_input, 1, 1)
        
        # 材料ID
        create_layout.addWidget(QLabel("材料ID:"), 1, 2)
        self.material_id_input = QSpinBox()
        self.material_id_input.setMinimum(1)
        self.material_id_input.setMaximum(999999)
        create_layout.addWidget(self.material_id_input, 1, 3)
        
        # 动态参数输入区域
        self.params_frame = QFrame()
        self.params_layout = QGridLayout(self.params_frame)
        create_layout.addWidget(self.params_frame, 2, 0, 1, 4)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        self.btn_create_material = QPushButton("创建材料")
        self.btn_preview_command = QPushButton("预览命令")
        btn_layout.addWidget(self.btn_create_material)
        btn_layout.addWidget(self.btn_preview_command)
        create_layout.addLayout(btn_layout, 3, 0, 1, 4)
        
        layout.addWidget(create_group)
        
        # 初始化材料参数输入区域
        self._on_material_type_changed(self.material_type_combo.currentText())

        # 材料列表
        materials_group = QGroupBox("材料列表")
        materials_layout = QVBoxLayout(materials_group)
        
        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(4)
        self.materials_table.setHorizontalHeaderLabels(["ID", "名称", "类型", "参数"])
        self.materials_table.setAlternatingRowColors(True)
        self.materials_table.horizontalHeader().setStretchLastSection(True)
        materials_layout.addWidget(self.materials_table)
        
        btn_layout = QHBoxLayout()
        self.btn_clear_materials = QPushButton("清空所有材料")
        btn_layout.addWidget(self.btn_clear_materials)
        materials_layout.addLayout(btn_layout)
        
        layout.addWidget(materials_group)
        
        return tab
        
    def _create_transforms_tab(self) -> QWidget:
        """创建坐标系变换标签页"""
        # 直接使用TransformPanel
        self.transforms_panel = TransformPanel(self.controller.transform_manager)
        return self.transforms_panel
        
    def _create_elements_tab(self) -> QWidget:
        """创建单元管理标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 创建单元区域
        create_group = QGroupBox("创建单元")
        create_layout = QGridLayout(create_group)
        
        # 单元类型
        create_layout.addWidget(QLabel("单元类型:"), 0, 0)
        self.element_type_combo = QComboBox()
        self.element_type_combo.addItems([
            "ZeroLength", "TwoNodeLink", "Truss", 
            "ElasticBeamColumn", "DispBeamColumn", "ForceBeamColumn"
        ])
        create_layout.addWidget(self.element_type_combo, 0, 1)
        
        # 单元ID
        create_layout.addWidget(QLabel("单元ID:"), 1, 0)
        self.element_id_input = QSpinBox()
        self.element_id_input.setMinimum(1)
        self.element_id_input.setMaximum(999999)
        create_layout.addWidget(self.element_id_input, 1, 1)
        
        # 节点ID
        create_layout.addWidget(QLabel("节点1 ID:"), 1, 2)
        self.node1_input = QSpinBox()
        self.node1_input.setMinimum(1)
        self.node1_input.setMaximum(999999)
        create_layout.addWidget(self.node1_input, 1, 3)
        
        create_layout.addWidget(QLabel("节点2 ID:"), 2, 0)
        self.node2_input = QSpinBox()
        self.node2_input.setMinimum(1)
        self.node2_input.setMaximum(999999)
        create_layout.addWidget(self.node2_input, 2, 1)
        
        # 动态参数输入区域
        self.element_params_frame = QFrame()
        self.element_params_layout = QGridLayout(self.element_params_frame)
        create_layout.addWidget(self.element_params_frame, 2, 2, 1, 2)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        self.btn_create_element = QPushButton("创建单元")
        self.btn_preview_element_command = QPushButton("预览命令")
        btn_layout.addWidget(self.btn_create_element)
        btn_layout.addWidget(self.btn_preview_element_command)
        create_layout.addLayout(btn_layout, 3, 0, 1, 4)
        
        layout.addWidget(create_group)
        
        # 初始化单元参数输入区域
        self._on_element_type_changed(self.element_type_combo.currentText())

        # 批量操作区域
        batch_group = QGroupBox("批量操作")
        batch_layout = QVBoxLayout(batch_group)
        
        btn_layout = QHBoxLayout()
        self.btn_elements_import_csv = QPushButton("从CSV导入")
        self.btn_elements_export_csv = QPushButton("导出CSV")
        self.btn_elements_create_template = QPushButton("创建模板")
        self.btn_clear_elements = QPushButton("清空所有单元")
        
        btn_layout.addWidget(self.btn_elements_import_csv)
        btn_layout.addWidget(self.btn_elements_export_csv)
        btn_layout.addWidget(self.btn_elements_create_template)
        btn_layout.addWidget(self.btn_clear_elements)
        batch_layout.addLayout(btn_layout)
        
        layout.addWidget(batch_group)
        
        # 单元列表
        elements_group = QGroupBox("单元列表")
        elements_layout = QVBoxLayout(elements_group)
        
        self.elements_table = QTableWidget()
        self.elements_table.setColumnCount(6)
        self.elements_table.setHorizontalHeaderLabels(["ID", "类型", "节点1", "节点2", "材料", "参数"])
        self.elements_table.setAlternatingRowColors(True)
        self.elements_table.horizontalHeader().setStretchLastSection(True)
        elements_layout.addWidget(self.elements_table)
        
        layout.addWidget(elements_group)
        
        return tab
        
    def _create_sections_tab(self) -> QWidget:
        """创建截面管理标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 截面列表
        sections_group = QGroupBox("截面列表")
        sections_layout = QVBoxLayout(sections_group)
        
        self.sections_list = QListWidget()
        sections_layout.addWidget(self.sections_list)
        
        btn_layout = QHBoxLayout()
        self.btn_refresh_sections = QPushButton("刷新")
        self.btn_export_section = QPushButton("导出截面代码")
        self.btn_section_properties = QPushButton("截面属性")
        btn_layout.addWidget(self.btn_refresh_sections)
        btn_layout.addWidget(self.btn_export_section)
        btn_layout.addWidget(self.btn_section_properties)
        sections_layout.addLayout(btn_layout)
        
        layout.addWidget(sections_group)
        
        # 截面详情
        details_group = QGroupBox("截面详情")
        details_layout = QVBoxLayout(details_group)
        
        self.section_details = QTextEdit()
        self.section_details.setReadOnly(True)
        self.section_details.setMaximumHeight(150)
        details_layout.addWidget(self.section_details)
        
        layout.addWidget(details_group)
        
        return tab
        
    def _create_beam_integration_tab(self) -> QWidget:
        """创建beamIntegration标签页"""
        self.beam_integration_panel = BeamIntegrationPanel(self.controller.beam_integration_manager)
        return self.beam_integration_panel
        
    def _create_fix_boundary_tab(self) -> QWidget:
        """创建fix边界条件标签页"""
        self.fix_boundary_panel = FixBoundaryPanel(self.controller.fix_boundary_manager)
        return self.fix_boundary_panel
        
    def _create_export_tab(self) -> QWidget:
        """创建代码导出标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 导出设置
        settings_group = QGroupBox("导出设置")
        settings_layout = QVBoxLayout(settings_group)
        
        # 导出选项
        self.include_imports_cb = QCheckBox("包含导入语句")
        self.include_imports_cb.setChecked(True)
        settings_layout.addWidget(self.include_imports_cb)
        
        self.include_prints_cb = QCheckBox("包含调试输出")
        settings_layout.addWidget(self.include_prints_cb)
        
        self.include_comments_cb = QCheckBox("包含详细注释")
        self.include_comments_cb.setChecked(True)
        settings_layout.addWidget(self.include_comments_cb)
        
        layout.addWidget(settings_group)
        
        # 代码预览
        preview_group = QGroupBox("代码预览")
        preview_layout = QVBoxLayout(preview_group)
        
        self.code_preview = QTextEdit()
        self.code_preview.setFont(QFont("Courier", 10))
        self.code_preview.setReadOnly(True)
        preview_layout.addWidget(self.code_preview)
        
        btn_layout = QHBoxLayout()
        self.btn_refresh_preview = QPushButton("刷新预览")
        self.btn_export_file = QPushButton("导出到文件")
        btn_layout.addWidget(self.btn_refresh_preview)
        btn_layout.addWidget(self.btn_export_file)
        preview_layout.addLayout(btn_layout)
        
        layout.addWidget(preview_group)
        
        return tab
        
    def _connect_signals(self):
        """连接信号"""
        # 模型设置信号
        self.btn_apply_settings.clicked.connect(self._on_apply_model_settings)
        self.btn_reset_model.clicked.connect(self._on_reset_model)
        self.btn_refresh_summary.clicked.connect(self._on_refresh_model_summary)
        self.ndm_combo.currentTextChanged.connect(self._on_ndm_changed)
        
        # 节点管理信号
        self.btn_create_node.clicked.connect(self._on_create_node)
        self.btn_import_csv.clicked.connect(self._on_import_nodes_csv)
        self.btn_export_csv.clicked.connect(self._on_export_nodes_csv)
        self.btn_create_template.clicked.connect(self._on_create_node_template)
        self.btn_clear_nodes.clicked.connect(self._on_clear_nodes)
        
        # 节点表格编辑信号
        self.nodes_table.itemChanged.connect(self._on_nodes_table_item_changed)
        
        # 材料管理信号
        self.btn_create_material.clicked.connect(self._on_create_material)
        self.btn_preview_command.clicked.connect(self._on_preview_material_command)
        self.material_type_combo.currentTextChanged.connect(self._on_material_type_changed)
        self.btn_clear_materials.clicked.connect(self._on_clear_materials)
        
        # 单元管理信号
        self.element_type_combo.currentTextChanged.connect(self._on_element_type_changed)
        self.btn_create_element.clicked.connect(self._on_create_element)
        self.btn_preview_element_command.clicked.connect(self._on_preview_element_command)
        self.btn_elements_import_csv.clicked.connect(self._on_import_elements_csv)
        self.btn_elements_export_csv.clicked.connect(self._on_export_elements_csv)
        self.btn_elements_create_template.clicked.connect(self._on_create_element_template)
        self.btn_clear_elements.clicked.connect(self._on_clear_elements)
        
        # 截面管理信号
        self.btn_refresh_sections.clicked.connect(self._on_refresh_sections)
        self.btn_export_section.clicked.connect(self._on_export_section_code)
        self.btn_section_properties.clicked.connect(self._on_section_properties)
        
        # 导出信号
        self.btn_refresh_preview.clicked.connect(self._on_refresh_code_preview)
        self.btn_export_file.clicked.connect(self._on_export_to_file)
        
        # 控制器信号
        self.controller.data_changed.connect(self._on_data_changed)
        self.controller.export_completed.connect(self._on_export_completed)
        self.controller.validation_error.connect(self._on_validation_error)
        
    def _update_display(self):
        """更新显示"""
        self._update_model_summary()
        self._update_nodes_table()
        self._update_materials_table()
        self._update_elements_table()
        self._update_sections_list()
        self._update_code_preview()
        
    def _update_3d_view(self):
        """更新3D视图"""
        if hasattr(self.main_window, 'openseespy_3d_view') and self.main_window.openseespy_3d_view:
            self.main_window.openseespy_3d_view.update_from_controller(self.controller)
            
    def _on_nodes_table_item_changed(self, item):
        """节点表格项变化事件处理"""
        row = item.row()
        col = item.column()
        
        # 获取节点ID（第一列）
        node_id_item = self.nodes_table.item(row, 0)
        if not node_id_item:
            return
            
        try:
            node_id = int(node_id_item.text())
        except ValueError:
            QMessageBox.warning(self, "错误", "无效的节点ID")
            return
            
        # 获取当前节点数据
        nodes = self.controller.get_all_nodes()
        node_ids = self.controller.get_all_node_ids()
        
        if node_id not in node_ids:
            QMessageBox.warning(self, "错误", f"节点 {node_id} 不存在")
            return
            
        node = nodes[node_ids.index(node_id)]
        
        # 更新节点坐标或质量
        try:
            if col == 1:  # X坐标
                new_x = float(item.text())
                node.x = new_x
            elif col == 2:  # Y坐标
                new_y = float(item.text())
                node.y = new_y
            elif col == 3:  # Z坐标
                new_z = float(item.text())
                node.z = new_z
            elif col == 4:  # 质量UX
                new_mass_ux = float(item.text())
                node.mass[0] = new_mass_ux
            elif col == 5:  # 质量UY
                new_mass_uy = float(item.text())
                node.mass[1] = new_mass_uy
            elif col == 6:  # 质量UZ
                new_mass_uz = float(item.text())
                node.mass[2] = new_mass_uz
            elif col == 7:  # 质量RX
                new_mass_rx = float(item.text())
                node.mass[3] = new_mass_rx
            elif col == 8:  # 质量RY
                new_mass_ry = float(item.text())
                node.mass[4] = new_mass_ry
            elif col == 9:  # 质量RZ
                new_mass_rz = float(item.text())
                node.mass[5] = new_mass_rz
            else:
                return
                
            # 更新节点时间戳
            from datetime import datetime
            node.updated_at = datetime.now()
            
            # 更新3D视图
            self._update_3d_view()
            
        except ValueError:
            QMessageBox.warning(self, "错误", "请输入有效的数值")
        
    def _on_apply_model_settings(self):
        """应用模型设置"""
        ndm_text = self.ndm_combo.currentText()
        ndm = 3 if "3D" in ndm_text else 2
        
        success = self.controller.model_settings.set_model_dimension(ndm)
        if success:
            QMessageBox.information(self, "成功", "模型设置已更新")
            self._update_model_summary()
        else:
            QMessageBox.warning(self, "错误", "模型设置更新失败")
            
    def _on_reset_model(self):
        """重置模型"""
        reply = QMessageBox.question(
            self, "确认", "确定要重置整个模型吗？这将删除所有数据。",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.controller.reset_model()
            self._update_display()
            QMessageBox.information(self, "成功", "模型已重置")
            
    def _on_refresh_model_summary(self):
        """刷新模型摘要"""
        self._update_model_summary()
        
    def _on_ndm_changed(self):
        """模型维度改变"""
        ndm_text = self.ndm_combo.currentText()
        if "3D" in ndm_text:
            self.ndf_label.setText("自由度数量: 6")
            self.dof_label.setText("自由度列表: UX, UY, UZ, RX, RY, RZ")
        else:
            self.ndf_label.setText("自由度数量: 3")
            self.dof_label.setText("自由度列表: UX, UY, RZ")
            
    def _on_create_node(self):
        """创建节点"""
        node_id = self.node_id_input.value()
        x = self.x_input.value()
        y = self.y_input.value()
        z = self.z_input.value()
        
        # 6个自由度的质量
        mass = [
            self.mass_ux_input.value(),  # UX
            self.mass_uy_input.value(),  # UY
            self.mass_uz_input.value(),  # UZ
            self.mass_rx_input.value(),  # RX
            self.mass_ry_input.value(),  # RY
            self.mass_rz_input.value()   # RZ
        ]
        
        success, error = self.controller.create_node(node_id, x, y, z, mass)
        
        if success:
            QMessageBox.information(self, "成功", f"节点 {node_id} 创建成功")
            self._update_nodes_table()
            self._update_3d_view()  # 更新3D视图
        else:
            QMessageBox.warning(self, "错误", f"节点创建失败: {error}")
            
    def _on_import_nodes_csv(self):
        """从CSV导入节点"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择CSV文件", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            success, error, count = self.controller.import_nodes_from_excel(file_path)
            
            if success:
                QMessageBox.information(self, "成功", f"成功导入 {count} 个节点")
                self._update_nodes_table()
            else:
                QMessageBox.warning(self, "错误", f"导入失败: {error}")
                
    def _on_export_nodes_csv(self):
        """导出节点到CSV"""
        # TODO: 实现CSV导出
        QMessageBox.information(self, "提示", "导出功能待实现")
        
    def _on_create_node_template(self):
        """创建节点模板"""
        success, message = self.controller.create_node_template()
        
        if success:
            QMessageBox.information(self, "成功", message)
        else:
            QMessageBox.warning(self, "错误", message)
            
    def _on_clear_nodes(self):
        """清空所有节点"""
        reply = QMessageBox.question(
            self, "确认", "确定要删除所有节点吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.controller.clear_nodes()
            self._update_nodes_table()
            self._update_3d_view()  # 更新3D视图
            
    def _create_parameter_input(self, label_text: str, row: int, col: int, 
                                spinbox: QDoubleSpinBox, default_value: float, 
                                min_val: float, max_val: float, decimals: int = 0) -> QDoubleSpinBox:
        """创建参数输入控件的辅助函数"""
        self.params_layout.addWidget(QLabel(label_text), row, col)
        spinbox.setDecimals(decimals)
        spinbox.setMinimum(min_val)
        spinbox.setMaximum(max_val)
        spinbox.setValue(default_value)
        self.params_layout.addWidget(spinbox, row, col + 1)
        return spinbox
    
    def _clear_parameter_inputs(self):
        """清空参数输入区域"""
        for i in reversed(range(self.params_layout.count())):
            child = self.params_layout.itemAt(i).widget()
            if child:
                child.deleteLater()
        
    def _on_material_type_changed(self, material_type):
        """材料类型变化时更新参数输入区域"""
        # 清空现有参数输入
        self._clear_parameter_inputs()
        
        if material_type == "Steel02":
            # Steel02钢筋材料参数
            self.fy_input = self._create_parameter_input("屈服强度(Fy):", 0, 0, 
                                                         QDoubleSpinBox(), 400.0, 1.0, 1e9, 0)
            self.E0_input = self._create_parameter_input("弹性模量(E0):", 0, 2, 
                                                         QDoubleSpinBox(), 200000.0, 1.0, 1e12, 0)
            self.b_input = self._create_parameter_input("应变硬化率(b):", 1, 0, 
                                                        QDoubleSpinBox(), 0.01, 0.0, 1.0, 3)
            
            # *params 参数（可选）
            self.params_layout.addWidget(QLabel("*params:"), 1, 2)
            self.params_input = QLineEdit()
            self.params_input.setPlaceholderText("可选，用逗号分隔多个参数")
            self.params_layout.addWidget(self.params_input, 1, 3)
            
            self.a1_input = self._create_parameter_input("a1系数:", 2, 0, 
                                                         QDoubleSpinBox(), 0.0, 0.0, 1e6, 6)
            self.a2_input = self._create_parameter_input("a2系数:", 2, 2, 
                                                         QDoubleSpinBox(), 1.0, 0.0, 1e6, 3)
            self.a3_input = self._create_parameter_input("a3系数:", 3, 0, 
                                                         QDoubleSpinBox(), 0.0, 0.0, 1e6, 6)
            self.a4_input = self._create_parameter_input("a4系数:", 3, 2, 
                                                         QDoubleSpinBox(), 1.0, 0.0, 1e6, 3)
            
            self.sigInit_input = self._create_parameter_input("初始应力(sigInit):", 4, 0, 
                                                              QDoubleSpinBox(), 0.0, -1e9, 1e9, 2)
            
        elif material_type == "Concrete02":
            # Concrete02混凝土材料参数
            self.fc_input = self._create_parameter_input("抗压强度(fc):", 0, 0, 
                                                         QDoubleSpinBox(), -25.0, -1e9, 0.0, 1)
            self.epsc0_input = self._create_parameter_input("峰值应变(epsc0):", 0, 2, 
                                                            QDoubleSpinBox(), -0.002, -1.0, 0.0, 4)
            
            self.epscu_input = self._create_parameter_input("极限应变(epscu):", 1, 0, 
                                                            QDoubleSpinBox(), -0.0035, -1.0, 0.0, 4)
            self.ft_input = self._create_parameter_input("抗拉强度(ft):", 1, 2, 
                                                         QDoubleSpinBox(), 2.5, 0.0, 1e6, 2)
            self.etu_input = self._create_parameter_input("极限拉应变(etu):", 2, 0, 
                                                          QDoubleSpinBox(), 0.004, 0.0, 1.0, 4)
            self.Ec_input = self._create_parameter_input("弹性模量(Ec):", 2, 2, 
                                                         QDoubleSpinBox(), 25000.0, 1.0, 1e12, 0)
            self.beta_input = self._create_parameter_input("退化参数(beta):", 3, 0, 
                                                           QDoubleSpinBox(), 0.1, 0.0, 1.0, 2)
            
        elif material_type == "Concrete04":
            # Concrete04混凝土Popovics材料参数
            self.params_layout.addWidget(QLabel("抗压强度(fc):"), 0, 0)
            self.fc_input = QDoubleSpinBox()
            self.fc_input.setDecimals(1)
            self.fc_input.setMinimum(-1e9)
            self.fc_input.setMaximum(0.0)
            self.fc_input.setValue(-25.0)  # 默认值
            self.params_layout.addWidget(self.fc_input, 0, 1)
            
            self.params_layout.addWidget(QLabel("峰值应变(epsc0):"), 0, 2)
            self.epsc0_input = QDoubleSpinBox()
            self.epsc0_input.setDecimals(4)
            self.epsc0_input.setMinimum(-1.0)
            self.epsc0_input.setMaximum(0.0)
            self.epsc0_input.setValue(-0.002)  # 默认值
            self.params_layout.addWidget(self.epsc0_input, 0, 3)
            
            self.params_layout.addWidget(QLabel("弹性模量(Ec):"), 1, 0)
            self.Ec_input = QDoubleSpinBox()
            self.Ec_input.setDecimals(0)
            self.Ec_input.setMinimum(1.0)
            self.Ec_input.setMaximum(1e12)
            self.Ec_input.setValue(25000.0)  # 默认值
            self.params_layout.addWidget(self.Ec_input, 1, 1)
            
            self.params_layout.addWidget(QLabel("抗拉强度(ft):"), 1, 2)
            self.ft_input = QDoubleSpinBox()
            self.ft_input.setDecimals(2)
            self.ft_input.setMinimum(0.0)
            self.ft_input.setMaximum(1e6)
            self.ft_input.setValue(2.5)  # 默认值
            self.params_layout.addWidget(self.ft_input, 1, 3)
            
            self.params_layout.addWidget(QLabel("极限拉应变(etu):"), 2, 0)
            self.etu_input = QDoubleSpinBox()
            self.etu_input.setDecimals(4)
            self.etu_input.setMinimum(0.0)
            self.etu_input.setMaximum(1.0)
            self.etu_input.setValue(0.004)  # 默认值
            self.params_layout.addWidget(self.etu_input, 2, 1)
            
            self.params_layout.addWidget(QLabel("退化参数(beta):"), 2, 2)
            self.beta_input = QDoubleSpinBox()
            self.beta_input.setDecimals(2)
            self.beta_input.setMinimum(0.0)
            self.beta_input.setMaximum(1.0)
            self.beta_input.setValue(0.1)  # 默认值
            self.params_layout.addWidget(self.beta_input, 2, 3)
            
            self.params_layout.addWidget(QLabel("压应变软化参数(es):"), 3, 0)
            self.es_input = QDoubleSpinBox()
            self.es_input.setDecimals(1)
            self.es_input.setMinimum(0.1)
            self.es_input.setMaximum(10.0)
            self.es_input.setValue(2.0)  # 默认值
            self.params_layout.addWidget(self.es_input, 3, 1)
            
        elif material_type == "Elastic":
            # 弹性材料参数
            self.params_layout.addWidget(QLabel("弹性模量(E):"), 0, 0)
            self.E_input = QDoubleSpinBox()
            self.E_input.setDecimals(0)
            self.E_input.setMinimum(1.0)
            self.E_input.setMaximum(1e12)
            self.E_input.setValue(200000.0)  # 默认值
            self.params_layout.addWidget(self.E_input, 0, 1)
            
            self.params_layout.addWidget(QLabel("泊松比(nu):"), 0, 2)
            self.nu_input = QDoubleSpinBox()
            self.nu_input.setDecimals(3)
            self.nu_input.setMinimum(0.0)
            self.nu_input.setMaximum(0.5)
            self.nu_input.setValue(0.3)  # 默认值
            self.params_layout.addWidget(self.nu_input, 0, 3)
            
    def _on_element_type_changed(self, element_type):
        """单元类型变化时更新参数输入区域"""
        # 清空现有参数输入
        for i in reversed(range(self.element_params_layout.count())):
            child = self.element_params_layout.itemAt(i).widget()
            if child:
                child.deleteLater()
        
        if element_type == "ZeroLength":
            # ZeroLength单元参数
            self.element_params_layout.addWidget(QLabel("材料标签:"), 0, 0)
            self.element_mat_tags_input = QLineEdit()
            self.element_mat_tags_input.setPlaceholderText("用逗号分隔，如: 1,2,3")
            self.element_params_layout.addWidget(self.element_mat_tags_input, 0, 1)
            
            self.element_params_layout.addWidget(QLabel("方向参数:"), 0, 2)
            self.element_dirs_input = QLineEdit()
            self.element_dirs_input.setPlaceholderText("用逗号分隔，如: 1,2,3")
            self.element_params_layout.addWidget(self.element_dirs_input, 0, 3)
            
            self.element_params_layout.addWidget(QLabel("瑞利阻尼:"), 1, 0)
            self.element_do_rayleigh_cb = QCheckBox("启用")
            self.element_params_layout.addWidget(self.element_do_rayleigh_cb, 1, 1)
            
            self.element_params_layout.addWidget(QLabel("阻尼标志:"), 1, 2)
            self.element_r_flag_input = QSpinBox()
            self.element_r_flag_input.setMinimum(0)
            self.element_r_flag_input.setMaximum(1)
            self.element_r_flag_input.setValue(0)
            self.element_params_layout.addWidget(self.element_r_flag_input, 1, 3)
            
        elif element_type == "TwoNodeLink":
            # TwoNodeLink单元参数
            self.element_params_layout.addWidget(QLabel("材料标签:"), 0, 0)
            self.element_mat_tags_input = QLineEdit()
            self.element_mat_tags_input.setPlaceholderText("用逗号分隔，如: 1,2,3")
            self.element_params_layout.addWidget(self.element_mat_tags_input, 0, 1)
            
            self.element_params_layout.addWidget(QLabel("方向参数:"), 0, 2)
            self.element_dirs_input = QLineEdit()
            self.element_dirs_input.setPlaceholderText("用逗号分隔，如: 1,2,3")
            self.element_params_layout.addWidget(self.element_dirs_input, 0, 3)
            
            self.element_params_layout.addWidget(QLabel("质量:"), 1, 0)
            self.element_mass_input = QDoubleSpinBox()
            self.element_mass_input.setDecimals(6)
            self.element_mass_input.setMinimum(0.0)
            self.element_mass_input.setMaximum(1e12)
            self.element_mass_input.setValue(0.0)
            self.element_params_layout.addWidget(self.element_mass_input, 1, 1)
            
            self.element_params_layout.addWidget(QLabel("瑞利阻尼:"), 1, 2)
            self.element_do_rayleigh_cb = QCheckBox("启用")
            self.element_params_layout.addWidget(self.element_do_rayleigh_cb, 1, 3)
            
        elif element_type == "Truss":
            # Truss单元参数
            self.element_params_layout.addWidget(QLabel("截面积(A):"), 0, 0)
            self.element_A_input = QDoubleSpinBox()
            self.element_A_input.setDecimals(4)
            self.element_A_input.setMinimum(0.001)
            self.element_A_input.setMaximum(1e12)
            self.element_A_input.setValue(1.0)
            self.element_params_layout.addWidget(self.element_A_input, 0, 1)
            
            self.element_params_layout.addWidget(QLabel("材料标签:"), 0, 2)
            self.element_mat_tag_input = QSpinBox()
            self.element_mat_tag_input.setMinimum(1)
            self.element_mat_tag_input.setMaximum(999999)
            self.element_mat_tag_input.setValue(1)
            self.element_params_layout.addWidget(self.element_mat_tag_input, 0, 3)
            
            self.element_params_layout.addWidget(QLabel("密度(rho):"), 1, 0)
            self.element_rho_input = QDoubleSpinBox()
            self.element_rho_input.setDecimals(2)
            self.element_rho_input.setMinimum(0.0)
            self.element_rho_input.setMaximum(10000.0)
            self.element_rho_input.setValue(0.0)
            self.element_params_layout.addWidget(self.element_rho_input, 1, 1)
            
            self.element_params_layout.addWidget(QLabel("一致质量矩阵:"), 1, 2)
            self.element_c_mass_cb = QCheckBox("启用")
            self.element_params_layout.addWidget(self.element_c_mass_cb, 1, 3)
            
        elif element_type == "ElasticBeamColumn":
            # ElasticBeamColumn单元参数
            self.element_params_layout.addWidget(QLabel("截面积(Area):"), 0, 0)
            self.element_Area_input = QDoubleSpinBox()
            self.element_Area_input.setDecimals(4)
            self.element_Area_input.setMinimum(0.001)
            self.element_Area_input.setMaximum(1e12)
            self.element_Area_input.setValue(1.0)
            self.element_params_layout.addWidget(self.element_Area_input, 0, 1)
            
            self.element_params_layout.addWidget(QLabel("弹性模量(E):"), 0, 2)
            self.element_E_mod_input = QDoubleSpinBox()
            self.element_E_mod_input.setDecimals(0)
            self.element_E_mod_input.setMinimum(1.0)
            self.element_E_mod_input.setMaximum(1e12)
            self.element_E_mod_input.setValue(200000.0)
            self.element_params_layout.addWidget(self.element_E_mod_input, 0, 3)
            
            self.element_params_layout.addWidget(QLabel("惯性矩(Iz):"), 1, 0)
            self.element_Iz_input = QDoubleSpinBox()
            self.element_Iz_input.setDecimals(6)
            self.element_Iz_input.setMinimum(0.000001)
            self.element_Iz_input.setMaximum(1e12)
            self.element_Iz_input.setValue(1.0)
            self.element_params_layout.addWidget(self.element_Iz_input, 1, 1)
            
            self.element_params_layout.addWidget(QLabel("变换标签:"), 1, 2)
            self.element_transf_tag_input = QSpinBox()
            self.element_transf_tag_input.setMinimum(1)
            self.element_transf_tag_input.setMaximum(999999)
            self.element_transf_tag_input.setValue(1)
            self.element_params_layout.addWidget(self.element_transf_tag_input, 1, 3)
            
        elif element_type == "DispBeamColumn":
            # DispBeamColumn单元参数
            self.element_params_layout.addWidget(QLabel("变换标签:"), 0, 0)
            self.element_transf_tag_input = QSpinBox()
            self.element_transf_tag_input.setMinimum(1)
            self.element_transf_tag_input.setMaximum(999999)
            self.element_transf_tag_input.setValue(1)
            self.element_params_layout.addWidget(self.element_transf_tag_input, 0, 1)
            
            self.element_params_layout.addWidget(QLabel("积分标签:"), 0, 2)
            self.element_integration_tag_input = QSpinBox()
            self.element_integration_tag_input.setMinimum(1)
            self.element_integration_tag_input.setMaximum(999999)
            self.element_integration_tag_input.setValue(1)
            self.element_params_layout.addWidget(self.element_integration_tag_input, 0, 3)
            
            self.element_params_layout.addWidget(QLabel("质量:"), 1, 0)
            self.element_mass_input = QDoubleSpinBox()
            self.element_mass_input.setDecimals(6)
            self.element_mass_input.setMinimum(0.0)
            self.element_mass_input.setMaximum(1e12)
            self.element_mass_input.setValue(0.0)
            self.element_params_layout.addWidget(self.element_mass_input, 1, 1)
            
            self.element_params_layout.addWidget(QLabel("一致质量矩阵:"), 1, 2)
            self.element_c_mass_cb = QCheckBox("启用")
            self.element_params_layout.addWidget(self.element_c_mass_cb, 1, 3)
            
        elif element_type == "ForceBeamColumn":
            # ForceBeamColumn单元参数
            self.element_params_layout.addWidget(QLabel("变换标签:"), 0, 0)
            self.element_transf_tag_input = QSpinBox()
            self.element_transf_tag_input.setMinimum(1)
            self.element_transf_tag_input.setMaximum(999999)
            self.element_transf_tag_input.setValue(1)
            self.element_params_layout.addWidget(self.element_transf_tag_input, 0, 1)
            
            self.element_params_layout.addWidget(QLabel("积分标签:"), 0, 2)
            self.element_integration_tag_input = QSpinBox()
            self.element_integration_tag_input.setMinimum(1)
            self.element_integration_tag_input.setMaximum(999999)
            self.element_integration_tag_input.setValue(1)
            self.element_params_layout.addWidget(self.element_integration_tag_input, 0, 3)
            
            self.element_params_layout.addWidget(QLabel("最大迭代次数:"), 1, 0)
            self.element_max_iter_input = QSpinBox()
            self.element_max_iter_input.setMinimum(1)
            self.element_max_iter_input.setMaximum(100)
            self.element_max_iter_input.setValue(10)
            self.element_params_layout.addWidget(self.element_max_iter_input, 1, 1)
            
            self.element_params_layout.addWidget(QLabel("收敛容差:"), 1, 2)
            self.element_tol_input = QDoubleSpinBox()
            self.element_tol_input.setDecimals(12)
            self.element_tol_input.setMinimum(1e-15)
            self.element_tol_input.setMaximum(1.0)
            self.element_tol_input.setValue(1e-12)
            self.element_params_layout.addWidget(self.element_tol_input, 1, 3)
            
            self.element_params_layout.addWidget(QLabel("质量:"), 2, 0)
            self.element_mass_input = QDoubleSpinBox()
            self.element_mass_input.setDecimals(6)
            self.element_mass_input.setMinimum(0.0)
            self.element_mass_input.setMaximum(1e12)
            self.element_mass_input.setValue(0.0)
            self.element_params_layout.addWidget(self.element_mass_input, 2, 1)
            

            


            
    def _on_preview_material_command(self):
        """预览OpenSeesPy材料创建命令"""
        try:
            material_type = self.material_type_combo.currentText()
            material_id = self.material_id_input.value()
            
            command = ""
            if material_type == "Steel02":
                fy = self.fy_input.value()
                E0 = self.E0_input.value()
                b = self.b_input.value()
                params_text = self.params_input.text().strip()
                a1 = self.a1_input.value()
                a2 = self.a2_input.value()
                a3 = self.a3_input.value()
                a4 = self.a4_input.value()
                sigInit = self.sigInit_input.value()
                
                params_str = f", {params_text}" if params_text else ""
                command = f"uniaxialMaterial('Steel02', {material_id}, {fy}, {E0}, {b}{params_str}, a1={a1}, a2={a2}, a3={a3}, a4={a4}, sigInit={sigInit})"
                
            elif material_type == "Concrete02":
                fc = self.fc_input.value()
                epsc0 = self.epsc0_input.value()
                epscu = self.epscu_input.value()
                ft = self.ft_input.value()
                etu = self.etu_input.value()
                Ec = self.Ec_input.value()
                beta = self.beta_input.value()
                command = f"uniaxialMaterial('Concrete02', {material_id}, {fc}, {epsc0}, {epscu}, {ft}, {etu}, Ec={Ec}, beta={beta})"
                
            elif material_type == "Concrete04":
                fc = self.fc_input.value()
                epsc0 = self.epsc0_input.value()
                Ec = self.Ec_input.value()
                ft = self.ft_input.value()
                etu = self.etu_input.value()
                beta = self.beta_input.value()
                es = self.es_input.value()
                command = f"uniaxialMaterial('Concrete04', {material_id}, {fc}, {epsc0}, Ec={Ec}, ft={ft}, etu={etu}, beta={beta}, es={es})"
                
            elif material_type == "Elastic":
                E = self.E_input.value()
                nu = self.nu_input.value()
                command = f"uniaxialMaterial('Elastic', {material_id}, {E}, {nu})"
            
            QMessageBox.information(self, "OpenSeesPy命令预览", 
                                   f"生成的OpenSeesPy命令:\n\n{command}")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"生成命令时出错: {str(e)}")
            
    def _on_create_material(self):
        """创建材料"""
        try:
            material_type = self.material_type_combo.currentText()
            name = self.material_name_input.text() or f"{material_type}_material"
            material_id = self.material_id_input.value()
            
            kwargs = {}
            
            if material_type == "Steel02":
                fy = self.fy_input.value()
                E0 = self.E0_input.value()
                b = self.b_input.value()
                params_text = self.params_input.text().strip()
                a1 = self.a1_input.value()
                a2 = self.a2_input.value()
                a3 = self.a3_input.value()
                a4 = self.a4_input.value()
                sigInit = self.sigInit_input.value()
                
                if params_text:
                    kwargs = {'Fy': fy, 'E0': E0, 'b': b, 'a1': a1, 'a2': a2, 'a3': a3, 'a4': a4, 'sigInit': sigInit, 'params': params_text}
                else:
                    kwargs = {'Fy': fy, 'E0': E0, 'b': b, 'a1': a1, 'a2': a2, 'a3': a3, 'a4': a4, 'sigInit': sigInit}
                
            elif material_type == "Concrete02":
                fc = self.fc_input.value()
                epsc0 = self.epsc0_input.value()
                epscu = self.epscu_input.value()
                ft = self.ft_input.value()
                etu = self.etu_input.value()
                Ec = self.Ec_input.value()
                beta = self.beta_input.value()
                kwargs = {'fc': fc, 'epsc0': epsc0, 'epscu': epscu, 'ft': ft, 'etu': etu, 'Ec': Ec, 'beta': beta}
                
            elif material_type == "Concrete04":
                fc = self.fc_input.value()
                epsc0 = self.epsc0_input.value()
                Ec = self.Ec_input.value()
                ft = self.ft_input.value()
                etu = self.etu_input.value()
                beta = self.beta_input.value()
                es = self.es_input.value()
                kwargs = {'fc': fc, 'epsc0': epsc0, 'Ec': Ec, 'ft': ft, 'etu': etu, 'beta': beta, 'es': es}
                
            elif material_type == "Elastic":
                E = self.E_input.value()
                nu = self.nu_input.value()
                kwargs = {'E': E, 'nu': nu}
            
            success, error, material = self.controller.create_material(
                material_type, name, material_id=material_id, **kwargs
            )
            
            if success:
                QMessageBox.information(self, "成功", f"材料 {name} 创建成功")
                self._update_materials_table()
            else:
                QMessageBox.warning(self, "错误", f"材料创建失败: {error}")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"创建材料时出错: {str(e)}")
        
    def _on_clear_materials(self):
        """清空所有材料"""
        reply = QMessageBox.question(
            self, "确认", "确定要删除所有材料吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.controller.clear_materials()
            self._update_materials_table()
            
    def _on_create_element(self):
        """创建单元"""
        element_type = self.element_type_combo.currentText()
        element_id = self.element_id_input.value()
        node_ids = [self.node1_input.value(), self.node2_input.value()]
        
        kwargs = {}
        
        # 根据单元类型获取参数
        if element_type == "ZeroLength":
            mat_tags_text = self.element_mat_tags_input.text().strip()
            dirs_text = self.element_dirs_input.text().strip()
            do_rayleigh = self.element_do_rayleigh_cb.isChecked()
            r_flag = self.element_r_flag_input.value()
            
            if not mat_tags_text or not dirs_text:
                QMessageBox.warning(self, "错误", "ZeroLength单元需要材料标签和方向参数")
                return
            
            try:
                mat_tags = [int(x.strip()) for x in mat_tags_text.split(',')]
                dirs = [int(x.strip()) for x in dirs_text.split(',')]
            except ValueError:
                QMessageBox.warning(self, "错误", "材料标签和方向参数必须是整数，用逗号分隔")
                return
            
            kwargs.update({
                'mat_tags': mat_tags,
                'dirs': dirs,
                'do_rayleigh': do_rayleigh,
                'r_flag': r_flag
            })
            
        elif element_type == "TwoNodeLink":
            mat_tags_text = self.element_mat_tags_input.text().strip()
            dirs_text = self.element_dirs_input.text().strip()
            mass = self.element_mass_input.value()
            do_rayleigh = self.element_do_rayleigh_cb.isChecked()
            
            if not mat_tags_text or not dirs_text:
                QMessageBox.warning(self, "错误", "TwoNodeLink单元需要材料标签和方向参数")
                return
            
            try:
                mat_tags = [int(x.strip()) for x in mat_tags_text.split(',')]
                dirs = [int(x.strip()) for x in dirs_text.split(',')]
            except ValueError:
                QMessageBox.warning(self, "错误", "材料标签和方向参数必须是整数，用逗号分隔")
                return
            
            kwargs.update({
                'mat_tags': mat_tags,
                'dirs': dirs,
                'mass': mass,
                'do_rayleigh': do_rayleigh
            })
            
        elif element_type == "Truss":
            A = self.element_A_input.value()
            mat_tag = self.element_mat_tag_input.value()
            rho = self.element_rho_input.value()
            c_mass = self.element_c_mass_cb.isChecked()
            
            kwargs.update({
                'A': A,
                'mat_tag': mat_tag,
                'rho': rho,
                'c_mass': c_mass
            })
            
        elif element_type == "ElasticBeamColumn":
            Area = self.element_Area_input.value()
            E_mod = self.element_E_mod_input.value()
            Iz = self.element_Iz_input.value()
            transf_tag = self.element_transf_tag_input.value()
            
            kwargs.update({
                'Area': Area,
                'E_mod': E_mod,
                'Iz': Iz,
                'transf_tag': transf_tag
            })
            
        elif element_type == "DispBeamColumn":
            transf_tag = self.element_transf_tag_input.value()
            integration_tag = self.element_integration_tag_input.value()
            mass = self.element_mass_input.value()
            c_mass = self.element_c_mass_cb.isChecked()
            
            kwargs.update({
                'transf_tag': transf_tag,
                'integration_tag': integration_tag,
                'mass': mass,
                'c_mass': c_mass
            })
            
        elif element_type == "ForceBeamColumn":
            transf_tag = self.element_transf_tag_input.value()
            integration_tag = self.element_integration_tag_input.value()
            max_iter = self.element_max_iter_input.value()
            tol = self.element_tol_input.value()
            mass = self.element_mass_input.value()
            
            kwargs.update({
                'transf_tag': transf_tag,
                'integration_tag': integration_tag,
                'max_iter': max_iter,
                'tol': tol,
                'mass': mass
            })
        
        success, error, element = self.controller.create_element(
            element_type, element_id, node_ids, **kwargs
        )
        
        if success:
            QMessageBox.information(self, "成功", f"单元 {element_id} 创建成功")
            self._update_elements_table()
            self._update_3d_view()  # 更新3D视图
        else:
            QMessageBox.warning(self, "错误", f"单元创建失败: {error}")
            
    def _on_preview_element_command(self):
        """预览OpenSeesPy单元创建命令"""
        try:
            element_type = self.element_type_combo.currentText()
            element_id = self.element_id_input.value()
            node_ids = [self.node1_input.value(), self.node2_input.value()]
            
            command = ""
            
            if element_type == "ZeroLength":
                mat_tags_text = self.element_mat_tags_input.text().strip()
                dirs_text = self.element_dirs_input.text().strip()
                do_rayleigh = self.element_do_rayleigh_cb.isChecked()
                r_flag = self.element_r_flag_input.value()
                
                if not mat_tags_text or not dirs_text:
                    QMessageBox.warning(self, "错误", "ZeroLength单元需要材料标签和方向参数")
                    return
                
                mat_tags = ','.join(mat_tags_text.split())
                dirs = ','.join(dirs_text.split())
                
                rayleigh_str = ", '-doRayleigh', 1" if do_rayleigh else ""
                command = f"ops.element('zeroLength', {element_id}, {node_ids[0]}, {node_ids[1]}, '-mat', {mat_tags}, '-dir', {dirs}{rayleigh_str})"
                
            elif element_type == "TwoNodeLink":
                mat_tags_text = self.element_mat_tags_input.text().strip()
                dirs_text = self.element_dirs_input.text().strip()
                mass = self.element_mass_input.value()
                do_rayleigh = self.element_do_rayleigh_cb.isChecked()
                
                if not mat_tags_text or not dirs_text:
                    QMessageBox.warning(self, "错误", "TwoNodeLink单元需要材料标签和方向参数")
                    return
                
                mat_tags = ','.join(mat_tags_text.split())
                dirs = ','.join(dirs_text.split())
                
                mass_str = f", '-mass', {mass}" if mass > 0 else ""
                rayleigh_str = ", '-doRayleigh', 1" if do_rayleigh else ""
                command = f"ops.element('twoNodeLink', {element_id}, {node_ids[0]}, {node_ids[1]}, '-mat', {mat_tags}, '-dir', {dirs}{mass_str}{rayleigh_str})"
                
            elif element_type == "Truss":
                A = self.element_A_input.value()
                mat_tag = self.element_mat_tag_input.value()
                rho = self.element_rho_input.value()
                c_mass = self.element_c_mass_cb.isChecked()
                
                rho_str = f", '-rho', {rho}" if rho > 0 else ""
                c_mass_str = ", '-cMass'" if c_mass else ""
                command = f"ops.element('Truss', {element_id}, {node_ids[0]}, {node_ids[1]}, {A}, {mat_tag}{rho_str}{c_mass_str})"
                
            elif element_type == "ElasticBeamColumn":
                Area = self.element_Area_input.value()
                E_mod = self.element_E_mod_input.value()
                Iz = self.element_Iz_input.value()
                transf_tag = self.element_transf_tag_input.value()
                
                command = f"ops.element('elasticBeamColumn', {element_id}, {node_ids[0]}, {node_ids[1]}, {Area}, {E_mod}, {Iz}, {transf_tag})"
                
            elif element_type == "DispBeamColumn":
                transf_tag = self.element_transf_tag_input.value()
                integration_tag = self.element_integration_tag_input.value()
                mass = self.element_mass_input.value()
                c_mass = self.element_c_mass_cb.isChecked()
                
                mass_str = f", '-mass', {mass}" if mass > 0 else ""
                c_mass_str = ", '-cMass'" if c_mass else ""
                command = f"ops.element('dispBeamColumn', {element_id}, {node_ids[0]}, {node_ids[1]}, {transf_tag}, {integration_tag}{mass_str}{c_mass_str})"
                
            elif element_type == "ForceBeamColumn":
                transf_tag = self.element_transf_tag_input.value()
                integration_tag = self.element_integration_tag_input.value()
                max_iter = self.element_max_iter_input.value()
                tol = self.element_tol_input.value()
                mass = self.element_mass_input.value()
                
                iter_str = f", '-iter', {max_iter}, {tol}" if (max_iter != 10 or tol != 1e-12) else ""
                mass_str = f", '-mass', {mass}" if mass > 0 else ""
                command = f"ops.element('forceBeamColumn', {element_id}, {node_ids[0]}, {node_ids[1]}, {transf_tag}, {integration_tag}{iter_str}{mass_str})"
            
            # 显示预览对话框
            dialog = QDialog(self)
            dialog.setWindowTitle(f"单元命令预览 - {element_type}")
            dialog.setModal(True)
            dialog.resize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            # 标题
            title_label = QLabel(f"单元类型: {element_type}")
            title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            layout.addWidget(title_label)
            
            # 命令文本框
            text_edit = QTextEdit()
            text_edit.setPlainText(command)
            text_edit.setReadOnly(True)
            text_edit.setFont(QFont("Courier", 10))
            layout.addWidget(text_edit)
            
            # 复制按钮
            btn_layout = QHBoxLayout()
            copy_btn = QPushButton("复制命令")
            copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(command))
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(dialog.accept)
            btn_layout.addWidget(copy_btn)
            btn_layout.addStretch()
            btn_layout.addWidget(close_btn)
            
            layout.addLayout(btn_layout)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"预览命令失败: {str(e)}")
            
    def _on_import_elements_csv(self):
        """从多页文件导入单元"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", "Excel Files (*.xlsx *.xls);;CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            success, error, stats = self.controller.import_elements_from_multisheet_file(file_path)
            
            if success:
                # 显示统计信息
                stats_text = "导入成功！\n"
                for element_type, count in stats.items():
                    stats_text += f"{element_type}: {count} 个单元\n"
                QMessageBox.information(self, "成功", stats_text)
                self._update_elements_table()
            else:
                QMessageBox.warning(self, "错误", f"导入失败: {error}")
                
    def _on_export_elements_csv(self):
        """导出单元到多页文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", "", "Excel Files (*.xlsx);;CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            success, error = self.controller.export_elements_to_multisheet_file(file_path)
            
            if success:
                QMessageBox.information(self, "成功", f"导出成功: {error}")
            else:
                QMessageBox.warning(self, "错误", f"导出失败: {error}")
        
    def _on_create_element_template(self):
        """创建单元模板"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存模板", "", "Excel Files (*.xlsx);;CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            success, error = self.controller.create_element_template(file_path)
            
            if success:
                QMessageBox.information(self, "成功", f"模板创建成功: {error}")
            else:
                QMessageBox.warning(self, "错误", f"模板创建失败: {error}")
            
    def _on_clear_elements(self):
        """清空所有单元"""
        reply = QMessageBox.question(
            self, "确认", "确定要删除所有单元吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.controller.clear_elements()
            self._update_elements_table()
            self._update_3d_view()  # 更新3D视图
            
    def _on_refresh_sections(self):
        """刷新截面列表"""
        self._update_sections_list()
        
    def _on_export_section_code(self):
        """导出截面代码"""
        selected_items = self.sections_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择要导出的截面")
            return
            
        # TODO: 实现截面代码导出
        QMessageBox.information(self, "提示", "截面代码导出功能待实现")
        
    def _on_section_properties(self):
        """显示截面属性"""
        selected_items = self.sections_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择截面")
            return
            
        # TODO: 实现截面属性显示
        QMessageBox.information(self, "提示", "截面属性显示功能待实现")
        
    def _on_refresh_code_preview(self):
        """刷新代码预览"""
        self._update_code_preview()
        
    def _on_export_to_file(self):
        """导出到文件"""
        success, message = self.controller.export_complete_model()
        
        if success:
            QMessageBox.information(self, "成功", message)
        else:
            QMessageBox.warning(self, "错误", message)
            
    def _on_data_changed(self, data_type: str):
        """数据变化回调"""
        self._update_display()
        self.model_changed.emit()
        
    def _on_export_completed(self, file_path: str):
        """导出完成回调"""
        QMessageBox.information(self, "成功", f"代码已导出到: {file_path}")
        self.export_completed.emit(file_path)
        
    def _on_validation_error(self, error_msg: str):
        """验证错误回调"""
        QMessageBox.warning(self, "验证错误", error_msg)
        
    def _update_model_summary(self):
        """更新模型摘要"""
        summary = self.controller.get_model_summary()
        
        if 'error' in summary:
            self.model_summary.setText(f"错误: {summary['error']}")
            return
            
        model_info = summary.get('model_settings', {})
        stats = summary.get('statistics', {})
        validation = summary.get('validation', {})
        
        summary_text = f"""模型维度: {model_info.get('dimension', 'N/A')}D
自由度数量: {model_info.get('dof_count', 'N/A')}
节点数量: {stats.get('nodes', 0)}
材料数量: {stats.get('materials', 0)}
单元数量: {stats.get('elements', 0)}
截面数量: {stats.get('sections', 0)}

模型状态: {'有效' if validation.get('is_valid', False) else '无效'}
警告数量: {len(validation.get('warnings', []))}
错误数量: {len(validation.get('errors', []))}
"""
        
        self.model_summary.setText(summary_text)
        
    def _update_nodes_table(self):
        """更新节点表格"""
        nodes = self.controller.get_all_nodes()
        node_ids = self.controller.get_all_node_ids()
        
        self.nodes_table.setRowCount(len(nodes))
        
        for row, (node_id, node) in enumerate(zip(node_ids, nodes)):
            self.nodes_table.setItem(row, 0, QTableWidgetItem(str(node_id)))
            self.nodes_table.setItem(row, 1, QTableWidgetItem(f"{node.x:.3f}"))
            self.nodes_table.setItem(row, 2, QTableWidgetItem(f"{node.y:.3f}"))
            self.nodes_table.setItem(row, 3, QTableWidgetItem(f"{node.z:.3f}"))
            # 显示6个自由度的质量：UX, UY, UZ, RX, RY, RZ
            self.nodes_table.setItem(row, 4, QTableWidgetItem(f"{node.mass[0]:.6f}"))  # UX
            self.nodes_table.setItem(row, 5, QTableWidgetItem(f"{node.mass[1]:.6f}"))  # UY
            self.nodes_table.setItem(row, 6, QTableWidgetItem(f"{node.mass[2]:.6f}"))  # UZ
            self.nodes_table.setItem(row, 7, QTableWidgetItem(f"{node.mass[3]:.6f}"))  # RX
            self.nodes_table.setItem(row, 8, QTableWidgetItem(f"{node.mass[4]:.6f}"))  # RY
            self.nodes_table.setItem(row, 9, QTableWidgetItem(f"{node.mass[5]:.6f}"))  # RZ
            
    def _update_materials_table(self):
        """更新材料表格"""
        materials = self.controller.get_all_materials()
        material_ids = self.controller.get_all_material_ids()
        
        self.materials_table.setRowCount(len(materials))
        
        for row, (material_id, material) in enumerate(zip(material_ids, materials)):
            self.materials_table.setItem(row, 0, QTableWidgetItem(str(material_id)))
            self.materials_table.setItem(row, 1, QTableWidgetItem(material.name))
            self.materials_table.setItem(row, 2, QTableWidgetItem(material.type))
            self.materials_table.setItem(row, 3, QTableWidgetItem(str(material.__dict__)))
            
    def _update_elements_table(self):
        """更新单元表格"""
        elements = self.controller.get_all_elements()
        element_ids = self.controller.get_all_element_ids()
        
        self.elements_table.setRowCount(len(elements))
        
        for row, (element_id, element) in enumerate(zip(element_ids, elements)):
            self.elements_table.setItem(row, 0, QTableWidgetItem(str(element_id)))
            self.elements_table.setItem(row, 1, QTableWidgetItem(element.type))
            self.elements_table.setItem(row, 2, QTableWidgetItem(str(element.node_ids)))
            self.elements_table.setItem(row, 3, QTableWidgetItem(str(getattr(element, 'mat_tag', 'N/A'))))
            self.elements_table.setItem(row, 4, QTableWidgetItem(str(element.__dict__)))
            
    def _update_sections_list(self):
        """更新截面列表"""
        sections = self.controller.get_all_sections()
        
        self.sections_list.clear()
        
        for section in sections:
            item = QListWidgetItem(f"截面 {section.id}: {section.name}")
            item.setData(Qt.UserRole, section.id)
            self.sections_list.addItem(item)
            
        # 更新截面详情
        if sections:
            section = sections[0]
            details = f"""ID: {section.id}
名称: {section.name}
形状数量: {len(section.shapes)}
纤维数量: {len(section.fibers) if section.fibers else 0}
扭转刚度: {section.GJ}
创建时间: {section.created_time}
更新时间: {section.updated_time}"""
            
            self.section_details.setText(details)
            
    def _update_code_preview(self):
        """更新代码预览"""
        code = self.controller.generate_model_preview()
        self.code_preview.setText(code)