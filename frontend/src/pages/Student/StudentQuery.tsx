import React, { useState } from 'react';
import { Card, Form, Input, Button, message, Tabs, Table, Tag, Descriptions, Empty } from 'antd';
import { UserOutlined, IdcardOutlined, RadarChartOutlined, FileTextOutlined, EditOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import api from '../../services/api';

interface StudentInfo {
  id: number;
  student_no: string;
  name: string;
  gender: string;
  class_name: string;
  grade_name: string;
}

interface EvaluationData {
  category: string;
  indicator: string;
  value: string | number;
  recorded_at: string;
}

interface RadarData {
  categories: string[];
  values: number[];
  max_values: number[];
}

interface CommentData {
  semester_name: string;
  ai_comment: string;
  teacher_comment: string;
  created_at: string;
}

interface CalligraphyRecord {
  id: number;
  filename: string;
  overall_score: number;
  ai_comment: string;
  graded_at: string;
}

const StudentQuery: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [studentInfo, setStudentInfo] = useState<StudentInfo | null>(null);
  const [evaluations, setEvaluations] = useState<EvaluationData[]>([]);
  const [radarData, setRadarData] = useState<RadarData | null>(null);
  const [comments, setComments] = useState<CommentData[]>([]);
  const [calligraphyRecords, setCalligraphyRecords] = useState<CalligraphyRecord[]>([]);
  const [activeTab, setActiveTab] = useState('evaluation');

  const onFinish = async (values: { student_no: string; name: string }) => {
    setLoading(true);
    try {
      // Query student info
      const res = await api.post('/api/student/query', values);
      if (res.data.success) {
        setStudentInfo(res.data.student);
        setEvaluations(res.data.evaluations || []);
        setRadarData(res.data.radar_data || null);
        setComments(res.data.comments || []);
        setCalligraphyRecords(res.data.calligraphy_records || []);
        message.success('查询成功');
      } else {
        message.error(res.data.message || '查询失败');
        resetData();
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '查询失败，请检查学号和姓名');
      resetData();
    } finally {
      setLoading(false);
    }
  };

  const resetData = () => {
    setStudentInfo(null);
    setEvaluations([]);
    setRadarData(null);
    setComments([]);
    setCalligraphyRecords([]);
  };

  const getRadarOption = () => {
    if (!radarData) return {};
    
    const indicators = radarData.categories.map((cat, idx) => ({
      name: cat,
      max: radarData.max_values[idx] || 100
    }));

    return {
      title: {
        text: '综合素质评价雷达图',
        left: 'center'
      },
      tooltip: {
        trigger: 'item'
      },
      radar: {
        indicator: indicators,
        shape: 'polygon',
        splitNumber: 5,
        axisName: {
          color: '#333'
        },
        splitLine: {
          lineStyle: {
            color: ['#e5e5e5']
          }
        },
        splitArea: {
          show: true,
          areaStyle: {
            color: ['rgba(24, 144, 255, 0.1)', 'rgba(24, 144, 255, 0.2)']
          }
        }
      },
      series: [{
        type: 'radar',
        data: [{
          value: radarData.values,
          name: studentInfo?.name || '评价数据',
          areaStyle: {
            color: 'rgba(24, 144, 255, 0.4)'
          },
          lineStyle: {
            color: '#1890ff',
            width: 2
          },
          itemStyle: {
            color: '#1890ff'
          }
        }]
      }]
    };
  };

  const evaluationColumns = [
    {
      title: '评价类别',
      dataIndex: 'category',
      key: 'category',
      render: (text: string) => <Tag color="blue">{text}</Tag>
    },
    {
      title: '评价指标',
      dataIndex: 'indicator',
      key: 'indicator'
    },
    {
      title: '评价结果',
      dataIndex: 'value',
      key: 'value',
      render: (value: string | number) => {
        if (typeof value === 'number') {
          const color = value >= 90 ? 'green' : value >= 60 ? 'orange' : 'red';
          return <Tag color={color}>{value}分</Tag>;
        }
        return <Tag>{value}</Tag>;
      }
    },
    {
      title: '记录时间',
      dataIndex: 'recorded_at',
      key: 'recorded_at'
    }
  ];

  const calligraphyColumns = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename'
    },
    {
      title: '评分',
      dataIndex: 'overall_score',
      key: 'overall_score',
      render: (score: number) => {
        const color = score >= 90 ? 'green' : score >= 70 ? 'blue' : score >= 60 ? 'orange' : 'red';
        return <Tag color={color}>{score}分</Tag>;
      }
    },
    {
      title: 'AI评语',
      dataIndex: 'ai_comment',
      key: 'ai_comment',
      ellipsis: true
    },
    {
      title: '批改时间',
      dataIndex: 'graded_at',
      key: 'graded_at'
    }
  ];

  const tabItems = [
    {
      key: 'evaluation',
      label: (
        <span>
          <IdcardOutlined />
          评价数据
        </span>
      ),
      children: (
        <Table
          columns={evaluationColumns}
          dataSource={evaluations}
          rowKey={(record, index) => `${record.category}-${record.indicator}-${index}`}
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: <Empty description="暂无评价数据" /> }}
        />
      )
    },
    {
      key: 'radar',
      label: (
        <span>
          <RadarChartOutlined />
          雷达图
        </span>
      ),
      children: radarData ? (
        <ReactECharts option={getRadarOption()} style={{ height: 400 }} />
      ) : (
        <Empty description="暂无雷达图数据" />
      )
    },
    {
      key: 'calligraphy',
      label: (
        <span>
          <EditOutlined />
          书法成绩
        </span>
      ),
      children: (
        <Table
          columns={calligraphyColumns}
          dataSource={calligraphyRecords}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: <Empty description="暂无书法批改记录" /> }}
        />
      )
    },
    {
      key: 'comments',
      label: (
        <span>
          <FileTextOutlined />
          期末评语
        </span>
      ),
      children: comments.length > 0 ? (
        <div>
          {comments.map((comment, index) => (
            <Card key={index} title={comment.semester_name} style={{ marginBottom: 16 }}>
              {comment.ai_comment && (
                <div style={{ marginBottom: 16 }}>
                  <h4>AI评语</h4>
                  <p style={{ whiteSpace: 'pre-wrap', background: '#f5f5f5', padding: 16, borderRadius: 4 }}>
                    {comment.ai_comment}
                  </p>
                </div>
              )}
              {comment.teacher_comment && (
                <div>
                  <h4>教师评语</h4>
                  <p style={{ whiteSpace: 'pre-wrap', background: '#e6f7ff', padding: 16, borderRadius: 4 }}>
                    {comment.teacher_comment}
                  </p>
                </div>
              )}
              <p style={{ color: '#999', marginTop: 8, marginBottom: 0 }}>生成时间: {comment.created_at}</p>
            </Card>
          ))}
        </div>
      ) : (
        <Empty description="暂无期末评语" />
      )
    }
  ];

  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '40px 20px'
    }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <Card style={{ marginBottom: 24 }}>
          <h1 style={{ textAlign: 'center', marginBottom: 24 }}>
            <UserOutlined style={{ marginRight: 8 }} />
            学生综合素质评价查询
          </h1>
          
          <Form
            layout="inline"
            onFinish={onFinish}
            style={{ justifyContent: 'center', marginBottom: 24 }}
          >
            <Form.Item
              name="student_no"
              rules={[{ required: true, message: '请输入学号' }]}
            >
              <Input
                prefix={<IdcardOutlined />}
                placeholder="请输入学号"
                style={{ width: 200 }}
              />
            </Form.Item>
            <Form.Item
              name="name"
              rules={[{ required: true, message: '请输入姓名' }]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="请输入姓名"
                style={{ width: 150 }}
              />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading}>
                查询
              </Button>
            </Form.Item>
          </Form>
        </Card>

        {studentInfo && (
          <>
            <Card style={{ marginBottom: 24 }}>
              <Descriptions title="学生信息" bordered>
                <Descriptions.Item label="学号">{studentInfo.student_no}</Descriptions.Item>
                <Descriptions.Item label="姓名">{studentInfo.name}</Descriptions.Item>
                <Descriptions.Item label="性别">{studentInfo.gender === 'M' ? '男' : '女'}</Descriptions.Item>
                <Descriptions.Item label="年级">{studentInfo.grade_name}</Descriptions.Item>
                <Descriptions.Item label="班级">{studentInfo.class_name}</Descriptions.Item>
              </Descriptions>
            </Card>

            <Card>
              <Tabs
                activeKey={activeTab}
                onChange={setActiveTab}
                items={tabItems}
              />
            </Card>
          </>
        )}
      </div>
    </div>
  );
};

export default StudentQuery;
