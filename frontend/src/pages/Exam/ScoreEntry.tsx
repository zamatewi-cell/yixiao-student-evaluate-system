import React, { useState, useEffect, useCallback } from 'react'
import {
    Card, Table, Button, Select, message, Space, InputNumber, Tag, Typography, Alert
} from 'antd'
import {
    SaveOutlined, ReloadOutlined, EditOutlined
} from '@ant-design/icons'
import axios from 'axios'

const { Option } = Select
const { Text } = Typography

interface Student {
    student_id: number
    student_no: string
    student_name: string
    gender: string
    class_name: string
    grade_name: string
    score: number | null
    class_rank: number | null
    grade_rank: number | null
}

interface Subject {
    id: number
    subject_name: string
    full_score: number
    pass_score: number
    excellent_score: number
}

const ScoreEntry: React.FC = () => {
    const [loading, setLoading] = useState(false)
    const [saving, setSaving] = useState(false)
    const [exams, setExams] = useState<any[]>([])
    const [classes, setClasses] = useState<any[]>([])
    const [subjects, setSubjects] = useState<Subject[]>([])
    const [students, setStudents] = useState<Student[]>([])
    const [selectedExam, setSelectedExam] = useState<number | null>(null)
    const [selectedClass, setSelectedClass] = useState<number | null>(null)
    const [selectedSubject, setSelectedSubject] = useState<number | null>(null)
    const [modifiedScores, setModifiedScores] = useState<{ [key: number]: number }>({})

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
        } catch (error) {
            message.error('获取班级列表失败')
        }
    }, [])

    // 获取考试科目
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

    // 获取成绩数据
    const fetchScores = useCallback(async () => {
        if (!selectedExam || !selectedSubject) return

        setLoading(true)
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get(`/api/exam/scores/${selectedExam}/${selectedSubject}`, {
                headers: { Authorization: `Bearer ${token}` },
                params: selectedClass ? { class_id: selectedClass } : {}
            })
            setStudents(response.data.data || [])
            setModifiedScores({})
        } catch (error) {
            message.error('获取成绩数据失败')
        } finally {
            setLoading(false)
        }
    }, [selectedExam, selectedSubject, selectedClass])

    useEffect(() => {
        fetchExams()
        fetchClasses()
    }, [fetchExams, fetchClasses])

    useEffect(() => {
        if (selectedExam) {
            fetchSubjects(selectedExam)
            setSelectedSubject(null)
            setStudents([])
        }
    }, [selectedExam, fetchSubjects])

    useEffect(() => {
        fetchScores()
    }, [fetchScores])

    // 更新分数
    const handleScoreChange = (studentId: number, value: number | null) => {
        if (value !== null) {
            setModifiedScores(prev => ({ ...prev, [studentId]: value }))
            setStudents(prev => prev.map(s =>
                s.student_id === studentId ? { ...s, score: value } : s
            ))
        }
    }

    // 保存成绩
    const handleSave = async () => {
        if (!selectedExam || !selectedSubject) {
            message.warning('请选择考试和科目')
            return
        }

        const scoresToSave = Object.entries(modifiedScores).map(([studentId, score]) => ({
            student_id: parseInt(studentId),
            score
        }))

        if (scoresToSave.length === 0) {
            message.info('没有需要保存的成绩')
            return
        }

        setSaving(true)
        try {
            const token = localStorage.getItem('token')
            await axios.post('/api/exam/scores/input', {
                exam_id: selectedExam,
                subject_id: selectedSubject,
                scores: scoresToSave
            }, {
                headers: { Authorization: `Bearer ${token}` }
            })

            message.success(`成功保存 ${scoresToSave.length} 条成绩`)
            setModifiedScores({})
            fetchScores()
        } catch (error: any) {
            message.error('保存失败: ' + (error.response?.data?.detail || error.message))
        } finally {
            setSaving(false)
        }
    }

    // 获取当前科目信息
    const currentSubject = subjects.find(s => s.id === selectedSubject)

    // 分数状态样式
    const getScoreStyle = (score: number | null) => {
        if (score === null) return {}
        if (currentSubject) {
            if (score >= currentSubject.excellent_score) return { color: '#52c41a', fontWeight: 'bold' }
            if (score >= currentSubject.pass_score) return { color: '#1890ff' }
            return { color: '#ff4d4f' }
        }
        return {}
    }

    const columns = [
        {
            title: '学号',
            dataIndex: 'student_no',
            key: 'student_no',
            width: 100,
            fixed: 'left' as const
        },
        {
            title: '姓名',
            dataIndex: 'student_name',
            key: 'student_name',
            width: 80,
            fixed: 'left' as const
        },
        {
            title: '班级',
            dataIndex: 'class_name',
            key: 'class_name',
            width: 100
        },
        {
            title: '成绩',
            dataIndex: 'score',
            key: 'score',
            width: 120,
            render: (score: number | null, record: Student) => (
                <InputNumber
                    value={score}
                    min={0}
                    max={currentSubject?.full_score || 100}
                    precision={1}
                    style={{ width: 80, ...getScoreStyle(score) }}
                    onChange={(value) => handleScoreChange(record.student_id, value)}
                />
            )
        },
        {
            title: '等级',
            key: 'level',
            width: 80,
            render: (_: any, record: Student) => {
                const score = record.score
                if (score === null) return <Tag>未录入</Tag>
                if (currentSubject) {
                    if (score >= currentSubject.excellent_score) return <Tag color="gold">优秀</Tag>
                    if (score >= currentSubject.pass_score) return <Tag color="blue">及格</Tag>
                    return <Tag color="red">不及格</Tag>
                }
                return null
            }
        },
        {
            title: '班级排名',
            dataIndex: 'class_rank',
            key: 'class_rank',
            width: 90,
            align: 'center' as const,
            render: (rank: number | null) => rank ? <Text strong>{rank}</Text> : '-'
        },
        {
            title: '年级排名',
            dataIndex: 'grade_rank',
            key: 'grade_rank',
            width: 90,
            align: 'center' as const,
            render: (rank: number | null) => rank ? <Text type="secondary">{rank}</Text> : '-'
        }
    ]

    // 统计信息
    const getStats = () => {
        const validScores = students.filter(s => s.score !== null)
        if (validScores.length === 0) return null

        const scores = validScores.map(s => s.score as number)
        const avg = scores.reduce((a, b) => a + b, 0) / scores.length
        const max = Math.max(...scores)
        const min = Math.min(...scores)
        const passCount = currentSubject ? scores.filter(s => s >= currentSubject.pass_score).length : 0
        const excellentCount = currentSubject ? scores.filter(s => s >= currentSubject.excellent_score).length : 0

        return {
            count: validScores.length,
            avg: avg.toFixed(1),
            max,
            min,
            passRate: ((passCount / validScores.length) * 100).toFixed(1),
            excellentRate: ((excellentCount / validScores.length) * 100).toFixed(1)
        }
    }

    const stats = getStats()

    return (
        <div style={{ padding: 24 }}>
            <Card
                title={
                    <Space>
                        <EditOutlined />
                        <span>成绩录入</span>
                    </Space>
                }
                extra={
                    <Space>
                        <Select
                            style={{ width: 200 }}
                            placeholder="选择考试"
                            value={selectedExam}
                            onChange={setSelectedExam}
                            showSearch
                            optionFilterProp="children"
                        >
                            {exams.map(e => (
                                <Option key={e.id} value={e.id}>{e.name}</Option>
                            ))}
                        </Select>
                        <Select
                            style={{ width: 120 }}
                            placeholder="选择科目"
                            value={selectedSubject}
                            onChange={setSelectedSubject}
                            disabled={!selectedExam || subjects.length === 0}
                        >
                            {subjects.map(s => (
                                <Option key={s.id} value={s.id}>{s.subject_name}</Option>
                            ))}
                        </Select>
                        <Select
                            style={{ width: 120 }}
                            placeholder="选择班级"
                            value={selectedClass}
                            onChange={setSelectedClass}
                            allowClear
                        >
                            {classes.map(c => (
                                <Option key={c.id} value={c.id}>{c.name}</Option>
                            ))}
                        </Select>
                        <Button icon={<ReloadOutlined />} onClick={fetchScores}>刷新</Button>
                        <Button
                            type="primary"
                            icon={<SaveOutlined />}
                            onClick={handleSave}
                            loading={saving}
                            disabled={Object.keys(modifiedScores).length === 0}
                        >
                            保存 {Object.keys(modifiedScores).length > 0 && `(${Object.keys(modifiedScores).length})`}
                        </Button>
                    </Space>
                }
            >
                {currentSubject && (
                    <Alert
                        message={
                            <Space split={<span>|</span>}>
                                <span>科目：<strong>{currentSubject.subject_name}</strong></span>
                                <span>满分：<strong>{currentSubject.full_score}</strong></span>
                                <span>及格：<strong>{currentSubject.pass_score}</strong></span>
                                <span>优秀：<strong>{currentSubject.excellent_score}</strong></span>
                                {stats && (
                                    <>
                                        <span>已录入：<strong>{stats.count}人</strong></span>
                                        <span>平均分：<strong>{stats.avg}</strong></span>
                                        <span>及格率：<strong>{stats.passRate}%</strong></span>
                                        <span>优秀率：<strong>{stats.excellentRate}%</strong></span>
                                    </>
                                )}
                            </Space>
                        }
                        type="info"
                        style={{ marginBottom: 16 }}
                    />
                )}

                <Table
                    dataSource={students}
                    columns={columns}
                    rowKey="student_id"
                    loading={loading}
                    pagination={{ pageSize: 50, showTotal: (total) => `共 ${total} 人` }}
                    size="middle"
                    scroll={{ x: 800 }}
                    rowClassName={(record) => {
                        if (modifiedScores[record.student_id] !== undefined) {
                            return 'modified-row'
                        }
                        return ''
                    }}
                />
            </Card>

            <style>{`
                .modified-row {
                    background-color: #e6f7ff !important;
                }
            `}</style>
        </div>
    )
}

export default ScoreEntry
