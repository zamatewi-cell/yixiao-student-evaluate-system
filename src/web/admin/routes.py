# -*- coding: utf-8 -*-
"""
管理员路由模块 - 用户/学期/班级/学生/教师/指标管理
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64

from ..auth.dependencies import get_db_connection, require_admin, CurrentUser
from ..auth.jwt import get_password_hash

router = APIRouter(prefix="/api/admin", tags=["管理员"])


# ============== 数据模型 ==============

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = 'student'
    real_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class UserUpdate(BaseModel):
    real_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None


class SemesterCreate(BaseModel):
    name: str
    academic_year: str
    term: str
    start_date: str
    end_date: str
    is_current: bool = False


class ClassCreate(BaseModel):
    grade_id: int
    name: str
    head_teacher_id: Optional[int] = None


class StudentCreate(BaseModel):
    student_no: str
    name: str
    gender: str = 'male'
    class_id: Optional[int] = None
    birth_date: Optional[str] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None


class TeacherCreate(BaseModel):
    name: str
    gender: str = 'female'
    employee_no: Optional[str] = None
    subjects: Optional[str] = None
    title: Optional[str] = None
    password: Optional[str] = None  # 前端发送的初始密码
    phone: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None  # 'active' 或 'inactive' (在职/离职)


class IndicatorCreate(BaseModel):
    category_id: int
    name: str
    code: Optional[str] = None
    type: str = 'score'
    options: Optional[List[str]] = None
    max_score: float = 100
    description: Optional[str] = None
    weight: float = 1.0  # 权重
    is_active: bool = True  # 是否启用
    sort_order: int = 0  # 排序


# ============== 用户管理 ==============

@router.get("/users")
async def list_users(
    role: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: CurrentUser = Depends(require_admin)
):
    """获取用户列表"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        where_clauses = []
        params = []
        
        if role:
            where_clauses.append("role = %s")
            params.append(role)
        
        if search:
            where_clauses.append("(username LIKE %s OR real_name LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # 统计总数
        cursor.execute(f"SELECT COUNT(*) as total FROM users WHERE {where_sql}", params)
        total = cursor.fetchone()['total']
        
        # 分页查询
        offset = (page - 1) * page_size
        cursor.execute(f"""
            SELECT id, username, role, real_name, phone, email, is_active, last_login, created_at
            FROM users WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, params + [page_size, offset])
        
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return {"total": total, "page": page, "page_size": page_size, "data": users}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users")
async def create_user(
    user: UserCreate,
    _: CurrentUser = Depends(require_admin)
):
    """创建用户"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        password_hash = get_password_hash(user.password)
        
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, real_name, phone, email)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user.username, password_hash, user.role, user.real_name, user.phone, user.email))
        
        user_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"id": user_id, "message": "用户创建成功"}
    except Error as e:
        conn.close()
        if "Duplicate entry" in str(e):
            raise HTTPException(status_code=400, detail="用户名已存在")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user: UserUpdate,
    _: CurrentUser = Depends(require_admin)
):
    """更新用户"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        updates = []
        params = []
        
        if user.real_name is not None:
            updates.append("real_name = %s")
            params.append(user.real_name)
        if user.phone is not None:
            updates.append("phone = %s")
            params.append(user.phone)
        if user.email is not None:
            updates.append("email = %s")
            params.append(user.email)
        if user.is_active is not None:
            updates.append("is_active = %s")
            params.append(user.is_active)
        
        if updates:
            params.append(user_id)
            cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = %s", params)
            conn.commit()
        
        cursor.close()
        conn.close()
        return {"message": "更新成功"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, _: CurrentUser = Depends(require_admin)):
    """删除用户"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "删除成功"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 学期管理 ==============

@router.get("/semesters")
async def list_semesters(_: CurrentUser = Depends(require_admin)):
    """获取学期列表"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, name, academic_year, term, start_date, end_date, is_current, created_at
            FROM semesters
            ORDER BY academic_year DESC, term DESC
        """)
        semesters = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # 格式化日期字段
        for sem in semesters:
            if sem.get('start_date'):
                sem['start_date'] = str(sem['start_date'])
            if sem.get('end_date'):
                sem['end_date'] = str(sem['end_date'])
            if sem.get('created_at'):
                sem['created_at'] = str(sem['created_at'])
        
        return {"data": semesters}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/semesters")
async def create_semester(semester: SemesterCreate, _: CurrentUser = Depends(require_admin)):
    """创建学期"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        
        # 转换学期映射
        term_map = {"第一学期": "first", "第二学期": "second", "first": "first", "second": "second"}
        db_term = term_map.get(semester.term, "first")
        
        # 如果设为当前学期，先重置其他学期
        if semester.is_current:
            cursor.execute("UPDATE semesters SET is_current = FALSE")
            
        cursor.execute("""
            INSERT INTO semesters (name, academic_year, term, start_date, end_date, is_current)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (semester.name, semester.academic_year, db_term, semester.start_date, semester.end_date, semester.is_current))
        semester_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return {"id": semester_id, "message": "学期创建成功"}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")


@router.put("/semesters/{semester_id}/set-current")
async def set_current_semester(semester_id: int, _: CurrentUser = Depends(require_admin)):
    """设置当前学期"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE semesters SET is_current = FALSE")
        cursor.execute("UPDATE semesters SET is_current = TRUE WHERE id = %s", (semester_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "设置成功"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/semesters/{semester_id}/set-current")
async def set_current_semester_post(semester_id: int, _: CurrentUser = Depends(require_admin)):
    """设置当前学期(POST方式)"""
    return await set_current_semester(semester_id, _)


@router.put("/semesters/{semester_id}")
async def update_semester(semester_id: int, semester: SemesterCreate, _: CurrentUser = Depends(require_admin)):
    """更新学期"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        
        # 转换学期映射
        term_map = {"第一学期": "first", "第二学期": "second", "first": "first", "second": "second"}
        db_term = term_map.get(semester.term, "first")
        
        # 如果设为当前学期，先重置其他学期
        if semester.is_current:
            cursor.execute("UPDATE semesters SET is_current = FALSE")
            
        cursor.execute("""
            UPDATE semesters SET name=%s, academic_year=%s, term=%s, start_date=%s, end_date=%s, is_current=%s
            WHERE id = %s
        """, (semester.name, semester.academic_year, db_term, semester.start_date, semester.end_date, semester.is_current, semester_id))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "学期更新成功"}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")


@router.delete("/semesters/{semester_id}")
async def delete_semester(semester_id: int, _: CurrentUser = Depends(require_admin)):
    """删除学期"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM semesters WHERE id = %s", (semester_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "学期删除成功"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/semesters/{semester_id}/set-current")
async def set_current_semester(semester_id: int, _: CurrentUser = Depends(require_admin)):
    """设置当前学期"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        # 先重置所有学期的当前状态
        cursor.execute("UPDATE semesters SET is_current = FALSE")
        # 设置指定学期为当前学期
        cursor.execute("UPDATE semesters SET is_current = TRUE WHERE id = %s", (semester_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "已设置为当前学期"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 年级管理 ==============

@router.get("/grades")
async def list_grades(_: CurrentUser = Depends(require_admin)):
    """获取年级列表"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, sort_order FROM grades ORDER BY sort_order")
        grades = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"data": grades}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 班级管理 ==============

@router.get("/classes")
async def list_classes(
    grade_id: Optional[int] = None,
    _: CurrentUser = Depends(require_admin)
):
    """获取班级列表"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if grade_id:
            cursor.execute("""
                SELECT c.*, g.name as grade_name, t.name as head_teacher_name,
                       (SELECT COUNT(*) FROM students s WHERE s.class_id = c.id AND s.status = 'active') as student_count
                FROM classes c
                LEFT JOIN grades g ON c.grade_id = g.id
                LEFT JOIN teachers t ON c.head_teacher_id = t.id
                WHERE c.grade_id = %s
                ORDER BY g.sort_order, c.name
            """, (grade_id,))
        else:
            cursor.execute("""
                SELECT c.*, g.name as grade_name, t.name as head_teacher_name,
                       (SELECT COUNT(*) FROM students s WHERE s.class_id = c.id AND s.status = 'active') as student_count
                FROM classes c
                LEFT JOIN grades g ON c.grade_id = g.id
                LEFT JOIN teachers t ON c.head_teacher_id = t.id
                ORDER BY g.sort_order, c.name
            """)
        
        classes = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"data": classes}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classes")
async def create_class(cls: ClassCreate, _: CurrentUser = Depends(require_admin)):
    """创建班级"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO classes (grade_id, name, head_teacher_id)
            VALUES (%s, %s, %s)
        """, (cls.grade_id, cls.name, cls.head_teacher_id))
        class_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return {"id": class_id, "message": "班级创建成功"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/classes/{class_id}")
async def update_class(class_id: int, cls: ClassCreate, _: CurrentUser = Depends(require_admin)):
    """更新班级"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE classes SET grade_id=%s, name=%s, head_teacher_id=%s WHERE id=%s
        """, (cls.grade_id, cls.name, cls.head_teacher_id, class_id))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "班级更新成功"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/classes/{class_id}")
async def delete_class(class_id: int, _: CurrentUser = Depends(require_admin)):
    """删除班级"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM classes WHERE id = %s", (class_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "班级删除成功"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 学生管理 ==============

@router.get("/students")
async def list_students(
    class_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: CurrentUser = Depends(require_admin)
):
    """获取学生列表"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        where_clauses = ["s.status = 'active'"]
        params = []
        
        if class_id:
            where_clauses.append("s.class_id = %s")
            params.append(class_id)
        
        if search:
            where_clauses.append("(s.student_no LIKE %s OR s.name LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])
        
        where_sql = " AND ".join(where_clauses)
        
        cursor.execute(f"SELECT COUNT(*) as total FROM students s WHERE {where_sql}", params)
        total = cursor.fetchone()['total']
        
        offset = (page - 1) * page_size
        cursor.execute(f"""
            SELECT s.*, c.name as class_name, g.name as grade_name
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            LEFT JOIN grades g ON c.grade_id = g.id
            WHERE {where_sql}
            ORDER BY s.student_no
            LIMIT %s OFFSET %s
        """, params + [page_size, offset])
        
        students = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return {"total": total, "page": page, "page_size": page_size, "data": students}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/students")
async def create_student(student: StudentCreate, _: CurrentUser = Depends(require_admin)):
    """创建学生"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        
        # 创建用户账号
        password_hash = get_password_hash(student.student_no)  # 默认密码为学号
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, real_name)
            VALUES (%s, %s, 'student', %s)
        """, (student.student_no, password_hash, student.name))
        user_id = cursor.lastrowid
        
        # 创建学生记录
        cursor.execute("""
            INSERT INTO students (user_id, student_no, name, gender, class_id, barcode, birth_date, parent_name, parent_phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, student.student_no, student.name, student.gender, student.class_id, 
              student.student_no, student.birth_date, student.parent_name, student.parent_phone))
        
        student_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"id": student_id, "message": "学生创建成功"}
    except Error as e:
        conn.close()
        if "Duplicate entry" in str(e):
            raise HTTPException(status_code=400, detail="学号已存在")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/students/{student_id}/barcode")
async def get_student_barcode(student_id: int, _: CurrentUser = Depends(require_admin)):
    """生成学生条码图片"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT student_no, name, barcode FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not student:
            raise HTTPException(status_code=404, detail="学生不存在")
        
        # 生成条码
        code128 = barcode.get_barcode_class('code128')
        barcode_obj = code128(student['barcode'] or student['student_no'], writer=ImageWriter())
        
        buffer = BytesIO()
        barcode_obj.write(buffer)
        buffer.seek(0)
        
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        
        return {
            "student_no": student['student_no'],
            "name": student['name'],
            "barcode_image": f"data:image/png;base64,{img_base64}"
        }
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/students/{student_id}")
async def update_student(student_id: int, student: StudentCreate, _: CurrentUser = Depends(require_admin)):
    """更新学生信息"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE students SET name=%s, gender=%s, class_id=%s, birth_date=%s, parent_name=%s, parent_phone=%s
            WHERE id = %s
        """, (student.name, student.gender, student.class_id, student.birth_date, 
              student.parent_name, student.parent_phone, student_id))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "学生信息更新成功"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/students/{student_id}")
async def delete_student(student_id: int, _: CurrentUser = Depends(require_admin)):
    """删除学生"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        # 获取学生的user_id
        cursor.execute("SELECT user_id FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        if student:
            cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
            if student.get('user_id'):
                cursor.execute("DELETE FROM users WHERE id = %s", (student['user_id'],))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "学生删除成功"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 教师管理 ==============

@router.get("/teachers")
async def list_teachers(_: CurrentUser = Depends(require_admin)):
    """获取教师列表"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT t.id, t.user_id, t.name, t.gender, t.employee_no, t.subjects, t.title, 
                   t.can_edit,
                   u.username, u.phone, u.email, u.is_active,
                   CASE WHEN u.is_active = 1 THEN 'active' ELSE 'inactive' END as status,
                   (SELECT COUNT(*) FROM classes c WHERE c.head_teacher_id = t.id) as class_count
            FROM teachers t
            LEFT JOIN users u ON t.user_id = u.id
            ORDER BY t.name
        """)
        teachers = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"data": teachers}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teachers")
async def create_teacher(teacher: TeacherCreate, _: CurrentUser = Depends(require_admin)):
    """创建教师"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        
        # 创建用户账号
        username = teacher.employee_no or f"teacher_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        # 使用前端传入的密码，如果没有则使用默认密码
        password = teacher.password or "123456"
        password_hash = get_password_hash(password)
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, real_name, phone, email)
            VALUES (%s, %s, 'teacher', %s, %s, %s)
        """, (username, password_hash, teacher.name, teacher.phone, teacher.email))
        user_id = cursor.lastrowid
        
        # 创建教师记录
        cursor.execute("""
            INSERT INTO teachers (user_id, employee_no, name, gender, subjects, title)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, teacher.employee_no, teacher.name, teacher.gender, teacher.subjects, teacher.title))
        
        teacher_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"id": teacher_id, "username": username, "message": f"教师创建成功，密码：{password}"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/teachers/{teacher_id}")
async def update_teacher(teacher_id: int, teacher: TeacherCreate, _: CurrentUser = Depends(require_admin)):
    """更新教师信息"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取教师的 user_id
        cursor.execute("SELECT user_id FROM teachers WHERE id = %s", (teacher_id,))
        teacher_row = cursor.fetchone()
        if not teacher_row:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="教师不存在")
        
        user_id = teacher_row['user_id']
        
        # 更新教师表
        cursor.execute("""
            UPDATE teachers SET name=%s, gender=%s, subjects=%s, title=%s
            WHERE id = %s
        """, (teacher.name, teacher.gender, teacher.subjects, teacher.title, teacher_id))
        
        # 如果有 user_id，更新用户表的联系信息
        if user_id:
            cursor.execute("""
                UPDATE users SET real_name=%s, phone=%s, email=%s
                WHERE id = %s
            """, (teacher.name, teacher.phone, teacher.email, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "教师信息更新成功"}
    except Error as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/teachers/{teacher_id}")
async def delete_teacher(teacher_id: int, _: CurrentUser = Depends(require_admin)):
    """删除教师"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取教师的 user_id
        cursor.execute("SELECT user_id FROM teachers WHERE id = %s", (teacher_id,))
        teacher = cursor.fetchone()
        if teacher:
            cursor.execute("DELETE FROM teachers WHERE id = %s", (teacher_id,))
            # 同时删除关联的用户账号
            if teacher.get('user_id'):
                cursor.execute("DELETE FROM users WHERE id = %s", (teacher['user_id'],))
        
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "教师删除成功"}
    except Error as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teachers/{teacher_id}/authorize")
async def authorize_teacher(teacher_id: int, _: CurrentUser = Depends(require_admin)):
    """授权教师（启用账号）"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取教师的 user_id
        cursor.execute("SELECT user_id, name FROM teachers WHERE id = %s", (teacher_id,))
        teacher = cursor.fetchone()
        if not teacher:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="教师不存在")
        
        if teacher.get('user_id'):
            cursor.execute("UPDATE users SET is_active = TRUE WHERE id = %s", (teacher['user_id'],))
            conn.commit()
        
        cursor.close()
        conn.close()
        return {"message": f"教师 {teacher['name']} 已授权"}
    except Error as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teachers/{teacher_id}/disable")
async def disable_teacher(teacher_id: int, _: CurrentUser = Depends(require_admin)):
    """禁用教师账号"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取教师的 user_id
        cursor.execute("SELECT user_id, name FROM teachers WHERE id = %s", (teacher_id,))
        teacher = cursor.fetchone()
        if not teacher:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="教师不存在")
        
        if teacher.get('user_id'):
            cursor.execute("UPDATE users SET is_active = FALSE WHERE id = %s", (teacher['user_id'],))
            conn.commit()
        
        cursor.close()
        conn.close()
        return {"message": f"教师 {teacher['name']} 已禁用"}
    except Error as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teachers/{teacher_id}/grant-edit")
async def grant_teacher_edit_permission(teacher_id: int, _: CurrentUser = Depends(require_admin)):
    """授权教师编辑权限（允许数据录入和评语管理）"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取教师信息
        cursor.execute("SELECT id, name FROM teachers WHERE id = %s", (teacher_id,))
        teacher = cursor.fetchone()
        if not teacher:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="教师不存在")
        
        # 授权编辑权限
        cursor.execute("UPDATE teachers SET can_edit = TRUE WHERE id = %s", (teacher_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        return {"message": f"教师 {teacher['name']} 已获得数据编辑权限"}
    except Error as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teachers/{teacher_id}/revoke-edit")
async def revoke_teacher_edit_permission(teacher_id: int, _: CurrentUser = Depends(require_admin)):
    """取消教师编辑权限"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取教师信息
        cursor.execute("SELECT id, name FROM teachers WHERE id = %s", (teacher_id,))
        teacher = cursor.fetchone()
        if not teacher:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="教师不存在")
        
        # 取消编辑权限
        cursor.execute("UPDATE teachers SET can_edit = FALSE WHERE id = %s", (teacher_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        return {"message": f"教师 {teacher['name']} 的数据编辑权限已取消"}
    except Error as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 评价指标管理 ==============

@router.get("/indicator-categories")
async def list_indicator_categories(_: CurrentUser = Depends(require_admin)):
    """获取指标分类"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM indicator_categories ORDER BY sort_order")
        categories = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"data": categories}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indicators")
async def list_indicators(
    category_id: Optional[int] = None,
    _: CurrentUser = Depends(require_admin)
):
    """获取评价指标"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if category_id:
            cursor.execute("""
                SELECT i.*, c.name as category_name
                FROM indicators i
                LEFT JOIN indicator_categories c ON i.category_id = c.id
                WHERE i.category_id = %s AND i.is_active = TRUE
                ORDER BY i.sort_order
            """, (category_id,))
        else:
            cursor.execute("""
                SELECT i.*, c.name as category_name
                FROM indicators i
                LEFT JOIN indicator_categories c ON i.category_id = c.id
                ORDER BY c.sort_order, i.sort_order
            """)
        
        indicators = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # 格式化数据
        import json
        from decimal import Decimal
        for ind in indicators:
            # 将Decimal转换为float
            if isinstance(ind.get('weight'), Decimal):
                ind['weight'] = float(ind['weight'])
            if isinstance(ind.get('max_score'), Decimal):
                ind['max_score'] = float(ind['max_score'])
            if isinstance(ind.get('min_score'), Decimal):
                ind['min_score'] = float(ind['min_score'])
            # 解析options JSON字符串
            if ind.get('options') and isinstance(ind['options'], str):
                try:
                    ind['options'] = json.loads(ind['options'])
                except:
                    pass
        
        return {"data": indicators}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/indicators")
async def create_indicator(indicator: IndicatorCreate, _: CurrentUser = Depends(require_admin)):
    """创建评价指标"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        import json
        options_json = json.dumps(indicator.options, ensure_ascii=False) if indicator.options else None
        
        cursor.execute("""
            INSERT INTO indicators (category_id, name, code, type, options, max_score, description, weight, is_active, sort_order)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (indicator.category_id, indicator.name, indicator.code, indicator.type,
              options_json, indicator.max_score, indicator.description, 
              indicator.weight, indicator.is_active, indicator.sort_order))
        
        indicator_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"id": indicator_id, "message": "指标创建成功"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


class CategoryCreate(BaseModel):
    """分类创建模型"""
    name: str
    description: Optional[str] = None
    sort_order: int = 0


@router.post("/indicator-categories")
async def create_indicator_category(category: CategoryCreate, _: CurrentUser = Depends(require_admin)):
    """创建指标分类"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO indicator_categories (name, description, sort_order)
            VALUES (%s, %s, %s)
        """, (category.name, category.description, category.sort_order))
        category_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return {"id": category_id, "message": "分类创建成功"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/indicators/{indicator_id}")
async def update_indicator(indicator_id: int, indicator: IndicatorCreate, _: CurrentUser = Depends(require_admin)):
    """更新评价指标"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        import json
        options_json = json.dumps(indicator.options, ensure_ascii=False) if indicator.options else None
        
        cursor.execute("""
            UPDATE indicators SET category_id=%s, name=%s, code=%s, type=%s, options=%s, max_score=%s, description=%s, weight=%s, is_active=%s, sort_order=%s
            WHERE id = %s
        """, (indicator.category_id, indicator.name, indicator.code, indicator.type,
              options_json, indicator.max_score, indicator.description, 
              indicator.weight, indicator.is_active, indicator.sort_order, indicator_id))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "指标更新成功"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/indicators/{indicator_id}")
async def delete_indicator(indicator_id: int, _: CurrentUser = Depends(require_admin)):
    """删除评价指标"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM indicators WHERE id = %s", (indicator_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "指标删除成功"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/teachers/{teacher_id}")
async def update_teacher(teacher_id: int, teacher: TeacherCreate, _: CurrentUser = Depends(require_admin)):
    """更新教师"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取教师的 user_id
        cursor.execute("SELECT user_id FROM teachers WHERE id = %s", (teacher_id,))
        teacher_record = cursor.fetchone()
        if not teacher_record:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="教师不存在")
        
        user_id = teacher_record['user_id']
        
        # 更新 teachers 表
        cursor.execute("""
            UPDATE teachers SET name=%s, gender=%s, employee_no=%s, subjects=%s, title=%s
            WHERE id = %s
        """, (teacher.name, teacher.gender, teacher.employee_no, teacher.subjects, teacher.title, teacher_id))
        
        # 更新 users 表中的 phone、email 和 is_active
        # 构建动态更新语句
        user_updates = []
        user_params = []
        
        if teacher.phone is not None:
            user_updates.append("phone = %s")
            user_params.append(teacher.phone)
        if teacher.email is not None:
            user_updates.append("email = %s")
            user_params.append(teacher.email)
        if teacher.status is not None:
            is_active = 1 if teacher.status == 'active' else 0
            user_updates.append("is_active = %s")
            user_params.append(is_active)
        # 同步更新 real_name
        user_updates.append("real_name = %s")
        user_params.append(teacher.name)
        
        if user_updates:
            user_params.append(user_id)
            cursor.execute(f"UPDATE users SET {', '.join(user_updates)} WHERE id = %s", user_params)
        
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "教师更新成功"}
    except Error as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/teachers/{teacher_id}")
async def delete_teacher(teacher_id: int, _: CurrentUser = Depends(require_admin)):
    """删除教师"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        # 获取教师的user_id
        cursor.execute("SELECT user_id FROM teachers WHERE id = %s", (teacher_id,))
        teacher = cursor.fetchone()
        if teacher:
            cursor.execute("DELETE FROM teachers WHERE id = %s", (teacher_id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (teacher['user_id'],))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "教师删除成功"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 统计报表 ==============

@router.get("/dashboard-stats")
async def get_dashboard_stats(_: CurrentUser = Depends(require_admin)):
    """获取仪表盘统计数据"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 学生总数
        cursor.execute("SELECT COUNT(*) as count FROM students WHERE status = 'active'")
        student_count = cursor.fetchone()['count']
        
        # 教师总数
        cursor.execute("SELECT COUNT(*) as count FROM teachers")
        teacher_count = cursor.fetchone()['count']
        
        # 班级总数
        cursor.execute("SELECT COUNT(*) as count FROM classes")
        class_count = cursor.fetchone()['count']
        
        # 评价记录总数
        cursor.execute("SELECT COUNT(*) as count FROM evaluations")
        evaluation_count = cursor.fetchone()['count']
        
        # 各年级统计
        cursor.execute("""
            SELECT g.name, COUNT(DISTINCT s.id) as student_count,
                   COALESCE(AVG(CAST(e.value AS DECIMAL(10,2))), 0) as avg_score
            FROM grades g
            LEFT JOIN classes c ON g.id = c.grade_id
            LEFT JOIN students s ON c.id = s.class_id AND s.status = 'active'
            LEFT JOIN evaluations e ON s.id = e.student_id
            GROUP BY g.id, g.name
            ORDER BY g.sort_order
        """)
        grades = cursor.fetchall()
        
        # 各分类评价统计
        cursor.execute("""
            SELECT ic.name, COUNT(e.id) as count
            FROM indicator_categories ic
            LEFT JOIN indicators i ON ic.id = i.category_id
            LEFT JOIN evaluations e ON i.id = e.indicator_id
            GROUP BY ic.id, ic.name
            ORDER BY ic.sort_order
        """)
        categories = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "overview": {
                "student_count": student_count,
                "teacher_count": teacher_count,
                "class_count": class_count,
                "evaluation_count": evaluation_count
            },
            "grades": grades,
            "categories": categories
        }
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics(
    semester_id: Optional[int] = None,
    _: CurrentUser = Depends(require_admin)
):
    """获取综合统计数据"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 使用指定学期或当前学期
        if not semester_id:
            cursor.execute("SELECT id FROM semesters WHERE is_current = TRUE LIMIT 1")
            sem = cursor.fetchone()
            if sem:
                semester_id = sem['id']
        
        # 学生总数
        cursor.execute("SELECT COUNT(*) as count FROM students WHERE status = 'active'")
        total_students = cursor.fetchone()['count']
        
        # 教师总数
        cursor.execute("SELECT COUNT(*) as count FROM teachers")
        total_teachers = cursor.fetchone()['count']
        
        # 评价记录总数
        where_clause = "WHERE e.semester_id = %s" if semester_id else ""
        params = [semester_id] if semester_id else []
        cursor.execute(f"SELECT COUNT(*) as count FROM evaluations e {where_clause}", params)
        total_evaluations = cursor.fetchone()['count']
        
        # 评语总数
        cursor.execute(f"SELECT COUNT(*) as count FROM student_comments sc {where_clause.replace('e.', 'sc.')}", params)
        total_comments = cursor.fetchone()['count']
        
        # 班级统计
        cursor.execute("""
            SELECT c.name as class_name, g.name as grade_name,
                   COUNT(DISTINCT s.id) as student_count,
                   COUNT(e.id) as evaluation_count,
                   COALESCE(AVG(CAST(e.value AS DECIMAL(10,2))), 0) as avg_score
            FROM classes c
            JOIN grades g ON c.grade_id = g.id
            LEFT JOIN students s ON c.id = s.class_id AND s.status = 'active'
            LEFT JOIN evaluations e ON s.id = e.student_id
            GROUP BY c.id, c.name, g.name
            ORDER BY g.sort_order, c.name
        """)
        class_stats = cursor.fetchall()
        
        # 指标统计
        cursor.execute("""
            SELECT i.name, ic.name as category_name,
                   COALESCE(AVG(CAST(e.value AS DECIMAL(10,2))), 0) as avg_score,
                   COUNT(e.id) as count
            FROM indicators i
            LEFT JOIN indicator_categories ic ON i.category_id = ic.id
            LEFT JOIN evaluations e ON i.id = e.indicator_id
            WHERE i.is_active = TRUE
            GROUP BY i.id, i.name, ic.name
            ORDER BY ic.sort_order, i.sort_order
        """)
        indicator_stats = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "total_students": total_students,
            "total_teachers": total_teachers,
            "total_evaluations": total_evaluations,
            "total_comments": total_comments,
            "class_stats": class_stats,
            "indicator_stats": indicator_stats
        }
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 学生转班 ==============

class StudentTransferRequest(BaseModel):
    student_id: int
    to_class_id: int
    reason: Optional[str] = None


@router.post("/students/transfer")
async def transfer_student(
    data: StudentTransferRequest,
    current_user: CurrentUser = Depends(require_admin)
):
    """学生转班"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取学生当前班级
        cursor.execute("SELECT class_id FROM students WHERE id = %s", (data.student_id,))
        student = cursor.fetchone()
        if not student:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="学生不存在")
        
        from_class_id = student['class_id']
        
        # 更新学生班级
        cursor.execute("""
            UPDATE students SET class_id = %s WHERE id = %s
        """, (data.to_class_id, data.student_id))
        
        # 记录转班历史
        cursor.execute("""
            INSERT INTO student_transfers 
            (student_id, transfer_type, from_class_id, to_class_id, transfer_date, reason, operated_by, created_at)
            VALUES (%s, 'class_transfer', %s, %s, CURDATE(), %s, %s, NOW())
        """, (data.student_id, from_class_id, data.to_class_id, data.reason, current_user.id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "转班成功"}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 学年升级 ==============

@router.post("/students/grade-upgrade")
async def grade_upgrade(
    current_user: CurrentUser = Depends(require_admin)
):
    """全校学年升级（六年级毕业，其他年级升级）"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取所有年级
        cursor.execute("SELECT id, name, sort_order FROM grades ORDER BY sort_order DESC")
        grades = cursor.fetchall()
        
        upgrade_count = 0
        graduate_count = 0
        
        for grade in grades:
            grade_id = grade['id']
            sort_order = grade['sort_order']
            
            # 获取该年级的所有班级
            cursor.execute("SELECT id FROM classes WHERE grade_id = %s", (grade_id,))
            classes = cursor.fetchall()
            
            for cls in classes:
                class_id = cls['id']
                
                if sort_order == 6:  # 六年级，标记毕业
                    # 获取学生列表
                    cursor.execute("""
                        SELECT id FROM students 
                        WHERE class_id = %s AND status = 'active' AND (enrollment_status IS NULL OR enrollment_status = 'enrolled')
                    """, (class_id,))
                    students = cursor.fetchall()
                    
                    for student in students:
                        # 更新学生状态为毕业
                        cursor.execute("""
                            UPDATE students SET enrollment_status = 'graduated', graduation_year = YEAR(CURDATE())
                            WHERE id = %s
                        """, (student['id'],))
                        
                        # 记录毕业历史
                        cursor.execute("""
                            INSERT INTO student_transfers 
                            (student_id, transfer_type, from_class_id, from_grade_id, transfer_date, operated_by, created_at)
                            VALUES (%s, 'graduation', %s, %s, CURDATE(), %s, NOW())
                        """, (student['id'], class_id, grade_id, current_user.id))
                        
                        graduate_count += 1
                else:
                    # 其他年级升级 - 查找下一个年级
                    cursor.execute("""
                        SELECT id FROM grades WHERE sort_order = %s
                    """, (sort_order + 1,))
                    next_grade = cursor.fetchone()
                    
                    if next_grade:
                        next_grade_id = next_grade['id']
                        
                        # 查找目标年级对应的班级（按班级名称匹配）
                        cursor.execute("""
                            SELECT c2.id as to_class_id
                            FROM classes c1
                            JOIN classes c2 ON REPLACE(REPLACE(c1.name, CAST(c1.grade_id AS CHAR), ''), '年级', '') 
                                            = REPLACE(REPLACE(c2.name, CAST(c2.grade_id AS CHAR), ''), '年级', '')
                            WHERE c1.id = %s AND c2.grade_id = %s
                        """, (class_id, next_grade_id))
                        target_class = cursor.fetchone()
                        
                        # 如果找不到对应班级，尝试简单匹配
                        if not target_class:
                            # 获取当前班级名称中的班号
                            cursor.execute("SELECT name FROM classes WHERE id = %s", (class_id,))
                            current_class = cursor.fetchone()
                            class_name = current_class['name'] if current_class else ''
                            
                            # 提取班号（如 "一班" -> "一"）
                            import re
                            match = re.search(r'([一二三四五六七八九十\d]+)班', class_name)
                            if match:
                                class_num = match.group(1)
                                cursor.execute("""
                                    SELECT id FROM classes 
                                    WHERE grade_id = %s AND name LIKE %s
                                """, (next_grade_id, f'%{class_num}班%'))
                                target_class = cursor.fetchone()
                        
                        if target_class:
                            to_class_id = target_class['to_class_id'] if 'to_class_id' in target_class else target_class['id']
                            
                            # 获取学生列表
                            cursor.execute("""
                                SELECT id FROM students 
                                WHERE class_id = %s AND status = 'active' AND (enrollment_status IS NULL OR enrollment_status = 'enrolled')
                            """, (class_id,))
                            students = cursor.fetchall()
                            
                            for student in students:
                                # 更新学生班级
                                cursor.execute("""
                                    UPDATE students SET class_id = %s WHERE id = %s
                                """, (to_class_id, student['id']))
                                
                                # 记录升级历史
                                cursor.execute("""
                                    INSERT INTO student_transfers 
                                    (student_id, transfer_type, from_class_id, to_class_id, from_grade_id, to_grade_id, transfer_date, operated_by, created_at)
                                    VALUES (%s, 'grade_upgrade', %s, %s, %s, %s, CURDATE(), %s, NOW())
                                """, (student['id'], class_id, to_class_id, grade_id, next_grade_id, current_user.id))
                                
                                upgrade_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "message": f"学年升级完成：{upgrade_count}人升级，{graduate_count}人毕业",
            "upgrade_count": upgrade_count,
            "graduate_count": graduate_count
        }
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 数据库备份 ==============

@router.post("/system/backup")
async def create_backup(
    current_user: CurrentUser = Depends(require_admin)
):
    """创建数据库备份"""
    import subprocess
    import os
    from datetime import datetime
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        
        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{timestamp}.sql"
        backup_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backups')
        
        # 创建备份目录
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, backup_name)
        
        # 记录备份任务
        cursor.execute("""
            INSERT INTO system_backups (backup_name, backup_path, backup_type, status, created_by, created_at)
            VALUES (%s, %s, 'manual', 'pending', %s, NOW())
        """, (backup_name, backup_path, current_user.id))
        backup_id = cursor.lastrowid
        conn.commit()
        
        # 执行备份命令（注意：需要配置mysqldump路径）
        try:
            # 从配置获取数据库信息
            from ...config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
            
            cmd = f'mysqldump -h {DB_HOST} -u {DB_USER} -p{DB_PASSWORD} {DB_NAME} > "{backup_path}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                # 获取文件大小
                file_size = os.path.getsize(backup_path) if os.path.exists(backup_path) else 0
                
                cursor.execute("""
                    UPDATE system_backups SET status = 'success', backup_size = %s, completed_at = NOW()
                    WHERE id = %s
                """, (file_size, backup_id))
                conn.commit()
                
                cursor.close()
                conn.close()
                return {"message": "备份成功", "backup_name": backup_name, "size": file_size}
            else:
                cursor.execute("""
                    UPDATE system_backups SET status = 'failed' WHERE id = %s
                """, (backup_id,))
                conn.commit()
                
                cursor.close()
                conn.close()
                raise HTTPException(status_code=500, detail=f"备份失败: {result.stderr}")
        except Exception as e:
            cursor.execute("""
                UPDATE system_backups SET status = 'failed' WHERE id = %s
            """, (backup_id,))
            conn.commit()
            raise HTTPException(status_code=500, detail=f"备份失败: {str(e)}")
        
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/backups")
async def list_backups(
    current_user: CurrentUser = Depends(require_admin)
):
    """获取备份列表"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM system_backups ORDER BY created_at DESC LIMIT 50
        """)
        backups = cursor.fetchall()
        
        for backup in backups:
            if backup.get('created_at'):
                backup['created_at'] = str(backup['created_at'])
            if backup.get('completed_at'):
                backup['completed_at'] = str(backup['completed_at'])
        
        cursor.close()
        conn.close()
        return {"data": backups}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

