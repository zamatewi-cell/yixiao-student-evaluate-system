import { useState } from 'react'
import { Form, Input, Button, Card, message, Tabs } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../services/api'
import { useAuthStore } from '../stores/authStore'

const Login = () => {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const setAuth = useAuthStore((state) => state.setAuth)

  const onFinish = async (values: { username: string; password: string }) => {
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

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <Card style={{ width: 400, boxShadow: '0 10px 40px rgba(0,0,0,0.2)' }}>
        <h2 style={{ textAlign: 'center', marginBottom: 24 }}>学生成长综合素质评价系统</h2>
        
        <Tabs
          defaultActiveKey="admin"
          centered
          items={[
            {
              key: 'admin',
              label: '管理员/教师登录',
              children: (
                <Form onFinish={onFinish} size="large">
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
        
        <div style={{ textAlign: 'center', marginTop: 16, color: '#999', fontSize: 12 }}>
          默认管理员: admin / admin123
        </div>
      </Card>
    </div>
  )
}

export default Login
