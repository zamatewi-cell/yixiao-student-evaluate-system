# -*- coding: utf-8 -*-
"""
系统健康监控模块
监控系统运行状态
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
import mysql.connector
from mysql.connector import Error
import os
import psutil

from ..auth.dependencies import get_db_connection, require_admin, CurrentUser

router = APIRouter(prefix="/api/health", tags=["系统健康"])


@router.get("/status")
async def get_system_status():
    """获取系统基本状态（公开）"""
    # 检查数据库连接
    db_status = "ok"
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
        else:
            db_status = "error"
    except Exception:
        db_status = "error"
    
    return {
        "status": "running",
        "database": db_status,
        "timestamp": datetime.now().isoformat(),
        "version": "2.1.0"
    }


@router.get("/detailed")
async def get_detailed_status(
    current_user: CurrentUser = Depends(require_admin)
):
    """获取详细系统状态（需管理员权限）"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 数据库统计
        stats = {}
        
        # 用户统计
        cursor.execute("SELECT COUNT(*) as total FROM users")
        stats['total_users'] = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role = 'teacher'")
        stats['total_teachers'] = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM students WHERE status = 'active'")
        stats['total_students'] = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM classes")
        stats['total_classes'] = cursor.fetchone()['total']
        
        # 今日统计
        today = datetime.now().date()
        
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE DATE(last_login) = %s", (today,))
        stats['today_logins'] = cursor.fetchone()['total']
        
        # 尝试获取考勤数据
        try:
            cursor.execute("SELECT COUNT(*) as total FROM attendance WHERE date = %s", (today,))
            stats['today_attendance'] = cursor.fetchone()['total']
        except Exception:
            stats['today_attendance'] = 0
        
        # 数据库大小（MySQL）
        cursor.execute("""
            SELECT 
                SUM(data_length + index_length) / 1024 / 1024 as size_mb
            FROM information_schema.tables 
            WHERE table_schema = DATABASE()
        """)
        result = cursor.fetchone()
        stats['database_size_mb'] = round(float(result['size_mb'] or 0), 2)
        
        # 表记录数
        tables = ['users', 'students', 'teachers', 'classes', 'semesters']
        table_counts = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
                table_counts[table] = cursor.fetchone()['cnt']
            except Exception:
                table_counts[table] = 0
        
        cursor.close()
        conn.close()
        
        # 服务器资源（如果可用）
        server_info = {}
        try:
            server_info['cpu_percent'] = psutil.cpu_percent(interval=1)
            server_info['memory_percent'] = psutil.virtual_memory().percent
            server_info['disk_percent'] = psutil.disk_usage('/').percent
        except Exception:
            server_info['cpu_percent'] = None
            server_info['memory_percent'] = None
            server_info['disk_percent'] = None
        
        return {
            "data": {
                "status": "running",
                "timestamp": datetime.now().isoformat(),
                "version": "2.1.0",
                "statistics": stats,
                "table_counts": table_counts,
                "server": server_info
            }
        }
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard-summary")
async def get_dashboard_summary(
    current_user: CurrentUser = Depends(require_admin)
):
    """获取仪表盘摘要数据"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 基础统计
        summary = {}
        
        # 学生性别分布
        cursor.execute("""
            SELECT gender, COUNT(*) as count FROM students 
            WHERE status = 'active' GROUP BY gender
        """)
        gender_stats = {r['gender']: r['count'] for r in cursor.fetchall()}
        summary['gender_distribution'] = gender_stats
        
        # 年级人数分布
        cursor.execute("""
            SELECT g.name as grade_name, COUNT(s.id) as count
            FROM grades g
            LEFT JOIN classes c ON g.id = c.grade_id
            LEFT JOIN students s ON c.id = s.class_id AND s.status = 'active'
            GROUP BY g.id, g.name
            ORDER BY g.sort_order
        """)
        summary['grade_distribution'] = cursor.fetchall()
        
        # 最近7天登录趋势
        cursor.execute("""
            SELECT DATE(last_login) as date, COUNT(*) as count
            FROM users
            WHERE last_login >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY DATE(last_login)
            ORDER BY date
        """)
        login_trend = cursor.fetchall()
        for item in login_trend:
            item['date'] = str(item['date'])
        summary['login_trend'] = login_trend
        
        # 最近通知
        try:
            cursor.execute("""
                SELECT id, title, notice_type, created_at
                FROM notices
                WHERE status = 'published'
                ORDER BY created_at DESC
                LIMIT 5
            """)
            notices = cursor.fetchall()
            for n in notices:
                n['created_at'] = str(n['created_at'])
            summary['recent_notices'] = notices
        except Exception:
            summary['recent_notices'] = []
        
        cursor.close()
        conn.close()
        
        return {"data": summary}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))
