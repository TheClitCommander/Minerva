import React, { useState } from 'react';

// Widgets Component - Customizable widgets at the bottom of the orbital UI
export function Widgets() {
  const [expandedWidget, setExpandedWidget] = useState(null);
  
  // Define available widgets
  const widgets = [
    { 
      id: 'api-usage', 
      title: 'API Usage', 
      icon: 'chart-line',
      color: '#17a2b8',
      content: <ApiUsageWidget />
    },
    { 
      id: 'think-tank', 
      title: 'Think Tank', 
      icon: 'brain',
      color: '#4a6bdf',
      content: <ThinkTankWidget />
    },
    { 
      id: 'upcoming', 
      title: 'Upcoming Events', 
      icon: 'calendar-alt',
      color: '#28a745',
      content: <UpcomingEventsWidget />
    },
    { 
      id: 'memory-usage', 
      title: 'Memory Usage', 
      icon: 'memory',
      color: '#ffc107',
      content: <MemoryUsageWidget />
    }
  ];
  
  // Handle widget expansion/collapse
  const toggleWidget = (widgetId) => {
    setExpandedWidget(expandedWidget === widgetId ? null : widgetId);
  };
  
  return (
    <div 
      className="widgets-container"
      style={{
        position: 'absolute',
        bottom: '20px',
        left: '50%',
        transform: 'translateX(-50%)',
        display: 'flex',
        gap: '15px',
        zIndex: 30
      }}
    >
      {widgets.map((widget) => {
        const isExpanded = expandedWidget === widget.id;
        
        return (
          <div 
            key={widget.id}
            className={`widget ${isExpanded ? 'expanded' : ''}`}
            style={{
              width: isExpanded ? '300px' : '160px',
              height: isExpanded ? '250px' : '60px',
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              borderRadius: '6px',
              border: `1px solid ${widget.color}`,
              boxShadow: isExpanded ? `0 0 15px rgba(0, 0, 0, 0.5)` : 'none',
              transition: 'all 0.3s ease',
              overflow: 'hidden'
            }}
          >
            <div 
              className="widget-header"
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '10px 15px',
                borderBottom: isExpanded ? `1px solid ${widget.color}` : 'none',
                cursor: 'pointer'
              }}
              onClick={() => toggleWidget(widget.id)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <i 
                  className={`fas fa-${widget.icon}`} 
                  style={{ color: widget.color, fontSize: '18px' }}
                ></i>
                <span style={{ color: 'white', fontSize: '0.9rem', fontWeight: 'bold' }}>
                  {widget.title}
                </span>
              </div>
              
              <i 
                className={`fas fa-chevron-${isExpanded ? 'down' : 'up'}`} 
                style={{ color: widget.color, fontSize: '14px' }}
              ></i>
            </div>
            
            <div 
              className="widget-content"
              style={{
                padding: isExpanded ? '15px' : '0px',
                opacity: isExpanded ? 1 : 0,
                height: isExpanded ? 'calc(100% - 60px)' : '0px',
                transition: 'all 0.3s ease',
                overflow: 'hidden'
              }}
            >
              {widget.content}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// API Usage Widget Component
function ApiUsageWidget() {
  // Sample API usage data
  const apiUsage = [
    { model: 'GPT-4', usage: 75, color: '#FF5733' },
    { model: 'Claude', usage: 60, color: '#33FF57' },
    { model: 'Gemini', usage: 40, color: '#3357FF' },
    { model: 'Mistral', usage: 25, color: '#F3FF33' }
  ];
  
  return (
    <div style={{ color: 'white', height: '100%' }}>
      <div style={{ fontSize: '0.8rem', marginBottom: '10px' }}>
        Monthly usage: <span style={{ color: '#17a2b8', fontWeight: 'bold' }}>65%</span>
      </div>
      
      {apiUsage.map((api) => (
        <div key={api.model} style={{ marginBottom: '8px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
            <span style={{ fontSize: '0.8rem' }}>{api.model}</span>
            <span style={{ fontSize: '0.8rem' }}>{api.usage}%</span>
          </div>
          <div 
            className="api-progress"
            style={{
              height: '6px',
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '3px',
              overflow: 'hidden'
            }}
          >
            <div
              className="api-bar"
              style={{
                width: `${api.usage}%`,
                height: '100%',
                backgroundColor: api.color,
                borderRadius: '3px'
              }}
            ></div>
          </div>
        </div>
      ))}
      
      <div style={{ fontSize: '0.8rem', marginTop: '15px', color: '#aaa' }}>
        <i className="fas fa-info-circle"></i> Think Tank enabled
      </div>
    </div>
  );
}

// Think Tank Widget Component
function ThinkTankWidget() {
  return (
    <div style={{ color: 'white', height: '100%' }}>
      <div style={{ fontSize: '0.8rem', marginBottom: '15px' }}>
        <span style={{ color: '#4a6bdf', fontWeight: 'bold' }}>Active Models:</span>
      </div>
      
      <div className="model-ranking" style={{ marginBottom: '15px' }}>
        {[
          { name: 'GPT-4', score: 92, strengths: 'Technical', color: '#FF5733' },
          { name: 'Claude-3', score: 89, strengths: 'Reasoning', color: '#33FF57' },
          { name: 'Gemini', score: 85, strengths: 'Research', color: '#3357FF' },
          { name: 'Mistral', score: 79, strengths: 'Efficiency', color: '#F3FF33' }
        ].map((model, index) => (
          <div 
            key={model.name}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '5px 0',
              borderBottom: index < 3 ? '1px solid rgba(255, 255, 255, 0.1)' : 'none'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <div 
                style={{ 
                  width: '10px', 
                  height: '10px', 
                  borderRadius: '50%', 
                  backgroundColor: model.color 
                }}
              ></div>
              <span style={{ fontSize: '0.8rem' }}>{model.name}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.7rem', color: '#aaa' }}>{model.strengths}</span>
              <span style={{ fontSize: '0.8rem', color: '#fff', fontWeight: 'bold' }}>{model.score}</span>
            </div>
          </div>
        ))}
      </div>
      
      <div style={{ fontSize: '0.8rem', color: '#4a6bdf' }}>
        <i className="fas fa-magic"></i> Response Blending: <span style={{ color: 'white' }}>Enabled</span>
      </div>
    </div>
  );
}

// Upcoming Events Widget Component
function UpcomingEventsWidget() {
  return (
    <div style={{ color: 'white', height: '100%', overflow: 'auto' }}>
      {[
        { title: 'Project Deadline', time: '2025-03-15', project: 'AI Assistant', priority: 'high' },
        { title: 'Weekly Meeting', time: '2025-03-12 10:00', project: 'Finance AI', priority: 'medium' },
        { title: 'Code Review', time: '2025-03-13 14:30', project: 'Web Research', priority: 'normal' }
      ].map((event, index) => (
        <div
          key={index}
          style={{
            padding: '8px 0',
            borderBottom: index < 2 ? '1px solid rgba(255, 255, 255, 0.1)' : 'none',
            display: 'flex',
            flexDirection: 'column',
            gap: '3px'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>{event.title}</span>
            <span 
              style={{ 
                fontSize: '0.7rem', 
                padding: '2px 5px', 
                borderRadius: '3px', 
                backgroundColor: 
                  event.priority === 'high' ? 'rgba(220, 53, 69, 0.2)' : 
                  event.priority === 'medium' ? 'rgba(255, 193, 7, 0.2)' : 
                  'rgba(40, 167, 69, 0.2)',
                color:
                  event.priority === 'high' ? '#dc3545' : 
                  event.priority === 'medium' ? '#ffc107' : 
                  '#28a745'
              }}
            >
              {event.priority}
            </span>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#aaa' }}>
            <i className="far fa-clock"></i> {event.time}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#ddd' }}>
            <i className="fas fa-project-diagram"></i> {event.project}
          </div>
        </div>
      ))}
    </div>
  );
}

// Memory Usage Widget Component
function MemoryUsageWidget() {
  return (
    <div style={{ color: 'white', height: '100%' }}>
      <div style={{ fontSize: '0.8rem', marginBottom: '15px' }}>
        <span style={{ color: '#ffc107', fontWeight: 'bold' }}>Memory System:</span> <span style={{ color: 'white' }}>Optimized</span>
      </div>
      
      <div style={{ marginBottom: '15px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
          <span style={{ fontSize: '0.8rem' }}>Total Records</span>
          <span style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>152</span>
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
          <span style={{ fontSize: '0.8rem' }}>Cache Health</span>
          <span style={{ fontSize: '0.8rem', color: '#28a745' }}>Excellent</span>
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
          <span style={{ fontSize: '0.8rem' }}>Response Time</span>
          <span style={{ fontSize: '0.8rem' }}>45ms</span>
        </div>
      </div>
      
      <div style={{ fontSize: '0.8rem', marginBottom: '10px' }}>Memory by Category:</div>
      
      {[
        { category: 'User Preferences', count: 48, color: '#4a6bdf' },
        { category: 'Project Context', count: 65, color: '#28a745' },
        { category: 'Technical Specs', count: 39, color: '#dc3545' }
      ].map((item) => (
        <div key={item.category} style={{ marginBottom: '5px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
            <span style={{ fontSize: '0.75rem' }}>{item.category}</span>
            <span style={{ fontSize: '0.75rem' }}>{item.count}</span>
          </div>
          <div 
            style={{
              height: '5px',
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '3px',
              overflow: 'hidden'
            }}
          >
            <div
              style={{
                width: `${(item.count / 152) * 100}%`,
                height: '100%',
                backgroundColor: item.color,
                borderRadius: '3px'
              }}
            ></div>
          </div>
        </div>
      ))}
    </div>
  );
}
