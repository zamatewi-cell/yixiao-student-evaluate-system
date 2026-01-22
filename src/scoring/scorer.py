"""
评分模块
- 对比学生字与标准字
- 计算各维度得分
"""

import cv2
import numpy as np
from typing import Dict, Optional, Tuple
from pathlib import Path


class CalligraphyScorer:
    """书法评分器"""
    
    def __init__(self, config: dict):
        self.config = config
        scoring_config = config.get('scoring', {})
        
        # 权重配置
        weights = scoring_config.get('weights', {})
        self.weight_center = weights.get('center_of_mass', 0.25)
        self.weight_stroke = weights.get('stroke_accuracy', 0.40)
        self.weight_structure = weights.get('structure', 0.35)
        
        # 评级阈值
        thresholds = scoring_config.get('thresholds', {})
        self.threshold_excellent = thresholds.get('excellent', 90)
        self.threshold_good = thresholds.get('good', 75)
        self.threshold_medium = thresholds.get('medium', 60)
        self.threshold_pass = thresholds.get('pass', 45)
        
        # 标准字模板路径
        self.templates_path = Path(config.get('paths', {}).get('templates', 'data/templates'))
        self.templates_cache = {}
        
        # 初始化字体渲染器（延迟加载）
        self._font_renderer = None
    
    def _get_font_renderer(self):
        """获取字体渲染器（延迟初始化）"""
        if self._font_renderer is None:
            try:
                from src.utils.font_renderer import FontRenderer
                # 查找字体文件
                for font_file in self.templates_path.glob('*.ttf'):
                    self._font_renderer = FontRenderer(str(font_file))
                    print(f"已加载标准字体: {font_file.name}")
                    break
            except Exception as e:
                print(f"字体渲染器初始化失败: {e}")
        return self._font_renderer
    
    def load_template(self, char: str, target_size: Tuple[int, int] = (256, 256)) -> Optional[np.ndarray]:
        """
        加载标准字模板
        Args:
            char: 汉字字符
            target_size: 目标尺寸
        Returns:
            标准字图像 (二值化后，黑底白字)
        """
        cache_key = (char, target_size)
        if cache_key in self.templates_cache:
            return self.templates_cache[cache_key]
        
        template = None
        
        # 方法1: 尝试从预渲染的 PNG 文件加载
        template_path = self.templates_path / f"{char}.png"
        if template_path.exists():
            template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
            if template is not None:
                template = cv2.resize(template, target_size, interpolation=cv2.INTER_AREA)
                # 确保是二值图像（黑底白字）
                if np.mean(template) > 127:
                    template = 255 - template
                _, template = cv2.threshold(template, 127, 255, cv2.THRESH_BINARY)
        
        # 方法2: 检查 rendered 子目录
        if template is None:
            rendered_path = self.templates_path / "rendered" / f"{char}.png"
            if rendered_path.exists():
                template = cv2.imread(str(rendered_path), cv2.IMREAD_GRAYSCALE)
                if template is not None:
                    template = cv2.resize(template, target_size, interpolation=cv2.INTER_AREA)
        
        # 方法3: 使用字体实时渲染
        if template is None:
            renderer = self._get_font_renderer()
            if renderer:
                try:
                    template = renderer.render_char(char, target_size)
                except Exception as e:
                    pass
        
        if template is not None:
            self.templates_cache[cache_key] = template
        
        return template
    
    def score_center_of_mass(self, student_center: Dict, template_center: Dict) -> float:
        """
        评估重心偏差
        Args:
            student_center: 学生字重心 {'x': float, 'y': float}
            template_center: 标准字重心 {'x': float, 'y': float}
        Returns:
            得分 (0-100)
        """
        # 计算欧氏距离
        dx = student_center['x'] - template_center['x']
        dy = student_center['y'] - template_center['y']
        distance = np.sqrt(dx**2 + dy**2)
        
        # 距离越小分数越高，最大容忍偏差 0.3
        max_deviation = 0.3
        score = max(0, 100 * (1 - distance / max_deviation))
        
        return score
    
    def score_stroke_accuracy(self, student_features: Dict, template_features: Dict) -> float:
        """
        评估笔画到位度
        Args:
            student_features: 学生字笔画特征
            template_features: 标准字笔画特征
        Returns:
            得分 (0-100)
        """
        # 比较笔画总长度比例
        s_length = student_features.get('stroke_features', {}).get('total_length', 0)
        t_length = template_features.get('stroke_features', {}).get('total_length', 0)
        
        if t_length == 0:
            length_score = 50
        else:
            ratio = s_length / t_length
            # 比例越接近1分数越高
            length_score = 100 * max(0, 1 - abs(ratio - 1))
        
        # 比较角度分布
        s_angles = student_features.get('angles', [])
        t_angles = template_features.get('angles', [])
        
        if len(s_angles) > 0 and len(t_angles) > 0:
            # 计算角度直方图相似度
            s_hist, _ = np.histogram(s_angles, bins=36, range=(-180, 180))
            t_hist, _ = np.histogram(t_angles, bins=36, range=(-180, 180))
            
            # 归一化
            s_hist = s_hist.astype(float) / (s_hist.sum() + 1e-6)
            t_hist = t_hist.astype(float) / (t_hist.sum() + 1e-6)
            
            # 使用直方图相关性
            angle_score = 100 * max(0, cv2.compareHist(
                s_hist.astype(np.float32), 
                t_hist.astype(np.float32), 
                cv2.HISTCMP_CORREL
            ))
        else:
            angle_score = 50
        
        return 0.5 * length_score + 0.5 * angle_score
    
    def score_structure(self, student_features: Dict, template_features: Dict) -> float:
        """
        评估间架结构
        Args:
            student_features: 学生字特征
            template_features: 标准字特征
        Returns:
            得分 (0-100)
        """
        s_ratios = student_features.get('ratios', {})
        t_ratios = template_features.get('ratios', {})
        
        scores = []
        
        # 比较上下比例
        if 'upper_ratio' in s_ratios and 'upper_ratio' in t_ratios:
            diff = abs(s_ratios['upper_ratio'] - t_ratios['upper_ratio'])
            scores.append(100 * max(0, 1 - diff * 3))
        
        # 比较左右比例
        if 'left_ratio' in s_ratios and 'left_ratio' in t_ratios:
            diff = abs(s_ratios['left_ratio'] - t_ratios['left_ratio'])
            scores.append(100 * max(0, 1 - diff * 3))
        
        return np.mean(scores) if scores else 50
    
    def score_char(self, student_features: Dict, template_features: Dict) -> Dict:
        """
        对单个字进行综合评分
        Args:
            student_features: 学生字特征
            template_features: 标准字特征
        Returns:
            评分结果字典
        """
        # 各维度得分
        center_score = self.score_center_of_mass(
            student_features.get('center_of_mass', {'x': 0.5, 'y': 0.5}),
            template_features.get('center_of_mass', {'x': 0.5, 'y': 0.5})
        )
        
        stroke_score = self.score_stroke_accuracy(student_features, template_features)
        structure_score = self.score_structure(student_features, template_features)
        
        # 加权综合得分
        total_score = (
            self.weight_center * center_score +
            self.weight_stroke * stroke_score +
            self.weight_structure * structure_score
        )
        
        # 确定评级
        if total_score >= self.threshold_excellent:
            grade = '优秀'
        elif total_score >= self.threshold_good:
            grade = '良好'
        elif total_score >= self.threshold_medium:
            grade = '中等'
        elif total_score >= self.threshold_pass:
            grade = '及格'
        else:
            grade = '需加强'
        
        return {
            'total_score': round(total_score, 1),
            'grade': grade,
            'dimensions': {
                'center_of_mass': round(center_score, 1),
                'stroke_accuracy': round(stroke_score, 1),
                'structure': round(structure_score, 1)
            },
            'student_features': student_features,
            'template_features': template_features
        }
