import React, { useState, useEffect, useCallback } from 'react'
import {
    Card, Table, Button, Select, Tag, Space, message, Modal, Form, Input,
    Row, Col, Statistic, Progress, Divider, Typography, InputNumber, Tabs, Empty
} from 'antd'
import {
    PlusOutlined, BulbOutlined, BarChartOutlined,
    FileSearchOutlined, ReloadOutlined, RobotOutlined
} from '@ant-design/icons'
import axios from 'axios'

const { Option } = Select
const { TextArea } = Input
const { Text, Paragraph } = Typography
const { TabPane } = Tabs

interface WrongAnswer {
    id: number
    student_name: string
    exam_name: string
    subject_name: string
    question_number: number
    question_content: string
    correct_answer: string
    student_answer: string
    knowledge_point: string
    error_type: string
    created_at: string
}

interface ClassStats {
    knowledge_stats: { knowledge_point: string; count: number }[]
    error_type_stats: { error_type: string; count: number }[]
    student_stats: { id: number; name: string; wrong_count: number }[]
}

const WrongAnswerAnalysis: React.FC = () => {
    const [loading, setLoading] = useState(false)
    const [analyzing, setAnalyzing] = useState(false)
    const [exams, setExams] = useState<any[]>([])
    const [classes, setClasses] = useState<any[]>([])
    const [subjects, setSubjects] = useState<any[]>([])
    const [wrongAnswers, setWrongAnswers] = useState<WrongAnswer[]>([])
    const [classStats, setClassStats] = useState<ClassStats | null>(null)
    const [analysis, setAnalysis] = useState<string>('')
    const [selectedExam, setSelectedExam] = useState<number | null>(null)
    const [selectedClass, setSelectedClass] = useState<number | null>(null)
    const [selectedSubject, setSelectedSubject] = useState<number | null>(null)
    const [modalVisible, setModalVisible] = useState(false)
    const [form] = Form.useForm()
    const [activeTab, setActiveTab] = useState('stats')

    // 获取考试列表
    const fetchExams = useCallback(async () => {
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/exam/list', {
                headers: { Authorization: `Bearer ${token}` }
            })
            setExams(response.data.data || [])
        } catch (error) {
            message.error('获取考试列表失败')
        }
    }, [])

    // 获取班级列表
    const fetchClasses = useCallback(async () => {
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/teacher/my-classes', {
                headers: { Authorization: `Bearer ${token}` }
            })
            setClasses(response.data.data || [])
            if (response.data.data?.length > 0) {
                setSelectedClass(response.data.data[0].id)
            }
        } catch (error) {
            message.error('获取班级列表失败')
        }
    }, [])

    // 获取科目列表
    const fetchSubjects = useCallback(async (examId: number) => {
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get(`/api/exam/${examId}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            setSubjects(response.data.data?.subjects || [])
        } catch (error) {
            message.error('获取科目失败')
        }
    }, [])

    // 获取班级错题统计
    const fetchClassStats = useCallback(async () => {
        if (!selectedClass) return

        setLoading(true)
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get(`/api/wrong-answer/class/${selectedClass}`, {
                headers: { Authorization: `Bearer ${token}` },
                params: selectedExam ? { exam_id: selectedExam } : {}
            })
            setClassStats(response.data.data)
        } catch (error) {
            console.error('获取统计失败')
        } finally {
            setLoading(false)
        }
    }, [selectedClass, selectedExam])

    useEffect(() => {
        fetchExams()
        fetchClasses()
    }, [fetchExams, fetchClasses])

    useEffect(() => {
        if (selectedExam) {
            fetchSubjects(selectedExam)
        }
    }, [selectedExam, fetchSubjects])

    useEffect(() => {
        fetchClassStats()
    }, [fetchClassStats])

    // 添加错题
    const handleAddWrongAnswer = async () => {
        try {
            const values = await form.validateFields()
            const token = localStorage.getItem('token')

            await axios.post('/api/wrong-answer/record', {
                ...values,
                exam_id: selectedExam,
                subject_id: selectedSubject
            }, {
                headers: { Authorization: `Bearer ${token}` }
            })

            message.success('错题添加成功')
            setModalVisible(false)
            form.resetFields()
            fetchClassStats()
        } catch (error: any) {
            message.error('添加失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    // AI分析
    const handleAIAnalysis = async () => {
        setAnalyzing(true)
        try {
            const token = localStorage.getItem('token')
            const response = await axios.post('/api/wrong-answer/analyze', {
                class_id: selectedClass,
                exam_id: selectedExam,
                subject_id: selectedSubject
            }, {
                headers: { Authorization: `Bearer ${token}` }
            })

            setAnalysis(response.data.analysis)
            setActiveTab('analysis')
            message.success('分析完成')
        } catch (error) {
            message.error('AI分析失败')
        } finally {
            setAnalyzing(false)
        }
    }

    // 错误类型显示
    const renderErrorType = (type: string) => {
        const typeMap: { [key: string]: { color: string; text: string } } = {
            'calculation': { color: 'orange', text: '计算错误' },
            'concept': { color: 'red', text: '概念混淆' },
            'careless': { color: 'blue', text: '粗心大意' },
            'unknown': { color: 'purple', text: '不会做' },
            'other': { color: 'default', text: '其他' }
        }
        const info = typeMap[type] || { color: 'default', text: type || '未分类' }
        return <Tag color={info.color}>{info.text}</Tag>
    }

    return (
        <div style={{ padding: 24 }}>
            <Card
                title={
                    <Space>
                        <FileSearchOutlined />
                        <span>错题分析</span>
                    </Space>
                }
                extra={
                    <Space>
                        <Select
                            style={{ width: 150 }}
                            placeholder="选择班级"
                            value={selectedClass}
                            onChange={setSelectedClass}
                        >
                            {classes.map(c => (
                                <Option key={c.id} value={c.id}>{c.name}</Option>
                            ))}
                        </Select>
                        <Select
                            style={{ width: 180 }}
                            placeholder="选择考试"
                            value={selectedExam}
                            onChange={setSelectedExam}
                            allowClear
                        >
                            {exams.map(e => (
                                <Option key={e.id} value={e.id}>{e.name}</Option>
                            ))}
                        </Select>
                        <Button icon={<ReloadOutlined />} onClick={fetchClassStats}>刷新</Button>
                        <Button
                            type="primary"
                            icon={<RobotOutlined />}
                            onClick={handleAIAnalysis}
                            loading={analyzing}
                        >
                            AI分析
                        </Button>
                        <Button icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>
                            添加错题
                        </Button>
                    </Space>
                }
            >
                <Tabs activeKey={activeTab} onChange={setActiveTab}>
                    <TabPane tab="统计概览" key="stats">
                        {classStats ? (
                            <>
                                <Row gutter={16} style={{ marginBottom: 24 }}>
                                    <Col span={8}>
                                        <Card title="知识点错误排行" size="small">
                                            {classStats.knowledge_stats.length > 0 ? (
                                                classStats.knowledge_stats.slice(0, 5).map((item, index) => (
                                                    <div key={index} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                                                        <Text>{item.knowledge_point || '未分类'}</Text>
                                                        <Tag color="red">{item.count}道</Tag>
                                                    </div>
                                                ))
                                            ) : (
                                                <Empty description="暂无数据" />
                                            )}
                                        </Card>
                                    </Col>
                                    <Col span={8}>
                                        <Card title="错误类型分布" size="small">
                                            {classStats.error_type_stats.length > 0 ? (
                                                classStats.error_type_stats.map((item, index) => (
                                                    <div key={index} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                                                        {renderErrorType(item.error_type)}
                                                        <Text strong>{item.count}道</Text>
                                                    </div>
                                                ))
                                            ) : (
                                                <Empty description="暂无数据" />
                                            )}
                                        </Card>
                                    </Col>
                                    <Col span={8}>
                                        <Card title="学生错题排行" size="small">
                                            {classStats.student_stats.length > 0 ? (
                                                classStats.student_stats.slice(0, 5).map((item, index) => (
                                                    <div key={index} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                                                        <Space>
                                                            <Tag color={index < 3 ? 'volcano' : 'default'}>{index + 1}</Tag>
                                                            <Text>{item.name}</Text>
                                                        </Space>
                                                        <Text type="secondary">{item.wrong_count}道</Text>
                                                    </div>
                                                ))
                                            ) : (
                                                <Empty description="暂无数据" />
                                            )}
                                        </Card>
                                    </Col>
                                </Row>
                            </>
                        ) : (
                            <Empty description="请选择班级查看统计" />
                        )}
                    </TabPane>

                    <TabPane tab="AI分析报告" key="analysis">
                        {analysis ? (
                            <Card>
                                <div
                                    style={{
                                        whiteSpace: 'pre-wrap',
                                        lineHeight: 1.8,
                                        padding: 16,
                                        background: '#f5f5f5',
                                        borderRadius: 8
                                    }}
                                    dangerouslySetInnerHTML={{
                                        __html: analysis
                                            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                            .replace(/##\s?(.*)/g, '<h3>$1</h3>')
                                            .replace(/###\s?(.*)/g, '<h4>$1</h4>')
                                            .replace(/- (.*)/g, '<li>$1</li>')
                                    }}
                                />
                            </Card>
                        ) : (
                            <Empty
                                description="点击「AI分析」按钮生成分析报告"
                                image={Empty.PRESENTED_IMAGE_SIMPLE}
                            >
                                <Button
                                    type="primary"
                                    icon={<RobotOutlined />}
                                    onClick={handleAIAnalysis}
                                    loading={analyzing}
                                >
                                    开始分析
                                </Button>
                            </Empty>
                        )}
                    </TabPane>
                </Tabs>
            </Card>

            {/* 添加错题模态框 */}
            <Modal
                title="添加错题"
                open={modalVisible}
                onOk={handleAddWrongAnswer}
                onCancel={() => {
                    setModalVisible(false)
                    form.resetFields()
                }}
                okText="添加"
                cancelText="取消"
                width={600}
            >
                <Form form={form} layout="vertical">
                    <Row gutter={16}>
                        <Col span={12}>
                            <Form.Item
                                name="student_id"
                                label="学生"
                                rules={[{ required: true, message: '请选择学生' }]}
                            >
                                <Select placeholder="选择学生" showSearch optionFilterProp="children">
                                    {/* 这里需要加载学生列表 */}
                                </Select>
                            </Form.Item>
                        </Col>
                        <Col span={12}>
                            <Form.Item name="question_number" label="题号">
                                <InputNumber min={1} style={{ width: '100%' }} placeholder="如: 5" />
                            </Form.Item>
                        </Col>
                    </Row>
                    <Form.Item
                        name="question_content"
                        label="题目内容"
                        rules={[{ required: true, message: '请输入题目内容' }]}
                    >
                        <TextArea rows={3} placeholder="输入题目内容" />
                    </Form.Item>
                    <Row gutter={16}>
                        <Col span={12}>
                            <Form.Item name="correct_answer" label="正确答案">
                                <Input placeholder="正确答案" />
                            </Form.Item>
                        </Col>
                        <Col span={12}>
                            <Form.Item name="student_answer" label="学生答案">
                                <Input placeholder="学生的错误答案" />
                            </Form.Item>
                        </Col>
                    </Row>
                    <Row gutter={16}>
                        <Col span={12}>
                            <Form.Item name="knowledge_point" label="知识点">
                                <Input placeholder="如: 分数加减法" />
                            </Form.Item>
                        </Col>
                        <Col span={12}>
                            <Form.Item name="error_type" label="错误类型">
                                <Select placeholder="选择错误类型">
                                    <Option value="calculation">计算错误</Option>
                                    <Option value="concept">概念混淆</Option>
                                    <Option value="careless">粗心大意</Option>
                                    <Option value="unknown">不会做</Option>
                                    <Option value="other">其他</Option>
                                </Select>
                            </Form.Item>
                        </Col>
                    </Row>
                </Form>
            </Modal>
        </div>
    )
}

export default WrongAnswerAnalysis
