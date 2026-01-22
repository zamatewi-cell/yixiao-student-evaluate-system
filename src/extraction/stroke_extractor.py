"""
笔画级特征提取模块
- 骨架提取
- 笔画分割
- 几何特征计算
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from skimage.morphology import skeletonize
from scipy import ndimage


class StrokeExtractor:
    """笔画特征提取器"""
    
    def __init__(self, config: dict):
        extraction_config = config.get('extraction', {})
        self.min_stroke_length = extraction_config.get('min_stroke_length', 5)
    
    def extract_skeleton(self, binary_image: np.ndarray) -> np.ndarray:
        """
        提取骨架
        Args:
            binary_image: 二值图像（白色为笔画，黑色为背景）
        Returns:
            骨架图像
        """
        # 确保是二值图像
        if binary_image.max() > 1:
            binary = (binary_image > 127).astype(np.uint8)
        else:
            binary = binary_image.astype(np.uint8)
        
        # skimage 的 skeletonize 需要布尔数组
        skeleton = skeletonize(binary > 0)
        return (skeleton * 255).astype(np.uint8)
    
    def compute_center_of_mass(self, binary_image: np.ndarray) -> Tuple[float, float]:
        """
        计算重心
        Args:
            binary_image: 二值图像
        Returns:
            (cx, cy) 归一化重心坐标 (0-1范围)
        """
        moments = cv2.moments(binary_image)
        if moments['m00'] == 0:
            return 0.5, 0.5
        
        cx = moments['m10'] / moments['m00']
        cy = moments['m01'] / moments['m00']
        
        # 归一化
        h, w = binary_image.shape[:2]
        return cx / w, cy / h
    
    def compute_aspect_ratio(self, binary_image: np.ndarray) -> Dict[str, float]:
        """
        计算比例特征
        Args:
            binary_image: 二值图像
        Returns:
            包含各种比例特征的字典
        """
        h, w = binary_image.shape[:2]
        
        # 上下比例
        upper_half = binary_image[:h//2, :]
        lower_half = binary_image[h//2:, :]
        upper_pixels = np.sum(upper_half > 0)
        lower_pixels = np.sum(lower_half > 0)
        total_pixels = upper_pixels + lower_pixels
        
        upper_ratio = upper_pixels / total_pixels if total_pixels > 0 else 0.5
        
        # 左右比例
        left_half = binary_image[:, :w//2]
        right_half = binary_image[:, w//2:]
        left_pixels = np.sum(left_half > 0)
        right_pixels = np.sum(right_half > 0)
        total_lr = left_pixels + right_pixels
        
        left_ratio = left_pixels / total_lr if total_lr > 0 else 0.5
        
        return {
            'upper_ratio': upper_ratio,
            'lower_ratio': 1 - upper_ratio,
            'left_ratio': left_ratio,
            'right_ratio': 1 - left_ratio
        }
    
    def compute_stroke_features(self, skeleton: np.ndarray) -> Dict:
        """
        从骨架中提取笔画特征
        Args:
            skeleton: 骨架图像
        Returns:
            笔画特征字典
        """
        # 找到所有非零点
        points = np.argwhere(skeleton > 0)
        
        if len(points) == 0:
            return {
                'total_length': 0,
                'stroke_count': 0,
                'endpoints': [],
                'junctions': []
            }
        
        # 计算总长度（骨架像素数）
        total_length = len(points)
        
        # 检测端点和交叉点
        endpoints, junctions = self._detect_key_points(skeleton)
        
        # 估算笔画数（端点数 / 2 + 交叉点调整）
        stroke_count = max(1, (len(endpoints) + 1) // 2)
        
        return {
            'total_length': total_length,
            'stroke_count': stroke_count,
            'endpoints': endpoints,
            'junctions': junctions
        }
    
    def _detect_key_points(self, skeleton: np.ndarray) -> Tuple[List, List]:
        """
        检测骨架中的端点和交叉点
        Args:
            skeleton: 骨架图像
        Returns:
            (端点列表, 交叉点列表)
        """
        # 使用3x3邻域卷积检测关键点
        kernel = np.ones((3, 3), dtype=np.uint8)
        kernel[1, 1] = 0
        
        binary_skeleton = (skeleton > 0).astype(np.uint8)
        neighbor_count = cv2.filter2D(binary_skeleton, -1, kernel)
        
        # 端点：邻域只有1个点
        endpoints = np.argwhere((skeleton > 0) & (neighbor_count == 1))
        
        # 交叉点：邻域有3个以上点
        junctions = np.argwhere((skeleton > 0) & (neighbor_count >= 3))
        
        return endpoints.tolist(), junctions.tolist()
    
    def compute_stroke_angles(self, skeleton: np.ndarray) -> List[float]:
        """
        计算笔画方向角度分布
        Args:
            skeleton: 骨架图像
        Returns:
            角度列表
        """
        # 使用Sobel计算梯度方向
        binary = (skeleton > 0).astype(np.float32)
        
        gx = cv2.Sobel(binary, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(binary, cv2.CV_32F, 0, 1, ksize=3)
        
        # 计算角度
        angles = np.arctan2(gy, gx) * 180 / np.pi
        
        # 只取骨架上的角度
        skeleton_mask = skeleton > 0
        valid_angles = angles[skeleton_mask]
        
        return valid_angles.tolist()
    
    def extract_all_features(self, binary_image: np.ndarray) -> Dict:
        """
        提取所有笔画特征
        Args:
            binary_image: 二值图像
        Returns:
            完整特征字典
        """
        # 1. 提取骨架
        skeleton = self.extract_skeleton(binary_image)
        
        # 2. 计算重心
        center = self.compute_center_of_mass(binary_image)
        
        # 3. 计算比例
        ratios = self.compute_aspect_ratio(binary_image)
        
        # 4. 笔画特征
        stroke_features = self.compute_stroke_features(skeleton)
        
        # 5. 角度分布
        angles = self.compute_stroke_angles(skeleton)
        
        return {
            'center_of_mass': {'x': center[0], 'y': center[1]},
            'ratios': ratios,
            'stroke_features': stroke_features,
            'angles': angles,
            'skeleton': skeleton
        }
