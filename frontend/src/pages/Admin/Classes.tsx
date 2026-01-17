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
    TeamOutlined,
    UserOutlined
} from '@ant-design/icons'
import axios from 'axios'

const { Title } = Typography
const { Option } = Select

interface Class {
    id: number
    name: string
    grade_id: number
    grade_name: string
    head_teacher_id: number | null
    head_teacher_name: string | null
    student_count: number
}

interface Grade {
    id: number
    name: string
}

interface Teacher {
    id: number
    name: string
    user_id: number
}

const Classes: React.FC = () => {
    const [loading, setLoading] = useState(false)
    const [classes, setClasses] = useState<Class[]>([])
    const [grades, setGrades] = useState<Grade[]>([])
    const [teachers, setTeachers] = useState<Teacher[]>([])
    const [modalVisible, setModalVisible] = useState(false)
    const [editingClass, setEditingClass] = useState<Class | null>(null)
    const [form] = Form.useForm()

    // 获取班级列表
    const fetchClasses = async () => {
        try {
            setLoading(true)
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/admin/classes', {
                headers: { Authorization: `Bearer ${token}` }
            })
            setClasses(response.data.data || [])
        } catch (error: any) {
            message.error('获取班级列表失败: ' + (error.response?.data?.detail || error.message))
        } finally {
            setLoading(false)
        }
    }

    // 获取年级列表
    const fetchGrades = async () => {
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/admin/grades', {
                headers: { Authorization: `Bearer ${token}` }
            })
            setGrades(response.data.data || [])
        } catch (error: any) {
            console.error('获取年级失败:', error)
        }
    }

    // 获取教师列表
    const fetchTeachers = async () => {
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/admin/teachers', {
                headers: { Authorization: `Bearer ${token}` }
            })
            setTeachers(response.data.data || [])
        } catch (error: any) {
            console.error('获取教师失败:', error)
        }
    }

    useEffect(() => {
        fetchClasses()
        fetchGrades()
        fetchTeachers()
    }, [])

    // 打开新建模态框
    const handleAdd = () => {
        setEditingClass(null)
        form.resetFields()
        setModalVisible(true)
    }

    // 打开编辑模态框
    const handleEdit = (record: Class) => {
        setEditingClass(record)
        form.setFieldsValue({
            name: record.name,
            grade_id: record.grade_id,
            head_teacher_id: record.head_teacher_id
        })
        setModalVisible(true)
    }

    // 提交表单
    const handleSubmit = async () => {
        try {
            const values = await form.validateFields()
            const token = localStorage.getItem('token')

            if (editingClass) {
                await axios.put(`/api/admin/classes/${editingClass.id}`, values, {
                    headers: { Authorization: `Bearer ${token}` }
                })
                message.success('班级更新成功')
            } else {
                await axios.post('/api/admin/classes', values, {
                    headers: { Authorization: `Bearer ${token}` }
                })
                message.success('班级创建成功')
            }

            setModalVisible(false)
            fetchClasses()
        } catch (error: any) {
            message.error('操作失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    // 删除班级
    const handleDelete = async (id: number) => {
        try {
            const token = localStorage.getItem('token')
            await axios.delete(`/api/admin/classes/${id}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            message.success('班级删除成功')
            fetchClasses()
        } catch (error: any) {
            message.error('删除失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    const columns = [
        {
            title: '班级名称',
            key: 'fullName',
            render: (_: any, record: Class) => (
                <Space>
                    <TeamOutlined />
                    {record.grade_name} {record.name}
                </Space>
            )
        },
        {
            title: '年级',
            dataIndex: 'grade_name',
            key: 'grade_name'
        },
        {
            title: '班主任',
            dataIndex: 'head_teacher_name',
            key: 'head_teacher_name',
            render: (text: string | null) => text ? (
                <Space>
                    <UserOutlined />
                    {text}
                </Space>
            ) : <Tag color="default">未分配</Tag>
        },
        {
            title: '学生人数',
            dataIndex: 'student_count',
            key: 'student_count',
            render: (count: number) => <Tag color="blue">{count} 人</Tag>
        },
        {
            title: '操作',
            key: 'actions',
            width: 200,
            render: (_: any, record: Class) => (
                <Space>
                    <Button
                        type="link"
                        icon={<EditOutlined />}
                        onClick={() => handleEdit(record)}
                    >
                        编辑
                    </Button>
                    <Popconfirm
                        title="确定要删除这个班级吗？"
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
                        <TeamOutlined />
                        <Title level={4} style={{ margin: 0 }}>班级管理</Title>
                    </Space>
                }
                extra={
                    <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
                        新建班级
                    </Button>
                }
            >
                <Table
                    columns={columns}
                    dataSource={classes}
                    rowKey="id"
                    loading={loading}
                    pagination={{ pageSize: 10 }}
                />
            </Card>

            <Modal
                title={editingClass ? '编辑班级' : '新建班级'}
                open={modalVisible}
                onOk={handleSubmit}
                onCancel={() => setModalVisible(false)}
                width={500}
            >
                <Form form={form} layout="vertical">
                    <Form.Item
                        name="grade_id"
                        label="年级"
                        rules={[{ required: true, message: '请选择年级' }]}
                    >
                        <Select placeholder="请选择年级">
                            {grades.map(grade => (
                                <Option key={grade.id} value={grade.id}>
                                    {grade.name}
                                </Option>
                            ))}
                        </Select>
                    </Form.Item>
                    <Form.Item
                        name="name"
                        label="班级名称"
                        rules={[{ required: true, message: '请输入班级名称' }]}
                    >
                        <Input placeholder="例如：一班、二班" />
                    </Form.Item>
                    <Form.Item
                        name="head_teacher_id"
                        label="班主任"
                    >
                        <Select placeholder="请选择班主任" allowClear>
                            {teachers.map(teacher => (
                                <Option key={teacher.id} value={teacher.id}>
                                    {teacher.name}
                                </Option>
                            ))}
                        </Select>
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    )
}

export default Classes
