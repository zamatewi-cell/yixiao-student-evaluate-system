import React, { useState, useEffect, useCallback } from 'react'
import {
    Card, Form, Input, Button, Switch, Select, Tabs, message, Divider,
    Row, Col, Space, Typography, InputNumber, Spin, Alert
} from 'antd'
import {
    SettingOutlined, SaveOutlined, ReloadOutlined, DatabaseOutlined,
    SafetyOutlined, RobotOutlined, BankOutlined
} from '@ant-design/icons'
import axios from 'axios'

const { Title, Text } = Typography
const { Option } = Select
const { TextArea } = Input
const { TabPane } = Tabs

interface ConfigItem {
    config_key: string
    config_value: string
    description: string
    category: string
}

const SystemSettings: React.FC = () => {
    const [loading, setLoading] = useState(false)
    const [saving, setSaving] = useState(false)
    const [configs, setConfigs] = useState<{ [key: string]: ConfigItem }>({})
    const [form] = Form.useForm()

    // 获取配置
    const fetchConfigs = useCallback(async () => {
        setLoading(true)
        try {
            const token = localStorage.getItem('token')
            const response = await axios.get('/api/system-config/list', {
                headers: { Authorization: `Bearer ${token}` }
            })

            const configMap: { [key: string]: ConfigItem } = {}
            for (const item of response.data.data || []) {
                configMap[item.config_key] = item
            }
            setConfigs(configMap)

            // 设置表单初始值
            const formValues: { [key: string]: any } = {}
            for (const [key, item] of Object.entries(configMap)) {
                formValues[key] = item.config_value
            }
            form.setFieldsValue(formValues)
        } catch (error) {
            message.error('获取配置失败')
        } finally {
            setLoading(false)
        }
    }, [form])

    useEffect(() => {
        fetchConfigs()
    }, [fetchConfigs])

    // 保存配置
    const handleSave = async () => {
        setSaving(true)
        try {
            const values = await form.validateFields()
            const token = localStorage.getItem('token')

            const configItems = Object.entries(values).map(([key, value]) => ({
                key,
                value: String(value ?? ''),
                description: configs[key]?.description || ''
            }))

            await axios.put('/api/system-config/update', {
                configs: configItems
            }, {
                headers: { Authorization: `Bearer ${token}` }
            })

            message.success('配置保存成功')
            fetchConfigs()
        } catch (error) {
            message.error('保存失败')
        } finally {
            setSaving(false)
        }
    }

    // 初始化默认配置
    const handleInitDefaults = async () => {
        try {
            const token = localStorage.getItem('token')
            await axios.post('/api/system-config/init-defaults', {}, {
                headers: { Authorization: `Bearer ${token}` }
            })
            message.success('默认配置初始化完成')
            fetchConfigs()
        } catch (error) {
            message.error('初始化失败')
        }
    }

    if (loading) {
        return (
            <div style={{ padding: 24, textAlign: 'center' }}>
                <Spin size="large" tip="加载配置中..." />
            </div>
        )
    }

    return (
        <div style={{ padding: 24 }}>
            <Card
                title={
                    <Space>
                        <SettingOutlined />
                        <span>系统设置</span>
                    </Space>
                }
                extra={
                    <Space>
                        <Button icon={<ReloadOutlined />} onClick={fetchConfigs}>
                            刷新
                        </Button>
                        <Button onClick={handleInitDefaults}>
                            初始化默认
                        </Button>
                        <Button
                            type="primary"
                            icon={<SaveOutlined />}
                            onClick={handleSave}
                            loading={saving}
                        >
                            保存配置
                        </Button>
                    </Space>
                }
            >
                <Form form={form} layout="vertical">
                    <Tabs defaultActiveKey="basic">
                        <TabPane
                            tab={<><BankOutlined /> 学校信息</>}
                            key="basic"
                        >
                            <Row gutter={24}>
                                <Col span={12}>
                                    <Form.Item name="school_name" label="学校名称">
                                        <Input placeholder="输入学校名称" />
                                    </Form.Item>
                                </Col>
                                <Col span={12}>
                                    <Form.Item name="school_phone" label="学校电话">
                                        <Input placeholder="输入联系电话" />
                                    </Form.Item>
                                </Col>
                                <Col span={24}>
                                    <Form.Item name="school_address" label="学校地址">
                                        <TextArea rows={2} placeholder="输入学校地址" />
                                    </Form.Item>
                                </Col>
                            </Row>
                        </TabPane>

                        <TabPane
                            tab={<><DatabaseOutlined /> 考试设置</>}
                            key="exam"
                        >
                            <Row gutter={24}>
                                <Col span={8}>
                                    <Form.Item name="max_score" label="默认满分">
                                        <InputNumber min={1} max={200} style={{ width: '100%' }} />
                                    </Form.Item>
                                </Col>
                                <Col span={8}>
                                    <Form.Item name="score_pass_line" label="及格分数线">
                                        <InputNumber min={0} max={100} style={{ width: '100%' }} />
                                    </Form.Item>
                                </Col>
                                <Col span={8}>
                                    <Form.Item name="score_excellent_line" label="优秀分数线">
                                        <InputNumber min={0} max={100} style={{ width: '100%' }} />
                                    </Form.Item>
                                </Col>
                            </Row>
                            <Alert
                                message="分数线设置会影响成绩统计中的及格率和优秀率计算"
                                type="info"
                                showIcon
                                style={{ marginTop: 16 }}
                            />
                        </TabPane>

                        <TabPane
                            tab={<><SafetyOutlined /> 考勤设置</>}
                            key="attendance"
                        >
                            <Row gutter={24}>
                                <Col span={12}>
                                    <Form.Item name="attendance_late_minutes" label="迟到判定时间（分钟）">
                                        <InputNumber min={1} max={60} style={{ width: '100%' }} />
                                    </Form.Item>
                                </Col>
                            </Row>
                        </TabPane>

                        <TabPane
                            tab={<><RobotOutlined /> AI设置</>}
                            key="ai"
                        >
                            <Row gutter={24}>
                                <Col span={12}>
                                    <Form.Item name="ai_model" label="AI模型">
                                        <Select>
                                            <Option value="qwen-turbo">通义千问-Turbo</Option>
                                            <Option value="qwen-plus">通义千问-Plus</Option>
                                            <Option value="qwen-max">通义千问-Max</Option>
                                        </Select>
                                    </Form.Item>
                                </Col>
                                <Col span={12}>
                                    <Form.Item name="ai_api_key" label="API密钥">
                                        <Input.Password placeholder="输入API密钥" />
                                    </Form.Item>
                                </Col>
                            </Row>
                            <Alert
                                message="AI功能用于自动生成学生评语和试卷分析，需要有效的API密钥"
                                type="info"
                                showIcon
                            />
                        </TabPane>

                        <TabPane
                            tab={<><SettingOutlined /> 系统设置</>}
                            key="system"
                        >
                            <Row gutter={24}>
                                <Col span={8}>
                                    <Form.Item name="session_timeout_hours" label="会话超时（小时）">
                                        <InputNumber min={1} max={168} style={{ width: '100%' }} />
                                    </Form.Item>
                                </Col>
                                <Col span={8}>
                                    <Form.Item name="backup_keep_days" label="备份保留天数">
                                        <InputNumber min={7} max={365} style={{ width: '100%' }} />
                                    </Form.Item>
                                </Col>
                                <Col span={8}>
                                    <Form.Item
                                        name="backup_auto_enabled"
                                        label="自动备份"
                                        valuePropName="checked"
                                    >
                                        <Switch checkedChildren="开启" unCheckedChildren="关闭" />
                                    </Form.Item>
                                </Col>
                            </Row>
                        </TabPane>
                    </Tabs>
                </Form>
            </Card>
        </div>
    )
}

export default SystemSettings
