import React, { useState, useEffect } from 'react';
import {
  Card,
  Tabs,
  List,
  Typography,
  Tag,
  Space,
  Empty,
  Button,
  Modal,
  Popconfirm,
  message
} from 'antd';
import { analysisAPI, generationAPI, recommendationAPI, getHistoryDetail, deleteHistory } from '../services/api';
import { DeleteOutlined, EyeOutlined } from '@ant-design/icons';

const { Title, Paragraph } = Typography;

const HistoryPage = () => {
  const { Text } = Typography;
  const [activeTab, setActiveTab] = useState('analysis');
  const [analysisHistory, setAnalysisHistory] = useState([]);
  const [generationHistory, setGenerationHistory] = useState([]);
  const [recommendationHistory, setRecommendationHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [detailData, setDetailData] = useState(null);

  useEffect(() => {
    loadHistory();
  }, [activeTab]);

  const loadHistory = async () => {
    setLoading(true);
    try {
      if (activeTab === 'analysis') {
        const response = await analysisAPI.getHistory(null, 20);
        if (response.data.success) {
          setAnalysisHistory(response.data.data || []);
        }
      } else if (activeTab === 'generation') {
        const response = await generationAPI.getHistory(null, 20);
        if (response.data.success) {
          setGenerationHistory(response.data.data || []);
        }
      } else if (activeTab === 'recommendation') {
        const response = await recommendationAPI.getHistory(null, 20);
        if (response.data.success) {
          setRecommendationHistory(response.data.data || []);
        }
      }
    } catch (error) {
      console.error('加载历史失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '未知时间';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
  };

  const handleViewDetail = async (type, id) => {
    try {
      const response = await getHistoryDetail(type, id);
      if (response.data.success) {
        setDetailData(response.data.data);
        setDetailModalVisible(true);
      }
    } catch (error) {
      message.error('加载详情失败：' + (error.response?.data?.error || error.message));
    }
  };

  const handleDelete = async (type, id) => {
    try {
      const response = await deleteHistory(type, id);
      if (response.data.success) {
        message.success('删除成功');
        loadHistory(); // 重新加载列表
      }
    } catch (error) {
      message.error('删除失败：' + (error.response?.data?.error || error.message));
    }
  };

  const tabItems = [
    {
      key: 'analysis',
      label: '分析历史',
      children: (
        <List
          loading={loading}
          dataSource={analysisHistory}
          renderItem={(item) => (
            <List.Item
              actions={[
                <Button
                  type="link"
                  icon={<EyeOutlined />}
                  onClick={() => handleViewDetail('analysis', item.id)}
                >
                  查看详情
                </Button>,
                <Popconfirm
                  title="确定要删除这条记录吗？"
                  onConfirm={() => handleDelete('analysis', item.id)}
                  okText="确定"
                  cancelText="取消"
                >
                  <Button type="link" danger icon={<DeleteOutlined />}>
                    删除
                  </Button>
                </Popconfirm>
              ]}
            >
              <Card style={{ width: '100%' }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Tag color="blue">分析记录</Tag>
                    <Text type="secondary" style={{ marginLeft: 8 }}>
                      {formatDate(item.created_at)}
                    </Text>
                  </div>
                  <Paragraph>
                    <Text strong>歌词：</Text>
                    <Text>{item.lyrics?.substring(0, 100)}...</Text>
                  </Paragraph>
                          {item.sentiment_result && (
                            <Card size="small" style={{ marginTop: 8, background: '#f5f5f5' }}>
                              <Text strong>分析结果：</Text>
                              <div style={{ marginTop: 8 }}>
                                {(() => {
                                  try {
                                    const sentiment = JSON.parse(item.sentiment_result);
                                    return (
                                      <div>
                                        <Text type="secondary">情感基调：{sentiment.overall_tone}</Text>
                                        <br />
                                        <Text type="secondary">情感得分：{sentiment.overall_score?.toFixed(2)}</Text>
                                      </div>
                                    );
                                  } catch (e) {
                                    return <Text type="secondary">分析结果数据格式错误</Text>;
                                  }
                                })()}
                              </div>
                            </Card>
                          )}
                          {item.theme_result && (
                            <Card size="small" style={{ marginTop: 8, background: '#f5f5f5' }}>
                              <Text strong>主题分析：</Text>
                              <div style={{ marginTop: 8 }}>
                                {(() => {
                                  try {
                                    const theme = JSON.parse(item.theme_result);
                                    return (
                                      <div>
                                        {theme.themes && theme.themes.length > 0 ? (
                                          theme.themes.map((t, i) => (
                                            <div key={i} style={{ marginTop: 4 }}>
                                              <Text type="secondary">
                                                {i + 1}. {t.theme} (匹配度: {t.score})
                                              </Text>
                                            </div>
                                          ))
                                        ) : (
                                          <Text type="secondary">未检测到主题</Text>
                                        )}
                                      </div>
                                    );
                                  } catch (e) {
                                    return <Text type="secondary">主题数据格式错误</Text>;
                                  }
                                })()}
                              </div>
                            </Card>
                          )}
                </Space>
              </Card>
            </List.Item>
          )}
          locale={{ emptyText: <Empty description="暂无分析历史" /> }}
        />
      )
    },
    {
      key: 'generation',
      label: '生成历史',
      children: (
        <List
          loading={loading}
          dataSource={generationHistory}
          renderItem={(item) => (
            <List.Item
              actions={[
                <Button
                  type="link"
                  icon={<EyeOutlined />}
                  onClick={() => handleViewDetail('generation', item.id)}
                >
                  查看详情
                </Button>,
                <Popconfirm
                  title="确定要删除这条记录吗？"
                  onConfirm={() => handleDelete('generation', item.id)}
                  okText="确定"
                  cancelText="取消"
                >
                  <Button type="link" danger icon={<DeleteOutlined />}>
                    删除
                  </Button>
                </Popconfirm>
              ]}
            >
              <Card style={{ width: '100%' }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Tag color="green">生成记录</Tag>
                    <Tag>{item.style || '通用'}</Tag>
                    <Text type="secondary" style={{ marginLeft: 8 }}>
                      {formatDate(item.created_at)}
                    </Text>
                  </div>
                  <Paragraph>
                    <Text strong>提示词：</Text>
                    <Text>{item.prompt}</Text>
                  </Paragraph>
                  <Paragraph>
                    <Text strong>生成内容：</Text>
                    <Text style={{ whiteSpace: 'pre-line' }}>
                      {item.generated_lyrics?.substring(0, 200)}...
                    </Text>
                  </Paragraph>
                </Space>
              </Card>
            </List.Item>
          )}
          locale={{ emptyText: <Empty description="暂无生成历史" /> }}
        />
      )
    },
    {
      key: 'recommendation',
      label: '推荐历史',
      children: (
        <List
          loading={loading}
          dataSource={recommendationHistory}
          renderItem={(item) => (
            <List.Item
              actions={[
                <Button
                  type="link"
                  icon={<EyeOutlined />}
                  onClick={() => handleViewDetail('recommendation', item.id)}
                >
                  查看详情
                </Button>,
                <Popconfirm
                  title="确定要删除这条记录吗？"
                  onConfirm={() => handleDelete('recommendation', item.id)}
                  okText="确定"
                  cancelText="取消"
                >
                  <Button type="link" danger icon={<DeleteOutlined />}>
                    删除
                  </Button>
                </Popconfirm>
              ]}
            >
              <Card style={{ width: '100%' }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Tag color="red">推荐记录</Tag>
                    <Text type="secondary" style={{ marginLeft: 8 }}>
                      {formatDate(item.created_at)}
                    </Text>
                  </div>
                  <Paragraph>
                    <Text strong>查询歌词：</Text>
                    <Text>{item.query_lyrics?.substring(0, 100)}...</Text>
                  </Paragraph>
                </Space>
              </Card>
            </List.Item>
          )}
          locale={{ emptyText: <Empty description="暂无推荐历史" /> }}
        />
      )
    }
  ];

  const renderDetailContent = () => {
    if (!detailData) return null;
    
    if (activeTab === 'analysis') {
      return (
        <div>
          <Paragraph>
            <Text strong>歌词：</Text>
            <Text style={{ whiteSpace: 'pre-line' }}>{detailData.lyrics}</Text>
          </Paragraph>
          {detailData.sentiment_result && (
            <Card size="small" style={{ marginTop: 16 }}>
              <Title level={5}>情感分析结果</Title>
              {(() => {
                try {
                  const sentiment = JSON.parse(detailData.sentiment_result);
                  return (
                    <div>
                      <Paragraph>情感基调：{sentiment.overall_tone}</Paragraph>
                      <Paragraph>情感得分：{sentiment.overall_score?.toFixed(2)}</Paragraph>
                    </div>
                  );
                } catch (e) {
                  return <Text>数据格式错误</Text>;
                }
              })()}
            </Card>
          )}
          {detailData.theme_result && (
            <Card size="small" style={{ marginTop: 16 }}>
              <Title level={5}>主题分析结果</Title>
              {(() => {
                try {
                  const theme = JSON.parse(detailData.theme_result);
                  return (
                    <div>
                      {theme.themes?.map((t, i) => (
                        <Paragraph key={i}>
                          {t.theme} (匹配度: {t.score})
                        </Paragraph>
                      ))}
                    </div>
                  );
                } catch (e) {
                  return <Text>数据格式错误</Text>;
                }
              })()}
            </Card>
          )}
        </div>
      );
    } else if (activeTab === 'generation') {
      return (
        <div>
          <Paragraph>
            <Text strong>提示词：</Text>
            <Text>{detailData.prompt}</Text>
          </Paragraph>
          <Paragraph>
            <Text strong>风格：</Text>
            <Text>{detailData.style || '通用'}</Text>
          </Paragraph>
          <Paragraph>
            <Text strong>生成内容：</Text>
            <Text style={{ whiteSpace: 'pre-line' }}>{detailData.generated_lyrics}</Text>
          </Paragraph>
        </div>
      );
    } else if (activeTab === 'recommendation') {
      return (
        <div>
          <Paragraph>
            <Text strong>查询歌词：</Text>
            <Text style={{ whiteSpace: 'pre-line' }}>{detailData.query_lyrics}</Text>
          </Paragraph>
          {detailData.recommendations && (
            <Card size="small" style={{ marginTop: 16 }}>
              <Title level={5}>推荐结果</Title>
              {(() => {
                try {
                  const recs = JSON.parse(detailData.recommendations);
                  return (
                    <div>
                      {recs.recommendations?.map((rec, i) => (
                        <Card key={i} size="small" style={{ marginTop: 8 }}>
                          <Paragraph>
                            <Text strong>{rec.song?.title || `推荐 ${i + 1}`}</Text>
                            <br />
                            <Text type="secondary">歌手：{rec.song?.artist || '未知'}</Text>
                            <br />
                            <Text type="secondary">相似度：{(rec.similarity * 100).toFixed(1)}%</Text>
                          </Paragraph>
                        </Card>
                      ))}
                    </div>
                  );
                } catch (e) {
                  return <Text>数据格式错误</Text>;
                }
              })()}
            </Card>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="page-container">
      <Title level={2} className="page-title">📜 历史记录</Title>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
      />
      <Modal
        title="历史记录详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        {renderDetailContent()}
      </Modal>
    </div>
  );
};

export default HistoryPage;



