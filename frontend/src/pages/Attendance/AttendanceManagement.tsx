import React, { useState, useEffect, useCallback } from 'react'
import {
    Card, Table, Button, Select, DatePicker, Tag, Space, message,
    Row, Col, Statistic, Modal, Form, Input, Radio, Divider, Typography
} from 'antd'
import {
    CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined,
    TeamOutlined, SaveOutlined, ReloadOutlined
} from '@ant-design/icons'
import axios from 'axios'
import dayjs from 'dayjs'

const { Option } = Select
const { TextArea } = Input

interface Student {
    student_id: number
    student_no: string
    student_name: string
    status: string | null
    leave_type: string | null
    reason: string | null
}

interface AttendanceStats {
    total_students: number
    present_count: number
    absent_count: number
    late_count: number
    sick_leave_count: number
    personal_leave_count: number
}

const AttendanceManagement: React.FC = () => {
    const [loading, setLoading] = useState(false)
    const [saving, setSaving] = useState(false)
    const [classes, setClasses] = useState<any[]>([])
    const [selectedClass, setSelectedClass] = useState<number | null>(null)
    const [selectedDate, setSelectedDate] = useState<dayjs.Dayjs>(dayjs())
    const [students, setStudents] = useState<Student[]>([])
    const [editingRecord, setEditingRecord] = useState<any>(null)
    const [modalVisible, setModalVisible] = useState(false)
    const [form] = Form.useForm()

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

    // 获取考勤数据
    const fetchAttendance = useCallback(async () => {
        if (!selectedClass || !selectedDate) return

        setLoading(true)
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get(`/api/attendance/class/${selectedClass}`, {
                headers: { Authorization: `Bearer ${token}` },
                params: { date: selectedDate.format('YYYY-MM-DD') }
            })
            setStudents(response.data.data || [])
        } catch (error) {
            message.error('获取考勤数据失败')
        } finally {
            setLoading(false)
        }
    }, [selectedClass, selectedDate])

    useEffect(() => {
        fetchClasses()
    }, [fetchClasses])

    useEffect(() => {
        fetchAttendance()
    }, [fetchAttendance])

    // 统计数据
    const getStats = (): AttendanceStats => {
        const stats: AttendanceStats = {
            total_students: students.length,
            present_count: 0,
            absent_count: 0,
            late_count: 0,
            sick_leave_count: 0,
            personal_leave_count: 0
        }
        students.forEach(s => {
            switch (s.status) {
                case 'present': stats.present_count++; break
                case 'absent': stats.absent_count++; break
                case 'late': stats.late_count++; break
                case 'sick_leave': stats.sick_leave_count++; break
                case 'personal_leave': stats.personal_leave_count++; break
                default: break
            }
        })
        return stats
    }

    // 快速设置全部出勤
    const setAllPresent = () => {
        setStudents(prev => prev.map(s => ({ ...s, status: 'present', leave_type: null, reason: null })))
    }

    // 更新单个学生状态
    const updateStudentStatus = (studentId: number, status: string) => {
        if (status === 'sick_leave' || status === 'personal_leave') {
            // 打开模态框填写原因
            const student = students.find(s => s.student_id === studentId)
            setEditingRecord({ ...student, status })
            form.setFieldsValue({
                leave_type: status === 'sick_leave' ? 'sick' : 'personal',
                reason: ''
            })
            setModalVisible(true)
        } else {
            setStudents(prev => prev.map(s =>
                s.student_id === studentId
                    ? { ...s, status, leave_type: null, reason: null }
                    : s
            ))
        }
    }

    // 保存请假原因
    const handleSaveLeave = async () => {
        try {
            const values = await form.validateFields()
            setStudents(prev => prev.map(s =>
                s.student_id === editingRecord.student_id
                    ? { ...s, status: editingRecord.status, leave_type: values.leave_type, reason: values.reason }
                    : s
            ))
            setModalVisible(false)
            setEditingRecord(null)
            form.resetFields()
        } catch (error) {
            // 表单验证失败
        }
    }

    // 批量保存考勤
    const saveAttendance = async () => {
        setSaving(true)
        try {
            const token = localStorage.getItem('token')
            const records = students.map(s => ({
                student_id: s.student_id,
                status: s.status || 'present',
                leave_type: s.leave_type,
                reason: s.reason
            }))

            await axios.post('/api/attendance/batch', {
                date: selectedDate.format('YYYY-MM-DD'),
                records
            }, {
                headers: { Authorization: `Bearer ${token}` }
            })

            message.success('考勤保存成功')
            fetchAttendance()
        } catch (error: any) {
            message.error('保存失败: ' + (error.response?.data?.detail || error.message))
        } finally {
            setSaving(false)
        }
    }

    // 状态显示
    const renderStatus = (status: string | null) => {
        const statusMap: { [key: string]: { color: string; text: string; icon: React.ReactNode } } = {
            'present': { color: 'success', text: '出勤', icon: <CheckCircleOutlined /> },
            'absent': { color: 'error', text: '缺勤', icon: <CloseCircleOutlined /> },
            'late': { color: 'warning', text: '迟到', icon: <ClockCircleOutlined /> },
            'leave_early': { color: 'orange', text: '早退', icon: <ClockCircleOutlined /> },
            'sick_leave': { color: 'blue', text: '病假', icon: <ClockCircleOutlined /> },
            'personal_leave': { color: 'purple', text: '事假', icon: <ClockCircleOutlined /> }
        }
        const info = statusMap[status || ''] || { color: 'default', text: '未记录', icon: null }
        return <Tag color={info.color} icon={info.icon}>{info.text}</Tag>
    }

    const stats = getStats()

    const columns = [
        {
            title: '学号',
            dataIndex: 'student_no',
            key: 'student_no',
            width: 100
        },
        {
            title: '姓名',
            dataIndex: 'student_name',
            key: 'student_name',
            width: 100
        },
        {
            title: '状态',
            dataIndex: 'status',
            key: 'status',
            width: 100,
            render: (status: string) => renderStatus(status)
        },
        {
            title: '原因',
            dataIndex: 'reason',
            key: 'reason',
            ellipsis: true
        },
        {
            title: '操作',
            key: 'action',
            width: 320,
            render: (_: any, record: Student) => (
                <Space size="small">
                    <Button
                        type={record.status === 'present' ? 'primary' : 'default'}
                        size="small"
                        onClick={() => updateStudentStatus(record.student_id, 'present')}
                    >
                        出勤
                    </Button>
                    <Button
                        type={record.status === 'absent' ? 'primary' : 'default'}
                        danger={record.status === 'absent'}
                        size="small"
                        onClick={() => updateStudentStatus(record.student_id, 'absent')}
                    >
                        缺勤
                    </Button>
                    <Button
                        type={record.status === 'late' ? 'primary' : 'default'}
                        size="small"
                        onClick={() => updateStudentStatus(record.student_id, 'late')}
                        style={record.status === 'late' ? { background: '#faad14', borderColor: '#faad14' } : {}}
                    >
                        迟到
                    </Button>
                    <Button
                        type={record.status === 'sick_leave' ? 'primary' : 'default'}
                        size="small"
                        onClick={() => updateStudentStatus(record.student_id, 'sick_leave')}
                    >
                        病假
                    </Button>
                    <Button
                        type={record.status === 'personal_leave' ? 'primary' : 'default'}
                        size="small"
                        onClick={() => updateStudentStatus(record.student_id, 'personal_leave')}
                    >
                        事假
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
                        <span>考勤管理</span>
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
                            {classes.map(cls => (
                                <Option key={cls.id} value={cls.id}>{cls.name}</Option>
                            ))}
                        </Select>
                        <DatePicker
                            value={selectedDate}
                            onChange={(date) => date && setSelectedDate(date)}
                            allowClear={false}
                        />
                        <Button icon={<ReloadOutlined />} onClick={fetchAttendance}>
                            刷新
                        </Button>
                    </Space>
                }
            >
                {/* 统计卡片 */}
                <Row gutter={16} style={{ marginBottom: 24 }}>
                    <Col span={4}>
                        <Statistic
                            title="学生总数"
                            value={stats.total_students}
                            suffix="人"
                            valueStyle={{ color: '#1890ff' }}
                        />
                    </Col>
                    <Col span={4}>
                        <Statistic
                            title="出勤"
                            value={stats.present_count}
                            suffix="人"
                            valueStyle={{ color: '#52c41a' }}
                        />
                    </Col>
                    <Col span={4}>
                        <Statistic
                            title="缺勤"
                            value={stats.absent_count}
                            suffix="人"
                            valueStyle={{ color: '#ff4d4f' }}
                        />
                    </Col>
                    <Col span={4}>
                        <Statistic
                            title="迟到"
                            value={stats.late_count}
                            suffix="人"
                            valueStyle={{ color: '#faad14' }}
                        />
                    </Col>
                    <Col span={4}>
                        <Statistic
                            title="病假"
                            value={stats.sick_leave_count}
                            suffix="人"
                            valueStyle={{ color: '#1890ff' }}
                        />
                    </Col>
                    <Col span={4}>
                        <Statistic
                            title="事假"
                            value={stats.personal_leave_count}
                            suffix="人"
                            valueStyle={{ color: '#722ed1' }}
                        />
                    </Col>
                </Row>

                <Divider />

                {/* 操作按钮 */}
                <Space style={{ marginBottom: 16 }}>
                    <Button type="primary" onClick={setAllPresent}>
                        <CheckCircleOutlined /> 全部出勤
                    </Button>
                    <Button
                        type="primary"
                        icon={<SaveOutlined />}
                        onClick={saveAttendance}
                        loading={saving}
                    >
                        保存考勤
                    </Button>
                </Space>

                {/* 学生列表 */}
                <Table
                    dataSource={students}
                    columns={columns}
                    rowKey="student_id"
                    loading={loading}
                    pagination={false}
                    size="middle"
                />
            </Card>

            {/* 请假原因模态框 */}
            <Modal
                title={`${editingRecord?.student_name} - ${editingRecord?.status === 'sick_leave' ? '病假' : '事假'}`}
                open={modalVisible}
                onOk={handleSaveLeave}
                onCancel={() => {
                    setModalVisible(false)
                    setEditingRecord(null)
                    form.resetFields()
                }}
                okText="确定"
                cancelText="取消"
            >
                <Form form={form} layout="vertical">
                    <Form.Item
                        name="leave_type"
                        label="请假类型"
                        rules={[{ required: true, message: '请选择请假类型' }]}
                    >
                        <Radio.Group>
                            <Radio value="sick">病假</Radio>
                            <Radio value="personal">事假</Radio>
                            <Radio value="other">其他</Radio>
                        </Radio.Group>
                    </Form.Item>
                    <Form.Item
                        name="reason"
                        label="请假原因"
                    >
                        <TextArea rows={3} placeholder="请输入请假原因（可选）" />
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    )
}

export default AttendanceManagement
