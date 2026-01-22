"""
CASIA-HWDB 数据集解析工具
- 支持 GNT 格式（离线手写单字）
- 支持 DGRL 格式（手写文档）
"""

import struct
import numpy as np
from pathlib import Path
from typing import Generator, Tuple, List, Optional
import cv2


class GNTParser:
    """
    GNT 文件解析器
    GNT 格式用于存储离线手写汉字图像
    
    文件结构:
    - 每个样本: [sample_size (4 bytes)] [tag_code (2 bytes)] [width (2 bytes)] [height (2 bytes)] [bitmap]
    """
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"GNT 文件不存在: {file_path}")
    
    def parse(self) -> Generator[Tuple[str, np.ndarray], None, None]:
        """
        解析 GNT 文件，逐个返回样本
        Yields:
            (字符标签, 图像数组) 元组
        """
        with open(self.file_path, 'rb') as f:
            while True:
                # 读取样本大小 (4 bytes, little-endian)
                sample_size_bytes = f.read(4)
                if len(sample_size_bytes) < 4:
                    break  # 文件结束
                
                sample_size = struct.unpack('<I', sample_size_bytes)[0]
                
                # 读取标签码 (2 bytes, GB2312/GBK 编码)
                tag_code = f.read(2)
                try:
                    # 尝试 GBK 解码
                    char = tag_code.decode('gbk')
                except:
                    try:
                        # 尝试 GB2312 解码
                        char = tag_code.decode('gb2312')
                    except:
                        char = '?'  # 无法解码
                
                # 读取图像尺寸
                width = struct.unpack('<H', f.read(2))[0]
                height = struct.unpack('<H', f.read(2))[0]
                
                # 读取位图数据
                bitmap_size = width * height
                bitmap_data = f.read(bitmap_size)
                
                if len(bitmap_data) < bitmap_size:
                    break  # 数据不完整
                
                # 转换为 numpy 数组
                image = np.frombuffer(bitmap_data, dtype=np.uint8).reshape(height, width)
                
                yield char, image
    
    def parse_to_list(self, max_samples: int = None) -> List[Tuple[str, np.ndarray]]:
        """
        解析 GNT 文件为列表
        Args:
            max_samples: 最大样本数，None 表示全部
        Returns:
            [(字符, 图像), ...] 列表
        """
        samples = []
        for i, (char, image) in enumerate(self.parse()):
            if max_samples and i >= max_samples:
                break
            samples.append((char, image))
        return samples
    
    def count_samples(self) -> int:
        """统计文件中的样本数"""
        count = 0
        for _ in self.parse():
            count += 1
        return count
    
    def extract_char(self, target_char: str) -> List[np.ndarray]:
        """
        提取指定字符的所有样本
        Args:
            target_char: 目标字符
        Returns:
            该字符的所有图像列表
        """
        images = []
        for char, image in self.parse():
            if char == target_char:
                images.append(image)
        return images


class GNTDataset:
    """GNT 数据集管理器"""
    
    def __init__(self, data_dir: str):
        """
        初始化数据集
        Args:
            data_dir: 包含 GNT 文件的目录
        """
        self.data_dir = Path(data_dir)
        self.gnt_files = list(self.data_dir.glob('*.gnt'))
        print(f"找到 {len(self.gnt_files)} 个 GNT 文件")
    
    def iterate_all(self, max_per_file: int = None) -> Generator[Tuple[str, np.ndarray, str], None, None]:
        """
        遍历所有 GNT 文件中的样本
        Yields:
            (字符, 图像, 来源文件名) 元组
        """
        for gnt_file in self.gnt_files:
            parser = GNTParser(str(gnt_file))
            for i, (char, image) in enumerate(parser.parse()):
                if max_per_file and i >= max_per_file:
                    break
                yield char, image, gnt_file.name
    
    def get_char_samples(self, target_char: str, max_samples: int = None) -> List[np.ndarray]:
        """
        获取指定字符的所有样本
        Args:
            target_char: 目标字符
            max_samples: 最大样本数
        Returns:
            图像列表
        """
        images = []
        for char, image, _ in self.iterate_all():
            if char == target_char:
                images.append(image)
                if max_samples and len(images) >= max_samples:
                    break
        return images
    
    def get_statistics(self, max_samples: int = 10000) -> dict:
        """
        获取数据集统计信息
        Args:
            max_samples: 统计的最大样本数
        Returns:
            统计字典
        """
        char_counts = {}
        total = 0
        
        for char, _, _ in self.iterate_all():
            char_counts[char] = char_counts.get(char, 0) + 1
            total += 1
            if total >= max_samples:
                break
        
        return {
            'total_samples': total,
            'unique_chars': len(char_counts),
            'char_counts': char_counts
        }
    
    def export_samples(self, output_dir: str, chars: str = None, 
                       samples_per_char: int = 10, target_size: Tuple[int, int] = (256, 256)):
        """
        导出样本图像
        Args:
            output_dir: 输出目录
            chars: 要导出的字符（None 表示所有）
            samples_per_char: 每个字符最多导出的样本数
            target_size: 目标图像尺寸
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        char_sample_counts = {}
        
        for char, image, source in self.iterate_all():
            if chars and char not in chars:
                continue
            
            count = char_sample_counts.get(char, 0)
            if count >= samples_per_char:
                continue
            
            # 创建字符目录
            char_dir = output_path / char
            char_dir.mkdir(exist_ok=True)
            
            # 调整尺寸
            resized = cv2.resize(image, target_size, interpolation=cv2.INTER_AREA)
            
            # 保存
            save_path = char_dir / f"{count:04d}.png"
            cv2.imwrite(str(save_path), resized)
            
            char_sample_counts[char] = count + 1
        
        print(f"导出完成: {sum(char_sample_counts.values())} 个样本，{len(char_sample_counts)} 个字符")


class DGRLParser:
    """
    DGRL 文件解析器
    DGRL 格式用于存储手写文档（整页）
    
    注意：DGRL 格式较复杂，这里提供基本解析
    """
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"DGRL 文件不存在: {file_path}")
    
    def parse(self) -> dict:
        """
        解析 DGRL 文件
        Returns:
            解析结果字典
        """
        with open(self.file_path, 'rb') as f:
            # 读取文件头
            header_size = struct.unpack('<I', f.read(4))[0]
            format_code = f.read(8).decode('ascii', errors='ignore').strip('\x00')
            illustration = f.read(header_size - 12).decode('ascii', errors='ignore').strip('\x00')
            
            # 读取图像数据
            # DGRL 格式有多种变体，这里提供基本框架
            remaining = f.read()
            
            return {
                'header_size': header_size,
                'format_code': format_code,
                'illustration': illustration,
                'data_size': len(remaining)
            }


def preprocess_handwriting_image(image: np.ndarray, target_size: Tuple[int, int] = (256, 256)) -> np.ndarray:
    """
    预处理手写图像
    Args:
        image: 原始图像（灰度）
        target_size: 目标尺寸
    Returns:
        预处理后的二值图像
    """
    # 确保是灰度图
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 反转（如果需要，使笔画为白色）
    if np.mean(image) > 127:
        image = 255 - image
    
    # 二值化
    _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # 找到内容边界
    coords = np.column_stack(np.where(binary > 0))
    if len(coords) > 0:
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)
        
        # 添加边距
        padding = 10
        y_min = max(0, y_min - padding)
        x_min = max(0, x_min - padding)
        y_max = min(binary.shape[0], y_max + padding)
        x_max = min(binary.shape[1], x_max + padding)
        
        # 裁剪
        binary = binary[y_min:y_max, x_min:x_max]
    
    # 调整到目标尺寸（保持宽高比）
    h, w = binary.shape
    scale = min(target_size[0] / w, target_size[1] / h) * 0.9  # 留边距
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    resized = cv2.resize(binary, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    # 放到目标尺寸画布中央
    result = np.zeros(target_size[::-1], dtype=np.uint8)  # (height, width)
    y_offset = (target_size[1] - new_h) // 2
    x_offset = (target_size[0] - new_w) // 2
    result[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
    
    return result
