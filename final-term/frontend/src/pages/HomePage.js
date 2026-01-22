import React from 'react';
import { Card, Row, Col, Typography, Button } from 'antd';
import { useNavigate } from 'react-router-dom';
import {
  BarChartOutlined,
  EditOutlined,
  HeartOutlined
} from '@ant-design/icons';

const { Title, Paragraph } = Typography;

const HomePage = () => {
  const navigate = useNavigate();

  const features = [
    {
      title: '基础分析',
      icon: <BarChartOutlined style={{ fontSize: 48, color: '#4A90E2' }} />,
      description: '情感分析、主题提取、韵律检测、可视化报告',
      path: '/analysis',
      color: '#4A90E2'
    },
    {
      title: '创作助手',
      icon: <EditOutlined style={{ fontSize: 48, color: '#9B59B6' }} />,
      description: '智能歌词生成、创作优化、结构分析、创作评估',
      path: '/generation',
      color: '#9B59B6'
    },
    {
      title: '智能推荐',
      icon: <HeartOutlined style={{ fontSize: 48, color: '#6C5CE7' }} />,
      description: '个性化推荐、知识图谱、深度洞察',
      path: '/recommendation',
      color: '#6C5CE7'
    },
  ];

  return (
    <div style={{ 
      height: 'calc(100vh - 112px)', 
      display: 'flex', 
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '24px',
      position: 'relative',
      overflow: 'hidden',
      background: 'linear-gradient(135deg, #e6f0ff 0%, #e8e3ff 50%, #f0e6ff 100%)'
    }}>
      {/* 主要内容 */}
      <div style={{ 
        textAlign: 'center', 
        marginBottom: 48,
        zIndex: 1,
        maxWidth: '1200px',
        width: '100%'
      }}>
        <Title level={1} style={{ 
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          fontSize: '56px',
          fontWeight: 'bold',
          marginBottom: 16,
          letterSpacing: '2px'
        }}>
          旋律工坊
        </Title>
        <Paragraph style={{ 
          fontSize: 20, 
          color: '#666', 
          lineHeight: 1.8,
          marginBottom: 0
        }}>
          从理解到创作，从灵感到旋律
          <br />
          你的专属音乐创作伙伴
        </Paragraph>
      </div>

      <Row gutter={[32, 32]} style={{ 
        width: '100%',
        maxWidth: '1200px',
        zIndex: 1
      }}>
        {features.map((feature, index) => (
          <Col xs={24} sm={24} md={8} key={index}>
            <Card
              hoverable
              style={{
                height: 'auto',
                textAlign: 'center',
                background: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(10px)',
                border: `3px solid ${feature.color}`,
                borderRadius: 24,
                transition: 'all 0.3s ease',
                cursor: 'pointer',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
              }}
              onClick={() => navigate(feature.path)}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-12px) scale(1.05)';
                e.currentTarget.style.boxShadow = `0 20px 48px ${feature.color}60`;
                e.currentTarget.style.borderColor = feature.color;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0) scale(1)';
                e.currentTarget.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.1)';
                e.currentTarget.style.borderColor = feature.color;
              }}
            >
              <div style={{ marginBottom: 24, fontSize: 64 }}>
                {feature.icon}
              </div>
              <Title level={3} style={{ 
                color: feature.color,
                marginBottom: 16,
                fontSize: 26,
                fontWeight: 600
              }}>
                {feature.title}
              </Title>
              <Paragraph style={{ 
                color: '#666', 
                fontSize: 15,
                lineHeight: 1.7,
                marginBottom: 24,
                minHeight: 48
              }}>
                {feature.description}
              </Paragraph>
              <Button
                type="primary"
                shape="round"
                size="large"
                style={{ 
                  background: `linear-gradient(135deg, ${feature.color} 0%, ${feature.color}dd 100%)`,
                  border: 'none',
                  boxShadow: `0 6px 20px ${feature.color}50`,
                  height: 48,
                  fontSize: 16,
                  fontWeight: 600,
                  width: '100%'
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
    </div>
  );
};

export default HomePage;
