// MinervaUI.jsx - The main 3D orbital interface for Minerva with project orbs stationary and agent orbs orbiting
// MinervaUI.jsx - 3D orbital interface with stationary projects and orbiting agents
import React, { useRef, useEffect, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Text, Html } from '@react-three/drei';
import * as THREE from 'three';

// The core Orb component with glow effect
function Orb({ position, color, scale, onClick, pulsate = false, label = null }) {
  const ref = useRef();
  const [hovered, setHovered] = useState(false);
  const [pulseScale, setPulseScale] = useState(1);
  
  // Handle self-rotation and pulsating animation if enabled
  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y += 0.005;
      
      // Enhanced pulsating effect with dynamic glow
      if (pulsate) {
        const pulse = Math.sin(state.clock.elapsedTime * 2) * 0.05 + 1;
        setPulseScale(pulse);
        
        // Adjust glow intensity dynamically
        if (ref.current.material) {
          const glowIntensity = 0.8 + Math.sin(state.clock.elapsedTime * 3) * 0.2;
          ref.current.material.emissiveIntensity = glowIntensity;
        }
      } else if (ref.current.material) {
        // Default glow for non-pulsating orbs
        ref.current.material.emissiveIntensity = 0.5;
      }
    }
  });
  
  // Calculate final scale including pulse effect
  const finalScale = scale.map(s => s * (pulsate ? pulseScale : 1));
  
  return (
    <group position={position}>
      <mesh 
        ref={ref} 
        scale={finalScale}
        onClick={onClick}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <sphereGeometry args={[1, 32, 32]} />
        <meshStandardMaterial 
          color={color} 
          emissive={color} 
          emissiveIntensity={hovered ? 0.8 : 0.5} 
          roughness={0.2}
        />
      </mesh>
      
      {/* Glow effect */}
      <mesh scale={[scale[0] * 1.2, scale[1] * 1.2, scale[2] * 1.2]}>
        <sphereGeometry args={[1, 16, 16]} />
        <meshStandardMaterial 
          color={color} 
          transparent={true} 
          opacity={0.15} 
          roughness={1}
        />
      </mesh>
      
      {/* Label if provided */}
      {label && (
        <Html position={[0, scale[1] * 1.5, 0]} center>
          <div style={{ 
            color: 'white', 
            background: 'rgba(0,0,0,0.5)', 
            padding: '4px 8px', 
            borderRadius: '4px',
            fontSize: '12px',
            whiteSpace: 'nowrap'
          }}>
            {label}
          </div>
        </Html>
      )}
    </group>
  );
}

// Agent Orb component that orbits around its project orb in a lateral plane
function AgentOrb({ parentPosition, color, radius, speed, onClick, active = false, visible = false }) {
  const ref = useRef();
  const [angle, setAngle] = useState(Math.random() * Math.PI * 2); // Random starting position
  const [hovered, setHovered] = useState(false);
  const [clickable, setClickable] = useState(active);
  
  // Update clickable state when active prop changes
  useEffect(() => {
    setClickable(active);
  }, [active]);
  
  // Calculate orbital movement with enhanced moon-like orbits
  useFrame((state) => {
    if (ref.current) {
      // Smooth easing animation for orbit speed
      setAngle((prev) => prev + speed);
      
      // Update position in circular orbit - keeping it in a lateral plane
      ref.current.position.x = parentPosition[0] + radius * Math.cos(angle);
      // Small vertical oscillation for natural movement (tiny wave pattern)
      ref.current.position.y = parentPosition[1] + (Math.sin(angle * 0.3) * 0.3); 
      ref.current.position.z = parentPosition[2] + radius * Math.sin(angle);
      
      // Add slight orbit tilt effect for aesthetic depth
      ref.current.rotation.y += 0.01;
      ref.current.rotation.x = Math.sin(angle) * 0.05;
      ref.current.rotation.z = Math.cos(angle) * 0.03;
    }
  });

  // If not visible, don't render
  if (!visible) return null;

  return (
    <mesh 
      ref={ref} 
      scale={[0.5, 0.5, 0.5]}
      onClick={clickable ? onClick : null}
      onPointerOver={() => clickable && setHovered(true)}
      onPointerOut={() => setHovered(false)}
      cursor={clickable ? 'pointer' : 'default'}
    >
      <sphereGeometry args={[1, 24, 24]} />
      <meshStandardMaterial 
        color={color} 
        emissive={color} 
        emissiveIntensity={hovered ? 0.9 : 0.6} 
        roughness={0.3}
      />
      
      {/* Subtle glow for agents */}
      <pointLight 
        color={color} 
        intensity={0.5} 
        distance={1.5} 
        decay={2} 
      />
    </mesh>
  );
}

// Project Orb component with gentle floating motion and orbiting agents
function ProjectOrb({ position, agents, color, name = null, active = false, onClick }) {
  const ref = useRef();
  const [isActive, setIsActive] = useState(active);
  const [basePosition] = useState([...position]); // Store initial position
  
  // Update isActive state when active prop changes
  useEffect(() => {
    setIsActive(active);
  }, [active]);
  
  // Add gentle floating motion
  useFrame((state) => {
    if (ref.current) {
      // Gentle floating effect with different frequencies for each axis
      ref.current.position.y = basePosition[1] + Math.sin(state.clock.elapsedTime * 0.4) * 0.2;
      
      // Subtle lateral movement
      ref.current.position.x = basePosition[0] + Math.sin(state.clock.elapsedTime * 0.2) * 0.05;
      ref.current.position.z = basePosition[2] + Math.cos(state.clock.elapsedTime * 0.3) * 0.05;
    }
  });
  
  // Handle interaction with the project orb
  const handleClick = (e) => {
    e.stopPropagation();
    setIsActive(!isActive);
    if (onClick) onClick(e);
  };
  
  return (
    <group ref={ref} position={basePosition}>
      {/* The main project orb */}
      <Orb 
        position={[0, 0, 0]} 
        color={color} 
        scale={[1.5, 1.5, 1.5]} 
        onClick={handleClick} 
        pulsate={isActive}
        label={name}
      />
      
      {/* Agent orbs orbiting the project - only visible when project is active */}
      {agents && agents.map((agent, i) => {
        const baseSpeed = 0.01; // Slower base speed
        const speedVariation = 0.005; // Less variation between agents
        
        return (
          <AgentOrb 
            key={i} 
            parentPosition={position} 
            radius={2 + i * 0.5} // Increasing orbit radius for each agent
            speed={baseSpeed + speedVariation * i} 
            color={agent.color}
            active={isActive} // Agents become clickable when project is active
            visible={isActive} // Agents only visible when project is active
            onClick={() => console.log(`Agent ${i} clicked`)}
          />
        );
      })}
    </group>
  );
}

// Scene setup component for the starry background
function SceneSetup() {
  const { scene } = useThree();
  
  useEffect(() => {
    // Create a starry background
    const stars = new THREE.BufferGeometry();
    const starCount = 2000;
    const positions = new Float32Array(starCount * 3);
    
    for (let i = 0; i < starCount * 3; i += 3) {
      positions[i] = (Math.random() - 0.5) * 100;
      positions[i + 1] = (Math.random() - 0.5) * 100;
      positions[i + 2] = (Math.random() - 0.5) * 100;
    }
    
    stars.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    
    const starMaterial = new THREE.PointsMaterial({
      color: 0xffffff,
      size: 0.1,
      transparent: true,
      opacity: 0.8,
      sizeAttenuation: true
    });
    
    const starField = new THREE.Points(stars, starMaterial);
    scene.add(starField);
    
    return () => {
      scene.remove(starField);
      stars.dispose();
      starMaterial.dispose();
    };
  }, [scene]);
  
  return null;
}

// SpeedTab component for the perimeter around Minerva with enhanced visuals
function SpeedTab({ position, icon, label, onClick, hoveredRing, color = '#4a6bdf', active = false, notifications = 0 }) {
  const [hovered, setHovered] = useState(false);
  const ref = useRef();
  const glowRef = useRef();
  const pulseRef = useRef();
  
  // Add animations and effects based on state (hover, active, notifications)
  useFrame((state) => {
    if (ref.current) {
      // Base floating animation
      const baseFloat = Math.sin(state.clock.elapsedTime * 1.5) * 0.05;
      
      // Enhanced vertical motion for active tabs
      const activeBoost = active ? 0.05 : 0;
      ref.current.position.y = baseFloat + activeBoost;
      
      // Rotation effects
      if (hovered) {
        // More pronounced rotation when hovered
        ref.current.rotation.z = Math.sin(state.clock.elapsedTime * 4) * 0.1;
      } else if (active) {
        // Subtle continuous rotation for active tabs
        ref.current.rotation.z = Math.sin(state.clock.elapsedTime * 2) * 0.05;
      } else {
        // Gradually return to normal
        ref.current.rotation.z *= 0.9;
      }
    }
    
    // Enhanced neon glow effect
    if (glowRef.current && glowRef.current.material) {
      // Base glow pulse for all tabs
      const baseGlow = 0.5 + Math.sin(state.clock.elapsedTime * 2) * 0.2;
      
      // Increase intensity when hovered or active
      const hoverBoost = hovered ? 0.4 : 0;
      const activeBoost = active ? 0.3 : 0;
      
      // Apply combined glow effect
      glowRef.current.material.emissiveIntensity = baseGlow + hoverBoost + activeBoost;
      glowRef.current.material.opacity = 0.6 + (hovered ? 0.2 : 0) + (active ? 0.2 : 0);
    }
    
    // Enhanced notification pulse effect
    if (pulseRef.current && notifications > 0) {
      // Dynamic pulse speed and strength based on notification count
      const pulseSpeed = 2 + (notifications * 0.5); // Faster pulse with more notifications
      const pulseStrength = 0.15 + (notifications * 0.05); // Stronger pulse with more notifications
      
      // Create a more pronounced pulse effect
      const notificationPulse = 1 + Math.sin(state.clock.elapsedTime * pulseSpeed) * pulseStrength;
      pulseRef.current.scale.set(notificationPulse, notificationPulse, notificationPulse);
      
      // Pulsing opacity for attention-grabbing effect
      pulseRef.current.material.opacity = 0.7 + Math.sin(state.clock.elapsedTime * pulseSpeed) * 0.3;
      
      // Add color intensity variation if material has emissive property
      if (pulseRef.current.material.emissive) {
        const colorIntensity = 1.2 + Math.sin(state.clock.elapsedTime * pulseSpeed * 1.3) * 0.4;
        pulseRef.current.material.emissiveIntensity = colorIntensity;
      }
    }
    
    // We've already completely handled the glow effects in the enhanced neon glow section above
    // No additional glow effects needed here as they would conflict
  });
  
  // Calculate display properties based on state
  const getTabColor = () => {
    if (active) return color;
    if (hovered) return color;
    return '#2a4baf';
  };
  
  const getGlowColor = () => {
    if (notifications > 0) return '#dc3545'; // Red glow for notifications
    if (active) return color;
    return hoveredRing ? '#6a8bff' : '#3a5bdf';
  };
  
  const getScale = () => {
    if (active) return [0.7, 0.7, 0.15];
    return [0.6, 0.6, 0.1];
  };
  
  const getGlowScale = () => {
    if (active) return [0.85, 0.85, 0.05];
    if (notifications > 0) return [0.9, 0.9, 0.05];
    return [0.7, 0.7, 0.05];
  };
  
  const scale = getScale();
  const glowScale = getGlowScale();
  
  return (
    <group position={position}>
      <group ref={ref}>
        {/* Notification pulse effect (only shows if there are notifications) */}
        {notifications > 0 && (
          <mesh 
            ref={pulseRef}
            scale={[1, 1, 0.01]}
            renderOrder={0}
          >
            <circleGeometry args={[0.5, 16]} />
            <meshStandardMaterial 
              color="#dc3545" 
              emissive="#dc3545" 
              emissiveIntensity={0.7}
              transparent={true}
              opacity={0.3}
            />
          </mesh>
        )}
        
        {/* Glowing backdrop for the tab */}
        <mesh 
          ref={glowRef}
          scale={glowScale}
          renderOrder={1}
        >
          <boxGeometry args={[1, 1, 0.1]} />
          <meshStandardMaterial 
            color={getGlowColor()} 
            emissive={getGlowColor()} 
            emissiveIntensity={0.6}
            transparent={true}
            opacity={0.6}
          />
        </mesh>
        
        {/* Main tab */}
        <mesh 
          scale={scale}
          onClick={onClick}
          onPointerOver={() => setHovered(true)}
          onPointerOut={() => setHovered(false)}
          cursor="pointer"
          renderOrder={2}
        >
          <boxGeometry args={[1, 1, 0.3]} />
          <meshStandardMaterial 
            color={getTabColor()} 
            emissive={getTabColor()} 
            emissiveIntensity={active || hovered ? 0.8 : 0.5}
            metalness={0.5}
            roughness={0.2}
          />
        </mesh>
        
        <Html position={[0, 0, 0.2]} center>
          <div style={{ 
            color: 'white', 
            fontSize: '12px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            width: '40px',
            height: '40px',
            textShadow: '0 0 3px rgba(0,0,0,0.8)'
          }}>
            <i className={`fas ${icon}`} style={{ 
              fontSize: active ? '18px' : '16px',
              color: active ? 'white' : undefined,
              textShadow: active ? '0 0 5px rgba(255,255,255,0.8)' : undefined
            }}></i>
            
            {/* Show label when hovered or active */}
            {(hovered || active) && (
              <span style={{
                marginTop: '4px', 
                fontSize: '10px',
                fontWeight: active ? 'bold' : 'normal'
              }}>
                {label}
              </span>
            )}
            
            {/* Show notification count if any */}
            {notifications > 0 && (
              <div style={{ 
                position: 'absolute', 
                top: '-2px', 
                right: '-2px',
                background: '#dc3545',
                color: 'white',
                fontSize: '9px',
                fontWeight: 'bold',
                width: '14px',
                height: '14px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 3px rgba(0,0,0,0.5)'
              }}>
                {notifications}
              </div>
            )}
          </div>
        </Html>
      </group>
    </group>
  );
}

// ControlRing component that creates a circle of speed tabs around Minerva with activity-based effects
function ControlRing({ radius = 6, onTabClick }) {
  const [hovered, setHovered] = useState(false);
  const [activeTab, setActiveTab] = useState('Think Tank'); // Default active tab
  const ringRef = useRef();
  const pulseRef = useRef();
  
  // Define the tabs to display in the ring, with activity status and notification count
  const tabs = [
    { icon: 'fa-tachometer-alt', label: 'Dashboard', active: false, notifications: 0, color: '#4a6bdf' },
    { icon: 'fa-cube', label: 'Projects', active: false, notifications: 2, color: '#28a745' },
    { icon: 'fa-robot', label: 'Agents', active: false, notifications: 0, color: '#6f42c1' },
    { icon: 'fa-cog', label: 'Settings', active: false, notifications: 0, color: '#17a2b8' },
    { icon: 'fa-chart-line', label: 'Analytics', active: false, notifications: 1, color: '#fd7e14' },
    { icon: 'fa-file-alt', label: 'Logs', active: false, notifications: 3, color: '#dc3545' },
    { icon: 'fa-brain', label: 'Think Tank', active: true, notifications: 0, color: '#6f42c1' },
    { icon: 'fa-code', label: 'Workspace', active: false, notifications: 0, color: '#20c997' }
  ];
  
  // Handle tab click with active state tracking
  const handleTabClick = (label) => {
    setActiveTab(label);
    onTabClick(label);
  };
  
  // Rotate the entire ring slowly with pulsing effect
  useFrame((state) => {
    if (ringRef.current) {
      // Subtle rotation
      ringRef.current.rotation.z = Math.sin(state.clock.elapsedTime * 0.2) * 0.02;
    }
    
    if (pulseRef.current) {
      // Pulse effect for the outer ring
      const pulse = 0.03 + Math.sin(state.clock.elapsedTime * 1.5) * 0.02;
      pulseRef.current.scale.set(1 + pulse, 1 + pulse, 1);
    }
  });
  
  // Calculate notification glow intensity - more active items make the ring glow brighter
  const getNotificationIntensity = () => {
    const totalNotifications = tabs.reduce((sum, tab) => sum + tab.notifications, 0);
    return Math.min(0.2 + (totalNotifications * 0.1), 0.8); // Cap at 0.8
  };
  
  return (
    <group ref={ringRef}>
      {/* Main subtle ring indicator */}
      <mesh 
        rotation={[Math.PI/2, 0, 0]} // Rotate to lie flat
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <torusGeometry args={[radius, 0.05, 16, 100]} />
        <meshStandardMaterial 
          color="#2a4baf" 
          emissive="#2a4baf" 
          emissiveIntensity={hovered ? 0.6 : 0.3}
          transparent={true}
          opacity={0.4}
        />
      </mesh>
      
      {/* Outer pulsing ring for activity indication */}
      <mesh 
        ref={pulseRef}
        rotation={[Math.PI/2, 0, 0]}
      >
        <torusGeometry args={[radius, 0.02, 16, 100]} />
        <meshStandardMaterial 
          color="#4a6bdf" 
          emissive="#4a6bdf" 
          emissiveIntensity={getNotificationIntensity()}
          transparent={true}
          opacity={0.3}
        />
      </mesh>
      
      {/* Inner ring for active tab indication */}
      <mesh rotation={[Math.PI/2, 0, 0]}>
        <torusGeometry args={[radius - 0.15, 0.04, 16, 100]} />
        <meshStandardMaterial 
          color="#1e1e2f" 
          transparent={true}
          opacity={0.5}
        />
      </mesh>
      
      {/* Speed tabs positioned around the ring */}
      {tabs.map((tab, index) => {
        // Calculate position around the circle
        const angle = (index / tabs.length) * Math.PI * 2;
        const x = Math.cos(angle) * radius;
        const z = Math.sin(angle) * radius;
        // Slight Y offset to hover above the plane
        const y = 0.2;
        
        // Update active state based on activeTab
        const isActive = tab.label === activeTab;
        
        return (
          <SpeedTab 
            key={index}
            position={[x, y, z]}
            icon={tab.icon}
            label={tab.label}
            color={tab.color}
            active={isActive}
            notifications={tab.notifications}
            onClick={() => handleTabClick(tab.label)}
            hoveredRing={hovered}
          />
        );
      })}
    </group>
  );
}

// Widget component for the bottom UI with transition effects and enhanced Think Tank visualization
function Widget({ position, title, content, type = "standard", expanded = false, data = null, active = false, state = 'idle' }) {
  const [hovered, setHovered] = useState(false);
  const [visible, setVisible] = useState(true);
  const [isExpanded, setIsExpanded] = useState(expanded);
  const ref = useRef();
  
  // Handle hover, visibility, and activity animations
  useFrame((state) => {
    if (ref.current) {
      // Smooth rise animation when appearing
      if (visible && ref.current.position.y < 0) {
        ref.current.position.y = Math.min(0, ref.current.position.y + 0.05);
      }
      
      // Calculate base animation
      let baseAnimation = 0;
      
      // Add hover effect
      if (visible && hovered) {
        baseAnimation += Math.sin(state.clock.elapsedTime * 2) * 0.05;
      }
      
      // Add active effect with more pronounced motion when in thinking or processing state
      if (active) {
        baseAnimation += Math.sin(state.clock.elapsedTime * 3) * 0.03;
      }
      
      // Apply combined animation
      if (visible) {
        ref.current.position.y = baseAnimation;
      }
    }
  });
  
  // Toggle widget visibility
  const toggleVisibility = () => {
    setVisible(!visible);
  };
  
  // Toggle expanded state
  const toggleExpanded = (e) => {
    e.stopPropagation();
    setIsExpanded(!isExpanded);
  };
  
  // Determine the scale based on widget type and expanded state
  const getScale = () => {
    if (type === "thinkTank" && isExpanded) {
      return [4.5, 2.8, 0.1]; // Much larger for expanded Think Tank to show detailed model rankings
    } else if (type === "thinkTank") {
      return [3.0, 1.5, 0.1]; // Slightly larger for Think Tank
    } else {
      return [2, 1.2, 0.1]; // Standard size
    }
  };
  
  // Get blur effect intensity based on state
  const getBlurEffect = () => {
    if (type === "thinkTank") {
      if (state === 'processing') {
        return '8px'; // More intense blur during processing
      } else if (state === 'thinking') {
        return '6px'; // Medium blur during thinking
      } else {
        return '3px'; // Light blur when idle
      }
    } else {
      return '2px'; // Default for other widgets
    }
  };
  
  // Generate model activity indicator based on state and model activity
  const getModelActivityIndicator = (model) => {
    const isModelActive = model.active || (active && data && data.findIndex(m => m.name === model.name) === 0);
    
    if (state === 'thinking' && isModelActive) {
      return (
        <div style={{ 
          display: 'inline-flex',
          alignItems: 'center',
          marginLeft: '6px',
          background: 'rgba(111, 66, 193, 0.2)',
          padding: '2px 5px',
          borderRadius: '10px',
          fontSize: '9px'
        }}>
          <i className="fas fa-spinner fa-spin" style={{ marginRight: '3px' }}></i>
          Thinking
        </div>
      );
    } else if (state === 'processing' && isModelActive) {
      return (
        <div style={{ 
          display: 'inline-flex',
          alignItems: 'center',
          marginLeft: '6px',
          background: 'rgba(74, 107, 223, 0.2)',
          padding: '2px 5px',
          borderRadius: '10px',
          fontSize: '9px'
        }}>
          <i className="fas fa-cog fa-spin" style={{ marginRight: '3px' }}></i>
          Processing
        </div>
      );
    }
    return null;
  };

  // Render Think Tank content with model evaluations and activity indicators
  const renderThinkTankContent = () => {
    const models = data || [
      { 
        name: "Claude 3 Opus", 
        score: 9.4, 
        metrics: { quality: 94, relevance: 93, technical: 91, coherence: 95, helpfulness: 92 }, 
        capabilities: ["Research", "Analysis", "Reasoning"],
        reasoning: "Best overall quality with excellent structure and coherence. Strong technical accuracy with minimal AI self-references.",
        active: true
      },
      { 
        name: "GPT-4 Turbo", 
        score: 9.2, 
        metrics: { quality: 92, relevance: 95, technical: 89, coherence: 87, helpfulness: 94 }, 
        capabilities: ["Code", "Creative", "Problem-Solving"],
        reasoning: "Highest relevance and excellent code examples. Used for technical sections of the blended response."
      },
      { 
        name: "Gemini Pro", 
        score: 8.7, 
        metrics: { quality: 87, relevance: 89, technical: 85, coherence: 84, helpfulness: 86 }, 
        capabilities: ["Fast", "Concise", "Web Knowledge"],
        reasoning: "Contributed supplementary information and alternative perspectives to the blended response."
      }
    ];
    
    // Calculate blend percentages based on scores
    const totalScore = models.reduce((sum, model) => sum + model.score, 0);
    const blendPercentages = models.map(model => ({
      name: model.name,
      percentage: Math.round((model.score / totalScore) * 100)
    }));
    
    return (
      <div style={{ 
        width: isExpanded ? '400px' : '220px',
        backdropFilter: `blur(${getBlurEffect()})`,
        WebkitBackdropFilter: `blur(${getBlurEffect()})`,
        background: 'rgba(10, 10, 30, 0.75)',
        boxShadow: `0 0 20px rgba(111, 66, 193, ${active ? '0.6' : '0.2'})`,
        border: '1px solid rgba(111, 66, 193, 0.4)',
        borderRadius: '12px',
        padding: '0',
        overflow: 'hidden',
        transition: 'all 0.3s ease'
      }}>
        {/* Dramatic Header Bar */}
        <div style={{ 
          background: 'linear-gradient(90deg, rgba(111, 66, 193, 0.8) 0%, rgba(74, 107, 223, 0.8) 100%)',
          padding: '12px 15px',
          display: 'flex', 
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid rgba(111, 66, 193, 0.6)',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)'
        }}>
          <div style={{ 
            fontWeight: 'bold', 
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            color: 'white',
            textShadow: '0 0 10px rgba(111, 66, 193, 0.8)'
          }}>
            <i className="fas fa-brain" style={{ 
              marginRight: '10px',
              fontSize: '16px',
              color: 'white',
              textShadow: '0 0 15px rgba(255, 255, 255, 0.8)'
            }}></i>
            Think Tank Insights
            
            {/* Processing state indicator with improved styling */}
            {active && state !== 'idle' && (
              <div style={{ 
                marginLeft: '12px',
                fontSize: '11px',
                background: state === 'thinking' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(255, 255, 255, 0.15)',
                padding: '3px 8px',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                boxShadow: '0 0 8px rgba(111, 66, 193, 0.5)'
              }}>
                <i className={`fas fa-${state === 'thinking' ? 'spinner' : 'cog'} fa-spin`} 
                   style={{ marginRight: '6px' }}></i>
                {state === 'thinking' ? 'Thinking' : 'Processing'}
              </div>
            )}
          </div>
          <div 
            onClick={toggleExpanded} 
            style={{ 
              cursor: 'pointer', 
              fontSize: '12px',
              padding: '4px 10px',
              borderRadius: '20px',
              background: 'rgba(255, 255, 255, 0.15)',
              color: 'white',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              backdropFilter: 'blur(5px)',
              WebkitBackdropFilter: 'blur(5px)',
              transition: 'all 0.2s ease',
              boxShadow: '0 0 10px rgba(111, 66, 193, 0.4)'
            }}
          >
            {isExpanded ? 'Collapse' : 'Expand'}
          </div>
        </div>
        
        {/* Main content with padding */}
        <div style={{ 
          padding: '15px'
        }}>
          {models.map((model, i) => {
          const isModelActive = model.active || (active && i === 0);
          
          return (
            <div key={i} style={{
              marginBottom: '12px',
              background: isModelActive ? 'rgba(111, 66, 193, 0.25)' : 'rgba(20, 20, 40, 0.6)',
              padding: '8px',
              borderRadius: '6px',
              textAlign: 'left',
              border: isModelActive ? '1px solid rgba(111, 66, 193, 0.5)' : '1px solid rgba(60, 60, 90, 0.3)',
              boxShadow: isModelActive ? '0 0 15px rgba(111, 66, 193, 0.3)' : 'none',
              backdropFilter: 'blur(3px)',
              WebkitBackdropFilter: 'blur(3px)',
              transition: 'all 0.3s ease',
              position: 'relative',
              overflow: 'hidden'
            }}>
              {/* Sci-fi accent line */}
              <div style={{
                position: 'absolute',
                left: 0,
                top: 0,
                height: '100%',
                width: '3px',
                background: isModelActive ? 
                  'linear-gradient(to bottom, rgba(111, 66, 193, 0.8), rgba(74, 107, 223, 0.5))' : 
                  'rgba(60, 60, 90, 0.5)',
                boxShadow: isModelActive ? '0 0 5px rgba(111, 66, 193, 0.5)' : 'none'
              }}></div>
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '4px'
              }}>
                <span style={{ 
                  fontWeight: isModelActive ? 'bold' : 'normal', 
                  fontSize: '12px',
                  display: 'flex',
                  alignItems: 'center'
                }}>
                  {model.name}
                  {getModelActivityIndicator(model)}
                </span>
                <span style={{ 
                  background: isModelActive ? 'rgba(111, 66, 193, 0.3)' : 'rgba(74, 107, 223, 0.2)', 
                  padding: '2px 6px', 
                  borderRadius: '10px', 
                  fontSize: '11px', 
                  color: isModelActive ? '#9f62f1' : '#4a6bdf',
                  transition: 'all 0.3s ease'
                }}>{model.score}</span>
              </div>
              
              {isExpanded && (
                <>
                  <div style={{ fontSize: '11px', marginBottom: '4px' }}>
                    {/* Enhanced Quality Metrics with Pulsing Animations in a grid layout */}
                    <div style={{ 
                      display: 'grid', 
                      gridTemplateColumns: '1fr 1fr',
                      gap: '8px',
                      margin: '8px 0'
                    }}>
                      {/* Quality Metric */}
                      <div style={{ 
                        padding: '4px',
                        background: 'rgba(20, 20, 40, 0.5)',
                        borderRadius: '4px',
                        border: isModelActive ? '1px solid rgba(111, 66, 193, 0.3)' : '1px solid rgba(60, 60, 90, 0.2)'
                      }}>
                        <div style={{ 
                          display: 'flex', 
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          marginBottom: '4px',
                          fontSize: '10px'
                        }}>
                          <span>Quality</span>
                          <span style={{ fontWeight: 'bold' }}>{model.metrics.quality}%</span>
                        </div>
                        <div style={{ 
                          width: '100%', 
                          height: '6px', 
                          background: 'rgba(20, 20, 40, 0.8)', 
                          borderRadius: '3px',
                          overflow: 'hidden',
                          boxShadow: 'inset 0 0 3px rgba(0, 0, 0, 0.5)'
                        }}>
                          <div style={{ 
                            width: `${model.metrics.quality}%`, 
                            height: '100%', 
                            background: isModelActive ? 
                              'linear-gradient(to right, #6f42c1, #9f62f1)' : 
                              'linear-gradient(to right, #3a4db5, #4a6bdf)',
                            transition: 'width 0.5s ease',
                            boxShadow: isModelActive ? '0 0 8px rgba(111, 66, 193, 0.8)' : 'none'
                          }}></div>
                        </div>
                      </div>
                      
                      {/* Relevance Metric */}
                      <div style={{ 
                        padding: '4px',
                        background: 'rgba(20, 20, 40, 0.5)',
                        borderRadius: '4px',
                        border: isModelActive ? '1px solid rgba(111, 66, 193, 0.3)' : '1px solid rgba(60, 60, 90, 0.2)'
                      }}>
                        <div style={{ 
                          display: 'flex', 
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          marginBottom: '4px',
                          fontSize: '10px'
                        }}>
                          <span>Relevance</span>
                          <span style={{ fontWeight: 'bold' }}>{model.metrics.relevance}%</span>
                        </div>
                        <div style={{ 
                          width: '100%', 
                          height: '6px', 
                          background: 'rgba(20, 20, 40, 0.8)', 
                          borderRadius: '3px',
                          overflow: 'hidden',
                          boxShadow: 'inset 0 0 3px rgba(0, 0, 0, 0.5)'
                        }}>
                          <div style={{ 
                            width: `${model.metrics.relevance}%`, 
                            height: '100%', 
                            background: isModelActive ? 
                              'linear-gradient(to right, #4527a0, #7e57c2)' : 
                              'linear-gradient(to right, #1a8836, #28a745)',
                            transition: 'width 0.5s ease',
                            boxShadow: isModelActive ? '0 0 6px rgba(126, 87, 194, 0.8)' : 'none'
                          }}></div>
                        </div>
                      </div>
                      
                      {/* Technical Metric */}
                      <div style={{ 
                        padding: '4px',
                        background: 'rgba(20, 20, 40, 0.5)',
                        borderRadius: '4px',
                        border: isModelActive ? '1px solid rgba(111, 66, 193, 0.3)' : '1px solid rgba(60, 60, 90, 0.2)'
                      }}>
                        <div style={{ 
                          display: 'flex', 
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          marginBottom: '4px',
                          fontSize: '10px'
                        }}>
                          <span>Technical</span>
                          <span style={{ fontWeight: 'bold' }}>{model.metrics.technical}%</span>
                        </div>
                        <div style={{ 
                          width: '100%', 
                          height: '6px', 
                          background: 'rgba(20, 20, 40, 0.8)', 
                          borderRadius: '3px',
                          overflow: 'hidden',
                          boxShadow: 'inset 0 0 3px rgba(0, 0, 0, 0.5)'
                        }}>
                          <div style={{ 
                            width: `${model.metrics.technical}%`, 
                            height: '100%', 
                            background: isModelActive ? 
                              'linear-gradient(to right, #673ab7, #8a3cf7)' : 
                              'linear-gradient(to right, #d96c13, #fd7e14)',
                            transition: 'width 0.5s ease',
                            boxShadow: isModelActive ? '0 0 6px rgba(138, 60, 247, 0.8)' : 'none'
                          }}></div>
                        </div>
                      </div>
                      
                      {/* Coherence Metric */}
                      <div style={{ 
                        padding: '4px',
                        background: 'rgba(20, 20, 40, 0.5)',
                        borderRadius: '4px',
                        border: isModelActive ? '1px solid rgba(111, 66, 193, 0.3)' : '1px solid rgba(60, 60, 90, 0.2)'
                      }}>
                        <div style={{ 
                          display: 'flex', 
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          marginBottom: '4px',
                          fontSize: '10px'
                        }}>
                          <span>Coherence</span>
                          <span style={{ fontWeight: 'bold' }}>{model.metrics.coherence}%</span>
                        </div>
                        <div style={{ 
                          width: '100%', 
                          height: '6px', 
                          background: 'rgba(20, 20, 40, 0.8)', 
                          borderRadius: '3px',
                          overflow: 'hidden',
                          boxShadow: 'inset 0 0 3px rgba(0, 0, 0, 0.5)'
                        }}>
                          <div style={{ 
                            width: `${model.metrics.coherence}%`, 
                            height: '100%', 
                            background: isModelActive ? 
                              'linear-gradient(to right, #9c27b0, #d05ce3)' : 
                              'linear-gradient(to right, #0062cc, #007bff)',
                            transition: 'width 0.5s ease',
                            boxShadow: isModelActive ? '0 0 6px rgba(208, 92, 227, 0.8)' : 'none'
                          }}></div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Model Capabilities as Badges in a structured layout */}
                    {model.capabilities && model.capabilities.length > 0 && (
                      <div style={{ 
                        marginTop: '10px', 
                        marginBottom: '8px',
                        padding: '8px',
                        background: 'rgba(20, 20, 40, 0.3)',
                        borderRadius: '4px',
                        border: isModelActive ? '1px solid rgba(111, 66, 193, 0.2)' : '1px solid rgba(60, 60, 90, 0.1)'
                      }}>
                        <div style={{
                          fontSize: '10px',
                          fontWeight: 'bold',
                          marginBottom: '6px',
                          display: 'flex',
                          alignItems: 'center'
                        }}>
                          <i className="fas fa-cogs" style={{ 
                            marginRight: '5px', 
                            color: isModelActive ? '#9f62f1' : '#4a6bdf',
                            fontSize: '9px'
                          }}></i>
                          Capabilities
                        </div>
                        <div style={{ 
                          display: 'grid', 
                          gridTemplateColumns: `repeat(${Math.min(model.capabilities.length, 3)}, 1fr)`,
                          gap: '6px',
                        }}>
                          {model.capabilities.map((capability, idx) => (
                            <div key={idx} style={{
                              fontSize: '9px',
                              padding: '4px 6px',
                              borderRadius: '4px',
                              background: isModelActive ? 
                                'rgba(111, 66, 193, 0.15)' : 
                                'rgba(74, 107, 223, 0.1)',
                              border: `1px solid ${isModelActive ? 'rgba(138, 60, 247, 0.3)' : 'rgba(74, 107, 223, 0.2)'}`,
                              boxShadow: isModelActive ? '0 0 4px rgba(138, 60, 247, 0.2)' : 'none',
                              textAlign: 'center',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center'
                            }}>
                              {capability}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Model Reasoning with improved structure */}
                    {isExpanded && model.reasoning && (
                      <div style={{
                        marginTop: '10px',
                        padding: '10px',
                        background: 'rgba(20, 20, 40, 0.4)',
                        borderRadius: '6px',
                        border: isModelActive ? '1px solid rgba(111, 66, 193, 0.3)' : '1px solid rgba(60, 60, 90, 0.2)',
                        position: 'relative',
                        overflow: 'hidden'
                      }}>
                        {/* Section header with icon */}
                        <div style={{
                          fontSize: '10px',
                          fontWeight: 'bold',
                          marginBottom: '8px',
                          display: 'flex',
                          alignItems: 'center',
                          borderBottom: isModelActive ? '1px solid rgba(111, 66, 193, 0.2)' : '1px solid rgba(60, 60, 90, 0.1)',
                          paddingBottom: '5px'
                        }}>
                          <i className="fas fa-brain" style={{ 
                            marginRight: '5px', 
                            color: isModelActive ? '#9f62f1' : '#4a6bdf',
                            fontSize: '9px'
                          }}></i>
                          Reasoning
                        </div>
                        
                        {/* Reasoning content with improved typography */}
                        <div style={{
                          fontSize: '10px',
                          lineHeight: '1.4',
                          color: 'rgba(255, 255, 255, 0.8)',
                          position: 'relative',
                          zIndex: 1
                        }}>
                          {model.reasoning}
                        </div>
                        
                        {/* Subtle accent background for active models */}
                        {isModelActive && (
                          <div style={{
                            position: 'absolute',
                            top: 0,
                            right: 0,
                            width: '30%',
                            height: '100%',
                            background: 'linear-gradient(to left, rgba(111, 66, 193, 0.05), transparent)',
                            zIndex: 0
                          }}></div>
                        )}
                      </div>
                    )}
                  </div>
                  
                  {/* Response Blending Visualization - Only show for the first model and when expanded */}
                  {isExpanded && i === 0 && (
                    <div style={{ 
                      marginTop: '16px',
                      padding: '12px',
                      background: 'rgba(20, 20, 40, 0.5)',
                      borderRadius: '6px',
                      border: '1px solid rgba(111, 66, 193, 0.4)',
                      boxShadow: '0 0 10px rgba(111, 66, 193, 0.15)'
                    }}>
                      <div style={{ 
                        fontSize: '11px', 
                        fontWeight: 'bold',
                        display: 'flex',
                        alignItems: 'center',
                        marginBottom: '10px',
                        borderBottom: '1px solid rgba(111, 66, 193, 0.3)',
                        paddingBottom: '6px'
                      }}>
                        <i className="fas fa-code-branch" style={{ 
                          marginRight: '6px', 
                          color: '#9f62f1',
                          textShadow: '0 0 3px rgba(111, 66, 193, 0.6)'
                        }}></i>
                        Response Blending
                      </div>
                      
                      {/* Blending Visualization - Shows how models are combined with better styling */}
                      <div style={{ 
                        position: 'relative', 
                        height: '24px', 
                        width: '100%', 
                        marginBottom: '10px',
                        border: '1px solid rgba(40, 40, 70, 0.5)',
                        borderRadius: '12px',
                        overflow: 'hidden',
                        boxShadow: 'inset 0 0 10px rgba(0, 0, 0, 0.3)'
                      }}>
                        {/* Base gradient track */}
                        <div style={{
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          right: 0,
                          height: '100%',
                          background: 'linear-gradient(to right, rgba(20,20,40,0.6), rgba(30,30,50,0.6))'
                        }}>
                          {/* Model contribution segments - aligned with exact sizes */}
                          <div style={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            width: '60%',
                            height: '100%',
                            background: 'linear-gradient(to right, rgba(111,66,193,0.6), rgba(111,66,193,0.3))',
                            borderRight: '1px solid rgba(111,66,193,0.7)'
                          }}></div>
                          <div style={{
                            position: 'absolute',
                            top: 0,
                            left: '60%',
                            width: '30%',
                            height: '100%',
                            background: 'linear-gradient(to right, rgba(74,107,223,0.6), rgba(74,107,223,0.3))',
                            borderRight: '1px solid rgba(74,107,223,0.7)'
                          }}></div>
                          <div style={{
                            position: 'absolute',
                            top: 0,
                            left: '90%',
                            width: '10%',
                            height: '100%',
                            background: 'linear-gradient(to right, rgba(40,167,69,0.6), rgba(40,167,69,0.3))'
                          }}></div>
                          
                          {/* Pulsing glow effect */}
                          <div style={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            width: '100%',
                            height: '100%',
                            background: 'linear-gradient(90deg, rgba(111,66,193,0) 0%, rgba(111,66,193,0.2) 50%, rgba(111,66,193,0) 100%)',
                            opacity: 0.7,
                            animation: 'pulse 3s infinite ease-in-out'
                          }}></div>
                        </div>
                      </div>
                      
                      {/* Legend for blending percentages in an structured grid layout */}
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(3, 1fr)',
                        gap: '4px',
                        fontSize: '10px',
                        textAlign: 'center'
                      }}>
                        <div style={{ 
                          display: 'flex', 
                          alignItems: 'center',
                          justifyContent: 'center',
                          padding: '4px',
                          background: 'rgba(111,66,193,0.1)',
                          borderRadius: '4px',
                          border: '1px solid rgba(111,66,193,0.3)'
                        }}>
                          <div style={{ 
                            width: '10px', 
                            height: '10px', 
                            borderRadius: '3px', 
                            background: 'rgba(111,66,193,0.7)', 
                            marginRight: '5px',
                            boxShadow: '0 0 4px rgba(111,66,193,0.6)'
                          }}></div>
                          Claude (60%)
                        </div>
                        <div style={{ 
                          display: 'flex', 
                          alignItems: 'center',
                          justifyContent: 'center',
                          padding: '4px',
                          background: 'rgba(74,107,223,0.1)',
                          borderRadius: '4px',
                          border: '1px solid rgba(74,107,223,0.3)'
                        }}>
                          <div style={{ 
                            width: '10px', 
                            height: '10px', 
                            borderRadius: '3px', 
                            background: 'rgba(74,107,223,0.7)', 
                            marginRight: '5px',
                            boxShadow: '0 0 4px rgba(74,107,223,0.6)'
                          }}></div>
                          GPT-4 (30%)
                        </div>
                        <div style={{ 
                          display: 'flex', 
                          alignItems: 'center',
                          justifyContent: 'center',
                          padding: '4px',
                          background: 'rgba(40,167,69,0.1)',
                          borderRadius: '4px',
                          border: '1px solid rgba(40,167,69,0.3)'
                        }}>
                          <div style={{ 
                            width: '10px', 
                            height: '10px', 
                            borderRadius: '3px', 
                            background: 'rgba(40,167,69,0.7)', 
                            marginRight: '5px',
                            boxShadow: '0 0 4px rgba(40,167,69,0.6)'
                          }}></div>
                          Gemini (10%)
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          );
        })}
        
        {isExpanded && (
          <div style={{ 
            fontSize: '10px', 
            padding: '4px 8px', 
            background: active && state === 'processing' ? 'rgba(111, 66, 193, 0.2)' : 'rgba(40, 167, 69, 0.2)', 
            color: active && state === 'processing' ? '#9f62f1' : '#28a745',
            borderRadius: '4px',
            marginTop: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            {active && state === 'processing' ? (
              <>
                <i className="fas fa-sync-alt fa-spin" style={{ marginRight: '5px' }}></i>
                Optimizing blended response
              </>
            ) : (
              <>Blending enabled: combining model strengths</>
            )}
          </div>
        )}
      </div>
    );
  };
  
  // Render standard widget content
  const renderStandardContent = () => {
    return (
      <div style={{ width: '160px' }}>
        <div style={{ 
          fontWeight: 'bold', 
          marginBottom: '6px',
          borderBottom: '1px solid rgba(255,255,255,0.2)',
          paddingBottom: '4px'
        }}>
          {title}
        </div>
        <div>{content}</div>
      </div>
    );
  };
  
  const scale = getScale();
  
  return (
    <group position={position}>
      <group 
        ref={ref} 
        position={[0, visible ? 0 : -2, 0]}  // Start below if not visible
      >
        {/* Widget backdrop with glass effect */}
        <mesh 
          scale={[scale[0] + 0.2, scale[1] + 0.1, 0.05]}
          onPointerOver={() => setHovered(true)}
          onPointerOut={() => setHovered(false)}
          onClick={toggleVisibility}
        >
          <boxGeometry args={[1, 1, 0.5]} />
          <meshStandardMaterial 
            color="#1e1e2f" 
            transparent={true}
            opacity={0.7}
            metalness={0.5}
            roughness={0.2}
          />
        </mesh>
        
        {/* Main widget panel */}
        <mesh scale={scale}>
          <boxGeometry args={[1, 1, 0.5]} />
          <meshStandardMaterial 
            color="#1e1e2f" 
            transparent={true}
            opacity={0.8}
            metalness={0.3}
            roughness={0.4}
          />
        </mesh>
        
        {/* Widget border highlight with active state */}
        <mesh scale={[scale[0], scale[1], 0.08]} position={[0, 0, 0.05]}>
          <boxGeometry args={[1, 1, 0.01]} />
          <meshStandardMaterial 
            color={active ? "#6f42c1" : hovered ? "#4a6bdf" : "#2a4baf"}
            emissive={active ? "#6f42c1" : hovered ? "#4a6bdf" : "#2a4baf"}
            emissiveIntensity={active ? 0.9 : hovered ? 0.8 : 0.4}
            transparent={true}
            opacity={active ? 0.6 : 0.4}
          />
        </mesh>
        
        {/* Additional glow effect when active */}
        {active && type === "thinkTank" && (
          <mesh scale={[scale[0] + 0.4, scale[1] + 0.3, 0.01]} position={[0, 0, -0.05]}>
            <planeGeometry args={[1, 1]} />
            <meshStandardMaterial 
              color={state === 'thinking' ? "#6f42c1" : "#4a6bdf"}
              emissive={state === 'thinking' ? "#6f42c1" : "#4a6bdf"}
              emissiveIntensity={0.5 + Math.sin(Date.now() * 0.002) * 0.2}
              transparent={true}
              opacity={0.2}
            />
          </mesh>
        )}
        
        <Html position={[0, 0, 0.1]} center>
          <div style={{ 
            color: 'white', 
            padding: '8px',
            textAlign: type === "thinkTank" ? 'left' : 'center',
            fontSize: '12px',
            backgroundColor: 'rgba(30, 30, 47, 0.7)',
            borderRadius: '4px',
            boxShadow: active && type === "thinkTank" 
              ? '0 0 15px rgba(111, 66, 193, 0.5)' 
              : '0 0 10px rgba(74, 107, 223, 0.4)',
            border: active && type === "thinkTank" 
              ? '1px solid rgba(111, 66, 193, 0.5)' 
              : '1px solid rgba(74, 107, 223, 0.3)',
            maxHeight: '250px',
            overflowY: isExpanded ? 'auto' : 'hidden',
            transition: 'all 0.3s ease'
          }}>
            {type === "thinkTank" ? renderThinkTankContent() : renderStandardContent()}
          </div>
        </Html>
      </group>
    </group>
  );
}

// ThinkTankParticles component for visualizing AI model activity
function ThinkTankParticles({ active, activeModels }) {
  const particlesRef = useRef();
  const [particles, setParticles] = useState([]);
  
  // Generate particles when activity starts
  useEffect(() => {
    if (active) {
      // Create particles - more particles for more active models
      const particleCount = 30 + (activeModels.length * 20);
      const newParticles = [];
      
      for (let i = 0; i < particleCount; i++) {
        newParticles.push({
          id: i,
          position: [
            (Math.random() - 0.5) * 10,
            (Math.random() - 0.5) * 10,
            (Math.random() - 0.5) * 10
          ],
          speed: Math.random() * 0.03 + 0.01,
          size: Math.random() * 0.1 + 0.05,
          color: i % 3 === 0 ? '#6f42c1' : i % 3 === 1 ? '#4a6bdf' : '#28a745'
        });
      }
      
      setParticles(newParticles);
    } else {
      // Clear particles when inactive
      setParticles([]);
    }
  }, [active, activeModels.length]);
  
  // Animate particles flowing toward brain icon
  useFrame(() => {
    if (particlesRef.current && particles.length > 0) {
      // Target position is the think tank tab (approximate position)
      const targetX = Math.cos(6 * Math.PI / 8) * 6; // Brain icon position
      const targetZ = Math.sin(6 * Math.PI / 8) * 6;
      const targetY = 0.2;
      
      // Update particles in the group
      particlesRef.current.children.forEach((particle, i) => {
        if (i < particles.length) {
          // Calculate vector to target
          const dx = targetX - particle.position.x;
          const dy = targetY - particle.position.y;
          const dz = targetZ - particle.position.z;
          
          // Move towards target with some randomness
          particle.position.x += (dx * particles[i].speed) + (Math.random() - 0.5) * 0.02;
          particle.position.y += (dy * particles[i].speed) + (Math.random() - 0.5) * 0.02;
          particle.position.z += (dz * particles[i].speed) + (Math.random() - 0.5) * 0.02;
          
          // Determine intensity based on proximity to target
          const dist = Math.sqrt(dx*dx + dy*dy + dz*dz);
          if (dist < 2) {
            // Fade out as it gets closer to target
            particle.material.opacity = dist / 2;
            // Increase glow near target
            particle.material.emissiveIntensity = 1.5 - (dist / 2);
          }
          
          // Reset particle if it gets too close to target
          if (dist < 0.3) {
            // Reset to new starting position
            particle.position.set(
              (Math.random() - 0.5) * 10,
              (Math.random() - 0.5) * 10,
              (Math.random() - 0.5) * 10
            );
          }
        }
      });
    }
  });
  
  return (
    <group ref={particlesRef}>
      {particles.map((p) => (
        <mesh key={p.id} position={p.position} scale={[p.size, p.size, p.size]}>
          <sphereGeometry args={[1, 8, 8]} />
          <meshStandardMaterial 
            color={p.color}
            emissive={p.color}
            emissiveIntensity={0.8}
            transparent={true}
            opacity={0.7}
          />
        </mesh>
      ))}
    </group>
  );
}

// Main MinervaUI component that accepts projectOrbs as a prop
function MinervaUI({ projectOrbs = [] }) {
  const [activeProjectIndex, setActiveProjectIndex] = useState(null);
  const [minervaState, setMinervaState] = useState('idle'); // idle, thinking, processing
  const [activeModels, setActiveModels] = useState([]);
  const [thinkTankData, setThinkTankData] = useState([
    { 
      name: "GPT-4 Turbo", 
      score: 9.2, 
      metrics: { quality: 92, relevance: 95, technical: 89 }, 
      capabilities: ["Reasoning", "Code", "Creative"],
      active: false 
    },
    { 
      name: "Claude 3 Opus", 
      score: 9.4, 
      metrics: { quality: 94, relevance: 93, technical: 91 }, 
      capabilities: ["Research", "Analysis"],
      active: false 
    },
    { 
      name: "Mistral Large", 
      score: 8.9, 
      metrics: { quality: 89, relevance: 90, technical: 88 }, 
      capabilities: ["Math", "Code"],
      active: false 
    }
  ]);
  
  // Default project orbs if none provided
  const defaultProjects = [
    { position: [3, 1, 0], color: '#4a6bdf', agents: [{ color: '#dc3545' }] },
    { position: [-3, -1, 0], color: '#28a745', agents: [{ color: '#fd7e14' }] },
  ];
  
  // Use provided projectOrbs or fall back to defaults
  const projects = projectOrbs.length > 0 ? projectOrbs : defaultProjects;
  
  // Handle model activity simulation for Think Tank
  useEffect(() => {
    if (minervaState === 'thinking') {
      // Activate models with staggered start
      const updatedData = [...thinkTankData];
      
      // Schedule activation of each model with staggered timing
      updatedData.forEach((model, index) => {
        setTimeout(() => {
          setActiveModels(current => [...current, model.name]);
          setThinkTankData(current => {
            const updated = [...current];
            updated[index] = {...updated[index], active: true};
            return updated;
          });
        }, index * 800); // Stagger by 800ms
      });
    } else if (minervaState === 'processing') {
      // Update model scores after processing
      setTimeout(() => {
        // Update model scores to simulate ranking process
        setThinkTankData(current => {
          return current.map(model => ({
            ...model,
            // Slightly adjust scores to simulate re-ranking
            score: Math.min(10, model.score + (Math.random() * 0.4 - 0.2)).toFixed(1),
            // Keep model active during processing
            active: true
          }));
        });
      }, 1000);
    } else if (minervaState === 'idle') {
      // Reset active models
      setActiveModels([]);
      // Reset model active states
      setThinkTankData(current => {
        return current.map(model => ({
          ...model,
          active: false
        }));
      });
    }
  }, [minervaState]);
  
  // Handle clicks on project orbs
  const handleProjectClick = (index) => {
    setActiveProjectIndex(index === activeProjectIndex ? null : index);
  };
  
  // Handle tab clicks
  const handleTabClick = (tabName) => {
    console.log(`${tabName} clicked`);
    
    if (tabName === 'Think Tank') {
      // Simulate think tank workflow: thinking -> processing -> idle
      setMinervaState('thinking');
      setTimeout(() => {
        setMinervaState('processing');
        setTimeout(() => setMinervaState('idle'), 3000);
      }, 4000);
    }
  };
  
  return (
    <Canvas camera={{ position: [0, 0, 15], fov: 50 }}>
      {/* Scene lighting */}
      <ambientLight intensity={0.2} />
      <pointLight position={[0, 0, 0]} intensity={0.8} color="#ffffff" />
      
      {/* Enhanced lighting when models are active */}
      {minervaState !== 'idle' ? (
        <hemisphereLight intensity={0.5} color="#6f42c1" groundColor="#080820" />
      ) : (
        <hemisphereLight intensity={0.3} color="#4a6bdf" groundColor="#080820" />
      )}
      
      {/* Starry background */}
      <SceneSetup />
      
      {/* Think Tank particle effects */}
      <ThinkTankParticles active={minervaState !== 'idle'} activeModels={activeModels} />
      
      {/* Main Minerva Orb at center with enhanced pulsing effect */}
      <Orb 
        position={[0, 0, 0]} 
        color={minervaState !== 'idle' ? "#9f62f1" : "#6f42c1"} 
        scale={[2.5, 2.5, 2.5]} 
        pulsate={true}
        label="Minerva"
      />
      
      {/* Additional glow effect when processing */}
      {minervaState === 'processing' && (
        <mesh position={[0, 0, 0]} scale={[3.5, 3.5, 3.5]}>
          <sphereGeometry args={[1, 16, 16]} />
          <meshStandardMaterial 
            color="#6f42c1" 
            emissive="#6f42c1" 
            emissiveIntensity={0.3}
            transparent={true}
            opacity={0.2}
          />
        </mesh>
      )}
      
      {/* Project orbs positioned around Minerva */}
      {projects.map((proj, i) => (
        <ProjectOrb 
          key={i} 
          position={proj.position} 
          color={proj.color} 
          agents={proj.agents} 
          name={proj.name || `Project ${i + 1}`}
          active={i === activeProjectIndex}
          onClick={() => handleProjectClick(i)}
        />
      ))}
      
      {/* Control Ring with Speed Tabs around Minerva */}
      <ControlRing 
        radius={6} 
        onTabClick={handleTabClick} 
      />
      
      {/* Widgets at the bottom UI */}
      <Widget 
        position={[-5, -4, 0]} 
        title="Calendar" 
        content="Meeting with Dev Team at 3:00 PM"
      />
      <Widget 
        position={[0, -4, 0]} 
        type="thinkTank"
        expanded={true}
        active={minervaState !== 'idle'}
        state={minervaState}
        data={thinkTankData}
      />
      <Widget 
        position={[5, -4, 0]} 
        title="Tasks" 
        content="Implement UI: 75% complete"
      />
      
      {/* Camera controls */}
      <OrbitControls 
        enableZoom={true} 
        enablePan={false} 
        enableRotate={true}
        minDistance={5}
        maxDistance={25}
        dampingFactor={0.1}
        rotateSpeed={0.5}
      />
    </Canvas>
  );
}

export default MinervaUI;
