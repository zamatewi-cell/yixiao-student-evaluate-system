# -*- coding: utf-8 -*-
"""
自动批改模块 - 扫描仪文件自动处理
"""
import os
import sys
import time
import shutil
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional
import mysql.connector
from mysql.connector import Error

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from .barcode import read_barcode_from_image, read_barcode_from_region


# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Zrx@060309',
    'database': 'calligraphy_ai',
    'charset': 'utf8mb4'
}


def get_db_connection():
    """获取数据库连接"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"Database error: {e}")
        return None


def get_student_by_barcode(barcode: str) -> Optional[dict]:
    """根据条码查询学生"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.id, s.student_no, s.name, s.class_id, c.name as class_name
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            WHERE s.barcode = %s OR s.student_no = %s
        """, (barcode, barcode))
        student = cursor.fetchone()
        cursor.close()
        conn.close()
        return student
    except Error as e:
        print(f"Query error: {e}")
        conn.close()
        return None


def get_current_semester_id() -> Optional[int]:
    """获取当前学期ID"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM semesters WHERE is_current = TRUE LIMIT 1")
        semester = cursor.fetchone()
        cursor.close()
        conn.close()
        return semester['id'] if semester else None
    except Error:
        conn.close()
        return None


def process_scanned_image(image_path: str, upload_dir: str, use_ai: bool = True) -> dict:
    """
    处理扫描的图片
    
    Args:
        image_path: 图片路径
        upload_dir: 上传目录
        use_ai: 是否使用AI评分
        
    Returns:
        处理结果
    """
    result = {
        'success': False,
        'image_path': image_path,
        'barcode': None,
        'student': None,
        'score': None,
        'message': ''
    }
    
    try:
        # 1. 识别条码
        barcode = read_barcode_from_image(image_path)
        if not barcode:
            barcode = read_barcode_from_region(image_path)
        
        result['barcode'] = barcode
        
        # 2. 查询学生
        student = None
        if barcode:
            student = get_student_by_barcode(barcode)
            result['student'] = student
        
        # 3. 复制文件到上传目录
        ext = Path(image_path).suffix or '.jpg'
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        dest_path = Path(upload_dir) / unique_filename
        shutil.copy2(image_path, dest_path)
        
        # 4. 调用批改系统
        from src.api.grader import CalligraphyGrader
        
        grader = CalligraphyGrader(
            api_key='sk-64b7fb2c08b44369981491e4c65b03f6' if use_ai else None,
            use_ai=use_ai
        )
        
        grade_result = grader.grade(str(dest_path))
        
        # AI评分
        ai_result = {}
        if use_ai:
            try:
                ai_result = grader.grade_with_ai(str(dest_path))
            except Exception as e:
                print(f"AI grading error: {e}")
        
        # 5. 保存到数据库
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            semester_id = get_current_semester_id()
            student_id = student['id'] if student else None
            overall_score = grade_result.get('overall_score', 0)
            
            # 确定等级
            if overall_score >= 90:
                grade = 'Excellent'
            elif overall_score >= 80:
                grade = 'Good'
            elif overall_score >= 70:
                grade = 'Medium'
            elif overall_score >= 60:
                grade = 'Pass'
            else:
                grade = 'NeedImprove'
            
            cursor.execute("""
                INSERT INTO grading_records 
                (student_id, filename, original_filename, file_path, barcode, semester_id,
                 overall_score, grade, char_count, ai_comment, strengths, suggestions, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'completed')
            """, (
                student_id,
                unique_filename,
                Path(image_path).name,
                str(dest_path),
                barcode,
                semester_id,
                overall_score,
                grade,
                grade_result.get('char_count', 0),
                ai_result.get('overall_comment', ''),
                ', '.join(ai_result.get('feedback', {}).get('strengths', [])),
                ', '.join(ai_result.get('feedback', {}).get('suggestions', []))
            ))
            
            record_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            conn.close()
            
            result['record_id'] = record_id
            result['score'] = overall_score
            result['grade'] = grade
            result['success'] = True
            result['message'] = f"批改成功！分数：{overall_score}"
            
            if student:
                result['message'] += f" 学生：{student['name']}"
            else:
                result['message'] += " (未识别到学生条码)"
        
        return result
        
    except Exception as e:
        result['message'] = f"处理失败: {e}"
        return result


def auto_grade_folder(watch_folder: str, upload_dir: str, use_ai: bool = True, 
                      move_processed: bool = True):
    """
    批量处理文件夹中的图片
    
    Args:
        watch_folder: 监控文件夹
        upload_dir: 上传目录
        use_ai: 是否使用AI评分
        move_processed: 是否移动已处理文件
    """
    watch_path = Path(watch_folder)
    processed_path = watch_path / 'processed'
    processed_path.mkdir(exist_ok=True)
    
    # 支持的图片格式
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    
    results = []
    
    for file_path in watch_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            print(f"Processing: {file_path.name}")
            
            result = process_scanned_image(str(file_path), upload_dir, use_ai)
            results.append(result)
            
            print(f"  Result: {result['message']}")
            
            # 移动已处理文件
            if move_processed:
                try:
                    shutil.move(str(file_path), str(processed_path / file_path.name))
                except:
                    pass
    
    return results
