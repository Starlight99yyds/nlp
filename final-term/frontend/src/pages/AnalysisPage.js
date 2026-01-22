import React, { useState, useMemo, useCallback } from 'react';
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
  Tag
} from 'antd';
import { analysisAPI } from '../services/api';
import ReactECharts from 'echarts-for-react';
// import WordCloud from 'react-wordcloud'; // 如果安装有问题，可以注释掉

const { TextArea } = Input;
const { Title, Paragraph } = Typography;

const AnalysisPage = () => {
  const { Text } = Typography;
  // 从localStorage恢复保存的内容
  const [lyrics, setLyrics] = useState(() => {
    const saved = localStorage.getItem('analysis_lyrics');
    return saved || '';
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(() => {
    const saved = localStorage.getItem('analysis_result');
    return saved ? JSON.parse(saved) : null;
  });

  // 保存歌词到localStorage（使用 useCallback 优化）
  const handleLyricsChange = useCallback((value) => {
    setLyrics(value);
    // 使用防抖减少 localStorage 写入频率
    if (handleLyricsChange.timeout) {
      clearTimeout(handleLyricsChange.timeout);
    }
    handleLyricsChange.timeout = setTimeout(() => {
      localStorage.setItem('analysis_lyrics', value);
    }, 300);
  }, []);

  const handleAnalyze = useCallback(async () => {
    if (!lyrics.trim()) {
      message.warning('请输入歌词');
      return;
    }

    setLoading(true);
    try {
      const response = await analysisAPI.analyze(lyrics);
      if (response.data.success) {
        const resultData = response.data.data;
        setResult(resultData);
        // 保存结果到localStorage
        localStorage.setItem('analysis_result', JSON.stringify(resultData));
        message.success('分析完成！');
      }
    } catch (error) {
      message.error('分析失败：' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  }, [lyrics]);

  const getSentimentChartOption = useMemo(() => {
    if (!result?.sentiment?.timeline || !Array.isArray(result.sentiment.timeline) || result.sentiment.timeline.length === 0) {
      return {
        title: { text: '情感变化曲线', left: 'center' },
        xAxis: { type: 'category', data: [] },
        yAxis: { type: 'value', min: 0, max: 1 },
        series: [{ data: [], type: 'line' }]
      };
    }

    return {
      title: { text: '情感变化曲线', left: 'center' },
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: result.sentiment.timeline.map((_, i) => `第${i + 1}句`)
      },
      yAxis: { type: 'value', min: 0, max: 1 },
      series: [{
        data: result.sentiment.timeline.map(t => t.score || 0),
        type: 'line',
        smooth: true,
        areaStyle: {},
        itemStyle: { color: '#1890ff' }
      }]
    };
  }, [result]);

  const getSentimentDistributionOption = useMemo(() => {
    // 优先使用emotion_distribution，如果没有则从sentence_analyses中统计
    let emotionData = {};
    
    if (result?.sentiment?.emotion_distribution && Object.keys(result.sentiment.emotion_distribution).length > 0) {
      // 使用emotion_distribution
      emotionData = result.sentiment.emotion_distribution;
    } else if (result?.sentiment?.sentence_analyses && result.sentiment.sentence_analyses.length > 0) {
      // 从sentence_analyses中统计情感类型（只使用中文情感类型）
      const analyses = result.sentiment.sentence_analyses;
      emotionData = {};
      analyses.forEach(analysis => {
        let emotion = analysis.emotion_type || analysis.category || '未知';
        // 将英文情感类型转换为中文
        const emotionTranslations = {
          'positive': '积极', 'negative': '消极', 'neutral': '中性',
          'melancholic': '忧郁', 'joyful': '快乐', 'romantic': '浪漫',
          'lonely': '孤独', 'hopeful': '希望', 'nostalgic': '怀旧',
          'sad': '悲伤', 'happy': '快乐', 'angry': '愤怒',
          'peaceful': '平和', 'excited': '兴奋', 'calm': '平静'
        };
        emotion = emotionTranslations[emotion] || emotion;
        // 只保留中文情感类型，过滤掉英文
        if (/^[\u4e00-\u9fa5]+$/.test(emotion) || emotion === '未知') {
          emotionData[emotion] = (emotionData[emotion] || 0) + 1;
        }
      });
    } else if (result?.sentiment?.overall_tone) {
      // 如果只有overall_tone，根据它生成分布
      const tone = result.sentiment.overall_tone;
      // 解析复合情感（如"忧郁、失望、希望交织"）
      const emotions = tone.split(/[、，,]/).map(e => e.trim()).filter(e => e && /^[\u4e00-\u9fa5]+/.test(e));
      if (emotions.length > 0) {
        // 根据情感在overall_tone中的位置分配权重（前面的情感权重更大）
        // 这样占比就不会完全相等
        emotions.forEach((emotion, index) => {
          const weight = emotions.length - index; // 前面的情感权重更大
          emotionData[emotion] = weight;
        });
      } else {
        emotionData[tone] = 1;
      }
    }
    
    // 如果没有数据，显示默认
    if (Object.keys(emotionData).length === 0) {
      return {
        title: { text: '情感分布', left: 'center' },
        tooltip: { trigger: 'item' },
        series: [{
          type: 'pie',
          radius: ['40%', '70%'],
          data: [
            { value: 1, name: '暂无数据', itemStyle: { color: '#d9d9d9' } }
          ]
        }]
      };
    }
    
    // 丰富的颜色调色板（确保每个情感都有不同颜色）
    const colorPalette = [
      '#722ed1', // 紫色 - 忧郁
      '#595959', // 深灰 - 失望
      '#52c41a', // 绿色 - 希望
      '#faad14', // 橙色 - 快乐
      '#eb2f96', // 粉色 - 浪漫
      '#1890ff', // 蓝色 - 孤独
      '#13c2c2', // 青色 - 怀旧
      '#ff4d4f', // 红色 - 悲伤
      '#fa8c16', // 橙红 - 热情
      '#2f54eb', // 深蓝 - 深沉
      '#a0d911', // 黄绿 - 活力
      '#f759ab', // 粉红 - 温柔
      '#9254de', // 紫蓝 - 神秘
      '#36cfc9', // 青绿 - 清新
      '#ff7a45', // 橙黄 - 温暖
      '#b37feb', // 淡紫 - 优雅
      '#ff85c0', // 粉紫 - 甜美
      '#5cdbd3', // 青蓝 - 宁静
      '#ffc53d', // 金黄 - 明亮
      '#ff9c6e', // 珊瑚 - 柔和
      '#95de64', // 浅绿 - 生机
      '#ffd666', // 浅黄 - 阳光
      '#bae637', // 草绿 - 自然
      '#73d13d', // 翠绿 - 活力
      '#40a9ff', // 天蓝 - 自由
      '#597ef7', // 靛蓝 - 深邃
      '#d3adf7', // 淡紫 - 梦幻
      '#ffadd2', // 粉红 - 可爱
      '#87e8de', // 浅青 - 清新
      '#ffd591', // 浅橙 - 温暖
    ];
    
    // 情感颜色映射（优先使用）
    const emotionColorMap = {
      '忧郁': '#722ed1', '忧郁悲伤': '#722ed1',
      '失望': '#595959', '失望沮丧': '#595959',
      '希望': '#52c41a', '希望期待': '#52c41a',
      '快乐': '#faad14', '快乐喜悦': '#faad14',
      '浪漫': '#eb2f96', '浪漫温柔': '#eb2f96',
      '孤独': '#1890ff', '孤独寂寞': '#1890ff',
      '怀旧': '#13c2c2', '怀旧思念': '#13c2c2',
      '悲伤': '#ff4d4f', '痛苦': '#ff4d4f',
      '期待': '#52c41a', '憧憬': '#52c41a',
      '向往': '#36cfc9', '思念': '#13c2c2',
      '低沉': '#2f54eb', '感伤': '#722ed1',
      '失落': '#595959', '空虚': '#1890ff',
      '落寞': '#2f54eb', '回忆': '#13c2c2',
      '怀念': '#b37feb', '温馨怀旧': '#ff85c0',
      '甜蜜': '#ffadd2', '愉悦': '#faad14',
      '欢快': '#ffc53d', '开心': '#ffd666',
      '向上': '#73d13d', '乐观': '#95de64',
      '阳光': '#ffd666', '平和': '#5cdbd3',
      '平静': '#87e8de', '淡然': '#40a9ff',
      '温柔': '#ffadd2', '温馨': '#ff85c0',
      '深沉': '#2f54eb', '神秘': '#9254de',
      '优雅': '#b37feb', '梦幻': '#d3adf7',
      '甜美': '#ffadd2', '可爱': '#ffadd2',
      '清新': '#87e8de', '宁静': '#5cdbd3',
      '明亮': '#ffc53d', '柔和': '#ff9c6e',
      '生机': '#95de64', '自然': '#bae637',
      '活力': '#73d13d', '自由': '#40a9ff',
      '深邃': '#597ef7', '温暖': '#ffd591',
      '热情': '#fa8c16', '痛苦悲伤': '#ff4d4f',
      '沮丧': '#595959', '悲观': '#2f54eb',
    };
    
    // 已使用的颜色集合（确保每个情感都有不同颜色）
    const usedColors = new Set();
    const emotionColorAssignments = {}; // 记录每个情感分配的颜色
    
    // 转换为图表数据格式，过滤掉英文和积极/消极/中性
    // 优先支持2字的情感词语，也支持3-4字
    const data = Object.entries(emotionData)
      .filter(([emotion, value]) => {
        // 只保留中文情感类型（优先2字，也支持3-4字）
        const isChinese = /^[\u4e00-\u9fa5]+$/.test(emotion);
        const isValidLength = emotion.length >= 2 && emotion.length <= 4;
        // 过滤掉简单的积极/消极/中性
        const isSimple = ['积极', '消极', '中性', 'positive', 'negative', 'neutral'].includes(emotion);
        return isChinese && isValidLength && !isSimple && value > 0;
      })
      .sort((a, b) => {
        // 优先排序：2字词语在前，然后按值降序
        if (a[0].length === 2 && b[0].length !== 2) return -1;
        if (a[0].length !== 2 && b[0].length === 2) return 1;
        return b[1] - a[1];
      })
      .map(([emotion, value], index) => {
        // 优先使用映射表中的颜色（如果该颜色未被使用）
        let color = emotionColorMap[emotion];
        
        // 如果映射表中的颜色已被使用，则从未使用的调色板中选择
        if (color && usedColors.has(color)) {
          color = null; // 标记为需要重新分配
        }
        
        // 如果映射表中没有或颜色已被使用，从未使用的调色板中选择
        if (!color) {
          // 找到第一个未使用的颜色
          for (const paletteColor of colorPalette) {
            if (!usedColors.has(paletteColor)) {
              color = paletteColor;
              usedColors.add(paletteColor);
              emotionColorAssignments[emotion] = color;
              break;
            }
          }
          // 如果所有颜色都用完了，使用索引循环选择，但确保不重复
          if (!color) {
            // 从调色板中选择，跳过已使用的颜色
            let colorIndex = index;
            while (usedColors.has(colorPalette[colorIndex % colorPalette.length])) {
              colorIndex++;
              if (colorIndex > index + colorPalette.length) {
                // 如果所有颜色都用完了，使用哈希函数生成唯一颜色
                const hash = emotion.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
                color = colorPalette[hash % colorPalette.length];
                break;
              }
            }
            if (!color) {
              color = colorPalette[colorIndex % colorPalette.length];
            }
            usedColors.add(color);
            emotionColorAssignments[emotion] = color;
          }
        } else {
          // 如果颜色已经在映射表中且未被使用，标记为已使用
          usedColors.add(color);
          emotionColorAssignments[emotion] = color;
        }
        
        return {
          value: value,
          name: emotion,
          itemStyle: { 
            color: color,
            borderColor: '#fff',
            borderWidth: 2
          },
          emphasis: {
            itemStyle: { 
              color: color,
              opacity: 0.9,
              shadowBlur: 10,
              shadowColor: color
            }
          }
        };
      })
      .sort((a, b) => b.value - a.value); // 按值排序
    
    // 如果过滤后没有数据，使用overall_tone生成
    if (data.length === 0 && result?.sentiment?.overall_tone) {
      const tone = result.sentiment.overall_tone;
      const emotions = tone.split(/[、，,]/).map(e => e.trim()).filter(e => e && /^[\u4e00-\u9fa5]+/.test(e));
      
      // 如果有sentence_analyses，根据实际句子分析来计算每个情感的数量
      if (result?.sentiment?.sentence_analyses && result.sentiment.sentence_analyses.length > 0) {
        const analyses = result.sentiment.sentence_analyses;
        const emotionCounts = {};
        
        // 统计每个情感在句子分析中出现的次数
        analyses.forEach(analysis => {
          let emotion = analysis.emotion_type || analysis.category || '';
          // 将英文情感类型转换为中文
          const emotionTranslations = {
            'positive': '积极', 'negative': '消极', 'neutral': '中性',
            'melancholic': '忧郁', 'joyful': '快乐', 'romantic': '浪漫',
            'lonely': '孤独', 'hopeful': '希望', 'nostalgic': '怀旧',
            'sad': '悲伤', 'happy': '快乐', 'angry': '愤怒',
            'peaceful': '平和', 'excited': '兴奋', 'calm': '平静'
          };
          emotion = emotionTranslations[emotion] || emotion;
          
          // 如果这个情感在overall_tone的情感列表中，则计数
          if (emotions.includes(emotion)) {
            emotionCounts[emotion] = (emotionCounts[emotion] || 0) + 1;
          }
        });
        
        // 如果统计到了数据，使用统计结果
        if (Object.keys(emotionCounts).length > 0) {
          Object.entries(emotionCounts).forEach(([emotion, count], index) => {
            if (!['积极', '消极', '中性'].includes(emotion)) {
              // 确保每个情感都有不同的颜色
              let color = emotionColorMap[emotion];
              if (!color || usedColors.has(color)) {
                // 如果颜色已被使用，从未使用的调色板中选择
                for (const paletteColor of colorPalette) {
                  if (!usedColors.has(paletteColor)) {
                    color = paletteColor;
                    usedColors.add(paletteColor);
                    break;
                  }
                }
                // 如果所有颜色都用完了，使用索引循环
                if (!color || usedColors.has(color)) {
                  color = colorPalette[index % colorPalette.length];
                }
              }
              usedColors.add(color);
              data.push({
                value: count,
                name: emotion,
                itemStyle: { 
                  color: color,
                  borderColor: '#fff',
                  borderWidth: 2
                },
                emphasis: { 
                  itemStyle: { 
                    color: color, 
                    opacity: 0.9,
                    shadowBlur: 10,
                    shadowColor: color
                  } 
                }
              });
            }
          });
        } else {
          // 如果没有统计到数据，根据情感在overall_tone中的位置分配权重
          // 前面的情感权重更大
          emotions.forEach((emotion, index) => {
            if (!['积极', '消极', '中性'].includes(emotion)) {
              const weight = emotions.length - index; // 前面的情感权重更大
              // 确保每个情感都有不同的颜色
              let color = emotionColorMap[emotion];
              if (!color || usedColors.has(color)) {
                // 如果颜色已被使用，从未使用的调色板中选择
                for (const paletteColor of colorPalette) {
                  if (!usedColors.has(paletteColor)) {
                    color = paletteColor;
                    usedColors.add(paletteColor);
                    break;
                  }
                }
                // 如果所有颜色都用完了，使用索引循环
                if (!color || usedColors.has(color)) {
                  color = colorPalette[index % colorPalette.length];
                }
              }
              usedColors.add(color);
              data.push({
                value: weight,
                name: emotion,
                itemStyle: { 
                  color: color,
                  borderColor: '#fff',
                  borderWidth: 2
                },
                emphasis: { 
                  itemStyle: { 
                    color: color, 
                    opacity: 0.9,
                    shadowBlur: 10,
                    shadowColor: color
                  } 
                }
              });
            }
          });
        }
      } else {
        // 如果没有sentence_analyses，根据情感在overall_tone中的位置分配权重
        // 前面的情感权重更大
        emotions.forEach((emotion, index) => {
          if (!['积极', '消极', '中性'].includes(emotion)) {
            const weight = emotions.length - index; // 前面的情感权重更大
            // 确保每个情感都有不同的颜色
            let color = emotionColorMap[emotion];
            if (!color || usedColors.has(color)) {
              // 如果颜色已被使用，从未使用的调色板中选择
              for (const paletteColor of colorPalette) {
                if (!usedColors.has(paletteColor)) {
                  color = paletteColor;
                  usedColors.add(paletteColor);
                  break;
                }
              }
              // 如果所有颜色都用完了，使用索引循环
              if (!color || usedColors.has(color)) {
                color = colorPalette[index % colorPalette.length];
              }
            }
            usedColors.add(color);
            data.push({
              value: weight,
              name: emotion,
              itemStyle: { 
                color: color,
                borderColor: '#fff',
                borderWidth: 2
              },
              emphasis: { 
                itemStyle: { 
                  color: color, 
                  opacity: 0.9,
                  shadowBlur: 10,
                  shadowColor: color
                } 
              }
            });
          }
        });
      }
    }
    
    return {
      title: { 
        text: '情感分布', 
        left: 'center',
        textStyle: {
          fontSize: 16,
          fontWeight: 'bold'
        }
      },
      tooltip: { 
        trigger: 'item',
        formatter: (params) => {
          return `${params.name}: ${params.percent}%`;
        },
        backgroundColor: 'rgba(50, 50, 50, 0.9)',
        borderColor: '#fff',
        borderWidth: 1,
        textStyle: {
          color: '#fff',
          fontSize: 14
        },
        padding: [10, 15]
      },
      series: [{
        name: '情感分布',
        type: 'pie',
        radius: ['40%', '70%'], // 环形图，内半径和外半径
        center: ['50%', '50%'],
        avoidLabelOverlap: true,
        data: data,
        emphasis: {
          itemStyle: {
            shadowBlur: 20,
            shadowOffsetX: 0,
            shadowOffsetY: 0,
            shadowColor: 'rgba(0, 0, 0, 0.8)'
          },
          scale: true, // 鼠标悬停时放大
          scaleSize: 15, // 放大尺寸（像素）
          focus: 'self' // 只高亮当前扇形
        },
        label: {
          show: true,
          formatter: (params) => {
            // 优先显示2字词语，3-4字词语使用更小的字体
            const fontSize = params.name.length === 2 ? 13 : 11;
            return `{name|${params.name}}\n{percent|${params.percent}%}`;
          },
          rich: {
            name: {
              fontSize: 13,
              fontWeight: 'bold',
              color: '#333',
              lineHeight: 18
            },
            percent: {
              fontSize: 11,
              color: '#666',
              lineHeight: 16
            }
          },
          color: '#333'
        },
        labelLine: {
          show: true,
          length: 15,
          length2: 10,
          lineStyle: {
            width: 1
          }
        },
        animationType: 'scale', // 动画类型：缩放
        animationEasing: 'elasticOut', // 弹性动画
        animationDuration: 1000, // 动画时长
        itemStyle: {
          borderRadius: 8, // 圆角
          borderColor: '#fff',
          borderWidth: 2
        }
      }]
    };
  }, [result]);

  const getWordCloudData = useMemo(() => {
    if (!result?.theme?.wordcloud_data) return [];
    return result.theme.wordcloud_data.map(item => ({
      text: item.word,
      value: item.size
    }));
  }, [result]);

  return (
    <div className="page-container">
      <Title level={2} className="page-title">基础分析</Title>

      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={4}>输入歌词</Title>
            <TextArea
              rows={8}
              placeholder="请输入要分析的歌词..."
              value={lyrics}
              onChange={(e) => handleLyricsChange(e.target.value)}
            />
          </div>
          <Space style={{ width: '100%' }} direction="vertical">
            <Button
              type="primary"
              size="large"
              onClick={handleAnalyze}
              loading={loading}
              block
            >
              开始分析
            </Button>
            <Button
              onClick={() => {
                setLyrics('');
                setResult(null);
                // 清空相关的localStorage
                localStorage.removeItem('analysis_lyrics');
                localStorage.removeItem('analysis_result');
                message.info('已重置所有输入');
              }}
              block
            >
              重置
            </Button>
          </Space>
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
                            <strong>情感基调：</strong>
                            <div style={{ marginTop: 8, marginBottom: 16 }}>
                              {(() => {
                                // 优先从emotion_distribution或emotion_summary中提取2字词语
                                let emotionWords = [];
                                
                                // 方法1: 如果有emotion_summary，解析它
                                if (result.sentiment.emotion_summary) {
                                  const summaryWords = result.sentiment.emotion_summary.split(/[、，,]/).map(w => w.trim()).filter(w => w && /^[\u4e00-\u9fa5]{2,4}$/.test(w));
                                  if (summaryWords.length > 0) {
                                    emotionWords = summaryWords;
                                  }
                                }
                                
                                // 方法2: 如果没有emotion_summary，从emotion_distribution中提取
                                if (emotionWords.length === 0 && result.sentiment.emotion_distribution) {
                                  emotionWords = Object.keys(result.sentiment.emotion_distribution)
                                    .filter(word => /^[\u4e00-\u9fa5]{2,4}$/.test(word))
                                    .sort((a, b) => (result.sentiment.emotion_distribution[b] || 0) - (result.sentiment.emotion_distribution[a] || 0))
                                    .slice(0, 6); // 最多显示6个词语
                                }
                                
                                // 方法3: 如果都没有，尝试从overall_tone中解析（去除连接词）
                                if (emotionWords.length === 0 && result.sentiment.overall_tone) {
                                  const tone = result.sentiment.overall_tone;
                                  // 移除常见的连接词：与、和、及、以及、交织、带着、透着、中、的、等
                                  const cleanedTone = tone.replace(/(与|和|及|以及|交织|带着|透着|中|的|等)/g, '、');
                                  emotionWords = cleanedTone.split(/[、，,]/)
                                    .map(w => w.trim())
                                    .filter(w => w && /^[\u4e00-\u9fa5]{2,4}$/.test(w))
                                    .slice(0, 6);
                                }
                                
                                // 如果还是没有，显示原始文本
                                if (emotionWords.length === 0) {
                                  return <Text>{result.sentiment.overall_tone || '未知'}</Text>;
                                }
                                
                                // 以标签形式分散显示词语
                                return (
                                  <Space wrap>
                                    {emotionWords.map((word, index) => (
                                      <Tag 
                                        key={index} 
                                        color={index === 0 ? 'red' : index === 1 ? 'orange' : 'blue'}
                                        style={{ 
                                          margin: '4px',
                                          fontSize: '14px',
                                          padding: '4px 12px',
                                          borderRadius: '4px'
                                        }}
                                      >
                                        {word}
                                      </Tag>
                                    ))}
                                  </Space>
                                );
                              })()}
                            </div>
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
                          option={getSentimentDistributionOption}
                          style={{ height: 300 }}
                        />
                      </Col>
                    </Row>
                    <Card style={{ marginTop: 16 }}>
                      <ReactECharts
                        option={getSentimentChartOption}
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
                      {getWordCloudData.length > 0 ? (
                        <div style={{ padding: 20 }}>
                          {getWordCloudData.slice(0, 20).map((item, i) => (
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

