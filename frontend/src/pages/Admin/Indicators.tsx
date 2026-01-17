import React, { useState, useEffect } from 'react'
import {
    Card,
    Table,
    Button,
    Modal,
    Form,
    Input,
    Select,
    InputNumber,
    Switch,
    Space,
    message,
    Tag,
    Popconfirm,
    Typography,
    Collapse
} from 'antd'
import {
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    AppstoreOutlined,
    OrderedListOutlined
} from '@ant-design/icons'
import axios from 'axios'

const { Title } = Typography
const { Option } = Select
const { Panel } = Collapse
const { TextArea } = Input

interface Indicator {
    id: number
    name: string
    category_id: number
    category_name: string
    type: string
    options: string[] | null
    max_score: number
    weight: number
    description: string
    is_active: boolean
    sort_order: number
}

interface Category {
    id: number
    name: string
    description: string
    sort_order: number
}

const Indicators: React.FC = () => {
    const [loading, setLoading] = useState(false)
    const [indicators, setIndicators] = useState<Indicator[]>([])
    const [categories, setCategories] = useState<Category[]>([])
    const [modalVisible, setModalVisible] = useState(false)
    const [categoryModalVisible, setCategoryModalVisible] = useState(false)
    const [editingIndicator, setEditingIndicator] = useState<Indicator | null>(null)
    const [form] = Form.useForm()
    const [categoryForm] = Form.useForm()

    // 获取指标列表
    const fetchIndicators = async () => {
        try {
            setLoading(true)
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/admin/indicators', {
                headers: { Authorization: `Bearer ${token}` }
            })
            setIndicators(response.data.data || [])
        } catch (error: any) {
            message.error('获取指标列表失败: ' + (error.response?.data?.detail || error.message))
        } finally {
            setLoading(false)
        }
    }

    // 获取分类列表
    const fetchCategories = async () => {
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/admin/indicator-categories', {
                headers: { Authorization: `Bearer ${token}` }
            })
            setCategories(response.data.data || [])
        } catch (error: any) {
            console.error('获取分类失败:', error)
        }
    }

    useEffect(() => {
        fetchIndicators()
        fetchCategories()
    }, [])

    // 打开新建指标模态框
    const handleAdd = () => {
        setEditingIndicator(null)
        form.resetFields()
        form.setFieldsValue({ type: 'score', max_score: 100, weight: 1, is_active: true })
        setModalVisible(true)
    }

    // 打开编辑指标模态框
    const handleEdit = (record: Indicator) => {
        setEditingIndicator(record)
        form.setFieldsValue({
            ...record,
            options: record.options?.join(',') || ''
        })
        setModalVisible(true)
    }

    // 提交指标表单
    const handleSubmit = async () => {
        try {
            const values = await form.validateFields()
            const token = localStorage.getItem('token')

            // 处理options
            if (values.options && typeof values.options === 'string') {
                values.options = values.options.split(',').map((s: string) => s.trim()).filter((s: string) => s)
            }

            if (editingIndicator) {
                await axios.put(`/api/admin/indicators/${editingIndicator.id}`, values, {
                    headers: { Authorization: `Bearer ${token}` }
                })
                message.success('指标更新成功')
            } else {
                await axios.post('/api/admin/indicators', values, {
                    headers: { Authorization: `Bearer ${token}` }
                })
                message.success('指标创建成功')
            }

            setModalVisible(false)
            fetchIndicators()
        } catch (error: any) {
            message.error('操作失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    // 删除指标
    const handleDelete = async (id: number) => {
        try {
            const token = localStorage.getItem('token')
            await axios.delete(`/api/admin/indicators/${id}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            message.success('指标删除成功')
            fetchIndicators()
        } catch (error: any) {
            message.error('删除失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    // 添加分类
    const handleAddCategory = async () => {
        try {
            const values = await categoryForm.validateFields()
            const token = localStorage.getItem('token')
            await axios.post('/api/admin/indicator-categories', values, {
                headers: { Authorization: `Bearer ${token}` }
            })
            message.success('分类创建成功')
            setCategoryModalVisible(false)
            categoryForm.resetFields()
            fetchCategories()
        } catch (error: any) {
            message.error('创建失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    // 按分类分组指标
    const groupedIndicators = categories.map(cat => ({
        ...cat,
        indicators: indicators.filter(ind => ind.category_id === cat.id)
    }))

    const columns = [
        {
            title: '指标名称',
            dataIndex: 'name',
            key: 'name',
            render: (text: string, record: Indicator) => (
                <Space>
                    <OrderedListOutlined />
                    {text}
                    {!record.is_active && <Tag color="default">已禁用</Tag>}
                </Space>
            )
        },
        {
            title: '类型',
            dataIndex: 'type',
            key: 'type',
            render: (type: string) => {
                const typeMap: Record<string, { color: string; text: string }> = {
                    score: { color: 'blue', text: '分数' },
                    level: { color: 'green', text: '等级' },
                    boolean: { color: 'orange', text: '是否' },
                    number: { color: 'purple', text: '数值' }
                }
                const t = typeMap[type] || { color: 'default', text: type }
                return <Tag color={t.color}>{t.text}</Tag>
            }
        },
        {
            title: '最高分/选项',
            key: 'scoreOrOptions',
            render: (_: any, record: Indicator) => {
                if (record.type === 'score') {
                    return `0-${record.max_score}分`
                } else if (record.type === 'level' && record.options) {
                    return record.options.join(' / ')
                }
                return '-'
            }
        },
        {
            title: '权重',
            dataIndex: 'weight',
            key: 'weight',
            render: (weight: number) => `${weight}`
        },
        {
            title: '排序',
            dataIndex: 'sort_order',
            key: 'sort_order'
        },
        {
            title: '操作',
            key: 'actions',
            width: 200,
            render: (_: any, record: Indicator) => (
                <Space>
                    <Button
                        type="link"
                        icon={<EditOutlined />}
                        onClick={() => handleEdit(record)}
                    >
                        编辑
                    </Button>
                    <Popconfirm
                        title="确定要删除这个指标吗？"
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
                        <AppstoreOutlined />
                        <Title level={4} style={{ margin: 0 }}>评价指标管理</Title>
                    </Space>
                }
                extra={
                    <Space>
                        <Button onClick={() => setCategoryModalVisible(true)}>
                            添加分类
                        </Button>
                        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
                            添加指标
                        </Button>
                    </Space>
                }
            >
                {groupedIndicators.length > 0 ? (
                    <Collapse defaultActiveKey={groupedIndicators.map(g => g.id.toString())}>
                        {groupedIndicators.map(group => (
                            <Panel
                                header={
                                    <Space>
                                        <strong>{group.name}</strong>
                                        <Tag color="blue">{group.indicators.length} 个指标</Tag>
                                    </Space>
                                }
                                key={group.id.toString()}
                            >
                                <Table
                                    columns={columns}
                                    dataSource={group.indicators}
                                    rowKey="id"
                                    loading={loading}
                                    pagination={false}
                                    size="small"
                                />
                            </Panel>
                        ))}
                    </Collapse>
                ) : (
                    <Table
                        columns={columns}
                        dataSource={indicators}
                        rowKey="id"
                        loading={loading}
                        pagination={{ pageSize: 10 }}
                    />
                )}
            </Card>

            {/* 指标编辑模态框 */}
            <Modal
                title={editingIndicator ? '编辑指标' : '添加指标'}
                open={modalVisible}
                onOk={handleSubmit}
                onCancel={() => setModalVisible(false)}
                width={600}
            >
                <Form form={form} layout="vertical">
                    <Form.Item
                        name="category_id"
                        label="所属分类"
                        rules={[{ required: true, message: '请选择分类' }]}
                    >
                        <Select placeholder="请选择分类">
                            {categories.map(cat => (
                                <Option key={cat.id} value={cat.id}>
                                    {cat.name}
                                </Option>
                            ))}
                        </Select>
                    </Form.Item>
                    <Form.Item
                        name="name"
                        label="指标名称"
                        rules={[{ required: true, message: '请输入指标名称' }]}
                    >
                        <Input placeholder="例如：语文成绩、体育表现" />
                    </Form.Item>
                    <Form.Item
                        name="type"
                        label="指标类型"
                        rules={[{ required: true, message: '请选择类型' }]}
                    >
                        <Select placeholder="请选择类型">
                            <Option value="score">分数型（0-N分）</Option>
                            <Option value="level">等级型（优秀/良好/及格等）</Option>
                            <Option value="boolean">布尔型（是/否）</Option>
                            <Option value="number">数值型（次数、数量等）</Option>
                        </Select>
                    </Form.Item>
                    <Form.Item
                        noStyle
                        shouldUpdate={(prev, curr) => prev.type !== curr.type}
                    >
                        {({ getFieldValue }) =>
                            getFieldValue('type') === 'score' ? (
                                <Form.Item
                                    name="max_score"
                                    label="最高分数"
                                    rules={[{ required: true, message: '请输入最高分数' }]}
                                >
                                    <InputNumber min={1} max={1000} style={{ width: '100%' }} />
                                </Form.Item>
                            ) : getFieldValue('type') === 'level' ? (
                                <Form.Item
                                    name="options"
                                    label="等级选项"
                                    extra="多个选项用逗号分隔，如：优秀,良好,及格,不及格"
                                    rules={[{ required: true, message: '请输入等级选项' }]}
                                >
                                    <Input placeholder="优秀,良好,及格,不及格" />
                                </Form.Item>
                            ) : null
                        }
                    </Form.Item>
                    <Form.Item name="weight" label="权重">
                        <InputNumber min={0} max={10} step={0.1} style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item name="sort_order" label="排序（数字越小越靠前）">
                        <InputNumber min={0} style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item name="description" label="描述说明">
                        <TextArea rows={2} placeholder="对该指标的说明..." />
                    </Form.Item>
                    <Form.Item name="is_active" label="启用状态" valuePropName="checked">
                        <Switch checkedChildren="启用" unCheckedChildren="禁用" />
                    </Form.Item>
                </Form>
            </Modal>

            {/* 分类编辑模态框 */}
            <Modal
                title="添加指标分类"
                open={categoryModalVisible}
                onOk={handleAddCategory}
                onCancel={() => setCategoryModalVisible(false)}
                width={400}
            >
                <Form form={categoryForm} layout="vertical">
                    <Form.Item
                        name="name"
                        label="分类名称"
                        rules={[{ required: true, message: '请输入分类名称' }]}
                    >
                        <Input placeholder="例如：学业表现、品德发展" />
                    </Form.Item>
                    <Form.Item name="description" label="分类描述">
                        <TextArea rows={2} placeholder="对该分类的说明..." />
                    </Form.Item>
                    <Form.Item name="sort_order" label="排序">
                        <InputNumber min={0} style={{ width: '100%' }} />
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    )
}

export default Indicators
