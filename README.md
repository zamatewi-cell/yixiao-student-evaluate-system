# 学生综合素质评价系统

<p align="center">
  <img src="https://img.shields.io/badge/版本-1.0.0-blue.svg" alt="版本">
  <img src="https://img.shields.io/badge/状态-开发完成-green.svg" alt="状态">
  <img src="https://img.shields.io/badge/Python-3.9+-yellow.svg" alt="Python">
  <img src="https://img.shields.io/badge/React-18+-61DAFB.svg" alt="React">
</p>

## ? 项目简介

学生综合素质评价系统是一款面向中小学的综合素质评价管理平台，支持多维度评价指标配置、教师数据录入、AI智能评语生成、学生/家长查询等功能。

## ? 核心功能

### ? 管理员功能
- **学期管理**: 创建、编辑、删除学期，设置当前学期
- **班级管理**: 管理班级信息，分配班主任
- **学生管理**: 学生信息录入、条码生成、批量导入
- **教师管理**: 教师账号管理、权限分配
- **评价指标**: 自定义评价维度和指标（分数/等级/布尔类型）
- **统计报表**: 可视化数据统计，ECharts图表展示

### ??? 教师功能
- **数据录入**: 批量录入学生各项评价数据
- **评语管理**: AI智能生成期末评语，支持编辑和发布
- **Excel导入导出**: 
  - 下载评价模板
  - 批量导入评价数据
  - 导出班级评价报表
  - 导出期末评语

### ? 学生/家长功能
- **成绩查询**: 通过学号查询综合素质评价
- **评语查看**: 查看期末评语

## ?? 技术栈

### 后端
- **Python 3.9+**
- **FastAPI** - 高性能Web框架
- **MySQL 8.0** - 数据库
- **通义千问 (Qwen)** - AI评语生成

### 前端
- **React 18** - 前端框架
- **TypeScript** - 类型安全
- **Ant Design 5** - UI组件库
- **ECharts** - 数据可视化
- **Axios** - HTTP客户端

## ? 快速开始

### 环境要求
- Python 3.9+
- Node.js 18+
- MySQL 8.0+

### 1. 克隆项目
```bash
git clone <repository-url>
cd "AI Calligraphy"
```

### 2. 配置环境变量
创建 `.env` 文件：
```env
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_NAME=student_evaluation
DB_USER=root
DB_PASSWORD=your_password

# JWT配置
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# 通义千问API
QWEN_API_KEY=your-qwen-api-key
```

### 3. 初始化数据库
```bash
# 创建数据库
mysql -u root -p < scripts/init_database.sql
```

### 4. 安装后端依赖
```bash
pip install -r requirements.txt
```

### 5. 安装前端依赖
```bash
cd frontend
npm install
```

### 6. 启动服务

**启动后端**:
```bash
python run_web.py
```
后端运行在: http://localhost:8000

**启动前端**:
```bash
cd frontend
npm run dev
```
前端运行在: http://localhost:3000 或 http://localhost:5173

### 7. 访问系统
- **管理后台**: http://localhost:3000
- **API文档**: http://localhost:8000/docs
- **默认管理员**: 用户名 `admin`，密码 `admin123`

## ? 项目结构

```
AI Calligraphy/
├── frontend/                 # 前端项目
│   ├── src/
│   │   ├── components/       # 公共组件
│   │   ├── pages/           # 页面组件
│   │   │   ├── Admin/       # 管理员页面
│   │   │   ├── Teacher/     # 教师页面
│   │   │   └── Student/     # 学生页面
│   │   ├── stores/          # 状态管理
│   │   ├── services/        # API服务
│   │   └── App.tsx          # 应用入口
│   └── package.json
├── src/
│   ├── api/                  # API客户端
│   │   └── comment_generator.py  # AI评语生成器
│   └── web/                  # Web服务
│       ├── admin/           # 管理员路由
│       ├── teacher/         # 教师路由
│       ├── student/         # 学生路由
│       └── auth/            # 认证模块
├── scripts/                  # 脚本文件
├── run_web.py               # 后端启动入口
├── requirements.txt         # Python依赖
└── README.md
```

## ? 数据库表结构

| 表名 | 说明 |
|------|------|
| users | 用户账号表 |
| students | 学生信息表 |
| teachers | 教师信息表 |
| grades | 年级表 |
| classes | 班级表 |
| semesters | 学期表 |
| indicator_categories | 指标分类表 |
| indicators | 评价指标表 |
| evaluations | 评价数据表 |
| student_comments | 学生评语表 |

## ? API接口

### 认证
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/logout` - 用户登出

### 管理员
- `GET/POST/PUT/DELETE /api/admin/semesters` - 学期管理
- `GET/POST/PUT/DELETE /api/admin/classes` - 班级管理
- `GET/POST/PUT/DELETE /api/admin/students` - 学生管理
- `GET/POST/PUT/DELETE /api/admin/teachers` - 教师管理
- `GET/POST/PUT/DELETE /api/admin/indicators` - 指标管理
- `GET /api/admin/statistics` - 统计报表

### 教师
- `GET /api/teacher/my-classes` - 获取负责班级
- `POST /api/teacher/evaluations/batch` - 批量录入评价
- `POST /api/teacher/comments/generate` - 生成AI评语
- `POST /api/teacher/comments/batch-generate` - 批量生成评语
- `GET /api/teacher/excel/template` - 下载Excel模板
- `POST /api/teacher/excel/import` - 导入Excel数据

### 学生
- `GET /api/student/query` - 查询评价信息

## ? 更新日志

### v1.0.0 (2026-01-17)
- ? 完成用户认证系统
- ? 完成学期/班级/学生/教师管理
- ? 完成评价指标配置
- ? 完成教师数据录入功能
- ? 完成AI评语生成功能
- ? 完成Excel导入导出功能
- ? 完成统计报表（ECharts图表）
- ? 完成学生查询功能

## ? 贡献

欢迎提交Issue和Pull Request！

## ? 许可证

MIT License

---

**开发团队**: AI Calligraphy Team  
**联系方式**: support@example.com
