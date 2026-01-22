import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Card,
  Input,
  Button,
  Space,
  Typography,
  List,
  Tag,
  message,
  Empty
} from 'antd';
import { recommendationAPI } from '../services/api';

const { TextArea } = Input;
const { Title, Paragraph } = Typography;

const RecommendationPage = () => {
  const { Text } = Typography;
  // 从localStorage恢复保存的内容
  const [lyrics, setLyrics] = useState(() => {
    const saved = localStorage.getItem('recommendation_lyrics');
    return saved || '';
  });
  const [loading, setLoading] = useState(false);
  const [recommendations, setRecommendations] = useState(() => {
    const saved = localStorage.getItem('recommendation_results');
    return saved ? JSON.parse(saved) : [];
  });
  const [expandedLyrics, setExpandedLyrics] = useState({}); // 记录哪些歌词已展开
  
  // 使用ref来跟踪组件是否已卸载
  const isMountedRef = useRef(true);

  // 组件挂载时设置isMountedRef为true，并检查是否有正在进行的请求
  useEffect(() => {
    isMountedRef.current = true;
    
    // 检查是否有正在进行的请求（通过localStorage标记）
    const checkRequestStatus = () => {
      const isRequesting = localStorage.getItem('recommendation_requesting') === 'true';
      if (isRequesting) {
        setLoading(true);
        // 定期检查请求是否完成（通过检查localStorage中的结果）
        const checkInterval = setInterval(() => {
          const savedResults = localStorage.getItem('recommendation_results');
          const stillRequesting = localStorage.getItem('recommendation_requesting') === 'true';
          
          if (!stillRequesting && savedResults) {
            // 请求已完成
            clearInterval(checkInterval);
            try {
              const results = JSON.parse(savedResults);
              if (isMountedRef.current) {
                setRecommendations(results);
                setLoading(false);
                message.success('推荐完成！');
              }
            } catch (e) {
              if (isMountedRef.current) {
                setLoading(false);
              }
            }
          }
        }, 500); // 每500ms检查一次
        
        // 清理定时器
        return () => clearInterval(checkInterval);
      } else {
        // 没有正在进行的请求，直接加载已保存的结果
        const savedResults = localStorage.getItem('recommendation_results');
        if (savedResults) {
          try {
            const results = JSON.parse(savedResults);
            if (results.length > 0 && isMountedRef.current) {
              setRecommendations(results);
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    };
    
    const cleanup = checkRequestStatus();
    
    return () => {
      // 组件卸载时，不取消请求，只标记组件已卸载
      isMountedRef.current = false;
      if (cleanup) cleanup();
    };
  }, []);

  // 保存歌词到localStorage（使用 useCallback 优化）
  const handleLyricsChange = useCallback((value) => {
    setLyrics(value);
    // 使用防抖减少 localStorage 写入频率
    if (handleLyricsChange.timeout) {
      clearTimeout(handleLyricsChange.timeout);
    }
    handleLyricsChange.timeout = setTimeout(() => {
      localStorage.setItem('recommendation_lyrics', value);
    }, 300);
  }, []);

  const handleRecommend = useCallback(async () => {
    if (!lyrics.trim()) {
      message.warning('请输入歌词');
      return;
    }

    setLoading(true);
    // 标记请求正在进行
    localStorage.setItem('recommendation_requesting', 'true');
    
    try {
      const response = await recommendationAPI.recommend(lyrics, 5);
      
      // 请求完成后，无论组件是否已卸载，都保存结果
      if (response.data.success) {
        const recommendationsData = response.data.data.recommendations || [];
        
        // 保存结果到localStorage（即使组件已卸载也会保存）
        localStorage.setItem('recommendation_results', JSON.stringify(recommendationsData));
        localStorage.removeItem('recommendation_requesting');
        
        // 如果组件仍然挂载，更新状态
        if (isMountedRef.current) {
          setRecommendations(recommendationsData);
          setLoading(false);
          message.success('推荐完成！');
        } else {
          // 组件已卸载，但结果已保存到localStorage，用户切换回来时会自动恢复
          console.log('推荐完成，但组件已卸载，结果已保存到localStorage');
        }
      }
    } catch (error) {
      localStorage.removeItem('recommendation_requesting');
      
      // 如果组件仍然挂载，显示错误
      if (isMountedRef.current) {
        setLoading(false);
        message.error('推荐失败：' + (error.response?.data?.error || error.message));
      }
    }
  }, [lyrics]);

  return (
    <div className="page-container">
      <Title level={2} className="page-title">智能推荐</Title>

      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={4}>输入歌词</Title>
            <TextArea
              rows={6}
              placeholder="请输入歌词，系统将为您推荐相似的歌曲..."
              value={lyrics}
              onChange={(e) => handleLyricsChange(e.target.value)}
            />
          </div>
          <Space style={{ width: '100%' }} direction="vertical">
            <Button
              type="primary"
              size="large"
              onClick={handleRecommend}
              loading={loading}
              block
            >
              获取推荐
            </Button>
            <Button
              onClick={() => {
                setLyrics('');
                setRecommendations([]);
                setExpandedLyrics({});
                // 清空相关的localStorage
                localStorage.removeItem('recommendation_lyrics');
                localStorage.removeItem('recommendation_results');
                message.info('已重置所有输入');
              }}
              block
            >
              重置
            </Button>
          </Space>
        </Space>
      </Card>

      {recommendations.length > 0 && (
        <Card style={{ marginTop: 24 }}>
          <Title level={4}>推荐结果</Title>
          <List
            dataSource={recommendations}
            renderItem={(item, index) => (
              <List.Item>
                <List.Item.Meta
                  title={
                    <Space>
                      <Text strong>{item.song?.title || `推荐 ${index + 1}`}</Text>
                      <Tag color="blue">相似度: {(item.similarity * 100).toFixed(1)}%</Tag>
                    </Space>
                  }
                  description={
                    <div>
                      <Paragraph>
                        <Text type="secondary">歌手：</Text>
                        {item.song?.artist || '未知'}
                      </Paragraph>
                      <Paragraph>
                        <Text type="secondary">推荐理由：</Text>
                        {item.explanation || '基于歌词内容的综合相似度推荐'}
                      </Paragraph>
                      {item.song?.external_links && (
                        <div style={{ marginTop: 8, marginBottom: 8 }}>
                          <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
                            在线播放（点击下方链接在对应平台播放）：
                          </Text>
                          <Space wrap>
                            {item.song.external_links.qq_music && (
                              <Button
                                type="primary"
                                size="small"
                                onClick={() => window.open(item.song.external_links.qq_music, '_blank')}
                              >
                                🎵 QQ音乐
                              </Button>
                            )}
                            {item.song.external_links.netease && (
                              <Button
                                size="small"
                                onClick={() => window.open(item.song.external_links.netease, '_blank')}
                              >
                                🎵 网易云
                              </Button>
                            )}
                            {item.song.external_links.kugou && (
                              <Button
                                size="small"
                                onClick={() => window.open(item.song.external_links.kugou, '_blank')}
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
                      {item.song?.lyrics && (
                        <div style={{ marginTop: 8 }}>
                          <Button
                            type="link"
                            size="small"
                            onClick={() => {
                              setExpandedLyrics(prev => ({
                                ...prev,
                                [index]: !prev[index]
                              }));
                            }}
                          >
                            {expandedLyrics[index] ? '收起歌词' : '展开歌词'}
                          </Button>
                          {expandedLyrics[index] && (
                            <Card size="small" style={{ marginTop: 8, background: '#f5f5f5' }}>
                              <Text type="secondary" style={{ fontSize: 12, whiteSpace: 'pre-line' }}>
                                {item.song.lyrics.split('\n')
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
                          )}
                        </div>
                      )}
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        </Card>
      )}

      {recommendations.length === 0 && !loading && (
        <Card style={{ marginTop: 24 }}>
          <Empty description="暂无推荐结果，请输入歌词进行推荐" />
        </Card>
      )}
    </div>
  );
};

export default RecommendationPage;



