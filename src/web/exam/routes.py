# -*- coding: utf-8 -*-
"""
考试与成绩管理路由模块
"""
from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error

from ..auth.dependencies import get_db_connection, require_admin, require_teacher, CurrentUser

router = APIRouter(prefix="/api/exam", tags=["考试管理"])


# ============== 数据模型 ==============

class ExamCreate(BaseModel):
    """创建考试"""
    name: str
    exam_type: str = 'unit'  # unit/midterm/final/other
    semester_id: int
    grade_id: Optional[int] = None
    exam_date: Optional[str] = None
    subjects: List[dict] = []  # [{"name": "语文", "full_score": 100, "pass_score": 60, "excellent_score": 85}]


class ExamUpdate(BaseModel):
    """更新考试"""
    name: Optional[str] = None
    exam_type: Optional[str] = None
    exam_date: Optional[str] = None
    status: Optional[str] = None


class ScoreInput(BaseModel):
    """成绩录入"""
    exam_id: int
    subject_id: int
    scores: List[dict]  # [{"student_id": 1, "score": 95}, ...]


class ExamAnalysisInput(BaseModel):
    """试卷分析"""
    exam_id: int
    subject_id: int
    class_id: Optional[int] = None
    analysis_content: str


# ============== 考试管理 ==============

@router.get("/list")
async def list_exams(
    semester_id: Optional[int] = None,
    grade_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: CurrentUser = Depends(require_teacher)
):
    """获取考试列表"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        sql = """
            SELECT e.*, s.name as semester_name, g.name as grade_name,
                   (SELECT COUNT(*) FROM exam_subjects es WHERE es.exam_id = e.id) as subject_count
            FROM exams e
            LEFT JOIN semesters s ON e.semester_id = s.id
            LEFT JOIN grades g ON e.grade_id = g.id
            WHERE 1=1
        """
        params = []
        
        if semester_id:
            sql += " AND e.semester_id = %s"
            params.append(semester_id)
        if grade_id:
            sql += " AND e.grade_id = %s"
            params.append(grade_id)
        if status:
            sql += " AND e.status = %s"
            params.append(status)
        
        sql += " ORDER BY e.exam_date DESC, e.created_at DESC"
        
        cursor.execute(sql, tuple(params))
        exams = cursor.fetchall()
        
        # 格式化日期
        for exam in exams:
            if exam.get('exam_date'):
                exam['exam_date'] = str(exam['exam_date'])
            if exam.get('created_at'):
                exam['created_at'] = str(exam['created_at'])
        
        cursor.close()
        conn.close()
        return {"data": exams}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
async def create_exam(
    exam: ExamCreate,
    current_user: CurrentUser = Depends(require_admin)
):
    """创建考试"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        
        # 创建考试
        cursor.execute("""
            INSERT INTO exams (name, exam_type, semester_id, grade_id, exam_date, status, created_by, created_at)
            VALUES (%s, %s, %s, %s, %s, 'draft', %s, NOW())
        """, (exam.name, exam.exam_type, exam.semester_id, exam.grade_id, 
              exam.exam_date if exam.exam_date else None, current_user.id))
        exam_id = cursor.lastrowid
        
        # 添加考试科目
        for i, subject in enumerate(exam.subjects):
            cursor.execute("""
                INSERT INTO exam_subjects (exam_id, subject_name, full_score, pass_score, excellent_score, sort_order)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                exam_id,
                subject.get('name', '未命名'),
                subject.get('full_score', 100),
                subject.get('pass_score', 60),
                subject.get('excellent_score', 85),
                i
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "考试创建成功", "exam_id": exam_id}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{exam_id}")
async def get_exam_detail(
    exam_id: int,
    current_user: CurrentUser = Depends(require_teacher)
):
    """获取考试详情"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取考试信息
        cursor.execute("""
            SELECT e.*, s.name as semester_name, g.name as grade_name
            FROM exams e
            LEFT JOIN semesters s ON e.semester_id = s.id
            LEFT JOIN grades g ON e.grade_id = g.id
            WHERE e.id = %s
        """, (exam_id,))
        exam = cursor.fetchone()
        
        if not exam:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="考试不存在")
        
        # 获取科目列表
        cursor.execute("""
            SELECT * FROM exam_subjects WHERE exam_id = %s ORDER BY sort_order
        """, (exam_id,))
        subjects = cursor.fetchall()
        
        # 格式化
        if exam.get('exam_date'):
            exam['exam_date'] = str(exam['exam_date'])
        if exam.get('created_at'):
            exam['created_at'] = str(exam['created_at'])
        
        for subject in subjects:
            # 转换 Decimal 为 float
            for key in ['full_score', 'pass_score', 'excellent_score']:
                if subject.get(key):
                    subject[key] = float(subject[key])
        
        exam['subjects'] = subjects
        
        cursor.close()
        conn.close()
        return {"data": exam}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{exam_id}")
async def update_exam(
    exam_id: int,
    exam: ExamUpdate,
    current_user: CurrentUser = Depends(require_admin)
):
    """更新考试信息"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        
        updates = []
        values = []
        
        if exam.name:
            updates.append("name = %s")
            values.append(exam.name)
        if exam.exam_type:
            updates.append("exam_type = %s")
            values.append(exam.exam_type)
        if exam.exam_date:
            updates.append("exam_date = %s")
            values.append(exam.exam_date)
        if exam.status:
            updates.append("status = %s")
            values.append(exam.status)
        
        if updates:
            values.append(exam_id)
            sql = f"UPDATE exams SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(sql, tuple(values))
            conn.commit()
        
        cursor.close()
        conn.close()
        return {"message": "考试更新成功"}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{exam_id}")
async def delete_exam(
    exam_id: int,
    current_user: CurrentUser = Depends(require_admin)
):
    """删除考试"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM exams WHERE id = %s", (exam_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "考试删除成功"}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 成绩录入 ==============

@router.post("/scores/input")
async def input_scores(
    data: ScoreInput,
    current_user: CurrentUser = Depends(require_teacher)
):
    """录入成绩"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        success_count = 0
        
        for item in data.scores:
            student_id = item.get('student_id')
            score = item.get('score')
            
            if student_id is None or score is None:
                continue
            
            # 插入或更新成绩
            cursor.execute("""
                INSERT INTO exam_scores (exam_id, subject_id, student_id, score, recorded_by, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    score = VALUES(score),
                    recorded_by = VALUES(recorded_by),
                    updated_at = NOW()
            """, (data.exam_id, data.subject_id, student_id, score, current_user.id))
            success_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": f"成功录入 {success_count} 条成绩"}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scores/{exam_id}/{subject_id}")
async def get_subject_scores(
    exam_id: int,
    subject_id: int,
    class_id: Optional[int] = None,
    current_user: CurrentUser = Depends(require_teacher)
):
    """获取某科目成绩列表"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        sql = """
            SELECT s.id as student_id, s.student_no, s.name as student_name, s.gender,
                   c.name as class_name, g.name as grade_name,
                   es.score, es.class_rank, es.grade_rank
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            LEFT JOIN grades g ON c.grade_id = g.id
            LEFT JOIN exam_scores es ON s.id = es.student_id 
                AND es.exam_id = %s AND es.subject_id = %s
            WHERE s.status = 'active'
        """
        params = [exam_id, subject_id]
        
        if class_id:
            sql += " AND s.class_id = %s"
            params.append(class_id)
        
        sql += " ORDER BY c.name, s.student_no"
        
        cursor.execute(sql, tuple(params))
        scores = cursor.fetchall()
        
        # 转换 Decimal
        for item in scores:
            if item.get('score'):
                item['score'] = float(item['score'])
        
        cursor.close()
        conn.close()
        return {"data": scores}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 成绩统计 ==============

@router.post("/calculate-ranks/{exam_id}")
async def calculate_ranks(
    exam_id: int,
    current_user: CurrentUser = Depends(require_admin)
):
    """计算排名（班级排名和年级排名）"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取考试科目
        cursor.execute("SELECT id FROM exam_subjects WHERE exam_id = %s", (exam_id,))
        subjects = cursor.fetchall()
        
        for subject in subjects:
            subject_id = subject['id']
            
            # 计算班级排名
            cursor.execute("""
                UPDATE exam_scores es
                JOIN (
                    SELECT es2.id,
                           RANK() OVER (PARTITION BY s.class_id ORDER BY es2.score DESC) as class_rank
                    FROM exam_scores es2
                    JOIN students s ON es2.student_id = s.id
                    WHERE es2.exam_id = %s AND es2.subject_id = %s AND es2.score IS NOT NULL
                ) ranked ON es.id = ranked.id
                SET es.class_rank = ranked.class_rank
            """, (exam_id, subject_id))
            
            # 计算年级排名
            cursor.execute("""
                UPDATE exam_scores es
                JOIN (
                    SELECT es2.id,
                           RANK() OVER (ORDER BY es2.score DESC) as grade_rank
                    FROM exam_scores es2
                    WHERE es2.exam_id = %s AND es2.subject_id = %s AND es2.score IS NOT NULL
                ) ranked ON es.id = ranked.id
                SET es.grade_rank = ranked.grade_rank
            """, (exam_id, subject_id))
        
        # 计算总分和总分排名
        cursor.execute("""
            INSERT INTO exam_totals (exam_id, student_id, total_score, subject_count)
            SELECT %s, student_id, SUM(score), COUNT(*)
            FROM exam_scores
            WHERE exam_id = %s AND score IS NOT NULL
            GROUP BY student_id
            ON DUPLICATE KEY UPDATE
                total_score = VALUES(total_score),
                subject_count = VALUES(subject_count),
                updated_at = NOW()
        """, (exam_id, exam_id))
        
        # 计算总分班级排名
        cursor.execute("""
            UPDATE exam_totals et
            JOIN (
                SELECT et2.id,
                       RANK() OVER (PARTITION BY s.class_id ORDER BY et2.total_score DESC) as class_rank
                FROM exam_totals et2
                JOIN students s ON et2.student_id = s.id
                WHERE et2.exam_id = %s
            ) ranked ON et.id = ranked.id
            SET et.class_rank = ranked.class_rank
        """, (exam_id,))
        
        # 计算总分年级排名
        cursor.execute("""
            UPDATE exam_totals et
            JOIN (
                SELECT et2.id,
                       RANK() OVER (ORDER BY et2.total_score DESC) as grade_rank
                FROM exam_totals et2
                WHERE et2.exam_id = %s
            ) ranked ON et.id = ranked.id
            SET et.grade_rank = ranked.grade_rank
        """, (exam_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "排名计算完成"}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/{exam_id}")
async def get_exam_statistics(
    exam_id: int,
    class_id: Optional[int] = None,
    current_user: CurrentUser = Depends(require_teacher)
):
    """获取考试统计数据"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取科目统计
        sql = """
            SELECT 
                sub.id as subject_id,
                sub.subject_name,
                sub.full_score,
                sub.pass_score,
                sub.excellent_score,
                COUNT(es.id) as total_count,
                ROUND(AVG(es.score), 1) as avg_score,
                MAX(es.score) as max_score,
                MIN(es.score) as min_score,
                SUM(CASE WHEN es.score >= sub.pass_score THEN 1 ELSE 0 END) as pass_count,
                SUM(CASE WHEN es.score >= sub.excellent_score THEN 1 ELSE 0 END) as excellent_count
            FROM exam_subjects sub
            LEFT JOIN exam_scores es ON sub.id = es.subject_id AND es.score IS NOT NULL
        """
        
        if class_id:
            sql += " LEFT JOIN students s ON es.student_id = s.id AND s.class_id = %s"
            params = [exam_id, class_id]
        else:
            params = [exam_id]
        
        sql += " WHERE sub.exam_id = %s GROUP BY sub.id ORDER BY sub.sort_order"
        
        cursor.execute(sql, tuple(params))
        subjects = cursor.fetchall()
        
        # 计算及格率和优秀率
        for sub in subjects:
            total = sub['total_count'] or 0
            if total > 0:
                sub['pass_rate'] = round((sub['pass_count'] or 0) / total * 100, 1)
                sub['excellent_rate'] = round((sub['excellent_count'] or 0) / total * 100, 1)
            else:
                sub['pass_rate'] = 0
                sub['excellent_rate'] = 0
            
            # 转换 Decimal
            for key in ['full_score', 'pass_score', 'excellent_score', 'avg_score', 'max_score', 'min_score']:
                if sub.get(key):
                    sub[key] = float(sub[key])
        
        cursor.close()
        conn.close()
        return {"data": subjects}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 试卷分析 ==============

@router.post("/analysis")
async def save_exam_analysis(
    data: ExamAnalysisInput,
    current_user: CurrentUser = Depends(require_teacher)
):
    """保存试卷分析"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取教师ID
        cursor.execute("SELECT id FROM teachers WHERE user_id = %s", (current_user.id,))
        teacher = cursor.fetchone()
        teacher_id = teacher['id'] if teacher else None
        
        # 计算统计数据
        sql = """
            SELECT 
                COUNT(*) as total_count,
                ROUND(AVG(es.score), 1) as avg_score,
                MAX(es.score) as max_score,
                MIN(es.score) as min_score,
                SUM(CASE WHEN es.score >= sub.pass_score THEN 1 ELSE 0 END) as pass_count,
                SUM(CASE WHEN es.score >= sub.excellent_score THEN 1 ELSE 0 END) as excellent_count
            FROM exam_scores es
            JOIN exam_subjects sub ON es.subject_id = sub.id
        """
        params = [data.subject_id]
        
        if data.class_id:
            sql += " JOIN students s ON es.student_id = s.id WHERE es.subject_id = %s AND s.class_id = %s"
            params.append(data.class_id)
        else:
            sql += " WHERE es.subject_id = %s"
        
        cursor.execute(sql, tuple(params))
        stats = cursor.fetchone()
        
        # 计算及格率和优秀率
        total = stats['total_count'] or 0
        pass_rate = round((stats['pass_count'] or 0) / total * 100, 2) if total > 0 else 0
        excellent_rate = round((stats['excellent_count'] or 0) / total * 100, 2) if total > 0 else 0
        
        # 插入或更新分析
        cursor.execute("""
            INSERT INTO exam_analysis 
            (exam_id, subject_id, class_id, teacher_id, analysis_content, 
             avg_score, max_score, min_score, pass_count, excellent_count, total_count, pass_rate, excellent_rate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                analysis_content = VALUES(analysis_content),
                avg_score = VALUES(avg_score),
                max_score = VALUES(max_score),
                min_score = VALUES(min_score),
                pass_count = VALUES(pass_count),
                excellent_count = VALUES(excellent_count),
                total_count = VALUES(total_count),
                pass_rate = VALUES(pass_rate),
                excellent_rate = VALUES(excellent_rate),
                updated_at = NOW()
        """, (
            data.exam_id, data.subject_id, data.class_id, teacher_id, data.analysis_content,
            stats['avg_score'], stats['max_score'], stats['min_score'],
            stats['pass_count'], stats['excellent_count'], total,
            pass_rate, excellent_rate
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "试卷分析保存成功"}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/{exam_id}/{subject_id}")
async def get_exam_analysis(
    exam_id: int,
    subject_id: int,
    class_id: Optional[int] = None,
    current_user: CurrentUser = Depends(require_teacher)
):
    """获取试卷分析"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        sql = """
            SELECT ea.*, t.name as teacher_name, c.name as class_name
            FROM exam_analysis ea
            LEFT JOIN teachers t ON ea.teacher_id = t.id
            LEFT JOIN classes c ON ea.class_id = c.id
            WHERE ea.exam_id = %s AND ea.subject_id = %s
        """
        params = [exam_id, subject_id]
        
        if class_id:
            sql += " AND ea.class_id = %s"
            params.append(class_id)
        
        cursor.execute(sql, tuple(params))
        analysis = cursor.fetchone()
        
        if analysis:
            # 转换 Decimal
            for key in ['avg_score', 'max_score', 'min_score', 'pass_rate', 'excellent_rate']:
                if analysis.get(key):
                    analysis[key] = float(analysis[key])
            if analysis.get('created_at'):
                analysis['created_at'] = str(analysis['created_at'])
            if analysis.get('updated_at'):
                analysis['updated_at'] = str(analysis['updated_at'])
        
        cursor.close()
        conn.close()
        return {"data": analysis}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))
