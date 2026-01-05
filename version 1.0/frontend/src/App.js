import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import MainLayout from './components/Layout/MainLayout';
import HomePage from './pages/HomePage';
import AnalysisPage from './pages/AnalysisPage';
import GenerationPage from './pages/GenerationPage';
import RecommendationPage from './pages/RecommendationPage';
import HistoryPage from './pages/HistoryPage';
import './App.css';

const { Content } = Layout;

function App() {
  return (
    <Router>
      <MainLayout>
        <Content style={{ padding: '24px', minHeight: 'calc(100vh - 64px)' }}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/analysis" element={<AnalysisPage />} />
            <Route path="/generation" element={<GenerationPage />} />
            <Route path="/recommendation" element={<RecommendationPage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
        </Content>
      </MainLayout>
    </Router>
  );
}

export default App;







