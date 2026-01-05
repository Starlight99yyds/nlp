import React, { useState } from 'react';
import {
  Card,
  Input,
  Button,
  Space,
  Typography,
  Row,
  Col,
  Tabs,
  Spin,
  message,
  Divider,
  Tag
} from 'antd';
import { analysisAPI } from '../services/api';
import ReactECharts from 'echarts-for-react';
// import WordCloud from 'react-wordcloud'; // 如果安装有问题，可以注释掉

const { TextArea } = Input;
const { Title, Paragraph } = Typography;

const AnalysisPage = () => {
  const { Text } = Typography;
  const [lyrics, setLyrics] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleAnalyze = async () => {
    if (!lyrics.trim()) {
      message.warning('请输入歌词');
      return;
    }

    setLoading(true);
    try {
      const response = await analysisAPI.analyze(lyrics);
      if (response.data.success) {
        setResult(response.data.data);
        message.success('分析完成！');
      }
    } catch (error) {
      message.error('分析失败：' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  const getSentimentChartOption = () => {
    if (!result?.sentiment?.timeline) return {};

    return {
      title: { text: '情感变化曲线', left: 'center' },
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: result.sentiment.timeline.map((_, i) => `第${i + 1}句`)
      },
      yAxis: { type: 'value', min: 0, max: 1 },
      series: [{
        data: result.sentiment.timeline.map(t => t.score),
        type: 'line',
        smooth: true,
        areaStyle: {},
        itemStyle: { color: '#1890ff' }
      }]
    };
  };

  const getSentimentDistributionOption = () => {
    if (!result?.sentiment?.category_distribution) return {};

    const dist = result.sentiment.category_distribution;
    return {
      title: { text: '情感分布', left: 'center' },
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie',
        radius: '60%',
        data: [
          { value: dist.positive, name: '积极' },
          { value: dist.negative, name: '消极' },
          { value: dist.neutral, name: '中性' }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    };
  };

  const getWordCloudData = () => {
    if (!result?.theme?.wordcloud_data) return [];
    return result.theme.wordcloud_data.map(item => ({
      text: item.word,
      value: item.size
    }));
  };

  return (
    <div className="page-container">
      <Title level={2} className="page-title">📊 基础分析</Title>

      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={4}>输入歌词</Title>
            <TextArea
              rows={8}
              placeholder="请输入要分析的歌词..."
              value={lyrics}
              onChange={(e) => setLyrics(e.target.value)}
            />
          </div>
          <Button
            type="primary"
            size="large"
            onClick={handleAnalyze}
            loading={loading}
            block
          >
            开始分析
          </Button>
        </Space>
      </Card>

      {loading && (
        <Card style={{ marginTop: 24, textAlign: 'center' }}>
          <Spin size="large" />
          <Paragraph>正在分析中...</Paragraph>
        </Card>
      )}

      {result && !loading && (
        <>
          <Card style={{ marginTop: 24 }}>
            <Title level={4}>分析摘要</Title>
            <Paragraph>{result.summary}</Paragraph>
          </Card>

          <Tabs
            defaultActiveKey="sentiment"
            items={[
              {
                key: 'sentiment',
                label: '情感分析',
                children: (
                  <div>
                    <Row gutter={[16, 16]}>
                      <Col xs={24} md={12}>
                        <Card>
                          <Title level={5}>整体情感</Title>
                          <Paragraph>
                            <strong>情感基调：</strong>{result.sentiment.overall_tone}
                            <br />
                            <strong>情感得分：</strong>{result.sentiment.overall_score.toFixed(2)}
                            {result.sentiment.score_explanation && (
                              <>
                                <br />
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                  {result.sentiment.score_explanation}
                                </Text>
                              </>
                            )}
                            {result.sentiment.emotion_distribution && (
                              <>
                                <br />
                                <br />
                                <strong>情感分布：</strong>
                                <div style={{ marginTop: 8 }}>
                                  {Object.entries(result.sentiment.emotion_distribution)
                                    .sort((a, b) => b[1] - a[1])
                                    .map(([emotion, count]) => (
                                    <Tag key={emotion} color="blue" style={{ margin: '4px' }}>
                                      {emotion}: {count}句
                                    </Tag>
                                  ))}
                                </div>
                              </>
                            )}
                          </Paragraph>
                        </Card>
                      </Col>
                      <Col xs={24} md={12}>
                        <ReactECharts
                          option={getSentimentDistributionOption()}
                          style={{ height: 300 }}
                        />
                      </Col>
                    </Row>
                    <Card style={{ marginTop: 16 }}>
                      <ReactECharts
                        option={getSentimentChartOption()}
                        style={{ height: 300 }}
                      />
                    </Card>
                  </div>
                )
              },
              {
                key: 'theme',
                label: '主题分析',
                children: (
                  <div>
                    <Row gutter={[16, 16]}>
                      <Col xs={24} md={12}>
                        <Card>
                          <Title level={5}>主题分析</Title>
                          {result.theme.themes && result.theme.themes.length > 0 ? (
                            result.theme.themes.map((theme, i) => (
                              <div key={i} style={{ marginBottom: 12 }}>
                                <Space>
                                  <Tag color={i === 0 ? 'red' : i === 1 ? 'orange' : 'blue'}>
                                    {i + 1}
                                  </Tag>
                                  <Text strong>{theme.theme}</Text>
                                  <Text type="secondary">匹配度: {theme.score}</Text>
                                </Space>
                              </div>
                            ))
                          ) : (
                            <Text type="secondary">未检测到明确主题</Text>
                          )}
                        </Card>
                      </Col>
                      <Col xs={24} md={12}>
                        <Card>
                          <Title level={5}>关键词</Title>
                          <Space wrap>
                            {result.theme.keywords?.slice(0, 10).map((kw, i) => (
                              <Button key={i} size="small">
                                {kw.word}
                              </Button>
                            ))}
                          </Space>
                        </Card>
                      </Col>
                    </Row>
                    <Card style={{ marginTop: 16, minHeight: 300 }}>
                      <Title level={5}>词云图</Title>
                      {getWordCloudData().length > 0 ? (
                        <div style={{ padding: 20 }}>
                          {getWordCloudData().slice(0, 20).map((item, i) => (
                            <span
                              key={i}
                              style={{
                                fontSize: `${Math.max(12, item.value / 2)}px`,
                                margin: '4px',
                                display: 'inline-block',
                                color: '#1890ff'
                              }}
                            >
                              {item.text}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <div>暂无词云数据</div>
                      )}
                    </Card>
                  </div>
                )
              },
              {
                key: 'rhythm',
                label: '韵律分析',
                children: (
                  <div>
                    <Row gutter={[16, 16]}>
                      <Col xs={24} md={12}>
                        <Card>
                          <Title level={5}>押韵模式</Title>
                          <Paragraph>
                            <strong>模式：</strong>{result.rhythm.rhyme_pattern.pattern}
                            <br />
                            <strong>质量评分：</strong>{result.rhythm.rhyme_pattern.quality_score}
                            <br />
                            <strong>押韵对数：</strong>{result.rhythm.rhyme_pattern.rhyme_count}
                          </Paragraph>
                        </Card>
                      </Col>
                      <Col xs={24} md={12}>
                        <Card>
                          <Title level={5}>节奏分析</Title>
                          <Paragraph>
                            <strong>平均音节数：</strong>{result.rhythm.syllable_analysis.avg_syllables}
                            <br />
                            <strong>节奏一致性：</strong>{result.rhythm.syllable_analysis.rhythm_consistency}
                          </Paragraph>
                        </Card>
                      </Col>
                    </Row>
                  </div>
                )
              }
            ]}
          />
        </>
      )}
    </div>
  );
};

export default AnalysisPage;

