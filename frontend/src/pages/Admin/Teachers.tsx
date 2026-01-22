import React, { useState, useEffect } from 'react'
import {
    Card,
    Table,
    Button,
    Modal,
    Form,
    Input,
    Select,
    Space,
    message,
    Tag,
    Popconfirm,
    Typography,
    Tooltip,
    Badge
} from 'antd'
import {
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    UserOutlined,
    PhoneOutlined,
    MailOutlined,
    CheckCircleOutlined,
    StopOutlined,
    ExclamationCircleOutlined,
    UnlockOutlined,
    LockOutlined
} from '@ant-design/icons'
import axios from 'axios'

const { Title } = Typography
const { Option } = Select

interface Teacher {
    id: number
    user_id: number
    name: string
    employee_no: string
    phone: string
    email: string
    subjects: string
    status: string
    is_active: boolean
    can_edit: boolean
    class_count: number
}

const Teachers: React.FC = () => {
    const [loading, setLoading] = useState(false)
    const [teachers, setTeachers] = useState<Teacher[]>([])
    const [modalVisible, setModalVisible] = useState(false)
    const [editingTeacher, setEditingTeacher] = useState<Teacher | null>(null)
    const [form] = Form.useForm()

    // 获取教师列表
    const fetchTeachers = async () => {
        try {
            setLoading(true)
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/admin/teachers', {
                headers: { Authorization: `Bearer ${token}` }
            })
            setTeachers(response.data.data || [])
        } catch (error: any) {
            message.error('获取教师列表失败: ' + (error.response?.data?.detail || error.message))
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchTeachers()
    }, [])

    // 打开新建模态框
    const handleAdd = () => {
        setEditingTeacher(null)
        form.resetFields()
        setModalVisible(true)
    }

    // 打开编辑模态框
    const handleEdit = (record: Teacher) => {
        setEditingTeacher(record)
        form.setFieldsValue({
            name: record.name,
            employee_no: record.employee_no,
            phone: record.phone,
            email: record.email,
            subjects: record.subjects,
            status: record.status || 'active'
        })
        setModalVisible(true)
    }

    // 提交表单
    const handleSubmit = async () => {
        try {
            const values = await form.validateFields()
            const token = localStorage.getItem('token')

            if (editingTeacher) {
                await axios.put(`/api/admin/teachers/${editingTeacher.id}`, values, {
                    headers: { Authorization: `Bearer ${token}` }
                })
                message.success('教师信息更新成功')
            } else {
                await axios.post('/api/admin/teachers', values, {
                    headers: { Authorization: `Bearer ${token}` }
                })
                message.success('教师创建成功')
            }

            setModalVisible(false)
            fetchTeachers()
        } catch (error: any) {
            message.error('操作失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    // 删除教师
    const handleDelete = async (id: number) => {
        try {
            const token = localStorage.getItem('token')
            await axios.delete(`/api/admin/teachers/${id}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            message.success('教师删除成功')
            fetchTeachers()
        } catch (error: any) {
            message.error('删除失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    // 授权教师
    const handleAuthorize = async (id: number) => {
        try {
            const token = localStorage.getItem('token')
            await axios.post(`/api/admin/teachers/${id}/authorize`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            })
            message.success('教师已授权')
            fetchTeachers()
        } catch (error: any) {
            message.error('授权失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    // 禁用教师
    const handleDisable = async (id: number) => {
        try {
            const token = localStorage.getItem('token')
            await axios.post(`/api/admin/teachers/${id}/disable`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            })
            message.success('教师已禁用')
            fetchTeachers()
        } catch (error: any) {
            message.error('禁用失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    // 授权教师编辑权限
    const handleGrantEdit = async (id: number) => {
        try {
            const token = localStorage.getItem('token')
            await axios.post(`/api/admin/teachers/${id}/grant-edit`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            })
            message.success('已授权教师数据编辑权限')
            fetchTeachers()
        } catch (error: any) {
            message.error('授权失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    // 取消教师编辑权限
    const handleRevokeEdit = async (id: number) => {
        try {
            const token = localStorage.getItem('token')
            await axios.post(`/api/admin/teachers/${id}/revoke-edit`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            })
            message.success('已取消教师数据编辑权限')
            fetchTeachers()
        } catch (error: any) {
            message.error('取消授权失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    const columns = [
        {
            title: '教师姓名',
            dataIndex: 'name',
            key: 'name',
            render: (text: string, record: Teacher) => (
                <Space>
                    <Badge
                        status={record.is_active ? 'success' : 'error'}
                        text={<UserOutlined />}
                    />
                    {text}
                </Space>
            )
        },
        {
            title: '工号',
            dataIndex: 'employee_no',
            key: 'employee_no'
        },
        {
            title: '联系电话',
            dataIndex: 'phone',
            key: 'phone',
            render: (text: string) => text ? (
                <Space>
                    <PhoneOutlined />
                    {text}
                </Space>
            ) : '-'
        },
        {
            title: '邮箱',
            dataIndex: 'email',
            key: 'email',
            render: (text: string) => text ? (
                <Space>
                    <MailOutlined />
                    {text}
                </Space>
            ) : '-'
        },
        {
            title: '任教科目',
            dataIndex: 'subjects',
            key: 'subjects',
            render: (text: string) => text ? <Tag color="blue">{text}</Tag> : '-'
        },
        {
            title: '管理班级数',
            dataIndex: 'class_count',
            key: 'class_count',
            render: (count: number) => <Tag color="green">{count || 0} 个</Tag>
        },
        {
            title: '授权状态',
            dataIndex: 'is_active',
            key: 'is_active',
            render: (isActive: boolean) => (
                isActive ? (
                    <Tag color="success" icon={<CheckCircleOutlined />}>已授权</Tag>
                ) : (
                    <Tag color="warning" icon={<ExclamationCircleOutlined />}>待授权</Tag>
                )
            )
        },
        {
            title: '编辑权限',
            dataIndex: 'can_edit',
            key: 'can_edit',
            render: (canEdit: boolean, record: Teacher) => (
                record.is_active ? (
                    canEdit ? (
                        <Tag color="success" icon={<UnlockOutlined />}>可编辑</Tag>
                    ) : (
                        <Tag color="default" icon={<LockOutlined />}>只读</Tag>
                    )
                ) : (
                    <Tag color="default">-</Tag>
                )
            )
        },
        {
            title: '操作',
            key: 'actions',
            width: 360,
            render: (_: any, record: Teacher) => (
                <Space>
                    {record.is_active ? (
                        <Popconfirm
                            title="确定要禁用该教师账号吗？"
                            description="禁用后该教师将无法登录系统"
                            onConfirm={() => handleDisable(record.id)}
                            okText="确定"
                            cancelText="取消"
                        >
                            <Tooltip title="禁用账号">
                                <Button type="link" danger icon={<StopOutlined />}>
                                    禁用
                                </Button>
                            </Tooltip>
                        </Popconfirm>
                    ) : (
                        <Popconfirm
                            title="确定要授权该教师吗？"
                            description="授权后该教师将可以登录系统"
                            onConfirm={() => handleAuthorize(record.id)}
                            okText="确定"
                            cancelText="取消"
                        >
                            <Tooltip title="授权账号">
                                <Button type="link" style={{ color: '#52c41a' }} icon={<CheckCircleOutlined />}>
                                    授权
                                </Button>
                            </Tooltip>
                        </Popconfirm>
                    )}
                    {/* 编辑权限控制 - 只有已授权的教师才显示 */}
                    {record.is_active && (
                        record.can_edit ? (
                            <Popconfirm
                                title="确定要取消该教师的编辑权限吗？"
                                description="取消后该教师将无法进行数据录入和评语管理"
                                onConfirm={() => handleRevokeEdit(record.id)}
                                okText="确定"
                                cancelText="取消"
                            >
                                <Tooltip title="取消编辑权限">
                                    <Button type="link" icon={<LockOutlined />} style={{ color: '#faad14' }}>
                                        禁止编辑
                                    </Button>
                                </Tooltip>
                            </Popconfirm>
                        ) : (
                            <Popconfirm
                                title="确定要授权该教师编辑权限吗？"
                                description="授权后该教师可以进行数据录入和评语管理"
                                onConfirm={() => handleGrantEdit(record.id)}
                                okText="确定"
                                cancelText="取消"
                            >
                                <Tooltip title="授权编辑权限">
                                    <Button type="link" icon={<UnlockOutlined />} style={{ color: '#1890ff' }}>
                                        允许编辑
                                    </Button>
                                </Tooltip>
                            </Popconfirm>
                        )
                    )}
                    <Button
                        type="link"
                        icon={<EditOutlined />}
                        onClick={() => handleEdit(record)}
                    >
                        编辑
                    </Button>
                    <Popconfirm
                        title="确定要删除这个教师吗？"
                        onConfirm={() => handleDelete(record.id)}
                        okText="确定"
                        cancelText="取消"
                    >
                        <Button type="link" danger icon={<DeleteOutlined />}>
                            删除
                        </Button>
                    </Popconfirm>
                </Space>
            )
        }
    ]

    // 统计待授权数量
    const pendingCount = teachers.filter(t => !t.is_active).length

    return (
        <div style={{ padding: 24 }}>
            <Card
                title={
                    <Space>
                        <UserOutlined />
                        <Title level={4} style={{ margin: 0 }}>教师管理</Title>
                        {pendingCount > 0 && (
                            <Tag color="orange">{pendingCount} 人待授权</Tag>
                        )}
                    </Space>
                }
                extra={
                    <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
                        添加教师
                    </Button>
                }
            >
                <Table
                    columns={columns}
                    dataSource={teachers}
                    rowKey="id"
                    loading={loading}
                    pagination={{ pageSize: 10 }}
                    rowClassName={(record) => !record.is_active ? 'pending-row' : ''}
                />
            </Card>

            <Modal
                title={editingTeacher ? '编辑教师' : '添加教师'}
                open={modalVisible}
                onOk={handleSubmit}
                onCancel={() => setModalVisible(false)}
                width={500}
            >
                <Form form={form} layout="vertical">
                    <Form.Item
                        name="name"
                        label="教师姓名"
                        rules={[{ required: true, message: '请输入教师姓名' }]}
                    >
                        <Input placeholder="请输入教师姓名" />
                    </Form.Item>
                    <Form.Item
                        name="employee_no"
                        label="工号"
                        rules={[{ required: true, message: '请输入工号' }]}
                    >
                        <Input placeholder="请输入工号" disabled={!!editingTeacher} />
                    </Form.Item>
                    {!editingTeacher && (
                        <Form.Item
                            name="password"
                            label="初始密码"
                            rules={[{ required: true, message: '请输入初始密码' }]}
                        >
                            <Input.Password placeholder="请输入初始密码" />
                        </Form.Item>
                    )}
                    <Form.Item
                        name="phone"
                        label="联系电话"
                    >
                        <Input placeholder="请输入联系电话" />
                    </Form.Item>
                    <Form.Item
                        name="email"
                        label="邮箱"
                    >
                        <Input placeholder="请输入邮箱" />
                    </Form.Item>
                    <Form.Item
                        name="subjects"
                        label="任教科目"
                    >
                        <Select placeholder="请选择任教科目" allowClear>
                            <Option value="语文">语文</Option>
                            <Option value="数学">数学</Option>
                            <Option value="英语">英语</Option>
                            <Option value="体育">体育</Option>
                            <Option value="音乐">音乐</Option>
                            <Option value="美术">美术</Option>
                            <Option value="科学">科学</Option>
                            <Option value="品德">品德</Option>
                            <Option value="信息技术">信息技术</Option>
                        </Select>
                    </Form.Item>
                </Form>
            </Modal>

            <style>{`
                .pending-row {
                    background-color: #fffbe6;
                }
                .pending-row:hover > td {
                    background-color: #fff7cc !important;
                }
            `}</style>
        </div>
    )
}

export default Teachers
