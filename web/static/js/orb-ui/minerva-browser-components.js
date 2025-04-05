/**
 * Minerva Browser Components
 * 
 * This file contains browser-compatible versions of the MinervaUI components
 * using React.createElement() instead of JSX to avoid the need for transpilation.
 */

// Make sure React is defined
if (typeof React === 'undefined') {
  console.error('React is not loaded. Please load React before loading this file.');
}

// Create a namespace for our components
window.MinervaComponents = {};

(function() {
  const e = React.createElement;
  const { useState, useRef, useEffect } = React;
  
  // The core Orb component
  function Orb(props) {
    const { position = [0, 0, 0], color = '#4a6bdf', scale = [1, 1, 1], onClick, pulsate = false, label = null } = props;
    const ref = useRef();
    const [hovered, setHovered] = useState(false);
    const [glowIntensity, setGlowIntensity] = useState(1);
    
    useEffect(() => {
      // Simple glow effect simulation
      if (pulsate) {
        const interval = setInterval(() => {
          setGlowIntensity(prev => 0.8 + Math.sin(Date.now() / 500) * 0.2);
        }, 50);
        return () => clearInterval(interval);
      }
    }, [pulsate]);
    
    return e('div', {
      className: `orbital-element ${pulsate ? 'pulsating' : ''}`,
      style: {
        width: `${scale[0] * 50}px`,
        height: `${scale[1] * 50}px`,
        background: `radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.8), ${color})`,
        boxShadow: `0 0 ${20 * glowIntensity}px ${color}`,
        position: 'absolute',
        left: `${position[0]}px`,
        top: `${position[1]}px`,
        transform: 'translate(-50%, -50%)'
      },
      onClick: onClick,
      onMouseEnter: () => setHovered(true),
      onMouseLeave: () => setHovered(false)
    }, [
      label && e('div', {
        className: 'orb-label',
        style: {
          position: 'absolute',
          bottom: '-25px',
          left: '50%',
          transform: 'translateX(-50%)',
          whiteSpace: 'nowrap'
        }
      }, label)
    ]);
  }
  
  // Think Tank Model component
  function ThinkTankModel(props) {
    const { model, active, onClick } = props;
    
    return e('div', {
      className: `think-tank-model ${active ? 'active-model' : ''}`,
      onClick: onClick
    }, [
      // Model header
      e('div', { key: 'header', className: 'model-header' }, [
        // Model name
        e('div', { key: 'name', className: 'model-name' }, [
          model.name,
          active && e('div', {
            key: 'status',
            className: `model-status status-${props.state || 'active'}`
          }, props.state === 'thinking' ? 'Thinking' : props.state === 'processing' ? 'Processing' : 'Active')
        ]),
        
        // Score
        e('div', { key: 'score', className: 'model-score' }, `${model.score.toFixed(1)}`)
      ]),
      
      // Metrics
      e('div', { key: 'metrics', className: 'model-metrics' }, 
        Object.entries(model.metrics || {}).map(([key, value], i) => 
          e('div', { key: i, className: 'model-metric' }, `${key}: ${value}`)
        )
      ),
      
      // Capabilities
      e('div', { key: 'capabilities', className: 'model-capabilities' },
        (model.capabilities || []).map((cap, i) => 
          e('div', { key: i, className: 'model-capability' }, cap)
        )
      )
    ]);
  }
  
  // Think Tank Widget component
  function ThinkTankWidget(props) {
    const { position = [0, 0, 0], expanded = true, active = false, state = 'idle', data = [] } = props;
    const [isExpanded, setIsExpanded] = useState(expanded);
    
    return e('div', {
      className: 'widget-container',
      style: {
        position: 'absolute',
        left: `${position[0]}px`,
        top: `${position[1]}px`,
        transform: 'translate(-50%, -50%)',
        width: isExpanded ? '300px' : '150px',
        opacity: active ? 1 : 0.7
      }
    }, [
      // Widget header
      e('div', { key: 'header', className: 'widget-header' }, [
        e('div', { key: 'title', className: 'widget-title' }, [
          e('i', { key: 'icon', className: 'fas fa-brain' }),
          'Think Tank'
        ]),
        e('div', {
          key: 'expand',
          className: 'widget-expand-btn',
          onClick: () => setIsExpanded(!isExpanded)
        }, isExpanded ? 'Collapse' : 'Expand')
      ]),
      
      // Widget content - only show if expanded
      isExpanded && e('div', { key: 'content', className: 'widget-content' }, [
        // Status indicator
        e('div', {
          key: 'status',
          style: {
            padding: '5px',
            marginBottom: '10px',
            fontSize: '12px',
            background: state === 'idle' ? 'rgba(74, 107, 223, 0.2)' : 
                      state === 'thinking' ? 'rgba(111, 66, 193, 0.2)' : 
                      'rgba(20, 195, 142, 0.2)',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center'
          }
        }, [
          e('i', { 
            key: 'icon',
            className: `fas fa-${state === 'idle' ? 'brain' : 
                              state === 'thinking' ? 'spinner fa-spin' : 
                              'cog fa-spin'}`,
            style: { marginRight: '8px' }
          }),
          `Status: ${state.charAt(0).toUpperCase() + state.slice(1)}`
        ]),
        
        // Models
        ...(data || []).map((model, index) => 
          e(ThinkTankModel, {
            key: `model-${index}`,
            model: model,
            active: model.active,
            state: state,
            onClick: () => console.log(`Model ${model.name} clicked`)
          })
        ),
        
        // Empty state
        data.length === 0 && e('div', {
          key: 'empty',
          style: {
            padding: '20px',
            textAlign: 'center',
            color: 'rgba(255, 255, 255, 0.5)',
            fontStyle: 'italic'
          }
        }, 'No model data available')
      ])
    ]);
  }
  
  // Main Minerva UI component
  function MinervaUI(props) {
    const { projectOrbs = [], thinkTankData = [] } = props;
    const [activeProjectIndex, setActiveProjectIndex] = useState(null);
    const [minervaState, setMinervaState] = useState('idle'); // idle, thinking, processing
    const [thinkTankModels, setThinkTankModels] = useState(thinkTankData);
    
    const handleProjectClick = (index) => {
      setActiveProjectIndex(index === activeProjectIndex ? null : index);
    };
    
    const handleTabClick = (tabName) => {
      console.log(`${tabName} clicked`);
      
      if (tabName === 'Think Tank') {
        // Simulate think tank workflow
        setMinervaState('thinking');
        
        // Update models to active after delay
        setTimeout(() => {
          setThinkTankModels(prev => 
            prev.map(model => ({ ...model, active: true }))
          );
          
          // After 3 seconds, transition to processing state
          setTimeout(() => {
            setMinervaState('processing');
            
            // After 2 more seconds, return to idle state
            setTimeout(() => {
              setMinervaState('idle');
              setThinkTankModels(prev => 
                prev.map(model => ({ ...model, active: false }))
              );
            }, 2000);
          }, 3000);
        }, 1000);
      }
    };
    
    const containerStyle = {
      width: '100%',
      height: '100%',
      position: 'relative',
      background: 'linear-gradient(to bottom, #0a0a1a, #1a1a3a)',
      borderRadius: '5px',
      overflow: 'hidden'
    };
    
    return e('div', { style: containerStyle }, [
      // Center Orb
      e(Orb, {
        key: 'center-orb',
        position: [400, 250, 0],
        color: '#6f42c1',
        scale: [3, 3, 3],
        pulsate: minervaState !== 'idle',
        onClick: () => console.log('Center orb clicked')
      }),
      
      // Project Orbs
      ...(projectOrbs || []).map((project, index) => 
        e(Orb, {
          key: `project-${index}`,
          position: [
            400 + Math.cos(index * (2 * Math.PI / projectOrbs.length)) * 200,
            250 + Math.sin(index * (2 * Math.PI / projectOrbs.length)) * 200,
            0
          ],
          color: '#4a6bdf',
          scale: [1.5, 1.5, 1.5],
          label: project.name,
          pulsate: index === activeProjectIndex,
          onClick: () => handleProjectClick(index)
        })
      ),
      
      // Control Tabs
      e('div', {
        key: 'control-tabs',
        className: 'control-ring',
        style: {
          position: 'absolute',
          bottom: '20px',
          left: '50%',
          transform: 'translateX(-50%)',
          display: 'flex',
          gap: '15px'
        }
      }, [
        ['Dashboard', 'home'],
        ['Projects', 'folder-open'],
        ['Think Tank', 'brain'],
        ['Settings', 'cog']
      ].map(([label, icon], index) => 
        e('div', {
          key: `tab-${index}`,
          className: `control-tab ${label === 'Think Tank' && minervaState !== 'idle' ? 'active-tab' : ''}`,
          onClick: () => handleTabClick(label)
        }, [
          e('i', { key: 'icon', className: `fas fa-${icon}` }),
          e('span', { key: 'label' }, label)
        ])
      )),
      
      // Think Tank Widget
      e(ThinkTankWidget, {
        key: 'think-tank-widget',
        position: [400, 400, 0],
        expanded: true,
        active: minervaState !== 'idle',
        state: minervaState,
        data: thinkTankModels
      })
    ]);
  }

  // Export components to the global namespace
  window.MinervaComponents.Orb = Orb;
  window.MinervaComponents.ThinkTankModel = ThinkTankModel;
  window.MinervaComponents.ThinkTankWidget = ThinkTankWidget;
  window.MinervaComponents.MinervaUI = MinervaUI;
  
  // For compatibility with our adapter script
  window.MinervaUI = MinervaUI;
  
  console.log('Minerva browser components loaded successfully');
})();
