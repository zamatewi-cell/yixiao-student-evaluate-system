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
    Typography
} from 'antd'
import {
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    UserOutlined,
    PhoneOutlined,
    MailOutlined
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
    subject: string
    status: string
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
            subject: record.subject
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

    const columns = [
        {
            title: '教师姓名',
            dataIndex: 'name',
            key: 'name',
            render: (text: string) => (
                <Space>
                    <UserOutlined />
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
            dataIndex: 'subject',
            key: 'subject',
            render: (text: string) => text ? <Tag color="blue">{text}</Tag> : '-'
        },
        {
            title: '管理班级数',
            dataIndex: 'class_count',
            key: 'class_count',
            render: (count: number) => <Tag color="green">{count || 0} 个</Tag>
        },
        {
            title: '状态',
            dataIndex: 'status',
            key: 'status',
            render: (status: string) => (
                <Tag color={status === 'active' ? 'success' : 'default'}>
                    {status === 'active' ? '在职' : '离职'}
                </Tag>
            )
        },
        {
            title: '操作',
            key: 'actions',
            width: 200,
            render: (_: any, record: Teacher) => (
                <Space>
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

    return (
        <div style={{ padding: 24 }}>
            <Card
                title={
                    <Space>
                        <UserOutlined />
                        <Title level={4} style={{ margin: 0 }}>教师管理</Title>
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
                        name="subject"
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
                        </Select>
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    )
}

export default Teachers
