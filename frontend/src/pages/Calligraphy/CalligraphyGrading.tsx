/**
 * 书法批改页面组件
 * 
 * 功能说明：
 * - 支持上传书法图片进行AI智能批改
 * - 实时展示批改结果（评分、等级、评语）
 * - 查看历史批改记录
 * - 详细分析（优点和改进建议）
 */
import { useState, useCallback, useEffect } from 'react'
import {
    Card,
    Upload,
    Button,
    Progress,
    Typography,
    Space,
    Row,
    Col,
    Table,
    Tag,
    Modal,
    Image,
    Statistic,
    Divider,
    message,
    Spin,
    Empty,
    Tooltip,
    Switch,
    Badge,
} from 'antd'
import {
    InboxOutlined,
    FileImageOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    LoadingOutlined,
    StarOutlined,
    TrophyOutlined,
    EyeOutlined,
    DeleteOutlined,
    ReloadOutlined,
    BulbOutlined,
    RocketOutlined,
    HistoryOutlined,
    ExperimentOutlined,
} from '@ant-design/icons'
import type { UploadProps } from 'antd'
import type { ColumnsType } from 'antd/es/table'

const { Title, Text, Paragraph } = Typography
const { Dragger } = Upload

// 接口定义
interface GradingResult {
    id: number
    filename: string
    original_filename: string
    upload_time: string
    overall_score: number | null
    grade: string | null
    char_count: number
    ai_comment: string | null
    strengths: string | null
    suggestions: string | null
    status: 'pending' | 'processing' | 'completed' | 'failed'
    file_url: string
    barcode?: string | null
    student_id?: number | null
    error?: string | null
}

interface StatsData {
    total_records: number
    average_score: number
    grade_distribution: Record<string, number>
    total_characters: number
}

/**
 * 书法批改主页面组件
 */
const CalligraphyGrading = () => {
    // 状态管理
    const [uploading, setUploading] = useState(false)
    const [currentResult, setCurrentResult] = useState<GradingResult | null>(null)
    const [records, setRecords] = useState<GradingResult[]>([])
    const [loading, setLoading] = useState(false)
    const [detailModalVisible, setDetailModalVisible] = useState(false)
    const [selectedRecord, setSelectedRecord] = useState<GradingResult | null>(null)
    const [stats, setStats] = useState<StatsData | null>(null)
    const [useAI, setUseAI] = useState(true)
    const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })

    // API基础URL
    const API_BASE = 'http://localhost:8000'

    /**
     * 获取批改统计数据
     */
    const fetchStats = useCallback(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/stats`)
            if (response.ok) {
                const data = await response.json()
                setStats(data)
            }
        } catch (error) {
            console.error('获取统计数据失败:', error)
        }
    }, [API_BASE])

    /**
     * 获取历史批改记录
     */
    const fetchRecords = useCallback(async (page = 1, pageSize = 10) => {
        setLoading(true)
        try {
            const response = await fetch(`${API_BASE}/api/records?page=${page}&page_size=${pageSize}`)
            if (response.ok) {
                const data = await response.json()
                setRecords(data.results)
                setPagination({
                    current: data.page,
                    pageSize: data.page_size,
                    total: data.total
                })
            }
        } catch (error) {
            console.error('获取记录失败:', error)
            message.error('获取历史记录失败')
        } finally {
            setLoading(false)
        }
    }, [API_BASE])

    // 初始化加载
    useEffect(() => {
        fetchStats()
        fetchRecords()
    }, [fetchStats, fetchRecords])

    /**
     * 处理图片上传
     */
    const handleUpload = async (file: File) => {
        setUploading(true)
        setCurrentResult(null)

        const formData = new FormData()
        formData.append('file', file)

        try {
            const response = await fetch(`${API_BASE}/api/upload?use_ai=${useAI}`, {
                method: 'POST',
                body: formData,
            })

            if (!response.ok) {
                throw new Error('上传失败')
            }

            const result = await response.json()
            setCurrentResult(result)

            if (result.status === 'completed') {
                message.success('批改完成！')
            } else if (result.status === 'failed') {
                message.error(`批改失败: ${result.error || '未知错误'}`)
            }

            // 刷新记录和统计
            fetchRecords()
            fetchStats()
        } catch (error) {
            console.error('上传错误:', error)
            message.error('上传失败，请检查网络连接')
        } finally {
            setUploading(false)
        }
    }

    /**
     * 上传组件配置
     */
    const uploadProps: UploadProps = {
        name: 'file',
        multiple: false,
        accept: 'image/jpeg,image/png,image/bmp',
        showUploadList: false,
        beforeUpload: (file) => {
            // 验证文件类型
            const isImage = ['image/jpeg', 'image/png', 'image/bmp'].includes(file.type)
            if (!isImage) {
                message.error('只支持 JPG、PNG、BMP 格式的图片！')
                return false
            }
            // 验证文件大小（10MB）
            const isLt10M = file.size / 1024 / 1024 < 10
            if (!isLt10M) {
                message.error('图片大小不能超过 10MB！')
                return false
            }
            handleUpload(file)
            return false
        },
    }

    /**
     * 删除记录
     */
    const handleDelete = async (id: number) => {
        try {
            const response = await fetch(`${API_BASE}/api/records/${id}`, {
                method: 'DELETE',
            })
            if (response.ok) {
                message.success('删除成功')
                fetchRecords(pagination.current, pagination.pageSize)
                fetchStats()
            } else {
                message.error('删除失败')
            }
        } catch (error) {
            message.error('删除失败')
        }
    }

    /**
     * 根据分数获取等级颜色
     */
    const getGradeColor = (grade: string | null) => {
        const colors: Record<string, string> = {
            'Excellent': '#52c41a',
            'Good': '#1890ff',
            'Medium': '#faad14',
            'Pass': '#fa8c16',
            'NeedImprove': '#ff4d4f',
        }
        return colors[grade || ''] || '#999'
    }

    /**
     * 根据分数获取等级中文名
     */
    const getGradeText = (grade: string | null) => {
        const texts: Record<string, string> = {
            'Excellent': '优秀',
            'Good': '良好',
            'Medium': '中等',
            'Pass': '及格',
            'NeedImprove': '待提高',
        }
        return texts[grade || ''] || '未评定'
    }

    /**
     * 状态标签组件
     */
    const StatusTag = ({ status }: { status: string }) => {
        const config: Record<string, { color: string; icon: React.ReactNode; text: string }> = {
            pending: { color: 'default', icon: <LoadingOutlined />, text: '等待中' },
            processing: { color: 'processing', icon: <LoadingOutlined spin />, text: '处理中' },
            completed: { color: 'success', icon: <CheckCircleOutlined />, text: '已完成' },
            failed: { color: 'error', icon: <CloseCircleOutlined />, text: '失败' },
        }
        const { color, icon, text } = config[status] || config.pending
        return <Tag color={color} icon={icon}>{text}</Tag>
    }

    /**
     * 历史记录表格列配置
     */
    const columns: ColumnsType<GradingResult> = [
        {
            title: '预览',
            dataIndex: 'file_url',
            key: 'preview',
            width: 80,
            render: (url) => (
                <Image
                    src={`${API_BASE}${url}`}
                    width={50}
                    height={50}
                    style={{ objectFit: 'cover', borderRadius: 4 }}
                    preview={{
                        mask: <EyeOutlined />
                    }}
                />
            ),
        },
        {
            title: '文件名',
            dataIndex: 'original_filename',
            key: 'filename',
            ellipsis: true,
            render: (name) => (
                <Tooltip title={name}>
                    <Text ellipsis style={{ maxWidth: 150 }}>{name}</Text>
                </Tooltip>
            ),
        },
        {
            title: '评分',
            dataIndex: 'overall_score',
            key: 'score',
            width: 100,
            render: (score) => (
                score !== null ? (
                    <Text strong style={{
                        color: score >= 80 ? '#52c41a' : score >= 60 ? '#faad14' : '#ff4d4f',
                        fontSize: 16
                    }}>
                        {score.toFixed(1)}
                    </Text>
                ) : <Text type="secondary">-</Text>
            ),
        },
        {
            title: '等级',
            dataIndex: 'grade',
            key: 'grade',
            width: 80,
            render: (grade) => (
                <Tag color={getGradeColor(grade)}>{getGradeText(grade)}</Tag>
            ),
        },
        {
            title: '字数',
            dataIndex: 'char_count',
            key: 'char_count',
            width: 70,
        },
        {
            title: '状态',
            dataIndex: 'status',
            key: 'status',
            width: 100,
            render: (status) => <StatusTag status={status} />,
        },
        {
            title: '上传时间',
            dataIndex: 'upload_time',
            key: 'upload_time',
            width: 160,
        },
        {
            title: '操作',
            key: 'action',
            width: 100,
            render: (_, record) => (
                <Space>
                    <Tooltip title="查看详情">
                        <Button
                            type="link"
                            icon={<EyeOutlined />}
                            onClick={() => {
                                setSelectedRecord(record)
                                setDetailModalVisible(true)
                            }}
                        />
                    </Tooltip>
                    <Tooltip title="删除">
                        <Button
                            type="link"
                            danger
                            icon={<DeleteOutlined />}
                            onClick={() => {
                                Modal.confirm({
                                    title: '确认删除',
                                    content: '确定要删除这条记录吗？此操作不可恢复。',
                                    onOk: () => handleDelete(record.id),
                                })
                            }}
                        />
                    </Tooltip>
                </Space>
            ),
        },
    ]

    return (
        <div style={{ padding: 24, minHeight: '100%' }}>
            {/* 页面标题 */}
            <div style={{ marginBottom: 24 }}>
                <Title level={3} style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <ExperimentOutlined style={{ color: '#667eea' }} />
                    AI 书法批改
                </Title>
                <Text type="secondary">上传书法作品，AI智能分析并提供专业评价和改进建议</Text>
            </div>

            <Row gutter={24}>
                {/* 左侧 - 上传区域和结果展示 */}
                <Col xs={24} lg={14}>
                    {/* 上传卡片 */}
                    <Card
                        style={{
                            marginBottom: 24,
                            borderRadius: 12,
                            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                        }}
                        extra={
                            <Space>
                                <Text type="secondary">AI智能分析</Text>
                                <Switch
                                    checked={useAI}
                                    onChange={setUseAI}
                                    checkedChildren="开启"
                                    unCheckedChildren="关闭"
                                />
                            </Space>
                        }
                    >
                        <Dragger
                            {...uploadProps}
                            disabled={uploading}
                            style={{
                                padding: 40,
                                background: 'linear-gradient(135deg, #f5f7fa 0%, #f0f2f5 100%)',
                                borderRadius: 12,
                                border: '2px dashed #d9d9d9',
                                transition: 'all 0.3s',
                            }}
                        >
                            {uploading ? (
                                <Space direction="vertical" size="large">
                                    <Spin size="large" />
                                    <Text>正在上传并分析中...</Text>
                                    <Progress percent={30} status="active" style={{ width: 200 }} />
                                </Space>
                            ) : (
                                <>
                                    <p className="ant-upload-drag-icon">
                                        <InboxOutlined style={{ color: '#667eea', fontSize: 64 }} />
                                    </p>
                                    <p className="ant-upload-text" style={{ fontSize: 18, color: '#333' }}>
                                        点击或拖拽图片到此处上传
                                    </p>
                                    <p className="ant-upload-hint" style={{ color: '#888' }}>
                                        支持 JPG、PNG、BMP 格式，单个文件不超过 10MB
                                    </p>
                                    <Space style={{ marginTop: 16 }}>
                                        <Tag icon={<FileImageOutlined />} color="blue">JPG</Tag>
                                        <Tag icon={<FileImageOutlined />} color="green">PNG</Tag>
                                        <Tag icon={<FileImageOutlined />} color="orange">BMP</Tag>
                                    </Space>
                                </>
                            )}
                        </Dragger>
                    </Card>

                    {/* 批改结果展示 */}
                    {currentResult && (
                        <Card
                            title={
                                <Space>
                                    <TrophyOutlined style={{ color: '#faad14' }} />
                                    <span>批改结果</span>
                                    <StatusTag status={currentResult.status} />
                                </Space>
                            }
                            style={{
                                borderRadius: 12,
                                boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                            }}
                        >
                            {currentResult.status === 'completed' ? (
                                <Row gutter={24}>
                                    {/* 左侧图片展示 */}
                                    <Col span={10}>
                                        <Image
                                            src={`${API_BASE}${currentResult.file_url}`}
                                            style={{
                                                width: '100%',
                                                borderRadius: 8,
                                                border: '1px solid #f0f0f0',
                                            }}
                                            alt="书法作品"
                                        />
                                        <div style={{ textAlign: 'center', marginTop: 8 }}>
                                            <Text type="secondary">{currentResult.original_filename}</Text>
                                        </div>
                                    </Col>

                                    {/* 右侧评价信息 */}
                                    <Col span={14}>
                                        {/* 评分和等级 */}
                                        <Row gutter={16} style={{ marginBottom: 24 }}>
                                            <Col span={12}>
                                                <Card
                                                    size="small"
                                                    style={{
                                                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                                        borderRadius: 8,
                                                        textAlign: 'center',
                                                    }}
                                                    bodyStyle={{ padding: 16 }}
                                                >
                                                    <Statistic
                                                        title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>综合评分</Text>}
                                                        value={currentResult.overall_score || 0}
                                                        precision={1}
                                                        suffix="分"
                                                        valueStyle={{ color: '#fff', fontSize: 32 }}
                                                    />
                                                </Card>
                                            </Col>
                                            <Col span={12}>
                                                <Card
                                                    size="small"
                                                    style={{
                                                        background: getGradeColor(currentResult.grade),
                                                        borderRadius: 8,
                                                        textAlign: 'center',
                                                    }}
                                                    bodyStyle={{ padding: 16 }}
                                                >
                                                    <Statistic
                                                        title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>等级评定</Text>}
                                                        value={getGradeText(currentResult.grade)}
                                                        valueStyle={{ color: '#fff', fontSize: 28 }}
                                                    />
                                                </Card>
                                            </Col>
                                        </Row>

                                        {/* 识别字数 */}
                                        <div style={{ marginBottom: 16 }}>
                                            <Badge count={currentResult.char_count} overflowCount={999} style={{ backgroundColor: '#52c41a' }}>
                                                <Tag icon={<StarOutlined />} color="default" style={{ padding: '4px 12px' }}>
                                                    识别字符数
                                                </Tag>
                                            </Badge>
                                        </div>

                                        {/* AI 评语 */}
                                        {currentResult.ai_comment && (
                                            <>
                                                <Divider orientation="left">
                                                    <Space><BulbOutlined style={{ color: '#faad14' }} />AI 评语</Space>
                                                </Divider>
                                                <Paragraph
                                                    style={{
                                                        background: '#fafafa',
                                                        padding: 12,
                                                        borderRadius: 8,
                                                        borderLeft: '3px solid #667eea',
                                                    }}
                                                >
                                                    {currentResult.ai_comment}
                                                </Paragraph>
                                            </>
                                        )}

                                        {/* 优点 */}
                                        {currentResult.strengths && (
                                            <>
                                                <Divider orientation="left">
                                                    <Space><CheckCircleOutlined style={{ color: '#52c41a' }} />优点</Space>
                                                </Divider>
                                                <Paragraph
                                                    style={{
                                                        background: '#f6ffed',
                                                        padding: 12,
                                                        borderRadius: 8,
                                                        borderLeft: '3px solid #52c41a',
                                                    }}
                                                >
                                                    {currentResult.strengths}
                                                </Paragraph>
                                            </>
                                        )}

                                        {/* 改进建议 */}
                                        {currentResult.suggestions && (
                                            <>
                                                <Divider orientation="left">
                                                    <Space><RocketOutlined style={{ color: '#1890ff' }} />改进建议</Space>
                                                </Divider>
                                                <Paragraph
                                                    style={{
                                                        background: '#e6f7ff',
                                                        padding: 12,
                                                        borderRadius: 8,
                                                        borderLeft: '3px solid #1890ff',
                                                    }}
                                                >
                                                    {currentResult.suggestions}
                                                </Paragraph>
                                            </>
                                        )}
                                    </Col>
                                </Row>
                            ) : currentResult.status === 'failed' ? (
                                <Empty
                                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                                    description={
                                        <Text type="danger">批改失败: {currentResult.error || '未知错误'}</Text>
                                    }
                                />
                            ) : (
                                <div style={{ textAlign: 'center', padding: 40 }}>
                                    <Spin size="large" />
                                    <div style={{ marginTop: 16 }}>
                                        <Text type="secondary">正在分析中，请稍候...</Text>
                                    </div>
                                </div>
                            )}
                        </Card>
                    )}
                </Col>

                {/* 右侧 - 统计和历史记录 */}
                <Col xs={24} lg={10}>
                    {/* 统计卡片 */}
                    <Card
                        style={{
                            marginBottom: 24,
                            borderRadius: 12,
                            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        }}
                        bodyStyle={{ padding: 20 }}
                    >
                        <Row gutter={16}>
                            <Col span={12}>
                                <Statistic
                                    title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>累计批改</Text>}
                                    value={stats?.total_records || 0}
                                    suffix="份"
                                    valueStyle={{ color: '#fff' }}
                                />
                            </Col>
                            <Col span={12}>
                                <Statistic
                                    title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>平均分数</Text>}
                                    value={stats?.average_score || 0}
                                    precision={1}
                                    suffix="分"
                                    valueStyle={{ color: '#fff' }}
                                />
                            </Col>
                        </Row>
                        <Divider style={{ borderColor: 'rgba(255,255,255,0.2)', margin: '16px 0' }} />
                        <Row gutter={16}>
                            <Col span={12}>
                                <Statistic
                                    title={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>识别字符</Text>}
                                    value={stats?.total_characters || 0}
                                    suffix="个"
                                    valueStyle={{ color: '#fff', fontSize: 20 }}
                                />
                            </Col>
                            <Col span={12}>
                                <div>
                                    <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: 12 }}>等级分布</Text>
                                    <div style={{ marginTop: 4 }}>
                                        {stats?.grade_distribution && Object.entries(stats.grade_distribution).map(([grade, count]) => (
                                            <Tag
                                                key={grade}
                                                color={getGradeColor(grade)}
                                                style={{ marginBottom: 4 }}
                                            >
                                                {getGradeText(grade)}: {count}
                                            </Tag>
                                        ))}
                                    </div>
                                </div>
                            </Col>
                        </Row>
                    </Card>

                    {/* 历史记录 */}
                    <Card
                        title={
                            <Space>
                                <HistoryOutlined style={{ color: '#667eea' }} />
                                <span>历史记录</span>
                            </Space>
                        }
                        extra={
                            <Button
                                type="text"
                                icon={<ReloadOutlined />}
                                onClick={() => fetchRecords(pagination.current, pagination.pageSize)}
                                loading={loading}
                            >
                                刷新
                            </Button>
                        }
                        style={{
                            borderRadius: 12,
                            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                        }}
                        bodyStyle={{ padding: 0 }}
                    >
                        <Table
                            columns={columns}
                            dataSource={records}
                            rowKey="id"
                            loading={loading}
                            pagination={{
                                ...pagination,
                                size: 'small',
                                showSizeChanger: true,
                                showTotal: (total) => `共 ${total} 条`,
                                onChange: (page, pageSize) => fetchRecords(page, pageSize),
                            }}
                            size="small"
                            scroll={{ x: 800 }}
                        />
                    </Card>
                </Col>
            </Row>

            {/* 详情弹窗 */}
            <Modal
                title={
                    <Space>
                        <EyeOutlined />
                        <span>批改详情</span>
                    </Space>
                }
                open={detailModalVisible}
                onCancel={() => setDetailModalVisible(false)}
                footer={null}
                width={800}
            >
                {selectedRecord && (
                    <Row gutter={24}>
                        <Col span={12}>
                            <Image
                                src={`${API_BASE}${selectedRecord.file_url}`}
                                style={{ width: '100%', borderRadius: 8 }}
                            />
                            <div style={{ textAlign: 'center', marginTop: 8 }}>
                                <Text type="secondary">{selectedRecord.original_filename}</Text>
                            </div>
                        </Col>
                        <Col span={12}>
                            <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                <Card size="small" style={{ background: '#fafafa' }}>
                                    <Row gutter={16}>
                                        <Col span={12}>
                                            <Statistic title="综合评分" value={selectedRecord.overall_score || '-'} precision={1} />
                                        </Col>
                                        <Col span={12}>
                                            <Statistic
                                                title="等级"
                                                value={getGradeText(selectedRecord.grade)}
                                                valueStyle={{ color: getGradeColor(selectedRecord.grade) }}
                                            />
                                        </Col>
                                    </Row>
                                </Card>

                                <div>
                                    <Text strong>上传时间：</Text>
                                    <Text>{selectedRecord.upload_time}</Text>
                                </div>

                                <div>
                                    <Text strong>识别字数：</Text>
                                    <Text>{selectedRecord.char_count} 个</Text>
                                </div>

                                {selectedRecord.ai_comment && (
                                    <div>
                                        <Text strong>AI 评语：</Text>
                                        <Paragraph style={{ marginTop: 4, marginBottom: 0 }}>
                                            {selectedRecord.ai_comment}
                                        </Paragraph>
                                    </div>
                                )}

                                {selectedRecord.strengths && (
                                    <div>
                                        <Text strong style={{ color: '#52c41a' }}>优点：</Text>
                                        <Paragraph style={{ marginTop: 4, marginBottom: 0 }}>
                                            {selectedRecord.strengths}
                                        </Paragraph>
                                    </div>
                                )}

                                {selectedRecord.suggestions && (
                                    <div>
                                        <Text strong style={{ color: '#1890ff' }}>改进建议：</Text>
                                        <Paragraph style={{ marginTop: 4, marginBottom: 0 }}>
                                            {selectedRecord.suggestions}
                                        </Paragraph>
                                    </div>
                                )}

                                <div>
                                    <Text strong>状态：</Text>
                                    <StatusTag status={selectedRecord.status} />
                                </div>
                            </Space>
                        </Col>
                    </Row>
                )}
            </Modal>
        </div>
    )
}

export default CalligraphyGrading
