// static/js/chart-controls.js
document.addEventListener('DOMContentLoaded', function() {
    // Find all chart sections on the page
    const chartSections = document.querySelectorAll('.chart-section');
    
    chartSections.forEach(chartSection => {
        const chartImage = chartSection.querySelector('.chart-image');
        if (!chartImage) return; // Skip if no chart image found
        
        // Add zoom controls
        addZoomControls(chartSection, chartImage);
        
        // Add minimap
        addMinimap(chartSection, chartImage);
    });
    
    function addZoomControls(chartSection, chartImage) {
        // Create zoom controls container
        const zoomControls = document.createElement('div');
        zoomControls.className = 'chart-zoom-controls';
        zoomControls.innerHTML = `
            <button class="zoom-btn zoom-in"><i class="fas fa-search-plus"></i></button>
            <button class="zoom-btn zoom-out"><i class="fas fa-search-minus"></i></button>
            <button class="zoom-btn zoom-reset"><i class="fas fa-sync-alt"></i></button>
        `;
        chartSection.appendChild(zoomControls);
        
        // Create zoom level indicator
        const zoomLevel = document.createElement('div');
        zoomLevel.className = 'zoom-level';
        zoomLevel.textContent = '100%';
        chartSection.appendChild(zoomLevel);
        
        // Set up state variables
        let currentZoom = 1;
        let dragStart = { x: 0, y: 0 };
        let currentPos = { x: 0, y: 0 };
        let isDragging = false;
        let zoomLevelTimeout;
        
        // Zoom in functionality
        zoomControls.querySelector('.zoom-in').addEventListener('click', function() {
            currentZoom = Math.min(currentZoom + 0.25, 3); // Max zoom 3x
            applyTransform();
            updateZoomLevel();
        });
        
        // Zoom out functionality
        zoomControls.querySelector('.zoom-out').addEventListener('click', function() {
            currentZoom = Math.max(currentZoom - 0.25, 0.5); // Min zoom 0.5x
            applyTransform();
            updateZoomLevel();
        });
        
        // Reset zoom functionality
        zoomControls.querySelector('.zoom-reset').addEventListener('click', function() {
            currentZoom = 1;
            currentPos = { x: 0, y: 0 };
            applyTransform();
            updateZoomLevel();
        });
        
        // Mouse wheel zoom
        chartImage.addEventListener('wheel', function(e) {
            e.preventDefault();
            
            // Determine zoom direction
            const zoomIn = e.deltaY < 0;
            
            // Calculate zoom center relative to image
            const rect = chartImage.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            
            // Store old position and zoom
            const oldZoom = currentZoom;
            const oldPosX = currentPos.x;
            const oldPosY = currentPos.y;
            
            // Update zoom level
            if (zoomIn) {
                currentZoom = Math.min(currentZoom + 0.1, 3);
            } else {
                currentZoom = Math.max(currentZoom - 0.1, 0.5);
            }
            
            // Calculate new position to zoom towards mouse
            if (currentZoom !== 1) {
                // Calculate zoom point in original image coordinates
                const zoomPointX = (mouseX - oldPosX) / oldZoom;
                const zoomPointY = (mouseY - oldPosY) / oldZoom;
                
                // Calculate how much the zoom point moves in the new zoom level
                const newPointX = zoomPointX * currentZoom;
                const newPointY = zoomPointY * currentZoom;
                
                // Adjust position to keep zoom point stable
                currentPos.x = mouseX - newPointX;
                currentPos.y = mouseY - newPointY;
            }
            
            applyTransform();
            updateZoomLevel();
        });
        
        // Dragging functionality
        chartImage.addEventListener('mousedown', function(e) {
            if (currentZoom > 1) {
                isDragging = true;
                dragStart.x = e.clientX - currentPos.x;
                dragStart.y = e.clientY - currentPos.y;
                chartImage.classList.add('dragging');
            }
        });
        
        document.addEventListener('mousemove', function(e) {
            if (isDragging) {
                currentPos.x = e.clientX - dragStart.x;
                currentPos.y = e.clientY - dragStart.y;
                applyTransform();
                updateMinimapViewport();
            }
        });
        
        document.addEventListener('mouseup', function() {
            if (isDragging) {
                isDragging = false;
                chartImage.classList.remove('dragging');
            }
        });
        
        // Double-click to reset
        chartImage.addEventListener('dblclick', function() {
            currentZoom = 1;
            currentPos = { x: 0, y: 0 };
            applyTransform();
            updateZoomLevel();
        });
        
        // Update zoom level indicator
        function updateZoomLevel() {
            zoomLevel.textContent = `${Math.round(currentZoom * 100)}%`;
            zoomLevel.classList.add('visible');
            
            // Hide after delay
            clearTimeout(zoomLevelTimeout);
            zoomLevelTimeout = setTimeout(() => {
                zoomLevel.classList.remove('visible');
            }, 1500);
            
            // Update minimap viewport
            updateMinimapViewport();
        }
        
        // Apply transform to chart image
        function applyTransform() {
            chartImage.style.transform = `translate(${currentPos.x}px, ${currentPos.y}px) scale(${currentZoom})`;
        }
    }
    
    function addMinimap(chartSection, chartImage) {
        // Create minimap container
        const minimap = document.createElement('div');
        minimap.className = 'chart-minimap';
        
        // Clone the image for minimap
        const minimapImg = document.createElement('img');
        minimapImg.className = 'minimap-img';
        minimapImg.src = chartImage.src;
        
        // Create viewport indicator
        const viewport = document.createElement('div');
        viewport.className = 'minimap-viewport';
        
        // Add elements to DOM
        minimap.appendChild(minimapImg);
        minimap.appendChild(viewport);
        chartSection.appendChild(minimap);
        
        // Show minimap on zoom
        const zoomBtns = chartSection.querySelectorAll('.zoom-btn');
        zoomBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const currentZoom = parseFloat(chartSection.querySelector('.zoom-level').textContent) / 100;
                if (currentZoom > 1) {
                    minimap.classList.add('visible');
                    updateMinimapViewport();
                } else {
                    minimap.classList.remove('visible');
                }
            });
        });
        
        // Update viewport on wheel zoom
        chartImage.addEventListener('wheel', function() {
            const currentZoom = parseFloat(chartSection.querySelector('.zoom-level').textContent) / 100;
            if (currentZoom > 1) {
                minimap.classList.add('visible');
            } else {
                minimap.classList.remove('visible');
            }
        });
        
        // Update minimap viewport to reflect visible area
        window.updateMinimapViewport = function() {
            const imageRect = chartImage.getBoundingClientRect();
            const sectionRect = chartSection.getBoundingClientRect();
            const minimapRect = minimap.getBoundingClientRect();
            
            const currentZoom = parseFloat(chartSection.querySelector('.zoom-level').textContent) / 100;
            
            if (currentZoom <= 1) return;
            
            // Calculate viewport dimensions
            const viewportWidth = (minimapRect.width / currentZoom);
            const viewportHeight = (minimapRect.height / currentZoom);
            
            // Calculate viewport position
            const transformMatrix = window.getComputedStyle(chartImage).transform;
            let translateX = 0;
            let translateY = 0;
            
            if (transformMatrix && transformMatrix !== 'none') {
                const matrix = transformMatrix.match(/matrix.*\((.+)\)/)[1].split(', ');
                translateX = parseFloat(matrix[4]);
                translateY = parseFloat(matrix[5]);
            }
            
            // Calculate position as percentage
            const percentX = -translateX / (imageRect.width * currentZoom - imageRect.width);
            const percentY = -translateY / (imageRect.height * currentZoom - imageRect.height);
            
            // Set viewport position and size
            viewport.style.width = `${viewportWidth}px`;
            viewport.style.height = `${viewportHeight}px`;
            viewport.style.left = `${percentX * (minimapRect.width - viewportWidth)}px`;
            viewport.style.top = `${percentY * (minimapRect.height - viewportHeight)}px`;
        };
    }
});