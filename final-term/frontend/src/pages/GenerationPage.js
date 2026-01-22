import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Input,
  Button,
  Space,
  Typography,
  Row,
  Col,
  Select,
  Tabs,
  message,
  Tag,
  Switch,
  Modal,
  List,
  Progress,
  Alert
} from 'antd';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { generationAPI } from '../services/api';

const { TextArea } = Input;
const { Title, Paragraph } = Typography;
const { Option } = Select;

const GenerationPage = () => {
  const { Text } = Typography;
  const [activeTab, setActiveTab] = useState('generate');
  const [generationHistory, setGenerationHistory] = useState([]);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // 使用ref来跟踪组件是否已卸载，以及当前请求
  const isMountedRef = useRef(true);
  
  // 统一的歌词生成参数 - 从localStorage恢复
  const [theme, setTheme] = useState(() => {
    try { return localStorage.getItem('generation_theme') || ''; } catch { return ''; }
  });
  const [useCustomTheme, setUseCustomTheme] = useState(() => {
    try { return localStorage.getItem('generation_useCustomTheme') === 'true'; } catch { return false; }
  });
  const [themeCustom, setThemeCustom] = useState(() => {
    try { return localStorage.getItem('generation_themeCustom') || ''; } catch { return ''; }
  });
  const [emotion, setEmotion] = useState(() => {
    try { return localStorage.getItem('generation_emotion') || ''; } catch { return ''; }
  });
  const [useEmotion, setUseEmotion] = useState(() => {
    try { return localStorage.getItem('generation_useEmotion') === 'true'; } catch { return false; }
  });
  const [style, setStyle] = useState(() => {
    try { return localStorage.getItem('generation_style') || ''; } catch { return ''; }
  });
  const [useCustomStyle, setUseCustomStyle] = useState(() => {
    try { return localStorage.getItem('generation_useCustomStyle') === 'true'; } catch { return false; }
  });
  const [styleCustom, setStyleCustom] = useState(() => {
    try { return localStorage.getItem('generation_styleCustom') || ''; } catch { return ''; }
  });
  const [context, setContext] = useState(() => {
    try { return localStorage.getItem('generation_context') || ''; } catch { return ''; }
  });
  const [useContext, setUseContext] = useState(() => {
    try { return localStorage.getItem('generation_useContext') === 'true'; } catch { return false; }
  });
  const [length, setLength] = useState(() => {
    try { 
      const saved = localStorage.getItem('generation_length');
      return saved ? parseInt(saved) : null; 
    } catch { return null; }
  });
  const [useCustomLength, setUseCustomLength] = useState(() => {
    try { return localStorage.getItem('generation_useCustomLength') === 'true'; } catch { return false; }
  });
  const [customLength, setCustomLength] = useState(() => {
    try { return parseInt(localStorage.getItem('generation_customLength')) || 16; } catch { return 16; }
  });
  const [userIdea, setUserIdea] = useState(() => {
    try { return localStorage.getItem('generation_userIdea') || ''; } catch { return ''; }
  });
  const [generateResult, setGenerateResult] = useState(() => {
    try {
      const saved = localStorage.getItem('generation_result');
      return saved ? JSON.parse(saved) : null;
    } catch { return null; }
  });

  // 风格转换 - 从localStorage恢复
  const [convertLyrics, setConvertLyrics] = useState(() => {
    try { return localStorage.getItem('generation_convertLyrics') || ''; } catch { return ''; }
  });
  const [targetStyle, setTargetStyle] = useState(() => {
    try { return localStorage.getItem('generation_targetStyle') || '流行'; } catch { return '流行'; }
  });
  const [convertResult, setConvertResult] = useState(() => {
    try {
      const saved = localStorage.getItem('generation_convertResult');
      return saved ? JSON.parse(saved) : null;
    } catch { return null; }
  });
  
  // 继续对话 - 从localStorage恢复
  const [conversationLyrics, setConversationLyrics] = useState(() => {
    try { return localStorage.getItem('generation_conversationLyrics') || ''; } catch { return ''; }
  });
  const [userFeedback, setUserFeedback] = useState(() => {
    try { return localStorage.getItem('generation_userFeedback') || ''; } catch { return ''; }
  });
  const [conversationResult, setConversationResult] = useState(() => {
    try {
      const saved = localStorage.getItem('generation_conversationResult');
      return saved ? JSON.parse(saved) : null;
    } catch { return null; }
  });

  // 歌曲生成 - 从localStorage恢复
  const [songLyrics, setSongLyrics] = useState(() => {
    try { return localStorage.getItem('generation_songLyrics') || ''; } catch { return ''; }
  });
  const [songTitle, setSongTitle] = useState(() => {
    try { return localStorage.getItem('generation_songTitle') || ''; } catch { return ''; }
  });
  const [songStyle, setSongStyle] = useState(() => {
    try { return localStorage.getItem('generation_songStyle') || '流行'; } catch { return '流行'; }
  });
  const [songTags, setSongTags] = useState(() => {
    try { return localStorage.getItem('generation_songTags') || ''; } catch { return ''; }
  });
  const [songVoice, setSongVoice] = useState(() => {
    try { return localStorage.getItem('generation_songVoice') || 'default'; } catch { return 'default'; }
  });
  const [makeInstrumental, setMakeInstrumental] = useState(() => {
    try { return localStorage.getItem('generation_makeInstrumental') === 'true'; } catch { return false; }
  });
  const [songAsyncMode, setSongAsyncMode] = useState(() => {
    try { return localStorage.getItem('generation_songAsyncMode') !== 'false'; } catch { return true; }
  });
  const [songResult, setSongResult] = useState(() => {
    try {
      const saved = localStorage.getItem('generation_songResult');
      return saved ? JSON.parse(saved) : null;
    } catch { return null; }
  });
  const [songTaskId, setSongTaskId] = useState(() => {
    try { return localStorage.getItem('generation_songTaskId') || null; } catch { return null; }
  });
  const [pollingInterval, setPollingInterval] = useState(null);
  const [songProgress, setSongProgress] = useState(10);

  // 加载历史记录
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const response = await generationAPI.getHistory(null, 50);
        if (response.data.success) {
          const allHistory = response.data.data || [];
          // 只保留歌词生成历史（排除歌曲生成）
          const lyricsHistory = allHistory.filter(item => 
            !item.prompt || !item.prompt.includes('歌曲生成')
          );
          setGenerationHistory(lyricsHistory);
        }
      } catch (error) {
        console.error('加载历史记录失败:', error);
      }
    };
    loadHistory();
  }, []);

  // 组件挂载时设置isMountedRef为true，并检查是否有正在进行的请求
  useEffect(() => {
    isMountedRef.current = true;
    
    // 检查是否有正在进行的请求（通过localStorage标记）
    const checkRequestStatus = () => {
      const isRequesting = localStorage.getItem('generation_requesting') === 'true';
      if (isRequesting) {
        setLoading(true);
        // 定期检查请求是否完成（通过检查localStorage中的结果）
        // 添加最大检查次数，防止无限循环
        let checkCount = 0;
        const maxChecks = 120; // 最多检查60秒（120次 * 500ms）
        const checkInterval = setInterval(() => {
          checkCount++;
          const savedResult = localStorage.getItem('generation_result');
          const stillRequesting = localStorage.getItem('generation_requesting') === 'true';
          
          // 如果超过最大检查次数，强制停止
          if (checkCount >= maxChecks) {
            clearInterval(checkInterval);
            if (isMountedRef.current) {
              setLoading(false);
              message.warning('请求超时，请刷新页面重试');
            }
            return;
          }
          
          if (!stillRequesting && savedResult) {
            // 请求已完成
            clearInterval(checkInterval);
            try {
              const result = JSON.parse(savedResult);
              if (isMountedRef.current) {
                setGenerateResult(result);
                setLoading(false);
                message.success('生成成功！');
              }
            } catch (e) {
              if (isMountedRef.current) {
                setLoading(false);
              }
            }
          }
        }, 500); // 每500ms检查一次
        
        // 清理定时器
        return () => {
          clearInterval(checkInterval);
        };
      } else {
        // 没有正在进行的请求，直接加载已保存的结果
        const savedResult = localStorage.getItem('generation_result');
        if (savedResult) {
          try {
            const result = JSON.parse(savedResult);
            if (result && isMountedRef.current) {
              setGenerateResult(result);
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

  const handleGenerate = async () => {
    setLoading(true);
    // 标记请求正在进行
    localStorage.setItem('generation_requesting', 'true');
    
    try {
      // 构建生成参数
      const finalTheme = useCustomTheme ? themeCustom : theme;
      const finalStyle = useCustomStyle ? styleCustom : style;
      const finalLength = useCustomLength ? customLength : length;
      const finalEmotion = useEmotion ? emotion : undefined;
      const contextLines = useContext && context.trim() ? context.split('\n').filter(l => l.trim()) : undefined;
      
      // 根据是否有上下文选择不同的生成方式
      let response;
      if (contextLines && contextLines.length > 0) {
        // 有上下文，使用上下文生成，传递所有用户自定义参数
        response = await generationAPI.generateByContext(
          contextLines, 
          finalEmotion, 
          finalLength,
          finalTheme,
          finalStyle,
          userIdea
        );
      } else if (finalTheme || finalStyle || userIdea) {
        // 有主题、风格或想法，使用完整生成
        response = await generationAPI.generateFullSong(
          finalStyle || '流行',
          finalTheme || '通用',
          finalEmotion,
          userIdea,
          finalLength,
          undefined
        );
      } else {
        // 只有主题，使用主题生成
        response = await generationAPI.generateByTheme(
          finalTheme || '通用',
          finalEmotion,
          finalLength,
          userIdea
        );
      }
      
      // 请求完成后，无论组件是否已卸载，都保存结果
      if (response.data.success) {
        const result = response.data.data;
        
        // 保存结果到localStorage（即使组件已卸载也会保存）
        localStorage.setItem('generation_result', JSON.stringify(result));
        localStorage.removeItem('generation_requesting');
        
        // 如果组件仍然挂载，更新状态
        if (isMountedRef.current) {
          setGenerateResult(result);
          setLoading(false);
          message.success('生成成功！');
        } else {
          // 组件已卸载，但结果已保存到localStorage，用户切换回来时会自动恢复
          console.log('生成完成，但组件已卸载，结果已保存到localStorage');
        }
      }
    } catch (error) {
      localStorage.removeItem('generation_requesting');
      
      // 如果组件仍然挂载，显示错误
      if (isMountedRef.current) {
        setLoading(false);
        // 检查是否是超时错误
        if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
          message.error('生成超时，请检查网络连接或稍后重试');
        } else {
          message.error('生成失败：' + (error.response?.data?.error || error.message || '未知错误'));
        }
      }
    }
  };

  const handleConvert = async () => {
    if (!convertLyrics.trim()) {
      message.warning('请输入歌词');
      return;
    }
    setLoading(true);
    try {
      const response = await generationAPI.convertStyle(convertLyrics, targetStyle);
      if (response.data.success) {
        setConvertResult(response.data.data);
        message.success('转换成功！');
      }
    } catch (error) {
      // 检查是否是超时错误
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        message.error('转换超时，请检查网络连接或稍后重试');
      } else {
        message.error('转换失败：' + (error.response?.data?.error || error.message || '未知错误'));
      }
    } finally {
      setLoading(false);
    }
  };
  
  const handleContinueConversation = async () => {
    if (!conversationLyrics.trim() || !userFeedback.trim()) {
      message.warning('请输入歌词和反馈');
      return;
    }
    setLoading(true);
    try {
      const response = await generationAPI.continueConversation(conversationLyrics, userFeedback);
      if (response.data.success) {
        setConversationResult(response.data.data);
        message.success('修改完成！');
      }
    } catch (error) {
      // 检查是否是超时错误
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        message.error('修改超时，请检查网络连接或稍后重试');
      } else {
        message.error('修改失败：' + (error.response?.data?.error || error.message || '未知错误'));
      }
    } finally {
      setLoading(false);
    }
  };

  // 歌曲生成处理
  const handleGenerateSong = async () => {
    if (!songLyrics.trim()) {
      message.warning('请输入歌词');
      return;
    }
    setLoading(true);
    try {
      const response = await generationAPI.generateSong(
        songLyrics,
        songTitle || undefined,
        songTags || undefined,
        songStyle,
        songVoice,
        makeInstrumental,
        songAsyncMode,
        300,
        undefined
      );
      
      if (response.data.success) {
        const result = response.data.data;
        setSongResult(result);
        
        if (songAsyncMode && result.task_id) {
          // 异步模式：开始轮询任务状态
          setSongTaskId(result.task_id);
          message.success('歌曲生成任务已提交，正在处理...');
          startPollingTaskStatus(result.task_id);
        } else {
          // 同步模式：直接显示结果
          message.success('歌曲生成完成！');
        }
      }
    } catch (error) {
      // 检查是否是超时错误
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        message.error('生成超时，请检查网络连接或稍后重试');
      } else {
        message.error('生成失败：' + (error.response?.data?.error || error.message || '未知错误'));
      }
    } finally {
      setLoading(false);
    }
  };

  // 开始轮询任务状态
  const startPollingTaskStatus = (taskId) => {
    // 清除之前的轮询
    if (pollingInterval) {
      clearInterval(pollingInterval);
    }
    
    // 初始化进度
    setSongProgress(10);
    let progressInterval = setInterval(() => {
      setSongProgress(prev => {
        if (prev >= 90) return prev; // 最多到90%，等待实际完成
        return prev + Math.random() * 5; // 每次增加0-5%
      });
    }, 2000); // 每2秒更新一次

    const poll = async () => {
      try {
        const response = await generationAPI.querySongStatus(taskId);
        if (response.data.success) {
          const statusData = response.data.data;
          
          if (statusData.status === 'success') {
            // 任务完成
            clearInterval(progressInterval);
            clearInterval(pollingInterval);
            setPollingInterval(null);
            setSongProgress(100);
            
            // 选择最好的音频
            const clips = statusData.clips || (Array.isArray(statusData) ? statusData : []);
            const completedClips = clips.filter(c => c.status === 'complete' && c.audio_url);
            const bestClip = completedClips.length > 0 
              ? completedClips.reduce((best, current) => 
                  (current.duration || 0) > (best.duration || 0) ? current : best
                )
              : clips.find(c => c.audio_url) || clips[0];
            
            setSongResult({
              status: 'completed',
              clips: clips,
              audio_url: bestClip?.audio_url,
              duration: bestClip?.duration,
              ...statusData
            });
            message.success('歌曲生成完成！');
          } else if (statusData.status === 'failed') {
            // 任务失败
            clearInterval(progressInterval);
            clearInterval(pollingInterval);
            setPollingInterval(null);
            message.error('歌曲生成失败');
          }
          // in_progress 状态继续轮询
        }
      } catch (error) {
        console.error('查询任务状态失败:', error);
      }
    };

    // 立即执行一次
    poll();
    // 每5秒轮询一次
    const interval = setInterval(poll, 5000);
    setPollingInterval(interval);
  };

  // 手动查询任务状态
  const handleQuerySongStatus = async () => {
    if (!songTaskId) {
      message.warning('没有任务ID');
      return;
    }
    setLoading(true);
    try {
      const response = await generationAPI.querySongStatus(songTaskId);
      if (response.data.success) {
        const statusData = response.data.data;
        setSongResult(statusData);
        message.success('状态已更新');
      }
    } catch (error) {
      message.error('查询失败：' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 组件卸载时清理轮询
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  // 保存所有状态到localStorage
  useEffect(() => {
    localStorage.setItem('generation_theme', theme);
    localStorage.setItem('generation_themeCustom', themeCustom);
    localStorage.setItem('generation_emotion', emotion);
    localStorage.setItem('generation_style', style);
    localStorage.setItem('generation_styleCustom', styleCustom);
    localStorage.setItem('generation_context', context);
    localStorage.setItem('generation_userIdea', userIdea);
    if (length !== null) {
      localStorage.setItem('generation_length', length.toString());
    } else {
      localStorage.removeItem('generation_length');
    }
    localStorage.setItem('generation_customLength', customLength.toString());
    localStorage.setItem('generation_useCustomTheme', useCustomTheme.toString());
    localStorage.setItem('generation_useEmotion', useEmotion.toString());
    localStorage.setItem('generation_useCustomStyle', useCustomStyle.toString());
    localStorage.setItem('generation_useContext', useContext.toString());
    localStorage.setItem('generation_useCustomLength', useCustomLength.toString());
    if (generateResult) {
      localStorage.setItem('generation_result', JSON.stringify(generateResult));
    }
  }, [theme, themeCustom, emotion, style, styleCustom, context, userIdea, length, customLength, 
      useCustomTheme, useEmotion, useCustomStyle, useContext, useCustomLength, generateResult]);

  useEffect(() => {
    localStorage.setItem('generation_convertLyrics', convertLyrics);
    localStorage.setItem('generation_targetStyle', targetStyle);
    if (convertResult) {
      localStorage.setItem('generation_convertResult', JSON.stringify(convertResult));
    }
  }, [convertLyrics, targetStyle, convertResult]);

  useEffect(() => {
    localStorage.setItem('generation_conversationLyrics', conversationLyrics);
    localStorage.setItem('generation_userFeedback', userFeedback);
    if (conversationResult) {
      localStorage.setItem('generation_conversationResult', JSON.stringify(conversationResult));
    }
  }, [conversationLyrics, userFeedback, conversationResult]);

  useEffect(() => {
    localStorage.setItem('generation_songLyrics', songLyrics);
    localStorage.setItem('generation_songTitle', songTitle);
    localStorage.setItem('generation_songStyle', songStyle);
    localStorage.setItem('generation_songTags', songTags);
    localStorage.setItem('generation_songVoice', songVoice);
    localStorage.setItem('generation_makeInstrumental', makeInstrumental.toString());
    localStorage.setItem('generation_songAsyncMode', songAsyncMode.toString());
    if (songTaskId) {
      localStorage.setItem('generation_songTaskId', songTaskId);
    }
    if (songResult) {
      localStorage.setItem('generation_songResult', JSON.stringify(songResult));
    }
  }, [songLyrics, songTitle, songStyle, songTags, songVoice, makeInstrumental, songAsyncMode, songTaskId, songResult]);

  const tabItems = [
    {
      key: 'generate',
      label: '歌词生成',
      children: (
        <Card
          style={{ 
            background: 'linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%)',
            border: '1px solid #e8e8e8'
          }}
        >
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
              <Title level={3} style={{ 
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                marginBottom: 8
              }}>
                智能歌词生成
              </Title>
              <Paragraph type="secondary" style={{ fontSize: 15 }}>
                你可以选择性地输入以下信息，系统会根据你的输入智能生成歌词。所有字段都是可选的，留空将使用默认值。
              </Paragraph>
            </div>
            
            <Row gutter={16}>
              <Col xs={24} sm={12}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Switch checked={useCustomTheme} onChange={setUseCustomTheme} />
                    <Text style={{ marginLeft: 8 }}>
                      {useCustomTheme ? '自定义主题' : '选择主题（可选）'}
                    </Text>
                  </div>
                  {useCustomTheme ? (
                    <Input
                      placeholder="如：夏日海滩、都市夜晚、青春校园等"
                      value={themeCustom}
                      onChange={(e) => setThemeCustom(e.target.value)}
                    />
                  ) : (
                    <Select
                      value={theme}
                      onChange={setTheme}
                      style={{ width: '100%' }}
                      placeholder="选择主题（可选）"
                      allowClear
                    >
                      <Option value="爱情">爱情</Option>
                      <Option value="励志">励志</Option>
                      <Option value="怀旧">怀旧</Option>
                      <Option value="友情">友情</Option>
                      <Option value="自由">自由</Option>
                    </Select>
                  )}
                </Space>
              </Col>
              <Col xs={24} sm={12}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Switch checked={useEmotion} onChange={setUseEmotion} />
                    <Text style={{ marginLeft: 8 }}>
                      {useEmotion ? '指定情感' : '不指定情感'}
                    </Text>
                  </div>
                  {useEmotion && (
                    <Input
                      placeholder="如：欢快、忧郁、浪漫、平静、激情等（不限）"
                      value={emotion}
                      onChange={(e) => setEmotion(e.target.value)}
                    />
                  )}
                </Space>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col xs={24} sm={12}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Switch checked={useCustomStyle} onChange={setUseCustomStyle} />
                    <Text style={{ marginLeft: 8 }}>
                      {useCustomStyle ? '自定义风格' : '选择风格（可选）'}
                    </Text>
                  </div>
                  {useCustomStyle ? (
                    <Input
                      placeholder="如：爵士、电子、民谣、说唱等"
                      value={styleCustom}
                      onChange={(e) => setStyleCustom(e.target.value)}
                    />
                  ) : (
                    <Select
                      value={style}
                      onChange={setStyle}
                      style={{ width: '100%' }}
                      placeholder="选择风格（可选）"
                      allowClear
                    >
                      <Option value="流行">流行</Option>
                      <Option value="古风">古风</Option>
                      <Option value="摇滚">摇滚</Option>
                      <Option value="抒情">抒情</Option>
                    </Select>
                  )}
                </Space>
              </Col>
              <Col xs={24} sm={12}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Switch checked={useCustomLength} onChange={setUseCustomLength} />
                    <Text style={{ marginLeft: 8 }}>
                      {useCustomLength ? '自定义长度' : '不限制长度（系统自动生成）'}
                    </Text>
                  </div>
                  {useCustomLength && (
                    <Input
                      type="number"
                      placeholder="请输入行数"
                      value={customLength}
                      onChange={(e) => setCustomLength(parseInt(e.target.value) || 16)}
                      min={4}
                      max={100}
                    />
                  )}
                </Space>
              </Col>
            </Row>

            <div>
              <div>
                <Switch checked={useContext} onChange={setUseContext} />
                <Text style={{ marginLeft: 8 }}>
                  {useContext ? '提供上下文（可选）' : '不提供上下文'}
                </Text>
              </div>
              {useContext && (
                <TextArea
                  rows={4}
                  value={context}
                  onChange={(e) => setContext(e.target.value)}
                  placeholder="输入前文歌词，每行一句。系统将基于此继续创作"
                  style={{ marginTop: 8 }}
                />
              )}
            </div>

            <div>
              <Text>你的想法（可选）：</Text>
              <TextArea
                rows={3}
                value={userIdea}
                onChange={(e) => setUserIdea(e.target.value)}
                placeholder="描述你对这首歌的想法、场景、故事等，帮助系统更好地创作"
              />
            </div>

            <Space style={{ width: '100%' }} direction="vertical">
              <Button
                type="primary"
                onClick={handleGenerate}
                loading={loading}
                block
                size="large"
              >
                生成歌词
              </Button>
              <Button
                onClick={() => {
                  // 清空所有state
                  setTheme('');
                  setThemeCustom('');
                  setEmotion('');
                  setStyle('');
                  setStyleCustom('');
                  setContext('');
                  setUserIdea('');
                  setUseCustomTheme(false);
                  setUseEmotion(false);
                  setUseCustomStyle(false);
                  setUseContext(false);
                  setUseCustomLength(false);
                  setLength(null);
                  setCustomLength(16);
                  setGenerateResult(null);
                  // 清空所有相关的localStorage
                  localStorage.removeItem('generation_theme');
                  localStorage.removeItem('generation_themeCustom');
                  localStorage.removeItem('generation_emotion');
                  localStorage.removeItem('generation_style');
                  localStorage.removeItem('generation_styleCustom');
                  localStorage.removeItem('generation_context');
                  localStorage.removeItem('generation_userIdea');
                  localStorage.removeItem('generation_length');
                  localStorage.removeItem('generation_customLength');
                  localStorage.removeItem('generation_useCustomTheme');
                  localStorage.removeItem('generation_useEmotion');
                  localStorage.removeItem('generation_useCustomStyle');
                  localStorage.removeItem('generation_useContext');
                  localStorage.removeItem('generation_useCustomLength');
                  localStorage.removeItem('generation_result');
                  message.info('已重置所有输入');
                }}
                block
              >
                重置
              </Button>
            </Space>

            {generateResult && (
              <Card>
                <Title level={5}>生成结果：</Title>
                <div style={{ fontSize: 16, lineHeight: 1.8 }}>
                  {(() => {
                    let lyrics = String(generateResult.lyrics || generateResult.next_line || generateResult.improved_lyrics || '');
                    const title = generateResult.title;
                    
                    // 从歌词中移除所有标题行（避免重复显示）
                    const lyricsLines = lyrics.split('\n');
                    const cleanedLines = [];
                    
                    for (let i = 0; i < lyricsLines.length; i++) {
                      const line = lyricsLines[i];
                      const trimmedLine = line.trim();
                      
                      if (!trimmedLine) {
                        cleanedLines.push('');
                        continue;
                      }
                      
                      // 检查是否是标题格式（《...》或【...】或 # 《...》或 歌名：），删除所有标题行
                      let isTitleLine = 
                        /^《.*》\s*$/.test(trimmedLine) ||
                        /^【.*】\s*$/.test(trimmedLine) ||
                        /^#{1,6}\s*《.*》\s*$/.test(trimmedLine) ||
                        /^#{1,6}\s*【.*】\s*$/.test(trimmedLine) ||
                        /^歌名[：:]\s*《.*》\s*$/.test(trimmedLine) ||  // 歌名：《星轨证词》
                        /^歌名[：:]\s*/.test(trimmedLine);  // 歌名：星轨证词
                      
                      // 如果有title，也检查是否匹配title（无论是否已经是标题格式）
                      if (title) {
                        const titleClean = title.replace(/[《》"'【】[\]()（）\s#]+/g, '');
                        const lineClean = trimmedLine.replace(/[《》"'【】[\]()（）\s#]+/g, '');
                        if (lineClean === titleClean || trimmedLine === title || trimmedLine === `《${title}》` || trimmedLine === `# 《${title}》`) {
                          isTitleLine = true;
                        }
                      }
                      
                      // 如果是标题行，跳过（删除所有标题行）
                      if (isTitleLine) {
                        continue;
                      }
                      
                      cleanedLines.push(line);
                    }
                    lyrics = cleanedLines.join('\n');
                    
                    // 兜底处理：如果歌词都挤在一起（用空格分隔），转换为换行
                    // 按行处理，确保结构标记后的内容都单独提行
                    const finalLines = [];
                    const processedLyricsLines = lyrics.split('\n');
                    
                    for (let i = 0; i < processedLyricsLines.length; i++) {
                      let line = processedLyricsLines[i].trim();
                      if (!line) {
                        finalLines.push('');
                        continue;
                      }
                      
                      // 检查是否是结构标记行（纯结构标记，如"主歌1"）
                      const structureMatch = line.match(/^((?:主歌|副歌|预副歌|桥段|间奏|尾奏|前奏|Intro|Verse|Chorus|Bridge|Outro|Interlude)\d*)$/);
                      if (structureMatch) {
                        // 纯结构标记，单独一行
                        finalLines.push(line);
                        continue;
                      }
                      
                      // 检查行首是否有结构标记（如"主歌1 夜空之中 沉默着..."）
                      const structurePrefixMatch = line.match(/^((?:主歌|副歌|预副歌|桥段|间奏|尾奏|前奏|Intro|Verse|Chorus|Bridge|Outro|Interlude)\d*)\s+(.+)$/);
                      if (structurePrefixMatch) {
                        // 有结构标记，提取标记和内容
                        const structureMarker = structurePrefixMatch[1];
                        const content = structurePrefixMatch[2];
                        finalLines.push(structureMarker);
                        // 将内容部分的所有空格分隔的词语都转换为单独的行
                        const contentParts = content.split(/\s+/).filter(part => part.trim());
                        finalLines.push(...contentParts);
                      } else {
                        // 普通行，将空格分隔的内容转换为换行
                        // 先处理多个连续空格
                        line = line.replace(/\s{2,}/g, '\n');
                        // 然后处理单个空格（中文字符之间）
                        let replaceCount = 0;
                        const maxReplaceIterations = 100;
                        while (/([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])/.test(line) && replaceCount < maxReplaceIterations) {
                          const beforeReplace = line;
                          line = line.replace(/([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])/g, '$1\n$2');
                          if (beforeReplace === line) {
                            break;
                          }
                          replaceCount++;
                        }
                        // 按换行分割并添加
                        const lineParts = line.split('\n').filter(part => part.trim());
                        finalLines.push(...lineParts);
                      }
                    }
                    
                    lyrics = finalLines.join('\n');
                    
                    // 确保每行歌词都单独显示，并将标题和结构标记加粗
                    const lyricsWithBreaks = lyrics.split('\n')
                      .map(line => {
                        const trimmed = line.trim();
                        if (!trimmed) return '';
                        
                        // 检查是否是加粗的标题行（**《标题》**）
                        const titleBoldMatch = trimmed.match(/^\*\*《([^》]+)》\*\*$/);
                        if (titleBoldMatch) {
                          // 标题加粗显示
                          return `<strong>《${titleBoldMatch[1]}》</strong>`;
                        }
                        
                        // 检查是否是加粗的结构标记行（**主歌1**、**副歌**等）
                        const structureBoldMatch = trimmed.match(/^\*\*((?:主歌|副歌|预副歌|桥段|间奏|尾奏|前奏|Intro|Verse|Chorus|Bridge|Outro|Interlude)\d*)\*\*$/);
                        if (structureBoldMatch) {
                          // 结构标记加粗显示
                          return `<strong>${structureBoldMatch[1]}</strong>`;
                        }
                        
                        // 检查是否是纯结构标记（没有加粗标记，但内容是结构标记）
                        const structurePattern = /^((?:主歌|副歌|预副歌|桥段|间奏|尾奏|前奏|Intro|Verse|Chorus|Bridge|Outro|Interlude)\d*)$/;
                        if (structurePattern.test(trimmed)) {
                          // 结构标记加粗显示
                          return `<strong>${trimmed}</strong>`;
                        }
                        
                        // 普通歌词行，移除 markdown 加粗语法后返回
                        let processedLine = trimmed.replace(/\*\*/g, '');
                        return processedLine;
                      })
                      .filter(line => line) // 移除空行
                      .join('<br/>');
                    
                    return (
                      <div>
                        <div 
                          style={{ 
                            fontSize: 16, 
                            lineHeight: 1.8
                          }}
                          dangerouslySetInnerHTML={{ 
                            __html: lyricsWithBreaks
                          }}
                        />
                      </div>
                    );
                  })()}
                </div>
                <Space style={{ marginTop: 16 }}>
                  <Button
                    onClick={() => {
                      setConversationLyrics(generateResult.lyrics || generateResult.next_line || generateResult.improved_lyrics);
                      setActiveTab('continue');
                    }}
                  >
                    继续修改此歌词
                  </Button>
                  <Button
                    onClick={() => {
                      setGenerateResult(null);
                      // 清空输入，允许重新生成
                    }}
                  >
                    重新生成
                  </Button>
                </Space>
              </Card>
            )}
          </Space>
        </Card>
      )
    },
    {
      key: 'convert',
      label: '风格转换',
      children: (
        <Card
          style={{ 
            background: 'linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%)',
            border: '1px solid #e8e8e8'
          }}
        >
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
              <Title level={3} style={{ 
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                marginBottom: 8
              }}>
                歌词风格转换
              </Title>
              <Paragraph type="secondary" style={{ fontSize: 15 }}>
                将现有歌词转换为不同的音乐风格，保持原意但改变表达方式
              </Paragraph>
            </div>
            <div>
              <Text>原歌词：</Text>
              <TextArea
                rows={8}
                value={convertLyrics}
                onChange={(e) => setConvertLyrics(e.target.value)}
                placeholder="输入要转换的歌词"
              />
            </div>
            <div>
              <Text>目标风格：</Text>
              <Select
                value={targetStyle}
                onChange={setTargetStyle}
                style={{ width: '100%' }}
              >
                <Option value="流行">流行</Option>
                <Option value="古风">古风</Option>
                <Option value="摇滚">摇滚</Option>
                <Option value="抒情">抒情</Option>
                <Option value="爵士">爵士</Option>
                <Option value="电子">电子</Option>
                <Option value="民谣">民谣</Option>
                <Option value="说唱">说唱</Option>
              </Select>
            </div>
            <Space style={{ width: '100%' }} direction="vertical">
              <Button
                type="primary"
                onClick={handleConvert}
                loading={loading}
                block
                size="large"
              >
                转换风格
              </Button>
              <Button
                onClick={() => {
                  setConvertLyrics('');
                  setTargetStyle('流行');
                  setConvertResult(null);
                  // 清空相关的localStorage
                  localStorage.removeItem('generation_convertLyrics');
                  localStorage.removeItem('generation_targetStyle');
                  localStorage.removeItem('generation_convertResult');
                  message.info('已重置所有输入');
                }}
                block
              >
                重置
              </Button>
            </Space>
            {convertResult && (
              <Card>
                <Title level={5}>转换结果：</Title>
                <div style={{ fontSize: 16, lineHeight: 1.8 }}>
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    components={{
                      p: ({node, ...props}) => <div style={{ marginBottom: 0, lineHeight: 1.8 }} {...props} />,
                      strong: ({node, ...props}) => <strong style={{ fontSize: '1em' }} {...props} />,
                      br: () => <br />
                    }}
                  >
                    {String(convertResult.converted || '')}
                  </ReactMarkdown>
                </div>
              </Card>
            )}
          </Space>
        </Card>
      )
    },
    {
      key: 'continue',
      label: '继续对话',
      children: (
        <Card
          style={{ 
            background: 'linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%)',
            border: '1px solid #e8e8e8'
          }}
        >
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
              <Title level={3} style={{ 
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                marginBottom: 8
              }}>
                继续修改歌词
              </Title>
              <Paragraph type="secondary" style={{ fontSize: 15 }}>
                对生成的歌词不满意？提供反馈，系统会根据你的要求继续修改
              </Paragraph>
            </div>
            <div>
              <Text>当前歌词：</Text>
              <TextArea
                rows={8}
                value={conversationLyrics}
                onChange={(e) => setConversationLyrics(e.target.value)}
                placeholder="粘贴需要修改的歌词"
              />
            </div>
            <div>
              <Text>你的反馈：</Text>
              <TextArea
                rows={4}
                value={userFeedback}
                onChange={(e) => setUserFeedback(e.target.value)}
                placeholder="描述你希望如何修改，如：更浪漫一些、增加押韵、更简洁、更悲伤等"
              />
            </div>
            <Space style={{ width: '100%' }} direction="vertical">
              <Button
                type="primary"
                onClick={handleContinueConversation}
                loading={loading}
                block
                size="large"
              >
                根据反馈修改
              </Button>
              <Button
                onClick={() => {
                  setConversationLyrics('');
                  setUserFeedback('');
                  setConversationResult(null);
                  // 清空相关的localStorage
                  localStorage.removeItem('generation_conversationLyrics');
                  localStorage.removeItem('generation_userFeedback');
                  localStorage.removeItem('generation_conversationResult');
                  message.info('已重置所有输入');
                }}
                block
              >
                重置
              </Button>
            </Space>
            {conversationResult && (
              <Card>
                <Title level={5}>修改后的歌词：</Title>
                <div style={{ fontSize: 16, lineHeight: 1.8 }}>
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    components={{
                      p: ({node, ...props}) => <div style={{ marginBottom: 0, lineHeight: 1.8 }} {...props} />,
                      strong: ({node, ...props}) => <strong style={{ fontSize: '1em' }} {...props} />,
                      br: () => <br />
                    }}
                  >
                    {String(conversationResult.improved_lyrics || '')}
                  </ReactMarkdown>
                </div>
                <Button
                  style={{ marginTop: 16 }}
                  onClick={() => {
                    setConversationLyrics(conversationResult.improved_lyrics);
                    setUserFeedback('');
                    setConversationResult(null);
                  }}
                >
                  使用此版本继续修改
                </Button>
              </Card>
            )}
          </Space>
        </Card>
      )
    },
    {
      key: 'song',
      label: '歌曲生成',
      children: (
        <Card 
          style={{ 
            background: 'linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%)',
            border: '1px solid #e8e8e8'
          }}
        >
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
              <Title level={3} style={{ 
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                marginBottom: 8
              }}>
                AI 歌曲生成
              </Title>
              <Paragraph type="secondary" style={{ fontSize: 15 }}>
                输入歌词，AI 将为您生成完整的歌曲（包括音频和伴奏）。使用 Suno AI 技术，支持多种音乐风格。
              </Paragraph>
            </div>
            
            <Alert
              message="使用说明"
              description={
                <div>
                  <p style={{ margin: '4px 0' }}>• 歌曲生成需要1-5分钟时间，建议使用异步模式</p>
                  <p style={{ margin: '4px 0' }}>• 支持包含"主歌"、"副歌"、"桥段"等结构标记，系统会自动识别并忽略</p>
                  <p style={{ margin: '4px 0' }}>• 生成完成后将提供音频下载链接和在线播放</p>
                </div>
              }
              type="info"
              showIcon
              style={{ 
                marginBottom: 16,
                borderRadius: 8,
                background: 'rgba(102, 126, 234, 0.05)',
                border: '1px solid rgba(102, 126, 234, 0.2)'
              }}
            />

            <div>
              <Text strong>歌词内容（必需）：</Text>
              <Paragraph type="secondary" style={{ fontSize: 12, marginTop: 4 }}>
                支持包含"主歌"、"副歌"、"桥段"等结构标记，系统会自动识别并忽略这些标记
              </Paragraph>
              <TextArea
                rows={12}
                value={songLyrics}
                onChange={(e) => setSongLyrics(e.target.value)}
                placeholder="请输入歌词，每行一句&#10;可以包含结构标记，例如：&#10;&#10;主歌1&#10;那年长街春意正浓&#10;石板路映着新绿梧桐&#10;&#10;副歌&#10;一时心头悸动&#10;似你温柔剑锋"
                style={{ marginTop: 8, fontFamily: 'monospace', fontSize: 14 }}
              />
            </div>

            <Card 
              size="small" 
              style={{ 
                background: '#fafafa',
                border: '1px solid #e8e8e8',
                borderRadius: 8
              }}
            >
              <Row gutter={[16, 16]}>
                <Col xs={24} sm={12}>
                  <div>
                    <Text strong style={{ display: 'block', marginBottom: 8 }}>
                      歌曲标题（可选）
                    </Text>
                    <Input
                      value={songTitle}
                      onChange={(e) => setSongTitle(e.target.value)}
                      placeholder="如果不填写，将自动从歌词提取"
                      style={{ borderRadius: 6 }}
                    />
                  </div>
                </Col>
                <Col xs={24} sm={12}>
                  <div>
                    <Text strong style={{ display: 'block', marginBottom: 8 }}>
                      音乐风格
                    </Text>
                    <Select
                      value={songStyle}
                      onChange={setSongStyle}
                      style={{ width: '100%', borderRadius: 6 }}
                    >
                      <Option value="流行">流行</Option>
                      <Option value="摇滚">摇滚</Option>
                      <Option value="抒情">抒情</Option>
                      <Option value="古风">古风</Option>
                      <Option value="民谣">民谣</Option>
                      <Option value="电子">电子</Option>
                      <Option value="爵士">爵士</Option>
                      <Option value="说唱">说唱</Option>
                    </Select>
                  </div>
                </Col>
                <Col xs={24} sm={12}>
                  <div>
                    <Text strong style={{ display: 'block', marginBottom: 8 }}>
                      风格标签（可选）
                    </Text>
                    <Input
                      value={songTags}
                      onChange={(e) => setSongTags(e.target.value)}
                      placeholder="如：pop, cheerful, summer（留空将根据音乐风格自动生成）"
                      style={{ borderRadius: 6 }}
                    />
                  </div>
                </Col>
                <Col xs={24} sm={12}>
                  <div>
                    <Text strong style={{ display: 'block', marginBottom: 8 }}>
                      语音选择
                    </Text>
                    <Select
                      value={songVoice}
                      onChange={setSongVoice}
                      style={{ width: '100%', borderRadius: 6 }}
                    >
                      <Option value="default">默认</Option>
                      <Option value="male">男声</Option>
                      <Option value="female">女声</Option>
                    </Select>
                  </div>
                </Col>
              </Row>
            </Card>

            <Card 
              size="small" 
              style={{ 
                background: '#fafafa',
                border: '1px solid #e8e8e8',
                borderRadius: 8
              }}
            >
              <Row gutter={16}>
                <Col xs={24} sm={12}>
                  <Space>
                    <Switch 
                      checked={makeInstrumental} 
                      onChange={setMakeInstrumental}
                      style={{ minWidth: 44 }}
                    />
                    <Text strong>纯音乐（无歌词）</Text>
                  </Space>
                </Col>
                <Col xs={24} sm={12}>
                  <Space>
                    <Switch 
                      checked={songAsyncMode} 
                      onChange={setSongAsyncMode}
                      style={{ minWidth: 44 }}
                    />
                    <Text strong>异步模式（推荐）</Text>
                  </Space>
                </Col>
              </Row>
            </Card>

            <Space style={{ width: '100%' }} direction="vertical">
              <Button
                type="primary"
                onClick={handleGenerateSong}
                loading={loading}
                block
                size="large"
                style={{
                  height: 48,
                  fontSize: 16,
                  fontWeight: 600,
                  borderRadius: 8,
                  marginTop: 8
                }}
              >
                {loading ? '正在生成中...' : '生成歌曲'}
              </Button>
              <Button
                onClick={() => {
                  setSongLyrics('');
                  setSongTitle('');
                  setSongStyle('流行');
                  setSongTags('');
                  setSongVoice('default');
                  setMakeInstrumental(false);
                  setSongAsyncMode(true);
                  setSongResult(null);
                  setSongTaskId(null);
                  if (pollingInterval) {
                    clearInterval(pollingInterval);
                    setPollingInterval(null);
                  }
                  // 清空相关的localStorage
                  localStorage.removeItem('generation_songLyrics');
                  localStorage.removeItem('generation_songTitle');
                  localStorage.removeItem('generation_songStyle');
                  localStorage.removeItem('generation_songTags');
                  localStorage.removeItem('generation_songVoice');
                  localStorage.removeItem('generation_makeInstrumental');
                  localStorage.removeItem('generation_songAsyncMode');
                  localStorage.removeItem('generation_songResult');
                  localStorage.removeItem('generation_songTaskId');
                  message.info('已重置所有输入');
                }}
                block
              >
                重置
              </Button>
            </Space>

            {songResult && (
              <Card
                style={{
                  marginTop: 24,
                  background: 'linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%)',
                  border: '2px solid #e8e8e8',
                  borderRadius: 12
                }}
              >
                <Title level={4} style={{ 
                  color: '#667eea',
                  marginBottom: 16,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8
                }}>
                  生成结果
                </Title>
                {songResult.status === 'pending' || songResult.status === 'in_progress' ? (
                  <div>
                    <Alert
                      message="任务处理中"
                      description={
                        <div>
                          <p>任务ID: {songResult.task_id || songTaskId}</p>
                          <p>请稍候，正在生成歌曲...（通常需要1-5分钟）</p>
                          <Progress percent={songProgress} status="active" />
                          <Button
                            onClick={handleQuerySongStatus}
                            style={{ marginTop: 16 }}
                          >
                            手动刷新状态
                          </Button>
                        </div>
                      }
                      type="info"
                      showIcon
                    />
                  </div>
                ) : songResult.status === 'success' || songResult.status === 'completed' ? (
                  <div>
                    <Alert
                      message="生成完成！"
                      description="歌曲已成功生成"
                      type="success"
                      showIcon
                      style={{ marginBottom: 16 }}
                    />
                    {songResult.clips && songResult.clips.length > 0 ? (
                      (() => {
                        // 筛选出所有完成的音频（状态为complete且有audio_url）
                        const completedClips = songResult.clips.filter(c => c.status === 'complete' && c.audio_url);
                        // 如果没有完成的，使用所有有audio_url的
                        const availableClips = completedClips.length > 0 
                          ? completedClips 
                          : songResult.clips.filter(c => c.audio_url);
                        
                        // 只选择完整歌曲（时长大于60秒的），按时长排序
                        const fullSongs = availableClips.filter(c => (c.duration || 0) >= 60);
                        const clipsToShow = fullSongs.length >= 2 
                          ? fullSongs.slice(0, 3)  // 如果有多个完整歌曲，显示前3个
                          : availableClips.slice(0, 3);  // 否则显示所有可用的（最多3个）
                        
                        // 按时长排序，最长的在前
                        clipsToShow.sort((a, b) => (b.duration || 0) - (a.duration || 0));
                        
                        return clipsToShow.length > 0 ? (
                          <div>
                            <Title level={5} style={{ marginBottom: 16, marginTop: 16 }}>
                              生成的音频（请选择您喜欢的版本）：
                            </Title>
                            {clipsToShow.map((clip, index) => {
                              // 分析音频特点，生成风格描述
                              const tags = clip.tags || '';
                              
                              // 根据tags和索引生成风格描述
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
                                <Card 
                                  key={index} 
                                  style={{ 
                                    marginTop: index > 0 ? 16 : 0,
                                    border: '1px solid #e8e8e8',
                                    borderRadius: 8
                                  }}
                                >
                                  <Space direction="vertical" style={{ width: '100%' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                      <Text strong style={{ fontSize: 16 }}>
                                        版本 {index + 1}
                                      </Text>
                                      <Tag color={index === 0 ? 'green' : 'blue'}>
                                        {description}
                                      </Tag>
                                    </div>
                                    {clip.audio_url && (
                                      <div style={{ marginTop: 12 }}>
                                        <audio 
                                          controls 
                                          style={{ width: '100%' }}
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
                                      </div>
                                    )}
                                    <Button
                                      type="primary"
                                      href={clip.audio_url}
                                      target="_blank"
                                      style={{ marginTop: 8 }}
                                      block
                                    >
                                      下载此版本
                                    </Button>
                                  </Space>
                                </Card>
                              );
                            })}
                          </div>
                        ) : null;
                      })()
                    ) : (
                      <div>
                        {songResult.audio_url && (
                          <div>
                            <Text strong>音频链接：</Text>
                            <div style={{ marginTop: 8 }}>
                              <audio controls style={{ width: '100%' }}>
                                <source src={songResult.audio_url} type="audio/mpeg" />
                                您的浏览器不支持音频播放
                              </audio>
                            </div>
                            <Button
                              type="link"
                              href={songResult.audio_url}
                              target="_blank"
                              style={{ marginTop: 8 }}
                            >
                              下载音频
                            </Button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ) : (
                  <Alert
                    message="生成失败"
                    description={songResult.message || '未知错误'}
                    type="error"
                    showIcon
                  />
                )}
              </Card>
            )}
          </Space>
        </Card>
      )
    }
  ];

  return (
    <div className="page-container">
      <Title level={2} className="page-title">创作助手</Title>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
      />
      
      {/* 历史记录选择模态框 */}
      <Modal
        title="选择历史歌词"
        open={showHistoryModal}
        onCancel={() => setShowHistoryModal(false)}
        footer={null}
        width={800}
      >
        <List
          dataSource={generationHistory}
          renderItem={(item) => (
            <List.Item
              actions={[
                <Button
                  type="primary"
                  size="small"
                  onClick={() => {
                    setConversationLyrics(item.generated_lyrics);
                    setShowHistoryModal(false);
                    message.success('已选择历史歌词');
                  }}
                >
                  选择
                </Button>
              ]}
            >
              <List.Item.Meta
                title={`${item.prompt || '歌词生成'} - ${item.style || '通用风格'}`}
                description={
                  <div>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {new Date(item.created_at).toLocaleString()}
                    </Text>
                    <div style={{ marginTop: 8, maxHeight: 150, overflow: 'auto' }}>
                      <Text style={{ fontSize: 13, whiteSpace: 'pre-line' }}>
                        {item.generated_lyrics?.substring(0, 200)}
                        {item.generated_lyrics?.length > 200 ? '...' : ''}
                      </Text>
                    </div>
                  </div>
                }
              />
            </List.Item>
          )}
          pagination={{
            pageSize: 5,
            showSizeChanger: false
          }}
        />
      </Modal>
    </div>
  );
};

export default GenerationPage;
