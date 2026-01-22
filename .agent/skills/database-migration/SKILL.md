---
description: 数据库迁移和表设计的标准流程
---

# 数据库迁移 Skill

本文档描述如何创建数据库迁移脚本和设计数据表。

## 迁移文件命名规范

```
migrations/
├── v2_feature_expansion.sql      # V2.0功能扩展
├── v2.1_wrong_answer.sql         # V2.1错题分析
├── v2.2_system_enhance.sql       # V2.2系统增强
└── vX.X_module_name.sql          # 新迁移
```

命名格式: `vX.X_功能描述.sql`

## 迁移脚本模板

```sql
-- ============================================
-- 学生综合素质评价系统 - 功能描述
-- 日期：YYYY-MM-DD
-- 版本：X.X
-- ============================================

-- 创建新表
CREATE TABLE IF NOT EXISTS your_table (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL COMMENT '名称',
    status ENUM('active', 'inactive') DEFAULT 'active' COMMENT '状态',
    description TEXT COMMENT '描述',
    sort_order INT DEFAULT 0 COMMENT '排序',
    created_by INT COMMENT '创建人',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 外键
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    
    -- 索引
    INDEX idx_status (status),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='表描述';

-- 插入初始数据（可选）
INSERT INTO your_table (name, status) VALUES
    ('默认数据1', 'active'),
    ('默认数据2', 'active');

-- 完成提示
SELECT '迁移完成!' AS message;
```

## 常用数据类型

| 类型 | 用途 | 示例 |
|------|------|------|
| INT | 整数、ID、计数 | `id INT PRIMARY KEY AUTO_INCREMENT` |
| VARCHAR(n) | 短文本 | `name VARCHAR(100)` |
| TEXT | 长文本 | `content TEXT` |
| DECIMAL(m,n) | 精确数值 | `score DECIMAL(5,2)` |
| BOOLEAN | 布尔值 | `is_active BOOLEAN DEFAULT TRUE` |
| DATE | 日期 | `birth_date DATE` |
| DATETIME | 日期时间 | `login_time DATETIME` |
| TIMESTAMP | 时间戳 | `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |
| ENUM | 枚举 | `status ENUM('active', 'inactive')` |
| JSON | JSON数据 | `extra_data JSON` |

## 安全添加列（避免重复添加错误）

MySQL不支持 `ADD COLUMN IF NOT EXISTS`，使用存储过程：

```sql
DELIMITER //
CREATE PROCEDURE add_column_if_not_exists()
BEGIN
    IF NOT EXISTS (
        SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'your_table' 
        AND COLUMN_NAME = 'new_column'
    ) THEN
        ALTER TABLE your_table ADD COLUMN new_column VARCHAR(100) COMMENT '新列';
    END IF;
END //
DELIMITER ;

CALL add_column_if_not_exists();
DROP PROCEDURE IF EXISTS add_column_if_not_exists;
```

## 外键约束

```sql
-- 级联删除
FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE

-- 设为NULL
FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL

-- 限制删除
FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE RESTRICT
```

## 索引设计

```sql
-- 单列索引
INDEX idx_name (name)

-- 复合索引
INDEX idx_class_date (class_id, date)

-- 唯一索引
UNIQUE KEY unique_student_exam (student_id, exam_id)

-- 全文索引
FULLTEXT INDEX ft_content (content)
```

## 执行迁移

```bash
# Windows PowerShell
mysql -u root -p calligraphy_ai < migrations/vX.X_module_name.sql

# 或者登录MySQL后执行
mysql -u root -p
USE calligraphy_ai;
SOURCE migrations/vX.X_module_name.sql;
```

## 回滚脚本（可选）

建议为复杂迁移创建回滚脚本：

```sql
-- migrations/vX.X_module_name_rollback.sql
DROP TABLE IF EXISTS your_table;
ALTER TABLE other_table DROP COLUMN new_column;
```

## 数据库设计原则

1. **命名规范**
   - 表名：小写下划线，复数形式 (students, exam_scores)
   - 列名：小写下划线 (student_id, created_at)
   
2. **必备字段**
   - `id` - 主键
   - `created_at` - 创建时间
   - `updated_at` - 更新时间（可选）

3. **外键命名**
   - `表名单数_id` (student_id, class_id)

4. **索引优化**
   - 为常用查询条件添加索引
   - 外键列自动有索引
   - 避免过多索引影响写入性能
