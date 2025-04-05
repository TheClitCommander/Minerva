import React, { useRef, useState, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import * as THREE from 'three';
import { AgentOrb } from './AgentOrb';

export function ProjectOrb({ project, onClick, onHover, onHoverEnd, isHovered, isSelected, isZoomedIn }) {
  const orbRef = useRef();
  const ringRef = useRef();
  const particlesRef = useRef();
  
  // Animation state
  const [hoverScale, setHoverScale] = useState(1);
  const [floatPhase, setFloatPhase] = useState(() => Math.random() * Math.PI * 2);
  const [orbitRadius, setOrbitRadius] = useState(10);
  const [orbitSpeed, setOrbitSpeed] = useState(0.1 + Math.random() * 0.2);
  
  // Calculate the position based on time for floating animation
  useFrame((state, delta) => {
    if (orbRef.current) {
      // Update float phase for bobbing motion
      setFloatPhase(prev => (prev + delta * 0.5) % (Math.PI * 2));
      
      // Bobbing up and down motion when not zoomed in
      if (!isZoomedIn) {
        const floatY = Math.sin(floatPhase) * 0.2;
        orbRef.current.position.y = project.position[1] + floatY;
      }
      
      // Hover scale animation
      if (isHovered && hoverScale < 1.2) {
        setHoverScale(prev => Math.min(prev + delta * 2, 1.2));
      } else if (!isHovered && hoverScale > 1) {
        setHoverScale(prev => Math.max(prev - delta * 2, 1));
      }
      
      orbRef.current.scale.set(hoverScale, hoverScale, hoverScale);
      
      // Gentle rotation of the orb itself
      orbRef.current.rotation.y += delta * 0.2;
      
      // Rotate particles
      if (particlesRef.current) {
        particlesRef.current.rotation.y -= delta * 0.1;
        particlesRef.current.rotation.z += delta * 0.08;
      }
      
      // Rotate ring
      if (ringRef.current) {
        ringRef.current.rotation.z += delta * 0.15;
      }
    }
  });
  
  // Project color in Three.js color format
  const projectColor = new THREE.Color(project.color);
  
  // Handle project orb click
  const handleClick = (e) => {
    e.stopPropagation();
    onClick();
  };
  
  // Generate particle data for the project orb aura
  const createOrbitalParticles = () => {
    const particleCount = 50;
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const sizes = new Float32Array(particleCount);
    
    // Extract RGB components for particle colors
    const rgbColor = {
      r: parseInt(project.color.slice(1, 3), 16) / 255,
      g: parseInt(project.color.slice(3, 5), 16) / 255,
      b: parseInt(project.color.slice(5, 7), 16) / 255
    };
    
    for (let i = 0; i < particleCount; i++) {
      // Position particles in a spherical volume
      const radius = 1.5 + Math.random() * 0.5;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.random() * Math.PI * 2;
      
      positions[i * 3] = radius * Math.sin(theta) * Math.cos(phi);
      positions[i * 3 + 1] = radius * Math.sin(theta) * Math.sin(phi);
      positions[i * 3 + 2] = radius * Math.cos(theta);
      
      // Varying colors based on project color
      colors[i * 3] = rgbColor.r * (0.8 + Math.random() * 0.4);
      colors[i * 3 + 1] = rgbColor.g * (0.8 + Math.random() * 0.4);
      colors[i * 3 + 2] = rgbColor.b * (0.8 + Math.random() * 0.4);
      
      // Varying sizes
      sizes[i] = 0.05 + Math.random() * 0.1;
    }
    
    return { positions, colors, sizes };
  };
  
  // Generate particle data
  const particleData = createOrbitalParticles();
  
  return (
    <group position={project.position}>
      <group 
        ref={orbRef}
        onPointerOver={onHover}
        onPointerOut={onHoverEnd}
        onClick={handleClick}
        userData={{ clickable: true }}
      >
        {/* Core sphere */}
        <mesh>
          <sphereGeometry args={[1.2, 24, 24]} />
          <meshPhongMaterial 
            color={projectColor}
            emissive={projectColor}
            emissiveIntensity={0.3}
            shininess={30}
          />
        </mesh>
        
        {/* Inner glow sphere */}
        <mesh>
          <sphereGeometry args={[1.25, 24, 24]} />
          <meshBasicMaterial 
            color={projectColor}
            transparent={true}
            opacity={0.3}
          />
        </mesh>
        
        {/* Orbital ring */}
        <mesh ref={ringRef} rotation={[Math.PI / 2, 0, 0]}>
          <ringGeometry args={[1.4, 1.5, 48]} />
          <meshBasicMaterial 
            color={projectColor}
            transparent={true}
            opacity={0.7}
            side={THREE.DoubleSide}
          />
        </mesh>
        
        {/* Particles orbiting the project orb */}
        <points ref={particlesRef}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={particleData.positions.length / 3}
              array={particleData.positions}
              itemSize={3}
            />
            <bufferAttribute
              attach="attributes-color"
              count={particleData.colors.length / 3}
              array={particleData.colors}
              itemSize={3}
            />
            <bufferAttribute
              attach="attributes-size"
              count={particleData.sizes.length}
              array={particleData.sizes}
              itemSize={1}
            />
          </bufferGeometry>
          <pointsMaterial 
            size={0.1}
            vertexColors
            transparent
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </points>
        
        {/* Project Label */}
        <Html
          position={[0, -1.8, 0]}
          center
          distanceFactor={10}
          style={{
            opacity: isZoomedIn ? (isSelected ? 0 : 0.9) : 0.9,
            padding: '4px 8px',
            borderRadius: '4px', 
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            color: 'white',
            fontSize: '0.8rem',
            whiteSpace: 'nowrap',
            transition: 'opacity 0.3s ease'
          }}
        >
          {project.name}
        </Html>
        
        {/* Project Status */}
        <Html
          position={[0, 1.9, 0]}
          center
          distanceFactor={15}
          style={{
            opacity: isHovered ? 0.9 : 0,
            padding: '2px 6px',
            borderRadius: '3px', 
            backgroundColor: 'rgba(40, 167, 69, 0.2)',
            border: '1px solid rgba(40, 167, 69, 0.5)',
            color: '#28a745',
            fontSize: '0.6rem',
            whiteSpace: 'nowrap',
            transition: 'opacity 0.3s ease'
          }}
        >
          {project.agents.length} Active Agents
        </Html>
      </group>
      
      {/* Agent Orbs orbiting this project */}
      {project.agents.map((agent, index) => {
        // Calculate evenly distributed positions around the orbit
        const angleStep = (2 * Math.PI) / project.agents.length;
        const angle = index * angleStep;
        
        // Set orbit radius and position
        const orbitR = 2.5;
        
        return (
          <AgentOrb
            key={agent.id}
            agent={agent}
            projectColor={project.color}
            index={index}
            totalAgents={project.agents.length}
            orbitRadius={orbitR}
            parentVisible={isSelected || !isZoomedIn}
            parentIsHovered={isHovered}
          />
        );
      })}
      
      {/* Outer glow effect */}
      <mesh scale={[1.3, 1.3, 1.3]}>
        <sphereGeometry args={[1.2, 24, 24]} />
        <meshBasicMaterial 
          color={projectColor}
          transparent={true}
          opacity={0.1}
          side={THREE.BackSide}
        />
      </mesh>
    </group>
  );
}
