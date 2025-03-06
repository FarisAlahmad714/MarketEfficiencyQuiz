document.addEventListener('DOMContentLoaded', function() {
    console.log('Script loaded and DOM ready');
    if (!document.getElementById('homepage-chart')) {
        console.error('Chart container #homepage-chart not found');
        return;
    }
    
    // Set up chart
    const chartElement = document.getElementById('homepage-chart');
    console.log('Creating chart with element:', chartElement);
    const chart = LightweightCharts.createChart(chartElement, {
        width: chartElement.clientWidth,
        height: chartElement.clientHeight,
        layout: {
            background: { color: '#1E1E2F' },
            textColor: '#d1d4dc',
        },
        grid: {
            vertLines: { color: 'rgba(42, 46, 57, 0.5)' },
            horzLines: { color: 'rgba(42, 46, 57, 0.5)' },
        },
        rightPriceScale: {
            borderColor: 'rgba(197, 203, 206, 0.8)',
        },
        timeScale: {
            borderColor: 'rgba(197, 203, 206, 0.8)',
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
        },
    });
    
    // Add candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
        upColor: '#4CAF50',
        downColor: '#F44336',
        borderDownColor: '#F44336',
        borderUpColor: '#4CAF50',
        wickDownColor: '#F44336',
        wickUpColor: '#4CAF50',
    });
    
    const symbolSelect = document.getElementById('chart-symbol');
    const intervalSelect = document.getElementById('chart-interval');
    
    // Function to fetch data from Binance
    function fetchBinanceData(symbol, interval) {
        const url = `https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=${interval}&limit=100`;
        console.log('Fetching data from:', url);
        
        fetch(url)
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                console.log('Received data:', data);
                const formattedData = data.map(d => ({
                    time: d[0] / 1000,
                    open: parseFloat(d[1]),
                    high: parseFloat(d[2]),
                    low: parseFloat(d[3]),
                    close: parseFloat(d[4]),
                }));
                
                candlestickSeries.setData(formattedData);
                updatePriceInfo(formattedData[formattedData.length - 1], formattedData[formattedData.length - 2]);
                chart.timeScale().fitContent();
            })
            .catch(error => console.error('Error fetching chart data:', error));
    }
    
    // Update price information
    function updatePriceInfo(currentCandle, previousCandle) {
        const currentPrice = document.getElementById('current-price');
        const priceChange = document.getElementById('price-change');
        
        if (!currentCandle) {
            console.warn('No current candle data');
            return;
        }
        
        currentPrice.textContent = `$${currentCandle.close.toFixed(2)}`;
        
        if (previousCandle) {
            const change = ((currentCandle.close - previousCandle.close) / previousCandle.close) * 100;
            priceChange.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
            priceChange.className = 'price-change ' + (change >= 0 ? 'positive' : 'negative');
        }
    }
    
    // Initial fetch
    fetchBinanceData(symbolSelect.value, intervalSelect.value);
    
    // Handle user selections
    symbolSelect.addEventListener('change', () => {
        fetchBinanceData(symbolSelect.value, intervalSelect.value);
    });
    
    intervalSelect.addEventListener('change', () => {
        fetchBinanceData(symbolSelect.value, intervalSelect.value);
    });
    
    // Responsive chart
    window.addEventListener('resize', () => {
        chart.resize(chartElement.clientWidth, chartElement.clientHeight);
    });
    
    // Update data every minute
    setInterval(() => {
        fetchBinanceData(symbolSelect.value, intervalSelect.value);
    }, 60000);
});