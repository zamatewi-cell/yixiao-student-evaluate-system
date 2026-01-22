import React, { useState, useEffect } from 'react'
import {
    Card,
    Form,
    Input,
    Button,
    Avatar,
    message,
    Space,
    Typography,
    Divider,
    Row,
    Col,
    Tag,
    Descriptions,
    Spin,
    Modal
} from 'antd'
import {
    UserOutlined,
    EditOutlined,
    SaveOutlined,
    PhoneOutlined,
    MailOutlined,
    KeyOutlined,
    CheckCircleOutlined,
    ClockCircleOutlined
} from '@ant-design/icons'
import axios from 'axios'
import { useAuthStore } from '../../stores/authStore'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

interface UserProfile {
    id: number
    username: string
    role: string
    real_name: string
    phone: string
    email: string
    avatar: string
    signature: string
    is_active: boolean
    created_at: string
    last_login: string
}

interface TeacherInfo {
    teacher_id: number
    gender: string
    subjects: string
    can_edit: boolean
    class_count: number
}

const Profile: React.FC = () => {
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [editing, setEditing] = useState(false)
    const [profile, setProfile] = useState<UserProfile | null>(null)
    const [teacherInfo, setTeacherInfo] = useState<TeacherInfo | null>(null)
    const [form] = Form.useForm()
    const [passwordForm] = Form.useForm()
    const [passwordModalVisible, setPasswordModalVisible] = useState(false)
    const { user, setAuth } = useAuthStore()

    // 默认头像列表
    const defaultAvatars = [
        'https://api.dicebear.com/7.x/avataaars/svg?seed=1',
        'https://api.dicebear.com/7.x/avataaars/svg?seed=2',
        'https://api.dicebear.com/7.x/avataaars/svg?seed=3',
        'https://api.dicebear.com/7.x/avataaars/svg?seed=4',
        'https://api.dicebear.com/7.x/avataaars/svg?seed=5',
        'https://api.dicebear.com/7.x/avataaars/svg?seed=6',
        'https://api.dicebear.com/7.x/bottts/svg?seed=1',
        'https://api.dicebear.com/7.x/bottts/svg?seed=2',
    ]

    // 获取个人资料
    const fetchProfile = async () => {
        try {
            setLoading(true)
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/auth/profile', {
                headers: { Authorization: `Bearer ${token}` }
            })
            setProfile(response.data.user)
            setTeacherInfo(response.data.teacher_info)
            form.setFieldsValue({
                real_name: response.data.user.real_name,
                phone: response.data.user.phone,
                email: response.data.user.email,
                signature: response.data.user.signature
            })
        } catch (error: any) {
            message.error('获取个人资料失败: ' + (error.response?.data?.detail || error.message))
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchProfile()
    }, [])

    // 保存个人资料
    const handleSave = async () => {
        try {
            const values = await form.validateFields()
            setSaving(true)
            const token = localStorage.getItem('token')
            await axios.put('/api/auth/profile', values, {
                headers: { Authorization: `Bearer ${token}` }
            })
            message.success('个人资料保存成功')
            setEditing(false)

            // 更新本地存储的用户信息
            if (user && values.real_name) {
                const newUser = { ...user, real_name: values.real_name }
                const currentToken = localStorage.getItem('token')
                if (currentToken) {
                    setAuth(currentToken, newUser)
                }
            }

            fetchProfile()
        } catch (error: any) {
            message.error('保存失败: ' + (error.response?.data?.detail || error.message))
        } finally {
            setSaving(false)
        }
    }

    // 更换头像
    const handleAvatarChange = async (avatarUrl: string) => {
        try {
            const token = localStorage.getItem('token')
            await axios.put('/api/auth/profile', { avatar: avatarUrl }, {
                headers: { Authorization: `Bearer ${token}` }
            })
            message.success('头像更换成功')
            fetchProfile()
        } catch (error: any) {
            message.error('头像更换失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    // 修改密码
    const handleChangePassword = async () => {
        try {
            const values = await passwordForm.validateFields()
            if (values.new_password !== values.confirm_password) {
                message.error('两次输入的密码不一致')
                return
            }

            const token = localStorage.getItem('token')
            await axios.post('/api/auth/change-password', {
                old_password: values.old_password,
                new_password: values.new_password
            }, {
                headers: { Authorization: `Bearer ${token}` }
            })
            message.success('密码修改成功')
            setPasswordModalVisible(false)
            passwordForm.resetFields()
        } catch (error: any) {
            message.error('修改密码失败: ' + (error.response?.data?.detail || error.message))
        }
    }

    // 获取角色显示名称
    const getRoleName = (role: string) => {
        const roleMap: { [key: string]: string } = {
            'admin': '管理员',
            'teacher': '教师',
            'student': '学生'
        }
        return roleMap[role] || role
    }

    // 获取角色颜色
    const getRoleColor = (role: string) => {
        const colorMap: { [key: string]: string } = {
            'admin': 'red',
            'teacher': 'blue',
            'student': 'green'
        }
        return colorMap[role] || 'default'
    }

    if (loading) {
        return (
            <div style={{ padding: 24, textAlign: 'center' }}>
                <Spin size="large" />
            </div>
        )
    }

    return (
        <div style={{ padding: 24 }}>
            <Row gutter={24}>
                {/* 左侧：头像和基本信息 */}
                <Col xs={24} md={8}>
                    <Card>
                        <div style={{ textAlign: 'center', marginBottom: 24 }}>
                            <Avatar
                                size={120}
                                src={profile?.avatar}
                                icon={<UserOutlined />}
                                style={{
                                    backgroundColor: profile?.avatar ? 'transparent' : '#1890ff',
                                    marginBottom: 16
                                }}
                            />
                            <Title level={3} style={{ margin: 0 }}>
                                {profile?.real_name || profile?.username}
                            </Title>
                            <Space style={{ marginTop: 8 }}>
                                <Tag color={getRoleColor(profile?.role || '')}>
                                    {getRoleName(profile?.role || '')}
                                </Tag>
                                {profile?.is_active ? (
                                    <Tag color="success" icon={<CheckCircleOutlined />}>已激活</Tag>
                                ) : (
                                    <Tag color="warning" icon={<ClockCircleOutlined />}>待审核</Tag>
                                )}
                            </Space>
                            {profile?.signature && (
                                <Paragraph
                                    type="secondary"
                                    style={{ marginTop: 16, fontStyle: 'italic' }}
                                >
                                    "{profile.signature}"
                                </Paragraph>
                            )}
                        </div>

                        <Divider>选择头像</Divider>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center' }}>
                            {defaultAvatars.map((url, index) => (
                                <Avatar
                                    key={index}
                                    size={48}
                                    src={url}
                                    style={{
                                        cursor: 'pointer',
                                        border: profile?.avatar === url ? '2px solid #1890ff' : '2px solid transparent'
                                    }}
                                    onClick={() => handleAvatarChange(url)}
                                />
                            ))}
                        </div>

                        <Divider />
                        <Descriptions column={1} size="small">
                            <Descriptions.Item label="用户名">
                                {profile?.username}
                            </Descriptions.Item>
                            <Descriptions.Item label="注册时间">
                                {profile?.created_at?.split(' ')[0] || '-'}
                            </Descriptions.Item>
                            <Descriptions.Item label="最后登录">
                                {profile?.last_login || '-'}
                            </Descriptions.Item>
                        </Descriptions>
                    </Card>
                </Col>

                {/* 右侧：详细信息和编辑 */}
                <Col xs={24} md={16}>
                    <Card
                        title={
                            <Space>
                                <EditOutlined />
                                <span>个人资料</span>
                            </Space>
                        }
                        extra={
                            editing ? (
                                <Space>
                                    <Button onClick={() => setEditing(false)}>取消</Button>
                                    <Button
                                        type="primary"
                                        icon={<SaveOutlined />}
                                        onClick={handleSave}
                                        loading={saving}
                                    >
                                        保存
                                    </Button>
                                </Space>
                            ) : (
                                <Button
                                    type="primary"
                                    icon={<EditOutlined />}
                                    onClick={() => setEditing(true)}
                                >
                                    编辑资料
                                </Button>
                            )
                        }
                    >
                        <Form
                            form={form}
                            layout="vertical"
                            disabled={!editing}
                        >
                            <Row gutter={16}>
                                <Col span={12}>
                                    <Form.Item
                                        name="real_name"
                                        label="真实姓名"
                                        rules={[{ required: true, message: '请输入真实姓名' }]}
                                    >
                                        <Input
                                            prefix={<UserOutlined />}
                                            placeholder="请输入真实姓名"
                                        />
                                    </Form.Item>
                                </Col>
                                <Col span={12}>
                                    <Form.Item
                                        name="phone"
                                        label="联系电话"
                                    >
                                        <Input
                                            prefix={<PhoneOutlined />}
                                            placeholder="请输入联系电话"
                                        />
                                    </Form.Item>
                                </Col>
                            </Row>
                            <Row gutter={16}>
                                <Col span={12}>
                                    <Form.Item
                                        name="email"
                                        label="电子邮箱"
                                        rules={[{ type: 'email', message: '请输入有效的邮箱地址' }]}
                                    >
                                        <Input
                                            prefix={<MailOutlined />}
                                            placeholder="请输入电子邮箱"
                                        />
                                    </Form.Item>
                                </Col>
                                <Col span={12}>
                                    {/* 占位 */}
                                </Col>
                            </Row>
                            <Form.Item
                                name="signature"
                                label="个性签名"
                            >
                                <TextArea
                                    placeholder="写一句话介绍自己..."
                                    rows={2}
                                    maxLength={100}
                                    showCount
                                />
                            </Form.Item>
                        </Form>

                        {/* 教师特有信息 */}
                        {teacherInfo && (
                            <>
                                <Divider>教师信息</Divider>
                                <Descriptions column={2}>
                                    <Descriptions.Item label="任教科目">
                                        {teacherInfo.subjects || '-'}
                                    </Descriptions.Item>
                                    <Descriptions.Item label="管理班级数">
                                        <Tag color="blue">{teacherInfo.class_count} 个</Tag>
                                    </Descriptions.Item>
                                    <Descriptions.Item label="数据编辑权限">
                                        {teacherInfo.can_edit ? (
                                            <Tag color="success" icon={<CheckCircleOutlined />}>已授权</Tag>
                                        ) : (
                                            <Tag color="warning">无权限</Tag>
                                        )}
                                    </Descriptions.Item>
                                </Descriptions>
                            </>
                        )}
                    </Card>

                    {/* 安全设置 */}
                    <Card
                        title={
                            <Space>
                                <KeyOutlined />
                                <span>安全设置</span>
                            </Space>
                        }
                        style={{ marginTop: 16 }}
                    >
                        <Row align="middle" justify="space-between">
                            <Col>
                                <Text strong>登录密码</Text>
                                <br />
                                <Text type="secondary">定期更换密码可以提高账户安全性</Text>
                            </Col>
                            <Col>
                                <Button
                                    type="primary"
                                    ghost
                                    onClick={() => setPasswordModalVisible(true)}
                                >
                                    修改密码
                                </Button>
                            </Col>
                        </Row>
                    </Card>
                </Col>
            </Row>

            {/* 修改密码模态框 */}
            <Modal
                title="修改密码"
                open={passwordModalVisible}
                onOk={handleChangePassword}
                onCancel={() => {
                    setPasswordModalVisible(false)
                    passwordForm.resetFields()
                }}
                okText="确认修改"
                cancelText="取消"
            >
                <Form
                    form={passwordForm}
                    layout="vertical"
                >
                    <Form.Item
                        name="old_password"
                        label="当前密码"
                        rules={[{ required: true, message: '请输入当前密码' }]}
                    >
                        <Input.Password placeholder="请输入当前密码" />
                    </Form.Item>
                    <Form.Item
                        name="new_password"
                        label="新密码"
                        rules={[
                            { required: true, message: '请输入新密码' },
                            { min: 6, message: '密码长度至少6位' }
                        ]}
                    >
                        <Input.Password placeholder="请输入新密码（至少6位）" />
                    </Form.Item>
                    <Form.Item
                        name="confirm_password"
                        label="确认新密码"
                        rules={[{ required: true, message: '请再次输入新密码' }]}
                    >
                        <Input.Password placeholder="请再次输入新密码" />
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    )
}

export default Profile
