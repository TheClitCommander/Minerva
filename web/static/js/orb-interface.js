/**
 * Minerva Orb Interface
 * Interactive 3D spinnable ring for Minerva dashboard navigation
 * Options swing around the Minerva Orb with perspective depth effect
 */

// CRITICAL ERROR HANDLING FIXES - Implements Rule #4, #10, #17
// Ensure error objects are always properly structured
window.enhancedErrorHandling = {
    logError: function(context, error, level = 'error') {
        // Create properly structured error object to prevent empty {} in logs
        const errorInfo = {
            context: context,
            message: error?.message || 'Unknown error',
            timestamp: new Date().toISOString(),
            details: error?.stack || 'No stack trace available',
            code: error?.code || 'UNKNOWN_ERROR'
        };
        
        // Determine context-specific user-friendly message
        let userMessage = 'An error occurred in the Minerva interface.';
        if (context === 'API') {
            userMessage = 'Could not connect to the Think Tank API. Operating in offline mode.';
            errorInfo.fallbackAvailable = true;
        } else if (context === 'DOM') {
            userMessage = 'Interface element not found. Some features may be limited.';
        }
        
        // Log properly formatted error
        console[level](userMessage, errorInfo);
        
        return errorInfo;
    },
    
    // Handle API errors specifically
    handleApiError: function(error) {
        const errorInfo = this.logError('API', error);
        
        // Apply Rule #4: Graceful fallback if API fails
        if (typeof window.scheduleApiReconnection === 'function') {
            window.scheduleApiReconnection();
        } else {
            // Set up automatic retry every 60 seconds per Rule #4
            console.log('Scheduling API reconnection attempt in 60 seconds');
            setTimeout(() => {
                console.log('Attempting reconnection to Think Tank API');
                // Attempt a basic API test
                fetch('http://localhost:8080/api/think-tank', {
                    method: 'OPTIONS',
                    headers: { 'Content-Type': 'application/json' }
                }).catch(() => {
                    // Silently fail and reschedule
                    window.enhancedErrorHandling.handleApiError({
                        message: 'Reconnection attempt failed',
                        code: 'RECONNECT_FAILED'
                    });
                });
            }, 60000);
        }
        
        return errorInfo;
    }
};

document.addEventListener("DOMContentLoaded", function() {
    // Rule #1: Progressive Enhancement - Preserve existing functionality
    // Check if orbital UI is needed on this page
    try {
        if (!document.getElementById('orbital-container')) {
            // Log with more user-friendly message per Rule #10
            console.log('Orbital UI not needed on this page - continuing with other functionality');
            // Initialize other components that don't depend on the orbital UI
            initializeNonOrbitalComponents();
            return;
        }
    } catch (err) {
        // Use enhanced error handling
        window.enhancedErrorHandling.logError('DOM', err);
        // Continue with other components
        console.log('Continuing with non-orbital functionality');
        initializeNonOrbitalComponents();
        return;
    }
    
    // Constants for physics and 3D effect - calibrated for true orbital rotation
    const FRICTION = 0.95;
    const MIN_VELOCITY = 0.1;
    const SNAP_THRESHOLD = 10;
    const SNAP_DISTANCE = 60;
    const ELLIPSE_X_RATIO = 1.0;  // Width ratio of the elliptical path
    const ELLIPSE_Z_RATIO = 0.85; // Significantly increased for pronounced depth effect
    const OPTION_RADIUS = 200;    // Adjusted radius for proper orbital distance
    
    // Get elements with error handling per Rule #10
    const navRing = document.getElementById("nav-ring");
    const minervaOrb = document.getElementById("minerva-orb");
    const contentDisplay = document.getElementById("content-display");
    const spaceBackground = document.getElementById("space-background");
    
    // Validate required elements exist before continuing
    if (!navRing || !minervaOrb) {
        // Use enhanced error handling with proper error object (Rule #10)
        window.enhancedErrorHandling.logError('DOM', {
            message: 'Minerva Orbital UI container not found in the DOM',
            code: 'DOM_ELEMENT_MISSING',
            elements: {
                navRing: !!navRing,
                minervaOrb: !!minervaOrb
            }
        });
        
        // Create fallback elements if possible (Rule #1 - Progressive Enhancement)
        if (document.getElementById('orbital-container') && !navRing) {
            console.log('Creating fallback navigation interface...');
            try {
                const fallbackNav = document.createElement('div');
                fallbackNav.id = 'fallback-navigation';
                fallbackNav.className = 'fallback-nav';
                fallbackNav.innerHTML = `
                    <div class="fallback-nav-header">Navigation</div>
                    <div class="fallback-nav-item" data-section="dashboard">Dashboard</div>
                    <div class="fallback-nav-item" data-section="chat">Chat</div>
                    <div class="fallback-nav-item" data-section="projects">Projects</div>
                `;
                document.getElementById('orbital-container').appendChild(fallbackNav);
            } catch (e) {
                // Non-critical, continue without fallback
            }
        }
        
        initializeNonOrbitalComponents();
        return;
    }
    
    // Make the Minerva Orb function as a home button
    initializeMinervaOrbHomeButton();
    
    // Navigation options
    const navOptions = document.querySelectorAll(".nav-option");
    
    // Create stars for the background - with error handling
    try {
        if (spaceBackground) {
            createStars();
        }
    } catch (err) {
        console.log('Star background initialization skipped:', err.message);
    }
    
    // Initialize positions of nav options around the ring - with error handling
    try {
        if (navOptions && navOptions.length > 0) {
            initializeNavOptions();
        }
    } catch (err) {
        console.log('Nav options initialization skipped:', err.message);
    }
    
    // Variables to track dragging
    let isDragging = false;
    let startAngle = 0;
    let currentAngle = 0;
    let velocity = 0;
    let lastMouseX = 0;
    let lastMouseY = 0;
    let animationFrame = null;
    let activeOption = navOptions[0]; // Default to first option (Dashboard)
    
    // Add the dragging events for the ring
    navRing.addEventListener("mousedown", startDrag);
    document.addEventListener("mousemove", drag);
    document.addEventListener("mouseup", endDrag);
    
    // Touch events for mobile
    navRing.addEventListener("touchstart", startDragTouch);
    document.addEventListener("touchmove", dragTouch);
    document.addEventListener("touchend", endDrag);
    
    // Click events for nav options
    navOptions.forEach(option => {
        option.addEventListener("click", function(e) {
            e.stopPropagation();
            selectNavOption(this);
        });
    });
    
    // Minerva orb click event
    minervaOrb.addEventListener("click", function() {
        // Pulse effect when clicked
        this.style.animation = "none";
        setTimeout(() => {
            this.style.animation = "pulse 4s infinite alternate";
        }, 10);
        
        // Return to dashboard view
        selectNavOption(navOptions[0]);
    });
    
    /**
     * Initialize positions of navigation options in 3D space around the orb
     */
    function initializeNavOptions() {
        const centerX = 250; // Half of the ring size
        const centerY = 250;
        
        navOptions.forEach((option, index) => {
            const angleInRadians = (index * (2 * Math.PI / navOptions.length));
            
            // Store the initial angle for each option
            option.dataset.angle = angleInRadians;
            option.dataset.index = index;
            
            // Position in 3D space using the current angle
            positionOptionInEllipticalOrbit(option, angleInRadians);
        });
    }
    
    /**
     * Position an option in 3D space based on its angle along an elliptical orbit
     * Creates a rotating ring of options around the centered Minerva Orb
     * Ensures options pass in front and behind each other for depth effect
     */
    function positionOptionInEllipticalOrbit(option, angle) {
        // Ring dimensions
        const ringWidth = 500; 
        const ringHeight = 500;
        const centerX = ringWidth / 2;
        const centerY = ringHeight / 2;
        const optionWidth = 80;
        const halfOptionWidth = optionWidth / 2;
        
        // Calculate position on the elliptical path around the center
        const x = OPTION_RADIUS * Math.cos(angle) * ELLIPSE_X_RATIO;
        const z = OPTION_RADIUS * Math.sin(angle) * ELLIPSE_Z_RATIO;
        
        // Vertical motion with ring's 30-degree tilt
        const y = Math.sin(angle) * 30;
        
        // Position on the ring around the center
        const posX = centerX + x - halfOptionWidth;
        const posY = centerY + y - halfOptionWidth;
        
        // Set position
        option.style.left = `${posX}px`;
        option.style.top = `${posY}px`;
        
        // Apply rotation to face center
        const rotateY = -angle * 0.8;
        const translateZ = z;
        
        // Apply transform
        option.style.transform = `rotateY(${rotateY}rad) translateZ(${translateZ}px)`;
        
        // Store z-position for reference
        option.dataset.zPosition = z;
        
        // Apply depth effects
        applyDepthEffect(option, z);
    }
    
    /**
     * Apply depth effect to options as they rotate around the orb
     * Makes options pass in front and behind the orb for true orbital 3D effect
     */
    function applyDepthEffect(option, zPosition) {
        // Remove all position classes first
        option.classList.remove('nav-option-front', 'nav-option-back', 'nav-option-side');
        
        // Calculate scale and opacity based on z-position
        const scaleFactor = mapRange(zPosition, -OPTION_RADIUS * ELLIPSE_Z_RATIO, OPTION_RADIUS * ELLIPSE_Z_RATIO, 0.5, 1.5);
        const opacityFactor = mapRange(zPosition, -OPTION_RADIUS * ELLIPSE_Z_RATIO, OPTION_RADIUS * ELLIPSE_Z_RATIO, 0.4, 1.0);
        
        // Determine position state - front, back or side
        if (zPosition > OPTION_RADIUS * ELLIPSE_Z_RATIO * 0.1) {
            // Front options
            option.classList.add('nav-option-front');
            option.style.pointerEvents = 'auto'; // Clickable
        } else if (zPosition < -OPTION_RADIUS * ELLIPSE_Z_RATIO * 0.1) {
            // Back options
            option.classList.add('nav-option-back');
            option.style.pointerEvents = 'none'; // Not clickable when behind
        } else {
            // Side options
            option.classList.add('nav-option-side');
            option.style.pointerEvents = 'auto';
        }
        
        // Apply style changes
        option.style.opacity = opacityFactor;
        option.style.transform += ` scale(${scaleFactor})`;
        
        // Z-index logic - options need to pass behind the orb in the back half
        // Orb has z-index of 20
        if (zPosition > 0) {
            // Front half - higher z-index than orb to appear in front
            const frontZIndex = Math.round(mapRange(zPosition, 0, OPTION_RADIUS * ELLIPSE_Z_RATIO, 21, 30));
            option.style.zIndex = frontZIndex;
        } else {
            // Back half - lower z-index than orb to pass behind
            const backZIndex = Math.round(mapRange(zPosition, -OPTION_RADIUS * ELLIPSE_Z_RATIO, 0, 1, 19));
            option.style.zIndex = backZIndex;
        }
    }
    
    /**
     * Utility function to map a value from one range to another
     */
    function mapRange(value, fromLow, fromHigh, toLow, toHigh) {
        return toLow + (toHigh - toLow) * ((value - fromLow) / (fromHigh - fromLow));
    }
    
    /**
     * Start dragging the ring
     */
    function startDrag(e) {
        e.preventDefault();
        
        const rect = navRing.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        
        startAngle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
        isDragging = true;
        navRing.style.cursor = "grabbing";
        
        // Stop any current animation
        if (animationFrame) {
            cancelAnimationFrame(animationFrame);
            animationFrame = null;
        }
        
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;
        velocity = 0;
    }
    
    /**
     * Start dragging with touch
     */
    function startDragTouch(e) {
        e.preventDefault();
        
        const touch = e.touches[0];
        const rect = navRing.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        
        startAngle = Math.atan2(touch.clientY - centerY, touch.clientX - centerX);
        isDragging = true;
        
        // Stop any current animation
        if (animationFrame) {
            cancelAnimationFrame(animationFrame);
            animationFrame = null;
        }
        
        lastMouseX = touch.clientX;
        lastMouseY = touch.clientY;
        velocity = 0;
    }
    
    /**
     * Handle dragging motion with 3D effect
     */
    function drag(e) {
        if (!isDragging) return;
        e.preventDefault();
        
        const rect = navRing.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        
        const currentMouseAngle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
        let angleDiff = currentMouseAngle - startAngle;
        
        // Update velocity based on mouse movement
        const dx = e.clientX - lastMouseX;
        const dy = e.clientY - lastMouseY;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        // Calculate velocity with direction
        const direction = lastMouseX > e.clientX ? -1 : 1;
        velocity = distance * direction * 0.2;
        
        // Update angle
        currentAngle += angleDiff;
        
        // Update positions of all options based on current angle
        updateAllOptionsPositions();
        
        // Find which option is closest to the front position (active)
        updateActiveOption();
        
        // Update for next frame
        startAngle = currentMouseAngle;
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;
    }
    
    /**
     * Update the 3D positions of all nav options
     */
    function updateAllOptionsPositions() {
        navOptions.forEach(option => {
            const baseAngle = parseFloat(option.dataset.angle);
            const newAngle = (baseAngle + currentAngle) % (2 * Math.PI);
            positionOptionInEllipticalOrbit(option, newAngle);
        });
    }
    
    /**
     * Handle touch dragging with 3D effect
     */
    function dragTouch(e) {
        if (!isDragging) return;
        e.preventDefault();
        
        const touch = e.touches[0];
        const rect = navRing.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        
        const currentMouseAngle = Math.atan2(touch.clientY - centerY, touch.clientX - centerX);
        let angleDiff = currentMouseAngle - startAngle;
        
        // Update velocity based on touch movement
        const dx = touch.clientX - lastMouseX;
        const dy = touch.clientY - lastMouseY;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        // Calculate velocity with direction
        const direction = lastMouseX > touch.clientX ? -1 : 1;
        velocity = distance * direction * 0.2;
        
        // Update angle
        currentAngle += angleDiff;
        
        // Update positions of all options based on current angle
        updateAllOptionsPositions();
        
        // Find which option is closest to the front position (active)
        updateActiveOption();
        
        // Update for next frame
        startAngle = currentMouseAngle;
        lastMouseX = touch.clientX;
        lastMouseY = touch.clientY;
    }
    
    /**
     * End the drag with momentum
     */
    function endDrag() {
        if (!isDragging) return;
        isDragging = false;
        navRing.style.cursor = "grab";
        
        // Continue with momentum
        animateWithMomentum();
    }
    
    /**
     * Animate the ring with momentum effect in 3D space
     */
    function animateWithMomentum() {
        if (Math.abs(velocity) < MIN_VELOCITY) {
            // If velocity is very small, snap to nearest option
            snapToNearestOption();
            return;
        }
        
        velocity *= FRICTION;
        currentAngle += velocity * 0.01;
        
        // Update positions of all options in 3D space
        updateAllOptionsPositions();
        
        // Update active option during momentum animation
        updateActiveOption();
        
        // Continue animation
        animationFrame = requestAnimationFrame(animateWithMomentum);
    }
    
    /**
     * Snap to the nearest option after momentum stops
     */
    function snapToNearestOption() {
        // Find the closest option to the front position (0 degrees)
        let closestOption = null;
        let closestDistance = Infinity;
        
        navOptions.forEach(option => {
            // Calculate the option's current angle in the 3D ring
            const optionAngle = parseFloat(option.dataset.angle);
            const optionCurrentAngle = (optionAngle + currentAngle) % (2 * Math.PI);
            
            // Distance is based on how close the angle is to 0 (front position)
            let distance = Math.abs(optionCurrentAngle - 0);
            
            // Handle the wrap-around case
            if (distance > Math.PI) {
                distance = 2 * Math.PI - distance;
            }
            
            if (distance < closestDistance) {
                closestDistance = distance;
                closestOption = option;
            }
        });
        
        if (closestOption && closestDistance < SNAP_THRESHOLD) {
            selectNavOption(closestOption);
        }
    }
    
    /**
     * Update which option is currently active based on position in 3D space
     * The active option is the one closest to the front (highest z-position)
     */
    function updateActiveOption() {
        let closestOption = null;
        let closestDistance = Infinity;
        
        navOptions.forEach(option => {
            // Calculate the option's current angle in the 3D ring
            const optionAngle = parseFloat(option.dataset.angle);
            const optionCurrentAngle = (optionAngle + currentAngle) % (2 * Math.PI);
            
            // Distance is based on how close the angle is to 0 (front position)
            // In 3D space, this corresponds to the highest Z value (closest to viewer)
            let distance = Math.abs(optionCurrentAngle - 0);
            
            // Handle the wrap-around case
            if (distance > Math.PI) {
                distance = 2 * Math.PI - distance;
            }
            
            if (distance < closestDistance) {
                closestDistance = distance;
                closestOption = option;
            }
        });
        
        if (closestOption && closestDistance < SNAP_DISTANCE && closestOption !== activeOption) {
            // Remove active class from all options
            navOptions.forEach(opt => opt.classList.remove("active"));
            
            // Add active class to the closest option
            closestOption.classList.add("active");
            activeOption = closestOption;
            
            // Update content without snapping (just highlight the option)
            updateContent(closestOption.dataset.section);
        }
    }
    
    /**
     * Select a navigation option and update the view
     */
    function selectNavOption(option) {
        // Calculate the angle we need to rotate to
        const optionAngle = parseFloat(option.dataset.angle);
        const targetAngle = 0 - optionAngle; // 0 is the front position in our 3D layout
        
        // Animate rotation to this option
        animateRotationTo(targetAngle);
        
        // Remove active class from all options
        navOptions.forEach(opt => opt.classList.remove("active"));
        
        // Add active class to the selected option
        option.classList.add("active");
        activeOption = option;
        
        // Update content
        updateContent(option.dataset.section);
    }
    
    /**
     * Smoothly animate rotation to a specific angle with 3D perspective
     */
    function animateRotationTo(targetAngle) {
        // Cancel any ongoing animation
        if (animationFrame) {
            cancelAnimationFrame(animationFrame);
        }
        
        // Normalize current angle within 0-2PI range for easier comparison
        const normalizedCurrentAngle = currentAngle % (2 * Math.PI);
        
        // Determine shortest direction to rotate
        let angleDiff = targetAngle - normalizedCurrentAngle;
        
        // Adjust for shortest path (less than half a circle)
        if (angleDiff > Math.PI) {
            angleDiff -= 2 * Math.PI;
        } else if (angleDiff < -Math.PI) {
            angleDiff += 2 * Math.PI;
        }
        
        // Set up animation variables
        const startAngle = currentAngle;
        const endAngle = currentAngle + angleDiff;
        const startTime = performance.now();
        const duration = 600; // milliseconds - slightly longer for better 3D effect
        
        // Animation function
        function animateStep(timestamp) {
            const elapsed = timestamp - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easedProgress = easeOutCubic(progress);
            
            // Calculate new angle
            currentAngle = startAngle + angleDiff * easedProgress;
            
            // Update position of all options in 3D space
            updateAllOptionsPositions();
            
            // Continue animation if not complete
            if (progress < 1) {
                animationFrame = requestAnimationFrame(animateStep);
            } else {
                // Animation complete
                animationFrame = null;
                currentAngle = endAngle; // Ensure we end exactly at target
                updateAllOptionsPositions(); // Final position update
            }
        }
        
        // Start animation
        animationFrame = requestAnimationFrame(animateStep);
    }
    
    /**
     * Easing function for smoother animation
     */
    function easeOutCubic(t) {
        return 1 - Math.pow(1 - t, 3);
    }
    
    /**
     * Update the content display based on section
     */
    function updateContent(section) {
        // Get content for the selected section from dashboard.js sections object
        if (window.sections && window.sections[section]) {
            contentDisplay.innerHTML = window.sections[section];
            
            // Re-initialize any JS that might be needed for the new content
            if (section === "dashboard") {
                if (typeof updateSystemStats === "function") {
                    updateSystemStats();
                }
            }
        }
    }
    
    /**
     * Create stars in the background for visual effect
     */
    function createStars() {
        if (!spaceBackground) return;
        
        // Enhanced star layers for parallax effect
        const starLayer1 = document.querySelector('.star-layer-1');
        const starLayer2 = document.querySelector('.star-layer-2');
        const starLayer3 = document.querySelector('.star-layer-3');
        const nebulaLayer = document.querySelector('.nebula-layer');
        
        // Add parallax effect to star layers when present
        if (starLayer1 && starLayer2 && starLayer3 && nebulaLayer) {
            // Mouse parallax effect
            document.addEventListener('mousemove', function(e) {
                const moveX = (window.innerWidth / 2 - e.clientX) / 50;
                const moveY = (window.innerHeight / 2 - e.clientY) / 50;
                
                // Different movement speeds create parallax depth effect
                starLayer1.style.transform = `translate(${moveX}px, ${moveY}px)`;
                starLayer2.style.transform = `translate(${moveX * 1.5}px, ${moveY * 1.5}px)`;
                starLayer3.style.transform = `translate(${moveX * 2.5}px, ${moveY * 2.5}px)`;
                nebulaLayer.style.transform = `translate(${moveX * 0.8}px, ${moveY * 0.8}px)`;
            });
            
            // Add nebula effect
            createNebulaEffect(nebulaLayer);
        } else {
            // Fallback to dynamic stars if layers don't exist
            const starCount = 100;
            
            for (let i = 0; i < starCount; i++) {
                const star = document.createElement("div");
                star.className = "star";
                
                // Random size between 1-3px
                const size = Math.random() * 2 + 1;
                star.style.width = size + "px";
                star.style.height = size + "px";
                
                // Random position
                star.style.left = Math.random() * 100 + "vw";
                star.style.top = Math.random() * 100 + "vh";
                
                // Random delay for twinkling
                star.style.animationDelay = Math.random() * 5 + "s";
                
                spaceBackground.appendChild(star);
            }
        }
        
        // Occasionally add a comet
        setInterval(addComet, 8000);
        
        // Initialize home button functionality
        initializeHomeButton();
    }
    
    /**
     * Create a nebula effect in the background
     */
    function createNebulaEffect(nebulaLayer) {
        if (!nebulaLayer) return;
        
        // Create several cloud-like elements with different colors
        const nebulaColors = [
            'rgba(74, 107, 223, 0.1)',  // Blue
            'rgba(156, 93, 219, 0.1)',   // Purple
            'rgba(120, 170, 255, 0.1)',  // Light blue
            'rgba(200, 120, 255, 0.1)'   // Pink
        ];
        
        for (let i = 0; i < 5; i++) {
            const nebula = document.createElement('div');
            nebula.className = 'nebula-cloud';
            
            // Random position and size
            const posX = Math.random() * 80 + 10;
            const posY = Math.random() * 80 + 10;
            const size = Math.random() * 200 + 100;
            
            nebula.style.position = 'absolute';
            nebula.style.left = `${posX}%`;
            nebula.style.top = `${posY}%`;
            nebula.style.width = `${size}px`;
            nebula.style.height = `${size}px`;
            nebula.style.background = `radial-gradient(circle at center, ${nebulaColors[i % nebulaColors.length]} 0%, transparent 70%)`;
            nebula.style.borderRadius = '50%';
            nebula.style.filter = 'blur(30px)';
            
            // Slow pulsating animation
            const animDuration = Math.random() * 20 + 30;
            nebula.style.animation = `nebula-pulse ${animDuration}s infinite alternate ease-in-out`;
            
            nebulaLayer.appendChild(nebula);
        }
    }
    
    /**
     * Add a comet effect to the background
     */
    function addComet() {
        if (!spaceBackground) return;
        
        const comet = document.createElement("div");
        comet.className = "comet";
        
        // Randomly select which edge to start from
        const edge = Math.floor(Math.random() * 4); // 0: top, 1: right, 2: bottom, 3: left
        let startX, startY, angle;
        
        switch(edge) {
            case 0: // Top edge
                startX = Math.random() * 100;
                startY = 0;
                angle = Math.random() * 30 + 30; // 30-60 degrees
                break;
            case 1: // Right edge
                startX = 100;
                startY = Math.random() * 100;
                angle = Math.random() * 30 + 120; // 120-150 degrees
                break;
            case 2: // Bottom edge
                startX = Math.random() * 100;
                startY = 100;
                angle = Math.random() * 30 + 210; // 210-240 degrees
                break;
            case 3: // Left edge
                startX = 0;
                startY = Math.random() * 100;
                angle = Math.random() * 30 + 300; // 300-330 degrees
                break;
        }
        
        // Set position and rotation
        comet.style.left = startX + "vw";
        comet.style.top = startY + "vh";
        comet.style.transform = `rotate(${angle}deg)`;
        
        // Random length and brightness
        const length = Math.random() * 150 + 80;
        const brightness = Math.random() * 0.5 + 0.5;
        comet.style.width = `${length}px`;
        comet.style.opacity = brightness;
        
        // Add to background
        spaceBackground.appendChild(comet);
        
        // Remove with fade effect
        setTimeout(() => {
            comet.style.opacity = "0";
            comet.style.transition = "opacity 0.5s ease";
            setTimeout(() => {
                if (comet.parentNode) {
                    comet.remove();
                }
            }, 500);
        }, 1500);
    }
    
    /**
     * Initialize the home button functionality
     */
    function initializeHomeButton() {
        const homeButton = document.getElementById('home-button');
        if (!homeButton) return;
        
        // Add enhanced hover effects
        homeButton.addEventListener('mouseenter', function() {
            const glow = this.querySelector('.home-button-glow');
            if (glow) glow.style.opacity = '0.7';
            this.style.transform = 'translateX(-50%) scale(1.1)';
            this.style.boxShadow = '0 0 25px rgba(74, 107, 223, 0.8)';
        });
        
        homeButton.addEventListener('mouseleave', function() {
            const glow = this.querySelector('.home-button-glow');
            if (glow) glow.style.opacity = '';
            this.style.transform = 'translateX(-50%)';
            this.style.boxShadow = '';
        });
        
        // Add click animation
        homeButton.addEventListener('click', function(e) {
            this.style.transform = 'translateX(-50%) scale(0.9)';
            this.style.boxShadow = '0 0 35px rgba(74, 107, 223, 1)';
            // Animation will complete before link is followed
        });
    }
    
    /**
     * Initialize the Minerva Orb as a home button
     * Makes the orb clickable to return to Minerva Central (index.html)
     */
    function initializeMinervaOrbHomeButton() {
        if (minervaOrb) {
            // Add tooltip/title for accessibility
            minervaOrb.setAttribute('title', 'Return to Minerva Central');
            
            // Add click event listener to navigate to home/index page
            minervaOrb.addEventListener('click', function(event) {
                // Prevent the event from affecting the nav ring
                event.stopPropagation();
                
                // Visual feedback with subtle pulse
                this.style.transform = 'translate(-50%, -50%) translateZ(0) scale(0.95)';
                this.style.boxShadow = '0 0 50px rgba(74, 107, 223, 1), 0 0 100px rgba(74, 107, 223, 0.7)';
                
                // Small delay for visual feedback before navigation
                setTimeout(function() {
                    // Navigate to Minerva Central (index.html)
                    window.location.href = 'index.html';
                }, 200);
            });
            
            // Make sure the orb doesn't affect ring dragging
            minervaOrb.addEventListener('mousedown', function(event) {
                // Stop propagation to prevent affecting the ring's drag behavior
                event.stopPropagation();
            });
            
            // Same for touch events
            minervaOrb.addEventListener('touchstart', function(event) {
                event.stopPropagation();
            });
        }
    }
    
    // Connect with existing dashboard.js
    // Create a global reference to the active sections
    window.orbInterface = {
        selectNavOption,
        updateContent
    };
    
    // Add CSS for dynamic nebula animation if it doesn't exist
    if (!document.getElementById('dynamic-animations')) {
        const styleSheet = document.createElement('style');
        styleSheet.id = 'dynamic-animations';
        styleSheet.textContent = `
            @keyframes nebula-pulse {
                0% { transform: scale(1); opacity: 0.5; }
                50% { transform: scale(1.2); opacity: 0.7; }
                100% { transform: scale(1); opacity: 0.5; }
            }
        `;
        document.head.appendChild(styleSheet);
    }
});

/**
 * Initialize components that don't depend on the orbital UI
 * This function handles initialization of critical components when orbital UI is not present
 * Following Rule #1: Progressive Enhancement and Rule #10: UX Principles
 */
function initializeNonOrbitalComponents() {
    // Make sure chat interface is properly initialized
    ensureChatInterfaceVisible();
    
    // Initialize API connection status tracking
    initializeApiStatusTracking();
    
    // Fix any duplicate chat history elements
    fixChatHistoryElements();
}

/**
 * Ensure chat interface is visible and properly styled
 * Following Rule #5: UI & Chat Interface Standards
 */
function ensureChatInterfaceVisible() {
    const chatInterface = document.getElementById('chat-interface');
    if (chatInterface) {
        chatInterface.style.display = 'flex';
        chatInterface.style.visibility = 'visible';
        chatInterface.style.opacity = '1';
        console.log('🔵 Chat interface visibility enforced by orbital component');
    }
}

/**
 * Initialize API connection status tracking
 * Following Rule #4: API Connectivity Rules
 */
function initializeApiStatusTracking() {
    // Check if the orbital container exists
    const orbitalContainer = document.getElementById('minerva-orbital-ui');
    if (!orbitalContainer) {
        // Create a structured error instead of an empty object
        const errorDetails = {
            message: "Minerva Orbital UI container not found in the DOM",
            timestamp: new Date().toISOString(),
            container: "minerva-orbital-ui",
            severity: "warning",
            recoverable: true
        };
        console.error("[ERROR] Minerva Orbital UI container not found in the DOM", errorDetails);
    }
    
    // Update dashboard status indicators if present
    const dashboardStatus = document.querySelector('#dashboard-view .stat-card .status');
    if (dashboardStatus) {
        // Check actual API status rather than showing fixed "Online"
        if (window.minervaAPI && window.minervaAPI.connected === false) {
            dashboardStatus.className = 'status offline';
            const statusText = dashboardStatus.querySelector('.status-text');
            if (statusText) {
                statusText.textContent = 'Offline (Fallback Active)';
            }
        }
    }
    
    // Actively check API availability for UI status syncing
    const apiUrl = window.THINK_TANK_API_URL || 'http://localhost:8080/api/think-tank';
    console.log('Checking Think Tank API availability at:', apiUrl);
    
    // Create a timeout for the fetch
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5-second timeout
    
    fetch(apiUrl, {
        method: 'OPTIONS',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal
    })
    .then(response => {
        clearTimeout(timeoutId);
        if (response.ok) {
            console.log('Think Tank API is available:', apiUrl);
            document.body.classList.add('api-connected');
            document.body.classList.remove('api-disconnected');
            
            // Track API status globally for the app
            window.thinkTankApiStatus = {
                available: true,
                lastChecked: new Date().toISOString(),
                errorCount: 0
            };
        } else {
            // Use enhanced error handling
            const errorInfo = {
                context: 'API',
                message: `API returned error status: ${response.status}`,
                timestamp: new Date().toISOString(),
                details: `Response status: ${response.status}`,
                code: 'API_ERROR_STATUS',
                status: response.status,
                fallbackAvailable: true
            };
            
            console.error('Could not connect to the Think Tank API. Operating in offline mode.', errorInfo);
            document.body.classList.add('api-disconnected');
            document.body.classList.remove('api-connected');
            
            // Track API status globally
            window.thinkTankApiStatus = {
                available: false,
                lastChecked: new Date().toISOString(),
                lastError: errorInfo,
                errorCount: (window.thinkTankApiStatus?.errorCount || 0) + 1
            };
            
            // Rule #4: Schedule retry every 60 seconds
            setTimeout(initializeApiStatusTracking, 60000);
        }
    })
    .catch(error => {
        clearTimeout(timeoutId);
        // Create properly structured error object with ENUMERABLE properties to prevent empty {} in logs
        const errorInfo = new Error('API Connection Error');
        
        // Define all properties as enumerable so they show up in console.log
        Object.defineProperties(errorInfo, {
            context: { value: 'API', enumerable: true, configurable: true, writable: true },
            message: { value: error?.message || 'Unknown API connection error', enumerable: true, configurable: true, writable: true },
            timestamp: { value: new Date().toISOString(), enumerable: true, configurable: true, writable: true },
            details: { value: error?.stack || 'No stack trace available', enumerable: true, configurable: true, writable: true },
            code: { value: error?.code || 'UNKNOWN_API_ERROR', enumerable: true, configurable: true, writable: true },
            fallbackAvailable: { value: true, enumerable: true, configurable: true, writable: true },
            url: { value: apiUrl, enumerable: true, configurable: true, writable: true },
            isApiError: { value: true, enumerable: true, configurable: true, writable: true },
            // Add toString method to make sure the error is properly serialized in logs
            toString: {
                value: function() {
                    return `API Error: ${this.message} (${this.code})`;
                },
                enumerable: true
            }
        });
        
        console.error('Could not connect to the Think Tank API. Operating in offline mode.', errorInfo);
        document.body.classList.add('api-disconnected');
        document.body.classList.remove('api-connected');
        
        // Calculate exponential backoff for retries based on error count
        const errorCount = (window.thinkTankApiStatus?.errorCount || 0) + 1;
        const baseRetryMs = 15000; // 15 seconds base retry interval
        const maxRetryMs = 300000; // Maximum 5 minute retry interval
        const retryInterval = Math.min(baseRetryMs * Math.pow(1.5, Math.min(errorCount, 10)), maxRetryMs);
        
        // Track API status globally with improved properties
        window.thinkTankApiStatus = {
            available: false,
            lastChecked: new Date().toISOString(),
            lastError: errorInfo,
            errorCount: errorCount,
            retryInterval: retryInterval,
            errorMessage: errorInfo.message,
            fallbackActive: true
        };
        
        // Broadcast API status change event for other components to react
        const apiStatusEvent = new CustomEvent('thinkTankApiStatusChanged', {
            detail: { available: false, error: errorInfo }
        });
        document.dispatchEvent(apiStatusEvent);
        
        // Update chat interface with the API status if it exists
        const chatHistory = document.getElementById('chat-history');
        if (chatHistory) {
            // Check if there's already a warning message to avoid duplicates (Rule #17)
            // Use a more specific selector to only match API warning messages
            const existingWarning = chatHistory.querySelector('.message.system.warning[data-message-id^="api-warning-"]');
            if (!existingWarning) {
                const warningElement = document.createElement('div');
                warningElement.className = 'message system warning';
                warningElement.dataset.messageId = `api-warning-${Date.now()}`;
                warningElement.dataset.timestamp = new Date().toISOString();
                
                warningElement.innerHTML = `<div class="message-content">
                    <div class="message-text">Think Tank API is currently offline. Your messages are being saved locally and will sync when connection is restored.</div>
                    <div class="message-note">Using fallback mode per Rule #4</div>
                    <div class="message-time">${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
                </div>`;
                
                chatHistory.appendChild(warningElement);
                
                // Make sure the message is visible
                if (typeof scrollToBottom === 'function' && chatHistory) {
                    scrollToBottom(chatHistory);
                } else {
                    chatHistory.scrollTop = chatHistory.scrollHeight;
                }
            }
        }
        
        // Rule #4: Schedule retry with exponential backoff
        console.log(`Scheduling API status check retry in ${retryInterval/1000} seconds`);
        setTimeout(initializeApiStatusTracking, retryInterval);
    });
}

/**
 * Fix any duplicate or problematic elements in chat history
 * Following Rule #10: UX Principles and Rule #17: Prevent message duplicates
 */
function fixChatHistoryElements() {
    // Fix chat history duplicates
    const chatHistory = document.getElementById('chat-history');
    if (chatHistory) {
        // Map to track messages by their content or ID to prevent duplicates
        const processedMessages = new Map();
        
        // Get all messages in the history
        const allMessages = chatHistory.querySelectorAll('.message');
        
        // First pass - identify existing messages and assign IDs if missing
        allMessages.forEach(msg => {
            // Implement Rule #17 & #18: Use a chatMessageId system
            let messageId = msg.getAttribute('data-message-id');
            
            // Get content and role information
            const messageRole = msg.classList.contains('bot') ? 'assistant' : 
                              msg.classList.contains('user') ? 'user' : 'system';
            const messageContent = msg.querySelector('.message-text')?.textContent || '';
            
            // Generate an ID if one doesn't exist
            if (!messageId) {
                messageId = `${messageRole}-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
                msg.setAttribute('data-message-id', messageId);
            }
            
            // Create a key that combines role and content
            const contentKey = `${messageRole}:${messageContent.slice(0, 50)}`;
            
            // Track this message by both its ID and content
            if (!processedMessages.has(messageId)) {
                processedMessages.set(messageId, msg);
            }
            
            // Also track by content to catch duplicates with different IDs
            if (!processedMessages.has(contentKey)) {
                processedMessages.set(contentKey, msg);
            } else if (msg !== processedMessages.get(contentKey)) {
                // This is a duplicate by content, mark for removal
                msg.classList.add('duplicate-message');
            }
        });
        
        // Remove duplicate welcome messages (prioritizing the first one)
        const welcomeMessages = chatHistory.querySelectorAll('.message.system.info');
        if (welcomeMessages.length > 1) {
            // Keep only the first welcome message
            for (let i = 1; i < welcomeMessages.length; i++) {
                welcomeMessages[i].classList.add('duplicate-message');
            }
        }
        
        // Remove all messages marked as duplicates
        chatHistory.querySelectorAll('.duplicate-message').forEach(msg => {
            msg.remove();
        });
        
        // Improve error message display
        const errorMessages = chatHistory.querySelectorAll('.message.system.error');
        errorMessages.forEach(msg => {
            // Add a more user-friendly note to error messages with Rule #19 metadata
            if (msg.textContent.includes('Failed to fetch')) {
                // Add metadata for Rule #19
                msg.setAttribute('data-synced', 'false');
                msg.setAttribute('data-timestamp', new Date().toISOString());
                msg.setAttribute('data-source', 'fallback');
                
                // Enhanced user-friendly message
                msg.innerHTML = '<div class="message-text">Think Tank API is currently offline. ' + 
                    'Your messages are being saved locally and will sync when connection is restored.</div>' +
                    '<div class="message-note">Using fallback mode per rule #4</div>' + 
                    '<div class="sync-status" title="This message is stored locally">🔄</div>';
            }
        });
        
        // Add sync indicators to all messages per Rule #20
        allMessages.forEach(msg => {
            if (!msg.querySelector('.sync-status')) {
                const syncStatus = document.createElement('div');
                syncStatus.className = 'sync-status';
                syncStatus.title = 'Message sync status';
                
                // Determine sync status
                const isSynced = msg.getAttribute('data-synced') !== 'false';
                syncStatus.innerHTML = isSynced ? '✓' : '🔄';
                syncStatus.classList.add(isSynced ? 'synced' : 'pending');
                
                msg.appendChild(syncStatus);
            }
        });
    }
}
