import React from 'react';
import { Card, Row, Col, Typography, Button, Space } from 'antd';
import { useNavigate } from 'react-router-dom';
import {
  BarChartOutlined,
  EditOutlined,
  HeartOutlined,
  RocketOutlined
} from '@ant-design/icons';

const { Title, Paragraph } = Typography;

const HomePage = () => {
  const navigate = useNavigate();

  const features = [
    {
      title: '基础分析',
      icon: <BarChartOutlined style={{ fontSize: 48, color: '#1890ff' }} />,
      description: '情感分析、主题提取、韵律检测、可视化报告',
      path: '/analysis',
      color: '#1890ff'
    },
    {
      title: '创作助手',
      icon: <EditOutlined style={{ fontSize: 48, color: '#52c41a' }} />,
      description: '智能歌词生成、创作优化、结构分析、创作评估',
      path: '/generation',
      color: '#52c41a'
    },
    {
      title: '智能推荐',
      icon: <HeartOutlined style={{ fontSize: 48, color: '#f5222d' }} />,
      description: '个性化推荐、知识图谱、深度洞察',
      path: '/recommendation',
      color: '#f5222d'
    },
  ];

  return (
    <div className="page-container">
      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <Title level={1} style={{ 
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          fontSize: 48,
          fontWeight: 'bold',
          marginBottom: 16
        }}>
          🎵 旋律工坊
        </Title>
        <Paragraph style={{ fontSize: 18, color: '#666', lineHeight: 1.8 }}>
          从理解到创作，从灵感到旋律
          <br />
          你的专属音乐创作伙伴
        </Paragraph>
      </div>

      <Row gutter={[24, 24]}>
        {features.map((feature, index) => (
          <Col xs={24} sm={24} md={8} key={index}>
            <Card
              hoverable
              style={{
                height: '100%',
                textAlign: 'center',
                background: `linear-gradient(135deg, ${feature.color}15 0%, ${feature.color}05 100%)`,
                border: `2px solid ${feature.color}40`,
                borderRadius: 16,
                transition: 'all 0.3s ease',
                cursor: 'pointer'
              }}
              onClick={() => navigate(feature.path)}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-8px)';
                e.currentTarget.style.boxShadow = `0 12px 32px ${feature.color}30`;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 4px 16px rgba(0, 0, 0, 0.08)';
              }}
            >
              <div style={{ marginBottom: 16, fontSize: 64 }}>
                {feature.icon}
              </div>
              <Title level={3} style={{ 
                color: feature.color,
                background: `linear-gradient(135deg, ${feature.color} 0%, ${feature.color}dd 100%)`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}>
                {feature.title}
              </Title>
              <Paragraph style={{ color: '#666', minHeight: 60, fontSize: 15 }}>
                {feature.description}
              </Paragraph>
              <Button
                type="primary"
                shape="round"
                size="large"
                style={{ 
                  background: `linear-gradient(135deg, ${feature.color} 0%, ${feature.color}dd 100%)`,
                  border: 'none',
                  boxShadow: `0 4px 12px ${feature.color}40`
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(feature.path);
                }}
              >
                立即体验
              </Button>
            </Card>
          </Col>
        ))}
      </Row>

      <Card style={{ marginTop: 48, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
        <Space direction="vertical" size="large" style={{ width: '100%', textAlign: 'center' }}>
          <RocketOutlined style={{ fontSize: 64 }} />
          <Title level={2} style={{ color: 'white', margin: 0 }}>
            三大层级，渐进式体验
          </Title>
          <Row gutter={[16, 16]}>
            <Col xs={24} md={8}>
              <div style={{ padding: 16, background: 'rgba(255,255,255,0.1)', borderRadius: 8 }}>
                <Title level={4} style={{ color: 'white' }}>第一层：基础分析</Title>
                <Paragraph style={{ color: 'rgba(255,255,255,0.9)' }}>
                  快速理解歌词内容与情感
                </Paragraph>
              </div>
            </Col>
            <Col xs={24} md={8}>
              <div style={{ padding: 16, background: 'rgba(255,255,255,0.1)', borderRadius: 8 }}>
                <Title level={4} style={{ color: 'white' }}>第二层：创作助手</Title>
                <Paragraph style={{ color: 'rgba(255,255,255,0.9)' }}>
                  辅助音乐创作与优化
                </Paragraph>
              </div>
            </Col>
            <Col xs={24} md={8}>
              <div style={{ padding: 16, background: 'rgba(255,255,255,0.1)', borderRadius: 8 }}>
                <Title level={4} style={{ color: 'white' }}>第三层：智能系统</Title>
                <Paragraph style={{ color: 'rgba(255,255,255,0.9)' }}>
                  深度理解与个性化服务
                </Paragraph>
              </div>
            </Col>
          </Row>
        </Space>
      </Card>
    </div>
  );
};

export default HomePage;



