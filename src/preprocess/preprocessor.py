"""
图像预处理模块
- 透视矫正
- 光照处理
- 二值化与去噪
- 尺度统一
"""

import cv2
import numpy as np
from typing import Tuple, Optional


class ImagePreprocessor:
    """图像预处理器"""
    
    def __init__(self, config: dict):
        self.target_size = tuple(config.get('preprocess', {}).get('target_size', [256, 256]))
        self.binary_threshold = config.get('preprocess', {}).get('binary_threshold', 127)
        self.denoise_kernel = config.get('preprocess', {}).get('denoise_kernel', 3)
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        完整预处理流程
        Args:
            image: 输入图像 (BGR格式)
        Returns:
            预处理后的二值图像
        """
        # 1. 灰度化
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 2. 光照均衡化
        gray = self.normalize_lighting(gray)
        
        # 3. 去噪
        denoised = self.denoise(gray)
        
        # 4. 二值化
        binary = self.binarize(denoised)
        
        return binary
    
    def normalize_lighting(self, gray: np.ndarray) -> np.ndarray:
        """光照归一化"""
        # 使用 CLAHE (自适应直方图均衡)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(gray)
    
    def denoise(self, image: np.ndarray) -> np.ndarray:
        """去噪"""
        return cv2.medianBlur(image, self.denoise_kernel)
    
    def binarize(self, gray: np.ndarray) -> np.ndarray:
        """自适应二值化"""
        # 使用自适应阈值，效果更好
        binary = cv2.adaptiveThreshold(
            gray, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 
            11, 2
        )
        return binary
    
    def perspective_correct(self, image: np.ndarray, 
                           corners: Optional[np.ndarray] = None) -> np.ndarray:
        """
        透视矫正
        Args:
            image: 输入图像
            corners: 四个角点坐标 (可选，如果不提供则自动检测)
        Returns:
            矫正后的图像
        """
        if corners is None:
            corners = self._detect_corners(image)
        
        if corners is None:
            return image  # 无法检测到角点，返回原图
        
        # 计算目标尺寸
        width = int(max(
            np.linalg.norm(corners[0] - corners[1]),
            np.linalg.norm(corners[2] - corners[3])
        ))
        height = int(max(
            np.linalg.norm(corners[0] - corners[3]),
            np.linalg.norm(corners[1] - corners[2])
        ))
        
        # 目标角点
        dst_corners = np.array([
            [0, 0],
            [width - 1, 0],
            [width - 1, height - 1],
            [0, height - 1]
        ], dtype=np.float32)
        
        # 透视变换
        M = cv2.getPerspectiveTransform(corners.astype(np.float32), dst_corners)
        corrected = cv2.warpPerspective(image, M, (width, height))
        
        return corrected
    
    def _detect_corners(self, image: np.ndarray) -> Optional[np.ndarray]:
        """自动检测纸张四角"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # 找最大轮廓
        max_contour = max(contours, key=cv2.contourArea)
        
        # 近似为四边形
        epsilon = 0.02 * cv2.arcLength(max_contour, True)
        approx = cv2.approxPolyDP(max_contour, epsilon, True)
        
        if len(approx) == 4:
            return approx.reshape(4, 2)
        
        return None
    
    def resize_char(self, char_image: np.ndarray) -> np.ndarray:
        """将单字图像调整为统一尺寸"""
        return cv2.resize(char_image, self.target_size, interpolation=cv2.INTER_AREA)
