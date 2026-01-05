import React, { useState } from 'react';
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
  Divider
} from 'antd';
import { generationAPI } from '../services/api';

const { TextArea } = Input;
const { Title, Paragraph } = Typography;
const { Option } = Select;

const GenerationPage = () => {
  const { Text } = Typography;
  const [activeTab, setActiveTab] = useState('generate');
  const [loading, setLoading] = useState(false);
  
  // 统一的歌词生成参数
  const [theme, setTheme] = useState('');
  const [useCustomTheme, setUseCustomTheme] = useState(false);
  const [themeCustom, setThemeCustom] = useState('');
  const [emotion, setEmotion] = useState('');
  const [useEmotion, setUseEmotion] = useState(false);
  const [style, setStyle] = useState('');
  const [useCustomStyle, setUseCustomStyle] = useState(false);
  const [styleCustom, setStyleCustom] = useState('');
  const [context, setContext] = useState('');
  const [useContext, setUseContext] = useState(false);
  const [length, setLength] = useState(16);
  const [useCustomLength, setUseCustomLength] = useState(false);
  const [customLength, setCustomLength] = useState(16);
  const [userIdea, setUserIdea] = useState('');
  const [generateResult, setGenerateResult] = useState(null);

  // 风格转换
  const [convertLyrics, setConvertLyrics] = useState('');
  const [targetStyle, setTargetStyle] = useState('流行');
  const [convertResult, setConvertResult] = useState(null);
  
  // 继续对话
  const [conversationLyrics, setConversationLyrics] = useState('');
  const [userFeedback, setUserFeedback] = useState('');
  const [conversationResult, setConversationResult] = useState(null);

  const handleGenerate = async () => {
    setLoading(true);
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
        // 有上下文，使用上下文生成
        response = await generationAPI.generateByContext(contextLines);
      } else if (finalTheme || finalStyle || userIdea) {
        // 有主题、风格或想法，使用完整生成
        response = await generationAPI.generateFullSong(
          finalStyle || '流行',
          finalTheme || '通用',
          finalEmotion,
          userIdea,
          undefined
        );
      } else {
        // 只有主题，使用主题生成
        response = await generationAPI.generateByTheme(
          finalTheme || '通用',
          finalEmotion,
          finalLength
        );
      }
      
      if (response.data.success) {
        setGenerateResult(response.data.data);
        message.success('生成成功！');
      }
    } catch (error) {
      message.error('生成失败：' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
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
      message.error('转换失败：' + (error.response?.data?.error || error.message));
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
      message.error('修改失败：' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  const tabItems = [
    {
      key: 'generate',
      label: '歌词生成',
      children: (
        <Card>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Title level={4}>智能歌词生成</Title>
            <Paragraph type="secondary">
              你可以选择性地输入以下信息，系统会根据你的输入智能生成歌词。所有字段都是可选的，留空将使用默认值。
            </Paragraph>
            
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
                      {useCustomLength ? '自定义长度' : '默认长度（16行）'}
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

            <Button
              type="primary"
              onClick={handleGenerate}
              loading={loading}
              block
              size="large"
            >
              生成歌词
            </Button>

            {generateResult && (
              <Card>
                <Title level={5}>生成结果：</Title>
                <Paragraph style={{ whiteSpace: 'pre-line', fontSize: 16, lineHeight: 1.8 }}>
                  {generateResult.lyrics || generateResult.next_line || generateResult.improved_lyrics}
                </Paragraph>
                <Button
                  style={{ marginTop: 16 }}
                  onClick={() => {
                    setConversationLyrics(generateResult.lyrics || generateResult.next_line || generateResult.improved_lyrics);
                    setActiveTab('continue');
                  }}
                >
                  继续修改此歌词
                </Button>
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
        <Card>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Title level={4}>歌词风格转换</Title>
            <Paragraph type="secondary">
              将现有歌词转换为不同的音乐风格，保持原意但改变表达方式
            </Paragraph>
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
            <Button
              type="primary"
              onClick={handleConvert}
              loading={loading}
              block
              size="large"
            >
              转换风格
            </Button>
            {convertResult && (
              <Card>
                <Title level={5}>转换结果：</Title>
                <Paragraph style={{ whiteSpace: 'pre-line', fontSize: 16, lineHeight: 1.8 }}>
                  {convertResult.converted}
                </Paragraph>
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
        <Card>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Title level={4}>继续修改歌词</Title>
            <Paragraph type="secondary">
              对生成的歌词不满意？提供反馈，系统会根据你的要求继续修改
            </Paragraph>
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
            <Button
              type="primary"
              onClick={handleContinueConversation}
              loading={loading}
              block
              size="large"
            >
              根据反馈修改
            </Button>
            {conversationResult && (
              <Card>
                <Title level={5}>修改后的歌词：</Title>
                <Paragraph style={{ whiteSpace: 'pre-line', fontSize: 16, lineHeight: 1.8 }}>
                  {conversationResult.improved_lyrics}
                </Paragraph>
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
    }
  ];

  return (
    <div className="page-container">
      <Title level={2} className="page-title">✍️ 创作助手</Title>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
      />
    </div>
  );
};

export default GenerationPage;
