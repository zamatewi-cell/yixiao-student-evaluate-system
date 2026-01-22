# -*- coding: utf-8 -*-
"""
通知公告系统模块
发布和管理学校通知
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error

from ..auth.dependencies import get_db_connection, require_admin, require_teacher, CurrentUser

router = APIRouter(prefix="/api/notice", tags=["通知公告"])


class NoticeCreate(BaseModel):
    """创建通知"""
    title: str
    content: str
    notice_type: str = "general"  # general, exam, attendance, activity, urgent
    target_type: str = "all"  # all, teacher, student, class, grade
    target_ids: Optional[List[int]] = None
    is_pinned: bool = False
    valid_until: Optional[str] = None


class NoticeUpdate(BaseModel):
    """更新通知"""
    title: Optional[str] = None
    content: Optional[str] = None
    notice_type: Optional[str] = None
    is_pinned: Optional[bool] = None
    valid_until: Optional[str] = None
    status: Optional[str] = None


# 通知类型
NOTICE_TYPES = {
    "general": {"text": "一般通知", "color": "blue"},
    "exam": {"text": "考试通知", "color": "orange"},
    "attendance": {"text": "考勤通知", "color": "green"},
    "activity": {"text": "活动通知", "color": "purple"},
    "urgent": {"text": "紧急通知", "color": "red"}
}


@router.post("/create")
async def create_notice(
    notice: NoticeCreate,
    current_user: CurrentUser = Depends(require_admin)
):
    """创建通知"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO notices 
            (title, content, notice_type, target_type, target_ids, 
             is_pinned, valid_until, created_by, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'published', NOW())
        """, (
            notice.title, notice.content, notice.notice_type,
            notice.target_type, 
            ','.join(map(str, notice.target_ids)) if notice.target_ids else None,
            notice.is_pinned, notice.valid_until, current_user.id
        ))
        
        notice_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "通知发布成功", "id": notice_id}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def get_notices(
    notice_type: Optional[str] = None,
    target_type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    current_user: CurrentUser = Depends(require_teacher)
):
    """获取通知列表"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        sql = """
            SELECT n.*, u.real_name as author_name
            FROM notices n
            LEFT JOIN users u ON n.created_by = u.id
            WHERE 1=1
        """
        count_sql = "SELECT COUNT(*) as total FROM notices n WHERE 1=1"
        params = []
        
        if notice_type:
            sql += " AND n.notice_type = %s"
            count_sql += " AND n.notice_type = %s"
            params.append(notice_type)
        if target_type:
            sql += " AND n.target_type = %s"
            count_sql += " AND n.target_type = %s"
            params.append(target_type)
        if status:
            sql += " AND n.status = %s"
            count_sql += " AND n.status = %s"
            params.append(status)
        
        # 获取总数
        cursor.execute(count_sql, tuple(params))
        total = cursor.fetchone()['total']
        
        # 排序和分页
        sql += " ORDER BY n.is_pinned DESC, n.created_at DESC LIMIT %s OFFSET %s"
        params.extend([page_size, (page - 1) * page_size])
        
        cursor.execute(sql, tuple(params))
        notices = cursor.fetchall()
        
        # 格式化
        for n in notices:
            n['notice_type_info'] = NOTICE_TYPES.get(n['notice_type'], {"text": n['notice_type'], "color": "default"})
            if n.get('created_at'):
                n['created_at'] = str(n['created_at'])
            if n.get('valid_until'):
                n['valid_until'] = str(n['valid_until'])
        
        cursor.close()
        conn.close()
        
        return {
            "data": notices,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/public")
async def get_public_notices(
    limit: int = 5
):
    """获取公开通知（无需登录）"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, title, notice_type, is_pinned, created_at
            FROM notices
            WHERE status = 'published' 
                AND target_type = 'all'
                AND (valid_until IS NULL OR valid_until >= CURDATE())
            ORDER BY is_pinned DESC, created_at DESC
            LIMIT %s
        """, (limit,))
        notices = cursor.fetchall()
        
        for n in notices:
            n['notice_type_info'] = NOTICE_TYPES.get(n['notice_type'], {"text": n['notice_type'], "color": "default"})
            if n.get('created_at'):
                n['created_at'] = str(n['created_at'])
        
        cursor.close()
        conn.close()
        
        return {"data": notices}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{notice_id}")
async def get_notice_detail(
    notice_id: int,
    current_user: CurrentUser = Depends(require_teacher)
):
    """获取通知详情"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT n.*, u.real_name as author_name
            FROM notices n
            LEFT JOIN users u ON n.created_by = u.id
            WHERE n.id = %s
        """, (notice_id,))
        notice = cursor.fetchone()
        
        if not notice:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="通知不存在")
        
        # 更新阅读次数
        cursor.execute("UPDATE notices SET view_count = view_count + 1 WHERE id = %s", (notice_id,))
        conn.commit()
        
        notice['notice_type_info'] = NOTICE_TYPES.get(notice['notice_type'], {"text": notice['notice_type'], "color": "default"})
        if notice.get('created_at'):
            notice['created_at'] = str(notice['created_at'])
        if notice.get('valid_until'):
            notice['valid_until'] = str(notice['valid_until'])
        
        cursor.close()
        conn.close()
        
        return {"data": notice}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{notice_id}")
async def update_notice(
    notice_id: int,
    update_data: NoticeUpdate,
    current_user: CurrentUser = Depends(require_admin)
):
    """更新通知"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if update_data.title is not None:
            updates.append("title = %s")
            params.append(update_data.title)
        if update_data.content is not None:
            updates.append("content = %s")
            params.append(update_data.content)
        if update_data.notice_type is not None:
            updates.append("notice_type = %s")
            params.append(update_data.notice_type)
        if update_data.is_pinned is not None:
            updates.append("is_pinned = %s")
            params.append(update_data.is_pinned)
        if update_data.valid_until is not None:
            updates.append("valid_until = %s")
            params.append(update_data.valid_until)
        if update_data.status is not None:
            updates.append("status = %s")
            params.append(update_data.status)
        
        if updates:
            updates.append("updated_at = NOW()")
            params.append(notice_id)
            cursor.execute(f"UPDATE notices SET {', '.join(updates)} WHERE id = %s", tuple(params))
            conn.commit()
        
        cursor.close()
        conn.close()
        
        return {"message": "更新成功"}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{notice_id}")
async def delete_notice(
    notice_id: int,
    current_user: CurrentUser = Depends(require_admin)
):
    """删除通知"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM notices WHERE id = %s", (notice_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "删除成功"}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))
