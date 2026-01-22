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
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { analysisAPI, generationAPI, recommendationAPI, getHistoryDetail, deleteHistory } from '../services/api';
import { DeleteOutlined, EyeOutlined } from '@ant-design/icons';

const { Title, Paragraph } = Typography;

const HistoryPage = () => {
  const { Text } = Typography;
  const [activeTab, setActiveTab] = useState('analysis');
  const [analysisHistory, setAnalysisHistory] = useState([]);
  const [generationHistory, setGenerationHistory] = useState([]);
  const [songHistory, setSongHistory] = useState([]);
  const [recommendationHistory, setRecommendationHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [detailData, setDetailData] = useState(null);

  useEffect(() => {
    loadHistory();
  }, [activeTab]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadHistory = async () => {
    setLoading(true);
    try {
      if (activeTab === 'analysis') {
        const response = await analysisAPI.getHistory(null, 20);
        if (response.data.success) {
          setAnalysisHistory(response.data.data || []);
        }
      } else if (activeTab === 'generation') {
        const response = await generationAPI.getHistory(null, 50);
        if (response.data.success) {
          const allHistory = response.data.data || [];
          // 分离歌词生成和歌曲生成
          const lyricsHistory = allHistory.filter(item => 
            !item.prompt || !item.prompt.includes('歌曲生成')
          );
          const songs = allHistory.filter(item => 
            item.prompt && item.prompt.includes('歌曲生成')
          );
          setGenerationHistory(lyricsHistory);
          setSongHistory(songs);
        }
      } else if (activeTab === 'songs') {
        // 歌曲历史从generation历史中筛选
        const response = await generationAPI.getHistory(null, 100);
        if (response.data.success) {
          const allHistory = response.data.data || [];
          const songs = allHistory.filter(item => 
            item.prompt && item.prompt.includes('歌曲生成')
          );
          setSongHistory(songs);
        }
      } else if (activeTab === 'recommendation') {
        const response = await recommendationAPI.getHistory(null, 20);
        if (response.data.success) {
          setRecommendationHistory(response.data.data || []);
        }
      }
    } catch (error) {
      console.error('加载历史失败:', error);
      message.error('加载历史记录失败：' + (error.response?.data?.error || error.message));
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
              <Card 
                style={{ 
                  width: '100%',
                  borderRadius: 12,
                  border: '1px solid #e8e8e8',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                  transition: 'all 0.3s ease'
                }}
                hoverable
                onMouseEnter={(e) => {
                  e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.12)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.06)';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Tag color="blue" style={{ fontSize: 13, padding: '4px 12px', borderRadius: 6 }}>
                      分析记录
                    </Tag>
                    <Text type="secondary" style={{ marginLeft: 8, fontSize: 13 }}>
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
          dataSource={generationHistory.filter(item => 
            !item.prompt || !item.prompt.includes('歌曲生成')
          )}
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
              <Card 
                style={{ 
                  width: '100%',
                  borderRadius: 12,
                  border: '1px solid #e8e8e8',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                  transition: 'all 0.3s ease'
                }}
                hoverable
                onMouseEnter={(e) => {
                  e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.12)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.06)';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Tag color="green" style={{ fontSize: 13, padding: '4px 12px', borderRadius: 6 }}>
                      生成记录
                    </Tag>
                    <Tag color="cyan" style={{ fontSize: 13, padding: '4px 12px', borderRadius: 6 }}>
                      {item.style || '通用'}
                    </Tag>
                    <Text type="secondary" style={{ marginLeft: 8, fontSize: 13 }}>
                      {formatDate(item.created_at)}
                    </Text>
                  </div>
                  <Paragraph>
                    <Text strong>提示词：</Text>
                    <Text>{item.prompt}</Text>
                  </Paragraph>
                  <Paragraph>
                    <Text strong>生成内容：</Text>
                    <div style={{ marginTop: 8 }}>
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        components={{
                          h1: ({node, ...props}) => <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8 }} {...props} />,
                          h2: ({node, ...props}) => <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8 }} {...props} />,
                          h3: ({node, ...props}) => <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8 }} {...props} />,
                          h4: ({node, ...props}) => <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8 }} {...props} />,
                          h5: ({node, ...props}) => <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8 }} {...props} />,
                          h6: ({node, ...props}) => <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8 }} {...props} />,
                          p: ({node, ...props}) => <div style={{ marginBottom: 4, whiteSpace: 'pre-line' }} {...props} />
                        }}
                      >
                        {(() => {
                          const lyrics = String(item.generated_lyrics || '');
                          const lines = lyrics.split('\n');
                          const previewLines = lines.slice(0, 10);
                          return previewLines.join('\n') + (lines.length > 10 ? '\n\n...' : '');
                        })()}
                      </ReactMarkdown>
                    </div>
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
      key: 'songs',
      label: '生成歌曲',
      children: (
        <List
          loading={loading}
          dataSource={songHistory}
          renderItem={(item) => {
            // 解析歌曲数据
            let songData = null;
            try {
              // 尝试从generated_lyrics中解析JSON数据
              const lyricsContent = item.generated_lyrics || '';
              const jsonMatch = lyricsContent.match(/```json\n([\s\S]*?)\n```/);
              if (jsonMatch) {
                songData = JSON.parse(jsonMatch[1]);
              } else {
                // 如果没有JSON，尝试解析markdown格式
                const titleMatch = lyricsContent.match(/#\s*(.+)/);
                if (titleMatch) {
                  songData = {
                    title: titleMatch[1],
                    lyrics: lyricsContent.replace(/^#.*\n/, '').replace(/##.*\n/g, '').trim()
                  };
                }
              }
            } catch (e) {
              console.error('解析歌曲数据失败:', e);
            }

            return (
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
                <Card 
                  style={{ 
                    width: '100%',
                    borderRadius: 12,
                    border: '1px solid #e8e8e8',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                    transition: 'all 0.3s ease'
                  }}
                  hoverable
                  onMouseEnter={(e) => {
                    e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.12)';
                    e.currentTarget.style.transform = 'translateY(-2px)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.06)';
                    e.currentTarget.style.transform = 'translateY(0)';
                  }}
                >
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Tag color="purple" style={{ fontSize: 13, padding: '4px 12px', borderRadius: 6 }}>
                        歌曲生成
                      </Tag>
                      {songData?.title && (
                        <Tag color="blue" style={{ fontSize: 13, padding: '4px 12px', borderRadius: 6 }}>
                          {songData.title}
                        </Tag>
                      )}
                      {songData?.status && (
                        <Tag 
                          color={songData.status === 'completed' ? 'green' : 'orange'}
                          style={{ fontSize: 13, padding: '4px 12px', borderRadius: 6 }}
                        >
                          {songData.status === 'completed' ? '已完成' : songData.status === 'pending' ? '处理中' : songData.status}
                        </Tag>
                      )}
                      <Text type="secondary" style={{ marginLeft: 8, fontSize: 13 }}>
                        {formatDate(item.created_at)}
                      </Text>
                    </div>
                    {songData?.title && (
                      <Paragraph>
                        <Text strong>歌曲标题：</Text>
                        <Text>{songData.title}</Text>
                      </Paragraph>
                    )}
                    {songData?.lyrics && (
                      <Paragraph>
                        <Text strong>歌词：</Text>
                        <Text style={{ whiteSpace: 'pre-line' }}>
                          {songData.lyrics.substring(0, 150)}...
                        </Text>
                      </Paragraph>
                    )}
                    {songData?.audio_url && (
                      <div>
                        <Text strong>音频：</Text>
                        <div style={{ marginTop: 8 }}>
                          <audio controls style={{ width: '100%' }}>
                            <source src={songData.audio_url} type="audio/mpeg" />
                            您的浏览器不支持音频播放
                          </audio>
                          <Button
                            type="link"
                            href={songData.audio_url}
                            target="_blank"
                            style={{ marginTop: 8 }}
                          >
                            下载音频
                          </Button>
                        </div>
                      </div>
                    )}
                    {songData?.image_url && (
                      <div>
                        <Text strong>封面：</Text>
                        <div style={{ marginTop: 8 }}>
                          <img 
                            src={songData.image_url} 
                            alt="封面" 
                            style={{ maxWidth: '200px', height: 'auto', borderRadius: 8 }}
                          />
                        </div>
                      </div>
                    )}
                    {songData?.duration && Number(songData.duration) > 0 && (
                      <Text type="secondary">
                        时长: {songData.duration.toFixed(2)} 秒
                      </Text>
                    )}
                    {songData?.task_id && (
                      <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: songData?.duration && Number(songData.duration) > 0 ? 8 : 0 }}>
                        任务ID: {songData.task_id}
                      </Text>
                    )}
                  </Space>
                </Card>
              </List.Item>
            );
          }}
          locale={{ emptyText: <Empty description="暂无生成的歌曲" /> }}
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
              <Card 
                style={{ 
                  width: '100%',
                  borderRadius: 12,
                  border: '1px solid #e8e8e8',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                  transition: 'all 0.3s ease'
                }}
                hoverable
                onMouseEnter={(e) => {
                  e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.12)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.06)';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Tag color="red" style={{ fontSize: 13, padding: '4px 12px', borderRadius: 6 }}>
                      推荐记录
                    </Tag>
                    <Text type="secondary" style={{ marginLeft: 8, fontSize: 13 }}>
                      {formatDate(item.created_at)}
                    </Text>
                  </div>
                  <Paragraph style={{ marginBottom: 0 }}>
                    <Text strong>查询歌词：</Text>
                    <Text style={{ color: '#666' }}>{item.query_lyrics?.substring(0, 100)}...</Text>
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
            <div style={{ marginTop: 8 }}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {detailData.lyrics}
              </ReactMarkdown>
            </div>
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
    } else if (activeTab === 'generation' || activeTab === 'songs') {
      // 检查是否是歌曲生成记录
      const isSong = detailData.prompt && detailData.prompt.includes('歌曲生成');
      
      if (isSong) {
        // 解析歌曲数据
        let songData = null;
        try {
          const lyricsContent = detailData.generated_lyrics || '';
          const jsonMatch = lyricsContent.match(/```json\n([\s\S]*?)\n```/);
          if (jsonMatch) {
            songData = JSON.parse(jsonMatch[1]);
          } else {
            // 解析markdown格式
            const titleMatch = lyricsContent.match(/#\s*(.+)/);
            if (titleMatch) {
              songData = {
                title: titleMatch[1],
                lyrics: lyricsContent.replace(/^#.*\n/, '').replace(/##.*\n/g, '').trim()
              };
            }
          }
        } catch (e) {
          console.error('解析歌曲数据失败:', e);
        }

        return (
          <div>
            {songData && (
              <>
                {songData.title && (
                  <Card size="small" style={{ marginBottom: 16, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none' }}>
                    <Text strong style={{ color: '#fff', fontSize: 14, display: 'block' }}>
                      {songData.title}
                    </Text>
                  </Card>
                )}
                
                {songData.status && (
                  <Paragraph style={{ marginBottom: 16 }}>
                    <Text strong>状态：</Text>
                    <Tag color={songData.status === 'completed' ? 'green' : 'orange'} style={{ fontSize: 14, padding: '4px 12px' }}>
                      {songData.status === 'completed' ? '已完成' : songData.status === 'pending' ? '处理中' : songData.status}
                    </Tag>
                  </Paragraph>
                )}

                {songData.tags && (
                  <Paragraph style={{ marginBottom: 16 }}>
                    <Text strong>风格标签：</Text>
                    <Tag color="blue" style={{ fontSize: 13, padding: '4px 10px', marginLeft: 8 }}>
                      {songData.tags}
                    </Tag>
                  </Paragraph>
                )}

                {songData.lyrics && (
                  <Card 
                    size="small" 
                    style={{ 
                      marginBottom: 16,
                      border: '1px solid #e8e8e8',
                      borderRadius: 8,
                      boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
                    }}
                  >
                    <Title level={5} style={{ marginBottom: 12, color: '#1890ff' }}>
                      <span style={{ marginRight: 8 }}>📝</span>
                      用户输入的歌词
                    </Title>
                    <div 
                      style={{ 
                        marginTop: 8,
                        padding: '12px',
                        background: '#fafafa',
                        borderRadius: 6,
                        border: '1px solid #f0f0f0',
                        lineHeight: '1.8',
                        color: '#333',
                        whiteSpace: 'pre-line',
                        fontFamily: 'inherit'
                      }}
                    >
                      {songData.lyrics}
                    </div>
                  </Card>
                )}

                {(songData.clips && songData.clips.length > 0) || songData.audio_url ? (
                  <Card 
                    size="small" 
                    style={{ 
                      marginBottom: 16,
                      border: '1px solid #e8e8e8',
                      borderRadius: 8,
                      boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
                    }}
                  >
                    <Title level={5} style={{ marginBottom: 12, color: '#52c41a' }}>
                      <span style={{ marginRight: 8 }}>🎵</span>
                      生成的音频{songData.clips && songData.clips.length > 1 ? `（${songData.clips.length}个版本）` : ''}
                    </Title>
                    {songData.clips && songData.clips.length > 0 ? (
                      songData.clips.map((clip, index) => {
                        // 根据tags生成风格描述
                        const tags = songData.tags || '';
                        let description = '';
                        if (tags) {
                          const tagList = tags.split(',').map(t => t.trim()).filter(t => t);
                          if (tagList.length > 0) {
                            description = tagList.slice(0, 3).join('、');
                          } else {
                            description = '风格版本 ' + (index + 1);
                          }
                        } else {
                          // 根据索引生成默认描述
                          const styleDescriptions = ['经典风格', '现代风格', '创新风格'];
                          description = styleDescriptions[index] || `风格版本 ${index + 1}`;
                        }
                        
                        return (
                          <div key={index} style={{ marginTop: index > 0 ? 16 : 0 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                              <Text strong>版本 {index + 1}</Text>
                              <Tag color={index === 0 ? 'green' : 'blue'}>
                                {description}
                              </Tag>
                            </div>
                            {clip.audio_url && (
                              <>
                                <audio 
                                  controls 
                                  style={{ 
                                    width: '100%',
                                    borderRadius: 6,
                                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                                  }}
                                  onPlay={(e) => {
                                    // 设置全局音频
                                    const { setGlobalAudioState } = require('../components/AudioPlayer/GlobalAudioPlayer');
                                    const audio = e.target;
                                    setGlobalAudioState({
                                      src: clip.audio_url,
                                      playing: true,
                                      title: `版本 ${index + 1} - ${description}`
                                    });
                                    // 暂停其他音频
                                    document.querySelectorAll('audio').forEach(a => {
                                      if (a !== audio && !a.paused) {
                                        a.pause();
                                      }
                                    });
                                  }}
                                >
                                  <source src={clip.audio_url} type="audio/mpeg" />
                                  您的浏览器不支持音频播放
                                </audio>
                                <Button
                                  type="primary"
                                  href={clip.audio_url}
                                  target="_blank"
                                  style={{ 
                                    marginTop: 8,
                                    borderRadius: 6,
                                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                                  }}
                                  block
                                >
                                  下载此版本
                                </Button>
                              </>
                            )}
                          </div>
                        );
                      })
                    ) : songData.audio_url ? (
                      <div style={{ marginTop: 12 }}>
                        <audio 
                          controls 
                          style={{ 
                            width: '100%',
                            borderRadius: 6,
                            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                          }}
                          onPlay={(e) => {
                            // 设置全局音频
                            const { setGlobalAudioState } = require('../components/AudioPlayer/GlobalAudioPlayer');
                            const audio = e.target;
                            setGlobalAudioState({
                              src: songData.audio_url,
                              playing: true,
                              title: songData.title || '生成的歌曲'
                            });
                            // 暂停其他音频
                            document.querySelectorAll('audio').forEach(a => {
                              if (a !== audio && !a.paused) {
                                a.pause();
                              }
                            });
                          }}
                        >
                          <source src={songData.audio_url} type="audio/mpeg" />
                          您的浏览器不支持音频播放
                        </audio>
                        <Button
                          type="primary"
                          href={songData.audio_url}
                          target="_blank"
                          style={{ 
                            marginTop: 12,
                            borderRadius: 6,
                            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                          }}
                          block
                        >
                          下载音频
                        </Button>
                      </div>
                    ) : null}
                  </Card>
                ) : null}
              </>
            )}
            {!songData && (
              <>
                <Paragraph>
                  <Text strong>风格：</Text>
                  <Text>{detailData.style || '通用'}</Text>
                </Paragraph>
                <Paragraph>
                  <Text strong>生成内容：</Text>
                  <div style={{ marginTop: 8 }}>
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      components={{
                        h1: ({node, ...props}) => <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8 }} {...props} />,
                        h2: ({node, ...props}) => <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8 }} {...props} />,
                        h3: ({node, ...props}) => <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8 }} {...props} />,
                        h4: ({node, ...props}) => <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8 }} {...props} />,
                        h5: ({node, ...props}) => <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8 }} {...props} />,
                        h6: ({node, ...props}) => <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8 }} {...props} />,
                        p: ({node, ...props}) => <div style={{ marginBottom: 4, whiteSpace: 'pre-line' }} {...props} />
                      }}
                    >
                      {detailData.generated_lyrics}
                    </ReactMarkdown>
                  </div>
                </Paragraph>
              </>
            )}
          </div>
        );
      } else {
        // 普通歌词生成
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
            <div style={{ marginTop: 8 }}>
              <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={{
                  h1: ({node, ...props}) => <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8 }} {...props} />,
                  h2: ({node, ...props}) => <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8 }} {...props} />,
                  h3: ({node, ...props}) => <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8 }} {...props} />,
                  h4: ({node, ...props}) => <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8 }} {...props} />,
                  h5: ({node, ...props}) => <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8 }} {...props} />,
                  h6: ({node, ...props}) => <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8 }} {...props} />,
                  p: ({node, ...props}) => <div style={{ marginBottom: 4, whiteSpace: 'pre-line' }} {...props} />
                }}
              >
                {detailData.generated_lyrics}
              </ReactMarkdown>
            </div>
          </Paragraph>
        </div>
      );
      }
    } else if (activeTab === 'recommendation') {
      return (
        <div>
          <Paragraph>
            <Text strong>查询歌词：</Text>
            <div style={{ marginTop: 8 }}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {detailData.query_lyrics}
              </ReactMarkdown>
            </div>
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
                          <Space direction="vertical" style={{ width: '100%' }}>
                            <div>
                              <Text strong>{rec.song?.title || `推荐 ${i + 1}`}</Text>
                              <br />
                              <Text type="secondary">歌手：{rec.song?.artist || '未知'}</Text>
                              <br />
                              <Text type="secondary">相似度：{(rec.similarity * 100).toFixed(1)}%</Text>
                              <br />
                              <Text type="secondary">推荐理由：{rec.explanation || '基于歌词相似度的推荐'}</Text>
                            </div>
                            {rec.song?.external_links && (
                              <div style={{ marginTop: 8 }}>
                                <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
                                  在线播放（点击下方链接在对应平台播放）：
                                </Text>
                                <Space wrap>
                                  {rec.song.external_links.qq_music && (
                                    <Button
                                      type="primary"
                                      size="small"
                                      onClick={() => window.open(rec.song.external_links.qq_music, '_blank')}
                                    >
                                      🎵 QQ音乐
                                    </Button>
                                  )}
                                  {rec.song.external_links.netease && (
                                    <Button
                                      size="small"
                                      onClick={() => window.open(rec.song.external_links.netease, '_blank')}
                                    >
                                      🎵 网易云
                                    </Button>
                                  )}
                                  {rec.song.external_links.kugou && (
                                    <Button
                                      size="small"
                                      onClick={() => window.open(rec.song.external_links.kugou, '_blank')}
                                    >
                                      🎵 酷狗
                                    </Button>
                                  )}
                                </Space>
                                <Text type="secondary" style={{ fontSize: 11, display: 'block', marginTop: 8 }}>
                                  提示：点击上方按钮可在对应音乐平台播放，支持在线试听
                                </Text>
                              </div>
                            )}
                            {rec.song?.lyrics && (
                              <div style={{ marginTop: 8 }}>
                                <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                                  歌词：
                                </Text>
                                <Card size="small" style={{ background: '#f5f5f5' }}>
                                  <Text type="secondary" style={{ fontSize: 12, whiteSpace: 'pre-line' }}>
                                    {rec.song.lyrics.split('\n')
                                      .filter(line => {
                                        const timePattern = /^\[\d{2}:\d{2}\.\d{3}\]/;
                                        const metaPattern = /\[.*?(作词|作曲|编曲|制作人|监制).*?\]/;
                                        const trimmed = line.trim();
                                        return trimmed && !timePattern.test(trimmed) && !metaPattern.test(trimmed);
                                      })
                                      .map(line => line.replace(/\[\d{2}:\d{2}\.\d{3}\]/g, '').trim())
                                      .filter(line => line)
                                      .join('\n')}
                                  </Text>
                                </Card>
                              </div>
                            )}
                          </Space>
                        </Card>
                      ))}
                    </div>
                  );
                } catch (e) {
                  console.error('解析推荐数据失败:', e);
                  return <Text>数据格式错误: {e.message}</Text>;
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
    <div style={{ 
      padding: '24px', 
      background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
      minHeight: 'calc(100vh - 112px)'
    }}>
      <Card 
        style={{
          borderRadius: 16,
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          border: 'none',
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)'
        }}
      >
        <Title 
          level={2} 
          style={{ 
            marginBottom: 24,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            fontSize: 32,
            fontWeight: 'bold'
          }}
        >
          历史记录
        </Title>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
          size="large"
          style={{
            fontSize: 16
          }}
      />
      </Card>
      <Modal
        title={
          <span style={{ 
            fontSize: 20,
            fontWeight: 'bold',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            历史记录详情
          </span>
        }
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button 
            key="close" 
            onClick={() => setDetailModalVisible(false)}
            type="primary"
            style={{
              borderRadius: 6,
              height: 40,
              padding: '0 24px'
            }}
          >
            关闭
          </Button>
        ]}
        width={900}
        style={{
          borderRadius: 16
        }}
        styles={{
          body: {
            padding: '24px',
            maxHeight: '70vh',
            overflowY: 'auto'
          }
        }}
      >
        {renderDetailContent()}
      </Modal>
    </div>
  );
};

export default HistoryPage;



