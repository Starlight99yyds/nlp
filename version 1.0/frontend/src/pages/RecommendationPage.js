import React, { useState } from 'react';
import {
  Card,
  Input,
  Button,
  Space,
  Typography,
  Row,
  Col,
  List,
  Tag,
  message,
  Divider,
  Empty
} from 'antd';
import { recommendationAPI } from '../services/api';

const { TextArea } = Input;
const { Title, Paragraph } = Typography;

const RecommendationPage = () => {
  const { Text } = Typography;
  const [lyrics, setLyrics] = useState('');
  const [loading, setLoading] = useState(false);
  const [recommendations, setRecommendations] = useState([]);

  const handleRecommend = async () => {
    if (!lyrics.trim()) {
      message.warning('请输入歌词');
      return;
    }

    setLoading(true);
    try {
      const response = await recommendationAPI.recommend(lyrics, 5);
      if (response.data.success) {
        setRecommendations(response.data.data.recommendations || []);
        message.success('推荐完成！');
      }
    } catch (error) {
      message.error('推荐失败：' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <Title level={2} className="page-title">🎯 智能推荐</Title>

      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={4}>输入歌词</Title>
            <TextArea
              rows={6}
              placeholder="请输入歌词，系统将为您推荐相似的歌曲..."
              value={lyrics}
              onChange={(e) => setLyrics(e.target.value)}
            />
          </div>
          <Button
            type="primary"
            size="large"
            onClick={handleRecommend}
            loading={loading}
            block
          >
            获取推荐
          </Button>
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
                      {item.song?.lyrics && (
                        <Card size="small" style={{ marginTop: 8, background: '#f5f5f5' }}>
                          <Text type="secondary" style={{ fontSize: 12, whiteSpace: 'pre-line' }}>
                            {item.song.lyrics.split('\n')
                              .filter(line => {
                                // 过滤掉时间戳行，如 [00:00.000]
                                const timePattern = /^\[\d{2}:\d{2}\.\d{3}\]/;
                                // 过滤掉元信息行，如 [00:00.000] 作词 : xxx
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



