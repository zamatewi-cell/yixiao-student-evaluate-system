# -*- coding: utf-8 -*-
"""
教师角色权限管理模块
支持班主任和科任教师的细化权限
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error

from ..auth.dependencies import get_db_connection, require_admin, require_teacher, CurrentUser

router = APIRouter(prefix="/api/teacher-role", tags=["教师角色"])


class TeacherRoleUpdate(BaseModel):
    """教师角色更新"""
    is_head_teacher: bool = False
    teacher_type: str = "subject_teacher"  # head_teacher, subject_teacher, both


class TeacherSubjectAssign(BaseModel):
    """教师任课分配"""
    class_id: int
    subject_name: str
    semester_id: int


# ============== 教师角色管理 ==============

@router.get("/my-role")
async def get_my_role(current_user: CurrentUser = Depends(require_teacher)):
    """获取当前教师的角色信息"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取教师信息
        cursor.execute("""
            SELECT t.id, t.name, t.is_head_teacher, t.teacher_type, t.subjects,
                   c.id as head_class_id, c.name as head_class_name
            FROM teachers t
            LEFT JOIN classes c ON c.head_teacher_id = t.id
            WHERE t.user_id = %s
        """, (current_user.id,))
        teacher = cursor.fetchone()
        
        if not teacher:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="教师信息不存在")
        
        # 获取任课班级
        cursor.execute("""
            SELECT ts.id, ts.class_id, c.name as class_name, ts.subject_name,
                   g.name as grade_name, sem.name as semester_name
            FROM teacher_subjects ts
            JOIN classes c ON ts.class_id = c.id
            JOIN grades g ON c.grade_id = g.id
            JOIN semesters sem ON ts.semester_id = sem.id
            WHERE ts.teacher_id = %s AND ts.is_active = TRUE
            ORDER BY g.sort_order, c.name, ts.subject_name
        """, (teacher['id'],))
        teaching_classes = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "data": {
                "teacher_id": teacher['id'],
                "name": teacher['name'],
                "is_head_teacher": teacher['is_head_teacher'] or False,
                "teacher_type": teacher['teacher_type'] or 'subject_teacher',
                "subjects": teacher['subjects'],
                "head_class": {
                    "id": teacher['head_class_id'],
                    "name": teacher['head_class_name']
                } if teacher['head_class_id'] else None,
                "teaching_classes": teaching_classes,
                "permissions": get_teacher_permissions(teacher)
            }
        }
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


def get_teacher_permissions(teacher: dict) -> dict:
    """根据教师角色获取权限"""
    permissions = {
        "can_view_all_classes": False,
        "can_manage_attendance": False,
        "can_manage_students": False,
        "can_input_scores": True,
        "can_generate_comments": False,
        "can_view_class_stats": False,
        "can_transfer_students": False
    }
    
    teacher_type = teacher.get('teacher_type', 'subject_teacher')
    is_head = teacher.get('is_head_teacher', False)
    
    if is_head or teacher_type in ['head_teacher', 'both']:
        permissions.update({
            "can_view_all_classes": False,  # 只能看自己班
            "can_manage_attendance": True,
            "can_manage_students": True,
            "can_generate_comments": True,
            "can_view_class_stats": True,
            "can_transfer_students": False  # 转班需要管理员
        })
    
    return permissions


@router.put("/update/{teacher_id}")
async def update_teacher_role(
    teacher_id: int,
    role_data: TeacherRoleUpdate,
    current_user: CurrentUser = Depends(require_admin)
):
    """更新教师角色（管理员操作）"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE teachers 
            SET is_head_teacher = %s, teacher_type = %s
            WHERE id = %s
        """, (role_data.is_head_teacher, role_data.teacher_type, teacher_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "教师角色更新成功"}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 任课分配 ==============

@router.post("/assign-subject")
async def assign_subject(
    assignment: TeacherSubjectAssign,
    teacher_id: int,
    current_user: CurrentUser = Depends(require_admin)
):
    """分配教师任课（管理员操作）"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO teacher_subjects (teacher_id, class_id, subject_name, semester_id, is_active)
            VALUES (%s, %s, %s, %s, TRUE)
            ON DUPLICATE KEY UPDATE is_active = TRUE
        """, (teacher_id, assignment.class_id, assignment.subject_name, assignment.semester_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "任课分配成功"}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/remove-subject/{assignment_id}")
async def remove_subject_assignment(
    assignment_id: int,
    current_user: CurrentUser = Depends(require_admin)
):
    """移除任课分配"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE teacher_subjects SET is_active = FALSE WHERE id = %s", (assignment_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "移除成功"}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/class-teachers/{class_id}")
async def get_class_teachers(
    class_id: int,
    current_user: CurrentUser = Depends(require_teacher)
):
    """获取班级的所有任课教师"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 班主任
        cursor.execute("""
            SELECT t.id, t.name, '班主任' as role
            FROM classes c
            JOIN teachers t ON c.head_teacher_id = t.id
            WHERE c.id = %s
        """, (class_id,))
        head_teacher = cursor.fetchone()
        
        # 任课教师
        cursor.execute("""
            SELECT t.id, t.name, ts.subject_name as role
            FROM teacher_subjects ts
            JOIN teachers t ON ts.teacher_id = t.id
            WHERE ts.class_id = %s AND ts.is_active = TRUE
        """, (class_id,))
        subject_teachers = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        teachers = []
        if head_teacher:
            teachers.append(head_teacher)
        teachers.extend(subject_teachers)
        
        return {"data": teachers}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))
