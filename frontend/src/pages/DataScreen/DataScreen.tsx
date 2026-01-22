import React, { useState, useEffect, useCallback } from 'react'
import { Card, Row, Col, Statistic, Progress, Table, Tag, Typography, Space, Spin } from 'antd'
import {
    TeamOutlined,
    TrophyOutlined,
    CheckCircleOutlined,
    ClockCircleOutlined,
    UserOutlined,
    BarChartOutlined
} from '@ant-design/icons'
import axios from 'axios'

const { Title, Text } = Typography

interface GradeStats {
    grade_id: number
    grade_name: string
    total_students: number
    present_count: number
    absent_count: number
    attendance_rate: number
}

interface ClassAttendance {
    class_id: number
    class_name: string
    total_students: number
    present_count: number
    absent_count: number
    late_count: number
    sick_leave_count: number
    personal_leave_count: number
    attendance_rate: number
}

const DataScreen: React.FC = () => {
    const [loading, setLoading] = useState(true)
    const [currentTime, setCurrentTime] = useState(new Date())
    const [selectedGrade, setSelectedGrade] = useState<number | null>(null)
    const [gradeStats, setGradeStats] = useState<GradeStats[]>([])
    const [classAttendance, setClassAttendance] = useState<ClassAttendance[]>([])
    const [schoolStats, setSchoolStats] = useState<any>(null)

    // 更新时间
    useEffect(() => {
        const timer = setInterval(() => {
            setCurrentTime(new Date())
        }, 1000)
        return () => clearInterval(timer)
    }, [])

    // 获取考勤数据
    const fetchAttendanceData = useCallback(async () => {
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/attendance/dashboard', {
                headers: { Authorization: `Bearer ${token}` }
            })
            setSchoolStats(response.data.data.school_stats)
            setGradeStats(response.data.data.grade_stats || [])
        } catch (error) {
            console.error('获取考勤数据失败:', error)
        }
    }, [])

    // 获取年级考勤详情
    const fetchGradeAttendance = useCallback(async (gradeId: number) => {
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get(`/api/attendance/statistics/grade/${gradeId}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            setClassAttendance(response.data.data || [])
        } catch (error) {
            console.error('获取年级考勤失败:', error)
        }
    }, [])

    // 初始化数据
    useEffect(() => {
        const init = async () => {
            setLoading(true)
            await fetchAttendanceData()
            setLoading(false)
        }
        init()

        // 每5分钟刷新一次
        const refreshTimer = setInterval(fetchAttendanceData, 5 * 60 * 1000)
        return () => clearInterval(refreshTimer)
    }, [fetchAttendanceData])

    // 选择年级后获取详情
    useEffect(() => {
        if (selectedGrade) {
            fetchGradeAttendance(selectedGrade)
        }
    }, [selectedGrade, fetchGradeAttendance])

    // 格式化时间
    const formatTime = (date: Date) => {
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            weekday: 'long'
        })
    }

    // 计算全校出勤率
    const getSchoolAttendanceRate = () => {
        if (!schoolStats) return 0
        const total = schoolStats.total_students || 0
        const present = schoolStats.present_count || 0
        return total > 0 ? Math.round(present / total * 100) : 0
    }

    // 考勤状态列配置
    const attendanceColumns = [
        {
            title: '班级',
            dataIndex: 'class_name',
            key: 'class_name',
            render: (text: string) => <Text strong>{text}</Text>
        },
        {
            title: '学生总数',
            dataIndex: 'total_students',
            key: 'total_students',
            align: 'center' as const
        },
        {
            title: '出勤',
            dataIndex: 'present_count',
            key: 'present_count',
            align: 'center' as const,
            render: (v: number) => <Tag color="success">{v || 0}</Tag>
        },
        {
            title: '缺勤',
            dataIndex: 'absent_count',
            key: 'absent_count',
            align: 'center' as const,
            render: (v: number) => v > 0 ? <Tag color="error">{v}</Tag> : <span>0</span>
        },
        {
            title: '迟到',
            dataIndex: 'late_count',
            key: 'late_count',
            align: 'center' as const,
            render: (v: number) => v > 0 ? <Tag color="warning">{v}</Tag> : <span>0</span>
        },
        {
            title: '病假',
            dataIndex: 'sick_leave_count',
            key: 'sick_leave_count',
            align: 'center' as const,
            render: (v: number) => v > 0 ? <Tag color="blue">{v}</Tag> : <span>0</span>
        },
        {
            title: '事假',
            dataIndex: 'personal_leave_count',
            key: 'personal_leave_count',
            align: 'center' as const,
            render: (v: number) => v > 0 ? <Tag color="purple">{v}</Tag> : <span>0</span>
        },
        {
            title: '出勤率',
            dataIndex: 'attendance_rate',
            key: 'attendance_rate',
            align: 'center' as const,
            render: (rate: number) => (
                <Progress
                    percent={rate || 0}
                    size="small"
                    status={rate >= 95 ? 'success' : rate >= 85 ? 'normal' : 'exception'}
                    format={(percent) => `${percent}%`}
                />
            )
        }
    ]

    if (loading) {
        return (
            <div style={{
                height: '100vh',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)'
            }}>
                <Spin size="large" />
            </div>
        )
    }

    return (
        <div style={{
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
            padding: 24,
            color: '#fff'
        }}>
            {/* 标题栏 */}
            <div style={{
                textAlign: 'center',
                marginBottom: 32,
                padding: '16px 0',
                background: 'rgba(255,255,255,0.05)',
                borderRadius: 12
            }}>
                <Title level={2} style={{
                    margin: 0,
                    color: '#fff',
                    background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    fontSize: 36
                }}>
                    📊 学生综合素质评价系统 - 数据大屏
                </Title>
                <Text style={{ color: 'rgba(255,255,255,0.7)', fontSize: 18 }}>
                    {formatTime(currentTime)}
                </Text>
            </div>

            {/* 统计卡片 */}
            <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
                <Col xs={24} sm={12} md={6}>
                    <Card
                        style={{
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            border: 'none',
                            borderRadius: 12
                        }}
                    >
                        <Statistic
                            title={<span style={{ color: 'rgba(255,255,255,0.8)' }}>学生总数</span>}
                            value={schoolStats?.total_students || 0}
                            prefix={<TeamOutlined />}
                            valueStyle={{ color: '#fff', fontSize: 32 }}
                            suffix="人"
                        />
                    </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                    <Card
                        style={{
                            background: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
                            border: 'none',
                            borderRadius: 12
                        }}
                    >
                        <Statistic
                            title={<span style={{ color: 'rgba(255,255,255,0.8)' }}>今日出勤</span>}
                            value={schoolStats?.present_count || 0}
                            prefix={<CheckCircleOutlined />}
                            valueStyle={{ color: '#fff', fontSize: 32 }}
                            suffix="人"
                        />
                    </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                    <Card
                        style={{
                            background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                            border: 'none',
                            borderRadius: 12
                        }}
                    >
                        <Statistic
                            title={<span style={{ color: 'rgba(255,255,255,0.8)' }}>今日请假</span>}
                            value={(schoolStats?.sick_leave_count || 0) + (schoolStats?.personal_leave_count || 0)}
                            prefix={<ClockCircleOutlined />}
                            valueStyle={{ color: '#fff', fontSize: 32 }}
                            suffix="人"
                        />
                    </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                    <Card
                        style={{
                            background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                            border: 'none',
                            borderRadius: 12
                        }}
                    >
                        <Statistic
                            title={<span style={{ color: 'rgba(255,255,255,0.8)' }}>全校出勤率</span>}
                            value={getSchoolAttendanceRate()}
                            prefix={<BarChartOutlined />}
                            valueStyle={{ color: '#fff', fontSize: 32 }}
                            suffix="%"
                        />
                    </Card>
                </Col>
            </Row>

            {/* 年级出勤率概览 */}
            <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
                <Col span={24}>
                    <Card
                        title={
                            <Space>
                                <TrophyOutlined style={{ color: '#ffc107' }} />
                                <span style={{ color: '#fff' }}>各年级出勤率</span>
                            </Space>
                        }
                        style={{
                            background: 'rgba(255,255,255,0.05)',
                            border: '1px solid rgba(255,255,255,0.1)',
                            borderRadius: 12
                        }}
                        headStyle={{
                            background: 'rgba(255,255,255,0.05)',
                            borderBottom: '1px solid rgba(255,255,255,0.1)',
                            color: '#fff'
                        }}
                        bodyStyle={{ padding: 16 }}
                    >
                        <Row gutter={16}>
                            {gradeStats.map(grade => (
                                <Col key={grade.grade_id} xs={12} sm={8} md={4}>
                                    <div
                                        style={{
                                            textAlign: 'center',
                                            padding: 16,
                                            background: selectedGrade === grade.grade_id
                                                ? 'rgba(102, 126, 234, 0.3)'
                                                : 'rgba(255,255,255,0.05)',
                                            borderRadius: 8,
                                            cursor: 'pointer',
                                            transition: 'all 0.3s',
                                            border: selectedGrade === grade.grade_id
                                                ? '2px solid #667eea'
                                                : '2px solid transparent'
                                        }}
                                        onClick={() => setSelectedGrade(grade.grade_id)}
                                    >
                                        <Text strong style={{ color: '#fff', fontSize: 16, display: 'block' }}>
                                            {grade.grade_name}
                                        </Text>
                                        <div style={{ margin: '12px 0' }}>
                                            <Progress
                                                type="circle"
                                                percent={grade.attendance_rate || 0}
                                                width={80}
                                                strokeColor={
                                                    grade.attendance_rate >= 95 ? '#52c41a' :
                                                        grade.attendance_rate >= 85 ? '#1890ff' : '#ff4d4f'
                                                }
                                                format={(percent) => (
                                                    <span style={{ color: '#fff', fontSize: 16 }}>{percent}%</span>
                                                )}
                                            />
                                        </div>
                                        <Text style={{ color: 'rgba(255,255,255,0.6)' }}>
                                            {grade.total_students}人
                                        </Text>
                                    </div>
                                </Col>
                            ))}
                        </Row>
                    </Card>
                </Col>
            </Row>

            {/* 班级考勤详情 */}
            {selectedGrade && (
                <Row gutter={[24, 24]}>
                    <Col span={24}>
                        <Card
                            title={
                                <Space>
                                    <UserOutlined style={{ color: '#52c41a' }} />
                                    <span style={{ color: '#fff' }}>
                                        {gradeStats.find(g => g.grade_id === selectedGrade)?.grade_name || ''} 班级考勤详情
                                    </span>
                                </Space>
                            }
                            style={{
                                background: 'rgba(255,255,255,0.05)',
                                border: '1px solid rgba(255,255,255,0.1)',
                                borderRadius: 12
                            }}
                            headStyle={{
                                background: 'rgba(255,255,255,0.05)',
                                borderBottom: '1px solid rgba(255,255,255,0.1)',
                                color: '#fff'
                            }}
                        >
                            <Table
                                dataSource={classAttendance}
                                columns={attendanceColumns}
                                rowKey="class_id"
                                pagination={false}
                                size="middle"
                                style={{
                                    background: 'transparent'
                                }}
                            />
                        </Card>
                    </Col>
                </Row>
            )}
        </div>
    )
}

export default DataScreen
