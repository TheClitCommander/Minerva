import React, { useState } from 'react';

// Speed Tabs Component - Quick access buttons around the orbital UI perimeter
export function SpeedTabs() {
  const [activeTab, setActiveTab] = useState(null);
  
  // Define speed tabs with their positions around the perimeter
  const speedTabs = [
    { id: 'settings', icon: 'cog', label: 'Settings', position: 'top', color: '#4a6bdf' },
    { id: 'analytics', icon: 'chart-bar', label: 'Analytics', position: 'top-right', color: '#17a2b8' },
    { id: 'memory', icon: 'database', label: 'Memory', position: 'right', color: '#ffc107' },
    { id: 'tutorials', icon: 'book', label: 'Tutorials', position: 'bottom-right', color: '#28a745' },
    { id: 'search', icon: 'search', label: 'Search', position: 'bottom', color: '#dc3545' },
    { id: 'models', icon: 'brain', label: 'Models', position: 'bottom-left', color: '#6f42c1' },
    { id: 'tools', icon: 'tools', label: 'Tools', position: 'left', color: '#fd7e14' },
    { id: 'profile', icon: 'user', label: 'Profile', position: 'top-left', color: '#e83e8c' }
  ];
  
  // Handle tab click
  const handleTabClick = (tabId) => {
    setActiveTab(tabId === activeTab ? null : tabId);
    console.log(`Speed tab clicked: ${tabId}`);
    // Future: Navigate to tab content or open panel
  };
  
  // Calculate position styles based on tab position property
  const getPositionStyle = (position) => {
    switch (position) {
      case 'top':
        return { top: '5%', left: '50%', transform: 'translateX(-50%)' };
      case 'top-right':
        return { top: '15%', right: '15%' };
      case 'right':
        return { top: '50%', right: '5%', transform: 'translateY(-50%)' };
      case 'bottom-right':
        return { bottom: '15%', right: '15%' };
      case 'bottom':
        return { bottom: '5%', left: '50%', transform: 'translateX(-50%)' };
      case 'bottom-left':
        return { bottom: '15%', left: '15%' };
      case 'left':
        return { top: '50%', left: '5%', transform: 'translateY(-50%)' };
      case 'top-left':
        return { top: '15%', left: '15%' };
      default:
        return {};
    }
  };
  
  return (
    <div className="speed-tabs-container">
      {speedTabs.map((tab) => {
        const positionStyle = getPositionStyle(tab.position);
        const isActive = activeTab === tab.id;
        
        return (
          <div 
            key={tab.id}
            className={`speed-tab ${isActive ? 'active' : ''}`}
            style={{
              ...positionStyle,
              position: 'absolute',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              cursor: 'pointer',
              zIndex: 10,
              transition: 'all 0.3s ease'
            }}
            onClick={() => handleTabClick(tab.id)}
          >
            <div 
              className="speed-tab-icon"
              style={{
                width: '50px',
                height: '50px',
                borderRadius: '50%',
                backgroundColor: 'rgba(0, 0, 0, 0.7)',
                border: `2px solid ${tab.color}`,
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                color: tab.color,
                boxShadow: isActive ? `0 0 15px ${tab.color}` : 'none',
                transition: 'all 0.3s ease'
              }}
            >
              <i className={`fas fa-${tab.icon}`} style={{ fontSize: '20px' }}></i>
            </div>
            
            <div 
              className="speed-tab-label"
              style={{
                marginTop: '5px',
                padding: '3px 8px',
                backgroundColor: 'rgba(0, 0, 0, 0.7)',
                borderRadius: '3px',
                color: 'white',
                fontSize: '0.8rem',
                opacity: isActive ? 1 : 0,
                transform: isActive ? 'translateY(0)' : 'translateY(-5px)',
                transition: 'all 0.3s ease'
              }}
            >
              {tab.label}
            </div>
            
            {isActive && (
              <div 
                className="speed-tab-panel"
                style={{
                  position: 'absolute',
                  top: '60px',
                  width: '250px',
                  padding: '15px',
                  backgroundColor: 'rgba(0, 0, 0, 0.8)',
                  borderRadius: '5px',
                  border: `1px solid ${tab.color}`,
                  color: 'white',
                  boxShadow: `0 0 15px rgba(0, 0, 0, 0.5)`,
                  zIndex: 20,
                  // Adjust position based on tab location to keep panel visible
                  ...(tab.position.includes('right') ? { right: 0 } : {}),
                  ...(tab.position.includes('bottom') ? { bottom: '60px', top: 'auto' } : {})
                }}
              >
                <h3 style={{ color: tab.color, marginTop: 0 }}>{tab.label}</h3>
                <div style={{ fontSize: '0.9rem' }}>
                  {tab.id === 'settings' && (
                    <div>
                      <div className="setting-item">
                        <span>Dark Mode</span>
                        <label className="toggle">
                          <input type="checkbox" defaultChecked={true} />
                          <span className="slider"></span>
                        </label>
                      </div>
                      <div className="setting-item">
                        <span>Animation Speed</span>
                        <input type="range" min="0" max="10" defaultValue="5" />
                      </div>
                      <div className="setting-item">
                        <span>Notifications</span>
                        <label className="toggle">
                          <input type="checkbox" defaultChecked={true} />
                          <span className="slider"></span>
                        </label>
                      </div>
                    </div>
                  )}
                  
                  {tab.id === 'models' && (
                    <div>
                      <div className="model-item">
                        <span className="model-name">GPT-4</span>
                        <span className="model-status active">Active</span>
                      </div>
                      <div className="model-item">
                        <span className="model-name">Claude 3</span>
                        <span className="model-status active">Active</span>
                      </div>
                      <div className="model-item">
                        <span className="model-name">Gemini</span>
                        <span className="model-status">Standby</span>
                      </div>
                      <div className="model-item">
                        <span className="model-name">Mistral</span>
                        <span className="model-status">Standby</span>
                      </div>
                    </div>
                  )}
                  
                  {tab.id === 'analytics' && (
                    <div>
                      <div className="stat-item">
                        <span>API Usage</span>
                        <div className="progress-bar">
                          <div className="progress" style={{ width: '65%', backgroundColor: '#17a2b8' }}></div>
                        </div>
                      </div>
                      <div className="stat-item">
                        <span>Response Time</span>
                        <div className="progress-bar">
                          <div className="progress" style={{ width: '80%', backgroundColor: '#28a745' }}></div>
                        </div>
                      </div>
                      <div className="stat-item">
                        <span>Projects Active</span>
                        <div className="stat-value">3/5</div>
                      </div>
                    </div>
                  )}
                  
                  {(tab.id !== 'settings' && tab.id !== 'models' && tab.id !== 'analytics') && (
                    <div>
                      Quick access controls for {tab.label} will appear here.
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
