# 更新日志 (CHANGELOG)

## [2.2.0] - 2026-01-22

### ✨ 新功能

#### 系统配置中心（新增模块）
- **统一配置**：学校信息、考试设置、考勤设置、AI配置集中管理
- **分类管理**：按类别组织配置项（basic/exam/attendance/ai/system）
- **默认初始化**：一键初始化默认配置

#### 审计日志（新增模块）
- **操作记录**：记录登录、创建、更新、删除、导入导出等操作
- **多条件筛选**：按用户、操作类型、模块、日期筛选
- **活动统计**：统计近7天操作趋势、活跃用户排行
- **日志清理**：定期清理90天前的旧日志

#### 通知公告（新增模块）
- **发布通知**：支持一般/考试/考勤/活动/紧急多种类型
- **目标受众**：可选择发布给全部用户、教师或学生
- **置顶功能**：重要通知可置顶显示
- **阅读统计**：记录通知阅读次数

#### 成绩单生成（新增模块）
- **HTML报告**：生成可打印的学生成绩报告单
- **成绩汇总**：包含各科成绩、班级排名、年级排名
- **教师评语**：自动填充AI生成的评语
- **签名区域**：预留班主任、学校、家长签名位置

#### 系统健康监控（新增模块）
- **基础状态**：数据库连接、系统版本检查
- **详细统计**：用户数、学生数、今日登录等
- **服务器资源**：CPU、内存、磁盘使用率监控
- **仪表盘摘要**：性别分布、年级分布、登录趋势

### 🔧 后端 API 新增

| API | 方法 | 功能 |
|-----|------|------|
| `/api/system-config/list` | GET | 获取配置列表 |
| `/api/system-config/update` | PUT | 批量更新配置 |
| `/api/audit-log/list` | GET | 获取审计日志 |
| `/api/audit-log/statistics` | GET | 日志统计 |
| `/api/audit-log/cleanup` | DELETE | 清理旧日志 |
| `/api/notice/create` | POST | 发布通知 |
| `/api/notice/list` | GET | 通知列表 |
| `/api/notice/public` | GET | 公开通知 |
| `/api/report/student-report/{id}` | GET | 学生成绩单 |
| `/api/report/class-report/{id}` | GET | 班级成绩汇总 |
| `/api/health/status` | GET | 系统状态 |
| `/api/health/detailed` | GET | 详细状态 |
| `/api/health/dashboard-summary` | GET | 仪表盘数据 |

### 📁 新增文件

**后端模块**
- `src/web/system_config/routes.py` - 系统配置API
- `src/web/audit_log/routes.py` - 审计日志API
- `src/web/notice/routes.py` - 通知公告API
- `src/web/report/routes.py` - 报告生成API
- `src/web/health/routes.py` - 健康监控API

**前端页面**
- `frontend/src/pages/Admin/SystemSettings.tsx` - 系统设置页面
- `frontend/src/pages/Admin/NoticeManagement.tsx` - 通知管理页面
- `frontend/src/pages/Admin/AuditLogViewer.tsx` - 审计日志页面

**数据库迁移**
- `migrations/v2.2_system_enhance.sql` - V2.2数据库表

### 🗄️ 数据库变更

新增表：
- `system_configs` - 系统配置表
- `audit_logs` - 审计日志表
- `notices` - 通知公告表
- `notice_reads` - 通知阅读记录表

---

## [2.1.0] - 2026-01-22

### ✨ 新功能

#### 教师权限管理（新增模块）
- **角色区分**：支持班主任和科任教师两种角色
- **权限细化**：班主任可管理考勤、评语；科任教师仅限成绩录入
- **任课分配**：管理员可为教师分配班级和科目

#### 错题分析（新增模块）
- **错题记录**：记录学生错题、知识点、错误类型
- **班级统计**：统计班级错题分布、知识点薄弱项
- **AI分析**：智能分析错题规律和学习建议

### 🔧 后端 API 新增

| API | 方法 | 功能 |
|-----|------|------|
| `/api/teacher-role/my-role` | GET | 获取教师角色 |
| `/api/teacher-role/update/{id}` | PUT | 更新角色 |
| `/api/teacher-role/assign-subject` | POST | 分配任课 |
| `/api/wrong-answer/record` | POST | 记录错题 |
| `/api/wrong-answer/class/{id}` | GET | 班级错题统计 |
| `/api/wrong-answer/analyze` | POST | AI分析 |

### 📁 新增文件

- `src/web/teacher_role/routes.py` - 教师角色API
- `src/web/wrong_answer/routes.py` - 错题分析API
- `frontend/src/pages/Admin/TeacherRoleManagement.tsx` - 权限管理页面
- `frontend/src/pages/WrongAnswer/WrongAnswerAnalysis.tsx` - 错题分析页面
- `migrations/v2.1_wrong_answer.sql` - V2.1数据库迁移

---

## [2.0.0] - 2026-01-22

### ✨ 重大功能更新

#### 考试与成绩管理（新增模块）
- **考试管理**：支持创建单元测试、期中、期末等各类考试
- **科目管理**：每个考试可配置多个科目，设置满分、及格分、优秀分
- **成绩录入**：教师可录入学生各科目成绩
- **排名计算**：自动计算班级排名和年级排名
- **成绩统计**：计算平均分、最高分、最低分、及格率、优秀率
- **试卷分析**：教师可撰写试卷分析报告

#### 考勤管理（新增模块）
- **考勤记录**：支持记录出勤、缺勤、迟到、早退、病假、事假
- **批量录入**：支持按班级批量录入考勤
- **请假管理**：区分病假和事假，记录请假原因
- **考勤统计**：班级、年级、全校多维度统计

#### 数据大屏展示（新增模块）
- **全校概览**：学生总数、今日出勤、请假人数、全校出勤率
- **年级看板**：各年级出勤率圆环图展示
- **班级详情**：点击年级查看各班考勤详情
- **实时刷新**：每5分钟自动刷新数据
- **深色主题**：专业的大屏展示样式

#### 学生管理增强
- **学生转班**：支持学生在班级间转移，记录转班历史
- **学年升级**：一键操作全校学年升级
- **毕业处理**：六年级学生自动标记毕业状态
- **变更记录**：完整记录学生转班、升级、毕业历史

#### 系统管理增强
- **数据库备份**：支持手动创建数据库备份
- **备份记录**：查看历史备份记录

#### 数据导入导出（新增模块）
- **学生导入导出**：CSV格式，支持批量导入学生信息
- **教师导入导出**：CSV格式，导出教师列表
- **成绩导入导出**：CSV格式，按考试导入导出成绩
- **下载模板**：提供标准导入模板，避免格式错误

#### AI试卷分析（新增模块）
- **智能分析**：调用通义千问大模型分析考试成绩
- **自动报告**：生成包含成绩分布、问题诊断、教学建议的报告
- **本地备选**：API不可用时使用本地算法生成分析
- **历史记录**：保存分析结果便于查阅

### 🔧 后端 API 新增

| 模块 | API | 方法 | 说明 |
|------|-----|------|------|
| 考试 | `/api/exam/list` | GET | 获取考试列表 |
| 考试 | `/api/exam/create` | POST | 创建考试 |
| 考试 | `/api/exam/{id}` | GET/PUT/DELETE | 考试CRUD |
| 成绩 | `/api/exam/scores/input` | POST | 录入成绩 |
| 成绩 | `/api/exam/scores/{exam_id}/{subject_id}` | GET | 获取成绩 |
| 成绩 | `/api/exam/calculate-ranks/{exam_id}` | POST | 计算排名 |
| 成绩 | `/api/exam/statistics/{exam_id}` | GET | 成绩统计 |
| 分析 | `/api/exam/analysis` | POST | 保存试卷分析 |
| 考勤 | `/api/attendance/record` | POST | 记录考勤 |
| 考勤 | `/api/attendance/batch` | POST | 批量考勤 |
| 考勤 | `/api/attendance/class/{id}` | GET | 班级考勤 |
| 考勤 | `/api/attendance/statistics/class/{id}` | GET | 班级统计 |
| 考勤 | `/api/attendance/statistics/grade/{id}` | GET | 年级统计 |
| 考勤 | `/api/attendance/dashboard` | GET | 大屏数据 |
| 学生 | `/api/admin/students/transfer` | POST | 学生转班 |
| 学生 | `/api/admin/students/grade-upgrade` | POST | 学年升级 |
| 系统 | `/api/admin/system/backup` | POST | 创建备份 |
| 系统 | `/api/admin/system/backups` | GET | 备份列表 |
| 导入 | `/api/import-export/students/export` | GET | 导出学生 |
| 导入 | `/api/import-export/students/import` | POST | 导入学生 |
| 导入 | `/api/import-export/teachers/export` | GET | 导出教师 |
| 导入 | `/api/import-export/scores/export/{exam_id}` | GET | 导出成绩 |
| 导入 | `/api/import-export/scores/import/{exam_id}` | POST | 导入成绩 |
| 导入 | `/api/import-export/templates/students` | GET | 学生模板 |
| 导入 | `/api/import-export/templates/scores/{exam_id}` | GET | 成绩模板 |
| AI | `/api/ai-analysis/generate` | POST | AI分析生成 |
| AI | `/api/ai-analysis/history/{exam_id}/{subject_id}` | GET | 分析历史 |

### 📋 新增文件清单

| 文件 | 说明 |
|------|------|
| `src/web/exam/routes.py` | 考试与成绩管理 API |
| `src/web/exam/__init__.py` | 考试模块初始化 |
| `src/web/attendance/routes.py` | 考勤管理 API |
| `src/web/attendance/__init__.py` | 考勤模块初始化 |
| `src/web/import_export/routes.py` | 数据导入导出 API |
| `src/web/import_export/__init__.py` | 导入导出模块初始化 |
| `src/web/ai_analysis/routes.py` | AI试卷分析 API |
| `src/web/ai_analysis/__init__.py` | AI分析模块初始化 |
| `frontend/src/pages/DataScreen/DataScreen.tsx` | 数据大屏页面 |
| `frontend/src/pages/Attendance/AttendanceManagement.tsx` | 考勤管理页面 |
| `frontend/src/pages/Exam/ExamManagement.tsx` | 考试管理页面 |
| `frontend/src/pages/Exam/ScoreEntry.tsx` | 成绩录入页面 |
| `migrations/v2_feature_expansion.sql` | 数据库迁移脚本 |
| `.agent/implementation_plan_v2.md` | 功能实施计划 |

### 🗄️ 数据库变更

需要执行迁移脚本 `migrations/v2_feature_expansion.sql` 添加以下表：
- `exams` - 考试表
- `exam_subjects` - 考试科目表
- `exam_scores` - 学生成绩表
- `exam_totals` - 学生总分表
- `exam_analysis` - 试卷分析表
- `attendance` - 考勤表
- `teacher_subjects` - 教师任课表
- `student_transfers` - 学生变更记录表
- `system_backups` - 系统备份记录表

同时更新 `students` 和 `teachers` 表添加新字段。

---

## [1.4.0] - 2026-01-21

### ✨ 新增功能

#### 教师数据编辑权限控制
- **编辑权限机制**：新增 `can_edit` 字段控制教师是否可以进行数据录入和评语管理
- **管理员授权控制**：管理员可以在教师管理页面授权/取消教师的编辑权限
- **权限状态显示**：教师管理页面新增"编辑权限"列，显示"可编辑"/"只读"状态
- **教师端权限提示**：数据录入和评语管理页面显示权限状态标签和警告提示
- **权限检查 API**：教师端新增获取自身编辑权限状态的接口

#### 教师端 API 优化
- **独立学期接口**：教师端新增 `/api/teacher/semesters` 接口，无需管理员权限
- **独立指标接口**：教师端新增 `/api/teacher/indicators` 接口，无需管理员权限
- **权限检查接口**：新增 `/api/teacher/edit-permission` 接口获取编辑权限状态

#### 个人资料管理
- **个人资料页面**：新增个人资料页面，支持查看和编辑个人信息
- **头像选择**：提供多种预设头像供用户选择
- **个性签名**：支持设置个性签名
- **密码修改**：支持修改登录密码
- **教师信息显示**：教师用户可以查看任教科目、管理班级数、编辑权限等信息

### 🐛 Bug 修复
- **修复管理员权限问题**：管理员进入数据录入和评语管理页面时正确显示"已授权"状态

### 🔧 后端 API 新增

| API | 方法 | 说明 |
|-----|------|------|
| `/api/teacher/semesters` | GET | 教师获取学期列表 |
| `/api/teacher/indicators` | GET | 教师获取评价指标 |
| `/api/teacher/edit-permission` | GET | 获取教师编辑权限状态 |
| `/api/admin/teachers/{id}/grant-edit` | POST | 授权教师编辑权限 |
| `/api/admin/teachers/{id}/revoke-edit` | POST | 取消教师编辑权限 |
| `/api/auth/profile` | GET | 获取用户完整个人资料 |
| `/api/auth/profile` | PUT | 更新用户个人资料 |

### 📋 修复文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/web/teacher/routes.py` | 修改 | 添加权限检查、学期/指标 API |
| `src/web/admin/routes.py` | 修改 | 添加授权/取消编辑权限 API |
| `src/web/auth/routes.py` | 修改 | 添加个人资料获取和更新 API |
| `frontend/src/pages/Admin/Teachers.tsx` | 修改 | 添加编辑权限列和授权按钮 |
| `frontend/src/pages/Teacher/DataEntry.tsx` | 修改 | 添加权限检查和提示，修复管理员权限 |
| `frontend/src/pages/Teacher/CommentManagement.tsx` | 修改 | 添加权限检查和提示，修复管理员权限 |
| `frontend/src/pages/Profile/Profile.tsx` | 新增 | 个人资料页面组件 |
| `frontend/src/App.tsx` | 修改 | 添加个人资料路由 |
| `frontend/src/components/Layout/AdminLayout.tsx` | 修改 | 添加个人资料入口 |
| `migrations/add_teacher_can_edit.sql` | 新增 | 数据库迁移脚本 |
| `migrations/add_user_profile_fields.sql` | 新增 | 数据库迁移脚本 |

### 🗄️ 数据库变更

需要执行以下迁移脚本：
```sql
-- 添加教师编辑权限字段
ALTER TABLE teachers ADD COLUMN can_edit BOOLEAN DEFAULT FALSE;

-- 添加用户头像和签名字段
ALTER TABLE users ADD COLUMN avatar VARCHAR(500) DEFAULT NULL;
ALTER TABLE users ADD COLUMN signature VARCHAR(200) DEFAULT NULL;
```

---

## [1.3.0] - 2026-01-21

### ✨ 新增功能

#### 教师注册与授权系统
- **教师自助注册**：登录页面新增"教师注册"Tab，支持教师自行注册账号
- **待授权机制**：新注册教师默认为待授权状态，需要管理员审核
- **管理员授权功能**：教师管理页面新增授权/禁用按钮
- **授权状态显示**：教师列表显示已授权/待授权状态，待授权行高亮显示
- **待授权统计**：教师管理页面标题显示待授权人数

#### 教师专属工作台
- **个性化仪表盘**：教师登录后显示专属工作台，而非管理员仪表盘
- **智能问候语**：根据时间显示早上好/下午好/晚上好等问候
- **统计卡片**：显示我的班级、学生总数、评价录入、待办评语
- **快捷入口**：数据录入、评语管理、书法批改、作品分配
- **我的班级列表**：显示教师负责的班级及学生人数
- **工作进度图表**：本学期工作完成进度可视化
- **待办任务列表**：显示待完成的工作任务

#### 学生管理增强
- **编辑功能**：添加编辑按钮和编辑表单
- **编辑字段**：支持编辑姓名、性别、班级、出生日期、家长信息

#### 学生端查询优化
- **综合查询 API**：新增 `POST /api/student/query` 端点
- **一次性获取数据**：评价数据、雷达图、期末评语、书法成绩

#### AI 评语模块重构
- **CommentGenerator 类**：重构评语生成器为类接口
- **兼容教师路由调用**：支持传入评价数据直接生成评语

### 🔧 后端 API 新增

| API | 方法 | 说明 |
|-----|------|------|
| `/api/auth/register/teacher` | POST | 教师注册 |
| `/api/admin/teachers/{id}/authorize` | POST | 授权教师 |
| `/api/admin/teachers/{id}/disable` | POST | 禁用教师 |
| `/api/admin/teachers/{id}` | PUT | 更新教师 |
| `/api/admin/teachers/{id}` | DELETE | 删除教师 |
| `/api/student/query` | POST | 学生综合查询 |

### 📋 修复文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/web/auth/routes.py` | 修改 | 添加教师注册API |
| `src/web/admin/routes.py` | 修改 | 添加授权/禁用/更新/删除教师API |
| `src/web/student/routes.py` | 修改 | 添加学生综合查询API |
| `src/api/comment_generator.py` | 重构 | CommentGenerator类 |
| `frontend/src/pages/Login.tsx` | 修改 | 添加教师注册Tab |
| `frontend/src/pages/Admin/Teachers.tsx` | 重写 | 授权状态列和授权按钮 |
| `frontend/src/pages/Admin/Students.tsx` | 修改 | 添加编辑功能 |
| `frontend/src/pages/Teacher/TeacherDashboard.tsx` | 新增 | 教师工作台 |
| `frontend/src/App.tsx` | 修改 | 角色路由区分 |
| `frontend/src/components/Layout/AdminLayout.tsx` | 修改 | 角色菜单区分 |

---

## [1.2.1] - 2026-01-21

### 🐛 Bug 修复

#### 班级管理显示问题修复
- **修复班主任显示问题**：班级列表现在正确显示班主任姓名，而不是"未分配"
- **修复学生人数显示问题**：班级列表现在正确显示学生人数，通过子查询统计

#### 教师管理功能完善
- **修复联系方式显示/编辑**：教师的电话和邮箱现在可以正确保存和编辑
- **修复管理班级数显示**：教师列表现在正确显示每位教师担任班主任的班级数量
- **新增状态编辑功能**：教师在职/离职状态现在可以在编辑时修改	

#### 班级选择器优化
- **修复班级选择显示空数据问题**：数据录入、评语管理、作品分配页面现在可以正确显示班级
- **添加兜底机制**：教师接口返回空时，自动尝试管理员接口获取班级列表
- **年级分组显示**：班级选择器现在按年级分组显示，支持搜索功能

### 📋 修复文件清单

| 文件 | 修改内容 |
|------|----------|
| `src/web/admin/routes.py` | 修复 list_classes、list_teachers、update_teacher 接口 |
| `frontend/src/pages/Admin/Teachers.tsx` | 添加状态编辑控件 |
| `frontend/src/pages/Teacher/DataEntry.tsx` | 班级选择器分组 + 兜底逻辑 |
| `frontend/src/pages/Teacher/CommentManagement.tsx` | 班级选择器分组 + 兜底逻辑 |
| `frontend/src/pages/Calligraphy/CalligraphyAssignment.tsx` | 班级选择器分组 + 兜底逻辑 |

---

## [1.2.0] - 2026-01-21

### 🐛 Bug 修复

#### 教师班级同步修复
- **修复 my-classes API**：教师现在可以看到所有班级，而不仅仅是作为班主任管理的班级
- 班级列表增加 `is_head_teacher` 标识，区分班主任管理的班级

### ✨ 新增功能

#### 书法作品分配功能
- **新增书法作品分配页面** (`/calligraphy-assignment`)：在不使用条码的情况下，手动将书法作品分配给学生
- **每个学生只能分配一个作品**：系统会检查并防止重复分配
- **取消分配功能**：支持取消已分配的作品关联

#### 书法评语同步功能
- **单条同步**：将单个书法批改评语同步到期末评语管理
- **批量同步**：一键将班级所有已分配作品的评语同步到期末评语
- **追加模式**：评语可以追加到现有的期末评语中，自动添加【书法评价】标识

#### 新增后端 API
- `GET /api/teacher/calligraphy-records/unassigned` - 获取未分配学生的作品列表
- `POST /api/teacher/calligraphy-records/assign` - 手动分配作品给学生
- `POST /api/teacher/calligraphy-records/batch-assign` - 批量分配作品
- `DELETE /api/teacher/calligraphy-records/{id}/unassign` - 取消作品分配
- `POST /api/teacher/calligraphy-records/sync-comment` - 同步单条评语到期末评语
- `POST /api/teacher/calligraphy-records/batch-sync-comments` - 批量同步班级评语

### 📋 功能更新

| 模块 | 功能 | 状态 |
|------|------|:----:|
| 书法批改 | AI 批改 | ✅ |
| 书法批改 | 作品分配 | ✅ 新增 |
| 书法批改 | 评语同步 | ✅ 新增 |
| 数据录入 | 班级选择 | ✅ 修复 |
| 评语管理 | 班级选择 | ✅ 修复 |

---

## [1.1.0] - 2026-01-20


### 🐛 Bug 修复

#### 认证系统修复
- **修复 Token 同步问题**：登录时 token 现在会同步存储到 `localStorage`，解决了前端页面获取 token 失败的问题
- **修复 authStore**：添加 `onRehydrateStorage` 回调，确保页面刷新后 token 正确同步

#### 前后端数据模型修复
- **TeacherCreate 模型**：添加 `password`、`phone`、`email` 字段，支持前端传入
- **IndicatorCreate 模型**：添加 `weight`、`is_active`、`sort_order` 字段
- **Indicators API**：修复返回数据格式，正确处理 `Decimal` 类型转换和 JSON 解析

#### 学期选择修复
- **DataEntry.tsx**：修改为获取所有学期列表，自动选中当前学期
- **CommentManagement.tsx**：同样修复学期选择逻辑

### ✨ 新增功能

#### 后端 API
- **POST /api/admin/semesters/{id}/set-current**：设置当前学期
- **PUT /api/admin/students/{id}**：更新学生信息
- **DELETE /api/admin/students/{id}**：删除学生

#### 前端功能
- **学生管理**：添加删除按钮和确认对话框
- **API 服务层**：添加所有实体的 `update` 和 `delete` API 方法

### 📋 功能完整性确认

| 模块 | 新建 | 编辑 | 删除 | 特殊功能 |
|------|:----:|:----:|:----:|---------|
| 学期管理 | ✅ | ✅ | ✅ | 设为当前学期 |
| 班级管理 | ✅ | ✅ | ✅ | - |
| 学生管理 | ✅ | - | ✅ | 条码生成 |
| 教师管理 | ✅ | ✅ | ✅ | - |
| 评价指标 | ✅ | ✅ | ✅ | 分类管理 |

### 🔧 技术改进

- 统一了前后端的数据模型
- 优化了错误提示信息
- 改进了学期选择的用户体验

---

## [1.0.0] - 初始版本

### 功能
- 管理员后台：用户、学期、班级、学生、教师、评价指标管理
- 教师功能：数据录入、批量导入、评语管理
- 学生查询：评价数据查看
- AI 评语生成（基于千问 API）
