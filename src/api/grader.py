"""
Calligraphy Grading Core Module
- Integrates preprocessing, detection, feature extraction, scoring, feedback
- Supports both algorithmic and AI-powered scoring
"""

import cv2
import numpy as np
from typing import Dict, List, Optional
from pathlib import Path

from src.preprocess.preprocessor import ImagePreprocessor
from src.detection.detector import TextDetector
from src.extraction.stroke_extractor import StrokeExtractor
from src.scoring.scorer import CalligraphyScorer
from src.feedback.generator import FeedbackGenerator


class CalligraphyGrader:
    """Calligraphy Grader - Main Pipeline Controller"""
    
    def __init__(self, config: dict, api_key: str = None, use_ai: bool = True):
        """
        Initialize grader
        Args:
            config: Configuration dictionary
            api_key: Qwen API key for AI scoring (optional)
            use_ai: Whether to enable AI scoring
        """
        self.config = config
        self.use_ai = use_ai
        self.api_key = api_key
        
        # Initialize modules
        self.preprocessor = ImagePreprocessor(config)
        self.detector = TextDetector(config)
        self.extractor = StrokeExtractor(config)
        self.scorer = CalligraphyScorer(config)
        self.feedback_gen = FeedbackGenerator(config)
        
        # Initialize AI scorer if enabled
        self.ai_scorer = None
        self.hybrid_scorer = None
        if use_ai and api_key:
            try:
                from src.scoring.ai_scorer import QwenAIScorer, HybridScorer
                self.ai_scorer = QwenAIScorer(api_key=api_key, config=config)
                self.hybrid_scorer = HybridScorer(config=config, api_key=api_key)
                print("AI Scoring enabled")
            except Exception as e:
                print(f"AI Scorer init failed: {e}, using algorithmic only")
                self.use_ai = False
        
        # Template features cache
        self.template_features_cache = {}
        self.template_image_cache = {}
    
    def _read_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Read image with support for Chinese file paths on Windows
        """
        try:
            # Use np.fromfile + imdecode to handle Chinese paths
            image = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
            return image
        except Exception:
            return None
    
    def grade(self, image_path: str) -> Dict:
        """
        Grade a single image
        Args:
            image_path: Image file path
        Returns:
            Grading result dictionary
        """
        # 1. Read image (supports Chinese paths)
        image = self._read_image(image_path)
        if image is None:
            return {'error': 'Cannot read image: {}'.format(image_path)}
        
        # 2. 预处理
        binary = self.preprocessor.preprocess(image)
        
        # 3. 检测单字
        chars = self.detector.detect_single_chars(image)
        
        if not chars:
            return {'error': '未检测到文字'}
        
        # 4. 逐字批改
        results = []
        for char_info in chars:
            char = char_info['char']
            bbox = np.array(char_info['bbox'])
            
            # 裁剪单字区域
            char_image = self.detector.crop_char(binary, bbox)
            if char_image.size == 0:
                continue
            
            # 统一尺寸
            char_image = self.preprocessor.resize_char(char_image)
            
            # 提取特征
            student_features = self.extractor.extract_all_features(char_image)
            
            # 获取标准字特征
            template_features = self._get_template_features(char)
            
            if template_features is None:
                # 没有找到标准模板，跳过评分
                results.append({
                    'char': char,
                    'bbox': bbox.tolist(),
                    'score': None,
                    'feedback': '未找到该字的标准模板'
                })
                continue
            
            # 评分
            score_result = self.scorer.score_char(student_features, template_features)
            
            # 生成反馈
            feedback = self.feedback_gen.generate_feedback(score_result)
            
            results.append({
                'char': char,
                'bbox': bbox.tolist(),
                'score': score_result['total_score'],
                'grade': score_result['grade'],
                'dimensions': score_result['dimensions'],
                'feedback': feedback['feedback_items'],
                'suggestions': feedback['suggestions']
            })
        
        # 5. 计算整体得分
        valid_scores = [r['score'] for r in results if r.get('score') is not None]
        overall_score = np.mean(valid_scores) if valid_scores else 0
        
        return {
            'overall_score': round(overall_score, 1),
            'char_count': len(results),
            'chars': results
        }
    
    def grade_single_char(self, char_image: np.ndarray, char: str) -> Dict:
        """
        批改单个字
        Args:
            char_image: 单字图像（已裁剪）
            char: 汉字字符
        Returns:
            批改结果
        """
        # 预处理
        if len(char_image.shape) == 3:
            binary = self.preprocessor.preprocess(char_image)
        else:
            binary = char_image
        
        # 统一尺寸
        binary = self.preprocessor.resize_char(binary)
        
        # 提取特征
        student_features = self.extractor.extract_all_features(binary)
        
        # 获取标准字特征
        template_features = self._get_template_features(char)
        
        if template_features is None:
            return {
                'char': char,
                'error': '未找到该字的标准模板'
            }
        
        # 评分
        score_result = self.scorer.score_char(student_features, template_features)
        
        # 生成反馈
        feedback = self.feedback_gen.generate_feedback(score_result)
        
        return {
            'char': char,
            'score': score_result['total_score'],
            'grade': score_result['grade'],
            'dimensions': score_result['dimensions'],
            'feedback_text': self.feedback_gen.format_feedback_text(feedback)
        }
    
    def _get_template_features(self, char: str) -> Optional[Dict]:
        """Get template features with caching"""
        if char in self.template_features_cache:
            return self.template_features_cache[char]
        
        # Load template
        template = self.scorer.load_template(char)
        
        if template is None:
            return None
        
        # Resize
        template = self.preprocessor.resize_char(template)
        
        # Cache template image
        self.template_image_cache[char] = template
        
        # Extract features
        features = self.extractor.extract_all_features(template)
        
        # Cache
        self.template_features_cache[char] = features
        
        return features
    
    def _get_template_image(self, char: str) -> Optional[np.ndarray]:
        """Get template image with caching"""
        if char in self.template_image_cache:
            return self.template_image_cache[char]
        
        # Load and cache via features method
        self._get_template_features(char)
        return self.template_image_cache.get(char)
    
    def grade_with_ai(self, image_path: str) -> Dict:
        """
        Grade image using AI scoring
        Args:
            image_path: Image file path
        Returns:
            AI scoring result
        """
        if not self.ai_scorer:
            return {'error': 'AI scorer not available'}
        
        return self.ai_scorer.score_image(image_path)
    
    def grade_single_char_with_ai(self, char_image: np.ndarray, char: str) -> Dict:
        """
        Grade single character with AI + algorithmic hybrid scoring
        Args:
            char_image: Character image
            char: The character
        Returns:
            Hybrid scoring result
        """
        # Preprocess
        if len(char_image.shape) == 3:
            binary = self.preprocessor.preprocess(char_image)
        else:
            binary = char_image
        
        binary = self.preprocessor.resize_char(binary)
        
        # Get template
        template = self._get_template_image(char)
        
        if template is None:
            return {'char': char, 'error': 'Template not found'}
        
        # Use hybrid scorer if available
        if self.hybrid_scorer:
            result = self.hybrid_scorer.score_char(binary, template, char, use_ai=True)
            return {
                'char': char,
                'score': result['total_score'],
                'grade': result['grade'],
                'dimensions': result['dimensions'],
                'algo_score': result.get('algo_score'),
                'ai_score': result.get('ai_score'),
                'feedback': result.get('feedback', {}),
                'overall_comment': result.get('overall_comment', ''),
                'scoring_method': result.get('scoring_method', 'hybrid')
            }
        
        # Fallback to algorithmic scoring
        return self.grade_single_char(char_image, char)
    
    def compare_with_template(self, char_image: np.ndarray, char: str) -> Dict:
        """
        Detailed AI comparison between student writing and template
        Args:
            char_image: Student's character image
            char: The character
        Returns:
            Detailed comparison analysis
        """
        if not self.ai_scorer:
            return {'error': 'AI scorer not available'}
        
        # Preprocess
        if len(char_image.shape) == 3:
            binary = self.preprocessor.preprocess(char_image)
        else:
            binary = char_image
        
        binary = self.preprocessor.resize_char(binary)
        
        # Get template
        template = self._get_template_image(char)
        
        if template is None:
            return {'char': char, 'error': 'Template not found'}
        
        return self.ai_scorer.compare_with_template(binary, template, char)
