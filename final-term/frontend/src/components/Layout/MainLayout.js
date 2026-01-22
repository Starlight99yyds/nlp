import React, { useState } from 'react';
import { Layout, Menu, theme } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  HomeOutlined,
  BarChartOutlined,
  EditOutlined,
  HeartOutlined,
  HistoryOutlined
} from '@ant-design/icons';

const { Header, Sider } = Layout;

const MainLayout = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  // 主题配置（如果需要使用主题颜色，可以取消注释）
  // const {
  //   token: { colorBgContainer },
  // } = theme.useToken();

  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: '首页',
    },
    {
      key: '/analysis',
      icon: <BarChartOutlined />,
      label: '基础分析',
    },
    {
      key: '/generation',
      icon: <EditOutlined />,
      label: '创作助手',
    },
    {
      key: '/recommendation',
      icon: <HeartOutlined />,
      label: '智能推荐',
    },
    {
      key: '/history',
      icon: <HistoryOutlined />,
      label: '历史记录',
    },
  ];

  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="light"
        width={200}
      >
        <div style={{ 
          height: 64, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          fontSize: collapsed ? 20 : 18,
          fontWeight: 'bold',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          borderRadius: collapsed ? '50%' : '8px',
          margin: collapsed ? '8px' : '16px',
          width: collapsed ? 48 : 'auto',
          minHeight: collapsed ? 48 : 64
        }}>
          {collapsed ? '🎵' : '旋律工坊'}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout>
        <Header style={{ 
          padding: '0 24px', 
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          display: 'flex',
          alignItems: 'center',
          fontSize: 20,
          fontWeight: 'bold',
          color: 'white',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          旋律工坊 - 智能音乐创作平台
        </Header>
        {children}
      </Layout>
    </Layout>
  );
};

export default MainLayout;



