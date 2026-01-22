---
description: 项目测试和调试的标准流程
---

# 测试和调试 Skill

本文档描述如何测试和调试本项目。

## 启动开发环境

### 后端启动

```bash
# 在项目根目录
python run_web.py
```

后端启动后访问:
- API服务: http://localhost:8000
- Swagger文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/api/health/status

### 前端启动

```bash
cd frontend
npm run dev
```

前端启动后访问:
- 应用首页: http://localhost:3000
- 登录页: http://localhost:3000/login
- 数据大屏: http://localhost:3000/data-screen

## 测试账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |

## API测试

### 使用Swagger UI

1. 访问 http://localhost:8000/docs
2. 点击 "Authorize" 按钮
3. 先调用 `/api/auth/login` 获取token
4. 将token填入授权框
5. 测试各API接口

### 使用curl测试

```bash
# 登录获取token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 使用token调用API
curl -X GET http://localhost:8000/api/admin/students \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 常见API端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/me` | GET | 当前用户信息 |
| `/api/admin/students` | GET | 学生列表 |
| `/api/admin/teachers` | GET | 教师列表 |
| `/api/admin/classes` | GET | 班级列表 |
| `/api/teacher/semesters` | GET | 学期列表 |
| `/api/health/status` | GET | 系统状态 |

## 常见问题排查

### 后端问题

**1. 数据库连接失败**
```
错误: Can't connect to MySQL server
解决: 
- 检查MySQL服务是否启动
- 检查 src/web/app.py 中的DB_CONFIG配置
- 确认数据库calligraphy_ai存在
```

**2. 模块导入错误**
```
错误: ModuleNotFoundError
解决:
- 检查 __init__.py 是否存在
- 检查导入路径是否正确
- 确认requirements已安装
```

**3. API返回500错误**
```
检查:
- 查看终端错误日志
- 检查SQL语句是否正确
- 检查数据库表是否存在
```

### 前端问题

**1. 页面空白**
```
检查:
- 浏览器控制台错误
- 组件导入是否正确
- 路由配置是否正确
```

**2. API调用失败**
```
错误: Network Error / CORS
解决:
- 确认后端已启动
- 检查vite.config.ts代理配置
- 检查token是否有效
```

**3. 登录后跳转异常**
```
检查:
- authStore状态
- localStorage中的token
- 路由守卫逻辑
```

## 调试技巧

### Python后端调试

```python
# 打印调试
print(f"Debug: {variable}")

# 使用logging
import logging
logging.debug(f"Debug: {variable}")

# 断点调试（VS Code）
# 在代码行左侧点击添加断点
# F5启动调试
```

### React前端调试

```tsx
// 打印调试
console.log('Debug:', data)

// 使用React DevTools
// 安装浏览器扩展查看组件状态

// 网络请求
// 浏览器开发者工具 -> Network面板
```

## 代码热重载

- **后端**: uvicorn自动重载（修改代码后自动重启）
- **前端**: Vite HMR（修改代码后自动刷新）

## 数据库调试

```sql
-- 查看表结构
DESCRIBE your_table;

-- 查看最近数据
SELECT * FROM your_table ORDER BY id DESC LIMIT 10;

-- 检查外键约束
SELECT * FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
WHERE TABLE_SCHEMA = 'calligraphy_ai';
```

## 日志查看

后端日志直接输出到终端，包含:
- 请求路径
- 响应状态码
- 错误堆栈

## 性能检查

```python
# 后端性能分析
import time
start = time.time()
# ... 代码 ...
print(f"耗时: {time.time() - start:.3f}s")
```

```tsx
// 前端性能
console.time('operation')
// ... 代码 ...
console.timeEnd('operation')
```
