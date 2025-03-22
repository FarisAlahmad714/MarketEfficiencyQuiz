document.addEventListener('DOMContentLoaded', function() {
    // Initialize variables
    let price = 21000;
    
    // Get DOM elements
    const cryptoLoader = document.getElementById('cryptoLoader');
    const currentPrice = document.getElementById('current-price');
    const priceChange = document.getElementById('price-change');
    const trendLine = document.getElementById('trend-line');
    const candles = document.getElementById('candles-container');
    
    // Create and position the external message bar
    let externalMessage = null;
    let spinner = null;
    if (cryptoLoader) {
        externalMessage = document.createElement('div');
        externalMessage.id = 'external-loader-message';
        externalMessage.style.position = 'absolute';
        externalMessage.style.bottom = '15%';
        externalMessage.style.left = '50%';
        externalMessage.style.transform = 'translateX(-50%)';
        externalMessage.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
        externalMessage.style.color = 'white';
        externalMessage.style.padding = '10px 20px';
        externalMessage.style.textAlign = 'center';
        externalMessage.style.fontSize = '16px';
        externalMessage.style.fontWeight = 'bold';
        externalMessage.style.zIndex = '100';
        externalMessage.style.borderRadius = '8px';
        externalMessage.style.whiteSpace = 'normal';
        externalMessage.style.opacity = '0';
        externalMessage.style.transition = 'opacity 0.5s ease';
        
        spinner = document.createElement('span');
        spinner.innerHTML = '⟳';
        spinner.style.display = 'inline-block';
        spinner.style.marginRight = '8px';
        spinner.style.animation = 'spin 1s linear infinite';
        
        const style = document.createElement('style');
        style.textContent = '@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }';
        document.head.appendChild(style);
        
        externalMessage.appendChild(spinner);
        externalMessage.appendChild(document.createTextNode('Loading chart data...'));
        cryptoLoader.appendChild(externalMessage);
        
        setTimeout(() => {
            externalMessage.style.opacity = '1';
        }, 100);
        
        window.updateLoaderMessage = function(text) {
            if (externalMessage) {
                externalMessage.innerHTML = '';
                // Only show spinner for non-final messages
                if (text !== 'All assets loaded! Random tests are now fully optimized.') {
                    externalMessage.appendChild(spinner);
                }
                externalMessage.appendChild(document.createTextNode(text));
            }
        };
    }
    
    function animateCandles() {
        if (!candles) return;
        
        candles.innerHTML = '';
        const candleCount = 20;
        let candlesCreated = 0;
        
        for (let i = 0; i < candleCount; i++) {
            setTimeout(() => {
                const candle = document.createElement('div');
                candle.className = 'candle';
                const isBullish = Math.random() > 0.4;
                const heightPercent = 20 + Math.random() * 60;
                
                const priceMove = Math.random() * 100;
                price += isBullish ? priceMove : -priceMove * 0.7;
                
                if (currentPrice) {
                    currentPrice.textContent = Math.round(price).toLocaleString();
                }
                
                const changePercent = (Math.random() * 2).toFixed(2);
                if (priceChange) {
                    priceChange.textContent = isBullish ? `+${changePercent}%` : `-${changePercent}%`;
                    priceChange.className = `price-change ${isBullish ? 'positive' : 'negative'}`;
                }
                
                const body = document.createElement('div');
                body.className = `candle-body ${isBullish ? 'bullish' : 'bearish'}`;
                const bodyHeight = heightPercent * 0.6;
                body.style.height = `${bodyHeight}%`;
                body.style.bottom = isBullish ? '0' : `${heightPercent - bodyHeight}%`;
                
                const wick = document.createElement('div');
                wick.className = 'candle-wick';
                wick.style.height = `${heightPercent}%`;
                wick.style.bottom = '0';
                
                candle.appendChild(wick);
                candle.appendChild(body);
                candles.appendChild(candle);
                candle.style.animation = `growCandle 0.5s ease forwards`;
                
                if (i > 0) {
                    updateTrendLine(i, candleCount);
                }
                
                candlesCreated++;
                
                if (candlesCreated === candleCount) {
                    if (externalMessage) {
                        externalMessage.innerHTML = '';
                        externalMessage.appendChild(document.createTextNode(globalLoader.currentMessage || 'All assets loaded! Random tests are now fully optimized.'));
                    }
                    
                    if (cryptoLoader.classList.contains('active')) {
                        setTimeout(() => {
                            if (cryptoLoader.classList.contains('active')) {
                                resetAnimation();
                            }
                        }, 2000);
                    }
                }
                
            }, i * 150);
        }
    }
    
    function updateTrendLine(currentCandle, totalCandles) {
        if (!trendLine) return;
        const widthPercent = (currentCandle / totalCandles) * 100;
        const heightPosition = 30 + (Math.sin(currentCandle * 0.3) * 20) + (currentCandle * 0.5);
        trendLine.style.bottom = `${heightPosition}%`;
        trendLine.style.width = `${widthPercent}%`;
        if (currentCandle === 1) {
            trendLine.style.opacity = '1';
        }
    }
    
    window.resetAnimation = function() {
        price = 21000;
        if (currentPrice) currentPrice.textContent = price.toLocaleString();
        if (priceChange) {
            priceChange.textContent = '+0.00%';
            priceChange.className = 'price-change positive';
        }
        if (trendLine) {
            trendLine.style.width = '0';
            trendLine.style.opacity = '0';
        }
        
        if (externalMessage) {
            externalMessage.innerHTML = '';
            externalMessage.appendChild(spinner);
            externalMessage.appendChild(document.createTextNode('Loading chart data...'));
        }
        
        animateCandles();
    };
    
    if (cryptoLoader && cryptoLoader.classList.contains('active')) {
        resetAnimation();
    }
});