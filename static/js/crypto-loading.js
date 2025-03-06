// Add this to static/js/crypto-loading.js

document.addEventListener('DOMContentLoaded', function() {
    // Create the crypto loader HTML
    const loaderHTML = `
        <div class="crypto-loader">
            <div class="crypto-loader-container">
                <div class="chart-grid">
                    <div class="horizontal-line" style="top: 25%;"></div>
                    <div class="horizontal-line" style="top: 50%;"></div>
                    <div class="horizontal-line" style="top: 75%;"></div>
                    
                    <div class="vertical-line" style="left: 20%;"></div>
                    <div class="vertical-line" style="left: 40%;"></div>
                    <div class="vertical-line" style="left: 60%;"></div>
                    <div class="vertical-line" style="left: 80%;"></div>
                </div>
                
                <div class="chart-price">
                    $<span id="current-price">0</span>
                    <span id="price-change" class="price-change">+0.00%</span>
                </div>
                
                <div class="chart-price-labels">
                    <div class="price-label">$22,000</div>
                    <div class="price-label">$21,500</div>
                    <div class="price-label">$21,000</div>
                    <div class="price-label">$20,500</div>
                </div>
                
                <div class="chart-time-labels">
                    <div class="time-label">12:00</div>
                    <div class="time-label">14:00</div>
                    <div class="time-label">16:00</div>
                    <div class="time-label">18:00</div>
                    <div class="time-label">20:00</div>
                </div>
                
                <div class="candles-container" id="candles-container">
                    <!-- Candles will be inserted here via JS -->
                </div>
                
                <div id="trend-line" class="trend-line"></div>
                
                <div class="loading-text">
                    <div class="loading-spinner"></div>
                    Loading chart data...
                </div>
            </div>
        </div>
    `;
    
    // Add the loader to the DOM
    document.body.insertAdjacentHTML('beforeend', loaderHTML);
    
    // Get DOM elements
    const cryptoLoader = document.querySelector('.crypto-loader');
    const currentPrice = document.getElementById('current-price');
    const priceChange = document.getElementById('price-change');
    const trendLine = document.getElementById('trend-line');
    
    // Initialize price value
    let price = 21000;
    
    // Function to create and animate candles
    function animateCandles() {
        const container = document.getElementById('candles-container');
        
        // Clear any existing candles
        container.innerHTML = '';
        
        // Number of candles to display
        const candleCount = 20;
        
        // Create candles with a staggered animation
        for (let i = 0; i < candleCount; i++) {
            setTimeout(() => {
                // Create a new candle
                const candle = document.createElement('div');
                candle.className = 'candle';
                
                // Randomly determine if bullish or bearish
                const isBullish = Math.random() > 0.4; // Slightly more bullish for positive feel
                
                // Randomize candle properties
                // Higher height means more price movement
                const heightPercent = 20 + Math.random() * 60; 
                
                // Adjust price based on candle
                const priceMove = Math.random() * 100;
                if (isBullish) {
                    price += priceMove;
                } else {
                    price -= priceMove * 0.7; // Less downward movement for uptrend
                }
                
                // Format the current price
                currentPrice.textContent = Math.round(price).toLocaleString();
                
                // Calculate a pseudo price change percentage
                const changePercent = (Math.random() * 2).toFixed(2);
                priceChange.textContent = isBullish ? `+${changePercent}%` : `-${changePercent}%`;
                priceChange.className = `price-change ${isBullish ? 'positive' : 'negative'}`;
                
                // Create candle body
                const body = document.createElement('div');
                body.className = `candle-body ${isBullish ? 'bullish' : 'bearish'}`;
                
                // Position the body based on bullish/bearish
                const bodyHeight = heightPercent * 0.6; // Body is 60% of the height
                body.style.height = `${bodyHeight}%`;
                
                // Position body properly - top aligned for bearish, bottom for bullish
                if (isBullish) {
                    body.style.bottom = '0';
                } else {
                    body.style.bottom = `${heightPercent - bodyHeight}%`;
                }
                
                // Create candle wick
                const wick = document.createElement('div');
                wick.className = 'candle-wick';
                wick.style.height = `${heightPercent}%`;
                wick.style.bottom = '0';
                
                // Append elements
                candle.appendChild(wick);
                candle.appendChild(body);
                container.appendChild(candle);
                
                // Animate the candle growing
                candle.style.animation = `growCandle 0.5s ease forwards`;
                
                // Update trend line with each new candle
                if (i > 0) {
                    updateTrendLine(i, candleCount);
                }
                
            }, i * 150); // 150ms delay between each candle
        }
    }
    
    // Function to update the trend line
    function updateTrendLine(currentCandle, totalCandles) {
        // Calculate trend line width percentage based on current candle
        const widthPercent = (currentCandle / totalCandles) * 100;
        
        // Get container dimensions
        const container = document.querySelector('.candles-container');
        const containerHeight = container.offsetHeight;
        
        // Position the trend line at a variable height
        // Creating a smoother curve as candles progress
        const heightPosition = 30 + (Math.sin(currentCandle * 0.3) * 20) + (currentCandle * 0.5);
        trendLine.style.bottom = `${heightPosition}%`;
        trendLine.style.width = `${widthPercent}%`;
        
        // Make trend line visible when first candle appears
        if (currentCandle === 1) {
            trendLine.style.opacity = '1';
        }
    }
    
    // Reset and restart the animation
    function resetAnimation() {
        // Reset price to starting value
        price = 21000;
        currentPrice.textContent = price.toLocaleString();
        priceChange.textContent = '+0.00%';
        
        // Clear trend line
        trendLine.style.width = '0';
        trendLine.style.opacity = '0';
        
        // Restart candle animation
        animateCandles();
    }
    
    // Replace the default loading overlays with the crypto loader
    const quizForms = document.querySelectorAll('form');
    quizForms.forEach(form => {
        form.addEventListener('submit', function() {
            // Hide existing loading overlays if any
            const existingOverlay = document.getElementById('loadingOverlay');
            if (existingOverlay) {
                existingOverlay.style.display = 'none';
            }
            
            // Show crypto loader
            cryptoLoader.classList.add('active');
            
            // Start the animation
            resetAnimation();
        });
    });
    
    // Prepare the animation but don't start it yet
    // It will only run when a form is submitted
});