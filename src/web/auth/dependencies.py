# -*- coding: utf-8 -*-
"""
认证依赖模块 - FastAPI 依赖注入
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import mysql.connector
from mysql.connector import Error

from .jwt import decode_token

# Bearer Token 安全方案
security = HTTPBearer()

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Zrx@060309',
    'database': 'calligraphy_ai',
    'charset': 'utf8mb4'
}


def get_db_connection():
    """获取数据库连接"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None


class CurrentUser:
    """当前用户信息"""
    def __init__(self, id: int, username: str, role: str, real_name: str = None):
        self.id = id
        self.username = username
        self.role = role
        self.real_name = real_name
    
    def is_admin(self) -> bool:
        return self.role == 'admin'
    
    def is_teacher(self) -> bool:
        return self.role == 'teacher'
    
    def is_student(self) -> bool:
        return self.role == 'student'


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """获取当前登录用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None:
        raise credentials_exception
    
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # 查询用户信息
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, username, role, real_name, is_active FROM users WHERE id = %s",
            (user_id,)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user is None:
            raise credentials_exception
        
        if not user['is_active']:
            raise HTTPException(status_code=403, detail="用户已被禁用")
        
        return CurrentUser(
            id=user['id'],
            username=user['username'],
            role=user['role'],
            real_name=user['real_name']
        )
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"查询用户失败: {e}")


async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """获取当前活跃用户"""
    return current_user


async def require_admin(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """要求管理员权限"""
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def require_teacher(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """要求教师或管理员权限"""
    if not (current_user.is_teacher() or current_user.is_admin()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要教师权限"
        )
    return current_user


async def require_student(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """要求学生或更高权限"""
    return current_user  # 所有登录用户都可以
