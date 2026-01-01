from typing import Optional, Dict, Any, List
from PyQt5.QtCore import QObject, pyqtSignal
import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, current_dir)

from fiber_section_gui.data.data_manager import DataManager

from .model_settings import ModelSettings, DOF
from .node_manager import NodeManager
from .material_manager import MaterialManager
from .element_manager import ElementManager
from .transform_manager import TransformManager
from .beam_integration_manager import BeamIntegrationManager
from .fix_boundary_manager import FixBoundaryManager
from .section_manager import SectionManager
from .openseespy_exporter import OpenSeesPyExporter
from .excel_templates import ExcelTemplates


class OpenSeesPyController(QObject):
    """OpenSeesPy建模功能控制器"""
    
    # 信号定义
    model_initialized = pyqtSignal()           # 模型初始化完成
    model_reset = pyqtSignal()                 # 模型重置
    data_changed = pyqtSignal(str)             # 数据变化（节点/材料/单元/截面）
    export_completed = pyqtSignal(str)         # 导出完成
    export_error = pyqtSignal(str)             # 导出错误
    validation_error = pyqtSignal(str)         # 验证错误
    
    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.data_manager = data_manager
        
        # 初始化各个管理器
        self.model_settings = ModelSettings()
        self.node_manager = NodeManager(self.model_settings)
        self.material_manager = MaterialManager()
        self.element_manager = ElementManager()
        self.transform_manager = TransformManager()
        self.beam_integration_manager = BeamIntegrationManager()
        self.fix_boundary_manager = FixBoundaryManager()
        self.section_manager = SectionManager(data_manager)
        
        # 初始化导出器和模板生成器
        self.exporter = OpenSeesPyExporter(
            self.model_settings,
            self.node_manager,
            self.material_manager,
            self.element_manager,
            self.transform_manager,
            self.beam_integration_manager,
            self.fix_boundary_manager,
            self.data_manager
        )
        self.excel_templates = ExcelTemplates(self.model_settings, self.node_manager, self.element_manager)
        
        # 连接信号
        self._connect_signals()
        
        # 默认模型设置
        self._initialize_default_model()
        
    def _connect_signals(self):
        """连接各个管理器的信号"""
        # 导出器信号
        self.exporter.export_completed.connect(self.export_completed.emit)
        self.exporter.export_error.connect(self.export_error.emit)
        
        # 模板生成器信号
        self.excel_templates.template_created.connect(self._on_template_created)
        self.excel_templates.template_error.connect(self.validation_error.emit)
        
        # 数据变化信号
        self.node_manager.nodes_changed.connect(lambda: self.data_changed.emit("nodes"))
        self.material_manager.material_added.connect(lambda: self.data_changed.emit("materials"))
        self.element_manager.elements_changed.connect(lambda: self.data_changed.emit("elements"))
        self.transform_manager.transforms_changed.connect(lambda: self.data_changed.emit("transforms"))
        self.beam_integration_manager.integrations_changed.connect(lambda: self.data_changed.emit("beam_integrations"))
        self.fix_boundary_manager.boundaries_changed.connect(lambda: self.data_changed.emit("fix_boundaries"))
        self.section_manager.section_created.connect(lambda: self.data_changed.emit("sections"))
        self.section_manager.section_updated.connect(lambda: self.data_changed.emit("sections"))
        
    def _initialize_default_model(self):
        """初始化默认模型设置"""
        # 设置默认的三维六自由度模型
        self.model_settings.set_model_dimension(3)
        self.model_settings.set_dof_list(DOF.DOF_3D_6)
        
    def reset_model(self):
        """重置整个模型"""
        try:
            # 清空所有数据
            self.node_manager.clear_all_nodes()
            self.material_manager.clear_all_materials()
            self.element_manager.clear_all_elements()
            self.transform_manager.clear_all_transforms()
            self.beam_integration_manager.clear_all_integrations()
            self.fix_boundary_manager.clear_all_boundaries()
            self.section_manager.clear_all_sections()  # 需要在SectionManager中添加此方法
            
            # 重新初始化模型设置
            self._initialize_default_model()
            
            self.model_reset.emit()
            
        except Exception as e:
            self.validation_error.emit(f"模型重置失败: {str(e)}")
            
    def validate_model(self) -> Dict[str, Any]:
        """验证整个模型"""
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        try:
            # 验证节点
            node_count = self.node_manager.get_node_count()
            if node_count == 0:
                validation_results['warnings'].append("没有定义节点")
            validation_results['statistics']['nodes'] = node_count
            
            # 验证坐标系变换
            transform_count = self.transform_manager.get_transform_count()
            if transform_count == 0:
                validation_results['warnings'].append("没有定义坐标系变换")
            validation_results['statistics']['transforms'] = transform_count
            
            # 验证材料
            material_count = self.material_manager.get_material_count()
            if material_count == 0:
                validation_results['warnings'].append("没有定义材料")
            validation_results['statistics']['materials'] = material_count
            
            # 验证单元
            element_count = self.element_manager.get_element_count()
            if element_count == 0:
                validation_results['warnings'].append("没有定义单元")
            validation_results['statistics']['elements'] = element_count
            
            # 验证截面
            section_count = len(self.section_manager.get_all_sections())
            if section_count == 0:
                validation_results['warnings'].append("没有定义截面")
            validation_results['statistics']['sections'] = section_count
            
            # 检查节点与单元的一致性
            node_ids = set(self.node_manager.get_all_node_ids())
            element_node_ids = set()
            for element in self.element_manager.elements.values():
                element_node_ids.update(element.node_ids)
                
            missing_nodes = element_node_ids - node_ids
            if missing_nodes:
                validation_results['errors'].append(f"单元引用的节点不存在: {missing_nodes}")
                
            # 检查材料引用
            material_ids = set(self.material_manager.get_all_material_ids())
            element_material_ids = set()
            for element in self.element_manager.elements.values():
                if hasattr(element, 'mat_tag'):
                    element_material_ids.add(element.mat_tag)
                    
            missing_materials = element_material_ids - material_ids
            if missing_materials:
                validation_results['errors'].append(f"单元引用的材料不存在: {missing_materials}")
                
            validation_results['is_valid'] = len(validation_results['errors']) == 0
            
        except Exception as e:
            validation_results['is_valid'] = False
            validation_results['errors'].append(f"验证过程出错: {str(e)}")
            
        return validation_results
        
    def get_model_summary(self) -> Dict[str, Any]:
        """获取模型摘要信息"""
        try:
            summary = {
                'model_settings': {
                    'dimension': self.model_settings.ndm,
                    'dof_count': self.model_settings.ndf,
                    'dof_list': self.model_settings.dof_list
                },
                'statistics': {
                    'nodes': self.node_manager.get_node_count(),
                    'transforms': self.transform_manager.get_transform_count(),
                    'materials': self.material_manager.get_material_count(),
                    'elements': self.element_manager.get_element_count(),
                    'sections': len(self.section_manager.get_all_sections())
                },
                'validation': self.validate_model()
            }
            
            return summary
            
        except Exception as e:
            return {'error': str(e)}
            
    def export_complete_model(self, file_path: Optional[str] = None) -> tuple:
        """导出完整模型"""
        try:
            return self.exporter.export_to_file(file_path)
        except Exception as e:
            error_msg = f"导出模型失败: {str(e)}"
            self.export_error.emit(error_msg)
            return False, error_msg
            
    def generate_model_preview(self) -> str:
        """生成模型预览代码"""
        try:
            return self.exporter.generate_complete_script()
        except Exception as e:
            return f"# 生成预览失败: {str(e)}"
            
    def create_node_template(self, file_path: Optional[str] = None) -> tuple:
        """创建节点模板"""
        try:
            return self.excel_templates.create_node_template(file_path)
        except Exception as e:
            error_msg = f"创建节点模板失败: {str(e)}"
            self.validation_error.emit(error_msg)
            return False, error_msg
            
    def create_element_template(self, file_path: Optional[str] = None) -> tuple:
        """创建单元模板"""
        try:
            return self.excel_templates.create_element_template(file_path)
        except Exception as e:
            error_msg = f"创建单元模板失败: {str(e)}"
            self.validation_error.emit(error_msg)
            return False, error_msg
            
    def import_nodes_from_excel(self, file_path: str) -> tuple:
        """从Excel文件导入节点"""
        try:
            return self.node_manager.import_from_excel(file_path)
        except Exception as e:
            error_msg = f"导入节点失败: {str(e)}"
            self.validation_error.emit(error_msg)
            return False, error_msg, 0
            
    def import_elements_from_excel(self, file_path: str) -> tuple:
        """从Excel文件导入单元"""
        try:
            return self.element_manager.import_from_excel(file_path)
        except Exception as e:
            error_msg = f"导入单元失败: {str(e)}"
            self.validation_error.emit(error_msg)
            return False, error_msg, 0
            
    def import_elements_from_multisheet_file(self, file_path: str) -> tuple:
        """从多页文件（Excel或CSV）导入单元"""
        try:
            success, error, stats = self.element_manager.import_elements_from_multisheet_file(file_path)
            return success, error, stats
        except Exception as e:
            error_msg = f"导入多页单元文件失败: {str(e)}"
            self.validation_error.emit(error_msg)
            return False, error_msg, {}
            
    def export_elements_to_multisheet_file(self, file_path: str, export_types: Optional[List[str]] = None) -> tuple:
        """导出单元到多页文件（Excel或CSV）"""
        try:
            return self.element_manager.export_elements_to_multisheet_file(file_path, export_types)
        except Exception as e:
            error_msg = f"导出多页单元文件失败: {str(e)}"
            self.validation_error.emit(error_msg)
            return False, error_msg
            
    def create_element_template(self, file_path: Optional[str] = None, element_types: Optional[List[str]] = None) -> tuple:
        """创建单元模板"""
        try:
            return self.element_manager.create_element_template(file_path, element_types)
        except Exception as e:
            error_msg = f"创建单元模板失败: {str(e)}"
            self.validation_error.emit(error_msg)
            return False, error_msg
            
    def _on_template_created(self, file_path: str, template_type: str):
        """模板创建完成回调"""
        print(f"{template_type}模板已创建: {file_path}")
        
    # 便捷方法，委托给各个管理器
    def create_node(self, node_id: int, x: float, y: float, z: float = 0.0, 
                   mass: Optional[list] = None) -> tuple:
        """创建单个节点"""
        if mass is None:
            mass = [0.0] * self.model_settings.ndf
        return self.node_manager.create_node(node_id, x, y, z, mass)
        
    def create_material(self, material_type: str, name: str, material_id: Optional[int] = None, **kwargs) -> tuple:
        """创建材料"""
        success, error, material = self.material_manager.create_material(material_type, name, material_id=material_id, **kwargs)
        return success, error, material
        
    def create_element(self, element_type: str, element_id: int, node_ids: list, **kwargs) -> tuple:
        """创建单元"""
        # 将element_id和node_ids添加到kwargs中
        kwargs['element_id'] = element_id
        kwargs['node_ids'] = node_ids
        return self.element_manager.create_element(element_type, **kwargs)
        
    def create_transform(self, transform_type: str, name: str, transform_id: Optional[int] = None, **kwargs) -> tuple:
        """创建坐标系变换"""
        return self.transform_manager.create_transform(transform_type, name, transform_id, **kwargs)
        
    def create_section(self, name: str, description: str = "") -> object:
        """创建截面"""
        return self.section_manager.create_section(name, description)
        
    def get_all_nodes(self) -> dict:
        """获取所有节点"""
        return self.node_manager.get_all_nodes()
        
    def get_all_materials(self) -> dict:
        """获取所有材料"""
        return self.material_manager.get_all_materials()
        
    def get_all_elements(self) -> dict:
        """获取所有单元"""
        return self.element_manager.get_all_elements()
        
    def get_all_transforms(self) -> dict:
        """获取所有坐标系变换"""
        return self.transform_manager.get_all_transforms()
        
    def get_all_node_ids(self) -> List[int]:
        """获取所有节点ID"""
        return self.node_manager.get_all_node_ids()
        
    def get_all_material_ids(self) -> List[int]:
        """获取所有材料ID"""
        return self.material_manager.get_all_material_ids()
        
    def get_all_element_ids(self) -> List[int]:
        """获取所有单元ID"""
        return self.element_manager.get_all_element_ids()
        
    def get_all_transform_ids(self) -> List[int]:
        """获取所有坐标系变换ID"""
        return self.transform_manager.get_all_transform_ids()
        
    def get_all_sections(self) -> list:
        """获取所有截面"""
        return self.section_manager.get_all_sections()
        
    def clear_nodes(self) -> bool:
        """清空所有节点"""
        return self.node_manager.clear_all_nodes()
        
    def clear_materials(self) -> bool:
        """清空所有材料"""
        return self.material_manager.clear_all_materials()
        
    def clear_elements(self) -> bool:
        """清空所有单元"""
        return self.element_manager.clear_all_elements()
        
    def clear_transforms(self) -> bool:
        """清空所有坐标系变换"""
        return self.transform_manager.clear_all_transforms()
        
    # 高级功能
    def auto_generate_mesh_nodes(self, element_ids: list, node_spacing: float = 1.0) -> tuple:
        """自动生成网格节点（用于梁单元）"""
        try:
            created_count = 0
            for element_id in element_ids:
                element = self.element_manager.get_element_by_id(element_id)
                if element and len(element.node_ids) == 2:
                    # 在两个节点之间生成中间节点
                    node1 = self.node_manager.get_node_by_id(element.node_ids[0])
                    node2 = self.node_manager.get_node_by_id(element.node_ids[1])
                    
                    if node1 and node2:
                        # 简化：只在中间生成一个节点
                        mid_x = (node1.x + node2.x) / 2
                        mid_y = (node1.y + node2.y) / 2
                        mid_z = (node1.z + node2.z) / 2
                        
                        # 生成新节点ID
                        new_node_id = max(self.node_manager.get_all_node_ids(), default=0) + 1
                        
                        success, error = self.node_manager.create_node(new_node_id, mid_x, mid_y, mid_z)
                        if success:
                            created_count += 1
                        else:
                            return False, f"节点 {new_node_id} 创建失败: {error}", created_count
                            
            return True, f"成功创建 {created_count} 个网格节点", created_count
            
        except Exception as e:
            return False, f"自动生成网格节点失败: {str(e)}", 0
            
    def generate_structural_grid(self, origin: tuple, 
                               size: tuple, 
                               divisions: tuple) -> tuple:
        """生成结构网格"""
        try:
            origin_x, origin_y, origin_z = origin
            size_x, size_y, size_z = size
            div_x, div_y, div_z = divisions
            
            step_x = size_x / div_x if div_x > 0 else size_x
            step_y = size_y / div_y if div_y > 0 else size_y
            step_z = size_z / div_z if div_z > 0 else size_z
            
            created_count = 0
            
            for i in range(div_x + 1):
                for j in range(div_y + 1):
                    for k in range(div_z + 1):
                        x = origin_x + i * step_x
                        y = origin_y + j * step_y
                        z = origin_z + k * step_z
                        
                        # 生成节点ID（按网格位置）
                        node_id = (i + 1) * 10000 + (j + 1) * 100 + (k + 1)
                        
                        success, error = self.node_manager.create_node(node_id, x, y, z)
                        if success:
                            created_count += 1
                        else:
                            return False, f"网格节点 {node_id} 创建失败: {error}", created_count
                            
            return True, f"成功创建 {created_count} 个网格节点", created_count
            
        except Exception as e:
            return False, f"生成结构网格失败: {str(e)}", 0