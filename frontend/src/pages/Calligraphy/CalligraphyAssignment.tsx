/**
 * 书法作品学生分配页面
 * 
 * 功能说明：
 * - 查看未分配学生的书法作品
 * - 手动将作品分配给学生（每个学生一个作品）
 * - 批量分配功能
 * - 同步评语到期末评语管理
 */
import { useState, useEffect, useCallback } from 'react'
import {
    Card,
    Table,
    Button,
    Select,
    Space,
    Row,
    Col,
    Image,
    Tag,
    Modal,
    message,
    Tooltip,
    Typography,
    Divider,
    Alert,
    Popconfirm,
} from 'antd'
import {
    UserAddOutlined,
    SyncOutlined,
    EyeOutlined,
    LinkOutlined,
    DisconnectOutlined,
    TeamOutlined,
    ReloadOutlined,
} from '@ant-design/icons'
import axios from 'axios'

const { Title, Text, Paragraph } = Typography
const { Option, OptGroup } = Select

// 接口定义
interface GradingRecord {
    id: number
    filename: string
    original_filename: string
    upload_time: string
    overall_score: number | null
    grade: string | null
    char_count: number
    ai_comment: string | null
    strengths: string | null
    suggestions: string | null
    file_url: string
    barcode?: string | null
    student_id?: number | null
    student_name?: string | null
    student_no?: string | null
    class_name?: string | null
    synced_to_evaluation?: boolean
}

interface Student {
    id: number
    student_no: string
    name: string
    gender: string
}

interface Class {
    id: number
    name: string
    grade_id: number
    grade_name: string
    student_count: number
    is_head_teacher?: number
}

interface Semester {
    id: number
    name: string
    is_current: boolean
}

const CalligraphyAssignment = () => {
    // 状态管理
    const [loading, setLoading] = useState(false)
    const [assignedRecords, setAssignedRecords] = useState<GradingRecord[]>([])
    const [unassignedRecords, setUnassignedRecords] = useState<GradingRecord[]>([])
    const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })

    // 班级和学生
    const [classes, setClasses] = useState<Class[]>([])
    const [students, setStudents] = useState<Student[]>([])
    const [selectedClass, setSelectedClass] = useState<number | null>(null)
    const [semesters, setSemesters] = useState<Semester[]>([])
    const [selectedSemester, setSelectedSemester] = useState<number | null>(null)

    // 弹窗
    const [assignModalVisible, setAssignModalVisible] = useState(false)
    const [selectedRecord, setSelectedRecord] = useState<GradingRecord | null>(null)
    const [selectedStudent, setSelectedStudent] = useState<number | null>(null)
    const [submitting, setSubmitting] = useState(false)

    // API 基础 URL
    const API_BASE = 'http://localhost:8000'

    // 获取Token
    const getAuthHeaders = () => {
        const token = localStorage.getItem('token')
        return { Authorization: `Bearer ${token}` }
    }

    // 获取班级列表（优先使用教师接口，如果返回空则试用管理员接口）
    const fetchClasses = useCallback(async () => {
        try {
            let response = await axios.get(`${API_BASE}/api/teacher/my-classes`, {
                headers: getAuthHeaders()
            })
            let classData = response.data.data || []

            // 如果教师接口返回空，尝试管理员接口
            if (classData.length === 0) {
                try {
                    response = await axios.get(`${API_BASE}/api/admin/classes`, {
                        headers: getAuthHeaders()
                    })
                    classData = response.data.data || []
                } catch {
                    // 忽略
                }
            }

            setClasses(classData)
        } catch (error) {
            // 教师接口失败，尝试管理员接口
            try {
                const response = await axios.get(`${API_BASE}/api/admin/classes`, {
                    headers: getAuthHeaders()
                })
                setClasses(response.data.data || [])
            } catch {
                console.error('获取班级失败:', error)
                message.error('获取班级列表失败')
            }
        }
    }, [])

    // 获取学期列表
    const fetchSemesters = useCallback(async () => {
        try {
            const response = await axios.get(`${API_BASE}/api/admin/semesters`, {
                headers: getAuthHeaders()
            })
            const semesterList = response.data.data || []
            setSemesters(semesterList)

            // 自动选中当前学期
            const currentSemester = semesterList.find((s: Semester) => s.is_current)
            if (currentSemester) {
                setSelectedSemester(currentSemester.id)
            } else if (semesterList.length > 0) {
                setSelectedSemester(semesterList[0].id)
            }
        } catch (error) {
            console.error('获取学期失败:', error)
        }
    }, [])

    // 获取班级学生
    const fetchClassStudents = useCallback(async (classId: number) => {
        try {
            const response = await axios.get(`${API_BASE}/api/teacher/classes/${classId}/students`, {
                headers: getAuthHeaders()
            })
            setStudents(response.data.data || [])
        } catch (error) {
            console.error('获取学生失败:', error)
            message.error('获取学生列表失败')
        }
    }, [])

    // 获取未分配的作品
    const fetchUnassignedRecords = useCallback(async (page = 1, pageSize = 10) => {
        setLoading(true)
        try {
            const response = await axios.get(`${API_BASE}/api/teacher/calligraphy-records/unassigned`, {
                params: { page, page_size: pageSize },
                headers: getAuthHeaders()
            })
            setUnassignedRecords(response.data.data || [])
            setPagination({
                current: response.data.page,
                pageSize: response.data.page_size,
                total: response.data.total
            })
        } catch (error) {
            console.error('获取未分配作品失败:', error)
            message.error('获取未分配作品列表失败')
        } finally {
            setLoading(false)
        }
    }, [])

    // 获取已分配的作品
    const fetchAssignedRecords = useCallback(async () => {
        if (!selectedClass) return
        setLoading(true)
        try {
            const response = await axios.get(`${API_BASE}/api/teacher/calligraphy-records`, {
                params: { class_id: selectedClass, page: 1, page_size: 100 },
                headers: getAuthHeaders()
            })
            setAssignedRecords(response.data.data || [])
        } catch (error) {
            console.error('获取已分配作品失败:', error)
        } finally {
            setLoading(false)
        }
    }, [selectedClass])

    // 初始化
    useEffect(() => {
        fetchClasses()
        fetchSemesters()
        fetchUnassignedRecords()
    }, [fetchClasses, fetchSemesters, fetchUnassignedRecords])

    // 班级变化时获取学生
    useEffect(() => {
        if (selectedClass) {
            fetchClassStudents(selectedClass)
            fetchAssignedRecords()
        }
    }, [selectedClass, fetchClassStudents, fetchAssignedRecords])

    // 分配作品给学生
    const handleAssign = async () => {
        if (!selectedRecord || !selectedStudent) {
            message.warning('请选择学生')
            return
        }

        setSubmitting(true)
        try {
            await axios.post(`${API_BASE}/api/teacher/calligraphy-records/assign`, {
                record_id: selectedRecord.id,
                student_id: selectedStudent
            }, {
                headers: getAuthHeaders()
            })

            message.success('分配成功')
            setAssignModalVisible(false)
            setSelectedRecord(null)
            setSelectedStudent(null)

            // 刷新列表
            fetchUnassignedRecords(pagination.current, pagination.pageSize)
            if (selectedClass) {
                fetchAssignedRecords()
            }
        } catch (error: any) {
            message.error(error.response?.data?.detail || '分配失败')
        } finally {
            setSubmitting(false)
        }
    }

    // 取消分配
    const handleUnassign = async (recordId: number) => {
        try {
            await axios.delete(`${API_BASE}/api/teacher/calligraphy-records/${recordId}/unassign`, {
                headers: getAuthHeaders()
            })
            message.success('已取消分配')
            fetchUnassignedRecords(pagination.current, pagination.pageSize)
            if (selectedClass) {
                fetchAssignedRecords()
            }
        } catch (error: any) {
            message.error(error.response?.data?.detail || '取消分配失败')
        }
    }

    // 同步评语
    const handleSyncComment = async (recordId: number) => {
        if (!selectedSemester) {
            message.warning('请先选择学期')
            return
        }

        try {
            await axios.post(`${API_BASE}/api/teacher/calligraphy-records/sync-comment`, {
                record_id: recordId,
                semester_id: selectedSemester,
                append_to_existing: true
            }, {
                headers: getAuthHeaders()
            })
            message.success('评语已同步到期末评语管理')
            if (selectedClass) {
                fetchAssignedRecords()
            }
        } catch (error: any) {
            message.error(error.response?.data?.detail || '同步失败')
        }
    }

    // 批量同步评语
    const handleBatchSyncComments = async () => {
        if (!selectedClass || !selectedSemester) {
            message.warning('请先选择班级和学期')
            return
        }

        try {
            const response = await axios.post(`${API_BASE}/api/teacher/calligraphy-records/batch-sync-comments`, null, {
                params: {
                    class_id: selectedClass,
                    semester_id: selectedSemester,
                    append_to_existing: true
                },
                headers: getAuthHeaders()
            })
            message.success(response.data.message)
        } catch (error: any) {
            message.error(error.response?.data?.detail || '批量同步失败')
        }
    }

    // 等级颜色
    const getGradeColor = (grade: string | null) => {
        const colors: Record<string, string> = {
            'Excellent': '#52c41a',
            'Good': '#1890ff',
            'Medium': '#faad14',
            'Pass': '#fa8c16',
            'NeedImprove': '#ff4d4f',
        }
        return colors[grade || ''] || '#999'
    }

    // 等级文本
    const getGradeText = (grade: string | null) => {
        const texts: Record<string, string> = {
            'Excellent': '优秀',
            'Good': '良好',
            'Medium': '中等',
            'Pass': '及格',
            'NeedImprove': '待提高',
        }
        return texts[grade || ''] || '未评定'
    }

    // 未分配作品表格列
    const unassignedColumns = [
        {
            title: '预览',
            dataIndex: 'file_url',
            key: 'preview',
            width: 80,
            render: (url: string) => (
                <Image
                    src={`${API_BASE}${url}`}
                    width={50}
                    height={50}
                    style={{ objectFit: 'cover', borderRadius: 4 }}
                    preview={{ mask: <EyeOutlined /> }}
                />
            ),
        },
        {
            title: '文件名',
            dataIndex: 'original_filename',
            key: 'filename',
            ellipsis: true,
            render: (name: string) => (
                <Tooltip title={name}>
                    <Text ellipsis style={{ maxWidth: 150 }}>{name}</Text>
                </Tooltip>
            ),
        },
        {
            title: '评分',
            dataIndex: 'overall_score',
            key: 'score',
            width: 80,
            render: (score: number | null) => (
                score !== null ? (
                    <Text strong style={{
                        color: score >= 80 ? '#52c41a' : score >= 60 ? '#faad14' : '#ff4d4f',
                        fontSize: 14
                    }}>
                        {score.toFixed(1)}
                    </Text>
                ) : <Text type="secondary">-</Text>
            ),
        },
        {
            title: '等级',
            dataIndex: 'grade',
            key: 'grade',
            width: 80,
            render: (grade: string | null) => (
                <Tag color={getGradeColor(grade)}>{getGradeText(grade)}</Tag>
            ),
        },
        {
            title: '上传时间',
            dataIndex: 'upload_time',
            key: 'upload_time',
            width: 160,
        },
        {
            title: '操作',
            key: 'action',
            width: 100,
            render: (_: any, record: GradingRecord) => (
                <Button
                    type="primary"
                    size="small"
                    icon={<UserAddOutlined />}
                    onClick={() => {
                        setSelectedRecord(record)
                        setAssignModalVisible(true)
                    }}
                >
                    分配
                </Button>
            ),
        },
    ]

    // 已分配作品表格列
    const assignedColumns = [
        {
            title: '预览',
            dataIndex: 'file_url',
            key: 'preview',
            width: 80,
            render: (_: any, record: GradingRecord) => (
                <Image
                    src={`${API_BASE}/uploads/${record.filename}`}
                    width={50}
                    height={50}
                    style={{ objectFit: 'cover', borderRadius: 4 }}
                    preview={{ mask: <EyeOutlined /> }}
                />
            ),
        },
        {
            title: '学生',
            key: 'student',
            width: 150,
            render: (_: any, record: GradingRecord) => (
                <Space direction="vertical" size={0}>
                    <Text strong>{record.student_name || '-'}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>{record.student_no}</Text>
                </Space>
            ),
        },
        {
            title: '评分',
            dataIndex: 'overall_score',
            key: 'score',
            width: 80,
            render: (score: number | null) => (
                score !== null ? (
                    <Text strong style={{
                        color: score >= 80 ? '#52c41a' : score >= 60 ? '#faad14' : '#ff4d4f',
                    }}>
                        {typeof score === 'number' ? score.toFixed(1) : score}
                    </Text>
                ) : <Text type="secondary">-</Text>
            ),
        },
        {
            title: '等级',
            dataIndex: 'grade',
            key: 'grade',
            width: 80,
            render: (grade: string | null) => (
                <Tag color={getGradeColor(grade)}>{getGradeText(grade)}</Tag>
            ),
        },
        {
            title: '同步状态',
            dataIndex: 'synced_to_evaluation',
            key: 'synced',
            width: 100,
            render: (synced: boolean) => (
                synced ?
                    <Tag color="success">已同步</Tag> :
                    <Tag color="default">未同步</Tag>
            ),
        },
        {
            title: '操作',
            key: 'action',
            width: 180,
            render: (_: any, record: GradingRecord) => (
                <Space size="small">
                    <Tooltip title="同步评语到期末评语">
                        <Button
                            size="small"
                            icon={<SyncOutlined />}
                            onClick={() => handleSyncComment(record.id)}
                            disabled={!selectedSemester}
                        >
                            同步
                        </Button>
                    </Tooltip>
                    <Popconfirm
                        title="确定要取消分配吗？"
                        onConfirm={() => handleUnassign(record.id)}
                        okText="确定"
                        cancelText="取消"
                    >
                        <Tooltip title="取消分配">
                            <Button
                                size="small"
                                danger
                                icon={<DisconnectOutlined />}
                            />
                        </Tooltip>
                    </Popconfirm>
                </Space>
            ),
        },
    ]

    return (
        <div style={{ padding: 24 }}>
            {/* 页面标题 */}
            <div style={{ marginBottom: 24 }}>
                <Title level={3} style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <LinkOutlined style={{ color: '#667eea' }} />
                    书法作品分配
                </Title>
                <Text type="secondary">将书法作品手动分配给学生，并同步评语到期末评语管理</Text>
            </div>

            {/* 筛选条件 */}
            <Card style={{ marginBottom: 24 }}>
                <Row gutter={16} align="middle">
                    <Col>
                        <Text strong>选择班级：</Text>
                        <Select
                            placeholder="请选择班级"
                            value={selectedClass}
                            onChange={setSelectedClass}
                            style={{ width: 220, marginLeft: 8 }}
                            allowClear
                            showSearch
                            optionFilterProp="children"
                            notFoundContent="暂无可用班级"
                        >
                            {classes && classes.length > 0 ? (
                                Object.entries(
                                    classes.reduce((groups: { [key: string]: typeof classes }, cls) => {
                                        const gradeName = cls.grade_name || '未分配年级'
                                        if (!groups[gradeName]) groups[gradeName] = []
                                        groups[gradeName].push(cls)
                                        return groups
                                    }, {})
                                ).sort(([a], [b]) => a.localeCompare(b, 'zh-CN')).map(([gradeName, classList]) => (
                                    <OptGroup key={gradeName} label={gradeName}>
                                        {classList.map(cls => (
                                            <Option key={cls.id} value={cls.id}>
                                                {cls.name}
                                                {cls.is_head_teacher ? <Tag color="blue" style={{ marginLeft: 8 }}>班主任</Tag> : null}
                                            </Option>
                                        ))}
                                    </OptGroup>
                                ))
                            ) : null}
                        </Select>
                    </Col>
                    <Col>
                        <Text strong>选择学期：</Text>
                        <Select
                            placeholder="请选择学期"
                            value={selectedSemester}
                            onChange={setSelectedSemester}
                            style={{ width: 200, marginLeft: 8 }}
                        >
                            {semesters.map(sem => (
                                <Option key={sem.id} value={sem.id}>
                                    {sem.name} {sem.is_current && <Tag color="green">当前</Tag>}
                                </Option>
                            ))}
                        </Select>
                    </Col>
                    <Col flex="auto" style={{ textAlign: 'right' }}>
                        <Button
                            icon={<ReloadOutlined />}
                            onClick={() => {
                                fetchUnassignedRecords()
                                if (selectedClass) {
                                    fetchAssignedRecords()
                                }
                            }}
                        >
                            刷新
                        </Button>
                    </Col>
                </Row>
            </Card>

            <Row gutter={24}>
                {/* 左侧：未分配的作品 */}
                <Col xs={24} lg={12}>
                    <Card
                        title={
                            <Space>
                                <TeamOutlined style={{ color: '#faad14' }} />
                                <span>未分配作品</span>
                                <Tag color="orange">{pagination.total} 个</Tag>
                            </Space>
                        }
                    >
                        <Alert
                            message="选择作品并分配给学生，每个学生只能分配一个作品"
                            type="info"
                            showIcon
                            style={{ marginBottom: 16 }}
                        />
                        <Table
                            columns={unassignedColumns}
                            dataSource={unassignedRecords}
                            rowKey="id"
                            loading={loading}
                            pagination={{
                                ...pagination,
                                size: 'small',
                                showSizeChanger: true,
                                showTotal: (total) => `共 ${total} 个`,
                                onChange: (page, pageSize) => fetchUnassignedRecords(page, pageSize),
                            }}
                            size="small"
                            scroll={{ x: 600 }}
                        />
                    </Card>
                </Col>

                {/* 右侧：已分配的作品 */}
                <Col xs={24} lg={12}>
                    <Card
                        title={
                            <Space>
                                <LinkOutlined style={{ color: '#52c41a' }} />
                                <span>已分配作品</span>
                                {selectedClass && <Tag color="green">{assignedRecords.length} 个</Tag>}
                            </Space>
                        }
                        extra={
                            selectedClass && selectedSemester && assignedRecords.length > 0 && (
                                <Button
                                    type="primary"
                                    icon={<SyncOutlined />}
                                    onClick={handleBatchSyncComments}
                                >
                                    批量同步评语
                                </Button>
                            )
                        }
                    >
                        {!selectedClass ? (
                            <Alert
                                message="请先选择班级查看已分配的作品"
                                type="warning"
                                showIcon
                            />
                        ) : (
                            <Table
                                columns={assignedColumns}
                                dataSource={assignedRecords}
                                rowKey="id"
                                loading={loading}
                                pagination={{ pageSize: 10 }}
                                size="small"
                                scroll={{ x: 600 }}
                                locale={{
                                    emptyText: '该班级暂无已分配的书法作品'
                                }}
                            />
                        )}
                    </Card>
                </Col>
            </Row>

            {/* 分配弹窗 */}
            <Modal
                title={
                    <Space>
                        <UserAddOutlined />
                        <span>分配作品给学生</span>
                    </Space>
                }
                open={assignModalVisible}
                onCancel={() => {
                    setAssignModalVisible(false)
                    setSelectedRecord(null)
                    setSelectedStudent(null)
                }}
                onOk={handleAssign}
                confirmLoading={submitting}
                okText="确认分配"
                cancelText="取消"
                width={600}
            >
                {selectedRecord && (
                    <Space direction="vertical" style={{ width: '100%' }} size="large">
                        {/* 作品预览 */}
                        <Card size="small">
                            <Row gutter={16}>
                                <Col span={8}>
                                    <Image
                                        src={`${API_BASE}${selectedRecord.file_url}`}
                                        style={{ width: '100%', borderRadius: 8 }}
                                    />
                                </Col>
                                <Col span={16}>
                                    <Space direction="vertical" style={{ width: '100%' }}>
                                        <Text strong>{selectedRecord.original_filename}</Text>
                                        <Text>评分：<Text strong style={{ color: getGradeColor(selectedRecord.grade) }}>
                                            {selectedRecord.overall_score?.toFixed(1) || '-'} ({getGradeText(selectedRecord.grade)})
                                        </Text></Text>
                                        {selectedRecord.ai_comment && (
                                            <Paragraph ellipsis={{ rows: 2 }} style={{ marginBottom: 0 }}>
                                                {selectedRecord.ai_comment}
                                            </Paragraph>
                                        )}
                                    </Space>
                                </Col>
                            </Row>
                        </Card>

                        <Divider style={{ margin: '12px 0' }} />

                        {/* 选择班级和学生 */}
                        <div>
                            <Text strong style={{ display: 'block', marginBottom: 8 }}>选择班级：</Text>
                            <Select
                                placeholder="请选择班级"
                                value={selectedClass}
                                onChange={(value) => {
                                    setSelectedClass(value)
                                    setSelectedStudent(null)
                                }}
                                style={{ width: '100%' }}
                                showSearch
                                optionFilterProp="children"
                                notFoundContent="暂无可用班级"
                            >
                                {classes && classes.length > 0 ? (
                                    Object.entries(
                                        classes.reduce((groups: { [key: string]: typeof classes }, cls) => {
                                            const gradeName = cls.grade_name || '未分配年级'
                                            if (!groups[gradeName]) groups[gradeName] = []
                                            groups[gradeName].push(cls)
                                            return groups
                                        }, {})
                                    ).sort(([a], [b]) => a.localeCompare(b, 'zh-CN')).map(([gradeName, classList]) => (
                                        <OptGroup key={gradeName} label={gradeName}>
                                            {classList.map(cls => (
                                                <Option key={cls.id} value={cls.id}>
                                                    {cls.name} ({cls.student_count || 0}人)
                                                </Option>
                                            ))}
                                        </OptGroup>
                                    ))
                                ) : null}
                            </Select>
                        </div>

                        <div>
                            <Text strong style={{ display: 'block', marginBottom: 8 }}>选择学生：</Text>
                            <Select
                                placeholder={selectedClass ? "请选择学生" : "请先选择班级"}
                                value={selectedStudent}
                                onChange={setSelectedStudent}
                                style={{ width: '100%' }}
                                disabled={!selectedClass}
                                showSearch
                                optionFilterProp="children"
                            >
                                {students.map(stu => (
                                    <Option key={stu.id} value={stu.id}>
                                        {stu.student_no} - {stu.name} ({stu.gender === 'male' ? '男' : '女'})
                                    </Option>
                                ))}
                            </Select>
                        </div>
                    </Space>
                )}
            </Modal>
        </div>
    )
}

export default CalligraphyAssignment
