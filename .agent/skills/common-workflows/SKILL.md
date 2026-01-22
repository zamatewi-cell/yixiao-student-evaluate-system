---
description: 常用开发工作流和快捷操作
---

# 常用工作流 Skill

本文档汇总常用的开发工作流和快捷操作。

## 快速开发工作流

### 添加完整CRUD功能

// turbo-all

1. 确定模块名称和数据结构
2. 创建数据库迁移脚本 `migrations/vX.X_module_name.sql`
3. 创建后端模块 `src/web/module_name/`
4. 在 `app.py` 注册路由
5. 创建前端页面 `frontend/src/pages/ModuleName/Page.tsx`
6. 在 `App.tsx` 添加路由
7. 在 `AdminLayout.tsx` 添加菜单
8. 更新 `CHANGELOG.md`
9. 更新 `README.md`

### 修复Bug工作流

1. 复现问题，记录错误信息
2. 定位问题代码
3. 修复代码
4. 测试验证
5. 记录修复内容到 CHANGELOG

### 更新文档工作流

1. 更新 `README.md` - 功能说明
2. 更新 `CHANGELOG.md` - 版本记录
3. 更新 `.agent/implementation_plan_v2.md` - 进度跟踪
4. 更新 `快速启动测试指南.md` - 测试项

## 常用代码片段

### 后端 - 分页查询

```python
@router.get("/list")
async def get_list(
    page: int = 1,
    page_size: int = 10,
    search: Optional[str] = None,
    current_user: CurrentUser = Depends(require_teacher)
):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 构建查询
    sql = "SELECT * FROM your_table WHERE 1=1"
    count_sql = "SELECT COUNT(*) as total FROM your_table WHERE 1=1"
    params = []
    
    if search:
        sql += " AND name LIKE %s"
        count_sql += " AND name LIKE %s"
        params.append(f"%{search}%")
    
    # 总数
    cursor.execute(count_sql, tuple(params))
    total = cursor.fetchone()['total']
    
    # 分页
    sql += " ORDER BY id DESC LIMIT %s OFFSET %s"
    params.extend([page_size, (page - 1) * page_size])
    
    cursor.execute(sql, tuple(params))
    data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return {
        "data": data,
        "total": total,
        "page": page,
        "page_size": page_size
    }
```

### 后端 - 批量操作

```python
@router.post("/batch-update")
async def batch_update(
    ids: List[int],
    status: str,
    current_user: CurrentUser = Depends(require_admin)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholders = ','.join(['%s'] * len(ids))
    cursor.execute(f"""
        UPDATE your_table 
        SET status = %s 
        WHERE id IN ({placeholders})
    """, [status] + ids)
    
    affected = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"message": f"更新了{affected}条记录"}
```

### 前端 - 搜索筛选

```tsx
const [search, setSearch] = useState('')
const [status, setStatus] = useState<string | undefined>()

const filteredData = useMemo(() => {
    return data.filter(item => {
        if (search && !item.name.includes(search)) return false
        if (status && item.status !== status) return false
        return true
    })
}, [data, search, status])

// JSX
<Input.Search
    placeholder="搜索名称"
    onSearch={setSearch}
    style={{ width: 200 }}
/>
<Select
    placeholder="状态"
    value={status}
    onChange={setStatus}
    allowClear
    style={{ width: 120 }}
>
    <Option value="active">启用</Option>
    <Option value="inactive">禁用</Option>
</Select>
```

### 前端 - 导出功能

```tsx
const handleExport = async () => {
    try {
        const token = localStorage.getItem('token')
        const response = await axios.get('/api/xxx/export', {
            headers: { Authorization: `Bearer ${token}` },
            responseType: 'blob'
        })
        
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `export_${Date.now()}.csv`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        
        message.success('导出成功')
    } catch (error) {
        message.error('导出失败')
    }
}
```

## 版本发布检查清单

- [ ] 所有功能测试通过
- [ ] 代码无lint错误
- [ ] 数据库迁移已提交
- [ ] CHANGELOG已更新
- [ ] README已更新
- [ ] 版本号已更新（app.py中的version）

## 紧急回滚

```bash
# 数据库回滚（如有回滚脚本）
mysql -u root -p calligraphy_ai < migrations/vX.X_rollback.sql

# 代码回滚
git checkout HEAD~1 -- file.py
```

## 代码风格自动修复

```bash
# Python格式化
pip install black
black src/

# TypeScript格式化
cd frontend
npm run lint:fix
```
