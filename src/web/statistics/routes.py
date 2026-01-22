# -*- coding: utf-8 -*-
"""
统计路由模块 - 雷达图、统计报表等
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
import mysql.connector
from mysql.connector import Error
import json

from ..auth.dependencies import get_db_connection, require_admin, require_teacher, CurrentUser

router = APIRouter(prefix="/api/statistics", tags=["统计"])


# ============== 学生个人统计 ==============

@router.get("/student/{student_id}")
async def get_student_statistics(
    student_id: int,
    semester_id: Optional[int] = None,
    _: CurrentUser = Depends(require_teacher)
):
    """获取学生个人统计数据"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取学期
        if not semester_id:
            cursor.execute("SELECT id FROM semesters WHERE is_current = TRUE LIMIT 1")
            semester = cursor.fetchone()
            semester_id = semester['id'] if semester else None
        
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
            raise HTTPException(status_code=404, detail="学生不存在")
        
        # 各分类平均分（雷达图数据）
        cursor.execute("""
            SELECT ic.id, ic.name, AVG(e.score) as avg_score
            FROM indicator_categories ic
            LEFT JOIN indicators i ON ic.id = i.category_id AND i.is_active = TRUE
            LEFT JOIN evaluations e ON i.id = e.indicator_id 
                AND e.student_id = %s AND e.semester_id = %s
            GROUP BY ic.id, ic.name
            ORDER BY ic.sort_order
        """, (student_id, semester_id))
        categories = cursor.fetchall()
        
        # 书法平均分
        cursor.execute("""
            SELECT AVG(overall_score) as avg_score, COUNT(*) as count
            FROM grading_records
            WHERE student_id = %s AND status = 'completed'
        """, (student_id,))
        calligraphy = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # 构建雷达图数据
        radar = {
            'indicators': [{'name': c['name'], 'max': 100} for c in categories],
            'values': [round(c['avg_score'] or 0, 1) for c in categories]
        }
        
        return {
            'student': student,
            'radar': radar,
            'calligraphy': {
                'avg_score': round(calligraphy['avg_score'] or 0, 1),
                'count': calligraphy['count']
            }
        }
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 班级统计 ==============

@router.get("/class/{class_id}")
async def get_class_statistics(
    class_id: int,
    semester_id: Optional[int] = None,
    _: CurrentUser = Depends(require_teacher)
):
    """获取班级统计数据"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if not semester_id:
            cursor.execute("SELECT id FROM semesters WHERE is_current = TRUE LIMIT 1")
            semester = cursor.fetchone()
            semester_id = semester['id'] if semester else None
        
        # 班级信息
        cursor.execute("""
            SELECT c.*, g.name as grade_name
            FROM classes c
            LEFT JOIN grades g ON c.grade_id = g.id
            WHERE c.id = %s
        """, (class_id,))
        class_info = cursor.fetchone()
        
        # 班级平均分（按分类）
        cursor.execute("""
            SELECT ic.id, ic.name, AVG(e.score) as avg_score
            FROM indicator_categories ic
            LEFT JOIN indicators i ON ic.id = i.category_id AND i.is_active = TRUE
            LEFT JOIN evaluations e ON i.id = e.indicator_id AND e.semester_id = %s
            LEFT JOIN students s ON e.student_id = s.id AND s.class_id = %s
            GROUP BY ic.id, ic.name
            ORDER BY ic.sort_order
        """, (semester_id, class_id))
        categories = cursor.fetchall()
        
        # 学生排名（综合分）
        cursor.execute("""
            SELECT s.id, s.student_no, s.name, 
                   AVG(e.score) as avg_score,
                   COUNT(e.id) as eval_count
            FROM students s
            LEFT JOIN evaluations e ON s.id = e.student_id AND e.semester_id = %s
            WHERE s.class_id = %s AND s.status = 'active'
            GROUP BY s.id, s.student_no, s.name
            ORDER BY avg_score DESC
        """, (semester_id, class_id))
        rankings = cursor.fetchall()
        
        # 书法统计
        cursor.execute("""
            SELECT AVG(g.overall_score) as avg_score, COUNT(g.id) as count
            FROM grading_records g
            JOIN students s ON g.student_id = s.id
            WHERE s.class_id = %s AND g.status = 'completed'
        """, (class_id,))
        calligraphy = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        radar = {
            'indicators': [{'name': c['name'], 'max': 100} for c in categories],
            'values': [round(c['avg_score'] or 0, 1) for c in categories]
        }
        
        return {
            'class': class_info,
            'radar': radar,
            'rankings': rankings,
            'calligraphy': calligraphy
        }
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 年级统计 ==============

@router.get("/grade/{grade_id}")
async def get_grade_statistics(
    grade_id: int,
    semester_id: Optional[int] = None,
    _: CurrentUser = Depends(require_admin)
):
    """获取年级统计数据"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if not semester_id:
            cursor.execute("SELECT id FROM semesters WHERE is_current = TRUE LIMIT 1")
            semester = cursor.fetchone()
            semester_id = semester['id'] if semester else None
        
        # 年级信息
        cursor.execute("SELECT * FROM grades WHERE id = %s", (grade_id,))
        grade_info = cursor.fetchone()
        
        # 各班级平均分对比
        cursor.execute("""
            SELECT c.id, c.name, AVG(e.score) as avg_score
            FROM classes c
            LEFT JOIN students s ON c.id = s.class_id AND s.status = 'active'
            LEFT JOIN evaluations e ON s.id = e.student_id AND e.semester_id = %s
            WHERE c.grade_id = %s
            GROUP BY c.id, c.name
            ORDER BY c.name
        """, (semester_id, grade_id))
        classes = cursor.fetchall()
        
        # 年级整体雷达图
        cursor.execute("""
            SELECT ic.name, AVG(e.score) as avg_score
            FROM indicator_categories ic
            LEFT JOIN indicators i ON ic.id = i.category_id AND i.is_active = TRUE
            LEFT JOIN evaluations e ON i.id = e.indicator_id AND e.semester_id = %s
            LEFT JOIN students s ON e.student_id = s.id
            LEFT JOIN classes c ON s.class_id = c.id AND c.grade_id = %s
            GROUP BY ic.id, ic.name
            ORDER BY ic.sort_order
        """, (semester_id, grade_id))
        categories = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            'grade': grade_info,
            'classes': classes,
            'radar': {
                'indicators': [{'name': c['name'], 'max': 100} for c in categories],
                'values': [round(c['avg_score'] or 0, 1) for c in categories]
            }
        }
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 全校统计 ==============

@router.get("/school")
async def get_school_statistics(
    semester_id: Optional[int] = None,
    _: CurrentUser = Depends(require_admin)
):
    """获取全校统计数据"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if not semester_id:
            cursor.execute("SELECT id FROM semesters WHERE is_current = TRUE LIMIT 1")
            semester = cursor.fetchone()
            semester_id = semester['id'] if semester else None
        
        # 基础统计
        cursor.execute("SELECT COUNT(*) as count FROM students WHERE status = 'active'")
        student_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM teachers")
        teacher_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM classes")
        class_count = cursor.fetchone()['count']
        
        # 各年级平均分
        cursor.execute("""
            SELECT g.id, g.name, AVG(e.score) as avg_score
            FROM grades g
            LEFT JOIN classes c ON g.id = c.grade_id
            LEFT JOIN students s ON c.id = s.class_id AND s.status = 'active'
            LEFT JOIN evaluations e ON s.id = e.student_id AND e.semester_id = %s
            GROUP BY g.id, g.name
            ORDER BY g.sort_order
        """, (semester_id,))
        grades = cursor.fetchall()
        
        # 全校雷达图
        cursor.execute("""
            SELECT ic.name, AVG(e.score) as avg_score
            FROM indicator_categories ic
            LEFT JOIN indicators i ON ic.id = i.category_id AND i.is_active = TRUE
            LEFT JOIN evaluations e ON i.id = e.indicator_id AND e.semester_id = %s
            GROUP BY ic.id, ic.name
            ORDER BY ic.sort_order
        """, (semester_id,))
        categories = cursor.fetchall()
        
        # 书法统计
        cursor.execute("""
            SELECT COUNT(*) as count, AVG(overall_score) as avg_score
            FROM grading_records WHERE status = 'completed'
        """)
        calligraphy = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            'overview': {
                'student_count': student_count,
                'teacher_count': teacher_count,
                'class_count': class_count
            },
            'grades': grades,
            'radar': {
                'indicators': [{'name': c['name'], 'max': 100} for c in categories],
                'values': [round(c['avg_score'] or 0, 1) for c in categories]
            },
            'calligraphy': calligraphy
        }
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
