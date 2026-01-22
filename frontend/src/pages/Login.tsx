import { useState } from 'react'
import { Form, Input, Button, Card, message, Tabs, Select, Row, Col, Modal } from 'antd'
import { UserOutlined, LockOutlined, PhoneOutlined, MailOutlined, IdcardOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../services/api'
import { useAuthStore } from '../stores/authStore'

const { Option } = Select

const Login = () => {
  const [loading, setLoading] = useState(false)
  const [registerLoading, setRegisterLoading] = useState(false)
  const navigate = useNavigate()
  const setAuth = useAuthStore((state) => state.setAuth)
  const [loginForm] = Form.useForm()
  const [registerForm] = Form.useForm()

  // 登录处理
  const onLogin = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      const res = await authApi.login(values.username, values.password)
      const { access_token, user } = res.data
      setAuth(access_token, user)
      message.success('登录成功')
      navigate('/dashboard')
    } catch (error: any) {
      message.error(error.response?.data?.detail || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  // 教师注册处理
  const onRegister = async (values: any) => {
    if (values.password !== values.confirmPassword) {
      message.error('两次输入的密码不一致')
      return
    }

    setRegisterLoading(true)
    try {
      const res = await authApi.registerTeacher({
        username: values.username,
        password: values.password,
        real_name: values.real_name,
        gender: values.gender || 'female',
        phone: values.phone,
        email: values.email,
        subjects: values.subjects,
      })

      if (res.data.success) {
        // 检查是否需要等待授权
        if (res.data.pending_approval) {
          Modal.success({
            title: '注册成功',
            content: (
              <div>
                <p>{res.data.message}</p>
                <p style={{ color: '#666', marginTop: 12 }}>
                  请联系管理员进行账号授权后再登录。
                </p>
              </div>
            ),
            okText: '我知道了',
          })
          // 重置表单
          registerForm.resetFields()
        } else if (res.data.access_token) {
          // 如果返回了token，直接登录
          const { access_token, user } = res.data
          setAuth(access_token, user)
          message.success('注册成功，已自动登录')
          navigate('/dashboard')
        }
      } else {
        message.error(res.data.message || '注册失败')
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '注册失败')
    } finally {
      setRegisterLoading(false)
    }
  }


  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <Card style={{ width: 480, boxShadow: '0 10px 40px rgba(0,0,0,0.2)' }}>
        <h2 style={{ textAlign: 'center', marginBottom: 24, fontSize: 20 }}>学生成长综合素质评价系统</h2>

        <Tabs
          defaultActiveKey="login"
          centered
          items={[
            {
              key: 'login',
              label: '登录',
              children: (
                <Form form={loginForm} onFinish={onLogin} size="large">
                  <Form.Item
                    name="username"
                    rules={[{ required: true, message: '请输入用户名' }]}
                  >
                    <Input prefix={<UserOutlined />} placeholder="用户名" />
                  </Form.Item>
                  <Form.Item
                    name="password"
                    rules={[{ required: true, message: '请输入密码' }]}
                  >
                    <Input.Password prefix={<LockOutlined />} placeholder="密码" />
                  </Form.Item>
                  <Form.Item>
                    <Button type="primary" htmlType="submit" loading={loading} block>
                      登录
                    </Button>
                  </Form.Item>
                  <div style={{ textAlign: 'center', color: '#999', fontSize: 12 }}>
                    默认管理员: admin / admin123
                  </div>
                </Form>
              ),
            },
            {
              key: 'register',
              label: '教师注册',
              children: (
                <Form form={registerForm} onFinish={onRegister} size="large" layout="vertical">
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        name="username"
                        label="用户名"
                        rules={[
                          { required: true, message: '请输入用户名' },
                          { pattern: /^[a-zA-Z0-9_]{4,20}$/, message: '4-20位字母、数字或下划线' }
                        ]}
                      >
                        <Input prefix={<UserOutlined />} placeholder="登录用户名" />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        name="real_name"
                        label="真实姓名"
                        rules={[{ required: true, message: '请输入真实姓名' }]}
                      >
                        <Input prefix={<IdcardOutlined />} placeholder="真实姓名" />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        name="password"
                        label="密码"
                        rules={[
                          { required: true, message: '请输入密码' },
                          { min: 6, message: '密码至少6位' }
                        ]}
                      >
                        <Input.Password prefix={<LockOutlined />} placeholder="密码" />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        name="confirmPassword"
                        label="确认密码"
                        rules={[
                          { required: true, message: '请确认密码' },
                          ({ getFieldValue }) => ({
                            validator(_, value) {
                              if (!value || getFieldValue('password') === value) {
                                return Promise.resolve()
                              }
                              return Promise.reject(new Error('两次密码不一致'))
                            },
                          }),
                        ]}
                      >
                        <Input.Password prefix={<LockOutlined />} placeholder="确认密码" />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item name="gender" label="性别" initialValue="female">
                        <Select>
                          <Option value="female">女</Option>
                          <Option value="male">男</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name="subjects" label="任教科目">
                        <Select placeholder="选择任教科目" allowClear>
                          <Option value="语文">语文</Option>
                          <Option value="数学">数学</Option>
                          <Option value="英语">英语</Option>
                          <Option value="科学">科学</Option>
                          <Option value="道德与法治">道德与法治</Option>
                          <Option value="音乐">音乐</Option>
                          <Option value="美术">美术</Option>
                          <Option value="体育">体育</Option>
                          <Option value="信息技术">信息技术</Option>
                          <Option value="书法">书法</Option>
                          <Option value="综合实践">综合实践</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                  </Row>

                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item name="phone" label="手机号码">
                        <Input prefix={<PhoneOutlined />} placeholder="手机号（选填）" />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name="email" label="邮箱">
                        <Input prefix={<MailOutlined />} placeholder="邮箱（选填）" />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Form.Item>
                    <Button type="primary" htmlType="submit" loading={registerLoading} block>
                      注册并登录
                    </Button>
                  </Form.Item>
                </Form>
              ),
            },
            {
              key: 'student',
              label: '学生查询',
              children: (
                <div style={{ textAlign: 'center', padding: 20 }}>
                  <p style={{ marginBottom: 16, color: '#666' }}>
                    学生可以通过学号和姓名查询自己的评价数据
                  </p>
                  <Button type="primary" onClick={() => navigate('/student')}>
                    进入学生查询页面
                  </Button>
                </div>
              ),
            },
          ]}
        />
      </Card>
    </div>
  )
}

export default Login
