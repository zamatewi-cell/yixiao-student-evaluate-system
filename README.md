# 学生综合素质评价系统 V2.2

<p align="center">
  <img src="https://img.shields.io/badge/version-2.2.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/python-3.9+-green.svg" alt="Python">
  <img src="https://img.shields.io/badge/node-18+-brightgreen.svg" alt="Node.js">
  <img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="License">
</p>

> 基于 FastAPI + React + MySQL 的学生综合素质评价管理系统

---

## ? 系统简介

学生综合素质评价系统是一款面向小学的综合管理平台，支持学生评价、成绩管理、考勤管理、AI智能分析等功能。

## ? 功能特性

### 核心功能
- ? **学生管理**：学生信息CRUD、转班、升级、毕业处理
- ??? **教师管理**：教师账号、权限控制、班级分配
- ? **评价指标**：自定义评价项、多类型评分（分数/等级/布尔）
- ? **AI评语生成**：基于评价数据自动生成学生期末评语

### V2.0 新增功能
- ? **考试管理**：创建考试、设置科目、成绩录入、排名计算
- ? **成绩统计**：平均分、及格率、优秀率、班级/年级排名
- ? **考勤管理**：考勤记录、请假管理、统计报表
- ? **数据大屏**：实时展示全校、年级、班级数据
- ? **数据导入导出**：学生、教师、成绩CSV导入导出
- ? **AI试卷分析**：智能分析考试成绩、生成教学建议
- ? **数据库备份**：手动备份、历史记录查询

### V2.1 新增功能
- ? **教师权限管理**：班主任/科任教师角色区分
- ?? **错题分析**：错题记录、知识点统计、AI分析

### V2.2 新增功能（当前版本）
- ?? **系统配置中心**：学校信息、考试设置、AI配置统一管理
- ? **审计日志**：操作记录、活动统计、日志清理
- ? **通知公告**：发布通知、置顶、多类型支持
- ? **成绩单打印**：生成可打印的HTML成绩报告单
- ? **系统健康监控**：数据库状态、服务器资源监控

## ?? 技术栈

### 后端
- **框架**: FastAPI 0.104+
- **数据库**: MySQL 8.0+
- **ORM**: 原生 mysql-connector
- **认证**: JWT Token
- **AI**: 通义千问 API

### 前端
- **框架**: React 18 + TypeScript
- **UI库**: Ant Design 5.x
- **状态管理**: Zustand
- **构建工具**: Vite 5
- **HTTP**: Axios

## ? 项目结构

```
yixiao-student-evaluate-system/
├── src/
│   └── web/
│       ├── auth/              # 认证模块
│       ├── admin/             # 管理员模块
│       ├── teacher/           # 教师模块
│       ├── student/           # 学生模块
│       ├── exam/              # 考试管理模块
│       ├── attendance/        # 考勤管理模块
│       ├── import_export/     # 导入导出模块
│       ├── ai_analysis/       # AI分析模块
│       ├── teacher_role/      # 教师角色模块
│       ├── wrong_answer/      # 错题分析模块
│       ├── system_config/     # 系统配置模块 (V2.2)
│       ├── audit_log/         # 审计日志模块 (V2.2)
│       ├── notice/            # 通知公告模块 (V2.2)
│       ├── report/            # 报告生成模块 (V2.2)
│       ├── health/            # 健康监控模块 (V2.2)
│       └── app.py             # 主应用
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Admin/         # 管理员页面
│       │   ├── Teacher/       # 教师页面
│       │   ├── Exam/          # 考试管理页面
│       │   ├── Attendance/    # 考勤管理页面
│       │   ├── WrongAnswer/   # 错题分析页面
│       │   └── DataScreen/    # 数据大屏
│       └── components/        # 公共组件
├── migrations/                # 数据库迁移脚本
├── database/                  # 数据库初始化脚本
└── configs/                   # 配置文件
```

## ? 快速开始

### 1. 环境要求
- Python 3.9+
- Node.js 18+
- MySQL 8.0+

### 2. 后端启动
```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库
mysql -u root -p < database/init_full.sql
mysql -u root -p calligraphy_ai < migrations/v2_feature_expansion.sql
mysql -u root -p calligraphy_ai < migrations/v2.1_wrong_answer.sql
mysql -u root -p calligraphy_ai < migrations/v2.2_system_enhance.sql

# 启动后端
python run_web.py
```

### 3. 前端启动
```bash
cd frontend
npm install
npm run dev
```

### 4. 访问系统
- 前端: http://localhost:3000
- 后端API: http://localhost:8000/docs
- 数据大屏: http://localhost:3000/data-screen
- 系统健康: http://localhost:8000/api/health/status

### 5. 默认账号
- 管理员: `admin` / `admin123`

## ? API 模块概览

| 模块 | 前缀 | 功能 |
|------|------|------|
| 认证 | `/api/auth` | 登录、注册、个人信息 |
| 管理员 | `/api/admin` | 用户、学期、班级、学生、教师管理 |
| 教师 | `/api/teacher` | 数据录入、评语管理 |
| 考试 | `/api/exam` | 考试CRUD、成绩录入、排名 |
| 考勤 | `/api/attendance` | 考勤记录、统计 |
| 导入导出 | `/api/import-export` | CSV导入导出 |
| AI分析 | `/api/ai-analysis` | AI试卷分析 |
| 错题 | `/api/wrong-answer` | 错题记录与分析 |
| 教师角色 | `/api/teacher-role` | 权限管理 |
| 系统配置 | `/api/system-config` | 参数配置 |
| 审计日志 | `/api/audit-log` | 操作日志 |
| 通知 | `/api/notice` | 通知公告 |
| 报告 | `/api/report` | 成绩单生成 |
| 健康 | `/api/health` | 系统状态 |

## ? 更新日志

查看 [CHANGELOG.md](./CHANGELOG.md) 了解版本更新详情。

## ? 贡献

欢迎提交 Issue 和 Pull Request！

## ? 许可证

MIT License

---

<p align="center">
  <strong>学生综合素质评价系统 V2.2</strong><br>
  最后更新: 2026-01-22
</p>
