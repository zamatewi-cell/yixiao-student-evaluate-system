---
description: 创建新的前端页面的标准流程
---

# 添加前端页面 Skill

本文档描述如何为本项目添加一个新的前端页面。

## 步骤概览

1. 创建页面组件文件
2. 添加路由配置
3. 添加菜单入口
4. 实现页面功能

## 详细步骤

### 1. 创建页面组件

在 `frontend/src/pages/` 下适当位置创建：

```
frontend/src/pages/
├── Admin/           # 管理员页面
├── Teacher/         # 教师页面
├── Exam/            # 考试相关
├── Attendance/      # 考勤相关
├── WrongAnswer/     # 错题分析
├── DataScreen/      # 数据大屏
└── YourModule/      # 新模块
    └── YourPage.tsx
```

### 2. 页面组件模板

```tsx
import React, { useState, useEffect, useCallback } from 'react'
import {
    Card, Table, Button, Space, message, Modal, Form, Input,
    Select, Tag, Popconfirm, Row, Col
} from 'antd'
import {
    PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined
} from '@ant-design/icons'
import axios from 'axios'

const { Option } = Select

interface YourDataType {
    id: number
    name: string
    status: string
    created_at: string
}

const YourPage: React.FC = () => {
    const [loading, setLoading] = useState(false)
    const [data, setData] = useState<YourDataType[]>([])
    const [modalVisible, setModalVisible] = useState(false)
    const [editingItem, setEditingItem] = useState<YourDataType | null>(null)
    const [form] = Form.useForm()

    // 获取数据
    const fetchData = useCallback(async () => {
        setLoading(true)
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/your-module/list', {
                headers: { Authorization: `Bearer ${token}` }
            })
            setData(response.data.data || [])
        } catch (error) {
            message.error('获取数据失败')
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchData()
    }, [fetchData])

    // 提交表单
    const handleSubmit = async () => {
        try {
            const values = await form.validateFields()
            const token = localStorage.getItem('token')

            if (editingItem) {
                await axios.put(`/api/your-module/${editingItem.id}`, values, {
                    headers: { Authorization: `Bearer ${token}` }
                })
                message.success('更新成功')
            } else {
                await axios.post('/api/your-module/create', values, {
                    headers: { Authorization: `Bearer ${token}` }
                })
                message.success('创建成功')
            }

            setModalVisible(false)
            setEditingItem(null)
            form.resetFields()
            fetchData()
        } catch (error: any) {
            message.error('操作失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    // 删除
    const handleDelete = async (id: number) => {
        try {
            const token = localStorage.getItem('token')
            await axios.delete(`/api/your-module/${id}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            message.success('删除成功')
            fetchData()
        } catch (error) {
            message.error('删除失败')
        }
    }

    // 表格列定义
    const columns = [
        {
            title: 'ID',
            dataIndex: 'id',
            key: 'id',
            width: 80
        },
        {
            title: '名称',
            dataIndex: 'name',
            key: 'name'
        },
        {
            title: '状态',
            dataIndex: 'status',
            key: 'status',
            render: (status: string) => (
                <Tag color={status === 'active' ? 'green' : 'default'}>
                    {status === 'active' ? '启用' : '禁用'}
                </Tag>
            )
        },
        {
            title: '创建时间',
            dataIndex: 'created_at',
            key: 'created_at',
            width: 180
        },
        {
            title: '操作',
            key: 'action',
            width: 150,
            render: (_: any, record: YourDataType) => (
                <Space>
                    <Button 
                        size="small" 
                        icon={<EditOutlined />}
                        onClick={() => {
                            setEditingItem(record)
                            form.setFieldsValue(record)
                            setModalVisible(true)
                        }}
                    />
                    <Popconfirm
                        title="确定删除？"
                        onConfirm={() => handleDelete(record.id)}
                    >
                        <Button size="small" danger icon={<DeleteOutlined />} />
                    </Popconfirm>
                </Space>
            )
        }
    ]

    return (
        <div style={{ padding: 24 }}>
            <Card
                title="页面标题"
                extra={
                    <Space>
                        <Button icon={<ReloadOutlined />} onClick={fetchData}>
                            刷新
                        </Button>
                        <Button 
                            type="primary" 
                            icon={<PlusOutlined />}
                            onClick={() => {
                                setEditingItem(null)
                                form.resetFields()
                                setModalVisible(true)
                            }}
                        >
                            新建
                        </Button>
                    </Space>
                }
            >
                <Table
                    dataSource={data}
                    columns={columns}
                    rowKey="id"
                    loading={loading}
                    pagination={{ pageSize: 10 }}
                />
            </Card>

            {/* 编辑/新建模态框 */}
            <Modal
                title={editingItem ? '编辑' : '新建'}
                open={modalVisible}
                onOk={handleSubmit}
                onCancel={() => {
                    setModalVisible(false)
                    setEditingItem(null)
                    form.resetFields()
                }}
                okText="保存"
                cancelText="取消"
            >
                <Form form={form} layout="vertical">
                    <Form.Item
                        name="name"
                        label="名称"
                        rules={[{ required: true, message: '请输入名称' }]}
                    >
                        <Input placeholder="输入名称" />
                    </Form.Item>
                    <Form.Item name="status" label="状态" initialValue="active">
                        <Select>
                            <Option value="active">启用</Option>
                            <Option value="inactive">禁用</Option>
                        </Select>
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    )
}

export default YourPage
```

### 3. 添加路由

在 `frontend/src/App.tsx` 中添加：

```tsx
// 导入
import YourPage from './pages/YourModule/YourPage'

// 在 Routes 中添加（根据权限放在对应位置）
// 管理员功能
{user?.role === 'admin' && (
  <>
    ...
    <Route path="/your-page" element={<YourPage />} />
  </>
)}

// 或教师功能
{(user?.role === 'teacher' || user?.role === 'admin') && (
  <>
    ...
    <Route path="/your-page" element={<YourPage />} />
  </>
)}
```

### 4. 添加菜单

在 `frontend/src/components/Layout/AdminLayout.tsx` 的 `getMenuItems` 函数中添加：

```tsx
// 在合适的位置添加菜单项
{
  key: '/your-page',
  icon: <YourIcon />,
  label: '页面名称',
},

// 或作为子菜单
{
  key: 'your-group',
  icon: <FolderOutlined />,
  label: '功能组',
  children: [
    {
      key: '/your-page',
      icon: <YourIcon />,
      label: '页面名称',
    },
  ]
},
```

## 常用Ant Design组件

| 组件 | 用途 |
|------|------|
| Card | 页面容器 |
| Table | 数据表格 |
| Form | 表单 |
| Modal | 模态框 |
| Button | 按钮 |
| Tag | 标签 |
| Space | 间距 |
| Select | 下拉选择 |
| Input | 输入框 |
| message | 消息提示 |
| Popconfirm | 确认弹窗 |

## 常用图标

```tsx
import {
    PlusOutlined,      // 新建
    EditOutlined,      // 编辑
    DeleteOutlined,    // 删除
    ReloadOutlined,    // 刷新
    SearchOutlined,    // 搜索
    SettingOutlined,   // 设置
    UserOutlined,      // 用户
    TeamOutlined,      // 团队
    BarChartOutlined,  // 图表
    CalendarOutlined,  // 日历
    FileOutlined,      // 文件
} from '@ant-design/icons'
```

## 注意事项

1. 所有API调用需要带上 `Authorization` header
2. 获取token: `localStorage.getItem('token')`
3. 错误处理使用 `message.error()`
4. 表格数据使用 `rowKey="id"`
5. 日期字符串后端返回时已格式化，无需前端处理
