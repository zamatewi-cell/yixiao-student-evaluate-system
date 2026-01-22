# -*- coding: utf-8 -*-
"""
系统配置中心模块
统一管理系统参数和配置
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
import json

from ..auth.dependencies import get_db_connection, require_admin, CurrentUser

router = APIRouter(prefix="/api/system-config", tags=["系统配置"])


class ConfigItem(BaseModel):
    """配置项"""
    key: str
    value: str
    description: Optional[str] = None


class ConfigUpdate(BaseModel):
    """配置更新"""
    configs: List[ConfigItem]


# 默认配置
DEFAULT_CONFIGS = {
    "school_name": {"value": "小学", "description": "学校名称", "category": "basic"},
    "school_logo": {"value": "", "description": "学校Logo URL", "category": "basic"},
    "school_address": {"value": "", "description": "学校地址", "category": "basic"},
    "school_phone": {"value": "", "description": "学校电话", "category": "basic"},
    
    "score_pass_line": {"value": "60", "description": "默认及格分数线", "category": "exam"},
    "score_excellent_line": {"value": "85", "description": "默认优秀分数线", "category": "exam"},
    "max_score": {"value": "100", "description": "默认满分", "category": "exam"},
    
    "attendance_late_minutes": {"value": "10", "description": "迟到判定时间(分钟)", "category": "attendance"},
    "attendance_absent_hours": {"value": "2", "description": "缺勤判定时间(小时)", "category": "attendance"},
    
    "ai_api_key": {"value": "", "description": "AI服务API密钥", "category": "ai"},
    "ai_model": {"value": "qwen-turbo", "description": "AI模型名称", "category": "ai"},
    
    "backup_auto_enabled": {"value": "false", "description": "是否启用自动备份", "category": "system"},
    "backup_keep_days": {"value": "30", "description": "备份保留天数", "category": "system"},
    "session_timeout_hours": {"value": "24", "description": "会话超时时间(小时)", "category": "system"},
}


@router.get("/list")
async def get_all_configs(
    category: Optional[str] = None,
    current_user: CurrentUser = Depends(require_admin)
):
    """获取所有配置项"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        sql = "SELECT * FROM system_configs"
        params = []
        if category:
            sql += " WHERE category = %s"
            params.append(category)
        sql += " ORDER BY category, config_key"
        
        cursor.execute(sql, tuple(params))
        configs = cursor.fetchall()
        
        # 如果数据库为空，返回默认配置
        if not configs:
            configs = []
            for key, info in DEFAULT_CONFIGS.items():
                configs.append({
                    "config_key": key,
                    "config_value": info["value"],
                    "description": info["description"],
                    "category": info["category"]
                })
        
        cursor.close()
        conn.close()
        
        # 按分类分组
        grouped = {}
        for c in configs:
            cat = c.get('category', 'other')
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(c)
        
        return {"data": configs, "grouped": grouped}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get/{key}")
async def get_config(
    key: str,
    current_user: CurrentUser = Depends(require_admin)
):
    """获取单个配置项"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM system_configs WHERE config_key = %s", (key,))
        config = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not config and key in DEFAULT_CONFIGS:
            return {
                "data": {
                    "config_key": key,
                    "config_value": DEFAULT_CONFIGS[key]["value"],
                    "description": DEFAULT_CONFIGS[key]["description"]
                }
            }
        
        return {"data": config}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/update")
async def update_configs(
    data: ConfigUpdate,
    current_user: CurrentUser = Depends(require_admin)
):
    """批量更新配置"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        
        for item in data.configs:
            default_info = DEFAULT_CONFIGS.get(item.key, {})
            category = default_info.get("category", "other")
            description = item.description or default_info.get("description", "")
            
            cursor.execute("""
                INSERT INTO system_configs (config_key, config_value, description, category, updated_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    config_value = VALUES(config_value),
                    description = VALUES(description),
                    updated_at = NOW()
            """, (item.key, item.value, description, category))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": f"成功更新{len(data.configs)}项配置"}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/init-defaults")
async def init_default_configs(
    current_user: CurrentUser = Depends(require_admin)
):
    """初始化默认配置"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        
        for key, info in DEFAULT_CONFIGS.items():
            cursor.execute("""
                INSERT IGNORE INTO system_configs (config_key, config_value, description, category, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (key, info["value"], info["description"], info["category"]))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "默认配置初始化完成"}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))
