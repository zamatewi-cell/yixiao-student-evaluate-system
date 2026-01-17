import { useState, ReactNode } from 'react'
import { Layout, Menu, Button, Dropdown, Avatar, Space } from 'antd'
import {
  DashboardOutlined,
  TeamOutlined,
  UserOutlined,
  CalendarOutlined,
  FormOutlined,
  BarChartOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SettingOutlined,
  CommentOutlined,
  EditOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'

const { Header, Sider, Content } = Layout

interface AdminLayoutProps {
  children: ReactNode
}

const AdminLayout = ({ children }: AdminLayoutProps) => {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()

  const isAdmin = user?.role === 'admin'
  const isTeacher = user?.role === 'teacher' || user?.role === 'admin'

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    ...(isAdmin ? [
      {
        key: 'admin-group',
        icon: <SettingOutlined />,
        label: '系统管理',
        children: [
          {
            key: '/semesters',
            icon: <CalendarOutlined />,
            label: '学期管理',
          },
          {
            key: '/classes',
            icon: <TeamOutlined />,
            label: '班级管理',
          },
          {
            key: '/students',
            icon: <UserOutlined />,
            label: '学生管理',
          },
          {
            key: '/teachers',
            icon: <TeamOutlined />,
            label: '教师管理',
          },
          {
            key: '/indicators',
            icon: <SettingOutlined />,
            label: '评价指标',
          },
        ]
      },
      {
        key: '/statistics',
        icon: <BarChartOutlined />,
        label: '统计报表',
      },
    ] : []),
    ...(isTeacher ? [
      {
        key: 'teacher-group',
        icon: <FormOutlined />,
        label: '教师功能',
        children: [
          {
            key: '/data-entry',
            icon: <FormOutlined />,
            label: '数据录入',
          },
          {
            key: '/comment-management',
            icon: <CommentOutlined />,
            label: '评语管理',
          },
          {
            key: '/calligraphy',
            icon: <EditOutlined />,
            label: '书法批改',
          },
        ]
      },
    ] : []),
  ]

  const handleMenuClick = ({ key }: { key: string }) => {
    if (!key.includes('-group')) {
      navigate(key)
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人信息',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        theme="light"
        width={220}
        style={{ boxShadow: '2px 0 8px rgba(0,0,0,0.08)' }}
      >
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderBottom: '1px solid #f0f0f0'
        }}>
          <h2 style={{
            margin: 0,
            fontSize: collapsed ? 16 : 18,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            {collapsed ? '评价' : '学生综合素质评价'}
          </h2>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          defaultOpenKeys={['admin-group', 'teacher-group']}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ border: 'none' }}
        />
      </Sider>
      <Layout>
        <Header style={{
          padding: '0 24px',
          background: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
        }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
          />
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar style={{ backgroundColor: '#667eea' }}>
                {user?.real_name?.[0] || user?.username?.[0] || 'U'}
              </Avatar>
              <span>{user?.real_name || user?.username}</span>
            </Space>
          </Dropdown>
        </Header>
        <Content style={{
          margin: 16,
          padding: 0,
          background: '#f0f2f5',
          borderRadius: 8,
          minHeight: 280,
          overflow: 'auto'
        }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  )
}

export default AdminLayout
