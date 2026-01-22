# 学生综合素质评价系统 - 功能扩展实施计划

## 📋 需求概览

### 一、学期与学年管理
1. **学期数据同步**：每学期开始时，系统自动同步或手动触发数据初始化
2. **学年升级**：新学年开始，学生自动升级到下一年级
3. **毕业处理**：六年级学生毕业后标记为已毕业状态
4. **学生转班**：支持学生在班级之间转移

### 二、成绩管理模块（新增）
1. **考试管理**：创建考试、设置科目、分数线
2. **成绩录入**：教师录入学生分数
3. **成绩统计**：
   - 学生总分计算
   - 班级排名、年级排名
   - 单科班级排名、年级排名
   - 班级优秀率、合格率
   - 年级优秀率、合格率
4. **试卷分析**：教师撰写试卷分析报告
5. **AI错题分析**：扫描试卷后自动分析错题和知识点掌握情况

### 三、考勤管理模块（新增）
1. **考勤记录**：记录学生出勤情况
2. **请假类型**：区分病假、事假及具体原因
3. **考勤统计**：班级、年级考勤汇总

### 四、数据大屏展示（新增）
1. **班级数据看板**：学生人数、成绩分布、考勤情况
2. **年级数据看板**：年级整体情况对比
3. **考勤数据展示**：各班考勤实时数据

### 五、角色权限细化
1. **班主任权限**：
   - 录入本班学生信息
   - 查看本班所有数据
   - 管理本班考勤
2. **科任教师权限**：
   - 录入任教科目成绩
   - 撰写试卷分析
   - 查看相关数据

### 六、数据导入导出
1. **学生导入导出**：Excel格式
2. **教师导入导出**：Excel格式
3. **成绩导入导出**：Excel格式

### 七、系统设置
1. **数据库备份**：手动/自动备份
2. **系统参数配置**：科目设置、分数线设置等

---

## 🗄️ 数据库设计

### 1. 考试表 (exams)
```sql
CREATE TABLE exams (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL COMMENT '考试名称',
    exam_type ENUM('unit', 'midterm', 'final', 'other') DEFAULT 'unit' COMMENT '考试类型',
    semester_id INT NOT NULL COMMENT '学期ID',
    grade_id INT COMMENT '年级ID（可选，不填则全校）',
    exam_date DATE COMMENT '考试日期',
    status ENUM('draft', 'active', 'completed') DEFAULT 'draft' COMMENT '状态',
    created_by INT COMMENT '创建人',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (semester_id) REFERENCES semesters(id),
    FOREIGN KEY (grade_id) REFERENCES grades(id)
);
```

### 2. 考试科目表 (exam_subjects)
```sql
CREATE TABLE exam_subjects (
    id INT PRIMARY KEY AUTO_INCREMENT,
    exam_id INT NOT NULL COMMENT '考试ID',
    subject_name VARCHAR(50) NOT NULL COMMENT '科目名称',
    full_score DECIMAL(5,1) DEFAULT 100 COMMENT '满分',
    pass_score DECIMAL(5,1) DEFAULT 60 COMMENT '及格分',
    excellent_score DECIMAL(5,1) DEFAULT 85 COMMENT '优秀分',
    sort_order INT DEFAULT 0 COMMENT '排序',
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
);
```

### 3. 学生成绩表 (exam_scores)
```sql
CREATE TABLE exam_scores (
    id INT PRIMARY KEY AUTO_INCREMENT,
    exam_id INT NOT NULL COMMENT '考试ID',
    subject_id INT NOT NULL COMMENT '科目ID',
    student_id INT NOT NULL COMMENT '学生ID',
    score DECIMAL(5,1) COMMENT '分数',
    class_rank INT COMMENT '班级排名',
    grade_rank INT COMMENT '年级排名',
    recorded_by INT COMMENT '录入人',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_exam_subject_student (exam_id, subject_id, student_id),
    FOREIGN KEY (exam_id) REFERENCES exams(id),
    FOREIGN KEY (subject_id) REFERENCES exam_subjects(id),
    FOREIGN KEY (student_id) REFERENCES students(id)
);
```

### 4. 学生总分表 (exam_totals)
```sql
CREATE TABLE exam_totals (
    id INT PRIMARY KEY AUTO_INCREMENT,
    exam_id INT NOT NULL COMMENT '考试ID',
    student_id INT NOT NULL COMMENT '学生ID',
    total_score DECIMAL(6,1) COMMENT '总分',
    class_rank INT COMMENT '班级排名',
    grade_rank INT COMMENT '年级排名',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_exam_student (exam_id, student_id),
    FOREIGN KEY (exam_id) REFERENCES exams(id),
    FOREIGN KEY (student_id) REFERENCES students(id)
);
```

### 5. 试卷分析表 (exam_analysis)
```sql
CREATE TABLE exam_analysis (
    id INT PRIMARY KEY AUTO_INCREMENT,
    exam_id INT NOT NULL COMMENT '考试ID',
    subject_id INT NOT NULL COMMENT '科目ID',
    class_id INT COMMENT '班级ID（可选）',
    teacher_id INT COMMENT '教师ID',
    analysis_content TEXT COMMENT '分析内容',
    avg_score DECIMAL(5,1) COMMENT '平均分',
    max_score DECIMAL(5,1) COMMENT '最高分',
    min_score DECIMAL(5,1) COMMENT '最低分',
    pass_rate DECIMAL(5,2) COMMENT '及格率',
    excellent_rate DECIMAL(5,2) COMMENT '优秀率',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (exam_id) REFERENCES exams(id),
    FOREIGN KEY (subject_id) REFERENCES exam_subjects(id),
    FOREIGN KEY (class_id) REFERENCES classes(id)
);
```

### 6. 考勤表 (attendance)
```sql
CREATE TABLE attendance (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL COMMENT '学生ID',
    date DATE NOT NULL COMMENT '日期',
    status ENUM('present', 'absent', 'late', 'leave_early', 'sick_leave', 'personal_leave') NOT NULL COMMENT '状态',
    leave_type ENUM('sick', 'personal', 'other') COMMENT '请假类型',
    reason VARCHAR(500) COMMENT '原因说明',
    recorded_by INT COMMENT '记录人',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_student_date (student_id, date),
    FOREIGN KEY (student_id) REFERENCES students(id)
);
```

### 7. 教师任课表 (teacher_subjects)
```sql
CREATE TABLE teacher_subjects (
    id INT PRIMARY KEY AUTO_INCREMENT,
    teacher_id INT NOT NULL COMMENT '教师ID',
    class_id INT NOT NULL COMMENT '班级ID',
    subject_name VARCHAR(50) NOT NULL COMMENT '任教科目',
    semester_id INT NOT NULL COMMENT '学期ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_teacher_class_subject (teacher_id, class_id, subject_name, semester_id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(id),
    FOREIGN KEY (class_id) REFERENCES classes(id),
    FOREIGN KEY (semester_id) REFERENCES semesters(id)
);
```

### 8. 学生变更记录表 (student_transfers)
```sql
CREATE TABLE student_transfers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL COMMENT '学生ID',
    from_class_id INT COMMENT '原班级ID',
    to_class_id INT NOT NULL COMMENT '目标班级ID',
    transfer_date DATE NOT NULL COMMENT '转班日期',
    reason VARCHAR(500) COMMENT '转班原因',
    operated_by INT COMMENT '操作人',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (from_class_id) REFERENCES classes(id),
    FOREIGN KEY (to_class_id) REFERENCES classes(id)
);
```

---

## 📅 实施阶段

### 第一阶段：基础数据管理（优先级：高）✅ 已完成
- [x] 1.1 学生转班功能 - `POST /api/admin/students/transfer`
- [x] 1.2 学年升级功能 - `POST /api/admin/students/grade-upgrade`
- [x] 1.3 毕业处理功能 - 集成在学年升级中
- [x] 1.4 角色权限细化（班主任/科任教师）- `src/web/teacher_role/routes.py`

### 第二阶段：成绩管理模块（优先级：高）✅ 已完成
- [x] 2.1 考试管理CRUD - `src/web/exam/routes.py`
- [x] 2.2 成绩录入界面 - `frontend/src/pages/Exam/ScoreEntry.tsx`
- [x] 2.3 成绩统计与排名计算 - `POST /api/exam/calculate-ranks/{exam_id}`
- [x] 2.4 试卷分析功能 - `POST /api/exam/analysis`

### 第三阶段：考勤管理模块（优先级：中）✅ 已完成
- [x] 3.1 考勤记录界面 - `frontend/src/pages/Attendance/AttendanceManagement.tsx`
- [x] 3.2 请假管理 - 支持病假/事假/其他
- [x] 3.3 考勤统计报表 - `/api/attendance/statistics/*`

### 第四阶段：数据大屏（优先级：中）✅ 已完成
- [x] 4.1 班级数据看板
- [x] 4.2 年级数据看板
- [x] 4.3 考勤数据展示 - `frontend/src/pages/DataScreen/DataScreen.tsx`

### 第五阶段：导入导出与备份（优先级：中）✅ 已完成
- [x] 5.1 学生导入导出 - `/api/import-export/students/export`, `/import`
- [x] 5.2 教师导入导出 - `/api/import-export/teachers/export`
- [x] 5.3 成绩导入导出 - `/api/import-export/scores/export/{exam_id}`, `/import/{exam_id}`
- [x] 5.4 数据库备份功能 - `/api/admin/system/backup`

### 第六阶段：高级功能（优先级：低）✅ 已完成
- [x] 6.1 AI试卷分析 - `/api/ai-analysis/generate`
- [x] 6.2 错题知识点分析 - `/api/wrong-answer/analyze`

---

## 📁 新增文件清单

### 后端 API 文件
| 文件路径 | 说明 |
|----------|------|
| `src/web/exam/routes.py` | 考试与成绩管理 |
| `src/web/exam/__init__.py` | 模块初始化 |
| `src/web/attendance/routes.py` | 考勤管理 |
| `src/web/attendance/__init__.py` | 模块初始化 |
| `src/web/import_export/routes.py` | 数据导入导出 |
| `src/web/import_export/__init__.py` | 模块初始化 |
| `src/web/ai_analysis/routes.py` | AI试卷分析 |
| `src/web/ai_analysis/__init__.py` | 模块初始化 |
| `src/web/teacher_role/routes.py` | 教师角色权限 |
| `src/web/teacher_role/__init__.py` | 模块初始化 |
| `src/web/wrong_answer/routes.py` | 错题分析 |
| `src/web/wrong_answer/__init__.py` | 模块初始化 |

### 前端页面文件
| 文件路径 | 说明 |
|----------|------|
| `frontend/src/pages/DataScreen/DataScreen.tsx` | 数据大屏 |
| `frontend/src/pages/Attendance/AttendanceManagement.tsx` | 考勤管理 |
| `frontend/src/pages/Exam/ExamManagement.tsx` | 考试管理 |
| `frontend/src/pages/Exam/ScoreEntry.tsx` | 成绩录入 |
| `frontend/src/pages/Admin/TeacherRoleManagement.tsx` | 教师权限管理 |
| `frontend/src/pages/WrongAnswer/WrongAnswerAnalysis.tsx` | 错题分析 |

### 数据库迁移文件
| 文件路径 | 说明 |
|----------|------|
| `migrations/v2_feature_expansion.sql` | V2.0所有新表 |
| `migrations/v2.1_wrong_answer.sql` | 错题分析功能表 |

---

## 🎯 完成状态

- **总进度**: 100% ✅
- **核心功能**: 100% 完成
- **V2.1新增**: 教师权限管理、错题分析

---

*最后更新: 2026-01-22*


