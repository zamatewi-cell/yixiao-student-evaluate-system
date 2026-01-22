---
description: 学生综合素质评价系统项目概览和开发规范
---

# 项目概览 Skill

## 系统信息

- **项目名称**: 学生综合素质评价系统 (yixiao-student-evaluate-system)
- **当前版本**: V2.2.0
- **技术栈**: FastAPI + React + MySQL + TypeScript

## 目录结构

```
yixiao-student-evaluate-system/
├── src/web/                    # 后端代码
│   ├── app.py                  # 主应用入口
│   ├── auth/                   # 认证模块
│   ├── admin/                  # 管理员模块
│   ├── teacher/                # 教师模块
│   ├── student/                # 学生模块
│   ├── exam/                   # 考试管理
│   ├── attendance/             # 考勤管理
│   ├── teacher_role/           # 教师权限
│   ├── wrong_answer/           # 错题分析
│   ├── import_export/          # 数据导入导出
│   ├── ai_analysis/            # AI分析
│   ├── system_config/          # 系统配置
│   ├── audit_log/              # 审计日志
│   ├── notice/                 # 通知公告
│   ├── report/                 # 报告生成
│   ├── health/                 # 健康监控
│   └── statistics/             # 统计模块
├── frontend/                   # 前端代码
│   └── src/
│       ├── pages/              # 页面组件
│       ├── components/         # 公共组件
│       ├── stores/             # Zustand状态
│       └── App.tsx             # 路由配置
├── migrations/                 # 数据库迁移
├── database/                   # 数据库初始化
├── configs/                    # 配置文件
└── .agent/                     # 开发文档
```

## 开发端口

| 服务 | 端口 | URL |
|------|------|-----|
| 前端 | 3000 | http://localhost:3000 |
| 后端 | 8000 | http://localhost:8000 |
| API文档 | 8000 | http://localhost:8000/docs |

## 数据库配置

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Zrx@060309',
    'database': 'calligraphy_ai',
    'charset': 'utf8mb4'
}
```

## 常用命令

### 启动服务
```bash
# 后端
python run_web.py

# 前端
cd frontend && npm run dev
```

### 数据库操作
```bash
# 初始化数据库
mysql -u root -p < database/init_full.sql

# 执行迁移
mysql -u root -p calligraphy_ai < migrations/xxx.sql
```

## 编码规范

1. **后端Python**
   - 所有注释使用中文
   - 使用类型注解
   - 遵循PEP 8规范
   - 每个模块有独立的 `routes.py` 和 `__init__.py`

2. **前端TypeScript**
   - 使用函数式组件
   - 使用 Ant Design 组件库
   - 使用 axios 进行API调用
   - 使用 zustand 管理状态

3. **API设计**
   - RESTful风格
   - 使用JWT认证
   - 返回格式: `{"data": ..., "message": ...}`
   - 错误使用 HTTPException

## 权限角色

| 角色 | 权限 |
|------|------|
| admin | 所有功能 |
| teacher | 教师功能（数据录入、评语等） |
| student | 学生查询（无需登录） |
