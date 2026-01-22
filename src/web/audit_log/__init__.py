# -*- coding: utf-8 -*-
"""审计日志模块"""
from .routes import router as audit_log_router, log_action

__all__ = ['audit_log_router', 'log_action']
