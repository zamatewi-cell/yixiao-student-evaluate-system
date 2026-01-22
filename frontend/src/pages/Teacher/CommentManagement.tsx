import React, { useState, useEffect } from 'react'
import {
    Card,
    Form,
    Select,
    Table,
    Button,
    Input,
    message,
    Space,
    Modal,
    Tag,
    Divider,
    Alert,
    Progress,
    Typography
} from 'antd'
import {
    CommentOutlined,
    ThunderboltOutlined,
    SaveOutlined,
    EyeOutlined,
    EditOutlined,
    CheckCircleOutlined,
    LockOutlined
} from '@ant-design/icons'
import axios from 'axios'

const { Option, OptGroup } = Select
const { TextArea } = Input
const { Title, Text, Paragraph } = Typography

interface Class {
    id: number
    name: string
    grade_id: number
    grade_name: string
    student_count: number
}

interface Semester {
    id: number
    name: string
    is_current: boolean
}

interface Comment {
    student_id: number
    student_no: string
    student_name: string
    ai_comment: string | null
    teacher_comment: string | null
    is_published: boolean
    updated_at: string | null
}

const CommentManagement: React.FC = () => {
    const [loading, setLoading] = useState(false)
    const [generating, setGenerating] = useState(false)
    const [batchProgress, setBatchProgress] = useState(0)

    // 基础数据
    const [myClasses, setMyClasses] = useState<Class[]>([])
    const [semesters, setSemesters] = useState<Semester[]>([])
    const [comments, setComments] = useState<Comment[]>([])

    // 选中的值
    const [selectedClass, setSelectedClass] = useState<number | null>(null)
    const [selectedSemester, setSelectedSemester] = useState<number | null>(null)

    // 编辑模态框
    const [editModalVisible, setEditModalVisible] = useState(false)
    const [editingComment, setEditingComment] = useState<Comment | null>(null)
    const [editForm] = Form.useForm()

    // 预览模态框
    const [previewModalVisible, setPreviewModalVisible] = useState(false)
    const [previewComment, setPreviewComment] = useState<Comment | null>(null)

    // 编辑权限状态
    const [canEdit, setCanEdit] = useState<boolean>(false)
    const [permissionLoaded, setPermissionLoaded] = useState<boolean>(false)

    // 检查编辑权限
    const checkEditPermission = async () => {
        try {
            const token = localStorage.getItem('token')

            // 首先检查用户角色，管理员直接拥有权限
            const authStorage = localStorage.getItem('auth-storage')
            if (authStorage) {
                const authData = JSON.parse(authStorage)
                if (authData.state?.user?.role === 'admin') {
                    setCanEdit(true)
                    setPermissionLoaded(true)
                    return
                }
            }

            // 教师需要检查权限
            const response = await axios.get('/api/teacher/edit-permission', {
                headers: { Authorization: `Bearer ${token}` }
            })
            setCanEdit(response.data.can_edit)
            if (!response.data.can_edit) {
                message.warning(response.data.message)
            }
        } catch (error: any) {
            // 出错时检查本地存储的角色
            const authStorage = localStorage.getItem('auth-storage')
            if (authStorage) {
                const authData = JSON.parse(authStorage)
                if (authData.state?.user?.role === 'admin') {
                    setCanEdit(true)
                    setPermissionLoaded(true)
                    return
                }
            }
            message.error('检查编辑权限失败')
        } finally {
            setPermissionLoaded(true)
        }
    }

    // 获取我的班级（优先使用教师接口，如果返回空则试用管理员接口）
    const fetchMyClasses = async () => {
        try {
            const token = localStorage.getItem('token')
            let response = await axios.get('/api/teacher/my-classes', {
                headers: { Authorization: `Bearer ${token}` }
            })
            let classData = response.data.data || []

            // 如果教师接口返回空，尝试管理员接口
            if (classData.length === 0) {
                try {
                    response = await axios.get('/api/admin/classes', {
                        headers: { Authorization: `Bearer ${token}` }
                    })
                    classData = response.data.data || []
                } catch {
                    // 忽略
                }
            }

            setMyClasses(classData)
        } catch (error: any) {
            try {
                const token = localStorage.getItem('token')
                const response = await axios.get('/api/admin/classes', {
                    headers: { Authorization: `Bearer ${token}` }
                })
                setMyClasses(response.data.data || [])
            } catch {
                message.error('获取班级列表失败: ' + (error.response?.data?.detail || error.message))
            }
        }
    }

    // 获取学期列表（使用教师接口）
    const fetchSemesters = async () => {
        try {
            const token = localStorage.getItem('token')
            // 使用教师接口获取学期列表
            const response = await axios.get('/api/teacher/semesters', {
                headers: { Authorization: `Bearer ${token}` }
            })
            const semesterList = response.data.data || []
            setSemesters(semesterList)

            // 自动选中当前学期（如果有的话）
            const currentSemester = semesterList.find((s: Semester) => s.is_current)
            if (currentSemester) {
                setSelectedSemester(currentSemester.id)
            } else if (semesterList.length > 0) {
                // 如果没有当前学期，选择第一个
                setSelectedSemester(semesterList[0].id)
            }
        } catch (error: any) {
            message.error('获取学期列表失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    // 获取班级评语
    const fetchClassComments = async (classId: number, semesterId: number) => {
        try {
            setLoading(true)
            const token = localStorage.getItem('token')
            const response = await axios.get(`/api/teacher/classes/${classId}/comments`, {
                params: { semester_id: semesterId },
                headers: { Authorization: `Bearer ${token}` }
            })
            setComments(response.data.data)
        } catch (error: any) {
            message.error('获取评语列表失败: ' + (error.response?.data?.detail || error.message))
        } finally {
            setLoading(false)
        }
    }

    // 初始化数据
    useEffect(() => {
        checkEditPermission()
        fetchMyClasses()
        fetchSemesters()
    }, [])

    // 班级或学期变化时加载评语
    useEffect(() => {
        if (selectedClass && selectedSemester) {
            fetchClassComments(selectedClass, selectedSemester)
        }
    }, [selectedClass, selectedSemester])

    // 生成单个学生评语
    const generateSingleComment = async (studentId: number) => {
        if (!selectedSemester) {
            message.warning('请选择学期')
            return
        }

        try {
            setGenerating(true)
            const token = localStorage.getItem('token')
            const response = await axios.post(
                '/api/teacher/comments/generate',
                {
                    student_id: studentId,
                    semester_id: selectedSemester
                },
                { headers: { Authorization: `Bearer ${token}` } }
            )

            if (response.data.success) {
                message.success('评语生成成功！')

                setComments(prev =>
                    prev.map(item =>
                        item.student_id === studentId
                            ? { ...item, ai_comment: response.data.comment }
                            : item
                    )
                )
            } else {
                message.error(response.data.error || '生成失败')
            }
        } catch (error: any) {
            message.error('生成评语失败: ' + (error.response?.data?.detail || error.message))
        } finally {
            setGenerating(false)
        }
    }

    // 批量生成评语
    const batchGenerateComments = async () => {
        if (!selectedClass || !selectedSemester) {
            message.warning('请选择班级和学期')
            return
        }

        Modal.confirm({
            title: '批量生成评语',
            content: '确定要为班级所有学生生成AI评语吗？这可能需要一些时间。',
            onOk: async () => {
                try {
                    setGenerating(true)
                    setBatchProgress(0)
                    const token = localStorage.getItem('token')

                    const response = await axios.post(
                        '/api/teacher/comments/batch-generate',
                        {
                            class_id: selectedClass,
                            semester_id: selectedSemester
                        },
                        { headers: { Authorization: `Bearer ${token}` } }
                    )

                    setBatchProgress(100)
                    message.success(`成功生成 ${response.data.success_count} / ${response.data.total} 条评语`)

                    fetchClassComments(selectedClass, selectedSemester)
                } catch (error: any) {
                    message.error('批量生成失败: ' + (error.response?.data?.detail || error.message))
                } finally {
                    setGenerating(false)
                    setBatchProgress(0)
                }
            }
        })
    }

    // 保存评语
    const saveComment = async (commentData: Comment, teacherComment?: string) => {
        try {
            const token = localStorage.getItem('token')
            await axios.post(
                '/api/teacher/comments/save',
                {
                    student_id: commentData.student_id,
                    semester_id: selectedSemester,
                    ai_comment: commentData.ai_comment,
                    teacher_comment: teacherComment || commentData.teacher_comment,
                    is_published: false
                },
                { headers: { Authorization: `Bearer ${token}` } }
            )

            message.success('评语保存成功')

            if (selectedClass && selectedSemester) {
                fetchClassComments(selectedClass, selectedSemester)
            }

            setEditModalVisible(false)
        } catch (error: any) {
            message.error('保存失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    // 发布评语
    const publishComment = async (commentData: Comment) => {
        try {
            const token = localStorage.getItem('token')
            await axios.post(
                '/api/teacher/comments/save',
                {
                    student_id: commentData.student_id,
                    semester_id: selectedSemester,
                    ai_comment: commentData.ai_comment,
                    teacher_comment: commentData.teacher_comment,
                    is_published: true
                },
                { headers: { Authorization: `Bearer ${token}` } }
            )

            message.success('评语已发布')

            if (selectedClass && selectedSemester) {
                fetchClassComments(selectedClass, selectedSemester)
            }
        } catch (error: any) {
            message.error('发布失败: ' + (error.response?.data?.detail || error.message))
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
            dataIndex: 'student_name',
            key: 'student_name',
            width: 100
        },
        {
            title: 'AI评语',
            dataIndex: 'ai_comment',
            key: 'ai_comment',
            ellipsis: true,
            render: (text: string | null) => text || <Text type="secondary">未生成</Text>
        },
        {
            title: '教师评语',
            dataIndex: 'teacher_comment',
            key: 'teacher_comment',
            ellipsis: true,
            render: (text: string | null) => text || <Text type="secondary">未编写</Text>
        },
        {
            title: '状态',
            key: 'status',
            width: 100,
            render: (_: any, record: Comment) => {
                if (record.is_published) {
                    return <Tag color="success" icon={<CheckCircleOutlined />}>已发布</Tag>
                } else if (record.ai_comment || record.teacher_comment) {
                    return <Tag color="warning">草稿</Tag>
                } else {
                    return <Tag color="default">未生成</Tag>
                }
            }
        },
        {
            title: '操作',
            key: 'actions',
            width: 280,
            render: (_: any, record: Comment) => (
                <Space size="small">
                    <Button
                        size="small"
                        type="primary"
                        icon={<ThunderboltOutlined />}
                        onClick={() => generateSingleComment(record.student_id)}
                        loading={generating}
                        disabled={generating}
                    >
                        生成
                    </Button>

                    {record.ai_comment && (
                        <Button
                            size="small"
                            icon={<EyeOutlined />}
                            onClick={() => {
                                setPreviewComment(record)
                                setPreviewModalVisible(true)
                            }}
                        >
                            预览
                        </Button>
                    )}

                    <Button
                        size="small"
                        icon={<EditOutlined />}
                        onClick={() => {
                            setEditingComment(record)
                            editForm.setFieldsValue({
                                teacher_comment: record.teacher_comment || ''
                            })
                            setEditModalVisible(true)
                        }}
                    >
                        编辑
                    </Button>

                    {(record.ai_comment || record.teacher_comment) && !record.is_published && (
                        <Button
                            size="small"
                            type="dashed"
                            onClick={() => publishComment(record)}
                        >
                            发布
                        </Button>
                    )}
                </Space>
            )
        }
    ]

    return (
        <div style={{ padding: 24 }}>
            <Card
                title={
                    <Space>
                        <Title level={4} style={{ margin: 0 }}>
                            <CommentOutlined /> 期末评语管理
                        </Title>
                        {permissionLoaded && !canEdit && (
                            <Tag color="warning" icon={<LockOutlined />}>无编辑权限</Tag>
                        )}
                        {permissionLoaded && canEdit && (
                            <Tag color="success" icon={<CheckCircleOutlined />}>已授权</Tag>
                        )}
                    </Space>
                }
            >
                {/* 筛选条件 */}
                <Space direction="vertical" style={{ width: '100%', marginBottom: 24 }}>
                    <Space size="large">
                        <div>
                            <Text strong>选择班级：</Text>
                            <Select
                                placeholder="请选择班级"
                                value={selectedClass}
                                onChange={setSelectedClass}
                                style={{ width: 220, marginLeft: 8 }}
                                showSearch
                                optionFilterProp="children"
                                notFoundContent="暂无可用班级"
                            >
                                {myClasses && myClasses.length > 0 ? (
                                    Object.entries(
                                        myClasses.reduce((groups: { [key: string]: typeof myClasses }, cls) => {
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
                                                </Option>
                                            ))}
                                        </OptGroup>
                                    ))
                                ) : null}
                            </Select>
                        </div>

                        <div>
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
                        </div>
                    </Space>

                    {/* 权限提示 */}
                    {permissionLoaded && !canEdit && (
                        <Alert
                            message="您尚未获得数据编辑权限"
                            description="请联系管理员授权后才能进行评语管理操作。您可以查看数据，但无法编辑。"
                            type="warning"
                            showIcon
                            icon={<LockOutlined />}
                            style={{ marginBottom: 16 }}
                        />
                    )}

                    {/* 批量操作 */}
                    {selectedClass && selectedSemester && (
                        <>
                            <Divider />
                            <Space>
                                <Button
                                    type="primary"
                                    icon={<ThunderboltOutlined />}
                                    onClick={batchGenerateComments}
                                    loading={generating}
                                    size="large"
                                    disabled={!canEdit}
                                >
                                    批量生成AI评语
                                </Button>
                                <Alert
                                    message={canEdit ? "提示：批量生成将为所有有评价数据的学生生成AI评语" : "您无权进行此操作，请联系管理员授权"}
                                    type={canEdit ? "info" : "warning"}
                                    showIcon
                                    style={{ flex: 1 }}
                                />
                            </Space>

                            {generating && batchProgress > 0 && (
                                <Progress percent={batchProgress} status="active" />
                            )}
                        </>
                    )}
                </Space>

                {/* 数据统计 */}
                {comments.length > 0 && (
                    <div style={{ marginBottom: 16, padding: 16, background: '#f0f2f5', borderRadius: 8 }}>
                        <Space size="large">
                            <Text>总学生数: <strong>{comments.length}</strong></Text>
                            <Text>已生成AI评语: <strong style={{ color: '#52c41a' }}>
                                {comments.filter(c => c.ai_comment).length}
                            </strong></Text>
                            <Text>已编写教师评语: <strong style={{ color: '#1890ff' }}>
                                {comments.filter(c => c.teacher_comment).length}
                            </strong></Text>
                            <Text>已发布: <strong style={{ color: '#fa8c16' }}>
                                {comments.filter(c => c.is_published).length}
                            </strong></Text>
                        </Space>
                    </div>
                )}

                {/* 评语表格 */}
                <Table
                    columns={columns}
                    dataSource={comments}
                    rowKey="student_id"
                    loading={loading}
                    pagination={{
                        pageSize: 20,
                        showSizeChanger: true,
                        showTotal: total => `共 ${total} 名学生`
                    }}
                    locale={{
                        emptyText: selectedClass ? '该班级暂无学生' : '请先选择班级和学期'
                    }}
                />
            </Card>

            {/* 编辑模态框 */}
            <Modal
                title={`编辑评语 - ${editingComment?.student_name || ''}`}
                open={editModalVisible}
                onCancel={() => setEditModalVisible(false)}
                width={800}
                footer={[
                    <Button key="cancel" onClick={() => setEditModalVisible(false)}>
                        取消
                    </Button>,
                    <Button
                        key="save"
                        type="primary"
                        icon={<SaveOutlined />}
                        onClick={() => {
                            const teacherComment = editForm.getFieldValue('teacher_comment')
                            if (editingComment) {
                                saveComment(editingComment, teacherComment)
                            }
                        }}
                    >
                        保存
                    </Button>
                ]}
            >
                {editingComment && (
                    <Space direction="vertical" style={{ width: '100%' }}>
                        <div>
                            <Text strong>AI评语：</Text>
                            <Paragraph style={{ background: '#f5f5f5', padding: 16, marginTop: 8, borderRadius: 4 }}>
                                {editingComment.ai_comment || '暂无AI评语'}
                            </Paragraph>
                        </div>

                        <Form form={editForm} layout="vertical">
                            <Form.Item
                                label="教师评语"
                                name="teacher_comment"
                                extra="可以在AI评语基础上进行修改，或直接编写新的评语"
                            >
                                <TextArea
                                    rows={6}
                                    placeholder="请输入教师评语..."
                                    maxLength={500}
                                    showCount
                                />
                            </Form.Item>
                        </Form>
                    </Space>
                )}
            </Modal>

            {/* 预览模态框 */}
            <Modal
                title={`评语预览 - ${previewComment?.student_name || ''}`}
                open={previewModalVisible}
                onCancel={() => setPreviewModalVisible(false)}
                width={700}
                footer={[
                    <Button key="close" onClick={() => setPreviewModalVisible(false)}>
                        关闭
                    </Button>
                ]}
            >
                {previewComment && (
                    <Space direction="vertical" style={{ width: '100%' }} size="large">
                        {previewComment.ai_comment && (
                            <div>
                                <Title level={5}>
                                    <CommentOutlined /> AI评语
                                </Title>
                                <Paragraph style={{ background: '#e6f7ff', padding: 16, borderRadius: 4, whiteSpace: 'pre-wrap' }}>
                                    {previewComment.ai_comment}
                                </Paragraph>
                            </div>
                        )}

                        {previewComment.teacher_comment && (
                            <div>
                                <Title level={5}>
                                    <EditOutlined /> 教师评语
                                </Title>
                                <Paragraph style={{ background: '#f6ffed', padding: 16, borderRadius: 4, whiteSpace: 'pre-wrap' }}>
                                    {previewComment.teacher_comment}
                                </Paragraph>
                            </div>
                        )}

                        {previewComment.updated_at && (
                            <Text type="secondary">更新时间: {previewComment.updated_at}</Text>
                        )}
                    </Space>
                )}
            </Modal>
        </div>
    )
}

export default CommentManagement
