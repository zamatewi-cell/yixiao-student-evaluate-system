import React, { useState, useEffect, useCallback } from 'react'
import {
    Card, Table, Button, Select, Tag, Space, message, Modal, Form,
    Row, Col, Descriptions, Switch, Badge, Divider, Typography, Tooltip
} from 'antd'
import {
    UserOutlined, TeamOutlined, SettingOutlined, CheckCircleOutlined,
    CloseCircleOutlined, CrownOutlined, BookOutlined
} from '@ant-design/icons'
import axios from 'axios'

const { Option } = Select
const { Text, Title } = Typography

interface Teacher {
    id: number
    name: string
    employee_no: string
    is_head_teacher: boolean
    teacher_type: string
    subjects: string
    head_class_name?: string
}

interface TeacherSubject {
    id: number
    class_id: number
    class_name: string
    subject_name: string
    grade_name: string
    semester_name: string
}

const TeacherRoleManagement: React.FC = () => {
    const [loading, setLoading] = useState(false)
    const [teachers, setTeachers] = useState<Teacher[]>([])
    const [selectedTeacher, setSelectedTeacher] = useState<Teacher | null>(null)
    const [teacherSubjects, setTeacherSubjects] = useState<TeacherSubject[]>([])
    const [detailModalVisible, setDetailModalVisible] = useState(false)
    const [assignModalVisible, setAssignModalVisible] = useState(false)
    const [classes, setClasses] = useState<any[]>([])
    const [semesters, setSemesters] = useState<any[]>([])
    const [form] = Form.useForm()

    // 获取教师列表
    const fetchTeachers = useCallback(async () => {
        setLoading(true)
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/admin/teachers', {
                headers: { Authorization: `Bearer ${token}` }
            })
            setTeachers(response.data.data || [])
        } catch (error) {
            message.error('获取教师列表失败')
        } finally {
            setLoading(false)
        }
    }, [])

    // 获取班级列表
    const fetchClasses = useCallback(async () => {
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/admin/classes', {
                headers: { Authorization: `Bearer ${token}` }
            })
            setClasses(response.data.data || [])
        } catch (error) {
            console.error('获取班级失败')
        }
    }, [])

    // 获取学期列表
    const fetchSemesters = useCallback(async () => {
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/teacher/semesters', {
                headers: { Authorization: `Bearer ${token}` }
            })
            setSemesters(response.data.data || [])
        } catch (error) {
            console.error('获取学期失败')
        }
    }, [])

    useEffect(() => {
        fetchTeachers()
        fetchClasses()
        fetchSemesters()
    }, [fetchTeachers, fetchClasses, fetchSemesters])

    // 更新教师角色
    const handleUpdateRole = async (teacherId: number, isHeadTeacher: boolean, teacherType: string) => {
        try {
            const token = localStorage.getItem('token')
            await axios.put(`/api/teacher-role/update/${teacherId}`, {
                is_head_teacher: isHeadTeacher,
                teacher_type: teacherType
            }, {
                headers: { Authorization: `Bearer ${token}` }
            })
            message.success('角色更新成功')
            fetchTeachers()
        } catch (error) {
            message.error('更新失败')
        }
    }

    // 分配任课
    const handleAssignSubject = async () => {
        try {
            const values = await form.validateFields()
            const token = localStorage.getItem('token')

            await axios.post('/api/teacher-role/assign-subject', {
                class_id: values.class_id,
                subject_name: values.subject_name,
                semester_id: values.semester_id
            }, {
                headers: { Authorization: `Bearer ${token}` },
                params: { teacher_id: selectedTeacher?.id }
            })

            message.success('任课分配成功')
            setAssignModalVisible(false)
            form.resetFields()
        } catch (error) {
            message.error('分配失败')
        }
    }

    // 教师类型显示
    const renderTeacherType = (type: string, isHead: boolean) => {
        if (isHead) {
            return <Tag color="gold" icon={<CrownOutlined />}>班主任</Tag>
        }
        switch (type) {
            case 'head_teacher':
                return <Tag color="gold" icon={<CrownOutlined />}>班主任</Tag>
            case 'both':
                return (
                    <Space>
                        <Tag color="gold" icon={<CrownOutlined />}>班主任</Tag>
                        <Tag color="blue" icon={<BookOutlined />}>科任教师</Tag>
                    </Space>
                )
            default:
                return <Tag color="blue" icon={<BookOutlined />}>科任教师</Tag>
        }
    }

    const columns = [
        {
            title: '工号',
            dataIndex: 'employee_no',
            key: 'employee_no',
            width: 100
        },
        {
            title: '姓名',
            dataIndex: 'name',
            key: 'name',
            width: 100
        },
        {
            title: '角色类型',
            key: 'role',
            width: 200,
            render: (_: any, record: Teacher) => renderTeacherType(record.teacher_type, record.is_head_teacher)
        },
        {
            title: '任教科目',
            dataIndex: 'subjects',
            key: 'subjects',
            ellipsis: true,
            render: (text: string) => text || '-'
        },
        {
            title: '班主任班级',
            dataIndex: 'head_class_name',
            key: 'head_class_name',
            render: (text: string) => text ? <Tag color="green">{text}</Tag> : '-'
        },
        {
            title: '操作',
            key: 'action',
            width: 300,
            render: (_: any, record: Teacher) => (
                <Space>
                    <Tooltip title={record.is_head_teacher ? '取消班主任' : '设为班主任'}>
                        <Switch
                            checkedChildren="班主任"
                            unCheckedChildren="科任"
                            checked={record.is_head_teacher}
                            onChange={(checked) => handleUpdateRole(record.id, checked, checked ? 'head_teacher' : 'subject_teacher')}
                        />
                    </Tooltip>
                    <Button
                        size="small"
                        icon={<SettingOutlined />}
                        onClick={() => {
                            setSelectedTeacher(record)
                            setAssignModalVisible(true)
                        }}
                    >
                        分配任课
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
                        <TeamOutlined />
                        <span>教师权限管理</span>
                    </Space>
                }
                extra={
                    <Button icon={<SettingOutlined />} onClick={fetchTeachers}>
                        刷新
                    </Button>
                }
            >
                {/* 权限说明 */}
                <Row gutter={16} style={{ marginBottom: 24 }}>
                    <Col span={12}>
                        <Card size="small" title={<><CrownOutlined style={{ color: '#faad14' }} /> 班主任权限</>}>
                            <ul style={{ paddingLeft: 20, margin: 0 }}>
                                <li><CheckCircleOutlined style={{ color: '#52c41a' }} /> 管理本班考勤</li>
                                <li><CheckCircleOutlined style={{ color: '#52c41a' }} /> 查看本班完整数据</li>
                                <li><CheckCircleOutlined style={{ color: '#52c41a' }} /> 生成学生评语</li>
                                <li><CheckCircleOutlined style={{ color: '#52c41a' }} /> 查看班级统计报表</li>
                                <li><CheckCircleOutlined style={{ color: '#52c41a' }} /> 管理学生基本信息</li>
                            </ul>
                        </Card>
                    </Col>
                    <Col span={12}>
                        <Card size="small" title={<><BookOutlined style={{ color: '#1890ff' }} /> 科任教师权限</>}>
                            <ul style={{ paddingLeft: 20, margin: 0 }}>
                                <li><CheckCircleOutlined style={{ color: '#52c41a' }} /> 录入任教科目成绩</li>
                                <li><CheckCircleOutlined style={{ color: '#52c41a' }} /> 查看任教班级成绩</li>
                                <li><CheckCircleOutlined style={{ color: '#52c41a' }} /> 撰写试卷分析</li>
                                <li><CloseCircleOutlined style={{ color: '#ff4d4f' }} /> 不可管理考勤</li>
                                <li><CloseCircleOutlined style={{ color: '#ff4d4f' }} /> 不可生成评语</li>
                            </ul>
                        </Card>
                    </Col>
                </Row>

                <Divider />

                <Table
                    dataSource={teachers}
                    columns={columns}
                    rowKey="id"
                    loading={loading}
                    pagination={{ pageSize: 10 }}
                />
            </Card>

            {/* 分配任课模态框 */}
            <Modal
                title={`分配任课 - ${selectedTeacher?.name || ''}`}
                open={assignModalVisible}
                onOk={handleAssignSubject}
                onCancel={() => {
                    setAssignModalVisible(false)
                    form.resetFields()
                }}
                okText="分配"
                cancelText="取消"
            >
                <Form form={form} layout="vertical">
                    <Form.Item
                        name="class_id"
                        label="班级"
                        rules={[{ required: true, message: '请选择班级' }]}
                    >
                        <Select placeholder="选择班级">
                            {classes.map(c => (
                                <Option key={c.id} value={c.id}>{c.name}</Option>
                            ))}
                        </Select>
                    </Form.Item>
                    <Form.Item
                        name="subject_name"
                        label="任教科目"
                        rules={[{ required: true, message: '请输入科目名称' }]}
                    >
                        <Select placeholder="选择或输入科目" mode="tags" maxCount={1}>
                            <Option value="语文">语文</Option>
                            <Option value="数学">数学</Option>
                            <Option value="英语">英语</Option>
                            <Option value="科学">科学</Option>
                            <Option value="道法">道德与法治</Option>
                            <Option value="体育">体育</Option>
                            <Option value="音乐">音乐</Option>
                            <Option value="美术">美术</Option>
                        </Select>
                    </Form.Item>
                    <Form.Item
                        name="semester_id"
                        label="学期"
                        rules={[{ required: true, message: '请选择学期' }]}
                    >
                        <Select placeholder="选择学期">
                            {semesters.map(s => (
                                <Option key={s.id} value={s.id}>
                                    {s.name} {s.is_current && <Tag color="green">当前</Tag>}
                                </Option>
                            ))}
                        </Select>
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    )
}

export default TeacherRoleManagement
