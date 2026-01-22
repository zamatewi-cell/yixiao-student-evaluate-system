# -*- coding: utf-8 -*-
"""
教师路由模块 - 数据录入、查看班级等
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query, File, UploadFile
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
import json
import io

from ..auth.dependencies import get_db_connection, require_teacher, CurrentUser

router = APIRouter(prefix="/api/teacher", tags=["教师"])


# ============== 辅助函数 ==============

def check_teacher_edit_permission(conn, user_id: int) -> dict:
    """
    检查教师是否有编辑权限
    返回: {'can_edit': bool, 'teacher_id': int, 'teacher_name': str}
    """
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT t.id, t.name, t.can_edit, u.is_active
        FROM teachers t
        JOIN users u ON t.user_id = u.id
        WHERE t.user_id = %s
    """, (user_id,))
    teacher = cursor.fetchone()
    cursor.close()
    
    if not teacher:
        return {'can_edit': False, 'teacher_id': None, 'teacher_name': None}
    
    # 检查账号是否激活且有编辑权限
    can_edit = teacher.get('is_active', False) and teacher.get('can_edit', False)
    return {
        'can_edit': can_edit,
        'teacher_id': teacher['id'],
        'teacher_name': teacher['name']
    }


# ============== 数据模型 ==============

class EvaluationInput(BaseModel):
    student_id: int
    indicator_id: int
    semester_id: int
    value: str
    remark: Optional[str] = None


class BatchEvaluationInput(BaseModel):
    semester_id: int
    indicator_id: int
    data: List[dict]  # [{student_id, value, remark}, ...]


# ============== 获取当前教师信息 ==============

@router.get("/profile")
async def get_teacher_profile(current_user: CurrentUser = Depends(require_teacher)):
    """获取当前教师信息"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT t.*, u.username, u.email, u.phone
            FROM teachers t
            JOIN users u ON t.user_id = u.id
            WHERE t.user_id = %s
        """, (current_user.id,))
        teacher = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not teacher:
            raise HTTPException(status_code=404, detail="教师信息不存在")
        
        return teacher
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 获取我的班级 ==============

@router.get("/my-classes")
async def get_my_classes(current_user: CurrentUser = Depends(require_teacher)):
    """获取当前教师负责的班级"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取教师ID
        cursor.execute("SELECT id FROM teachers WHERE user_id = %s", (current_user.id,))
        teacher = cursor.fetchone()
        
        if not teacher:
            cursor.close()
            conn.close()
            return {"data": []}
        
        # 获取教师可以管理的班级
        # 1. 首先获取班主任管理的班级
        cursor.execute("""
            SELECT c.*, g.name as grade_name,
                   (SELECT COUNT(*) FROM students s WHERE s.class_id = c.id AND s.status = 'active') as student_count,
                   CASE WHEN c.head_teacher_id = %s THEN 1 ELSE 0 END as is_head_teacher
            FROM classes c
            LEFT JOIN grades g ON c.grade_id = g.id
            ORDER BY g.sort_order, c.name
        """, (teacher['id'],))
        
        classes = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return {"data": classes}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 获取班级学生 ==============

@router.get("/classes/{class_id}/students")
async def get_class_students(
    class_id: int,
    current_user: CurrentUser = Depends(require_teacher)
):
    """获取班级学生列表"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, student_no, name, gender
            FROM students
            WHERE class_id = %s AND status = 'active'
            ORDER BY student_no
        """, (class_id,))
        students = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"data": students}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 获取当前学期 ==============

@router.get("/current-semester")
async def get_current_semester(current_user: CurrentUser = Depends(require_teacher)):
    """获取当前学期"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM semesters WHERE is_current = TRUE LIMIT 1")
        semester = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not semester:
            raise HTTPException(status_code=404, detail="未设置当前学期")
        
        return {"data": semester}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 获取所有学期列表（教师可访问） ==============

@router.get("/semesters")
async def get_teacher_semesters(current_user: CurrentUser = Depends(require_teacher)):
    """获取所有学期列表（教师使用）"""
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


# ============== 获取评价指标列表（教师可访问） ==============

@router.get("/indicators")
async def get_teacher_indicators(current_user: CurrentUser = Depends(require_teacher)):
    """获取评价指标列表（教师使用）"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT i.*, c.name as category_name
            FROM indicators i
            LEFT JOIN indicator_categories c ON i.category_id = c.id
            WHERE i.is_active = TRUE
            ORDER BY c.sort_order, i.sort_order
        """)
        indicators = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # 格式化数据
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
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 获取教师编辑权限状态 ==============

@router.get("/edit-permission")
async def get_teacher_edit_permission(current_user: CurrentUser = Depends(require_teacher)):
    """获取当前教师的编辑权限状态"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        permission = check_teacher_edit_permission(conn, current_user.id)
        conn.close()
        
        return {
            "can_edit": permission['can_edit'],
            "teacher_id": permission['teacher_id'],
            "teacher_name": permission['teacher_name'],
            "message": "您已获得数据编辑权限" if permission['can_edit'] else "您尚未获得数据编辑权限，请联系管理员授权"
        }
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 数据录入 ==============

@router.post("/evaluations")
async def create_evaluation(
    evaluation: EvaluationInput,
    current_user: CurrentUser = Depends(require_teacher)
):
    """录入单条评价数据"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        # 检查编辑权限（管理员跳过检查）
        if current_user.role != 'admin':
            permission = check_teacher_edit_permission(conn, current_user.id)
            if not permission['can_edit']:
                conn.close()
                raise HTTPException(status_code=403, detail="您尚未获得数据编辑权限，请联系管理员授权")
        
        cursor = conn.cursor()
        
        # 计算分数（用于统计）
        score = None
        if evaluation.value.replace('.', '').isdigit():
            score = float(evaluation.value)
        elif evaluation.value in ['优秀', '一级']:
            score = 95
        elif evaluation.value in ['良好', '二级']:
            score = 85
        elif evaluation.value in ['及格', '三级']:
            score = 70
        elif evaluation.value in ['不及格', '四级', '五级']:
            score = 50
        
        # 插入或更新
        cursor.execute("""
            INSERT INTO evaluations (student_id, indicator_id, semester_id, value, score, remark, recorded_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                value = VALUES(value), 
                score = VALUES(score),
                remark = VALUES(remark),
                recorded_by = VALUES(recorded_by),
                updated_at = NOW()
        """, (evaluation.student_id, evaluation.indicator_id, evaluation.semester_id,
              evaluation.value, score, evaluation.remark, current_user.id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "录入成功"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluations/batch")
async def batch_create_evaluations(
    batch: BatchEvaluationInput,
    current_user: CurrentUser = Depends(require_teacher)
):
    """批量录入评价数据"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        # 检查编辑权限（管理员跳过检查）
        if current_user.role != 'admin':
            permission = check_teacher_edit_permission(conn, current_user.id)
            if not permission['can_edit']:
                conn.close()
                raise HTTPException(status_code=403, detail="您尚未获得数据编辑权限，请联系管理员授权")
        
        cursor = conn.cursor()
        success_count = 0
        
        for item in batch.data:
            student_id = item.get('student_id')
            value = item.get('value')
            remark = item.get('remark', '')
            
            if not student_id or value is None:
                continue
            
            # 计算分数
            score = None
            if str(value).replace('.', '').isdigit():
                score = float(value)
            elif value in ['优秀', '一级']:
                score = 95
            elif value in ['良好', '二级']:
                score = 85
            elif value in ['及格', '三级']:
                score = 70
            elif value in ['不及格', '四级', '五级']:
                score = 50
            
            cursor.execute("""
                INSERT INTO evaluations (student_id, indicator_id, semester_id, value, score, remark, recorded_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    value = VALUES(value), 
                    score = VALUES(score),
                    remark = VALUES(remark),
                    recorded_by = VALUES(recorded_by),
                    updated_at = NOW()
            """, (student_id, batch.indicator_id, batch.semester_id, value, score, remark, current_user.id))
            success_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": f"成功录入 {success_count} 条数据"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 获取班级评价数据 ==============

@router.get("/classes/{class_id}/evaluations")
async def get_class_evaluations(
    class_id: int,
    semester_id: int,
    indicator_id: Optional[int] = None,
    current_user: CurrentUser = Depends(require_teacher)
):
    """获取班级评价数据"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取学生列表及其评价
        if indicator_id:
            cursor.execute("""
                SELECT s.id as student_id, s.student_no, s.name, s.gender,
                       e.value, e.score, e.remark, e.recorded_at
                FROM students s
                LEFT JOIN evaluations e ON s.id = e.student_id 
                    AND e.semester_id = %s AND e.indicator_id = %s
                WHERE s.class_id = %s AND s.status = 'active'
                ORDER BY s.student_no
            """, (semester_id, indicator_id, class_id))
        else:
            # 获取所有指标的评价
            cursor.execute("""
                SELECT s.id as student_id, s.student_no, s.name, s.gender,
                       i.id as indicator_id, i.name as indicator_name,
                       e.value, e.score
                FROM students s
                CROSS JOIN indicators i
                LEFT JOIN evaluations e ON s.id = e.student_id 
                    AND e.indicator_id = i.id AND e.semester_id = %s
                WHERE s.class_id = %s AND s.status = 'active' AND i.is_active = TRUE
                ORDER BY s.student_no, i.category_id, i.sort_order
            """, (semester_id, class_id))
        
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return {"data": data}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 书法批改记录 ==============

@router.get("/calligraphy-records")
async def get_calligraphy_records(
    class_id: Optional[int] = None,
    semester_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(require_teacher)
):
    """获取书法批改记录"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        where_clauses = ["g.status = 'completed'"]
        params = []
        
        if class_id:
            where_clauses.append("s.class_id = %s")
            params.append(class_id)
        
        if semester_id:
            where_clauses.append("g.semester_id = %s")
            params.append(semester_id)
        
        where_sql = " AND ".join(where_clauses)
        
        cursor.execute(f"""
            SELECT COUNT(*) as total 
            FROM grading_records g
            LEFT JOIN students s ON g.student_id = s.id
            WHERE {where_sql}
        """, params)
        total = cursor.fetchone()['total']
        
        offset = (page - 1) * page_size
        cursor.execute(f"""
            SELECT g.*, s.student_no, s.name as student_name, c.name as class_name
            FROM grading_records g
            LEFT JOIN students s ON g.student_id = s.id
            LEFT JOIN classes c ON s.class_id = c.id
            WHERE {where_sql}
            ORDER BY g.upload_time DESC
            LIMIT %s OFFSET %s
        """, params + [page_size, offset])
        
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return {"total": total, "page": page, "page_size": page_size, "data": records}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 书法批改 - 学生分配 ==============

class AssignStudentRequest(BaseModel):
    record_id: int
    student_id: int


class BatchAssignRequest(BaseModel):
    assignments: List[dict]  # [{record_id: int, student_id: int}, ...]


@router.get("/calligraphy-records/unassigned")
async def get_unassigned_calligraphy_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(require_teacher)
):
    """获取未分配学生的书法批改记录"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取未分配学生的记录总数
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM grading_records 
            WHERE student_id IS NULL AND status = 'completed'
        """)
        total = cursor.fetchone()['total']
        
        # 获取未分配学生的记录
        offset = (page - 1) * page_size
        cursor.execute("""
            SELECT id, filename, original_filename, file_path, upload_time,
                   overall_score, grade, char_count, ai_comment, strengths, suggestions, barcode
            FROM grading_records
            WHERE student_id IS NULL AND status = 'completed'
            ORDER BY upload_time DESC
            LIMIT %s OFFSET %s
        """, (page_size, offset))
        
        records = cursor.fetchall()
        
        # 格式化时间
        for record in records:
            if record.get('upload_time'):
                record['upload_time'] = record['upload_time'].strftime('%Y-%m-%d %H:%M:%S')
            record['file_url'] = f"/uploads/{record['filename']}"
            # 转换 Decimal 类型
            if record.get('overall_score'):
                record['overall_score'] = float(record['overall_score'])
        
        cursor.close()
        conn.close()
        
        return {"total": total, "page": page, "page_size": page_size, "data": records}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calligraphy-records/assign")
async def assign_student_to_record(
    request: AssignStudentRequest,
    current_user: CurrentUser = Depends(require_teacher)
):
    """手动将书法作品分配给学生"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 检查记录是否存在
        cursor.execute("SELECT id, student_id FROM grading_records WHERE id = %s", (request.record_id,))
        record = cursor.fetchone()
        if not record:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="批改记录不存在")
        
        # 检查学生是否存在
        cursor.execute("SELECT id, name, student_no FROM students WHERE id = %s AND status = 'active'", (request.student_id,))
        student = cursor.fetchone()
        if not student:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="学生不存在")
        
        # 检查该学生是否已经有分配的作品
        cursor.execute("""
            SELECT id FROM grading_records 
            WHERE student_id = %s AND status = 'completed' AND id != %s
        """, (request.student_id, request.record_id))
        existing = cursor.fetchone()
        if existing:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail=f"学生 {student['name']} 已有分配的作品，每个学生只能分配一个作品")
        
        # 更新记录，分配学生
        cursor.execute("""
            UPDATE grading_records 
            SET student_id = %s, updated_at = NOW()
            WHERE id = %s
        """, (request.student_id, request.record_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": f"成功将作品分配给学生 {student['name']}（学号：{student['student_no']}）"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calligraphy-records/batch-assign")
async def batch_assign_students(
    request: BatchAssignRequest,
    current_user: CurrentUser = Depends(require_teacher)
):
    """批量分配书法作品给学生"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        success_count = 0
        errors = []
        
        for assignment in request.assignments:
            record_id = assignment.get('record_id')
            student_id = assignment.get('student_id')
            
            if not record_id or not student_id:
                continue
            
            # 检查该学生是否已经有其他分配的作品
            cursor.execute("""
                SELECT id FROM grading_records 
                WHERE student_id = %s AND status = 'completed' AND id != %s
            """, (student_id, record_id))
            if cursor.fetchone():
                errors.append(f"记录 {record_id}: 学生已有分配的作品")
                continue
            
            # 更新记录
            cursor.execute("""
                UPDATE grading_records 
                SET student_id = %s, updated_at = NOW()
                WHERE id = %s
            """, (student_id, record_id))
            success_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "message": f"成功分配 {success_count} 个作品",
            "success_count": success_count,
            "errors": errors
        }
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/calligraphy-records/{record_id}/unassign")
async def unassign_student_from_record(
    record_id: int,
    current_user: CurrentUser = Depends(require_teacher)
):
    """取消书法作品与学生的分配关系"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE grading_records 
            SET student_id = NULL, updated_at = NOW()
            WHERE id = %s
        """, (record_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "已取消分配"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 书法评语同步到期末评语 ==============

class SyncCalligraphyCommentRequest(BaseModel):
    record_id: int
    semester_id: int
    append_to_existing: bool = True  # 是否追加到现有评语


@router.post("/calligraphy-records/sync-comment")
async def sync_calligraphy_comment_to_evaluation(
    request: SyncCalligraphyCommentRequest,
    current_user: CurrentUser = Depends(require_teacher)
):
    """将书法批改评语同步到期末评语管理"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取书法批改记录
        cursor.execute("""
            SELECT id, student_id, ai_comment, strengths, suggestions, overall_score, grade
            FROM grading_records 
            WHERE id = %s AND status = 'completed'
        """, (request.record_id,))
        record = cursor.fetchone()
        
        if not record:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="批改记录不存在或未完成")
        
        if not record['student_id']:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail="该作品尚未分配给学生，请先分配学生")
        
        # 组合书法评语
        calligraphy_comment = f"【书法评价】评分：{record.get('overall_score', 0):.1f}分（{record.get('grade', '未评定')}）\n"
        if record.get('ai_comment'):
            calligraphy_comment += f"评语：{record['ai_comment']}\n"
        if record.get('strengths'):
            calligraphy_comment += f"优点：{record['strengths']}\n"
        if record.get('suggestions'):
            calligraphy_comment += f"建议：{record['suggestions']}"
        
        # 检查是否已有期末评语
        cursor.execute("""
            SELECT id, ai_comment, teacher_comment 
            FROM semester_comments 
            WHERE student_id = %s AND semester_id = %s
        """, (record['student_id'], request.semester_id))
        existing_comment = cursor.fetchone()
        
        if existing_comment and request.append_to_existing:
            # 追加到现有评语
            new_ai_comment = (existing_comment.get('ai_comment') or '') + "\n\n" + calligraphy_comment
            cursor.execute("""
                UPDATE semester_comments 
                SET ai_comment = %s, updated_at = NOW()
                WHERE id = %s
            """, (new_ai_comment.strip(), existing_comment['id']))
        else:
            # 插入或替换
            cursor.execute("""
                INSERT INTO semester_comments 
                (student_id, semester_id, ai_comment, is_published, created_at, updated_at)
                VALUES (%s, %s, %s, FALSE, NOW(), NOW())
                ON DUPLICATE KEY UPDATE
                    ai_comment = VALUES(ai_comment),
                    updated_at = NOW()
            """, (record['student_id'], request.semester_id, calligraphy_comment))
        
        # 标记已同步
        cursor.execute("""
            UPDATE grading_records 
            SET synced_to_evaluation = TRUE, semester_id = %s
            WHERE id = %s
        """, (request.semester_id, request.record_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "书法评语已同步到期末评语管理"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calligraphy-records/batch-sync-comments")
async def batch_sync_calligraphy_comments(
    class_id: int,
    semester_id: int,
    append_to_existing: bool = True,
    current_user: CurrentUser = Depends(require_teacher)
):
    """批量将班级学生的书法评语同步到期末评语"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取班级所有学生的已分配书法批改记录
        cursor.execute("""
            SELECT g.id, g.student_id, g.ai_comment, g.strengths, g.suggestions, 
                   g.overall_score, g.grade, s.name as student_name
            FROM grading_records g
            JOIN students s ON g.student_id = s.id
            WHERE s.class_id = %s AND g.status = 'completed' AND g.student_id IS NOT NULL
        """, (class_id,))
        
        records = cursor.fetchall()
        
        if not records:
            cursor.close()
            conn.close()
            return {"message": "没有需要同步的书法评语", "success_count": 0}
        
        success_count = 0
        
        for record in records:
            # 组合书法评语
            calligraphy_comment = f"【书法评价】评分：{record.get('overall_score', 0):.1f}分（{record.get('grade', '未评定')}）\n"
            if record.get('ai_comment'):
                calligraphy_comment += f"评语：{record['ai_comment']}\n"
            if record.get('strengths'):
                calligraphy_comment += f"优点：{record['strengths']}\n"
            if record.get('suggestions'):
                calligraphy_comment += f"建议：{record['suggestions']}"
            
            # 检查现有评语
            cursor.execute("""
                SELECT id, ai_comment FROM semester_comments 
                WHERE student_id = %s AND semester_id = %s
            """, (record['student_id'], semester_id))
            existing = cursor.fetchone()
            
            if existing and append_to_existing:
                # 检查是否已包含书法评价
                if existing.get('ai_comment') and '【书法评价】' in existing['ai_comment']:
                    continue
                new_comment = (existing.get('ai_comment') or '') + "\n\n" + calligraphy_comment
                cursor.execute("""
                    UPDATE semester_comments SET ai_comment = %s, updated_at = NOW()
                    WHERE id = %s
                """, (new_comment.strip(), existing['id']))
            else:
                cursor.execute("""
                    INSERT INTO semester_comments 
                    (student_id, semester_id, ai_comment, is_published, created_at, updated_at)
                    VALUES (%s, %s, %s, FALSE, NOW(), NOW())
                    ON DUPLICATE KEY UPDATE
                        ai_comment = VALUES(ai_comment),
                        updated_at = NOW()
                """, (record['student_id'], semester_id, calligraphy_comment))
            
            # 标记已同步
            cursor.execute("""
                UPDATE grading_records 
                SET synced_to_evaluation = TRUE, semester_id = %s
                WHERE id = %s
            """, (semester_id, record['id']))
            
            success_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": f"成功同步 {success_count} 条书法评语", "success_count": success_count}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


class CommentBatchRequest(BaseModel):
    class_id: int
    semester_id: int


class CommentGenerateRequest(BaseModel):
    """生成评语请求模型"""
    student_id: int
    semester_id: int
    special_achievements: Optional[str] = None  # 特殊成就
    areas_for_improvement: Optional[str] = None  # 需改进领域


class CommentSaveRequest(BaseModel):
    student_id: int
    semester_id: int
    ai_comment: str
    teacher_comment: Optional[str] = None
    is_published: bool = False


@router.post("/comments/generate")
async def generate_student_comment(
    request: CommentGenerateRequest,
    current_user: CurrentUser = Depends(require_teacher)
):
    """生成单个学生的期末评语"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取学生信息
        cursor.execute("""
            SELECT s.*, c.name as class_name, g.name as grade_name
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            LEFT JOIN grades g ON c.grade_id = g.id
            WHERE s.id = %s
        """, (request.student_id,))
        student = cursor.fetchone()
        
        if not student:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="学生不存在")
        
        # 获取学生的评价数据
        cursor.execute("""
            SELECT ic.name as category_name, i.name as indicator_name,
                   i.type, i.max_score, e.value
            FROM evaluations e
            JOIN indicators i ON e.indicator_id = i.id
            JOIN indicator_categories ic ON i.category_id = ic.id
            WHERE e.student_id = %s AND e.semester_id = %s
            ORDER BY ic.sort_order, i.sort_order
        """, (request.student_id, request.semester_id))
        evaluations = cursor.fetchall()
        
        # 获取学期名称
        cursor.execute("SELECT name FROM semesters WHERE id = %s", (request.semester_id,))
        semester = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not evaluations:
            raise HTTPException(status_code=400, detail="该学生暂无评价数据")
        
        # 导入评语生成器
        try:
            from src.api.comment_generator import CommentGenerator
            generator = CommentGenerator()
            
            # 生成评语
            result = generator.generate_comment(
                student_name=student['name'],
                gender=student['gender'],
                evaluations=evaluations,
                semester_name=semester['name'] if semester else '',
                class_name=student.get('class_name', ''),
                grade_name=student.get('grade_name', ''),
                special_achievements=request.special_achievements,
                areas_for_improvement=request.areas_for_improvement
            )
            
            return result
        except ImportError:
            raise HTTPException(status_code=500, detail="AI评语生成模块未安装")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"生成评语失败: {str(e)}")
    
    except Error as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comments/batch-generate")
async def batch_generate_comments(
    request: CommentBatchRequest,
    current_user: CurrentUser = Depends(require_teacher)
):
    """批量生成班级所有学生的评语"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取班级所有学生
        cursor.execute("""
            SELECT s.*, c.name as class_name, g.name as grade_name
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            LEFT JOIN grades g ON c.grade_id = g.id
            WHERE s.class_id = %s AND s.status = 'active'
            ORDER BY s.student_no
        """, (request.class_id,))
        students = cursor.fetchall()
        
        # 获取学期名称
        cursor.execute("SELECT name FROM semesters WHERE id = %s", (request.semester_id,))
        semester = cursor.fetchone()
        
        if not students:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="班级无学生")
        
        # 导入评语生成器
        try:
            from src.api.comment_generator import CommentGenerator
            generator = CommentGenerator()
            
            results = []
            success_count = 0
            
            for student in students:
                # 获取学生评价数据
                cursor.execute("""
                    SELECT ic.name as category_name, i.name as indicator_name,
                           i.type, i.max_score, e.value
                    FROM evaluations e
                    JOIN indicators i ON e.indicator_id = i.id
                    JOIN indicator_categories ic ON i.category_id = ic.id
                    WHERE e.student_id = %s AND e.semester_id = %s
                    ORDER BY ic.sort_order, i.sort_order
                """, (student['id'], request.semester_id))
                evaluations = cursor.fetchall()
                
                if not evaluations:
                    results.append({
                        'student_id': student['id'],
                        'student_name': student['name'],
                        'success': False,
                        'error': '无评价数据'
                    })
                    continue
                
                # 生成评语
                result = generator.generate_comment(
                    student_name=student['name'],
                    gender=student['gender'],
                    evaluations=evaluations,
                    semester_name=semester['name'] if semester else '',
                    class_name=student.get('class_name', ''),
                    grade_name=student.get('grade_name', '')
                )
                
                result['student_id'] = student['id']
                result['student_name'] = student['name']
                results.append(result)
                
                if result.get('success'):
                    success_count += 1
            
            cursor.close()
            conn.close()
            
            return {
                'total': len(students),
                'success_count': success_count,
                'results': results
            }
            
        except ImportError:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=500, detail="AI评语生成模块未安装")
        except Exception as e:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=500, detail=f"批量生成失败: {str(e)}")
    
    except Error as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comments/save")
async def save_student_comment(
    request: CommentSaveRequest,
    current_user: CurrentUser = Depends(require_teacher)
):
    """保存学生评语"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        # 检查编辑权限（管理员跳过检查）
        if current_user.role != 'admin':
            permission = check_teacher_edit_permission(conn, current_user.id)
            if not permission['can_edit']:
                conn.close()
                raise HTTPException(status_code=403, detail="您尚未获得数据编辑权限，请联系管理员授权")
        
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO semester_comments 
            (student_id, semester_id, ai_comment, teacher_comment, is_published, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            ON DUPLICATE KEY UPDATE
                ai_comment = VALUES(ai_comment),
                teacher_comment = VALUES(teacher_comment),
                is_published = VALUES(is_published),
                updated_at = NOW()
        """, (request.student_id, request.semester_id, request.ai_comment, 
              request.teacher_comment, request.is_published))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "评语保存成功"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/classes/{class_id}/comments")
async def get_class_comments(
    class_id: int,
    semester_id: int,
    current_user: CurrentUser = Depends(require_teacher)
):
    """获取班级所有学生的评语"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT s.id as student_id, s.student_no, s.name as student_name,
                   sc.ai_comment, sc.teacher_comment, sc.is_published, sc.updated_at
            FROM students s
            LEFT JOIN semester_comments sc ON s.id = sc.student_id AND sc.semester_id = %s
            WHERE s.class_id = %s AND s.status = 'active'
            ORDER BY s.student_no
        """, (semester_id, class_id))
        
        comments = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return {"data": comments}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
