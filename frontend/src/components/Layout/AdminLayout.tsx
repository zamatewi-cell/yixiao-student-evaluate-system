import { useState, ReactNode } from 'react'
import { Layout, Menu, Button, Dropdown, Avatar, Space, Tag } from 'antd'
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
  LinkOutlined,
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

  // 根据角色生成菜单项
  const getMenuItems = () => {
    // 教师菜单（简洁版）
    if (user?.role === 'teacher') {
      return [
        {
          key: '/dashboard',
          icon: <DashboardOutlined />,
          label: '工作台',
        },
        {
          key: '/attendance',
          icon: <CalendarOutlined />,
          label: '考勤管理',
        },
        {
          key: '/score-entry',
          icon: <FormOutlined />,
          label: '成绩录入',
        },
        {
          key: '/wrong-answer',
          icon: <FormOutlined />,
          label: '错题分析',
        },
        {
          key: '/data-entry',
          icon: <FormOutlined />,
          label: '素质评价',
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
        {
          key: '/calligraphy-assignment',
          icon: <LinkOutlined />,
          label: '作品分配',
        },
      ]
    }

    // 管理员菜单（完整版）
    return [
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
              key: '/teacher-roles',
              icon: <SettingOutlined />,
              label: '权限管理',
            },
            {
              key: '/indicators',
              icon: <SettingOutlined />,
              label: '评价指标',
            },
            {
              key: '/exam-management',
              icon: <FormOutlined />,
              label: '考试管理',
            },
          ]
        },
        {
          key: '/statistics',
          icon: <BarChartOutlined />,
          label: '统计报表',
        },
        {
          key: 'system-group',
          icon: <SettingOutlined />,
          label: '系统工具',
          children: [
            {
              key: '/notices',
              icon: <SettingOutlined />,
              label: '通知公告',
            },
            {
              key: '/audit-logs',
              icon: <SettingOutlined />,
              label: '操作日志',
            },
            {
              key: '/system-settings',
              icon: <SettingOutlined />,
              label: '系统设置',
            },
          ]
        },
      ] : []),
      ...(isTeacher ? [
        {
          key: 'teacher-group',
          icon: <FormOutlined />,
          label: '教师功能',
          children: [
            {
              key: '/attendance',
              icon: <CalendarOutlined />,
              label: '考勤管理',
            },
            {
              key: '/score-entry',
              icon: <FormOutlined />,
              label: '成绩录入',
            },
            {
              key: '/wrong-answer',
              icon: <FormOutlined />,
              label: '错题分析',
            },
            {
              key: '/data-entry',
              icon: <FormOutlined />,
              label: '素质评价',
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
            {
              key: '/calligraphy-assignment',
              icon: <LinkOutlined />,
              label: '作品分配',
            },
          ]
        },
      ] : []),
    ]
  }

  const menuItems = getMenuItems()

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
      label: '个人资料',
      onClick: () => navigate('/profile'),
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  // 获取角色标签
  const getRoleTag = () => {
    if (user?.role === 'admin') {
      return <Tag color="red">管理员</Tag>
    } else if (user?.role === 'teacher') {
      return <Tag color="blue">教师</Tag>
    }
    return null
  }

  // 获取系统标题
  const getSystemTitle = () => {
    if (user?.role === 'teacher') {
      return collapsed ? '教师' : '教师工作台'
    }
    return collapsed ? '评价' : '学生综合素质评价'
  }

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
            {getSystemTitle()}
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
          <Space>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
            />
            {getRoleTag()}
          </Space>
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar style={{ backgroundColor: user?.role === 'admin' ? '#ff4d4f' : '#667eea' }}>
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
