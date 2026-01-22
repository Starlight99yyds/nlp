import React, { useState, useEffect, useRef } from 'react';
import { Card, Button, Space, Typography } from 'antd';
import { PlayCircleOutlined, PauseCircleOutlined, SoundOutlined } from '@ant-design/icons';

const { Text } = Typography;

// 全局音频播放器上下文
let globalAudioRef = null;
let globalAudioState = {
  src: null,
  playing: false,
  currentTime: 0,
  duration: 0,
  title: null
};

// 设置全局音频引用
export const setGlobalAudioRef = (ref) => {
  globalAudioRef = ref;
};

// 获取全局音频引用
export const getGlobalAudioRef = () => {
  return globalAudioRef;
};

// 设置全局音频状态
export const setGlobalAudioState = (state) => {
  globalAudioState = { ...globalAudioState, ...state };
  // 触发自定义事件通知组件更新
  window.dispatchEvent(new CustomEvent('globalAudioStateChanged', { detail: globalAudioState }));
};

// 获取全局音频状态
export const getGlobalAudioState = () => {
  return globalAudioState;
};

const GlobalAudioPlayer = () => {
  const [audioState, setAudioState] = useState(globalAudioState);
  const audioRef = useRef(null);
  const intervalRef = useRef(null);

  useEffect(() => {
    // 注册全局音频引用
    setGlobalAudioRef(audioRef.current);

    // 定期更新状态
    intervalRef.current = setInterval(() => {
      if (audioRef.current) {
        const newState = {
          src: audioRef.current.src || null,
          playing: !audioRef.current.paused,
          currentTime: audioRef.current.currentTime || 0,
          duration: audioRef.current.duration || 0,
          title: globalAudioState.title
        };
        setAudioState(newState);
        setGlobalAudioState(newState);
      }
    }, 100);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  // 监听全局音频状态变化
  useEffect(() => {
    const handleStateChange = (event) => {
      const state = event.detail;
      setAudioState(state);
      
      if (audioRef.current) {
        if (state.src && audioRef.current.src !== state.src) {
          audioRef.current.src = state.src;
          audioRef.current.load();
        }
        if (state.playing && audioRef.current.paused) {
          audioRef.current.play().catch(console.error);
        } else if (!state.playing && !audioRef.current.paused) {
          audioRef.current.pause();
        }
      }
    };

    window.addEventListener('globalAudioStateChanged', handleStateChange);
    
    // 定期同步状态
    const interval = setInterval(() => {
      const state = getGlobalAudioState();
      if (audioRef.current && state.src) {
        setAudioState({
          ...state,
          currentTime: audioRef.current.currentTime || 0,
          duration: audioRef.current.duration || 0
        });
      }
    }, 100);

    return () => {
      window.removeEventListener('globalAudioStateChanged', handleStateChange);
      clearInterval(interval);
    };
  }, []);

  const handlePlayPause = () => {
    if (audioRef.current) {
      if (audioRef.current.paused) {
        audioRef.current.play().catch(console.error);
      } else {
        audioRef.current.pause();
      }
    }
  };

  // 如果没有音频源，不显示播放器
  if (!audioState.src) {
    return null;
  }

  const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <Card
      style={{
        position: 'fixed',
        bottom: 20,
        right: 20,
        width: 320,
        zIndex: 1000,
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        borderRadius: 12,
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        border: 'none'
      }}
      bodyStyle={{ padding: '12px 16px' }}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="small">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Space>
            <Button
              type="text"
              icon={audioState.playing ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
              onClick={handlePlayPause}
              style={{ color: 'white', fontSize: 24 }}
            />
            <div>
              <Text style={{ color: 'white', fontSize: 12, display: 'block' }}>
                {audioState.title || '正在播放'}
              </Text>
              <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: 11 }}>
                {formatTime(audioState.currentTime)} / {formatTime(audioState.duration)}
              </Text>
            </div>
          </Space>
          <SoundOutlined style={{ color: 'white', fontSize: 20 }} />
        </div>
        <audio
          ref={audioRef}
          style={{ display: 'none' }}
          onTimeUpdate={(e) => {
            const audio = e.target;
            setAudioState({
              ...audioState,
              currentTime: audio.currentTime,
              duration: audio.duration
            });
          }}
          onEnded={() => {
            setAudioState({ ...audioState, playing: false });
            setGlobalAudioState({ ...globalAudioState, playing: false });
          }}
        />
      </Space>
    </Card>
  );
};

export default GlobalAudioPlayer;

