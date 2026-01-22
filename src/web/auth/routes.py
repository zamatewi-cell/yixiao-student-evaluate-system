# -*- coding: utf-8 -*-
"""
认证路由模块
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error

from .jwt import verify_password, get_password_hash, create_access_token
from .dependencies import get_db_connection, get_current_user, CurrentUser

router = APIRouter(prefix="/api/auth", tags=["认证"])


# ============== 请求/响应模型 ==============

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class TeacherRegisterRequest(BaseModel):
    """教师注册请求模型"""
    username: str
    password: str
    real_name: str
    gender: str = 'female'  # male/female
    phone: Optional[str] = None
    email: Optional[str] = None
    subjects: Optional[str] = None  # 任教科目


class UserInfoResponse(BaseModel):
    id: int
    username: str
    role: str
    real_name: Optional[str]
    phone: Optional[str]
    email: Optional[str]


# ============== 路由 ==============

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """用户登录"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, username, password_hash, role, real_name, is_active FROM users WHERE username = %s",
            (request.username,)
        )
        user = cursor.fetchone()
        
        if user is None:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        if not user['is_active']:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=403, detail="用户已被禁用")
        
        if not verify_password(request.password, user['password_hash']):
            cursor.close()
            conn.close()
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        # 更新最后登录时间
        cursor.execute(
            "UPDATE users SET last_login = %s WHERE id = %s",
            (datetime.now(), user['id'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        # 创建访问令牌
        access_token = create_access_token(data={"sub": str(user['id'])})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user['id'],
                "username": user['username'],
                "role": user['role'],
                "real_name": user['real_name']
            }
        }
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"登录失败: {e}")


@router.post("/register/teacher")
async def register_teacher(request: TeacherRegisterRequest):
    """教师注册"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 检查用户名是否已存在
        cursor.execute("SELECT id FROM users WHERE username = %s", (request.username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail="用户名已存在")
        
        # 验证用户名格式（字母、数字、下划线，4-20字符）
        import re
        if not re.match(r'^[a-zA-Z0-9_]{4,20}$', request.username):
            cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail="用户名需为4-20位字母、数字或下划线")
        
        # 验证密码长度
        if len(request.password) < 6:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail="密码长度至少6位")
        
        # 创建用户账号（is_active=FALSE，需要管理员审核授权）
        password_hash = get_password_hash(request.password)
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, real_name, phone, email, is_active, created_at)
            VALUES (%s, %s, 'teacher', %s, %s, %s, FALSE, NOW())
        """, (request.username, password_hash, request.real_name, request.phone, request.email))
        user_id = cursor.lastrowid
        
        # 同时创建教师记录（teachers表只有 name, gender, subjects, user_id, created_at 等字段）
        cursor.execute("""
            INSERT INTO teachers (name, gender, subjects, user_id, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (request.real_name, request.gender, request.subjects, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # 注册成功但需要等待管理员授权
        return {
            "success": True,
            "message": "注册成功！您的账号正在等待管理员审核授权，请稍后再登录。",
            "pending_approval": True,
            "user": {
                "id": user_id,
                "username": request.username,
                "role": "teacher",
                "real_name": request.real_name
            }
        }
    except Error as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=f"注册失败: {e}")


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(current_user: CurrentUser = Depends(get_current_user)):
    """获取当前用户信息"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, username, role, real_name, phone, email FROM users WHERE id = %s",
            (current_user.id,)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user is None:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return user
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"查询失败: {e}")


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """修改密码"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 验证旧密码
        cursor.execute(
            "SELECT password_hash FROM users WHERE id = %s",
            (current_user.id,)
        )
        user = cursor.fetchone()
        
        if not verify_password(request.old_password, user['password_hash']):
            cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail="原密码错误")
        
        # 更新密码
        new_hash = get_password_hash(request.new_password)
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (new_hash, current_user.id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "密码修改成功"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"修改密码失败: {e}")


@router.post("/logout")
async def logout(current_user: CurrentUser = Depends(get_current_user)):
    """登出（客户端需删除token）"""
    return {"message": "登出成功"}


# ============== 个人资料 ==============

class UpdateProfileRequest(BaseModel):
    """个人资料更新请求"""
    real_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None  # 头像URL
    signature: Optional[str] = None  # 个性签名


@router.get("/profile")
async def get_user_profile(current_user: CurrentUser = Depends(get_current_user)):
    """获取用户完整个人资料"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, username, role, real_name, phone, email, avatar, signature, 
                   is_active, created_at, last_login
            FROM users WHERE id = %s
        """, (current_user.id,))
        user = cursor.fetchone()
        
        # 如果是教师，获取教师相关信息
        teacher_info = None
        if user and user['role'] == 'teacher':
            cursor.execute("""
                SELECT t.id as teacher_id, t.gender, t.subjects, t.can_edit,
                       (SELECT COUNT(*) FROM classes c WHERE c.head_teacher_id = t.id) as class_count
                FROM teachers t WHERE t.user_id = %s
            """, (current_user.id,))
            teacher_info = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user is None:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 格式化日期
        if user.get('created_at'):
            user['created_at'] = str(user['created_at'])
        if user.get('last_login'):
            user['last_login'] = str(user['last_login'])
        
        result = {
            "user": user,
            "teacher_info": teacher_info
        }
        return result
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=f"查询失败: {e}")


@router.put("/profile")
async def update_user_profile(
    request: UpdateProfileRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """更新用户个人资料"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        
        # 构建动态更新语句
        updates = []
        values = []
        
        if request.real_name is not None:
            updates.append("real_name = %s")
            values.append(request.real_name)
        if request.phone is not None:
            updates.append("phone = %s")
            values.append(request.phone)
        if request.email is not None:
            updates.append("email = %s")
            values.append(request.email)
        if request.avatar is not None:
            updates.append("avatar = %s")
            values.append(request.avatar)
        if request.signature is not None:
            updates.append("signature = %s")
            values.append(request.signature)
        
        if not updates:
            cursor.close()
            conn.close()
            return {"message": "没有需要更新的内容"}
        
        values.append(current_user.id)
        sql = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(sql, tuple(values))
        
        # 如果是教师且更新了 real_name，同步更新 teachers 表
        if request.real_name is not None:
            cursor.execute("""
                UPDATE teachers SET name = %s WHERE user_id = %s
            """, (request.real_name, current_user.id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "个人资料更新成功"}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=f"更新失败: {e}")

