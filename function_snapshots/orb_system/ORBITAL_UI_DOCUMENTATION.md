# Minerva 3D Orbital UI Documentation

## Overview
The Minerva 3D Orbital UI is a sophisticated, holographic-style interface that presents projects and functionality as orbital spheres in a 3D space environment. This advanced visualization is core to Minerva's user experience and must be preserved.

## Core Components

### 1. Main Orbital Environment
- **Location**: `orb-ui-init.js`, React Three.js components
- **How it Works**:
  - Creates a 3D space environment using Three.js/React Three Fiber
  - Renders orbital rings and a central Minerva orb
  - Places project orbs in orbital positions around the central orb
  - Includes animated star field and space background

### 2. Minerva Central Orb
- **Location**: `MinervaOrb.jsx`
- **How it Works**:
  - Central pulsing orb represents the Minerva AI core
  - Functions as main hub for system navigation
  - Contains holographic interface elements
  - Provides context awareness to the entire system

### 3. Project Orbs
- **Location**: `ProjectOrb.jsx`, `orb-ui-project.js`
- **How it Works**:
  - Each project is represented by a glowing orb in orbit
  - Orbs have unique colors based on project type
  - Clicking orbs activates project context
  - Projects maintain their own sub-orbits of agents

### 4. Holographic UI Elements
- **Location**: `orbital-enhanced.css`, `orbital_home.html`
- **How it Works**:
  - Semi-transparent UI elements with glow effects
  - Positioned strategically around the 3D space
  - Provides navigation and functional controls
  - Dashboard, Projects, Agents, and Settings interfaces

## Critical Functions

### 3D Environment Initialization
- `initializeOrbitalUI()`: Sets up the 3D environment
- `createOrbitalRings()`: Generates the orbital ring system
- `positionProjectOrbs()`: Places project orbs in correct orbits
- `setupOrbitControls()`: Manages camera and user interaction

### User Interaction Handlers
- `handleOrbSelection()`: Processes user clicking on orbs
- `navigateToProject()`: Transitions to project context
- `rotateOrbitalView()`: Changes the viewing angle
- `zoomToOrb()`: Focuses camera on a specific orb

### Animation Systems
- `animateOrbitalSystem()`: Manages continuous orbital movement
- `pulseEffect()`: Creates the glowing pulse effect
- `starfieldAnimation()`: Animates background stars
- `transitionBetweenProjects()`: Smooth transitions between contexts

## Integration Points

### Chat Interface Integration
- Floating chat panel appears within 3D environment
- Chat context changes based on selected project orb
- UI elements reflect current conversation context

### Project System Integration
- New projects appear as new orbs in the system
- Project colors and positions reflect their type/category
- Project data is fetched and reflected in orb appearance

### Think Tank Integration
- Model visualization appears within orbital UI
- Think Tank agents have their own sub-orbs
- Model performance affects visual representation

## Implementation Details

### React Three.js Components
- `OrbitalUI`: Main container component
- `MinervaOrb`: Central Minerva orb component
- `ProjectOrb`: Individual project orb component
- `AgentOrb`: Sub-orbs for agents within projects
- `Scene`: Manages the 3D scene and camera

### CSS/Visual Effects
- Glow effects use CSS filters and box-shadows
- Holographic elements use semi-transparent backgrounds
- Star field uses layered radial gradients
- Orbital rings use border animations

## Known Limitations
- High performance requirements for 3D rendering
- Some browsers may have WebGL limitations
- Mobile support requires performance optimizations

## Testing Methodology
- Verify smooth orbital animations
- Test project orb selection and focus
- Confirm holographic UI element rendering
- Check responsive design at different screen sizes

---

## DO NOT MODIFY WITHOUT TESTING
Any changes to the orbital UI system should be thoroughly tested to ensure:
1. Visual integrity of the 3D environment
2. Proper orb positioning and animation
3. Correct interaction with user input
4. Seamless integration with other system components
