# -*- coding: utf-8 -*-
"""认证模块"""
from .routes import router
from .jwt import verify_password, get_password_hash, create_access_token, decode_token
from .dependencies import get_current_user, require_admin, require_teacher, CurrentUser, get_db_connection

__all__ = [
    'router',
    'verify_password',
    'get_password_hash',
    'create_access_token',
    'decode_token',
    'get_current_user',
    'require_admin',
    'require_teacher',
    'CurrentUser',
    'get_db_connection'
]
