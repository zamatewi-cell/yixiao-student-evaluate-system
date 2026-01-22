# -*- coding: utf-8 -*-
"""
数据导入导出路由模块
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
import io
import csv

from ..auth.dependencies import get_db_connection, require_admin, require_teacher, CurrentUser

router = APIRouter(prefix="/api/import-export", tags=["导入导出"])


# ============== 学生数据导入导出 ==============

@router.get("/students/export")
async def export_students(
    class_id: Optional[int] = None,
    grade_id: Optional[int] = None,
    current_user: CurrentUser = Depends(require_admin)
):
    """导出学生数据为CSV"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        sql = """
            SELECT s.student_no, s.name, s.gender, s.birth_date,
                   c.name as class_name, g.name as grade_name,
                   s.parent_name, s.parent_phone, s.status
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            LEFT JOIN grades g ON c.grade_id = g.id
            WHERE 1=1
        """
        params = []
        
        if class_id:
            sql += " AND s.class_id = %s"
            params.append(class_id)
        if grade_id:
            sql += " AND c.grade_id = %s"
            params.append(grade_id)
        
        sql += " ORDER BY g.sort_order, c.name, s.student_no"
        
        cursor.execute(sql, tuple(params))
        students = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 生成CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow(['学号', '姓名', '性别', '出生日期', '班级', '年级', '家长姓名', '家长电话', '状态'])
        
        # 写入数据
        for s in students:
            writer.writerow([
                s['student_no'],
                s['name'],
                '男' if s['gender'] == 'male' else '女',
                str(s['birth_date']) if s['birth_date'] else '',
                s['class_name'] or '',
                s['grade_name'] or '',
                s['parent_name'] or '',
                s['parent_phone'] or '',
                '在读' if s['status'] == 'active' else '已离校'
            ])
        
        output.seek(0)
        # 添加BOM以支持Excel中文
        content = '\ufeff' + output.getvalue()
        
        return StreamingResponse(
            io.BytesIO(content.encode('utf-8')),
            media_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename=students_{datetime.now().strftime("%Y%m%d")}.csv'}
        )
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/students/import")
async def import_students(
    file: UploadFile = File(...),
    class_id: int = None,
    current_user: CurrentUser = Depends(require_admin)
):
    """从CSV导入学生数据"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="请上传CSV文件")
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        content = await file.read()
        # 尝试不同编码
        try:
            text = content.decode('utf-8-sig')  # 处理BOM
        except:
            text = content.decode('gbk')
        
        reader = csv.DictReader(io.StringIO(text))
        
        cursor = conn.cursor()
        success_count = 0
        error_rows = []
        
        for row_num, row in enumerate(reader, start=2):
            try:
                student_no = row.get('学号', '').strip()
                name = row.get('姓名', '').strip()
                gender = 'male' if row.get('性别', '') == '男' else 'female'
                birth_date = row.get('出生日期', '').strip() or None
                parent_name = row.get('家长姓名', '').strip() or None
                parent_phone = row.get('家长电话', '').strip() or None
                
                if not student_no or not name:
                    error_rows.append(f"第{row_num}行：学号或姓名为空")
                    continue
                
                # 如果指定了class_id使用指定的，否则尝试根据班级名称查找
                target_class_id = class_id
                if not target_class_id and row.get('班级'):
                    cursor.execute("SELECT id FROM classes WHERE name = %s", (row.get('班级'),))
                    cls = cursor.fetchone()
                    if cls:
                        target_class_id = cls[0]
                
                # 插入或更新
                cursor.execute("""
                    INSERT INTO students (student_no, name, gender, birth_date, class_id, parent_name, parent_phone, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'active')
                    ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        gender = VALUES(gender),
                        birth_date = VALUES(birth_date),
                        class_id = VALUES(class_id),
                        parent_name = VALUES(parent_name),
                        parent_phone = VALUES(parent_phone)
                """, (student_no, name, gender, birth_date, target_class_id, parent_name, parent_phone))
                success_count += 1
            except Exception as e:
                error_rows.append(f"第{row_num}行：{str(e)}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "message": f"导入完成：成功{success_count}条",
            "success_count": success_count,
            "error_count": len(error_rows),
            "errors": error_rows[:10]  # 只返回前10条错误
        }
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


# ============== 教师数据导入导出 ==============

@router.get("/teachers/export")
async def export_teachers(
    current_user: CurrentUser = Depends(require_admin)
):
    """导出教师数据为CSV"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT t.employee_no, t.name, t.gender, t.subjects, t.title,
                   u.phone, u.email, u.is_active
            FROM teachers t
            LEFT JOIN users u ON t.user_id = u.id
            ORDER BY t.employee_no
        """)
        teachers = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 生成CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['工号', '姓名', '性别', '任教科目', '职称', '电话', '邮箱', '状态'])
        
        for t in teachers:
            writer.writerow([
                t['employee_no'] or '',
                t['name'],
                '男' if t['gender'] == 'male' else '女',
                t['subjects'] or '',
                t['title'] or '',
                t['phone'] or '',
                t['email'] or '',
                '在职' if t['is_active'] else '离职'
            ])
        
        output.seek(0)
        content = '\ufeff' + output.getvalue()
        
        return StreamingResponse(
            io.BytesIO(content.encode('utf-8')),
            media_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename=teachers_{datetime.now().strftime("%Y%m%d")}.csv'}
        )
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 成绩数据导入导出 ==============

@router.get("/scores/export/{exam_id}")
async def export_scores(
    exam_id: int,
    class_id: Optional[int] = None,
    current_user: CurrentUser = Depends(require_teacher)
):
    """导出考试成绩为CSV"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取考试信息
        cursor.execute("SELECT name FROM exams WHERE id = %s", (exam_id,))
        exam = cursor.fetchone()
        if not exam:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="考试不存在")
        
        # 获取科目列表
        cursor.execute("SELECT id, subject_name FROM exam_subjects WHERE exam_id = %s ORDER BY sort_order", (exam_id,))
        subjects = cursor.fetchall()
        
        # 获取学生成绩
        sql = """
            SELECT s.student_no, s.name as student_name, c.name as class_name
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            WHERE s.status = 'active'
        """
        params = []
        if class_id:
            sql += " AND s.class_id = %s"
            params.append(class_id)
        sql += " ORDER BY c.name, s.student_no"
        
        cursor.execute(sql, tuple(params))
        students = cursor.fetchall()
        
        # 获取每个学生的各科成绩
        for student in students:
            cursor.execute("""
                SELECT es.subject_id, es.score
                FROM exam_scores es
                JOIN students s ON es.student_id = s.id
                WHERE es.exam_id = %s AND s.student_no = %s
            """, (exam_id, student['student_no']))
            scores = {row['subject_id']: row['score'] for row in cursor.fetchall()}
            
            for subject in subjects:
                student[f"score_{subject['id']}"] = scores.get(subject['id'], '')
        
        cursor.close()
        conn.close()
        
        # 生成CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 表头
        header = ['学号', '姓名', '班级']
        for subject in subjects:
            header.append(subject['subject_name'])
        writer.writerow(header)
        
        # 数据
        for student in students:
            row = [student['student_no'], student['student_name'], student['class_name'] or '']
            for subject in subjects:
                score = student.get(f"score_{subject['id']}", '')
                row.append(score if score != '' else '')
            writer.writerow(row)
        
        output.seek(0)
        content = '\ufeff' + output.getvalue()
        
        exam_name = exam['name'].replace(' ', '_')
        return StreamingResponse(
            io.BytesIO(content.encode('utf-8')),
            media_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename=scores_{exam_name}_{datetime.now().strftime("%Y%m%d")}.csv'}
        )
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scores/import/{exam_id}")
async def import_scores(
    exam_id: int,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_teacher)
):
    """从CSV导入考试成绩"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="请上传CSV文件")
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        # 获取科目列表
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, subject_name FROM exam_subjects WHERE exam_id = %s", (exam_id,))
        subjects = {s['subject_name']: s['id'] for s in cursor.fetchall()}
        
        if not subjects:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail="考试没有设置科目")
        
        content = await file.read()
        try:
            text = content.decode('utf-8-sig')
        except:
            text = content.decode('gbk')
        
        reader = csv.DictReader(io.StringIO(text))
        
        success_count = 0
        error_rows = []
        
        for row_num, row in enumerate(reader, start=2):
            try:
                student_no = row.get('学号', '').strip()
                if not student_no:
                    continue
                
                # 查找学生
                cursor.execute("SELECT id FROM students WHERE student_no = %s", (student_no,))
                student = cursor.fetchone()
                if not student:
                    error_rows.append(f"第{row_num}行：学号{student_no}不存在")
                    continue
                
                student_id = student['id']
                
                # 录入各科成绩
                for subject_name, subject_id in subjects.items():
                    score_str = row.get(subject_name, '').strip()
                    if score_str:
                        try:
                            score = float(score_str)
                            cursor.execute("""
                                INSERT INTO exam_scores (exam_id, subject_id, student_id, score, recorded_by, created_at)
                                VALUES (%s, %s, %s, %s, %s, NOW())
                                ON DUPLICATE KEY UPDATE score = VALUES(score), recorded_by = VALUES(recorded_by), updated_at = NOW()
                            """, (exam_id, subject_id, student_id, score, current_user.id))
                            success_count += 1
                        except ValueError:
                            error_rows.append(f"第{row_num}行：{subject_name}成绩格式错误")
            except Exception as e:
                error_rows.append(f"第{row_num}行：{str(e)}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "message": f"导入完成：成功{success_count}条成绩",
            "success_count": success_count,
            "error_count": len(error_rows),
            "errors": error_rows[:10]
        }
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


# ============== 导出模板 ==============

@router.get("/templates/students")
async def get_student_template():
    """获取学生导入模板"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['学号', '姓名', '性别', '出生日期', '班级', '家长姓名', '家长电话'])
    writer.writerow(['2024001', '张三', '男', '2015-06-15', '一年级一班', '张父', '13800138000'])
    
    output.seek(0)
    content = '\ufeff' + output.getvalue()
    
    return StreamingResponse(
        io.BytesIO(content.encode('utf-8')),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename=student_template.csv'}
    )


@router.get("/templates/scores/{exam_id}")
async def get_score_template(
    exam_id: int,
    current_user: CurrentUser = Depends(require_teacher)
):
    """获取成绩导入模板"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT subject_name FROM exam_subjects WHERE exam_id = %s ORDER BY sort_order", (exam_id,))
        subjects = cursor.fetchall()
        cursor.close()
        conn.close()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        header = ['学号', '姓名', '班级']
        for s in subjects:
            header.append(s['subject_name'])
        writer.writerow(header)
        
        # 示例行
        example = ['2024001', '张三', '一年级一班']
        for _ in subjects:
            example.append('95')
        writer.writerow(example)
        
        output.seek(0)
        content = '\ufeff' + output.getvalue()
        
        return StreamingResponse(
            io.BytesIO(content.encode('utf-8')),
            media_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename=score_template_{exam_id}.csv'}
        )
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))
