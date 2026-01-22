import { useEffect, useState, useRef } from 'react'
import { Row, Col, Card, Statistic, Typography, Space, Button, List, Tag, Avatar, Progress, Divider, Empty } from 'antd'
import {
    UserOutlined,
    TeamOutlined,
    FormOutlined,
    CommentOutlined,
    EditOutlined,
    RightOutlined,
    CalendarOutlined,
    BookOutlined,
    CheckCircleOutlined,
    ClockCircleOutlined,
    ExclamationCircleOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import axios from 'axios'
import * as echarts from 'echarts'

const { Title, Text, Paragraph } = Typography

interface ClassInfo {
    id: number
    name: string
    grade_name: string
    student_count: number
}

interface TaskItem {
    key: string
    title: string
    description: string
    status: 'pending' | 'completed' | 'urgent'
    link: string
}

const TeacherDashboard = () => {
    const { user } = useAuthStore()
    const navigate = useNavigate()
    const [loading, setLoading] = useState(true)
    const [teacherInfo, setTeacherInfo] = useState<any>(null)
    const [myClasses, setMyClasses] = useState<ClassInfo[]>([])
    const [currentSemester, setCurrentSemester] = useState<string>('')
    const [stats, setStats] = useState({
        total_students: 0,
        total_evaluations: 0,
        pending_comments: 0,
        calligraphy_graded: 0,
    })

    const chartRef = useRef<HTMLDivElement>(null)
    const chartInstance = useRef<echarts.ECharts | null>(null)

    useEffect(() => {
        loadTeacherData()
    }, [])

    const loadTeacherData = async () => {
        const token = localStorage.getItem('token')
        const headers = { Authorization: `Bearer ${token}` }

        try {
            // 获取教师信息
            try {
                const profileRes = await axios.get('/api/teacher/profile', { headers })
                setTeacherInfo(profileRes.data)
            } catch {
                setTeacherInfo({ name: user?.real_name, subjects: '综合' })
            }

            // 获取我的班级
            try {
                const classesRes = await axios.get('/api/teacher/my-classes', { headers })
                const classes = classesRes.data?.data || []
                setMyClasses(classes)

                // 计算统计数据
                const totalStudents = classes.reduce((sum: number, c: ClassInfo) => sum + (c.student_count || 0), 0)
                setStats(prev => ({ ...prev, total_students: totalStudents }))
            } catch {
                // 如果没有分配班级，尝试获取所有班级（管理员兼教师）
                try {
                    const allClassesRes = await axios.get('/api/admin/classes', { headers })
                    const classes = allClassesRes.data?.data || []
                    setMyClasses(classes.slice(0, 6)) // 最多显示6个
                    const totalStudents = classes.reduce((sum: number, c: ClassInfo) => sum + (c.student_count || 0), 0)
                    setStats(prev => ({ ...prev, total_students: totalStudents }))
                } catch {
                    setMyClasses([])
                }
            }

            // 获取当前学期
            try {
                const semRes = await axios.get('/api/teacher/current-semester', { headers })
                if (semRes.data?.data) {
                    setCurrentSemester(semRes.data.data.name)
                }
            } catch {
                setCurrentSemester('未设置当前学期')
            }
        } catch (error) {
            console.error('加载教师数据失败:', error)
        } finally {
            setLoading(false)
        }
    }

    // 渲染工作进度图表
    useEffect(() => {
        if (!chartRef.current || loading) return

        if (!chartInstance.current) {
            chartInstance.current = echarts.init(chartRef.current)
        }

        const completedTasks = stats.total_evaluations > 0 ? 75 : 0
        const pendingTasks = 100 - completedTasks

        chartInstance.current.setOption({
            tooltip: { trigger: 'item' },
            series: [{
                type: 'pie',
                radius: ['60%', '80%'],
                avoidLabelOverlap: false,
                label: {
                    show: true,
                    position: 'center',
                    formatter: `{a|${completedTasks}%}\n{b|已完成}`,
                    rich: {
                        a: { fontSize: 28, fontWeight: 'bold', color: '#667eea' },
                        b: { fontSize: 14, color: '#999', padding: [8, 0, 0, 0] }
                    }
                },
                labelLine: { show: false },
                data: [
                    { value: completedTasks, name: '已完成', itemStyle: { color: '#667eea' } },
                    { value: pendingTasks, name: '待完成', itemStyle: { color: '#f0f0f0' } },
                ]
            }]
        })
    }, [loading, stats])

    // 待办任务列表
    const todoTasks: TaskItem[] = [
        {
            key: '1',
            title: '录入学生评价数据',
            description: '本学期学生综合素质评价数据录入',
            status: stats.total_evaluations > 0 ? 'completed' : 'pending',
            link: '/data-entry',
        },
        {
            key: '2',
            title: '生成期末评语',
            description: '为学生生成个性化期末评语',
            status: 'pending',
            link: '/comment-management',
        },
        {
            key: '3',
            title: '书法作品批改',
            description: '批改学生上传的书法作品',
            status: 'pending',
            link: '/calligraphy',
        },
        {
            key: '4',
            title: '分配书法作品',
            description: '将批改结果分配给对应学生',
            status: 'pending',
            link: '/calligraphy-assignment',
        },
    ]

    // 快捷入口
    const quickEntries = [
        { icon: <FormOutlined />, title: '数据录入', desc: '录入学生评价', path: '/data-entry', color: '#667eea' },
        { icon: <CommentOutlined />, title: '评语管理', desc: '生成管理评语', path: '/comment-management', color: '#f093fb' },
        { icon: <EditOutlined />, title: '书法批改', desc: '批改书法作品', path: '/calligraphy', color: '#4facfe' },
        { icon: <TeamOutlined />, title: '作品分配', desc: '分配给学生', path: '/calligraphy-assignment', color: '#43e97b' },
    ]

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'completed':
                return <CheckCircleOutlined style={{ color: '#52c41a' }} />
            case 'urgent':
                return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
            default:
                return <ClockCircleOutlined style={{ color: '#faad14' }} />
        }
    }

    const getStatusTag = (status: string) => {
        switch (status) {
            case 'completed':
                return <Tag color="success">已完成</Tag>
            case 'urgent':
                return <Tag color="error">紧急</Tag>
            default:
                return <Tag color="warning">待处理</Tag>
        }
    }

    return (
        <div style={{ padding: 24 }}>
            {/* 欢迎横幅 */}
            <Card
                style={{
                    marginBottom: 24,
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    border: 'none',
                    borderRadius: 16,
                }}
                bodyStyle={{ padding: '32px 40px' }}
            >
                <Row align="middle" justify="space-between">
                    <Col>
                        <Space align="start" size={24}>
                            <Avatar
                                size={80}
                                style={{
                                    backgroundColor: 'rgba(255,255,255,0.2)',
                                    fontSize: 32,
                                    border: '3px solid rgba(255,255,255,0.5)',
                                }}
                            >
                                {user?.real_name?.[0] || user?.username?.[0] || 'T'}
                            </Avatar>
                            <div>
                                <Title level={2} style={{ color: '#fff', margin: 0 }}>
                                    {getGreeting()}，{user?.real_name || user?.username || '老师'}！
                                </Title>
                                <Text style={{ color: 'rgba(255,255,255,0.85)', fontSize: 16, display: 'block', marginTop: 8 }}>
                                    <CalendarOutlined style={{ marginRight: 8 }} />
                                    当前学期：{currentSemester || '加载中...'}
                                </Text>
                                {teacherInfo?.subjects && (
                                    <Text style={{ color: 'rgba(255,255,255,0.7)', display: 'block', marginTop: 4 }}>
                                        <BookOutlined style={{ marginRight: 8 }} />
                                        任教科目：{teacherInfo.subjects}
                                    </Text>
                                )}
                            </div>
                        </Space>
                    </Col>
                    <Col>
                        <div style={{ textAlign: 'right' }}>
                            <Text style={{ color: 'rgba(255,255,255,0.7)', fontSize: 14, display: 'block' }}>
                                {new Date().toLocaleDateString('zh-CN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                            </Text>
                        </div>
                    </Col>
                </Row>
            </Card>

            {/* 统计卡片 */}
            <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
                <Col xs={12} sm={6}>
                    <Card hoverable style={{ borderRadius: 12, textAlign: 'center' }}>
                        <Statistic
                            title={<span style={{ fontSize: 14 }}>我的班级</span>}
                            value={myClasses.length}
                            prefix={<TeamOutlined style={{ color: '#667eea' }} />}
                            suffix="个"
                            valueStyle={{ color: '#667eea', fontSize: 32 }}
                        />
                    </Card>
                </Col>
                <Col xs={12} sm={6}>
                    <Card hoverable style={{ borderRadius: 12, textAlign: 'center' }}>
                        <Statistic
                            title={<span style={{ fontSize: 14 }}>学生总数</span>}
                            value={stats.total_students}
                            prefix={<UserOutlined style={{ color: '#f093fb' }} />}
                            suffix="人"
                            valueStyle={{ color: '#f093fb', fontSize: 32 }}
                        />
                    </Card>
                </Col>
                <Col xs={12} sm={6}>
                    <Card hoverable style={{ borderRadius: 12, textAlign: 'center' }}>
                        <Statistic
                            title={<span style={{ fontSize: 14 }}>评价录入</span>}
                            value={stats.total_evaluations}
                            prefix={<FormOutlined style={{ color: '#4facfe' }} />}
                            suffix="条"
                            valueStyle={{ color: '#4facfe', fontSize: 32 }}
                        />
                    </Card>
                </Col>
                <Col xs={12} sm={6}>
                    <Card hoverable style={{ borderRadius: 12, textAlign: 'center' }}>
                        <Statistic
                            title={<span style={{ fontSize: 14 }}>待办评语</span>}
                            value={stats.total_students}
                            prefix={<CommentOutlined style={{ color: '#43e97b' }} />}
                            suffix="份"
                            valueStyle={{ color: '#43e97b', fontSize: 32 }}
                        />
                    </Card>
                </Col>
            </Row>

            {/* 主内容区 */}
            <Row gutter={[24, 24]}>
                {/* 快捷入口 */}
                <Col xs={24} lg={16}>
                    <Card
                        title={<span style={{ fontSize: 16, fontWeight: 600 }}>🚀 快捷入口</span>}
                        style={{ borderRadius: 12, marginBottom: 24 }}
                    >
                        <Row gutter={[16, 16]}>
                            {quickEntries.map((entry, index) => (
                                <Col xs={12} sm={6} key={index}>
                                    <Card
                                        hoverable
                                        style={{
                                            borderRadius: 12,
                                            textAlign: 'center',
                                            cursor: 'pointer',
                                            transition: 'all 0.3s',
                                        }}
                                        bodyStyle={{ padding: '24px 16px' }}
                                        onClick={() => navigate(entry.path)}
                                    >
                                        <div
                                            style={{
                                                width: 56,
                                                height: 56,
                                                borderRadius: '50%',
                                                background: `linear-gradient(135deg, ${entry.color}20, ${entry.color}40)`,
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                margin: '0 auto 12px',
                                                fontSize: 24,
                                                color: entry.color,
                                            }}
                                        >
                                            {entry.icon}
                                        </div>
                                        <Text strong style={{ display: 'block', marginBottom: 4 }}>{entry.title}</Text>
                                        <Text type="secondary" style={{ fontSize: 12 }}>{entry.desc}</Text>
                                    </Card>
                                </Col>
                            ))}
                        </Row>
                    </Card>

                    {/* 我的班级 */}
                    <Card
                        title={<span style={{ fontSize: 16, fontWeight: 600 }}>📚 我的班级</span>}
                        style={{ borderRadius: 12 }}
                        extra={
                            myClasses.length > 0 && (
                                <Button type="link" onClick={() => navigate('/data-entry')}>
                                    开始录入 <RightOutlined />
                                </Button>
                            )
                        }
                    >
                        {myClasses.length > 0 ? (
                            <Row gutter={[16, 16]}>
                                {myClasses.map((cls) => (
                                    <Col xs={12} sm={8} key={cls.id}>
                                        <Card
                                            size="small"
                                            hoverable
                                            style={{ borderRadius: 8 }}
                                            onClick={() => navigate('/data-entry')}
                                        >
                                            <Space>
                                                <Avatar style={{ backgroundColor: '#667eea' }}>
                                                    {cls.grade_name?.[0] || cls.name?.[0]}
                                                </Avatar>
                                                <div>
                                                    <Text strong>{cls.grade_name} {cls.name}</Text>
                                                    <br />
                                                    <Text type="secondary" style={{ fontSize: 12 }}>
                                                        {cls.student_count || 0} 名学生
                                                    </Text>
                                                </div>
                                            </Space>
                                        </Card>
                                    </Col>
                                ))}
                            </Row>
                        ) : (
                            <Empty
                                description="暂未分配班级"
                                image={Empty.PRESENTED_IMAGE_SIMPLE}
                            >
                                <Text type="secondary">请联系管理员分配班级</Text>
                            </Empty>
                        )}
                    </Card>
                </Col>

                {/* 右侧边栏 */}
                <Col xs={24} lg={8}>
                    {/* 工作进度 */}
                    <Card
                        title={<span style={{ fontSize: 16, fontWeight: 600 }}>📊 本学期进度</span>}
                        style={{ borderRadius: 12, marginBottom: 24 }}
                    >
                        <div ref={chartRef} style={{ height: 180 }} />
                        <Divider style={{ margin: '16px 0' }} />
                        <Row gutter={16}>
                            <Col span={12}>
                                <Text type="secondary">数据录入</Text>
                                <Progress percent={stats.total_evaluations > 0 ? 80 : 0} size="small" strokeColor="#667eea" />
                            </Col>
                            <Col span={12}>
                                <Text type="secondary">评语生成</Text>
                                <Progress percent={0} size="small" strokeColor="#f093fb" />
                            </Col>
                        </Row>
                    </Card>

                    {/* 待办任务 */}
                    <Card
                        title={<span style={{ fontSize: 16, fontWeight: 600 }}>📋 待办任务</span>}
                        style={{ borderRadius: 12 }}
                    >
                        <List
                            size="small"
                            dataSource={todoTasks}
                            renderItem={(item) => (
                                <List.Item
                                    style={{ cursor: 'pointer', padding: '12px 0' }}
                                    onClick={() => navigate(item.link)}
                                    extra={getStatusTag(item.status)}
                                >
                                    <List.Item.Meta
                                        avatar={getStatusIcon(item.status)}
                                        title={<Text style={{ fontSize: 14 }}>{item.title}</Text>}
                                        description={<Text type="secondary" style={{ fontSize: 12 }}>{item.description}</Text>}
                                    />
                                </List.Item>
                            )}
                        />
                    </Card>
                </Col>
            </Row>
        </div>
    )
}

// 获取问候语
function getGreeting(): string {
    const hour = new Date().getHours()
    if (hour < 6) return '凌晨好'
    if (hour < 9) return '早上好'
    if (hour < 12) return '上午好'
    if (hour < 14) return '中午好'
    if (hour < 18) return '下午好'
    if (hour < 22) return '晚上好'
    return '夜深了'
}

export default TeacherDashboard
