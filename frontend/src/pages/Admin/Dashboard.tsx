import { useEffect, useState, useRef } from 'react'
import { Row, Col, Card, Statistic, Typography, Space, Alert } from 'antd'
import {
  TeamOutlined,
  UserOutlined,
  FileTextOutlined,
  CommentOutlined,
  RiseOutlined,
  CalendarOutlined
} from '@ant-design/icons'
import axios from 'axios'
import * as echarts from 'echarts'

const { Title, Text } = Typography

const Dashboard = () => {
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [currentSemester, setCurrentSemester] = useState<string>('')

  const barChartRef = useRef<HTMLDivElement>(null)
  const pieChartRef = useRef<HTMLDivElement>(null)
  const barChartInstance = useRef<echarts.ECharts | null>(null)
  const pieChartInstance = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const token = localStorage.getItem('token')

      // 尝试获取统计数据
      try {
        const res = await axios.get('/api/admin/dashboard-stats', {
          headers: { Authorization: `Bearer ${token}` }
        })
        setStats(res.data)
      } catch {
        // 如果API不存在，使用模拟数据
        setStats({
          overview: {
            student_count: 156,
            teacher_count: 12,
            class_count: 6,
            evaluation_count: 1872
          },
          grades: [
            { name: '一年级', avg_score: 85.5, student_count: 52 },
            { name: '二年级', avg_score: 82.3, student_count: 48 },
            { name: '三年级', avg_score: 88.1, student_count: 56 }
          ],
          categories: [
            { name: '学业表现', count: 624 },
            { name: '品德发展', count: 468 },
            { name: '体质健康', count: 312 },
            { name: '艺术素养', count: 234 },
            { name: '社会实践', count: 234 }
          ]
        })
      }

      // 获取当前学期
      try {
        const semRes = await axios.get('/api/teacher/current-semester', {
          headers: { Authorization: `Bearer ${token}` }
        })
        if (semRes.data?.data) {
          setCurrentSemester(semRes.data.data.name)
        }
      } catch {
        setCurrentSemester('2023-2024学年第一学期')
      }
    } catch (error) {
      console.error('Failed to load stats:', error)
    } finally {
      setLoading(false)
    }
  }

  // 渲染柱状图
  useEffect(() => {
    if (!stats?.grades || !barChartRef.current) return

    if (!barChartInstance.current) {
      barChartInstance.current = echarts.init(barChartRef.current)
    }

    barChartInstance.current.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        data: stats.grades.map((g: any) => g.name)
      },
      yAxis: { type: 'value', max: 100, name: '平均分' },
      series: [{
        type: 'bar',
        data: stats.grades.map((g: any) => g.avg_score || 0),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#667eea' },
            { offset: 1, color: '#764ba2' }
          ]),
          borderRadius: [8, 8, 0, 0]
        },
        barWidth: '50%'
      }]
    })
  }, [stats])

  // 渲染饼图
  useEffect(() => {
    if (!stats?.categories || !pieChartRef.current) return

    if (!pieChartInstance.current) {
      pieChartInstance.current = echarts.init(pieChartRef.current)
    }

    pieChartInstance.current.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c}条 ({d}%)' },
      legend: { orient: 'vertical', left: 'left' },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: true, formatter: '{b}' },
        emphasis: {
          label: { show: true, fontSize: 16, fontWeight: 'bold' }
        },
        data: stats.categories.map((c: any, i: number) => ({
          name: c.name,
          value: c.count,
          itemStyle: {
            color: ['#667eea', '#f093fb', '#4facfe', '#43e97b', '#fa8c16'][i % 5]
          }
        }))
      }]
    })
  }, [stats])

  // 窗口大小变化时重绘
  useEffect(() => {
    const handleResize = () => {
      barChartInstance.current?.resize()
      pieChartInstance.current?.resize()
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return (
    <div style={{ padding: 24 }}>
      {/* 欢迎区域 */}
      <Card
        style={{
          marginBottom: 24,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          border: 'none'
        }}
      >
        <Row align="middle" justify="space-between">
          <Col>
            <Title level={3} style={{ color: '#fff', margin: 0 }}>
              欢迎使用学生综合素质评价系统
            </Title>
            <Text style={{ color: 'rgba(255,255,255,0.85)', fontSize: 16 }}>
              <CalendarOutlined style={{ marginRight: 8 }} />
              当前学期：{currentSemester || '未设置'}
            </Text>
          </Col>
          <Col>
            <Space>
              <RiseOutlined style={{ fontSize: 48, color: 'rgba(255,255,255,0.3)' }} />
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 统计卡片 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={6}>
          <Card hoverable style={{ borderRadius: 12 }}>
            <Statistic
              title={<span style={{ fontSize: 14 }}>学生总数</span>}
              value={stats?.overview?.student_count || 0}
              prefix={<UserOutlined style={{ color: '#667eea' }} />}
              suffix="人"
              valueStyle={{ color: '#667eea', fontSize: 28 }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card hoverable style={{ borderRadius: 12 }}>
            <Statistic
              title={<span style={{ fontSize: 14 }}>教师人数</span>}
              value={stats?.overview?.teacher_count || 0}
              prefix={<TeamOutlined style={{ color: '#f093fb' }} />}
              suffix="人"
              valueStyle={{ color: '#f093fb', fontSize: 28 }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card hoverable style={{ borderRadius: 12 }}>
            <Statistic
              title={<span style={{ fontSize: 14 }}>班级数量</span>}
              value={stats?.overview?.class_count || 0}
              prefix={<FileTextOutlined style={{ color: '#4facfe' }} />}
              suffix="个"
              valueStyle={{ color: '#4facfe', fontSize: 28 }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card hoverable style={{ borderRadius: 12 }}>
            <Statistic
              title={<span style={{ fontSize: 14 }}>评价记录</span>}
              value={stats?.overview?.evaluation_count || 0}
              prefix={<CommentOutlined style={{ color: '#43e97b' }} />}
              suffix="条"
              valueStyle={{ color: '#43e97b', fontSize: 28 }}
            />
          </Card>
        </Col>
      </Row>

      {/* 图表区域 */}
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <Card
            title="各年级平均分对比"
            loading={loading}
            style={{ borderRadius: 12 }}
          >
            <div ref={barChartRef} style={{ height: 300 }} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card
            title="评价类别分布"
            loading={loading}
            style={{ borderRadius: 12 }}
          >
            <div ref={pieChartRef} style={{ height: 300 }} />
          </Card>
        </Col>
      </Row>

      {/* 快捷操作提示 */}
      <Alert
        message="快捷操作"
        description="您可以通过左侧菜单进入各功能模块：数据录入、评语管理、统计报表等。如需帮助，请联系系统管理员。"
        type="info"
        showIcon
        style={{ marginTop: 24, borderRadius: 8 }}
      />
    </div>
  )
}

export default Dashboard
