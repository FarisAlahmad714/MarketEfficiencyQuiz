class DrawingLayer {
    constructor(chartContainer) {
        this.container = chartContainer;
        this.svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        this.svg.style.position = "absolute";
        this.svg.style.top = "0";
        this.svg.style.left = "0";
        this.svg.style.width = "100%";
        this.svg.style.height = "100%";
        this.svg.style.pointerEvents = "all";
        this.svg.style.zIndex = "10"; // Ensure it's on top
        chartContainer.appendChild(this.svg);

        this.currentTool = null;
        this.isDrawing = false;
        this.currentElement = null;
        this.drawings = [];

        this.container.addEventListener('mousedown', this.startDrawing.bind(this));
        this.container.addEventListener('mousemove', this.draw.bind(this));
        this.container.addEventListener('mouseup', this.endDrawing.bind(this));

        // Use addEventListener for buttons
        document.getElementById('line-tool').addEventListener('click', () => this.setTool('line'));
        document.getElementById('pointer-tool').addEventListener('click', () => this.setTool('pointer'));
        document.getElementById('clear-btn').addEventListener('click', () => this.clearDrawings());
        document.getElementById('undo-btn').addEventListener('click', () => this.undoLastDrawing());

        console.log('DrawingLayer initialized');
    }

    setTool(tool) {
        this.currentTool = tool;
        console.log('Tool selected:', tool);
        this.container.style.cursor = tool === 'line' ? 'crosshair' : 'pointer';
    }

    startDrawing(e) {
        if (!this.currentTool) return;
        
        this.isDrawing = true;
        const point = this.getMousePosition(e);
        console.log('Started drawing at:', point);

        if (this.currentTool === 'line') {
            this.currentElement = this.createLine(point.x, point.y, point.x, point.y);
            this.svg.appendChild(this.currentElement);
        } else if (this.currentTool === 'pointer') {
            const circle = this.createPoint(point.x, point.y);
            this.svg.appendChild(circle);
            this.drawings.push(circle);
        }
    }

    draw(e) {
        if (!this.isDrawing || !this.currentElement || this.currentTool !== 'line') return;

        const point = this.getMousePosition(e);
        this.currentElement.setAttribute('x2', point.x);
        this.currentElement.setAttribute('y2', point.y);
        console.log('Drawing at:', point);
    }

    endDrawing(e) {
        if (!this.isDrawing) return;
        
        if (this.currentTool === 'line' && this.currentElement) {
            this.drawings.push(this.currentElement);
        }

        this.isDrawing = false;
        this.currentElement = null;
        console.log('Finished drawing');
    }

    createLine(x1, y1, x2, y2) {
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute('x1', x1);
        line.setAttribute('y1', y1);
        line.setAttribute('x2', x2);
        line.setAttribute('y2', y2);
        line.setAttribute('stroke', 'lime'); // Brighter color for visibility
        line.setAttribute('stroke-width', '3');
        return line;
    }

    createPoint(x, y) {
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute('cx', x);
        circle.setAttribute('cy', y);
        circle.setAttribute('r', '5');
        circle.setAttribute('fill', 'purple'); // Brighter color
        return circle;
    }

    getMousePosition(event) {
        const rect = this.container.getBoundingClientRect();
        return {
            x: event.clientX - rect.left,
            y: event.clientY - rect.top
        };
    }

    clearDrawings() {
        while (this.svg.firstChild) {
            this.svg.removeChild(this.svg.firstChild);
        }
        this.drawings = [];
        console.log('Drawings cleared');
    }

    undoLastDrawing() {
        if (this.drawings.length > 0) {
            const lastDrawing = this.drawings.pop();
            this.svg.removeChild(lastDrawing);
            console.log('Last drawing undone');
        }
    }
}

// Initialize when the page loads
document.addEventListener('DOMContentLoaded', () => {
    const chartContainer = document.getElementById('chart-container');
    if (chartContainer) {
        window.drawingLayer = new DrawingLayer(chartContainer);
        console.log('DrawingLayer initialized on chart-container');
    } else {
        console.error('Chart container not found!');
    }
});