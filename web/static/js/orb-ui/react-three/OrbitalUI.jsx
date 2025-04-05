import React, { useRef, useState, useEffect } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Html, useTexture } from '@react-three/drei';
import * as THREE from 'three';
import { MinervaOrb } from './MinervaOrb';
import { ProjectOrb } from './ProjectOrb';
import { SpeedTabs } from './SpeedTabs';
import { Widgets } from './Widgets';

// Sample project data - would come from API in production
const PROJECTS = [
  {
    id: 1,
    name: 'AI Assistant',
    color: '#4a6bdf',
    icon: 'robot',
    position: [0, 0, -10],
    agents: [
      { id: 101, name: 'Chat Agent', icon: 'comments', color: '#17a2b8', position: [0, 0, 1] },
      { id: 102, name: 'Think Tank', icon: 'brain', color: '#28a745', position: [0.866, 0, -0.5] },
      { id: 103, name: 'Memory', icon: 'memory', color: '#ffc107', position: [-0.866, 0, -0.5] }
    ]
  },
  {
    id: 2,
    name: 'Finance AI',
    color: '#28a745',
    icon: 'chart-line',
    position: [8.66, 0, -5],
    agents: [
      { id: 201, name: 'Market Analysis', icon: 'search-dollar', color: '#17a2b8', position: [0, 0, 1] },
      { id: 202, name: 'Portfolio Optimizer', icon: 'chart-pie', color: '#dc3545', position: [0, 0, -1] }
    ]
  },
  {
    id: 3,
    name: 'Web Research',
    color: '#dc3545',
    icon: 'globe',
    position: [-8.66, 0, -5],
    agents: [
      { id: 301, name: 'Web Crawler', icon: 'spider', color: '#ffc107', position: [0, 0, 1] },
      { id: 302, name: 'Document Parser', icon: 'file-alt', color: '#17a2b8', position: [0.866, 0, -0.5] },
      { id: 303, name: 'Data Storage', icon: 'database', color: '#28a745', position: [-0.866, 0, -0.5] }
    ]
  }
];

// Main Scene Component
function Scene() {
  const [hoveredProject, setHoveredProject] = useState(null);
  const [selectedProject, setSelectedProject] = useState(null);
  const [zoomedIn, setZoomedIn] = useState(false);
  const [camera, setCamera] = useState(null);
  const { camera: threeCamera } = useThree();
  
  // Store the camera reference
  useEffect(() => {
    setCamera(threeCamera);
  }, [threeCamera]);
  
  // Handle project selection
  const handleProjectClick = (project) => {
    if (!zoomedIn) {
      setSelectedProject(project);
      zoomToProject(project);
    }
  };
  
  // Handle Minerva orb click
  const handleMinervaClick = () => {
    if (zoomedIn) {
      resetZoom();
    } else {
      // Open Minerva settings
      console.log('Opening Minerva settings');
    }
  };
  
  // Zoom to a project
  const zoomToProject = (project) => {
    if (camera) {
      const targetPosition = new THREE.Vector3(...project.position);
      // Adjust the target position to be closer to the project
      targetPosition.multiplyScalar(0.6);
      
      // Calculate look-at position (slightly beyond the project position)
      const lookAtPosition = new THREE.Vector3(...project.position);
      lookAtPosition.multiplyScalar(1.2);
      
      // Store the original position
      const originalPosition = camera.position.clone();
      const originalTarget = new THREE.Vector3(0, 0, 0);
      
      // Animation timeframe
      const duration = 1000; // ms
      const startTime = Date.now();
      
      const animateZoom = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeProgress = easeInOutCubic(progress);
        
        // Interpolate camera position
        const newPosition = originalPosition.clone().lerp(targetPosition, easeProgress);
        camera.position.copy(newPosition);
        
        // Interpolate camera look-at
        const newLookAt = originalTarget.clone().lerp(lookAtPosition, easeProgress);
        camera.lookAt(newLookAt);
        
        if (progress < 1) {
          requestAnimationFrame(animateZoom);
        } else {
          setZoomedIn(true);
        }
      };
      
      animateZoom();
    }
  };
  
  // Reset zoom to the center
  const resetZoom = () => {
    if (camera) {
      // Target position is the origin
      const targetPosition = new THREE.Vector3(0, 0, 20);
      
      // Store the current position
      const originalPosition = camera.position.clone();
      
      // Animation timeframe
      const duration = 1000; // ms
      const startTime = Date.now();
      
      const animateReset = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeProgress = easeInOutCubic(progress);
        
        // Interpolate camera position
        const newPosition = originalPosition.clone().lerp(targetPosition, easeProgress);
        camera.position.copy(newPosition);
        
        // Reset camera look-at to origin
        camera.lookAt(0, 0, 0);
        
        if (progress < 1) {
          requestAnimationFrame(animateReset);
        } else {
          setZoomedIn(false);
          setSelectedProject(null);
        }
      };
      
      animateReset();
    }
  };
  
  // Easing function for smoother transitions
  const easeInOutCubic = (t) => {
    return t < 0.5 
      ? 4 * t * t * t 
      : 1 - Math.pow(-2 * t + 2, 3) / 2;
  };
  
  return (
    <>
      {/* Central Minerva Orb */}
      <MinervaOrb 
        position={[0, 0, 0]} 
        onClick={handleMinervaClick}
        isZoomedIn={zoomedIn}
      />
      
      {/* Project Orbs */}
      {PROJECTS.map((project) => (
        <ProjectOrb 
          key={project.id}
          project={project}
          onClick={() => handleProjectClick(project)}
          onHover={() => setHoveredProject(project.id)}
          onHoverEnd={() => setHoveredProject(null)}
          isHovered={hoveredProject === project.id}
          isSelected={selectedProject?.id === project.id}
          isZoomedIn={zoomedIn}
        />
      ))}
      
      {/* Ambient Light */}
      <ambientLight intensity={0.5} />
      
      {/* Directional Lights */}
      <directionalLight position={[10, 10, 5]} intensity={0.5} />
      <directionalLight position={[-10, -10, -5]} intensity={0.2} />
      
      {/* Point lights for orbs */}
      <pointLight position={[0, 0, 0]} intensity={0.8} color="#4a6bdf" />
      
      {/* Galaxy background (would be more sophisticated in production) */}
      <Stars />
    </>
  );
}

// Background stars component
function Stars() {
  const starsRef = useRef();
  
  useEffect(() => {
    if (starsRef.current) {
      const geometry = new THREE.BufferGeometry();
      const vertices = [];
      
      for (let i = 0; i < 5000; i++) {
        const x = (Math.random() - 0.5) * 2000;
        const y = (Math.random() - 0.5) * 2000;
        const z = (Math.random() - 0.5) * 2000;
        vertices.push(x, y, z);
      }
      
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
      starsRef.current.geometry = geometry;
    }
  }, []);
  
  useFrame(() => {
    if (starsRef.current) {
      starsRef.current.rotation.x += 0.0001;
      starsRef.current.rotation.y += 0.0001;
    }
  });
  
  return (
    <points ref={starsRef}>
      <bufferGeometry />
      <pointsMaterial size={1.5} color="#ffffff" />
    </points>
  );
}

// Main OrbitalUI Component
export default function OrbitalUI() {
  return (
    <div className="orbital-ui-container">
      <Canvas 
        camera={{ position: [0, 0, 20], fov: 60 }}
        style={{ background: 'radial-gradient(circle at center, #131c2e 0%, #0a0e17 100%)' }}
      >
        <Scene />
        {/* Removing OrbitControls for a more guided experience */}
        {/* <OrbitControls enableZoom={false} enablePan={false} /> */}
      </Canvas>
      
      {/* HTML overlay for Speed Tabs (perimeter) */}
      <SpeedTabs />
      
      {/* HTML overlay for Widgets (bottom) */}
      <Widgets />
    </div>
  );
}

// Re-export components for use elsewhere
export { MinervaOrb, ProjectOrb, SpeedTabs, Widgets };
