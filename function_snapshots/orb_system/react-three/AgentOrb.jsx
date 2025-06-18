import React, { useRef, useState, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import * as THREE from 'three';

export function AgentOrb({ 
  agent, 
  projectColor, 
  index, 
  totalAgents, 
  orbitRadius, 
  parentVisible, 
  parentIsHovered 
}) {
  const orbRef = useRef();
  const trailRef = useRef();
  
  // Calculate the orbit position
  const [orbitAngle, setOrbitAngle] = useState(() => {
    // Distribute agents evenly around the orbit
    return (index / totalAgents) * Math.PI * 2;
  });
  
  // Orbit speed varies slightly between agents
  const orbitSpeed = 0.3 + (index * 0.05);
  
  // Generate a trail for the agent orb
  const generateTrail = () => {
    const trailLength = 20;
    const trailPositions = new Float32Array(trailLength * 3);
    const trailColors = new Float32Array(trailLength * 3);
    
    // Agent color in RGB
    const agentRgb = {
      r: parseInt(agent.color.slice(1, 3), 16) / 255,
      g: parseInt(agent.color.slice(3, 5), 16) / 255,
      b: parseInt(agent.color.slice(5, 7), 16) / 255
    };
    
    for (let i = 0; i < trailLength; i++) {
      // Calculate trail position (will be updated in useFrame)
      const angle = orbitAngle - (i * 0.05);
      trailPositions[i * 3] = Math.cos(angle) * orbitRadius;
      trailPositions[i * 3 + 1] = 0;
      trailPositions[i * 3 + 2] = Math.sin(angle) * orbitRadius;
      
      // Fade out the trail
      const opacity = 1 - (i / trailLength);
      trailColors[i * 3] = agentRgb.r;
      trailColors[i * 3 + 1] = agentRgb.g;
      trailColors[i * 3 + 2] = agentRgb.b;
    }
    
    return { positions: trailPositions, colors: trailColors };
  };
  
  const trailData = generateTrail();
  
  // Update positions on each frame
  useFrame((state, delta) => {
    // Update orbit angle
    setOrbitAngle(prev => (prev + delta * orbitSpeed) % (Math.PI * 2));
    
    if (orbRef.current) {
      // Calculate new position
      const x = Math.cos(orbitAngle) * orbitRadius;
      const z = Math.sin(orbitAngle) * orbitRadius;
      
      // Update orb position
      orbRef.current.position.x = x;
      orbRef.current.position.z = z;
      
      // Rotate orb to face center
      orbRef.current.lookAt(0, 0, 0);
      
      // Add a gentle rotation
      orbRef.current.rotation.y += delta * 0.5;
    }
    
    // Update trail positions
    if (trailRef.current && trailRef.current.geometry.attributes.position) {
      const positions = trailRef.current.geometry.attributes.position.array;
      
      for (let i = 0; i < positions.length / 3; i++) {
        const angle = orbitAngle - (i * 0.05);
        positions[i * 3] = Math.cos(angle) * orbitRadius;
        positions[i * 3 + 1] = 0;
        positions[i * 3 + 2] = Math.sin(angle) * orbitRadius;
      }
      
      trailRef.current.geometry.attributes.position.needsUpdate = true;
    }
  });
  
  // Agent color in Three.js format
  const agentColor = new THREE.Color(agent.color);
  
  // Handle agent orb click
  const handleClick = (e) => {
    e.stopPropagation();
    console.log(`Agent ${agent.name} clicked`);
    // Future: Open agent details/actions
  };
  
  // Visibility based on parent project visibility
  const visibility = parentVisible ? 1 : 0;
  
  return (
    <group visible={parentVisible}>
      {/* Trail effect behind the agent */}
      <points ref={trailRef} visible={parentIsHovered}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={trailData.positions.length / 3}
            array={trailData.positions}
            itemSize={3}
          />
          <bufferAttribute
            attach="attributes-color"
            count={trailData.colors.length / 3}
            array={trailData.colors}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial 
          size={0.08}
          vertexColors
          transparent
          opacity={0.6}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>
      
      {/* Agent Orb */}
      <group 
        ref={orbRef} 
        onClick={handleClick}
        userData={{ clickable: true }}
      >
        {/* Core sphere */}
        <mesh>
          <sphereGeometry args={[0.5, 16, 16]} />
          <meshPhongMaterial 
            color={agentColor}
            emissive={agentColor}
            emissiveIntensity={0.3}
            shininess={30}
          />
        </mesh>
        
        {/* Glow effect */}
        <mesh>
          <sphereGeometry args={[0.55, 16, 16]} />
          <meshBasicMaterial 
            color={agentColor}
            transparent={true}
            opacity={0.3}
          />
        </mesh>
        
        {/* Agent Label */}
        <Html
          position={[0, 0.8, 0]}
          center
          distanceFactor={15}
          style={{
            opacity: parentIsHovered ? 0.9 : 0,
            padding: '2px 5px',
            borderRadius: '3px', 
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            color: 'white',
            fontSize: '0.6rem',
            whiteSpace: 'nowrap',
            transition: 'opacity 0.3s ease',
            pointerEvents: 'none'
          }}
        >
          {agent.name}
        </Html>
        
        {/* Agent capability indicator */}
        <mesh position={[0, 0, 0.55]} rotation={[0, 0, 0]}>
          <planeGeometry args={[0.3, 0.3]} />
          <meshBasicMaterial 
            color={agent.color}
            transparent={true}
            opacity={0.8}
            side={THREE.DoubleSide}
          >
            {/* This would ideally be a texture with the agent's icon */}
          </meshBasicMaterial>
        </mesh>
        
        {/* Think Tank capability visualization for agents that use it */}
        {agent.name === "Think Tank" && (
          <group>
            {/* Mini model nodes showing Think Tank capabilities */}
            {[
              { pos: [0.3, 0.2, 0.3], color: "#FF5733" },  // GPT-4
              { pos: [-0.3, 0.2, 0.3], color: "#33FF57" }, // Claude
              { pos: [0.3, -0.2, 0.3], color: "#3357FF" },  // Gemini
              { pos: [-0.3, -0.2, 0.3], color: "#F3FF33" }  // Mistral
            ].map((model, i) => (
              <mesh key={`model-dot-${i}`} position={model.pos} scale={[0.15, 0.15, 0.15]}>
                <sphereGeometry args={[1, 8, 8]} />
                <meshBasicMaterial color={model.color} />
              </mesh>
            ))}
            
            {/* Connecting lines between models */}
            {[
              { start: [0.3, 0.2, 0.3], end: [-0.3, 0.2, 0.3] },
              { start: [0.3, 0.2, 0.3], end: [0.3, -0.2, 0.3] },
              { start: [-0.3, 0.2, 0.3], end: [-0.3, -0.2, 0.3] },
              { start: [0.3, -0.2, 0.3], end: [-0.3, -0.2, 0.3] }
            ].map((line, i) => {
              const points = [
                new THREE.Vector3(...line.start),
                new THREE.Vector3(...line.end)
              ];
              const lineGeometry = new THREE.BufferGeometry().setFromPoints(points);
              
              return (
                <line key={`think-line-${i}`} geometry={lineGeometry}>
                  <lineBasicMaterial color="#ffffff" transparent opacity={0.4} />
                </line>
              );
            })}
          </group>
        )}
        
        {/* Memory agent visualization */}
        {agent.name === "Memory" && (
          <group>
            {/* Memory blocks visualization */}
            {Array.from({ length: 5 }).map((_, i) => {
              const angle = (i / 5) * Math.PI * 2;
              const radius = 0.25;
              return (
                <mesh 
                  key={`memory-block-${i}`} 
                  position={[
                    Math.cos(angle) * radius,
                    Math.sin(angle) * radius,
                    0.4
                  ]}
                  scale={[0.1, 0.1, 0.1]}
                >
                  <boxGeometry args={[1, 1, 1]} />
                  <meshBasicMaterial color="#ffc107" />
                </mesh>
              );
            })}
          </group>
        )}
      </group>
    </group>
  );
}
