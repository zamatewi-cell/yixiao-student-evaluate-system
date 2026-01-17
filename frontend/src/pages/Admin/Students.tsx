import { useEffect, useState } from 'react'
import { Table, Button, Space, Modal, Form, Input, Select, message, Card } from 'antd'
import { PlusOutlined, SearchOutlined, BarcodeOutlined } from '@ant-design/icons'
import { adminApi } from '../../services/api'

const Students = () => {
  const [students, setStudents] = useState([])
  const [classes, setClasses] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [barcodeModal, setBarcodeModal] = useState<any>(null)
  const [search, setSearch] = useState('')
  const [classId, setClassId] = useState<number>()
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 })
  const [form] = Form.useForm()

  useEffect(() => {
    loadClasses()
    loadStudents()
  }, [])

  const loadClasses = async () => {
    try {
      const res = await adminApi.getClasses()
      setClasses(res.data.data)
    } catch (error) {
      console.error(error)
    }
  }

  const loadStudents = async (page = 1) => {
    setLoading(true)
    try {
      const res = await adminApi.getStudents({
        page,
        page_size: pagination.pageSize,
        search,
        class_id: classId,
      })
      setStudents(res.data.data)
      setPagination({ ...pagination, current: page, total: res.data.total })
    } catch (error) {
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (values: any) => {
    try {
      await adminApi.createStudent(values)
      message.success('学生添加成功')
      setModalOpen(false)
      form.resetFields()
      loadStudents()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '添加失败')
    }
  }

  const showBarcode = async (record: any) => {
    try {
      const res = await adminApi.getStudentBarcode(record.id)
      setBarcodeModal(res.data)
    } catch (error) {
      message.error('获取条码失败')
    }
  }

  const columns = [
    { title: '学号', dataIndex: 'student_no', key: 'student_no', width: 120 },
    { title: '姓名', dataIndex: 'name', key: 'name', width: 100 },
    { title: '性别', dataIndex: 'gender', key: 'gender', width: 60,
      render: (v: string) => v === 'male' ? '男' : '女' },
    { title: '班级', dataIndex: 'class_name', key: 'class_name', width: 150 },
    { title: '年级', dataIndex: 'grade_name', key: 'grade_name', width: 100 },
    { title: '家长电话', dataIndex: 'parent_phone', key: 'parent_phone', width: 120 },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: any) => (
        <Button type="link" icon={<BarcodeOutlined />} onClick={() => showBarcode(record)}>
          条码
        </Button>
      ),
    },
  ]

  return (
    <div>
      <Card
        title="学生管理"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
            添加学生
          </Button>
        }
      >
        <Space style={{ marginBottom: 16 }}>
          <Input
            placeholder="搜索学号/姓名"
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onPressEnter={() => loadStudents(1)}
            style={{ width: 200 }}
          />
          <Select
            placeholder="选择班级"
            allowClear
            style={{ width: 150 }}
            value={classId}
            onChange={setClassId}
            options={classes.map((c: any) => ({
              value: c.id,
              label: `${c.grade_name} ${c.name}`,
            }))}
          />
          <Button type="primary" onClick={() => loadStudents(1)}>查询</Button>
        </Space>

        <Table
          columns={columns}
          dataSource={students}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            onChange: (page) => loadStudents(page),
          }}
        />
      </Card>

      <Modal
        title="添加学生"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
      >
        <Form form={form} onFinish={handleCreate} layout="vertical">
          <Form.Item name="student_no" label="学号" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="name" label="姓名" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="gender" label="性别" initialValue="male">
            <Select options={[
              { value: 'male', label: '男' },
              { value: 'female', label: '女' },
            ]} />
          </Form.Item>
          <Form.Item name="class_id" label="班级">
            <Select
              allowClear
              options={classes.map((c: any) => ({
                value: c.id,
                label: `${c.grade_name} ${c.name}`,
              }))}
            />
          </Form.Item>
          <Form.Item name="parent_phone" label="家长电话">
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="学生条码"
        open={!!barcodeModal}
        onCancel={() => setBarcodeModal(null)}
        footer={null}
      >
        {barcodeModal && (
          <div style={{ textAlign: 'center' }}>
            <p><strong>{barcodeModal.name}</strong> ({barcodeModal.student_no})</p>
            <img src={barcodeModal.barcode_image} alt="barcode" style={{ maxWidth: '100%' }} />
          </div>
        )}
      </Modal>
    </div>
  )
}

export default Students
