import React, { useState, useEffect, useCallback } from 'react'
import {
    Card, Table, Button, Select, Tag, Space, message, Modal, Form, Input,
    DatePicker, Row, Col, Statistic, Progress, Divider, InputNumber
} from 'antd'
import {
    PlusOutlined, DeleteOutlined, BarChartOutlined,
    TrophyOutlined, FileTextOutlined, ReloadOutlined
} from '@ant-design/icons'
import axios from 'axios'

const { Option } = Select
const { TextArea } = Input

interface Exam {
    id: number
    name: string
    exam_type: string
    semester_id: number
    semester_name: string
    grade_id: number | null
    grade_name: string | null
    exam_date: string | null
    status: string
    subject_count: number
    created_at: string
}

interface Subject {
    id: number
    subject_name: string
    full_score: number
    pass_score: number
    excellent_score: number
    sort_order: number
}

interface ExamStats {
    subject_id: number
    subject_name: string
    full_score: number
    pass_score: number
    excellent_score: number
    total_count: number
    avg_score: number
    max_score: number
    min_score: number
    pass_count: number
    excellent_count: number
    pass_rate: number
    excellent_rate: number
}

const ExamManagement: React.FC = () => {
    const [loading, setLoading] = useState(false)
    const [exams, setExams] = useState<Exam[]>([])
    const [semesters, setSemesters] = useState<any[]>([])
    const [grades, setGrades] = useState<any[]>([])
    const [selectedSemester, setSelectedSemester] = useState<number | null>(null)
    const [modalVisible, setModalVisible] = useState(false)
    const [detailModalVisible, setDetailModalVisible] = useState(false)
    const [selectedExam, setSelectedExam] = useState<Exam | null>(null)
    const [examDetail, setExamDetail] = useState<any>(null)
    const [examStats, setExamStats] = useState<ExamStats[]>([])
    const [form] = Form.useForm()

    // 获取学期列表
    const fetchSemesters = useCallback(async () => {
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/teacher/semesters', {
                headers: { Authorization: `Bearer ${token}` }
            })
            setSemesters(response.data.data || [])
            const current = response.data.data?.find((s: any) => s.is_current)
            if (current) {
                setSelectedSemester(current.id)
            }
        } catch (error) {
            message.error('获取学期列表失败')
        }
    }, [])

    // 获取年级列表
    const fetchGrades = useCallback(async () => {
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/admin/grades', {
                headers: { Authorization: `Bearer ${token}` }
            })
            setGrades(response.data.data || [])
        } catch (error) {
            console.error('获取年级失败')
        }
    }, [])

    // 获取考试列表
    const fetchExams = useCallback(async () => {
        if (!selectedSemester) return

        setLoading(true)
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/exam/list', {
                headers: { Authorization: `Bearer ${token}` },
                params: { semester_id: selectedSemester }
            })
            setExams(response.data.data || [])
        } catch (error) {
            message.error('获取考试列表失败')
        } finally {
            setLoading(false)
        }
    }, [selectedSemester])

    // 获取考试详情和统计
    const fetchExamDetail = useCallback(async (examId: number) => {
        try {
            const token = localStorage.getItem('token')

            // 获取详情
            const detailRes = await axios.get(`/api/exam/${examId}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            setExamDetail(detailRes.data.data)

            // 获取统计
            const statsRes = await axios.get(`/api/exam/statistics/${examId}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            setExamStats(statsRes.data.data || [])
        } catch (error) {
            message.error('获取考试详情失败')
        }
    }, [])

    useEffect(() => {
        fetchSemesters()
        fetchGrades()
    }, [fetchSemesters, fetchGrades])

    useEffect(() => {
        fetchExams()
    }, [fetchExams])

    // 创建考试
    const handleCreate = async () => {
        try {
            const values = await form.validateFields()
            const token = localStorage.getItem('token')

            // 解析科目
            const subjects = values.subjects?.split('\n').filter((s: string) => s.trim()).map((s: string, i: number) => ({
                name: s.trim(),
                full_score: values.full_score || 100,
                pass_score: values.pass_score || 60,
                excellent_score: values.excellent_score || 85
            })) || []

            await axios.post('/api/exam/create', {
                name: values.name,
                exam_type: values.exam_type,
                semester_id: selectedSemester,
                grade_id: values.grade_id,
                exam_date: values.exam_date?.format('YYYY-MM-DD'),
                subjects
            }, {
                headers: { Authorization: `Bearer ${token}` }
            })

            message.success('考试创建成功')
            setModalVisible(false)
            form.resetFields()
            fetchExams()
        } catch (error: any) {
            message.error('创建失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    // 删除考试
    const handleDelete = async (examId: number) => {
        Modal.confirm({
            title: '确认删除',
            content: '删除考试将同时删除所有相关成绩数据，是否继续？',
            onOk: async () => {
                try {
                    const token = localStorage.getItem('token')
                    await axios.delete(`/api/exam/${examId}`, {
                        headers: { Authorization: `Bearer ${token}` }
                    })
                    message.success('删除成功')
                    fetchExams()
                } catch (error) {
                    message.error('删除失败')
                }
            }
        })
    }

    // 计算排名
    const handleCalculateRanks = async (examId: number) => {
        try {
            const token = localStorage.getItem('token')
            await axios.post(`/api/exam/calculate-ranks/${examId}`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            })
            message.success('排名计算完成')
            if (selectedExam?.id === examId) {
                fetchExamDetail(examId)
            }
        } catch (error) {
            message.error('排名计算失败')
        }
    }

    // 查看详情
    const handleViewDetail = (exam: Exam) => {
        setSelectedExam(exam)
        fetchExamDetail(exam.id)
        setDetailModalVisible(true)
    }

    // 考试类型显示
    const renderExamType = (type: string) => {
        const typeMap: { [key: string]: { color: string; text: string } } = {
            'unit': { color: 'blue', text: '单元测验' },
            'midterm': { color: 'green', text: '期中考试' },
            'final': { color: 'red', text: '期末考试' },
            'other': { color: 'default', text: '其他' }
        }
        const info = typeMap[type] || { color: 'default', text: type }
        return <Tag color={info.color}>{info.text}</Tag>
    }

    // 状态显示
    const renderStatus = (status: string) => {
        const statusMap: { [key: string]: { color: string; text: string } } = {
            'draft': { color: 'default', text: '草稿' },
            'active': { color: 'processing', text: '进行中' },
            'completed': { color: 'success', text: '已完成' }
        }
        const info = statusMap[status] || { color: 'default', text: status }
        return <Tag color={info.color}>{info.text}</Tag>
    }

    const columns = [
        {
            title: '考试名称',
            dataIndex: 'name',
            key: 'name',
            render: (text: string, record: Exam) => (
                <a onClick={() => handleViewDetail(record)}>{text}</a>
            )
        },
        {
            title: '类型',
            dataIndex: 'exam_type',
            key: 'exam_type',
            width: 100,
            render: (type: string) => renderExamType(type)
        },
        {
            title: '年级',
            dataIndex: 'grade_name',
            key: 'grade_name',
            width: 100,
            render: (text: string) => text || '全校'
        },
        {
            title: '考试日期',
            dataIndex: 'exam_date',
            key: 'exam_date',
            width: 120
        },
        {
            title: '科目数',
            dataIndex: 'subject_count',
            key: 'subject_count',
            width: 80,
            align: 'center' as const
        },
        {
            title: '状态',
            dataIndex: 'status',
            key: 'status',
            width: 100,
            render: (status: string) => renderStatus(status)
        },
        {
            title: '操作',
            key: 'action',
            width: 200,
            render: (_: any, record: Exam) => (
                <Space>
                    <Button size="small" icon={<BarChartOutlined />} onClick={() => handleViewDetail(record)}>
                        详情
                    </Button>
                    <Button size="small" icon={<TrophyOutlined />} onClick={() => handleCalculateRanks(record.id)}>
                        计算排名
                    </Button>
                    <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)}>
                        删除
                    </Button>
                </Space>
            )
        }
    ]

    return (
        <div style={{ padding: 24 }}>
            <Card
                title={
                    <Space>
                        <FileTextOutlined />
                        <span>考试管理</span>
                    </Space>
                }
                extra={
                    <Space>
                        <Select
                            style={{ width: 200 }}
                            placeholder="选择学期"
                            value={selectedSemester}
                            onChange={setSelectedSemester}
                        >
                            {semesters.map(s => (
                                <Option key={s.id} value={s.id}>
                                    {s.name} {s.is_current && <Tag color="green">当前</Tag>}
                                </Option>
                            ))}
                        </Select>
                        <Button icon={<ReloadOutlined />} onClick={fetchExams}>刷新</Button>
                        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>
                            新建考试
                        </Button>
                    </Space>
                }
            >
                <Table
                    dataSource={exams}
                    columns={columns}
                    rowKey="id"
                    loading={loading}
                    pagination={{ pageSize: 10 }}
                />
            </Card>

            {/* 新建考试模态框 */}
            <Modal
                title="新建考试"
                open={modalVisible}
                onOk={handleCreate}
                onCancel={() => {
                    setModalVisible(false)
                    form.resetFields()
                }}
                okText="创建"
                cancelText="取消"
                width={600}
            >
                <Form form={form} layout="vertical">
                    <Form.Item
                        name="name"
                        label="考试名称"
                        rules={[{ required: true, message: '请输入考试名称' }]}
                    >
                        <Input placeholder="如：2026年春季第一次月考" />
                    </Form.Item>
                    <Row gutter={16}>
                        <Col span={12}>
                            <Form.Item
                                name="exam_type"
                                label="考试类型"
                                initialValue="unit"
                            >
                                <Select>
                                    <Option value="unit">单元测验</Option>
                                    <Option value="midterm">期中考试</Option>
                                    <Option value="final">期末考试</Option>
                                    <Option value="other">其他</Option>
                                </Select>
                            </Form.Item>
                        </Col>
                        <Col span={12}>
                            <Form.Item name="grade_id" label="适用年级">
                                <Select placeholder="留空则为全校" allowClear>
                                    {grades.map(g => (
                                        <Option key={g.id} value={g.id}>{g.name}</Option>
                                    ))}
                                </Select>
                            </Form.Item>
                        </Col>
                    </Row>
                    <Form.Item name="exam_date" label="考试日期">
                        <DatePicker style={{ width: '100%' }} />
                    </Form.Item>
                    <Divider>科目设置</Divider>
                    <Form.Item
                        name="subjects"
                        label="考试科目（每行一个科目名称）"
                        rules={[{ required: true, message: '请输入考试科目' }]}
                    >
                        <TextArea rows={4} placeholder="语文&#10;数学&#10;英语" />
                    </Form.Item>
                    <Row gutter={16}>
                        <Col span={8}>
                            <Form.Item name="full_score" label="满分" initialValue={100}>
                                <InputNumber min={1} max={200} style={{ width: '100%' }} />
                            </Form.Item>
                        </Col>
                        <Col span={8}>
                            <Form.Item name="pass_score" label="及格分" initialValue={60}>
                                <InputNumber min={0} max={200} style={{ width: '100%' }} />
                            </Form.Item>
                        </Col>
                        <Col span={8}>
                            <Form.Item name="excellent_score" label="优秀分" initialValue={85}>
                                <InputNumber min={0} max={200} style={{ width: '100%' }} />
                            </Form.Item>
                        </Col>
                    </Row>
                </Form>
            </Modal>

            {/* 考试详情模态框 */}
            <Modal
                title={`考试详情 - ${selectedExam?.name || ''}`}
                open={detailModalVisible}
                onCancel={() => {
                    setDetailModalVisible(false)
                    setSelectedExam(null)
                    setExamDetail(null)
                    setExamStats([])
                }}
                footer={null}
                width={900}
            >
                {examDetail && (
                    <>
                        <Row gutter={16} style={{ marginBottom: 24 }}>
                            <Col span={6}>
                                <Statistic title="考试类型" value={
                                    examDetail.exam_type === 'unit' ? '单元测验' :
                                        examDetail.exam_type === 'midterm' ? '期中考试' :
                                            examDetail.exam_type === 'final' ? '期末考试' : '其他'
                                } />
                            </Col>
                            <Col span={6}>
                                <Statistic title="考试日期" value={examDetail.exam_date || '未设置'} />
                            </Col>
                            <Col span={6}>
                                <Statistic title="科目数" value={examDetail.subjects?.length || 0} suffix="门" />
                            </Col>
                            <Col span={6}>
                                <Statistic title="状态" value={
                                    examDetail.status === 'draft' ? '草稿' :
                                        examDetail.status === 'active' ? '进行中' : '已完成'
                                } />
                            </Col>
                        </Row>

                        <Divider>各科目统计</Divider>

                        <Table
                            dataSource={examStats}
                            rowKey="subject_id"
                            pagination={false}
                            size="small"
                            columns={[
                                { title: '科目', dataIndex: 'subject_name', key: 'subject_name' },
                                { title: '满分', dataIndex: 'full_score', key: 'full_score', align: 'center' as const },
                                { title: '参考人数', dataIndex: 'total_count', key: 'total_count', align: 'center' as const },
                                {
                                    title: '平均分', dataIndex: 'avg_score', key: 'avg_score', align: 'center' as const,
                                    render: (v: number) => v ? v.toFixed(1) : '-'
                                },
                                { title: '最高分', dataIndex: 'max_score', key: 'max_score', align: 'center' as const },
                                { title: '最低分', dataIndex: 'min_score', key: 'min_score', align: 'center' as const },
                                {
                                    title: '及格率', dataIndex: 'pass_rate', key: 'pass_rate', align: 'center' as const,
                                    render: (v: number) => (
                                        <Progress percent={v || 0} size="small" format={(p) => `${p}%`} />
                                    )
                                },
                                {
                                    title: '优秀率', dataIndex: 'excellent_rate', key: 'excellent_rate', align: 'center' as const,
                                    render: (v: number) => (
                                        <Progress percent={v || 0} size="small" strokeColor="#52c41a" format={(p) => `${p}%`} />
                                    )
                                }
                            ]}
                        />
                    </>
                )}
            </Modal>
        </div>
    )
}

export default ExamManagement
