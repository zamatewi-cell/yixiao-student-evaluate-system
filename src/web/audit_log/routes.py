# -*- coding: utf-8 -*-
"""
操作日志审计模块
记录系统重要操作
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error

from ..auth.dependencies import get_db_connection, require_admin, CurrentUser

router = APIRouter(prefix="/api/audit-log", tags=["审计日志"])


class LogQuery(BaseModel):
    """日志查询条件"""
    user_id: Optional[int] = None
    action_type: Optional[str] = None
    module: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    page: int = 1
    page_size: int = 20


# 操作类型映射
ACTION_TYPES = {
    "login": "用户登录",
    "logout": "用户登出",
    "create": "创建数据",
    "update": "更新数据",
    "delete": "删除数据",
    "export": "导出数据",
    "import": "导入数据",
    "backup": "数据备份",
    "config": "系统配置",
    "permission": "权限变更"
}

# 模块映射
MODULES = {
    "auth": "认证模块",
    "student": "学生管理",
    "teacher": "教师管理",
    "class": "班级管理",
    "exam": "考试管理",
    "score": "成绩管理",
    "attendance": "考勤管理",
    "comment": "评语管理",
    "system": "系统管理"
}


def log_action(user_id: int, action_type: str, module: str, 
               description: str, ip_address: str = None, 
               target_id: int = None, target_type: str = None):
    """记录操作日志（工具函数，供其他模块调用）"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_logs 
            (user_id, action_type, module, description, ip_address, target_id, target_type, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        """, (user_id, action_type, module, description, ip_address, target_id, target_type))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception:
        if conn: conn.close()


@router.get("/list")
async def get_audit_logs(
    user_id: Optional[int] = None,
    action_type: Optional[str] = None,
    module: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: CurrentUser = Depends(require_admin)
):
    """获取审计日志列表"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 构建查询
        sql = """
            SELECT al.*, u.username, u.real_name
            FROM audit_logs al
            LEFT JOIN users u ON al.user_id = u.id
            WHERE 1=1
        """
        count_sql = "SELECT COUNT(*) as total FROM audit_logs al WHERE 1=1"
        params = []
        
        if user_id:
            sql += " AND al.user_id = %s"
            count_sql += " AND al.user_id = %s"
            params.append(user_id)
        if action_type:
            sql += " AND al.action_type = %s"
            count_sql += " AND al.action_type = %s"
            params.append(action_type)
        if module:
            sql += " AND al.module = %s"
            count_sql += " AND al.module = %s"
            params.append(module)
        if start_date:
            sql += " AND DATE(al.created_at) >= %s"
            count_sql += " AND DATE(al.created_at) >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND DATE(al.created_at) <= %s"
            count_sql += " AND DATE(al.created_at) <= %s"
            params.append(end_date)
        
        # 获取总数
        cursor.execute(count_sql, tuple(params))
        total = cursor.fetchone()['total']
        
        # 分页
        sql += " ORDER BY al.created_at DESC LIMIT %s OFFSET %s"
        params.extend([page_size, (page - 1) * page_size])
        
        cursor.execute(sql, tuple(params))
        logs = cursor.fetchall()
        
        # 格式化
        for log in logs:
            log['action_type_text'] = ACTION_TYPES.get(log['action_type'], log['action_type'])
            log['module_text'] = MODULES.get(log['module'], log['module'])
            if log.get('created_at'):
                log['created_at'] = str(log['created_at'])
        
        cursor.close()
        conn.close()
        
        return {
            "data": logs,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_log_statistics(
    days: int = 7,
    current_user: CurrentUser = Depends(require_admin)
):
    """获取日志统计"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        start_date = datetime.now() - timedelta(days=days)
        
        # 按操作类型统计
        cursor.execute("""
            SELECT action_type, COUNT(*) as count
            FROM audit_logs
            WHERE created_at >= %s
            GROUP BY action_type
            ORDER BY count DESC
        """, (start_date,))
        action_stats = cursor.fetchall()
        
        # 按模块统计
        cursor.execute("""
            SELECT module, COUNT(*) as count
            FROM audit_logs
            WHERE created_at >= %s
            GROUP BY module
            ORDER BY count DESC
        """, (start_date,))
        module_stats = cursor.fetchall()
        
        # 按日期统计
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM audit_logs
            WHERE created_at >= %s
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (start_date,))
        daily_stats = cursor.fetchall()
        
        # 活跃用户排行
        cursor.execute("""
            SELECT al.user_id, u.username, u.real_name, COUNT(*) as count
            FROM audit_logs al
            LEFT JOIN users u ON al.user_id = u.id
            WHERE al.created_at >= %s
            GROUP BY al.user_id, u.username, u.real_name
            ORDER BY count DESC
            LIMIT 10
        """, (start_date,))
        user_stats = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 格式化
        for s in action_stats:
            s['action_type_text'] = ACTION_TYPES.get(s['action_type'], s['action_type'])
        for s in module_stats:
            s['module_text'] = MODULES.get(s['module'], s['module'])
        for s in daily_stats:
            s['date'] = str(s['date'])
        
        return {
            "data": {
                "action_stats": action_stats,
                "module_stats": module_stats,
                "daily_stats": daily_stats,
                "user_stats": user_stats
            }
        }
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup")
async def cleanup_old_logs(
    days: int = 90,
    current_user: CurrentUser = Depends(require_admin)
):
    """清理旧日志"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        cursor.execute("DELETE FROM audit_logs WHERE created_at < %s", (cutoff_date,))
        deleted = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": f"清理完成，删除{deleted}条旧日志"}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))
