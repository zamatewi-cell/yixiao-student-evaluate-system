# -*- coding: utf-8 -*-
"""
AI 评语生成模块 - 使用千问生成学生期末评语
"""
from typing import Optional, Dict, List
import mysql.connector
from mysql.connector import Error
import os

try:
    from dashscope import Generation
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False


# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Zrx@060309',
    'database': 'calligraphy_ai',
    'charset': 'utf8mb4'
}

# API Key (优先从环境变量读取)
QWEN_API_KEY = os.environ.get('QWEN_API_KEY', 'sk-64b7fb2c08b44369981491e4c65b03f6')


def get_db_connection():
    """获取数据库连接"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error:
        return None


class CommentGenerator:
    """
    评语生成器类 - 支持按需生成学生期末评语
    """
    
    def __init__(self, api_key: str = None):
        """
        初始化评语生成器
        
        Args:
            api_key: 千问API密钥，不提供则使用默认密钥
        """
        self.api_key = api_key or QWEN_API_KEY
    
    def generate_comment(
        self,
        student_name: str,
        gender: str,
        evaluations: List[Dict],
        semester_name: str = '',
        class_name: str = '',
        grade_name: str = '',
        special_achievements: str = None,
        areas_for_improvement: str = None
    ) -> Dict:
        """
        生成学生期末评语
        
        Args:
            student_name: 学生姓名
            gender: 性别 (male/female)
            evaluations: 评价数据列表，每项包含 category_name, indicator_name, value
            semester_name: 学期名称
            class_name: 班级名称
            grade_name: 年级名称
            special_achievements: 特殊成就（可选）
            areas_for_improvement: 需改进领域（可选）
            
        Returns:
            {success: bool, comment: str, error: str}
        """
        # 检查 dashscope 是否可用
        if not DASHSCOPE_AVAILABLE:
            return {
                "success": False,
                "comment": "",
                "error": "AI评语功能不可用（请安装dashscope库: pip install dashscope）"
            }
        
        # 如果没有评价数据，返回错误
        if not evaluations:
            return {
                "success": False,
                "comment": "",
                "error": "暂无评价数据"
            }
        
        # 格式化评价数据
        gender_text = "他" if gender == 'male' else "她"
        eval_text = self._format_evaluations(evaluations)
        
        # 构建提示词
        prompt = self._build_prompt(
            student_name=student_name,
            gender_text=gender_text,
            eval_text=eval_text,
            semester_name=semester_name,
            class_name=class_name,
            grade_name=grade_name,
            special_achievements=special_achievements,
            areas_for_improvement=areas_for_improvement
        )
        
        # 调用AI生成
        try:
            response = Generation.call(
                api_key=self.api_key,
                model='qwen-turbo',
                prompt=prompt,
                max_tokens=500
            )
            
            if response.status_code == 200:
                comment = response.output.text.strip()
                return {
                    "success": True,
                    "comment": comment,
                    "error": ""
                }
            else:
                return {
                    "success": False,
                    "comment": "",
                    "error": f"AI服务返回错误: {response.message}"
                }
        except Exception as e:
            return {
                "success": False,
                "comment": "",
                "error": f"生成评语失败: {str(e)}"
            }
    
    def _format_evaluations(self, evaluations: List[Dict]) -> str:
        """格式化评价数据为文本"""
        # 按分类组织评价
        categories = {}
        for ev in evaluations:
            cat = ev.get('category_name', '其他')
            if cat not in categories:
                categories[cat] = []
            indicator = ev.get('indicator_name', '')
            value = ev.get('value', '')
            categories[cat].append(f"{indicator}：{value}")
        
        text = ""
        for cat, items in categories.items():
            text += f"【{cat}】\n"
            text += "\n".join(items)
            text += "\n\n"
        
        return text.strip()
    
    def _build_prompt(
        self,
        student_name: str,
        gender_text: str,
        eval_text: str,
        semester_name: str,
        class_name: str,
        grade_name: str,
        special_achievements: str,
        areas_for_improvement: str
    ) -> str:
        """构建AI提示词"""
        prompt = f"""你是一位经验丰富的小学班主任，请根据以下学生的学期评价数据，为该学生撰写一段温暖、鼓励性的期末评语。

学生信息：
- 姓名：{student_name}
- 班级：{grade_name} {class_name}
- 学期：{semester_name}

评价数据：
{eval_text}
"""
        
        if special_achievements:
            prompt += f"\n特殊成就：{special_achievements}\n"
        
        if areas_for_improvement:
            prompt += f"\n需要改进的领域：{areas_for_improvement}\n"
        
        prompt += f"""
要求：
1. 评语长度控制在150-200字
2. 语气亲切、温暖，体现对学生的关爱
3. 先肯定学生的优点和进步
4. 针对不足之处给予建设性的鼓励
5. 展望未来，表达期待
6. 不要使用"该生"，直接用"你"来称呼学生

请直接输出评语内容，不需要任何开头或结尾说明："""
        
        return prompt


# ============== 辅助函数（兼容旧代码） ==============

def get_student_data(student_id: int, semester_id: int) -> Optional[Dict]:
    """获取学生评价数据"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 学生基本信息
        cursor.execute("""
            SELECT s.*, c.name as class_name, g.name as grade_name
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            LEFT JOIN grades g ON c.grade_id = g.id
            WHERE s.id = %s
        """, (student_id,))
        student = cursor.fetchone()
        
        if not student:
            cursor.close()
            conn.close()
            return None
        
        # 各项评价数据
        cursor.execute("""
            SELECT ic.name as category_name, i.name as indicator_name,
                   e.value, e.score
            FROM evaluations e
            JOIN indicators i ON e.indicator_id = i.id
            JOIN indicator_categories ic ON i.category_id = ic.id
            WHERE e.student_id = %s AND e.semester_id = %s
            ORDER BY ic.sort_order, i.sort_order
        """, (student_id, semester_id))
        evaluations = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            'student': student,
            'evaluations': evaluations
        }
    except Error:
        if conn:
            conn.close()
        return None


def generate_comment(student_id: int, semester_id: int, api_key: str = None) -> Optional[str]:
    """
    生成学生期末评语（兼容旧接口）
    
    Args:
        student_id: 学生ID
        semester_id: 学期ID
        api_key: 千问API密钥
        
    Returns:
        生成的评语
    """
    # 获取学生数据
    data = get_student_data(student_id, semester_id)
    if not data:
        return None
    
    student = data['student']
    evaluations = data['evaluations']
    
    if not evaluations:
        return "暂无评价数据"
    
    # 使用新的 CommentGenerator 类生成
    generator = CommentGenerator(api_key)
    result = generator.generate_comment(
        student_name=student['name'],
        gender=student.get('gender', 'male'),
        evaluations=evaluations,
        class_name=student.get('class_name', ''),
        grade_name=student.get('grade_name', '')
    )
    
    if result.get('success'):
        return result['comment']
    else:
        return result.get('error', '生成失败')


def batch_generate_comments(class_id: int, semester_id: int, api_key: str = None) -> List[Dict]:
    """
    批量生成班级所有学生的评语
    
    Returns:
        [{student_id, student_name, comment}, ...]
    """
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, name, gender FROM students 
            WHERE class_id = %s AND status = 'active'
            ORDER BY student_no
        """, (class_id,))
        students = cursor.fetchall()
        cursor.close()
        conn.close()
        
        generator = CommentGenerator(api_key)
        results = []
        
        for student in students:
            # 获取学生评价数据
            data = get_student_data(student['id'], semester_id)
            if not data or not data.get('evaluations'):
                results.append({
                    'student_id': student['id'],
                    'student_name': student['name'],
                    'success': False,
                    'comment': '暂无评价数据'
                })
                continue
            
            result = generator.generate_comment(
                student_name=student['name'],
                gender=student.get('gender', 'male'),
                evaluations=data['evaluations']
            )
            
            results.append({
                'student_id': student['id'],
                'student_name': student['name'],
                'success': result.get('success', False),
                'comment': result.get('comment') or result.get('error', '')
            })
        
        return results
    except Error:
        if conn:
            conn.close()
        return []


def save_comment(student_id: int, semester_id: int, ai_comment: str, 
                 teacher_comment: str = None, publish: bool = False) -> bool:
    """保存评语到数据库"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO semester_comments (student_id, semester_id, ai_comment, teacher_comment, is_published, generated_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE 
                ai_comment = VALUES(ai_comment),
                teacher_comment = COALESCE(VALUES(teacher_comment), teacher_comment),
                is_published = VALUES(is_published),
                updated_at = NOW()
        """, (student_id, semester_id, ai_comment, teacher_comment, publish))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Error:
        conn.close()
        return False
