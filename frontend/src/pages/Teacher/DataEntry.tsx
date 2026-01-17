import React, { useState, useEffect } from 'react'
import {
    Card,
    Form,
    Select,
    Table,
    Button,
    Input,
    InputNumber,
    message,
    Space,
    Row,
    Col,
    Divider,
    Typography,
    Tag,
    Popconfirm
} from 'antd'
import {
    SaveOutlined,
    ReloadOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined
} from '@ant-design/icons'
import axios from 'axios'

const { Option } = Select
const { Title, Text } = Typography

interface Class {
    id: number
    name: string
    grade_name: string
    student_count: number
}

interface Semester {
    id: number
    name: string
    is_current: boolean
}

interface Indicator {
    id: number
    name: string
    category_name: string
    type: string
    options: string[] | null
    max_score: number
}

interface Student {
    id: number
    student_no: string
    name: string
    gender: string
}

interface EvaluationDataRow extends Student {
    value?: string | number
    remark?: string
    status?: 'pending' | 'success' | 'error'
}

const DataEntry: React.FC = () => {
    const [form] = Form.useForm()
    const [loading, setLoading] = useState(false)
    const [submitting, setSubmitting] = useState(false)

    // 基础数据
    const [myClasses, setMyClasses] = useState<Class[]>([])
    const [semesters, setSemesters] = useState<Semester[]>([])
    const [indicators, setIndicators] = useState<Indicator[]>([])

    // 选中的值
    const [selectedClass, setSelectedClass] = useState<number | null>(null)
    const [selectedSemester, setSelectedSemester] = useState<number | null>(null)
    const [selectedIndicator, setSelectedIndicator] = useState<Indicator | null>(null)

    // 表格数据
    const [tableData, setTableData] = useState<EvaluationDataRow[]>([])

    // 获取我的班级
    const fetchMyClasses = async () => {
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/teacher/my-classes', {
                headers: { Authorization: `Bearer ${token}` }
            })
            setMyClasses(response.data.data)
        } catch (error: any) {
            message.error('获取班级列表失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    // 获取学期列表
    const fetchSemesters = async () => {
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/teacher/current-semester', {
                headers: { Authorization: `Bearer ${token}` }
            })
            if (response.data.data) {
                setSemesters([response.data.data])
                setSelectedSemester(response.data.data.id)
            }
        } catch (error: any) {
            message.error('获取学期信息失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    // 获取评价指标
    const fetchIndicators = async () => {
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/admin/indicators', {
                headers: { Authorization: `Bearer ${token}` }
            })
            setIndicators(response.data.data)
        } catch (error: any) {
            message.error('获取评价指标失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    // 获取班级学生
    const fetchClassStudents = async (classId: number) => {
        try {
            setLoading(true)
            const token = localStorage.getItem('token')
            const response = await axios.get(`/api/teacher/classes/${classId}/students`, {
                headers: { Authorization: `Bearer ${token}` }
            })

            const initData: EvaluationDataRow[] = response.data.data.map((student: Student) => ({
                ...student,
                value: undefined,
                remark: '',
                status: 'pending'
            }))
            setTableData(initData)
        } catch (error: any) {
            message.error('获取学生列表失败: ' + (error.response?.data?.detail || error.message))
        } finally {
            setLoading(false)
        }
    }

    // 初始化数据
    useEffect(() => {
        fetchMyClasses()
        fetchSemesters()
        fetchIndicators()
    }, [])

    // 班级变化时加载学生
    useEffect(() => {
        if (selectedClass) {
            fetchClassStudents(selectedClass)
        }
    }, [selectedClass])

    // 处理指标选择
    const handleIndicatorChange = (indicatorId: number) => {
        const indicator = indicators.find(ind => ind.id === indicatorId)
        setSelectedIndicator(indicator || null)

        setTableData(prev => prev.map(row => ({
            ...row,
            value: undefined,
            status: 'pending'
        })))
    }

    // 更新单个学生的数据
    const updateStudentValue = (studentId: number, field: string, value: any) => {
        setTableData(prev =>
            prev.map(row =>
                row.id === studentId ? { ...row, [field]: value } : row
            )
        )
    }

    // 批量提交数据
    const handleBatchSubmit = async () => {
        if (!selectedClass || !selectedSemester || !selectedIndicator) {
            message.warning('请先选择班级、学期和评价指标')
            return
        }

        const validData = tableData.filter(row => row.value !== undefined && row.value !== null && row.value !== '')

        if (validData.length === 0) {
            message.warning('请至少录入一条数据')
            return
        }

        try {
            setSubmitting(true)
            const token = localStorage.getItem('token')

            const batchData = {
                semester_id: selectedSemester,
                indicator_id: selectedIndicator.id,
                data: validData.map(row => ({
                    student_id: row.id,
                    value: String(row.value),
                    remark: row.remark || ''
                }))
            }

            await axios.post('/api/teacher/evaluations/batch', batchData, {
                headers: { Authorization: `Bearer ${token}` }
            })

            message.success(`成功录入 ${validData.length} 条数据`)

            setTableData(prev =>
                prev.map(row => ({
                    ...row,
                    status: validData.find(v => v.id === row.id) ? 'success' : row.status
                }))
            )
        } catch (error: any) {
            message.error('批量提交失败: ' + (error.response?.data?.detail || error.message))
        } finally {
            setSubmitting(false)
        }
    }

    // 重置表单
    const handleReset = () => {
        setTableData(prev =>
            prev.map(row => ({
                ...row,
                value: undefined,
                remark: '',
                status: 'pending'
            }))
        )
        message.info('已重置所有数据')
    }

    // 渲染输入控件
    const renderInputControl = (record: EvaluationDataRow) => {
        if (!selectedIndicator) return null

        const { type, options, max_score } = selectedIndicator

        switch (type) {
            case 'score':
                return (
                    <InputNumber
                        min={0}
                        max={max_score}
                        precision={1}
                        placeholder={`0-${max_score}`}
                        value={record.value as number}
                        onChange={value => updateStudentValue(record.id, 'value', value)}
                        style={{ width: '100%' }}
                    />
                )

            case 'level':
                return (
                    <Select
                        placeholder="请选择等级"
                        value={record.value as string}
                        onChange={value => updateStudentValue(record.id, 'value', value)}
                        style={{ width: '100%' }}
                    >
                        {options?.map(opt => (
                            <Option key={opt} value={opt}>{opt}</Option>
                        ))}
                    </Select>
                )

            case 'boolean':
                return (
                    <Select
                        placeholder="请选择"
                        value={record.value as string}
                        onChange={value => updateStudentValue(record.id, 'value', value)}
                        style={{ width: '100%' }}
                    >
                        <Option value="是">是</Option>
                        <Option value="否">否</Option>
                    </Select>
                )

            default:
                return (
                    <Input
                        placeholder="请输入"
                        value={record.value as string}
                        onChange={e => updateStudentValue(record.id, 'value', e.target.value)}
                    />
                )
        }
    }

    // 表格列定义
    const columns = [
        {
            title: '序号',
            key: 'index',
            width: 60,
            render: (_: any, __: any, index: number) => index + 1
        },
        {
            title: '学号',
            dataIndex: 'student_no',
            key: 'student_no',
            width: 120
        },
        {
            title: '姓名',
            dataIndex: 'name',
            key: 'name',
            width: 100
        },
        {
            title: '性别',
            dataIndex: 'gender',
            key: 'gender',
            width: 60,
            render: (gender: string) => gender === 'male' ? '男' : '女'
        },
        {
            title: () => (
                <span>
                    {selectedIndicator?.name || '评价值'}
                    {selectedIndicator && (
                        <Tag color="blue" style={{ marginLeft: 8 }}>
                            {selectedIndicator.type === 'score' && `分数(0-${selectedIndicator.max_score})`}
                            {selectedIndicator.type === 'level' && '等级'}
                            {selectedIndicator.type === 'boolean' && '是否'}
                        </Tag>
                    )}
                </span>
            ),
            key: 'value',
            width: 200,
            render: (_: any, record: EvaluationDataRow) => renderInputControl(record)
        },
        {
            title: '备注',
            key: 'remark',
            width: 200,
            render: (_: any, record: EvaluationDataRow) => (
                <Input
                    placeholder="备注（可选）"
                    value={record.remark}
                    onChange={e => updateStudentValue(record.id, 'remark', e.target.value)}
                />
            )
        },
        {
            title: '状态',
            key: 'status',
            width: 80,
            render: (_: any, record: EvaluationDataRow) => {
                if (record.status === 'success') {
                    return <Tag icon={<CheckCircleOutlined />} color="success">已保存</Tag>
                } else if (record.status === 'error') {
                    return <Tag icon={<CloseCircleOutlined />} color="error">失败</Tag>
                }
                return <Tag color="default">待提交</Tag>
            }
        }
    ]

    return (
        <div style={{ padding: 24 }}>
            <Card
                title={
                    <Space>
                        <Title level={4} style={{ margin: 0 }}>数据录入</Title>
                    </Space>
                }
                extra={
                    <Button
                        icon={<ReloadOutlined />}
                        onClick={() => {
                            fetchMyClasses()
                            fetchIndicators()
                        }}
                    >
                        刷新
                    </Button>
                }
            >
                {/* 筛选条件 */}
                <Form form={form} layout="vertical">
                    <Row gutter={16}>
                        <Col span={6}>
                            <Form.Item label="选择班级" required>
                                <Select
                                    placeholder="请选择班级"
                                    value={selectedClass}
                                    onChange={setSelectedClass}
                                >
                                    {myClasses.map(cls => (
                                        <Option key={cls.id} value={cls.id}>
                                            {cls.grade_name} {cls.name}（{cls.student_count}人）
                                        </Option>
                                    ))}
                                </Select>
                            </Form.Item>
                        </Col>

                        <Col span={6}>
                            <Form.Item label="选择学期" required>
                                <Select
                                    placeholder="请选择学期"
                                    value={selectedSemester}
                                    onChange={setSelectedSemester}
                                    disabled={semesters.length === 0}
                                >
                                    {semesters.map(sem => (
                                        <Option key={sem.id} value={sem.id}>
                                            {sem.name} {sem.is_current && <Tag color="green">当前</Tag>}
                                        </Option>
                                    ))}
                                </Select>
                            </Form.Item>
                        </Col>

                        <Col span={12}>
                            <Form.Item label="评价指标" required>
                                <Select
                                    placeholder="请选择评价指标"
                                    value={selectedIndicator?.id}
                                    onChange={handleIndicatorChange}
                                >
                                    {indicators.map(ind => (
                                        <Option key={ind.id} value={ind.id}>
                                            [{ind.category_name}] {ind.name}
                                        </Option>
                                    ))}
                                </Select>
                            </Form.Item>
                        </Col>
                    </Row>
                </Form>

                <Divider />

                {/* 操作按钮 */}
                <Space style={{ marginBottom: 16 }}>
                    <Button
                        type="primary"
                        icon={<SaveOutlined />}
                        onClick={handleBatchSubmit}
                        loading={submitting}
                        disabled={!selectedClass || !selectedSemester || !selectedIndicator}
                    >
                        批量提交
                    </Button>
                    <Popconfirm
                        title="确定要重置所有录入的数据吗？"
                        onConfirm={handleReset}
                        okText="确定"
                        cancelText="取消"
                    >
                        <Button icon={<ReloadOutlined />}>重置</Button>
                    </Popconfirm>
                </Space>

                {/* 数据统计 */}
                {selectedClass && (
                    <div style={{ marginBottom: 16 }}>
                        <Space>
                            <Text>总学生数: <strong>{tableData.length}</strong></Text>
                            <Text>已录入: <strong style={{ color: '#52c41a' }}>
                                {tableData.filter(r => r.value !== undefined && r.value !== null && r.value !== '').length}
                            </strong></Text>
                            <Text>未录入: <strong style={{ color: '#faad14' }}>
                                {tableData.filter(r => r.value === undefined || r.value === null || r.value === '').length}
                            </strong></Text>
                            <Text>已保存: <strong style={{ color: '#1890ff' }}>
                                {tableData.filter(r => r.status === 'success').length}
                            </strong></Text>
                        </Space>
                    </div>
                )}

                {/* 学生数据表格 */}
                <Table
                    columns={columns}
                    dataSource={tableData}
                    rowKey="id"
                    loading={loading}
                    pagination={{
                        pageSize: 20,
                        showSizeChanger: true,
                        showTotal: total => `共 ${total} 名学生`
                    }}
                    scroll={{ x: 1000 }}
                    locale={{
                        emptyText: selectedClass ? '该班级暂无学生' : '请先选择班级'
                    }}
                />
            </Card>
        </div>
    )
}

export default DataEntry
