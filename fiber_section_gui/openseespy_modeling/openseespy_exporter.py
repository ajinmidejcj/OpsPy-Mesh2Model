# -*- coding: utf-8 -*-
"""
OpenSeesPy代码导出模块
用于按指定顺序生成完整的OpenSeesPy前处理建模代码
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QMessageBox

from .model_settings import ModelSettings
from .node_manager import NodeManager
from .material_manager import MaterialManager
from .element_manager import ElementManager
from .transform_manager import TransformManager
from .beam_integration_manager import BeamIntegrationManager
from .fix_boundary_manager import FixBoundaryManager
from fiber_section_gui.data.data_manager import DataManager  # 引用现有的截面管理


class CodeExportOptions:
    """代码导出选项"""
    
    def __init__(self):
        self.include_comments = True  # 包含注释
        self.include_imports = True   # 包含导入语句
        self.include_wipe = True      # 包含ops.wipe()
        self.include_prints = True    # 包含打印信息
        self.code_style = "standard"  # 代码风格: standard, compact
        self.file_encoding = "utf-8"  # 文件编码


class OpenSeesPyExporter(QObject):
    """OpenSeesPy代码导出器"""
    
    # 信号定义
    export_completed = pyqtSignal(str)  # 导出完成信号
    export_error = pyqtSignal(str)      # 导出错误信号
    export_progress = pyqtSignal(int, int)  # 导出进度信号 (当前, 总数)
    
    def __init__(self, model_settings: ModelSettings, node_manager: NodeManager,
                 material_manager: MaterialManager, element_manager: ElementManager,
                 transform_manager: TransformManager, beam_integration_manager: BeamIntegrationManager,
                 fix_boundary_manager: FixBoundaryManager, data_manager: DataManager):
        super().__init__()
        
        # 各个管理器
        self.model_settings = model_settings
        self.node_manager = node_manager
        self.material_manager = material_manager
        self.element_manager = element_manager
        self.transform_manager = transform_manager
        self.beam_integration_manager = beam_integration_manager
        self.fix_boundary_manager = fix_boundary_manager
        self.data_manager = data_manager
        
        # 导出选项
        self.export_options = CodeExportOptions()
        
    def set_export_options(self, options: CodeExportOptions):
        """设置导出选项"""
        self.export_options = options
        
    def generate_complete_script(self) -> str:
        """生成完整的OpenSeesPy脚本"""
        try:
            script_lines = []
            
            # 1. 添加文件头部信息
            script_lines.extend(self._generate_header())
            
            # 2. 添加导入语句
            if self.export_options.include_imports:
                script_lines.extend(self._generate_imports())
                
            # 3. 添加模型设置
            script_lines.extend(self._generate_model_setup())
            
            # 4. 添加节点创建
            script_lines.extend(self._generate_nodes())
            
            # 5. 添加坐标系变换
            script_lines.extend(self._generate_transformations())
            
            # 6. 添加材料创建
            script_lines.extend(self._generate_materials())
            
            # 7. 添加截面创建（现有功能）
            script_lines.extend(self._generate_sections())
            
            # 8. 添加beamIntegration
            script_lines.extend(self._generate_beam_integrations())
            
            # 9. 添加单元创建
            script_lines.extend(self._generate_elements())
            
            # 10. 添加fix边界条件
            script_lines.extend(self._generate_fix_boundaries())
            
            # 11. 添加文件尾部
            script_lines.extend(self._generate_footer())
            
            return "\n".join(script_lines)
            
        except Exception as e:
            self.export_error.emit(f"生成完整脚本时发生错误: {str(e)}")
            return ""
            
    def export_to_file(self, file_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        导出到文件
        
        Args:
            file_path: 文件路径，如果为None则弹出文件保存对话框
            
        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        try:
            # 如果没有指定文件路径，弹出保存对话框
            if file_path is None:
                file_path, _ = QFileDialog.getSaveFileName(
                    None,
                    "保存OpenSeesPy脚本",
                    f"openseespy_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py",
                    "Python Files (*.py);;All Files (*)"
                )
                
            if not file_path:
                return False, "用户取消了文件保存"
                
            # 生成脚本内容
            script_content = self.generate_complete_script()
            
            if not script_content:
                return False, "生成脚本内容失败"
                
            # 写入文件
            with open(file_path, 'w', encoding=self.export_options.file_encoding) as f:
                f.write(script_content)
                
            self.export_completed.emit(file_path)
            return True, f"成功导出到: {file_path}"
            
        except Exception as e:
            error_msg = f"导出文件时发生错误: {str(e)}"
            self.export_error.emit(error_msg)
            return False, error_msg
            
    def _generate_header(self) -> List[str]:
        """生成文件头部"""
        lines = []
        
        if self.export_options.include_comments:
            lines.extend([
                "# -*- coding: utf-8 -*-",
                f"#",
                f"# OpenSeesPy 有限元模型脚本",
                f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"# 模型设置: {self.model_settings.ndm}D, {self.model_settings.ndf}自由度",
                f"#",
                ""
            ])
            
        return lines
        
    def _generate_imports(self) -> List[str]:
        """生成导入语句"""
        lines = [
            "import openseespy.opensees as ops",
            "import numpy as np",
            "",
            "# 如果使用纤维截面功能",
            "# from纤维截面模块 import 相关类",
            ""
        ]
        
        return lines
        
    def _generate_model_setup(self) -> List[str]:
        """生成模型设置"""
        return self.model_settings.generate_opensees_code().split('\n')
        
    def _generate_nodes(self) -> List[str]:
        """生成节点创建代码"""
        return self.node_manager.generate_opensees_code().split('\n')
        
    def _generate_transformations(self) -> List[str]:
        """生成坐标系变换创建代码"""
        return self.transform_manager.generate_all_transform_code().split('\n')
        
    def _generate_materials(self) -> List[str]:
        """生成材料创建代码"""
        return self.material_manager.export_materials_to_python().split('\n')
        
    def _generate_sections(self) -> List[str]:
        """生成截面创建代码（集成现有功能）"""
        lines = []
        
        if self.export_options.include_prints:
            lines.append("\n# 截面创建")
            lines.append("print('正在创建截面...')")
            
        # 获取所有截面
        sections = self.data_manager.get_sections()
        
        if not sections:
            lines.append("# 无截面数据")
            return lines
            
        for section in sections:
            lines.append(f"\n# 截面: {section.name} (ID: {section.id})")
            
            # 添加形状创建代码
            if section.shapes:
                lines.append("# 创建几何形状")
                for shape in section.shapes:
                    shape_code = self._generate_shape_code(shape)
                    lines.extend(shape_code)
                    
            # 添加网格生成代码
            if section.mesh:
                lines.append("# 生成纤维网格")
                mesh_code = self._generate_mesh_code(section.mesh)
                lines.extend(mesh_code)
                
            # 添加纤维截面代码
            if section.fibers or (section.mesh and section.mesh.fibers):
                lines.append("# 创建纤维截面")
                section_code = section.get_opensees_section_command()
                lines.extend(section_code.split('\n'))
                
        return lines
        
    def _generate_shape_code(self, shape) -> List[str]:
        """生成单个形状的创建代码"""
        # 这里需要根据现有项目的形状类来生成代码
        # 暂时返回示例代码
        lines = [
            f"# 形状类型: {shape.__class__.__name__}",
            f"# 形状ID: {shape.id}",
            "# TODO: 实现具体形状的OpenSeesPy代码生成"
        ]
        return lines
        
    def _generate_mesh_code(self, mesh) -> List[str]:
        """生成网格创建代码"""
        lines = [
            f"# 网格ID: {mesh.id}",
            f"# 节点数: {len(mesh.nodes)}",
            f"# 单元数: {len(mesh.elements)}",
            f"# 纤维数: {len(mesh.fibers)}",
            "# TODO: 实现具体网格的OpenSeesPy代码生成"
        ]
        return lines
        
    def _generate_fiber_code(self, section) -> List[str]:
        """生成纤维截面代码"""
        lines = [
            f"# 纤维数量: {len(section.fibers) if section.fibers else 0}",
            "# TODO: 实现纤维截面的OpenSeesPy代码生成"
        ]
        return lines
        
    def _generate_elements(self) -> List[str]:
        """生成单元创建代码"""
        return self.element_manager.export_elements_to_python().split('\n')
        
    def _generate_beam_integrations(self) -> List[str]:
        """生成beamIntegration创建代码"""
        lines = []
        
        # 获取所有beamIntegration
        integrations = list(self.beam_integration_manager.integrations.values())
        
        if not integrations:
            return lines
            
        lines.append("# beamIntegration设置")
        
        for integration in integrations:
            code_line = integration.generate_opensees_code()
            if code_line:
                if self.export_options.include_comments:
                    lines.append(f"# {integration.name} ({integration.type})")
                lines.append(code_line)
                lines.append("")  # 空行分隔
        
        return lines
        
    def _generate_fix_boundaries(self) -> List[str]:
        """生成fix边界条件代码"""
        lines = []
        
        # 获取所有fix边界条件
        boundaries = list(self.fix_boundary_manager.boundaries.values())
        
        if not boundaries:
            return lines
            
        lines.append("# fix边界条件设置")
        
        for boundary in boundaries:
            code_line = boundary.generate_opensees_code()
            if code_line:
                if self.export_options.include_comments:
                    lines.append(f"# {boundary.name} (节点 {boundary.node_tag})")
                lines.append(code_line)
                lines.append("")  # 空行分隔
        
        return lines
        
    def _generate_footer(self) -> List[str]:
        """生成文件尾部"""
        lines = []
        
        if self.export_options.include_comments:
            lines.extend([
                "",
                "# 模型创建完成",
                f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "# 可以继续添加分析设置、荷载、边界条件等"
            ])
            
        return lines
        
    def generate_summary_report(self) -> str:
        """生成模型摘要报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("OpenSeesPy 模型摘要报告")
        lines.append("=" * 60)
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # 模型设置
        lines.append("1. 模型设置")
        lines.append(f"   空间维度: {self.model_settings.ndm}D")
        lines.append(f"   自由度数量: {self.model_settings.ndf}")
        lines.append(f"   自由度列表: {self.model_settings.get_dof_list_description()}")
        lines.append("")
        
        # 节点统计
        node_stats = self.node_manager.get_node_statistics()
        lines.append("2. 节点统计")
        lines.append(f"   总节点数: {node_stats.get('total', 0)}")
        if node_stats.get('total', 0) > 0:
            coord_ranges = node_stats.get('coordinate_ranges', {})
            lines.append(f"   X坐标范围: {coord_ranges.get('x', {}).get('min', 0):.3f} ~ {coord_ranges.get('x', {}).get('max', 0):.3f}")
            lines.append(f"   Y坐标范围: {coord_ranges.get('y', {}).get('min', 0):.3f} ~ {coord_ranges.get('y', {}).get('max', 0):.3f}")
            if self.model_settings.ndm == 3:
                lines.append(f"   Z坐标范围: {coord_ranges.get('z', {}).get('min', 0):.3f} ~ {coord_ranges.get('z', {}).get('max', 0):.3f}")
        lines.append("")
        
        # 坐标系变换统计
        transform_stats = self.transform_manager.get_transform_statistics()
        lines.append("3. 坐标系变换统计")
        lines.append(f"   总变换数: {transform_stats.get('total', 0)}")
        if transform_stats.get('types'):
            for transform_type, count in transform_stats['types'].items():
                lines.append(f"   {transform_type}变换: {count}个")
        lines.append("")
        
        # 材料统计
        material_stats = self.material_manager.get_material_statistics()
        lines.append("4. 材料统计")
        lines.append(f"   总材料数: {material_stats.get('total', 0)}")
        if material_stats.get('types'):
            for mat_type, count in material_stats['types'].items():
                lines.append(f"   {mat_type}材料: {count}个")
        lines.append("")
        
        # 单元统计
        element_stats = self.element_manager.get_element_statistics()
        lines.append("5. 单元统计")
        lines.append(f"   总单元数: {element_stats.get('total', 0)}")
        if element_stats.get('types'):
            for elem_type, count in element_stats['types'].items():
                lines.append(f"   {elem_type}单元: {count}个")
        lines.append("")
        
        # 截面统计
        sections = self.data_manager.get_sections()
        lines.append("6. 截面统计")
        lines.append(f"   总截面数: {len(sections)}")
        for section in sections:
            shape_count = len(section.shapes) if section.shapes else 0
            fiber_count = len(section.fibers) if section.fibers else 0
            lines.append(f"   截面'{section.name}' (ID:{section.id}): {shape_count}个形状, {fiber_count}个纤维")
        lines.append("")
        
        # 验证结果
        lines.append("7. 模型验证")
        
        # 验证节点
        node_valid, node_errors = self.node_manager.validate_all_nodes()
        if node_valid:
            lines.append("   ✓ 节点数据验证通过")
        else:
            lines.append("   ✗ 节点数据验证失败:")
            for error in node_errors[:5]:  # 只显示前5个错误
                lines.append(f"     - {error}")
            if len(node_errors) > 5:
                lines.append(f"     ... 还有{len(node_errors)-5}个错误")
                
        # 验证坐标系变换
        transform_valid, transform_errors = self.transform_manager.validate_all_transforms()
        if transform_valid:
            lines.append("   ✓ 坐标系变换数据验证通过")
        else:
            lines.append("   ✗ 坐标系变换数据验证失败:")
            for error in transform_errors[:5]:
                lines.append(f"     - {error}")
            if len(transform_errors) > 5:
                lines.append(f"     ... 还有{len(transform_errors)-5}个错误")
                
        # 验证材料
        material_valid, material_errors = self.material_manager.validate_all_materials()
        if material_valid:
            lines.append("   ✓ 材料数据验证通过")
        else:
            lines.append("   ✗ 材料数据验证失败:")
            for error in material_errors[:5]:
                lines.append(f"     - {error}")
            if len(material_errors) > 5:
                lines.append(f"     ... 还有{len(material_errors)-5}个错误")
                
        # 验证单元
        element_valid, element_errors = self.element_manager.validate_all_elements()
        if element_valid:
            lines.append("   ✓ 单元数据验证通过")
        else:
            lines.append("   ✗ 单元数据验证失败:")
            for error in element_errors[:5]:
                lines.append(f"     - {error}")
            if len(element_errors) > 5:
                lines.append(f"     ... 还有{len(element_errors)-5}个错误")
                
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)
        
    def export_summary_report(self, file_path: Optional[str] = None) -> Tuple[bool, str]:
        """导出摘要报告"""
        try:
            if file_path is None:
                file_path, _ = QFileDialog.getSaveFileName(
                    None,
                    "保存模型摘要报告",
                    f"model_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    "Text Files (*.txt);;All Files (*)"
                )
                
            if not file_path:
                return False, "用户取消了文件保存"
                
            report_content = self.generate_summary_report()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
                
            return True, f"成功导出摘要报告到: {file_path}"
            
        except Exception as e:
            return False, f"导出摘要报告时发生错误: {str(e)}"


from .section_manager import SectionManager as EnhancedSectionManager