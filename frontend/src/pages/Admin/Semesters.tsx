import React, { useState, useEffect } from 'react'
import {
    Card,
    Table,
    Button,
    Modal,
    Form,
    Input,
    DatePicker,
    Switch,
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
    CalendarOutlined,
    CheckCircleOutlined
} from '@ant-design/icons'
import axios from 'axios'
import dayjs from 'dayjs'

const { Title } = Typography

interface Semester {
    id: number
    name: string
    academic_year: string
    term: string
    start_date: string
    end_date: string
    is_current: boolean
    created_at: string
}

const Semesters: React.FC = () => {
    const [loading, setLoading] = useState(false)
    const [semesters, setSemesters] = useState<Semester[]>([])
    const [modalVisible, setModalVisible] = useState(false)
    const [editingSemester, setEditingSemester] = useState<Semester | null>(null)
    const [form] = Form.useForm()

    // 获取学期列表
    const fetchSemesters = async () => {
        try {
            setLoading(true)
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/admin/semesters', {
                headers: { Authorization: `Bearer ${token}` }
            })
            setSemesters(response.data.data || [])
        } catch (error: any) {
            message.error('获取学期列表失败: ' + (error.response?.data?.detail || error.message))
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchSemesters()
    }, [])

    // 打开新建模态框
    const handleAdd = () => {
        setEditingSemester(null)
        form.resetFields()
        setModalVisible(true)
    }

    // 打开编辑模态框
    const handleEdit = (record: Semester) => {
        setEditingSemester(record)
        form.setFieldsValue({
            ...record,
            start_date: dayjs(record.start_date),
            end_date: dayjs(record.end_date)
        })
        setModalVisible(true)
    }

    // 提交表单
    const handleSubmit = async () => {
        try {
            const values = await form.validateFields()
            const token = localStorage.getItem('token')

            const data = {
                ...values,
                start_date: values.start_date.format('YYYY-MM-DD'),
                end_date: values.end_date.format('YYYY-MM-DD')
            }

            if (editingSemester) {
                await axios.put(`/api/admin/semesters/${editingSemester.id}`, data, {
                    headers: { Authorization: `Bearer ${token}` }
                })
                message.success('学期更新成功')
            } else {
                await axios.post('/api/admin/semesters', data, {
                    headers: { Authorization: `Bearer ${token}` }
                })
                message.success('学期创建成功')
            }

            setModalVisible(false)
            fetchSemesters()
        } catch (error: any) {
            message.error('操作失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    // 删除学期
    const handleDelete = async (id: number) => {
        try {
            const token = localStorage.getItem('token')
            await axios.delete(`/api/admin/semesters/${id}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            message.success('学期删除成功')
            fetchSemesters()
        } catch (error: any) {
            message.error('删除失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    // 设置当前学期
    const handleSetCurrent = async (id: number) => {
        try {
            const token = localStorage.getItem('token')
            await axios.post(`/api/admin/semesters/${id}/set-current`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            })
            message.success('已设置为当前学期')
            fetchSemesters()
        } catch (error: any) {
            message.error('设置失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    const columns = [
        {
            title: '学期名称',
            dataIndex: 'name',
            key: 'name',
            render: (text: string, record: Semester) => (
                <Space>
                    <CalendarOutlined />
                    {text}
                    {record.is_current && <Tag color="green" icon={<CheckCircleOutlined />}>当前</Tag>}
                </Space>
            )
        },
        {
            title: '学年',
            dataIndex: 'academic_year',
            key: 'academic_year'
        },
        {
            title: '学期',
            dataIndex: 'term',
            key: 'term'
        },
        {
            title: '开始日期',
            dataIndex: 'start_date',
            key: 'start_date'
        },
        {
            title: '结束日期',
            dataIndex: 'end_date',
            key: 'end_date'
        },
        {
            title: '操作',
            key: 'actions',
            width: 280,
            render: (_: any, record: Semester) => (
                <Space>
                    {!record.is_current && (
                        <Button
                            type="link"
                            size="small"
                            onClick={() => handleSetCurrent(record.id)}
                        >
                            设为当前
                        </Button>
                    )}
                    <Button
                        type="link"
                        icon={<EditOutlined />}
                        onClick={() => handleEdit(record)}
                    >
                        编辑
                    </Button>
                    <Popconfirm
                        title="确定要删除这个学期吗？"
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
                        <CalendarOutlined />
                        <Title level={4} style={{ margin: 0 }}>学期管理</Title>
                    </Space>
                }
                extra={
                    <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
                        新建学期
                    </Button>
                }
            >
                <Table
                    columns={columns}
                    dataSource={semesters}
                    rowKey="id"
                    loading={loading}
                    pagination={false}
                />
            </Card>

            <Modal
                title={editingSemester ? '编辑学期' : '新建学期'}
                open={modalVisible}
                onOk={handleSubmit}
                onCancel={() => setModalVisible(false)}
                width={500}
            >
                <Form form={form} layout="vertical">
                    <Form.Item
                        name="name"
                        label="学期名称"
                        rules={[{ required: true, message: '请输入学期名称' }]}
                    >
                        <Input placeholder="例如：2023-2024学年第一学期" />
                    </Form.Item>
                    <Form.Item
                        name="academic_year"
                        label="学年"
                        rules={[{ required: true, message: '请输入学年' }]}
                    >
                        <Input placeholder="例如：2023-2024" />
                    </Form.Item>
                    <Form.Item
                        name="term"
                        label="学期"
                        rules={[{ required: true, message: '请输入学期' }]}
                    >
                        <Input placeholder="例如：第一学期" />
                    </Form.Item>
                    <Form.Item
                        name="start_date"
                        label="开始日期"
                        rules={[{ required: true, message: '请选择开始日期' }]}
                    >
                        <DatePicker style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item
                        name="end_date"
                        label="结束日期"
                        rules={[{ required: true, message: '请选择结束日期' }]}
                    >
                        <DatePicker style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item
                        name="is_current"
                        label="设为当前学期"
                        valuePropName="checked"
                    >
                        <Switch />
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    )
}

export default Semesters
