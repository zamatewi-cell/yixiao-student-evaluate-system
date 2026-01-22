import React, { useState, useEffect, useCallback } from 'react'
import {
    Card, Table, Tag, Space, Select, DatePicker, Button, Row, Col,
    Statistic, Typography, message
} from 'antd'
import {
    FileSearchOutlined, ReloadOutlined, UserOutlined,
    BarChartOutlined, DeleteOutlined
} from '@ant-design/icons'
import axios from 'axios'
import dayjs from 'dayjs'

const { Option } = Select
const { RangePicker } = DatePicker
const { Text } = Typography

interface AuditLog {
    id: number
    user_id: number
    username: string
    real_name: string
    action_type: string
    action_type_text: string
    module: string
    module_text: string
    description: string
    ip_address: string
    created_at: string
}

const ACTION_TYPES = [
    { value: 'login', label: '用户登录', color: 'green' },
    { value: 'logout', label: '用户登出', color: 'default' },
    { value: 'create', label: '创建数据', color: 'blue' },
    { value: 'update', label: '更新数据', color: 'orange' },
    { value: 'delete', label: '删除数据', color: 'red' },
    { value: 'export', label: '导出数据', color: 'purple' },
    { value: 'import', label: '导入数据', color: 'cyan' },
    { value: 'backup', label: '数据备份', color: 'gold' },
    { value: 'config', label: '系统配置', color: 'magenta' }
]

const MODULES = [
    { value: 'auth', label: '认证模块' },
    { value: 'student', label: '学生管理' },
    { value: 'teacher', label: '教师管理' },
    { value: 'class', label: '班级管理' },
    { value: 'exam', label: '考试管理' },
    { value: 'score', label: '成绩管理' },
    { value: 'attendance', label: '考勤管理' },
    { value: 'comment', label: '评语管理' },
    { value: 'system', label: '系统管理' }
]

const AuditLogViewer: React.FC = () => {
    const [loading, setLoading] = useState(false)
    const [logs, setLogs] = useState<AuditLog[]>([])
    const [total, setTotal] = useState(0)
    const [page, setPage] = useState(1)
    const [pageSize] = useState(15)
    const [actionType, setActionType] = useState<string | undefined>()
    const [module, setModule] = useState<string | undefined>()
    const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null)
    const [stats, setStats] = useState<any>(null)

    // 获取日志列表
    const fetchLogs = useCallback(async () => {
        setLoading(true)
        try {
            const token = localStorage.getItem('token')
            const params: any = { page, page_size: pageSize }

            if (actionType) params.action_type = actionType
            if (module) params.module = module
            if (dateRange) {
                params.start_date = dateRange[0].format('YYYY-MM-DD')
                params.end_date = dateRange[1].format('YYYY-MM-DD')
            }

            const response = await axios.get('/api/audit-log/list', {
                headers: { Authorization: `Bearer ${token}` },
                params
            })
            setLogs(response.data.data || [])
            setTotal(response.data.total || 0)
        } catch (error) {
            message.error('获取日志失败')
        } finally {
            setLoading(false)
        }
    }, [page, pageSize, actionType, module, dateRange])

    // 获取统计
    const fetchStats = useCallback(async () => {
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/audit-log/statistics', {
                headers: { Authorization: `Bearer ${token}` },
                params: { days: 7 }
            })
            setStats(response.data.data)
        } catch (error) {
            console.error('获取统计失败')
        }
    }, [])

    useEffect(() => {
        fetchLogs()
        fetchStats()
    }, [fetchLogs, fetchStats])

    // 清理日志
    const handleCleanup = async () => {
        try {
            const token = localStorage.getItem('token')
            const response = await axios.delete('/api/audit-log/cleanup', {
                headers: { Authorization: `Bearer ${token}` },
                params: { days: 90 }
            })
            message.success(response.data.message)
            fetchLogs()
            fetchStats()
        } catch (error) {
            message.error('清理失败')
        }
    }

    const getActionColor = (type: string) => {
        const found = ACTION_TYPES.find(a => a.value === type)
        return found?.color || 'default'
    }

    const columns = [
        {
            title: '时间',
            dataIndex: 'created_at',
            key: 'created_at',
            width: 180
        },
        {
            title: '用户',
            key: 'user',
            width: 120,
            render: (_: any, record: AuditLog) => (
                <Space>
                    <UserOutlined />
                    <Text>{record.real_name || record.username}</Text>
                </Space>
            )
        },
        {
            title: '操作',
            dataIndex: 'action_type',
            key: 'action_type',
            width: 100,
            render: (type: string, record: AuditLog) => (
                <Tag color={getActionColor(type)}>{record.action_type_text}</Tag>
            )
        },
        {
            title: '模块',
            dataIndex: 'module',
            key: 'module',
            width: 100,
            render: (_: string, record: AuditLog) => record.module_text
        },
        {
            title: '描述',
            dataIndex: 'description',
            key: 'description',
            ellipsis: true
        },
        {
            title: 'IP地址',
            dataIndex: 'ip_address',
            key: 'ip_address',
            width: 130
        }
    ]

    return (
        <div style={{ padding: 24 }}>
            {/* 统计卡片 */}
            {stats && (
                <Row gutter={16} style={{ marginBottom: 24 }}>
                    <Col span={6}>
                        <Card>
                            <Statistic
                                title="近7天操作总数"
                                value={stats.daily_stats?.reduce((sum: number, d: any) => sum + d.count, 0) || 0}
                                prefix={<BarChartOutlined />}
                            />
                        </Card>
                    </Col>
                    <Col span={6}>
                        <Card>
                            <Statistic
                                title="活跃用户数"
                                value={stats.user_stats?.length || 0}
                                prefix={<UserOutlined />}
                            />
                        </Card>
                    </Col>
                    <Col span={6}>
                        <Card>
                            <Statistic
                                title="最多操作类型"
                                value={stats.action_stats?.[0]?.action_type_text || '-'}
                                valueStyle={{ fontSize: 20 }}
                            />
                        </Card>
                    </Col>
                    <Col span={6}>
                        <Card>
                            <Statistic
                                title="最活跃模块"
                                value={stats.module_stats?.[0]?.module_text || '-'}
                                valueStyle={{ fontSize: 20 }}
                            />
                        </Card>
                    </Col>
                </Row>
            )}

            <Card
                title={
                    <Space>
                        <FileSearchOutlined />
                        <span>操作日志</span>
                    </Space>
                }
                extra={
                    <Space>
                        <Button icon={<ReloadOutlined />} onClick={fetchLogs}>刷新</Button>
                        <Button
                            danger
                            icon={<DeleteOutlined />}
                            onClick={handleCleanup}
                        >
                            清理90天前日志
                        </Button>
                    </Space>
                }
            >
                {/* 筛选区 */}
                <Row gutter={16} style={{ marginBottom: 16 }}>
                    <Col span={6}>
                        <Select
                            style={{ width: '100%' }}
                            placeholder="操作类型"
                            value={actionType}
                            onChange={setActionType}
                            allowClear
                        >
                            {ACTION_TYPES.map(a => (
                                <Option key={a.value} value={a.value}>
                                    <Tag color={a.color}>{a.label}</Tag>
                                </Option>
                            ))}
                        </Select>
                    </Col>
                    <Col span={6}>
                        <Select
                            style={{ width: '100%' }}
                            placeholder="模块"
                            value={module}
                            onChange={setModule}
                            allowClear
                        >
                            {MODULES.map(m => (
                                <Option key={m.value} value={m.value}>{m.label}</Option>
                            ))}
                        </Select>
                    </Col>
                    <Col span={8}>
                        <RangePicker
                            style={{ width: '100%' }}
                            value={dateRange}
                            onChange={(dates) => setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs])}
                        />
                    </Col>
                    <Col span={4}>
                        <Button
                            type="primary"
                            onClick={fetchLogs}
                            style={{ width: '100%' }}
                        >
                            查询
                        </Button>
                    </Col>
                </Row>

                <Table
                    dataSource={logs}
                    columns={columns}
                    rowKey="id"
                    loading={loading}
                    pagination={{
                        current: page,
                        total,
                        pageSize,
                        onChange: setPage,
                        showTotal: (t) => `共 ${t} 条记录`
                    }}
                    size="middle"
                />
            </Card>
        </div>
    )
}

export default AuditLogViewer
