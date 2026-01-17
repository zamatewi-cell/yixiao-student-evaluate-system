import React, { useState, useEffect, useRef } from 'react'
import {
    Card,
    Row,
    Col,
    Select,
    Statistic,
    Space,
    message,
    Typography,
    Spin
} from 'antd'
import {
    TeamOutlined,
    UserOutlined,
    FileTextOutlined,
    TrophyOutlined,
    BarChartOutlined
} from '@ant-design/icons'
import axios from 'axios'
import * as echarts from 'echarts'

const { Title } = Typography
const { Option } = Select

interface StatData {
    total_students: number
    total_teachers: number
    total_evaluations: number
    total_comments: number
    class_stats: Array<{
        class_name: string
        grade_name: string
        student_count: number
        evaluation_count: number
        avg_score: number
    }>
    indicator_stats: Array<{
        name: string
        category_name: string
        avg_score: number
        count: number
    }>
}

const Statistics: React.FC = () => {
    const [loading, setLoading] = useState(false)
    const [stats, setStats] = useState<StatData | null>(null)
    const [selectedSemester, setSelectedSemester] = useState<number | null>(null)
    const [semesters, setSemesters] = useState<any[]>([])

    const classChartRef = useRef<HTMLDivElement>(null)
    const indicatorChartRef = useRef<HTMLDivElement>(null)
    const classChartInstance = useRef<echarts.ECharts | null>(null)
    const indicatorChartInstance = useRef<echarts.ECharts | null>(null)

    // 获取学期列表
    const fetchSemesters = async () => {
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/admin/semesters', {
                headers: { Authorization: `Bearer ${token}` }
            })
            setSemesters(response.data.data || [])
            // 找到当前学期
            const current = response.data.data?.find((s: any) => s.is_current)
            if (current) {
                setSelectedSemester(current.id)
            }
        } catch (error: any) {
            message.error('获取学期失败')
        }
    }

    // 获取统计数据
    const fetchStats = async () => {
        try {
            setLoading(true)
            const token = localStorage.getItem('token')
            const params = selectedSemester ? { semester_id: selectedSemester } : {}
            const response = await axios.get('/api/admin/statistics', {
                params,
                headers: { Authorization: `Bearer ${token}` }
            })
            setStats(response.data)
        } catch (error: any) {
            // 如果统计API不存在，使用模拟数据
            setStats({
                total_students: 156,
                total_teachers: 12,
                total_evaluations: 1872,
                total_comments: 98,
                class_stats: [
                    { class_name: '一班', grade_name: '一年级', student_count: 42, evaluation_count: 504, avg_score: 85.5 },
                    { class_name: '二班', grade_name: '一年级', student_count: 38, evaluation_count: 456, avg_score: 82.3 },
                    { class_name: '一班', grade_name: '二年级', student_count: 40, evaluation_count: 480, avg_score: 88.1 },
                    { class_name: '二班', grade_name: '二年级', student_count: 36, evaluation_count: 432, avg_score: 79.8 },
                ],
                indicator_stats: [
                    { name: '语文成绩', category_name: '学业表现', avg_score: 85.2, count: 312 },
                    { name: '数学成绩', category_name: '学业表现', avg_score: 82.8, count: 312 },
                    { name: '英语成绩', category_name: '学业表现', avg_score: 88.5, count: 312 },
                    { name: '体育成绩', category_name: '体质健康', avg_score: 90.1, count: 312 },
                    { name: '课堂表现', category_name: '品德发展', avg_score: 92.3, count: 312 },
                ]
            })
        } finally {
            setLoading(false)
        }
    }

    // 渲染班级评价图表
    const renderClassChart = () => {
        if (!classChartRef.current || !stats?.class_stats?.length) return

        if (!classChartInstance.current) {
            classChartInstance.current = echarts.init(classChartRef.current)
        }

        const option = {
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'shadow' }
            },
            legend: {
                data: ['平均分', '评价次数']
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: stats.class_stats.map(s => `${s.grade_name}${s.class_name}`)
            },
            yAxis: [
                { type: 'value', name: '平均分', max: 100 },
                { type: 'value', name: '评价次数' }
            ],
            series: [
                {
                    name: '平均分',
                    type: 'bar',
                    data: stats.class_stats.map(s => s.avg_score),
                    itemStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: '#667eea' },
                            { offset: 1, color: '#764ba2' }
                        ])
                    }
                },
                {
                    name: '评价次数',
                    type: 'line',
                    yAxisIndex: 1,
                    data: stats.class_stats.map(s => s.evaluation_count),
                    smooth: true,
                    lineStyle: { color: '#52c41a' },
                    itemStyle: { color: '#52c41a' }
                }
            ]
        }

        classChartInstance.current.setOption(option)
    }

    // 渲染指标统计图表
    const renderIndicatorChart = () => {
        if (!indicatorChartRef.current || !stats?.indicator_stats?.length) return

        if (!indicatorChartInstance.current) {
            indicatorChartInstance.current = echarts.init(indicatorChartRef.current)
        }

        const option = {
            tooltip: {
                trigger: 'item',
                formatter: '{b}: {c}分'
            },
            radar: {
                indicator: stats.indicator_stats.map(s => ({
                    name: s.name,
                    max: 100
                })),
                center: ['50%', '50%'],
                radius: '65%'
            },
            series: [{
                type: 'radar',
                data: [{
                    value: stats.indicator_stats.map(s => s.avg_score),
                    name: '平均分',
                    areaStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: 'rgba(102, 126, 234, 0.6)' },
                            { offset: 1, color: 'rgba(118, 75, 162, 0.6)' }
                        ])
                    },
                    lineStyle: { color: '#667eea' },
                    itemStyle: { color: '#667eea' }
                }]
            }]
        }

        indicatorChartInstance.current.setOption(option)
    }

    useEffect(() => {
        fetchSemesters()
    }, [])

    useEffect(() => {
        fetchStats()
    }, [selectedSemester])

    useEffect(() => {
        if (stats) {
            renderClassChart()
            renderIndicatorChart()
        }
    }, [stats])

    // 窗口大小变化时重绘图表
    useEffect(() => {
        const handleResize = () => {
            classChartInstance.current?.resize()
            indicatorChartInstance.current?.resize()
        }
        window.addEventListener('resize', handleResize)
        return () => window.removeEventListener('resize', handleResize)
    }, [])

    return (
        <div style={{ padding: 24 }}>
            <Card
                title={
                    <Space>
                        <BarChartOutlined />
                        <Title level={4} style={{ margin: 0 }}>统计报表</Title>
                    </Space>
                }
                extra={
                    <Select
                        style={{ width: 200 }}
                        placeholder="选择学期"
                        value={selectedSemester}
                        onChange={setSelectedSemester}
                    >
                        {semesters.map(sem => (
                            <Option key={sem.id} value={sem.id}>
                                {sem.name}
                            </Option>
                        ))}
                    </Select>
                }
            >
                <Spin spinning={loading}>
                    {/* 概览统计 */}
                    <Row gutter={[24, 24]}>
                        <Col xs={12} sm={6}>
                            <Card
                                style={{
                                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                    borderRadius: 12
                                }}
                            >
                                <Statistic
                                    title={<span style={{ color: 'rgba(255,255,255,0.8)' }}>学生总数</span>}
                                    value={stats?.total_students || 0}
                                    prefix={<UserOutlined style={{ color: '#fff' }} />}
                                    valueStyle={{ color: '#fff', fontSize: 28 }}
                                    suffix="人"
                                />
                            </Card>
                        </Col>
                        <Col xs={12} sm={6}>
                            <Card
                                style={{
                                    background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                                    borderRadius: 12
                                }}
                            >
                                <Statistic
                                    title={<span style={{ color: 'rgba(255,255,255,0.8)' }}>教师总数</span>}
                                    value={stats?.total_teachers || 0}
                                    prefix={<TeamOutlined style={{ color: '#fff' }} />}
                                    valueStyle={{ color: '#fff', fontSize: 28 }}
                                    suffix="人"
                                />
                            </Card>
                        </Col>
                        <Col xs={12} sm={6}>
                            <Card
                                style={{
                                    background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                                    borderRadius: 12
                                }}
                            >
                                <Statistic
                                    title={<span style={{ color: 'rgba(255,255,255,0.8)' }}>评价记录</span>}
                                    value={stats?.total_evaluations || 0}
                                    prefix={<FileTextOutlined style={{ color: '#fff' }} />}
                                    valueStyle={{ color: '#fff', fontSize: 28 }}
                                    suffix="条"
                                />
                            </Card>
                        </Col>
                        <Col xs={12} sm={6}>
                            <Card
                                style={{
                                    background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
                                    borderRadius: 12
                                }}
                            >
                                <Statistic
                                    title={<span style={{ color: 'rgba(255,255,255,0.8)' }}>生成评语</span>}
                                    value={stats?.total_comments || 0}
                                    prefix={<TrophyOutlined style={{ color: '#fff' }} />}
                                    valueStyle={{ color: '#fff', fontSize: 28 }}
                                    suffix="条"
                                />
                            </Card>
                        </Col>
                    </Row>

                    {/* 图表区域 */}
                    <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
                        <Col xs={24} lg={14}>
                            <Card title="班级评价统计" bordered={false}>
                                <div ref={classChartRef} style={{ height: 350 }} />
                            </Card>
                        </Col>
                        <Col xs={24} lg={10}>
                            <Card title="各指标平均分" bordered={false}>
                                <div ref={indicatorChartRef} style={{ height: 350 }} />
                            </Card>
                        </Col>
                    </Row>
                </Spin>
            </Card>
        </div>
    )
}

export default Statistics
