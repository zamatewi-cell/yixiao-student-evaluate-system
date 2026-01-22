---
description: 创建新的后端API模块的标准流程
---

# 添加后端API模块 Skill

本文档描述如何为本项目添加一个新的后端API模块。

## 步骤概览

1. 创建模块目录和文件
2. 编写API路由代码
3. 注册路由到主应用
4. 创建数据库迁移（如需要）
5. 更新文档

## 详细步骤

### 1. 创建模块目录

在 `src/web/` 下创建新模块目录：

```
src/web/
└── your_module/
    ├── __init__.py
    └── routes.py
```

### 2. 编写 routes.py

使用此模板：

```python
# -*- coding: utf-8 -*-
"""
模块名称
模块功能描述
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error

from ..auth.dependencies import get_db_connection, require_admin, require_teacher, CurrentUser

router = APIRouter(prefix="/api/your-module", tags=["模块名称"])


# ============== 数据模型 ==============

class YourModel(BaseModel):
    """模型描述"""
    field1: str
    field2: Optional[int] = None


# ============== API 端点 ==============

@router.get("/list")
async def get_list(
    current_user: CurrentUser = Depends(require_teacher)
):
    """获取列表"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM your_table ORDER BY id DESC")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"data": results}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
async def create_item(
    data: YourModel,
    current_user: CurrentUser = Depends(require_admin)
):
    """创建项目"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO your_table (field1, field2, created_at)
            VALUES (%s, %s, NOW())
        """, (data.field1, data.field2))
        conn.commit()
        item_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return {"message": "创建成功", "id": item_id}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))
```

### 3. 编写 __init__.py

```python
# -*- coding: utf-8 -*-
"""模块名称"""
from .routes import router as your_module_router

__all__ = ['your_module_router']
```

### 4. 注册路由到 app.py

在 `src/web/app.py` 中添加：

```python
# 在导入区域添加
from .your_module import your_module_router

# 在路由注册区域添加
app.include_router(your_module_router)
```

### 5. 创建数据库迁移

在 `migrations/` 下创建SQL文件：

```sql
-- migrations/vX.X_your_module.sql

CREATE TABLE IF NOT EXISTS your_table (
    id INT PRIMARY KEY AUTO_INCREMENT,
    field1 VARCHAR(100) NOT NULL,
    field2 INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_field1 (field1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='表描述';
```

### 6. 更新文档

- 更新 `README.md` API列表
- 更新 `CHANGELOG.md` 添加变更记录
- 更新 `.agent/implementation_plan_v2.md` 进度

## 权限装饰器

| 装饰器 | 用途 |
|--------|------|
| `require_admin` | 仅管理员可访问 |
| `require_teacher` | 教师和管理员可访问 |
| 无装饰器 | 公开API |

## 常见模式

### 分页查询
```python
@router.get("/list")
async def get_list(page: int = 1, page_size: int = 10):
    offset = (page - 1) * page_size
    # SELECT ... LIMIT %s OFFSET %s, (page_size, offset)
```

### 日期格式化
```python
for item in results:
    if item.get('created_at'):
        item['created_at'] = str(item['created_at'])
```

### 事务处理
```python
try:
    cursor = conn.cursor()
    # 多个操作...
    conn.commit()
except:
    conn.rollback()
    raise
```
