import React, { useRef, useState, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html, useTexture } from '@react-three/drei';
import * as THREE from 'three';

// MinervaOrb component - The central hub of the UI
export function MinervaOrb({ position, onClick, isZoomedIn, isThinking = false, activeModels = [], processingState = 'idle' }) {
  const orbRef = useRef();
  const particlesRef = useRef();
  const ringRef = useRef();
  const glowRef = useRef();
  
  // Pulse animation state
  const [pulseScale, setPulseScale] = useState(1);
  const [pulseDirection, setPulseDirection] = useState(1);
  
  // Colors
  const minervaBlue = new THREE.Color('#4a6bdf');
  const glowColor = new THREE.Color('#7aa0ff');
  const thinkingColor = new THREE.Color('#6f42c1'); // Purple for thinking state
  const processingColor = new THREE.Color('#28a745'); // Green for processing state
  
  // Load textures
  const textures = useTexture({
    particleTexture: '/static/images/particle.png',  // You'll need to create this texture
    glowTexture: '/static/images/glow.png',         // You'll need to create this texture
  });
  
  // Animation frame updates
  useFrame((state, delta) => {
    if (orbRef.current) {
      // Gentle rotation of the orb
      orbRef.current.rotation.y += delta * 0.1;
      
      // Enhanced pulse effect when thinking or processing
      let pulseAmount = 0.2;
      let pulseMax = 1.05;
      let pulseMin = 0.95;
      
      if (isThinking) {
        pulseAmount = 0.4;
        pulseMax = 1.08;
        pulseMin = 0.94;
      }
      
      const newScale = pulseScale + (delta * pulseAmount * pulseDirection);
      
      // Reverse direction at min/max
      if (newScale > pulseMax) {
        setPulseDirection(-1);
      } else if (newScale < pulseMin) {
        setPulseDirection(1);
      }
      
      setPulseScale(newScale);
      orbRef.current.scale.set(newScale, newScale, newScale);
      
      // Rotate particles - faster when thinking
      if (particlesRef.current) {
        const particleSpeedMultiplier = isThinking ? 3 : 1;
        particlesRef.current.rotation.y -= delta * 0.05 * particleSpeedMultiplier;
        particlesRef.current.rotation.z += delta * 0.03 * particleSpeedMultiplier;
      }
      
      // Rotate ring - faster and reversed when in processing mode
      if (ringRef.current) {
        const ringSpeed = processingState === 'processing' ? -0.2 : 0.1;
        ringRef.current.rotation.z += delta * ringSpeed;
      }
      
      // Update glow intensity based on state
      if (glowRef.current && glowRef.current.material) {
        // Make the glow pulse with activity
        const glowPulse = 0.3 + Math.sin(state.clock.elapsedTime * 5) * 0.1;
        glowRef.current.material.opacity = isThinking ? glowPulse : 0.3;
      }
    }
  });
  
  // Create orbital particles
  const createOrbitalParticles = () => {
    const particleCount = 100;
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const sizes = new Float32Array(particleCount);
    
    for (let i = 0; i < particleCount; i++) {
      // Position particles in a spherical volume
      const radius = 2.5 + Math.random() * 0.5;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.random() * Math.PI * 2;
      
      positions[i * 3] = radius * Math.sin(theta) * Math.cos(phi);
      positions[i * 3 + 1] = radius * Math.sin(theta) * Math.sin(phi);
      positions[i * 3 + 2] = radius * Math.cos(theta);
      
      // Varying blue to cyan colors
      colors[i * 3] = 0.3 + Math.random() * 0.3;      // R
      colors[i * 3 + 1] = 0.5 + Math.random() * 0.3;  // G
      colors[i * 3 + 2] = 0.8 + Math.random() * 0.2;  // B
      
      // Varying sizes
      sizes[i] = 0.05 + Math.random() * 0.1;
    }
    
    return { positions, colors, sizes };
  };
  
  // Generate particle data
  const particleData = createOrbitalParticles();
  
  return (
    <group position={position}>
      {/* Main Minerva Orb */}
      <group 
        ref={orbRef} 
        onClick={onClick}
        userData={{ clickable: true }}
      >
        {/* Core sphere */}
        <mesh>
          <sphereGeometry args={[2, 32, 32]} />
          <meshPhongMaterial 
            color={minervaBlue}
            emissive={minervaBlue}
            emissiveIntensity={0.5}
            shininess={30}
          />
        </mesh>
        
        {/* Inner glow sphere */}
        <mesh ref={glowRef}>
          <sphereGeometry args={[2.05, 32, 32]} />
          <meshBasicMaterial 
            color={isThinking ? thinkingColor : glowColor}
            transparent={true}
            opacity={0.3}
          />
        </mesh>
        
        {/* Particles orbiting the Minerva orb */}
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
            size={0.15}
            vertexColors
            transparent
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </points>
        
        {/* Interactive control ring with segments */}
        <mesh ref={ringRef} rotation={[Math.PI / 2, 0, 0]}>
          <ringGeometry args={[2.3, 2.5, 64]} />
          <meshBasicMaterial 
            color={processingState === 'processing' ? processingColor : isThinking ? thinkingColor : minervaBlue}
            transparent={true}
            opacity={0.7}
            side={THREE.DoubleSide}
          />
        </mesh>
        
        {/* Second orbital ring at different angle */}
        <mesh rotation={[Math.PI / 3, Math.PI / 6, 0]}>
          <ringGeometry args={[2.4, 2.6, 64]} />
          <meshBasicMaterial 
            color={isThinking ? "#8a3cf7" : "#7952b3"}  // Purple
            transparent={true}
            opacity={isThinking ? 0.7 : 0.5}
            side={THREE.DoubleSide}
          />
        </mesh>
        
        {/* Interactive control ring segments */}
        {Array.from({ length: 8 }).map((_, i) => {
          const segmentActive = isThinking && (i % 3 === (Math.floor(Date.now() / 500) % 3));
          return (
            <mesh 
              key={`ring-segment-${i}`}
              rotation={[Math.PI / 2, 0, (Math.PI * 2 / 8) * i]}
              position={[0, 0, 0]}
            >
              <torusGeometry args={[2.4, 0.15, 8, 6, Math.PI / 16]} />
              <meshBasicMaterial 
                color={segmentActive ? "#9f62f1" : "#4a6bdf"}
                transparent={true}
                opacity={segmentActive ? 0.9 : 0.3}
                emissive={segmentActive ? "#9f62f1" : "#4a6bdf"}
                emissiveIntensity={segmentActive ? 1 : 0.3}
              />
            </mesh>
          );
        })}
        
        {/* Think Tank data streams visualization - represents the data flow between models */}
        <group rotation={[0, Math.PI / 4, 0]}>
          {Array.from({ length: 8 }).map((_, i) => {
            // Create pulsing effect for data streams when thinking
            const streamActive = isThinking && 
                               ((Date.now() % 1500) < (i * 180) || (Date.now() % 1500) > (1500 - i * 180));
            const streamIntensity = streamActive ? 1.0 : 0.7;
            const streamScale = streamActive ? 0.08 : 0.05;
            
            return (
              <mesh 
                key={`data-stream-${i}`}
                position={[0, 0, 0]}
                rotation={[0, (Math.PI * 2 / 8) * i, 0]}
              >
                <boxGeometry args={[streamScale, streamScale, 3]} />
                <meshBasicMaterial
                  color={isThinking ? (i % 2 === 0 ? "#6f42c1" : "#8a3cf7") : (i % 2 === 0 ? "#17a2b8" : "#7952b3")}
                  transparent={true}
                  opacity={streamIntensity}
                />
              </mesh>
            );
          })}
        </group>
        
        {/* AI model nodes - represent the different AI models in the Think Tank */}
        {[
          { position: [1.5, 1.0, 0.8], color: "#6f42c1", label: "GPT-4", id: "gpt4" },
          { position: [-1.2, 0.8, 1.2], color: "#4a6bdf", label: "Claude", id: "claude" },
          { position: [0.9, -1.3, 0.7], color: "#17a2b8", label: "Gemini", id: "gemini" },
          { position: [-0.8, -0.9, -1.3], color: "#28a745", label: "Mistral", id: "mistral" }
        ].map((model, i) => {
          const isModelActive = isThinking && (activeModels.includes(model.id) || (activeModels.length === 0 && i === 0));
          const pulseFrequency = 2 + (i * 0.5);
          const pulseFactor = isModelActive ? 0.15 + Math.sin(Date.now() / 200 * pulseFrequency) * 0.05 : 0;
          const modelScale = 0.2 + pulseFactor;
          
          return (
            <group key={`model-node-${i}`} position={model.position}>
              {/* Glowing halo effect for active models */}
              {isModelActive && (
                <mesh>
                  <sphereGeometry args={[modelScale + 0.1, 16, 16]} />
                  <meshBasicMaterial 
                    color={model.color}
                    transparent={true}
                    opacity={0.3}
                  />
                </mesh>
              )}
              
              {/* Model node sphere */}
              <mesh>
                <sphereGeometry args={[modelScale, 16, 16]} />
                <meshStandardMaterial 
                  color={model.color} 
                  emissive={model.color}
                  emissiveIntensity={isModelActive ? 0.6 : 0.2}
                />
              </mesh>
              
              {/* Activity indicators for active models */}
              {isModelActive && (
                <group>
                  {Array.from({ length: 3 }).map((_, j) => {
                    const ringRadius = modelScale + 0.1 + (j * 0.1);
                    const ringOpacity = 0.6 - (j * 0.15);
                    return (
                      <mesh key={`activity-ring-${j}`}>
                        <ringGeometry args={[ringRadius, ringRadius + 0.02, 16]} />
                        <meshBasicMaterial 
                          color={model.color}
                          transparent={true}
                          opacity={ringOpacity}
                          side={THREE.DoubleSide}
                        />
                      </mesh>
                    );
                  })}
                </group>
              )}
              
              {/* Model label with activity indicator */}
              <Html
                position={[0, 0.3, 0]}
                center
                distanceFactor={10}
                style={{
                  display: isZoomedIn ? 'none' : 'block',
                  opacity: isModelActive ? 1 : 0.8,
                  padding: '2px 5px',
                  borderRadius: '4px',
                  backgroundColor: isModelActive ? 
                    `rgba(${model.id === 'gpt4' ? '111, 66, 193, 0.9' : 
                           model.id === 'claude' ? '74, 107, 223, 0.9' : 
                           model.id === 'gemini' ? '23, 162, 184, 0.9' : '40, 167, 69, 0.9'})`
                    : 'rgba(0, 0, 0, 0.7)',
                  color: 'white',
                  fontSize: '0.6rem',
                  fontWeight: isModelActive ? 'bold' : 'normal',
                  boxShadow: isModelActive ? '0 0 5px rgba(255,255,255,0.5)' : 'none',
                  whiteSpace: 'nowrap',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                {isModelActive && (
                  <span style={{
                    width: '5px',
                    height: '5px',
                    borderRadius: '50%',
                    backgroundColor: '#fff',
                    display: 'inline-block',
                    animation: 'pulse 1s infinite'
                  }} />
                )}
                {model.label}
              </Html>
            </group>
          );
        })}
        
        {/* Minerva Label */}
        <Html
          position={[0, -2.5, 0]}
          center
          distanceFactor={10}
          style={{
            opacity: isZoomedIn ? 0 : 0.9,
            padding: '5px 10px',
            borderRadius: '5px', 
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            color: 'white',
            fontSize: '0.9rem',
            fontWeight: 'bold',
            whiteSpace: 'nowrap',
            transition: 'opacity 0.3s ease'
          }}
        >
          MINERVA
        </Html>
        
        {/* Think Tank Status - enhanced with activity state */}
        <Html
          position={[0, 2.7, 0]}
          center
          distanceFactor={15}
          style={{
            opacity: isZoomedIn ? 0 : (isThinking || processingState === 'processing' ? 1 : 0.8),
            padding: '3px 8px',
            borderRadius: '4px', 
            backgroundColor: 'rgba(23, 162, 184, 0.2)',
            border: '1px solid rgba(23, 162, 184, 0.5)',
            color: '#17a2b8',
            fontSize: '0.7rem',
            whiteSpace: 'nowrap',
            transition: 'opacity 0.3s ease'
          }}
        >
          Think Tank Active
        </Html>
      </group>
      
      {/* Outer glow effect with activity states */}
      <mesh ref={glowRef} scale={[1.2, 1.2, 1.2]}>
        <sphereGeometry args={[2, 32, 32]} />
        <meshBasicMaterial 
          color={isThinking ? thinkingColor : processingState === 'processing' ? processingColor : glowColor}
          transparent={true}
          opacity={isThinking ? 0.2 : 0.1}
          side={THREE.BackSide}
        />
      </mesh>
      
      {/* Additional activity indicator rays when thinking or processing */}
      {(isThinking || processingState === 'processing') && (
        <group position={position}>
          {Array.from({ length: 12 }).map((_, i) => {
            const rayAngle = (Math.PI * 2 / 12) * i;
            const rayX = Math.cos(rayAngle) * 3;
            const rayY = Math.sin(rayAngle) * 3;
            const rayActive = (i % 4 === Math.floor(Date.now() / 400) % 4);
            
            return (
              <mesh 
                key={`activity-ray-${i}`}
                position={[rayX * 0.7, rayY * 0.7, 0]}
                rotation={[0, 0, rayAngle]}
              >
                <planeGeometry args={[0.1, rayActive ? 2.5 : 1.5]} />
                <meshBasicMaterial 
                  color={isThinking ? thinkingColor : processingColor}
                  transparent={true}
                  opacity={rayActive ? 0.6 : 0.2}
                  side={THREE.DoubleSide}
                />
              </mesh>
            );
          })}
        </group>
      )}
    </group>
  );
}
