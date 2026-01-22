"""
反馈生成模块
- 将评分差异转换为自然语言反馈
- 生成具体的改进建议
"""

from typing import Dict, List


class FeedbackGenerator:
    """反馈生成器"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        
        # 反馈模板
        self.templates = {
            # 重心相关
            'center_left': "字体重心偏左，建议整体向右调整。",
            'center_right': "字体重心偏右，建议整体向左调整。",
            'center_up': "字体重心偏上，建议适当下移。",
            'center_down': "字体重心偏下，建议适当上移。",
            'center_good': "重心位置较好，继续保持。",
            
            # 比例相关
            'upper_heavy': "上部占比过大，建议压缩上半部分。",
            'lower_heavy': "下部占比过大，建议压缩下半部分。",
            'left_heavy': "左部占比过大，建议适当收紧左侧。",
            'right_heavy': "右部占比过大，建议适当收紧右侧。",
            'ratio_good': "结构比例协调，继续保持。",
            
            # 笔画相关
            'stroke_short': "笔画整体偏短，可适当拉长。",
            'stroke_long': "笔画整体偏长，可适当收敛。",
            'stroke_angle': "笔画角度有偏差，注意横平竖直。",
            'stroke_good': "笔画到位，书写流畅。",
            
            # 综合评价
            'excellent': "书写优秀！结构工整，笔画到位。",
            'good': "书写良好，稍加注意细节即可更上一层楼。",
            'medium': "书写尚可，建议多加练习基本笔画。",
            'pass': "基本合格，需要加强练习，注意结构与笔画。",
            'need_improve': "需要加强，建议从基本笔画开始练习。"
        }
    
    def generate_feedback(self, score_result: Dict) -> Dict:
        """
        根据评分结果生成详细反馈
        Args:
            score_result: 评分结果字典 (来自 CalligraphyScorer.score_char)
        Returns:
            反馈结果字典
        """
        feedback_items = []
        suggestions = []
        
        dimensions = score_result.get('dimensions', {})
        student_features = score_result.get('student_features', {})
        template_features = score_result.get('template_features', {})
        
        # 1. 重心反馈
        center_feedback = self._analyze_center(
            student_features.get('center_of_mass', {}),
            template_features.get('center_of_mass', {}),
            dimensions.get('center_of_mass', 0)
        )
        feedback_items.extend(center_feedback['items'])
        suggestions.extend(center_feedback['suggestions'])
        
        # 2. 比例反馈
        ratio_feedback = self._analyze_ratios(
            student_features.get('ratios', {}),
            template_features.get('ratios', {}),
            dimensions.get('structure', 0)
        )
        feedback_items.extend(ratio_feedback['items'])
        suggestions.extend(ratio_feedback['suggestions'])
        
        # 3. 笔画反馈
        stroke_feedback = self._analyze_strokes(
            student_features.get('stroke_features', {}),
            template_features.get('stroke_features', {}),
            dimensions.get('stroke_accuracy', 0)
        )
        feedback_items.extend(stroke_feedback['items'])
        suggestions.extend(stroke_feedback['suggestions'])
        
        # 4. 综合评语
        overall_comment = self._get_overall_comment(score_result.get('grade', ''))
        
        return {
            'overall_comment': overall_comment,
            'feedback_items': feedback_items,
            'suggestions': suggestions,
            'score': score_result.get('total_score', 0),
            'grade': score_result.get('grade', '')
        }
    
    def _analyze_center(self, student_center: Dict, template_center: Dict, 
                        score: float) -> Dict:
        """分析重心偏差"""
        items = []
        suggestions = []
        
        if score >= 85:
            items.append(self.templates['center_good'])
        else:
            dx = student_center.get('x', 0.5) - template_center.get('x', 0.5)
            dy = student_center.get('y', 0.5) - template_center.get('y', 0.5)
            
            # 水平偏差
            if dx < -0.05:
                items.append(self.templates['center_left'])
                suggestions.append("练习时注意字的中心线，向右微调。")
            elif dx > 0.05:
                items.append(self.templates['center_right'])
                suggestions.append("练习时注意字的中心线，向左微调。")
            
            # 垂直偏差
            if dy < -0.05:
                items.append(self.templates['center_up'])
                suggestions.append("注意字的重心位置，适当下移。")
            elif dy > 0.05:
                items.append(self.templates['center_down'])
                suggestions.append("注意字的重心位置，适当上移。")
        
        return {'items': items, 'suggestions': suggestions}
    
    def _analyze_ratios(self, student_ratios: Dict, template_ratios: Dict,
                        score: float) -> Dict:
        """分析结构比例"""
        items = []
        suggestions = []
        
        if score >= 85:
            items.append(self.templates['ratio_good'])
        else:
            # 上下比例
            s_upper = student_ratios.get('upper_ratio', 0.5)
            t_upper = template_ratios.get('upper_ratio', 0.5)
            
            if s_upper - t_upper > 0.1:
                items.append(self.templates['upper_heavy'])
                suggestions.append("上半部分写得太大，下次注意控制。")
            elif t_upper - s_upper > 0.1:
                items.append(self.templates['lower_heavy'])
                suggestions.append("下半部分写得太大，注意上下均衡。")
            
            # 左右比例
            s_left = student_ratios.get('left_ratio', 0.5)
            t_left = template_ratios.get('left_ratio', 0.5)
            
            if s_left - t_left > 0.1:
                items.append(self.templates['left_heavy'])
                suggestions.append("左边部分写得太宽，注意收紧。")
            elif t_left - s_left > 0.1:
                items.append(self.templates['right_heavy'])
                suggestions.append("右边部分写得太宽，注意收紧。")
        
        return {'items': items, 'suggestions': suggestions}
    
    def _analyze_strokes(self, student_strokes: Dict, template_strokes: Dict,
                         score: float) -> Dict:
        """分析笔画特征"""
        items = []
        suggestions = []
        
        if score >= 85:
            items.append(self.templates['stroke_good'])
        else:
            s_length = student_strokes.get('total_length', 0)
            t_length = template_strokes.get('total_length', 0)
            
            if t_length > 0:
                ratio = s_length / t_length
                if ratio < 0.85:
                    items.append(self.templates['stroke_short'])
                    suggestions.append("笔画可以写得更舒展一些。")
                elif ratio > 1.15:
                    items.append(self.templates['stroke_long'])
                    suggestions.append("笔画稍微收敛一点会更好看。")
            
            # 笔画数量差异
            s_count = student_strokes.get('stroke_count', 0)
            t_count = template_strokes.get('stroke_count', 0)
            
            if s_count != t_count and t_count > 0:
                suggestions.append(f"注意笔画数量，标准字有{t_count}笔。")
        
        return {'items': items, 'suggestions': suggestions}
    
    def _get_overall_comment(self, grade: str) -> str:
        """获取综合评语"""
        grade_map = {
            '优秀': self.templates['excellent'],
            '良好': self.templates['good'],
            '中等': self.templates['medium'],
            '及格': self.templates['pass'],
            '需加强': self.templates['need_improve']
        }
        return grade_map.get(grade, "继续努力！")
    
    def format_feedback_text(self, feedback: Dict) -> str:
        """
        将反馈字典格式化为可读文本
        Args:
            feedback: 反馈字典
        Returns:
            格式化后的文本
        """
        lines = []
        
        # 评分和等级
        lines.append(f"📝 综合评分：{feedback['score']} 分 ({feedback['grade']})")
        lines.append("")
        
        # 总评
        lines.append(f"💬 总体评价：{feedback['overall_comment']}")
        lines.append("")
        
        # 详细反馈
        if feedback['feedback_items']:
            lines.append("📋 详细分析：")
            for item in feedback['feedback_items']:
                lines.append(f"  • {item}")
            lines.append("")
        
        # 改进建议
        if feedback['suggestions']:
            lines.append("💡 改进建议：")
            for i, suggestion in enumerate(feedback['suggestions'], 1):
                lines.append(f"  {i}. {suggestion}")
        
        return "\n".join(lines)
