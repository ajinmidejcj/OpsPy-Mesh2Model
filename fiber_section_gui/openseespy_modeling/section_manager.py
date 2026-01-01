from typing import List, Dict, Optional, Tuple, Any
from PyQt5.QtCore import QObject, pyqtSignal
import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, current_dir)

from fiber_section_gui.data.data_manager import DataManager, SectionData
from fiber_section_gui.geometry.shapes import Shape
from fiber_section_gui.meshing.mesh import Mesh


class SectionManager(QObject):
    """增强的截面管理器，集成现有功能与OpenSeesPy建模"""
    
    # 信号定义
    section_created = pyqtSignal(object)  # 截面创建信号
    section_updated = pyqtSignal(object)  # 截面更新信号
    section_deleted = pyqtSignal(int)     # 截面删除信号
    section_switched = pyqtSignal(object) # 截面切换信号
    
    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.data_manager = data_manager
        
        # 纤维截面参数默认值
        self.default_fiber_area = 0.01  # 默认纤维面积
        self.default_material_id = 1    # 默认材料ID
        
    def create_section(self, name: str = "Section", description: str = "") -> SectionData:
        """创建新截面"""
        section = self.data_manager.create_section(name)
        
        if description:
            section.description = description
            
        self.section_created.emit(section)
        return section
        
    def get_all_sections(self) -> List[SectionData]:
        """获取所有截面"""
        return self.data_manager.sections
        
    def get_section_by_id(self, section_id: int) -> Optional[SectionData]:
        """根据ID获取截面"""
        return self.data_manager.get_section_by_id(section_id)
        
    def get_current_section(self) -> Optional[SectionData]:
        """获取当前截面"""
        return self.data_manager.get_current_section()
        
    def set_current_section(self, section_id: int) -> bool:
        """设置当前截面"""
        result = self.data_manager.set_current_section(section_id)
        if result:
            section = self.get_section_by_id(section_id)
            self.section_switched.emit(section)
        return result
        
    def delete_section(self, section_id: int) -> bool:
        """删除截面"""
        result = self.data_manager.delete_section(section_id)
        if result:
            self.section_deleted.emit(section_id)
        return result
        
    def update_section_name(self, section_id: int, new_name: str) -> bool:
        """更新截面名称"""
        section = self.get_section_by_id(section_id)
        if section:
            section.name = new_name
            section.updated_time = section.updated_time.now()
            self.section_updated.emit(section)
            return True
        return False
        
    def update_section_gj(self, section_id: int, gj_value: float) -> bool:
        """更新截面扭转刚度"""
        section = self.get_section_by_id(section_id)
        if section:
            section.GJ = gj_value
            section.updated_time = section.updated_time.now()
            self.section_updated.emit(section)
            return True
        return False
        
    # 形状管理功能
    def add_shape(self, section_id: int, shape: Shape) -> bool:
        """添加形状到截面"""
        try:
            self.data_manager.add_shape(section_id, shape)
            section = self.get_section_by_id(section_id)
            self.section_updated.emit(section)
            return True
        except Exception as e:
            print(f"添加形状失败: {e}")
            return False
            
    def delete_shape(self, section_id: int, shape_id: int) -> bool:
        """从截面删除形状"""
        try:
            result = self.data_manager.delete_shape(section_id, shape_id)
            if result:
                section = self.get_section_by_id(section_id)
                self.section_updated.emit(section)
            return result
        except Exception as e:
            print(f"删除形状失败: {e}")
            return False
            
    def get_shapes(self, section_id: int) -> List[Shape]:
        """获取截面的所有形状"""
        section = self.get_section_by_id(section_id)
        return section.shapes if section else []
        
    def get_active_shapes(self, section_id: int) -> List[Shape]:
        """获取截面激活的形状"""
        section = self.get_section_by_id(section_id)
        return section.get_active_shapes() if section else []
        
    # 网格管理功能
    def generate_mesh(self, section_id: int, mesh: Mesh) -> bool:
        """生成网格"""
        try:
            result = self.data_manager.generate_mesh(section_id, mesh)
            if result:
                section = self.get_section_by_id(section_id)
                self.section_updated.emit(section)
            return result
        except Exception as e:
            print(f"生成网格失败: {e}")
            return False
            
    def clear_mesh(self, section_id: int) -> bool:
        """清除截面网格"""
        section = self.get_section_by_id(section_id)
        if section:
            section.mesh = None
            section.fibers = []
            section.updated_time = section.updated_time.now()
            self.section_updated.emit(section)
            return True
        return False
        
    # 纤维管理功能
    def add_fibers(self, section_id: int, fibers: List) -> bool:
        """添加纤维到截面"""
        section = self.get_section_by_id(section_id)
        if section:
            if section.fibers is None:
                section.fibers = []
                
            # 确保纤维ID不重复
            existing_ids = {fiber.id for fiber in section.fibers}
            for fiber in fibers:
                if fiber.id in existing_ids:
                    # 生成新的ID
                    new_id = max(existing_ids) + 1 if existing_ids else 1
                    fiber.id = new_id
                    existing_ids.add(new_id)
                else:
                    existing_ids.add(fiber.id)
                    
            section.fibers.extend(fibers)
            section.updated_time = section.updated_time.now()
            self.section_updated.emit(section)
            return True
        return False
        
    def remove_fibers(self, section_id: int, fiber_ids: List[int]) -> bool:
        """从截面删除纤维"""
        section = self.get_section_by_id(section_id)
        if section and section.fibers:
            original_count = len(section.fibers)
            section.fibers = [fiber for fiber in section.fibers if fiber.id not in fiber_ids]
            
            if len(section.fibers) < original_count:
                section.updated_time = section.updated_time.now()
                self.section_updated.emit(section)
                return True
        return False
        
    def clear_fibers(self, section_id: int) -> bool:
        """清除截面所有纤维"""
        section = self.get_section_by_id(section_id)
        if section:
            section.fibers = []
            section.updated_time = section.updated_time.now()
            self.section_updated.emit(section)
            return True
        return False
        
    def get_fibers(self, section_id: int) -> List:
        """获取截面所有纤维"""
        section = self.get_section_by_id(section_id)
        return section.fibers if section and section.fibers else []
        
    def get_fiber_count(self, section_id: int) -> int:
        """获取截面纤维数量"""
        return len(self.get_fibers(section_id))
        
    # OpenSeesPy代码生成
    def generate_openseespy_section_code(self, section_id: int) -> str:
        """生成OpenSeesPy截面代码"""
        section = self.get_section_by_id(section_id)
        if not section:
            return f"# 截面 {section_id} 不存在"
            
        return section.get_opensees_section_command()
        
    def export_all_sections_to_python(self) -> str:
        """导出所有截面到Python代码"""
        sections = self.get_all_sections()
        if not sections:
            return "# 无截面数据"
            
        code_lines = []
        code_lines.append("# 截面定义")
        code_lines.append("")
        
        for section in sections:
            code_lines.append(f"# 截面: {section.name} (ID: {section.id})")
            code_lines.append(self.generate_openseespy_section_code(section.id))
            code_lines.append("")
            
        return "\n".join(code_lines)
        
    # 截面分析功能
    def calculate_section_properties(self, section_id: int) -> Dict[str, float]:
        """计算截面属性"""
        section = self.get_section_by_id(section_id)
        if not section:
            return {}
            
        properties = {
            'area': 0.0,
            'ixx': 0.0,  # 关于X轴的二次矩
            'izz': 0.0,  # 关于Z轴的二次矩
            'ixz': 0.0,  # 惯性积
            'centroid_y': 0.0,
            'centroid_z': 0.0,
            'fiber_count': len(section.fibers) if section.fibers else 0
        }
        
        # 计算形状属性
        total_area = 0.0
        moment_y = 0.0  # 关于Z轴的静矩
        moment_z = 0.0  # 关于Y轴的静矩
        
        for shape in section.shapes:
            if shape.active:
                shape_area = shape.get_area()
                centroid = shape.get_centroid()
                
                total_area += shape_area
                moment_y += shape_area * centroid.y
                moment_z += shape_area * centroid.z
                
        if total_area > 0:
            properties['centroid_y'] = moment_y / total_area
            properties['centroid_z'] = moment_z / total_area
            properties['area'] = total_area
            
            # 计算二次矩（简化计算）
            for shape in section.shapes:
                if shape.active:
                    shape_area = shape.get_area()
                    centroid = shape.get_centroid()
                    
                    # 移轴定理（简化）
                    dy = centroid.y - properties['centroid_y']
                    dz = centroid.z - properties['centroid_z']
                    
                    # 假设形状的自身惯性矩
                    self_moment = shape_area ** 2 / 12.0  # 简化假设
                    
                    properties['ixx'] += self_moment + shape_area * dz ** 2
                    properties['izz'] += self_moment + shape_area * dy ** 2
                    properties['ixz'] += shape_area * dy * dz
                    
        return properties
        
    def validate_section(self, section_id: int) -> Tuple[bool, List[str]]:
        """验证截面数据"""
        errors = []
        section = self.get_section_by_id(section_id)
        
        if not section:
            errors.append("截面不存在")
            return False, errors
            
        # 检查形状
        if not section.shapes:
            errors.append("截面没有形状")
            
        active_shapes = section.get_active_shapes()
        if not active_shapes:
            errors.append("没有激活的形状")
            
        # 检查纤维
        if section.fibers:
            for i, fiber in enumerate(section.fibers):
                if not hasattr(fiber, 'area') or fiber.area <= 0:
                    errors.append(f"纤维 {i+1} 面积无效")
                if not hasattr(fiber, 'y') or not hasattr(fiber, 'z'):
                    errors.append(f"纤维 {i+1} 坐标无效")
                    
        # 检查GJ值
        if section.GJ <= 0:
            errors.append("扭转刚度 GJ 必须大于 0")
            
        return len(errors) == 0, errors
        
    def duplicate_section(self, section_id: int, new_name: str = None) -> Optional[SectionData]:
        """复制截面"""
        original_section = self.get_section_by_id(section_id)
        if not original_section:
            return None
            
        # 创建新截面
        if new_name is None:
            new_name = f"{original_section.name}_副本"
            
        new_section = self.create_section(new_name)
        
        # 复制形状
        import copy
        for shape in original_section.shapes:
            new_shape = copy.deepcopy(shape)
            self.add_shape(new_section.id, new_shape)
            
        # 复制网格
        if original_section.mesh:
            new_mesh = copy.deepcopy(original_section.mesh)
            self.generate_mesh(new_section.id, new_mesh)
            
        # 复制纤维
        if original_section.fibers:
            new_fibers = copy.deepcopy(original_section.fibers)
            self.add_fibers(new_section.id, new_fibers)
            
        # 复制GJ值
        self.update_section_gj(new_section.id, original_section.GJ)
        
        return new_section
        
    def get_section_summary(self, section_id: int) -> Dict[str, Any]:
        """获取截面摘要信息"""
        section = self.get_section_by_id(section_id)
        if not section:
            return {}
            
        properties = self.calculate_section_properties(section_id)
        is_valid, errors = self.validate_section(section_id)
        
        summary = {
            'id': section.id,
            'name': section.name,
            'created_time': section.created_time.isoformat() if section.created_time else None,
            'updated_time': section.updated_time.isoformat() if section.updated_time else None,
            'shape_count': len(section.shapes),
            'active_shape_count': len(section.get_active_shapes()),
            'has_mesh': section.mesh is not None,
            'fiber_count': len(section.fibers) if section.fibers else 0,
            'gj_value': section.GJ,
            'properties': properties,
            'is_valid': is_valid,
            'errors': errors
        }
        
        return summary