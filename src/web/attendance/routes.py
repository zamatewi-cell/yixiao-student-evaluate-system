# -*- coding: utf-8 -*-
"""
考勤管理路由模块
"""
from datetime import datetime, date, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error

from ..auth.dependencies import get_db_connection, require_teacher, CurrentUser

router = APIRouter(prefix="/api/attendance", tags=["考勤管理"])


# ============== 数据模型 ==============

class AttendanceRecord(BaseModel):
    """考勤记录"""
    student_id: int
    date: str  # YYYY-MM-DD
    status: str  # present/absent/late/leave_early/sick_leave/personal_leave
    leave_type: Optional[str] = None  # sick/personal/other
    reason: Optional[str] = None


class BatchAttendanceInput(BaseModel):
    """批量考勤录入"""
    date: str
    records: List[dict]  # [{"student_id": 1, "status": "present"}, ...]


# ============== 考勤录入 ==============

@router.post("/record")
async def record_attendance(
    data: AttendanceRecord,
    current_user: CurrentUser = Depends(require_teacher)
):
    """记录单个学生考勤"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO attendance (student_id, date, status, leave_type, reason, recorded_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
                status = VALUES(status),
                leave_type = VALUES(leave_type),
                reason = VALUES(reason),
                recorded_by = VALUES(recorded_by),
                updated_at = NOW()
        """, (data.student_id, data.date, data.status, data.leave_type, data.reason, current_user.id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "考勤记录成功"}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_record_attendance(
    data: BatchAttendanceInput,
    current_user: CurrentUser = Depends(require_teacher)
):
    """批量记录考勤"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        success_count = 0
        
        for record in data.records:
            student_id = record.get('student_id')
            status = record.get('status', 'present')
            leave_type = record.get('leave_type')
            reason = record.get('reason')
            
            if not student_id:
                continue
            
            cursor.execute("""
                INSERT INTO attendance (student_id, date, status, leave_type, reason, recorded_by, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    status = VALUES(status),
                    leave_type = VALUES(leave_type),
                    reason = VALUES(reason),
                    recorded_by = VALUES(recorded_by),
                    updated_at = NOW()
            """, (student_id, data.date, status, leave_type, reason, current_user.id))
            success_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": f"成功记录 {success_count} 条考勤"}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 考勤查询 ==============

@router.get("/class/{class_id}")
async def get_class_attendance(
    class_id: int,
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: CurrentUser = Depends(require_teacher)
):
    """获取班级考勤数据"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 如果指定了单日期
        if date:
            cursor.execute("""
                SELECT s.id as student_id, s.student_no, s.name as student_name,
                       a.status, a.leave_type, a.reason
                FROM students s
                LEFT JOIN attendance a ON s.id = a.student_id AND a.date = %s
                WHERE s.class_id = %s AND s.status = 'active'
                ORDER BY s.student_no
            """, (date, class_id))
            records = cursor.fetchall()
            
            cursor.close()
            conn.close()
            return {"data": records, "date": date}
        
        # 日期范围查询
        if not start_date:
            start_date = str(datetime.now().date() - timedelta(days=7))
        if not end_date:
            end_date = str(datetime.now().date())
        
        cursor.execute("""
            SELECT s.id as student_id, s.student_no, s.name as student_name,
                   a.date, a.status, a.leave_type, a.reason
            FROM students s
            LEFT JOIN attendance a ON s.id = a.student_id 
                AND a.date BETWEEN %s AND %s
            WHERE s.class_id = %s AND s.status = 'active'
            ORDER BY s.student_no, a.date
        """, (start_date, end_date, class_id))
        records = cursor.fetchall()
        
        # 格式化日期
        for record in records:
            if record.get('date'):
                record['date'] = str(record['date'])
        
        cursor.close()
        conn.close()
        return {"data": records, "start_date": start_date, "end_date": end_date}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/student/{student_id}")
async def get_student_attendance(
    student_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: CurrentUser = Depends(require_teacher)
):
    """获取学生考勤记录"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        sql = """
            SELECT a.*, s.name as student_name, s.student_no
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE a.student_id = %s
        """
        params = [student_id]
        
        if start_date:
            sql += " AND a.date >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND a.date <= %s"
            params.append(end_date)
        
        sql += " ORDER BY a.date DESC"
        
        cursor.execute(sql, tuple(params))
        records = cursor.fetchall()
        
        # 格式化日期
        for record in records:
            if record.get('date'):
                record['date'] = str(record['date'])
            if record.get('created_at'):
                record['created_at'] = str(record['created_at'])
        
        cursor.close()
        conn.close()
        return {"data": records}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 考勤统计 ==============

@router.get("/statistics/class/{class_id}")
async def get_class_attendance_statistics(
    class_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: CurrentUser = Depends(require_teacher)
):
    """获取班级考勤统计"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 默认本月
        if not start_date:
            today = datetime.now().date()
            start_date = str(today.replace(day=1))
        if not end_date:
            end_date = str(datetime.now().date())
        
        # 获取班级学生总数
        cursor.execute("""
            SELECT COUNT(*) as total FROM students 
            WHERE class_id = %s AND status = 'active'
        """, (class_id,))
        total_students = cursor.fetchone()['total']
        
        # 获取各状态统计
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as count
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE s.class_id = %s AND a.date BETWEEN %s AND %s
            GROUP BY status
        """, (class_id, start_date, end_date))
        status_stats = cursor.fetchall()
        
        # 获取请假类型统计
        cursor.execute("""
            SELECT 
                leave_type,
                COUNT(*) as count
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE s.class_id = %s AND a.date BETWEEN %s AND %s
                AND a.status IN ('sick_leave', 'personal_leave')
            GROUP BY leave_type
        """, (class_id, start_date, end_date))
        leave_stats = cursor.fetchall()
        
        # 获取每日统计
        cursor.execute("""
            SELECT 
                a.date,
                SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present_count,
                SUM(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END) as absent_count,
                SUM(CASE WHEN a.status = 'late' THEN 1 ELSE 0 END) as late_count,
                SUM(CASE WHEN a.status IN ('sick_leave', 'personal_leave') THEN 1 ELSE 0 END) as leave_count
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE s.class_id = %s AND a.date BETWEEN %s AND %s
            GROUP BY a.date
            ORDER BY a.date
        """, (class_id, start_date, end_date))
        daily_stats = cursor.fetchall()
        
        # 格式化日期
        for item in daily_stats:
            if item.get('date'):
                item['date'] = str(item['date'])
        
        cursor.close()
        conn.close()
        
        return {
            "data": {
                "total_students": total_students,
                "status_stats": status_stats,
                "leave_stats": leave_stats,
                "daily_stats": daily_stats
            },
            "start_date": start_date,
            "end_date": end_date
        }
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/grade/{grade_id}")
async def get_grade_attendance_statistics(
    grade_id: int,
    date: Optional[str] = None,
    current_user: CurrentUser = Depends(require_teacher)
):
    """获取年级考勤统计（用于大屏展示）"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if not date:
            date = str(datetime.now().date())
        
        # 获取各班统计
        cursor.execute("""
            SELECT 
                c.id as class_id,
                c.name as class_name,
                (SELECT COUNT(*) FROM students WHERE class_id = c.id AND status = 'active') as total_students,
                SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present_count,
                SUM(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END) as absent_count,
                SUM(CASE WHEN a.status = 'late' THEN 1 ELSE 0 END) as late_count,
                SUM(CASE WHEN a.status = 'sick_leave' THEN 1 ELSE 0 END) as sick_leave_count,
                SUM(CASE WHEN a.status = 'personal_leave' THEN 1 ELSE 0 END) as personal_leave_count
            FROM classes c
            LEFT JOIN students s ON c.id = s.class_id AND s.status = 'active'
            LEFT JOIN attendance a ON s.id = a.student_id AND a.date = %s
            WHERE c.grade_id = %s
            GROUP BY c.id
            ORDER BY c.name
        """, (date, grade_id))
        class_stats = cursor.fetchall()
        
        # 计算出勤率
        for item in class_stats:
            total = item['total_students'] or 0
            present = item['present_count'] or 0
            if total > 0:
                item['attendance_rate'] = round(present / total * 100, 1)
            else:
                item['attendance_rate'] = 0
        
        cursor.close()
        conn.close()
        
        return {"data": class_stats, "date": date}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_attendance_dashboard(
    date: Optional[str] = None,
    current_user: CurrentUser = Depends(require_teacher)
):
    """获取考勤大屏数据"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if not date:
            date = str(datetime.now().date())
        
        # 全校统计
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM students WHERE status = 'active') as total_students,
                SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present_count,
                SUM(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END) as absent_count,
                SUM(CASE WHEN a.status = 'late' THEN 1 ELSE 0 END) as late_count,
                SUM(CASE WHEN a.status = 'sick_leave' THEN 1 ELSE 0 END) as sick_leave_count,
                SUM(CASE WHEN a.status = 'personal_leave' THEN 1 ELSE 0 END) as personal_leave_count
            FROM attendance a
            WHERE a.date = %s
        """, (date,))
        school_stats = cursor.fetchone()
        
        # 各年级统计
        cursor.execute("""
            SELECT 
                g.id as grade_id,
                g.name as grade_name,
                (SELECT COUNT(*) FROM students s JOIN classes c ON s.class_id = c.id 
                 WHERE c.grade_id = g.id AND s.status = 'active') as total_students,
                SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present_count,
                SUM(CASE WHEN a.status != 'present' OR a.status IS NULL THEN 0 ELSE 1 END) as recorded_count
            FROM grades g
            LEFT JOIN classes c ON g.id = c.grade_id
            LEFT JOIN students s ON c.id = s.class_id AND s.status = 'active'
            LEFT JOIN attendance a ON s.id = a.student_id AND a.date = %s
            GROUP BY g.id
            ORDER BY g.name
        """, (date,))
        grade_stats = cursor.fetchall()
        
        # 计算出勤率
        for item in grade_stats:
            total = item['total_students'] or 0
            present = item['present_count'] or 0
            if total > 0:
                item['attendance_rate'] = round(present / total * 100, 1)
            else:
                item['attendance_rate'] = 0
        
        cursor.close()
        conn.close()
        
        return {
            "data": {
                "school_stats": school_stats,
                "grade_stats": grade_stats,
                "date": date
            }
        }
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))
