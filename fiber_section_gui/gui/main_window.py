from PyQt5.QtWidgets import (QMainWindow, QSplitter, QVBoxLayout, QHBoxLayout,
                             QWidget, QToolBar, QAction, QMessageBox, QFileDialog,
                             QDialog, QDialogButtonBox, QVBoxLayout, QCheckBox,
                             QScrollArea, QLabel, QListWidget, QListWidgetItem,
                             QHBoxLayout, QPushButton, QTabWidget)
from PyQt5.QtCore import Qt, QSize
from gui.canvas import Canvas
from gui.control_panel import ControlPanel
from gui.openseespy_panel import OpenSeesPyPanel
from gui.openseespy_3d_view import OpenSeesPy3DView
from data.data_manager import DataManager
from meshing.mesh import MeshGenerator

class SectionSelectionDialog(QDialog):
    """选择截面的对话框"""
    def __init__(self, sections, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择要导出的截面")
        self.setMinimumSize(400, 300)
        self.sections = sections
        
        # 创建界面
        self._create_ui()
        
    def _create_ui(self):
        layout = QVBoxLayout(self)
        
        # 添加说明文字
        layout.addWidget(QLabel("选择要导出的截面（可多选）:"))
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 添加复选框
        self.section_checkboxes = []
        for section in self.sections:
            checkbox = QCheckBox(f"截面 {section.id}: {section.name}")
            checkbox.setChecked(True)  # 默认全选
            self.section_checkboxes.append(checkbox)
            scroll_layout.addWidget(checkbox)
        
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
        
        # 添加按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            self
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # 添加快捷按钮
        button_layout = QHBoxLayout()
        btn_select_all = QPushButton("全选")
        btn_select_all.clicked.connect(self._select_all)
        btn_select_none = QPushButton("全不选")
        btn_select_none.clicked.connect(self._select_none)
        button_layout.addWidget(btn_select_all)
        button_layout.addWidget(btn_select_none)
        layout.addLayout(button_layout)
    
    def _select_all(self):
        """全选"""
        for checkbox in self.section_checkboxes:
            checkbox.setChecked(True)
    
    def _select_none(self):
        """全不选"""
        for checkbox in self.section_checkboxes:
            checkbox.setChecked(False)
    
    def get_selected_sections(self):
        """获取选中的截面"""
        selected_ids = []
        for i, checkbox in enumerate(self.section_checkboxes):
            if checkbox.isChecked():
                selected_ids.append(self.sections[i].id)
        return selected_ids


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("纤维截面网格划分GUI")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化数据管理器
        self.data_manager = DataManager()
        
        # 初始化网格生成器
        self.mesh_generator = MeshGenerator()
        
        # 创建视图组件
        self._create_views()
        
        # 创建主布局
        self._create_main_layout()
        
        # 创建工具栏
        self._create_toolbar()
        
        # 连接信号
        self._connect_signals()
        
        # 初始显示纤维截面视图
        self._switch_to_section_view()
         
    def _create_views(self):
        """创建所有视图组件"""
        # 2D纤维截面视图
        self.canvas = Canvas(self.data_manager)
        
        # 3D OpenSeesPy建模视图
        self.openseespy_3d_view = OpenSeesPy3DView()
        
    def _switch_to_section_view(self):
        """切换到纤维截面视图"""
        # 清空左侧布局
        while self.left_layout.count():
            child = self.left_layout.takeAt(0)
            if child.widget():
                child.widget().hide()
                
        # 显示2D视图
        self.left_layout.addWidget(self.canvas)
        self.canvas.show()
        
        # 切换右侧标签页到纤维截面
        self.right_tabs.setCurrentIndex(0)
            
        self.statusBar().showMessage("已切换到纤维截面视图")
        
    def _switch_to_openseespy_view(self):
        """切换到OpenSeesPy建模视图"""
        # 清空左侧布局
        while self.left_layout.count():
            child = self.left_layout.takeAt(0)
            if child.widget():
                child.widget().hide()
                
        # 显示3D视图并更新数据
        self.left_layout.addWidget(self.openseespy_3d_view)
        
        # 从控制器更新模型数据
        if hasattr(self, 'openseespy_panel') and hasattr(self.openseespy_panel, 'controller'):
            self.openseespy_3d_view.update_from_controller(self.openseespy_panel.controller)
        
        self.openseespy_3d_view.show()
            
        # 切换右侧标签页到OpenSeesPy建模
        self.right_tabs.setCurrentIndex(1)
            
        self.statusBar().showMessage("已切换到OpenSeesPy建模视图")
         
    def _create_main_layout(self):
        # 创建主分割器
        main_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧视图区域（动态切换）
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout(self.left_widget)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 初始显示2D视图
        self.left_layout.addWidget(self.canvas)
        
        # 右侧面板区域（使用标签页）
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建右侧标签页
        self.right_tabs = QTabWidget()
        
        # 原始控制面板
        self.control_panel = ControlPanel(self.data_manager)
        self.right_tabs.addTab(self.control_panel, "纤维截面")
        
        # OpenSeesPy建模面板
        self.openseespy_panel = OpenSeesPyPanel(self.data_manager)
        self.right_tabs.addTab(self.openseespy_panel, "OpenSeesPy建模")
        
        right_layout.addWidget(self.right_tabs)
        
        # 添加到分割器
        main_splitter.addWidget(self.left_widget)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([800, 400])  # 设置初始大小
        
        # 设置主窗口中心部件
        self.setCentralWidget(main_splitter)
    
    def _create_toolbar(self):
        toolbar = QToolBar("工具栏")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)
        
        # 文件操作
        self.new_action = QAction("新建", self)
        self.open_action = QAction("打开", self)
        self.save_action = QAction("保存", self)
        self.export_action = QAction("导出", self)
        
        toolbar.addAction(self.new_action)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addAction(self.export_action)
        toolbar.addSeparator()
        
        # 视图控制
        self.zoom_in_action = QAction("放大", self)
        self.zoom_out_action = QAction("缩小", self)
        self.pan_action = QAction("平移", self)
        self.reset_view_action = QAction("重置视图", self)
        
        toolbar.addAction(self.zoom_in_action)
        toolbar.addAction(self.zoom_out_action)
        toolbar.addAction(self.pan_action)
        toolbar.addAction(self.reset_view_action)
        toolbar.addSeparator()
        
        # 显示切换
        self.show_grid_action = QAction("显示网格", self)
        self.show_fibers_action = QAction("显示纤维", self)
        self.show_materials_action = QAction("显示材料", self)
        
        toolbar.addAction(self.show_grid_action)
        toolbar.addAction(self.show_fibers_action)
        toolbar.addAction(self.show_materials_action)
    
    def _connect_signals(self):
        # 连接控制面板信号
        self.control_panel.btn_add_shape.clicked.connect(self._on_add_shape)
        self.control_panel.btn_generate_mesh.clicked.connect(self._on_generate_mesh)
        self.control_panel.btn_export_section.clicked.connect(self._on_export_section)
        self.control_panel.section_switched.connect(self._on_section_switched)
        self.control_panel.canvas_refresh.connect(self._on_canvas_refresh)
        
        # 连接新增的刷新信号
        self.control_panel.fiber_list_refresh.connect(self._on_fiber_list_refresh)
        self.control_panel.shape_list_refresh.connect(self._on_shape_list_refresh)
        
        # 连接右侧标签页切换信号
        self.right_tabs.currentChanged.connect(self._on_tab_changed)
        
        # 连接工具栏信号
        self.new_action.triggered.connect(self._on_new_project)
        self.open_action.triggered.connect(self._on_open_project)
        self.save_action.triggered.connect(self._on_save_project)
        self.export_action.triggered.connect(self._on_export_section)
        
        # 连接视图控制信号
        self.zoom_in_action.triggered.connect(self._on_zoom_in)
        self.zoom_out_action.triggered.connect(self._on_zoom_out)
        self.pan_action.triggered.connect(self._on_pan)
        self.reset_view_action.triggered.connect(self._on_reset_view)
        
    def _on_add_shape(self):
        # 获取形状参数
        shape_type = self.control_panel.geometry_tab.shape_type.currentText()
        params = self.control_panel.geometry_tab.get_shape_params()
        
        # 创建形状并添加到当前截面
        current_section = self.data_manager.get_current_section()
        
        # 使用数据管理器添加形状（包含操作记录）
        # 注意：这里不再直接调用current_section.add_shape，避免重复添加
        shape = current_section.create_shape(shape_type, params)
        
        if shape:
            self.data_manager.add_shape(current_section.id, shape)
        
        # 更新画布
        self.canvas.draw_shapes(current_section.get_shapes())
    
    def _on_generate_mesh(self):
        """生成网格事件处理"""
        # 验证前置条件
        if not self._validate_mesh_generation_conditions():
            return
            
        # 获取网格参数
        mesh_size, global_mesh_type = self._get_mesh_parameters()
        
        # 获取当前截面和激活形状
        current_section = self.data_manager.get_current_section()
        active_shapes = current_section.get_active_shapes()
        
        # 应用全局网格类型设置
        self._apply_global_mesh_type_settings(active_shapes, global_mesh_type)
        
        # 生成网格
        mesh = self._generate_mesh(active_shapes, mesh_size)
        if not mesh:
            return
            
        # 生成纤维
        fibers = self._generate_fibers(mesh, active_shapes)
        
        # 更新数据和UI
        self._update_mesh_data_and_ui(current_section, mesh, fibers)
        
        # 显示结果
        self._show_mesh_generation_result(mesh, active_shapes)
        
    def _validate_mesh_generation_conditions(self) -> bool:
        """验证网格生成的前置条件"""
        current_section = self.data_manager.get_current_section()
        active_shapes = current_section.get_active_shapes()
        
        if not active_shapes:
            QMessageBox.warning(self, "警告", "请先添加形状")
            return False
        return True
        
    def _get_mesh_parameters(self) -> tuple:
        """获取网格参数"""
        mesh_size = self.control_panel.mesh_size_input.value()
        global_mesh_type = self.control_panel.mesh_type_selector.currentText()
        
        # 将中文网格类型转换为英文
        if global_mesh_type == "三角形网格":
            global_mesh_type = "triangular"
        elif global_mesh_type == "四边形网格":
            global_mesh_type = "quadrilateral"
            
        return mesh_size, global_mesh_type
        
    def _apply_global_mesh_type_settings(self, active_shapes, global_mesh_type):
        """应用全局网格类型设置"""
        print(f"应用全局网格类型设置: {global_mesh_type}")
        for shape in active_shapes:
            # 如果形状没有明确设置网格类型，或者使用全局设置，则应用全局设置
            if not hasattr(shape, 'mesh_type') or shape.mesh_type is None:
                shape.mesh_type = global_mesh_type
                print(f"形状 {shape.id}: 设置网格类型为 {global_mesh_type}")
                
    def _generate_mesh(self, active_shapes, mesh_size):
        """生成网格"""
        mesh = self.mesh_generator.generate_mesh(active_shapes, mesh_size)
        
        if not mesh:
            QMessageBox.warning(self, "警告", "网格生成失败")
            return None
            
        return mesh
        
    def _generate_fibers(self, mesh, active_shapes):
        """生成纤维"""
        return mesh.generate_fibers(active_shapes)
        
    def _update_mesh_data_and_ui(self, current_section, mesh, fibers):
        """更新网格数据和UI"""
        # 更新截面数据
        self.data_manager.generate_mesh(current_section.id, mesh)
        
        # 更新画布 - 使用截面中当前的纤维列表（包含手动添加的纤维）
        current_fibers = current_section.fibers if current_section.fibers else fibers
        self.canvas.draw_mesh(mesh)
        self.canvas.draw_fibers(current_fibers)
        
        # 更新形状/纤维管理标签页
        self.control_panel.shape_fiber_tab._update_lists()
        
    def _show_mesh_generation_result(self, mesh, active_shapes):
        """显示网格生成结果"""
        mesh_type_counts = {}
        for shape in active_shapes:
            mesh_type = shape.mesh_type
            mesh_type_counts[mesh_type] = mesh_type_counts.get(mesh_type, 0) + 1
        
        type_info = []
        for mesh_type, count in mesh_type_counts.items():
            if mesh_type == "triangular":
                type_info.append(f"{count}个三角形网格")
            elif mesh_type == "quadrilateral":
                type_info.append(f"{count}个四边形网格")
        
        QMessageBox.information(
            self, "网格生成完成", 
            f"成功生成混合网格:\n" + 
            f"节点数: {len(mesh.nodes)}\n" +
            f"单元数: {len(mesh.elements)}\n" +
            f"网格类型: {', '.join(type_info)}"
        )
    
    def _on_section_switched(self):
        """截面切换事件处理"""
        # 清空画布
        self.canvas.clear()
        
        # 绘制当前截面内容
        self._draw_current_section_content()
        
    def _draw_current_section_content(self):
        """绘制当前截面内容"""
        current_section = self.data_manager.get_current_section()
        if not current_section:
            return
            
        # 绘制形状
        self._draw_section_shapes(current_section)
        
        # 绘制网格和纤维
        self._draw_section_mesh_and_fibers(current_section)
        
    def _draw_section_shapes(self, section):
        """绘制截面形状"""
        self.canvas.draw_shapes(section.get_shapes(), immediate=True)
        
    def _draw_section_mesh_and_fibers(self, section):
        """绘制截面网格和纤维"""
        if section.mesh:
            # 只绘制与激活形状相关的网格
            active_shapes = section.get_active_shapes()
            self.canvas.draw_mesh(section.mesh, active_shapes, immediate=True)
            
            # 绘制纤维（如果有）
            if section.fibers:
                self.canvas.draw_fibers(section.fibers, immediate=True)
    
    def _on_export_section(self):
        """导出截面事件处理"""
        # 验证是否有可导出的截面
        sections = self._get_exportable_sections()
        if not sections:
            return
            
        # 如果只有一个截面，直接导出
        if len(sections) == 1:
            self._export_single_section(sections[0])
            return
        
        # 处理多截面导出
        self._export_multiple_sections(sections)
        
    def _get_exportable_sections(self) -> list:
        """获取可导出的截面"""
        sections = self.data_manager.get_sections()
        if not sections:
            QMessageBox.warning(self, "警告", "没有可导出的截面")
            return []
        return sections
        
    def _export_single_section(self, section):
        """导出单个截面"""
        section_command = section.get_opensees_section_command()
        self._save_or_display_commands([section.id], [section_command])
        
    def _export_multiple_sections(self, sections):
        """导出多个截面"""
        # 创建选择对话框
        dialog = SectionSelectionDialog(sections, self)
        if dialog.exec_() != QDialog.Accepted:
            return
            
        # 获取选中的截面ID
        selected_ids = dialog.get_selected_sections()
        if not selected_ids:
            QMessageBox.information(self, "提示", "未选择任何截面")
            return
            
        # 生成命令文本
        commands_text = self._generate_section_commands_text(selected_ids)
        
        # 保存或显示命令
        self._save_or_display_commands(selected_ids, [commands_text])
        
    def _generate_section_commands_text(self, selected_ids) -> str:
        """生成截面命令文本"""
        section_commands = []
        for section_id in selected_ids:
            section = self.data_manager.get_section_by_id(section_id)
            if section:
                section_command = section.get_opensees_section_command()
                section_commands.append((section_id, section_command))
        
        # 整理命令文本
        all_commands = []
        for section_id, command in section_commands:
            section = self.data_manager.get_section_by_id(section_id)
            all_commands.append(f"# Section {section_id}: {section.name}")
            all_commands.append(command)
            all_commands.append("")  # 空行分隔
        
        return "\n".join(all_commands)
    
    def _save_or_display_commands(self, section_ids, commands):
        """保存命令到文件或显示"""
        # 判断是单个截面还是多个截面
        is_single_section = len(section_ids) == 1 and len(commands) == 1
        
        # 设置默认文件名
        if is_single_section:
            default_name = f"截面{section_ids[0]}_OpenSees命令.txt"
        else:
            selected_ids_str = "_".join(map(str, section_ids))
            default_name = f"截面{selected_ids_str}_OpenSees命令.txt"
        
        # 保存到文件
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出截面", default_name, "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    if is_single_section:
                        f.write(commands[0])
                    else:
                        for command in commands:
                            f.write(command)
                            f.write("\n")
                QMessageBox.information(self, "成功", "截面命令已导出到文件")
            except Exception as e:
                QMessageBox.error(self, "错误", f"导出失败: {str(e)}")
        else:
            # 如果用户取消保存，显示结果
            if is_single_section:
                QMessageBox.information(self, "导出结果", commands[0])
            else:
                display_text = "\n".join(commands)
                QMessageBox.information(self, "导出结果", display_text)
    
    def _on_new_project(self):
        """新建项目"""
        if not self._confirm_new_project():
            return
            
        self._reset_project_data()
    
    def _confirm_new_project(self) -> bool:
        """确认新建项目"""
        reply = QMessageBox.question(
            self, "确认", "新建项目将清除当前所有数据，是否继续？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        return reply == QMessageBox.Yes
        
    def _reset_project_data(self):
        """重置项目数据"""
        # 重置数据管理器
        self.data_manager = DataManager()
        # 重置画布
        self.canvas.clear()
            
    def _on_open_project(self):
        """打开项目"""
        file_path = self._get_project_file_path()
        if not file_path:
            return
            
        try:
            self._load_project_data(file_path)
            self._update_canvas_after_loading()
            QMessageBox.information(self, "成功", "项目已加载")
        except Exception as e:
            QMessageBox.error(self, "错误", f"加载失败: {str(e)}")
    
    def _get_project_file_path(self) -> str:
        """获取项目文件路径"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开项目", "", "项目文件 (*.json);;所有文件 (*)"
        )
        return file_path
        
    def _load_project_data(self, file_path: str):
        """加载项目数据"""
        self.data_manager.load_project(file_path)
        
    def _update_canvas_after_loading(self):
        """加载后更新画布"""
        self.canvas.clear()
        current_section = self.data_manager.get_current_section()
        if current_section:
            self._draw_section_content(current_section)
            
    def _draw_section_content(self, section):
        """绘制截面内容到画布"""
        # 绘制形状
        self.canvas.draw_shapes(section.get_shapes())
        
        # 绘制网格和纤维
        if section.mesh:
            self.canvas.draw_mesh(section.mesh)
            if section.fibers:
                self.canvas.draw_fibers(section.fibers)
    
    def _on_save_project(self):
        """保存项目"""
        file_path = self._get_save_file_path()
        if not file_path:
            return
            
        try:
            self._save_project_data(file_path)
            QMessageBox.information(self, "成功", "项目已保存")
        except Exception as e:
            QMessageBox.error(self, "错误", f"保存失败: {str(e)}")
    
    def _get_save_file_path(self) -> str:
        """获取保存文件路径"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存项目", "", "项目文件 (*.json);;所有文件 (*)"
        )
        return file_path
        
    def _save_project_data(self, file_path: str):
        """保存项目数据"""
        self.data_manager.save_project(file_path)
    
    def _on_zoom_in(self):
        """放大视图"""
        self.canvas.zoom_in()
    
    def _on_zoom_out(self):
        """缩小视图"""
        self.canvas.zoom_out()
    
    def _on_pan(self):
        """启用平移模式"""
        self.canvas.enable_pan()
    
    def _on_reset_view(self):
        """重置视图"""
        self.canvas.reset_view()
    
    def _on_canvas_refresh(self):
        """画布刷新处理"""
        current_section = self.data_manager.get_current_section()
        if current_section:
            self._refresh_canvas_with_section(current_section)
        else:
            self._clear_canvas()
    
    def _refresh_canvas_with_section(self, section):
        """使用截面数据刷新画布"""
        if self._has_direct_fibers(section):
            self._draw_section_fibers(section)
        elif self._has_mesh_fibers(section):
            self._draw_mesh_fibers(section)
        else:
            self._clear_and_redraw_canvas()
    
    def _has_direct_fibers(self, section) -> bool:
        """检查截面是否有直接的纤维数据"""
        return hasattr(section, 'fibers') and section.fibers
        
    def _has_mesh_fibers(self, section) -> bool:
        """检查截面是否有网格相关的纤维数据"""
        return (hasattr(section, 'mesh') and section.mesh and 
                hasattr(section.mesh, 'fibers') and section.mesh.fibers)
                
    def _draw_section_fibers(self, section):
        """绘制截面纤维"""
        self.canvas.draw_fibers(section.fibers, immediate=True)
        
    def _draw_mesh_fibers(self, section):
        """绘制网格纤维"""
        self.canvas.draw_fibers(section.mesh.fibers, immediate=True)
        
    def _clear_and_redraw_canvas(self):
        """清空并重绘画布"""
        self.canvas.clear()
        self.canvas.draw()
        
    def _clear_canvas(self):
        """清空画布"""
        self.canvas.clear()
        self.canvas.draw()
    
    def _on_fiber_list_refresh(self):
        """纤维列表刷新处理"""
        # 这个信号主要用于通知其他组件纤维列表已更新
        # 实际列表更新由ControlPanel中的ShapeFiberTab处理
        pass
    
    def _on_tab_changed(self, index: int):
        """标签页切换处理"""
        if index == 0:  # 纤维截面标签页
            self._switch_to_section_view()
        elif index == 1:  # OpenSeesPy建模标签页
            self._switch_to_openseespy_view()
        else:
            # 未知标签页索引，记录警告日志
            self._handle_unknown_tab_index(index)
    
    def _handle_unknown_tab_index(self, index: int):
        """处理未知的标签页索引"""
        print(f"警告: 未知的标签页索引: {index}")
    
    def _on_shape_list_refresh(self):
        """形状列表刷新处理"""
        # 这个信号主要用于通知其他组件形状列表已更新
        # 实际列表更新由ControlPanel中的ShapeFiberTab处理
        pass
