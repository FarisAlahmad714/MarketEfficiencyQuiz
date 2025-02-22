// static/js/swing_point_validation.js

const swingPointValidation = {
    tolerance: 0.2,  // 0.2% price tolerance for validation
    lookback: 3,     // Number of bars to check before/after

    expectedPoints: {
        highs: [
            { time: 1735862400, price: 98976.91 },  // Example point from your data
            { time: 1736121600, price: 102480.00 }  // Example point from your data
        ],
        lows: [
            { time: 1736035200, price: 97276.79 }   // Example point from your data
        ]
    },

    validatePoint(userPoint, type) {
        const expectedPoints = type === 'high' ? this.expectedPoints.highs : this.expectedPoints.lows;
        return expectedPoints.some(expected => {
            const priceDiff = Math.abs(expected.price - userPoint.price) / expected.price;
            return priceDiff <= this.tolerance;
        });
    }
};