import React, { useState, useEffect, useCallback } from 'react'
import {
    Card, Table, Button, Tag, Space, message, Modal, Form, Input,
    Select, Switch, Popconfirm, Typography, Badge
} from 'antd'
import {
    PlusOutlined, EditOutlined, DeleteOutlined, PushpinOutlined,
    NotificationOutlined, ReloadOutlined, EyeOutlined
} from '@ant-design/icons'
import axios from 'axios'

const { Option } = Select
const { TextArea } = Input
const { Text } = Typography

interface Notice {
    id: number
    title: string
    content: string
    notice_type: string
    notice_type_info: { text: string; color: string }
    target_type: string
    is_pinned: boolean
    view_count: number
    status: string
    author_name: string
    created_at: string
}

const NOTICE_TYPES = [
    { value: 'general', label: '一般通知', color: 'blue' },
    { value: 'exam', label: '考试通知', color: 'orange' },
    { value: 'attendance', label: '考勤通知', color: 'green' },
    { value: 'activity', label: '活动通知', color: 'purple' },
    { value: 'urgent', label: '紧急通知', color: 'red' }
]

const TARGET_TYPES = [
    { value: 'all', label: '全部用户' },
    { value: 'teacher', label: '教师' },
    { value: 'student', label: '学生' }
]

const NoticeManagement: React.FC = () => {
    const [loading, setLoading] = useState(false)
    const [notices, setNotices] = useState<Notice[]>([])
    const [total, setTotal] = useState(0)
    const [page, setPage] = useState(1)
    const [modalVisible, setModalVisible] = useState(false)
    const [detailModalVisible, setDetailModalVisible] = useState(false)
    const [editingNotice, setEditingNotice] = useState<Notice | null>(null)
    const [currentNotice, setCurrentNotice] = useState<Notice | null>(null)
    const [form] = Form.useForm()

    // 获取通知列表
    const fetchNotices = useCallback(async () => {
        setLoading(true)
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/notice/list', {
                headers: { Authorization: `Bearer ${token}` },
                params: { page, page_size: 10 }
            })
            setNotices(response.data.data || [])
            setTotal(response.data.total || 0)
        } catch (error) {
            message.error('获取通知列表失败')
        } finally {
            setLoading(false)
        }
    }, [page])

    useEffect(() => {
        fetchNotices()
    }, [fetchNotices])

    // 创建或更新通知
    const handleSubmit = async () => {
        try {
            const values = await form.validateFields()
            const token = localStorage.getItem('token')

            if (editingNotice) {
                await axios.put(`/api/notice/${editingNotice.id}`, values, {
                    headers: { Authorization: `Bearer ${token}` }
                })
                message.success('更新成功')
            } else {
                await axios.post('/api/notice/create', values, {
                    headers: { Authorization: `Bearer ${token}` }
                })
                message.success('发布成功')
            }

            setModalVisible(false)
            setEditingNotice(null)
            form.resetFields()
            fetchNotices()
        } catch (error) {
            message.error('操作失败')
        }
    }

    // 删除通知
    const handleDelete = async (id: number) => {
        try {
            const token = localStorage.getItem('token')
            await axios.delete(`/api/notice/${id}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            message.success('删除成功')
            fetchNotices()
        } catch (error) {
            message.error('删除失败')
        }
    }

    // 置顶/取消置顶
    const handleTogglePin = async (notice: Notice) => {
        try {
            const token = localStorage.getItem('token')
            await axios.put(`/api/notice/${notice.id}`, {
                is_pinned: !notice.is_pinned
            }, {
                headers: { Authorization: `Bearer ${token}` }
            })
            message.success(notice.is_pinned ? '已取消置顶' : '已置顶')
            fetchNotices()
        } catch (error) {
            message.error('操作失败')
        }
    }

    // 查看详情
    const handleView = async (notice: Notice) => {
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get(`/api/notice/${notice.id}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            setCurrentNotice(response.data.data)
            setDetailModalVisible(true)
        } catch (error) {
            message.error('获取详情失败')
        }
    }

    // 编辑
    const handleEdit = (notice: Notice) => {
        setEditingNotice(notice)
        form.setFieldsValue({
            title: notice.title,
            content: notice.content,
            notice_type: notice.notice_type,
            target_type: notice.target_type,
            is_pinned: notice.is_pinned
        })
        setModalVisible(true)
    }

    const columns = [
        {
            title: '标题',
            dataIndex: 'title',
            key: 'title',
            render: (text: string, record: Notice) => (
                <Space>
                    {record.is_pinned && <Tag color="gold"><PushpinOutlined /></Tag>}
                    <a onClick={() => handleView(record)}>{text}</a>
                </Space>
            )
        },
        {
            title: '类型',
            dataIndex: 'notice_type',
            key: 'notice_type',
            width: 120,
            render: (_: any, record: Notice) => (
                <Tag color={record.notice_type_info?.color || 'default'}>
                    {record.notice_type_info?.text || record.notice_type}
                </Tag>
            )
        },
        {
            title: '阅读',
            dataIndex: 'view_count',
            key: 'view_count',
            width: 80,
            align: 'center' as const,
            render: (count: number) => <Badge count={count} showZero overflowCount={999} />
        },
        {
            title: '发布者',
            dataIndex: 'author_name',
            key: 'author_name',
            width: 100
        },
        {
            title: '发布时间',
            dataIndex: 'created_at',
            key: 'created_at',
            width: 180
        },
        {
            title: '操作',
            key: 'action',
            width: 200,
            render: (_: any, record: Notice) => (
                <Space>
                    <Button
                        size="small"
                        icon={<EyeOutlined />}
                        onClick={() => handleView(record)}
                    />
                    <Button
                        size="small"
                        icon={<PushpinOutlined />}
                        type={record.is_pinned ? 'primary' : 'default'}
                        onClick={() => handleTogglePin(record)}
                    />
                    <Button
                        size="small"
                        icon={<EditOutlined />}
                        onClick={() => handleEdit(record)}
                    />
                    <Popconfirm
                        title="确定删除此通知？"
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
                title={
                    <Space>
                        <NotificationOutlined />
                        <span>通知公告管理</span>
                    </Space>
                }
                extra={
                    <Space>
                        <Button icon={<ReloadOutlined />} onClick={fetchNotices}>刷新</Button>
                        <Button
                            type="primary"
                            icon={<PlusOutlined />}
                            onClick={() => {
                                setEditingNotice(null)
                                form.resetFields()
                                setModalVisible(true)
                            }}
                        >
                            发布通知
                        </Button>
                    </Space>
                }
            >
                <Table
                    dataSource={notices}
                    columns={columns}
                    rowKey="id"
                    loading={loading}
                    pagination={{
                        current: page,
                        total,
                        pageSize: 10,
                        onChange: setPage
                    }}
                />
            </Card>

            {/* 创建/编辑模态框 */}
            <Modal
                title={editingNotice ? '编辑通知' : '发布通知'}
                open={modalVisible}
                onOk={handleSubmit}
                onCancel={() => {
                    setModalVisible(false)
                    setEditingNotice(null)
                    form.resetFields()
                }}
                okText={editingNotice ? '保存' : '发布'}
                cancelText="取消"
                width={600}
            >
                <Form form={form} layout="vertical">
                    <Form.Item
                        name="title"
                        label="标题"
                        rules={[{ required: true, message: '请输入标题' }]}
                    >
                        <Input placeholder="输入通知标题" />
                    </Form.Item>
                    <Form.Item
                        name="content"
                        label="内容"
                        rules={[{ required: true, message: '请输入内容' }]}
                    >
                        <TextArea rows={6} placeholder="输入通知内容" />
                    </Form.Item>
                    <Space size={24}>
                        <Form.Item name="notice_type" label="类型" initialValue="general">
                            <Select style={{ width: 150 }}>
                                {NOTICE_TYPES.map(t => (
                                    <Option key={t.value} value={t.value}>
                                        <Tag color={t.color}>{t.label}</Tag>
                                    </Option>
                                ))}
                            </Select>
                        </Form.Item>
                        <Form.Item name="target_type" label="发布对象" initialValue="all">
                            <Select style={{ width: 150 }}>
                                {TARGET_TYPES.map(t => (
                                    <Option key={t.value} value={t.value}>{t.label}</Option>
                                ))}
                            </Select>
                        </Form.Item>
                        <Form.Item name="is_pinned" label="置顶" valuePropName="checked">
                            <Switch />
                        </Form.Item>
                    </Space>
                </Form>
            </Modal>

            {/* 详情模态框 */}
            <Modal
                title={currentNotice?.title}
                open={detailModalVisible}
                onCancel={() => setDetailModalVisible(false)}
                footer={null}
                width={600}
            >
                {currentNotice && (
                    <div>
                        <Space style={{ marginBottom: 16 }}>
                            <Tag color={currentNotice.notice_type_info?.color}>
                                {currentNotice.notice_type_info?.text}
                            </Tag>
                            <Text type="secondary">
                                {currentNotice.author_name} 发布于 {currentNotice.created_at}
                            </Text>
                            <Text type="secondary">
                                阅读 {currentNotice.view_count} 次
                            </Text>
                        </Space>
                        <div
                            style={{
                                padding: 16,
                                background: '#f5f5f5',
                                borderRadius: 8,
                                whiteSpace: 'pre-wrap',
                                lineHeight: 1.8
                            }}
                        >
                            {currentNotice.content}
                        </div>
                    </div>
                )}
            </Modal>
        </div>
    )
}

export default NoticeManagement
