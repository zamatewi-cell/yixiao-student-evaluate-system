import { useEffect, useState } from 'react'
import { Table, Button, Space, Modal, Form, Input, Select, message, Card, Popconfirm, DatePicker } from 'antd'
import { PlusOutlined, SearchOutlined, BarcodeOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons'
import { adminApi } from '../../services/api'
import dayjs from 'dayjs'

const Students = () => {
  const [students, setStudents] = useState([])
  const [classes, setClasses] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingStudent, setEditingStudent] = useState<any>(null) // 当前正在编辑的学生
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

  // 打开添加模态框
  const handleOpenAdd = () => {
    setEditingStudent(null)
    form.resetFields()
    form.setFieldsValue({ gender: 'male' })
    setModalOpen(true)
  }

  // 打开编辑模态框
  const handleOpenEdit = (record: any) => {
    setEditingStudent(record)
    form.setFieldsValue({
      student_no: record.student_no,
      name: record.name,
      gender: record.gender,
      class_id: record.class_id,
      birth_date: record.birth_date ? dayjs(record.birth_date) : undefined,
      parent_name: record.parent_name,
      parent_phone: record.parent_phone,
    })
    setModalOpen(true)
  }

  // 提交表单（新增或编辑）
  const handleSubmit = async (values: any) => {
    try {
      // 处理日期格式
      const submitData = {
        ...values,
        birth_date: values.birth_date ? values.birth_date.format('YYYY-MM-DD') : null,
      }

      if (editingStudent) {
        // 编辑模式
        await adminApi.updateStudent(editingStudent.id, submitData)
        message.success('学生信息更新成功')
      } else {
        // 新增模式
        await adminApi.createStudent(submitData)
        message.success('学生添加成功')
      }
      setModalOpen(false)
      form.resetFields()
      setEditingStudent(null)
      loadStudents(pagination.current)
    } catch (error: any) {
      message.error(error.response?.data?.detail || (editingStudent ? '更新失败' : '添加失败'))
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await adminApi.deleteStudent(id)
      message.success('学生删除成功')
      loadStudents()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败')
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
    {
      title: '性别', dataIndex: 'gender', key: 'gender', width: 60,
      render: (v: string) => v === 'male' ? '男' : '女'
    },
    { title: '班级', dataIndex: 'class_name', key: 'class_name', width: 150 },
    { title: '年级', dataIndex: 'grade_name', key: 'grade_name', width: 100 },
    { title: '家长电话', dataIndex: 'parent_phone', key: 'parent_phone', width: 120 },
    {
      title: '操作',
      key: 'action',
      width: 230,
      render: (_: any, record: any) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleOpenEdit(record)}>
            编辑
          </Button>
          <Button type="link" icon={<BarcodeOutlined />} onClick={() => showBarcode(record)}>
            条码
          </Button>
          <Popconfirm
            title="确定要删除这个学生吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Card
        title="学生管理"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleOpenAdd}>
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
        title={editingStudent ? '编辑学生' : '添加学生'}
        open={modalOpen}
        onCancel={() => {
          setModalOpen(false)
          setEditingStudent(null)
          form.resetFields()
        }}
        onOk={() => form.submit()}
      >
        <Form form={form} onFinish={handleSubmit} layout="vertical">
          <Form.Item name="student_no" label="学号" rules={[{ required: true, message: '请输入学号' }]}>
            <Input disabled={!!editingStudent} placeholder="请输入学号" />
          </Form.Item>
          <Form.Item name="name" label="姓名" rules={[{ required: true, message: '请输入姓名' }]}>
            <Input placeholder="请输入姓名" />
          </Form.Item>
          <Form.Item name="gender" label="性别">
            <Select options={[
              { value: 'male', label: '男' },
              { value: 'female', label: '女' },
            ]} />
          </Form.Item>
          <Form.Item name="class_id" label="班级">
            <Select
              allowClear
              placeholder="请选择班级"
              options={classes.map((c: any) => ({
                value: c.id,
                label: `${c.grade_name} ${c.name}`,
              }))}
            />
          </Form.Item>
          <Form.Item name="birth_date" label="出生日期">
            <DatePicker placeholder="选择出生日期" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="parent_name" label="家长姓名">
            <Input placeholder="请输入家长姓名" />
          </Form.Item>
          <Form.Item name="parent_phone" label="家长电话">
            <Input placeholder="请输入家长电话" />
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
