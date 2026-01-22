# -*- coding: utf-8 -*-
"""
学生路由模块 - 查询个人评价、书法成绩等
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
from datetime import datetime

from ..auth.dependencies import get_db_connection, get_current_user, CurrentUser

router = APIRouter(prefix="/api/student", tags=["学生"])


# ============== 学生登录（简化版，学号+姓名） ==============

class StudentLoginRequest(BaseModel):
    student_no: str
    name: str


class StudentQueryRequest(BaseModel):
    """学生查询请求模型"""
    student_no: str
    name: str


@router.post("/simple-login")
async def student_simple_login(request: StudentLoginRequest):
    """学生简化登录（学号+姓名）"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.*, c.name as class_name, g.name as grade_name
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            LEFT JOIN grades g ON c.grade_id = g.id
            WHERE s.student_no = %s AND s.name = %s AND s.status = 'active'
        """, (request.student_no, request.name))
        student = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not student:
            raise HTTPException(status_code=401, detail="学号或姓名错误")
        
        # 返回学生信息（不需要token，简化版）
        return {
            "id": student['id'],
            "student_no": student['student_no'],
            "name": student['name'],
            "class_name": student['class_name'],
            "grade_name": student['grade_name']
        }
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== 学生综合查询（一次性获取所有数据） ==============

@router.post("/query")
async def query_student_data(request: StudentQueryRequest):
    """
    学生综合查询 - 通过学号和姓名查询学生的所有评价数据
    返回学生信息、评价数据、雷达图、期末评语和书法成绩
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 1. 验证学生身份
        cursor.execute("""
            SELECT s.id, s.student_no, s.name, s.gender, 
                   c.name as class_name, g.name as grade_name
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            LEFT JOIN grades g ON c.grade_id = g.id
            WHERE s.student_no = %s AND s.name = %s AND s.status = 'active'
        """, (request.student_no, request.name))
        student = cursor.fetchone()
        
        if not student:
            cursor.close()
            conn.close()
            return {"success": False, "message": "学号或姓名错误，请检查后重试"}
        
        student_id = student['id']
        
        # 2. 获取当前学期
        cursor.execute("SELECT id, name FROM semesters WHERE is_current = TRUE LIMIT 1")
        semester = cursor.fetchone()
        semester_id = semester['id'] if semester else None
        
        # 3. 获取评价数据
        evaluations = []
        if semester_id:
            cursor.execute("""
                SELECT ic.name as category, i.name as indicator,
                       e.value, e.score, e.recorded_at
                FROM evaluations e
                JOIN indicators i ON e.indicator_id = i.id
                JOIN indicator_categories ic ON i.category_id = ic.id
                WHERE e.student_id = %s AND e.semester_id = %s
                ORDER BY ic.sort_order, i.sort_order
            """, (student_id, semester_id))
            eval_rows = cursor.fetchall()
            for row in eval_rows:
                evaluations.append({
                    "category": row['category'],
                    "indicator": row['indicator'],
                    "value": row['value'] if row['value'] else row['score'],
                    "recorded_at": row['recorded_at'].strftime('%Y-%m-%d %H:%M') if row['recorded_at'] else ''
                })
        
        # 4. 获取雷达图数据
        radar_data = None
        if semester_id:
            cursor.execute("""
                SELECT ic.name as category_name, 
                       AVG(e.score) as avg_score,
                       MAX(i.max_score) as max_score
                FROM indicator_categories ic
                LEFT JOIN indicators i ON ic.id = i.category_id AND i.is_active = TRUE
                LEFT JOIN evaluations e ON i.id = e.indicator_id 
                    AND e.student_id = %s AND e.semester_id = %s
                GROUP BY ic.id, ic.name
                HAVING COUNT(e.id) > 0
                ORDER BY ic.sort_order
            """, (student_id, semester_id))
            categories = cursor.fetchall()
            
            if categories:
                radar_data = {
                    "categories": [c['category_name'] for c in categories],
                    "values": [round(c['avg_score'] or 0, 1) for c in categories],
                    "max_values": [c['max_score'] or 100 for c in categories]
                }
        
        # 5. 获取期末评语
        comments = []
        cursor.execute("""
            SELECT sc.ai_comment, sc.teacher_comment, sc.created_at, s.name as semester_name
            FROM semester_comments sc
            JOIN semesters s ON sc.semester_id = s.id
            WHERE sc.student_id = %s AND sc.is_published = TRUE
            ORDER BY s.start_date DESC
        """, (student_id,))
        comment_rows = cursor.fetchall()
        for row in comment_rows:
            comments.append({
                "semester_name": row['semester_name'],
                "ai_comment": row['ai_comment'] or '',
                "teacher_comment": row['teacher_comment'] or '',
                "created_at": row['created_at'].strftime('%Y-%m-%d %H:%M') if row['created_at'] else ''
            })
        
        # 6. 获取书法成绩
        calligraphy_records = []
        cursor.execute("""
            SELECT id, original_filename as filename, overall_score, ai_comment, 
                   upload_time as graded_at
            FROM grading_records
            WHERE student_id = %s AND status = 'completed'
            ORDER BY upload_time DESC
            LIMIT 20
        """, (student_id,))
        calligraphy_rows = cursor.fetchall()
        for row in calligraphy_rows:
            calligraphy_records.append({
                "id": row['id'],
                "filename": row['filename'] or '',
                "overall_score": row['overall_score'] or 0,
                "ai_comment": row['ai_comment'] or '',
                "graded_at": row['graded_at'].strftime('%Y-%m-%d %H:%M') if row['graded_at'] else ''
            })
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "student": student,
            "evaluations": evaluations,
            "radar_data": radar_data,
            "comments": comments,
            "calligraphy_records": calligraphy_records
        }
    
    except Error as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 获取学生评价数据 ==============

@router.get("/evaluations/{student_id}")
async def get_student_evaluations(
    student_id: int,
    semester_id: Optional[int] = None
):
    """获取学生评价数据"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 如果没指定学期，使用当前学期
        if not semester_id:
            cursor.execute("SELECT id FROM semesters WHERE is_current = TRUE LIMIT 1")
            semester = cursor.fetchone()
            if semester:
                semester_id = semester['id']
        
        # 获取评价数据
        cursor.execute("""
            SELECT ic.name as category_name, ic.id as category_id,
                   i.name as indicator_name, i.type, i.max_score,
                   e.value, e.score, e.remark
            FROM indicator_categories ic
            JOIN indicators i ON ic.id = i.category_id AND i.is_active = TRUE
            LEFT JOIN evaluations e ON i.id = e.indicator_id 
                AND e.student_id = %s AND e.semester_id = %s
            ORDER BY ic.sort_order, i.sort_order
        """, (student_id, semester_id))
        
        evaluations = cursor.fetchall()
        
        # 按分类分组
        categories = {}
        for ev in evaluations:
            cat_id = ev['category_id']
            if cat_id not in categories:
                categories[cat_id] = {
                    'name': ev['category_name'],
                    'indicators': []
                }
            categories[cat_id]['indicators'].append({
                'name': ev['indicator_name'],
                'type': ev['type'],
                'max_score': ev['max_score'],
                'value': ev['value'],
                'score': ev['score'],
                'remark': ev['remark']
            })
        
        cursor.close()
        conn.close()
        
        return {"semester_id": semester_id, "categories": list(categories.values())}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== 获取雷达图数据 ==============

@router.get("/radar/{student_id}")
async def get_student_radar(
    student_id: int,
    semester_id: Optional[int] = None
):
    """获取学生雷达图数据"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取当前学期
        if not semester_id:
            cursor.execute("SELECT id FROM semesters WHERE is_current = TRUE LIMIT 1")
            semester = cursor.fetchone()
            if semester:
                semester_id = semester['id']
        
        # 获取各分类平均分
        cursor.execute("""
            SELECT ic.name as category_name, 
                   AVG(e.score) as avg_score,
                   COUNT(e.id) as count
            FROM indicator_categories ic
            LEFT JOIN indicators i ON ic.id = i.category_id AND i.is_active = TRUE
            LEFT JOIN evaluations e ON i.id = e.indicator_id 
                AND e.student_id = %s AND e.semester_id = %s
            GROUP BY ic.id, ic.name
            ORDER BY ic.sort_order
        """, (student_id, semester_id))
        
        categories = cursor.fetchall()
        
        # 格式化为雷达图数据
        radar_data = {
            'indicators': [],
            'values': []
        }
        
        for cat in categories:
            radar_data['indicators'].append({
                'name': cat['category_name'],
                'max': 100
            })
            radar_data['values'].append(round(cat['avg_score'] or 0, 1))
        
        cursor.close()
        conn.close()
        
        return radar_data
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== 获取书法成绩 ==============

@router.get("/calligraphy/{student_id}")
async def get_student_calligraphy(
    student_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50)
):
    """获取学生书法批改记录"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            "SELECT COUNT(*) as total FROM grading_records WHERE student_id = %s AND status = 'completed'",
            (student_id,)
        )
        total = cursor.fetchone()['total']
        
        offset = (page - 1) * page_size
        cursor.execute("""
            SELECT id, filename, original_filename, upload_time, overall_score, grade,
                   char_count, ai_comment, strengths, suggestions
            FROM grading_records
            WHERE student_id = %s AND status = 'completed'
            ORDER BY upload_time DESC
            LIMIT %s OFFSET %s
        """, (student_id, page_size, offset))
        
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return {"total": total, "page": page, "page_size": page_size, "data": records}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== 获取期末评语 ==============

@router.get("/comments/{student_id}")
async def get_student_comments(
    student_id: int,
    semester_id: Optional[int] = None
):
    """获取学生期末评语"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if semester_id:
            cursor.execute("""
                SELECT sc.*, s.name as semester_name
                FROM semester_comments sc
                JOIN semesters s ON sc.semester_id = s.id
                WHERE sc.student_id = %s AND sc.semester_id = %s AND sc.is_published = TRUE
            """, (student_id, semester_id))
            comment = cursor.fetchone()
        else:
            cursor.execute("""
                SELECT sc.*, s.name as semester_name
                FROM semester_comments sc
                JOIN semesters s ON sc.semester_id = s.id
                WHERE sc.student_id = %s AND sc.is_published = TRUE
                ORDER BY s.start_date DESC
            """, (student_id,))
            comment = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {"data": comment}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
