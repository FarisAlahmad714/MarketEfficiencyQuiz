// static/js/drawing-tools.js
class DrawingTools {
    constructor(chart, containerId) {
        this.chart = chart;
        this.container = document.getElementById(containerId);
        this.svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        this.svg.setAttribute("style", "position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;");
        this.container.style.position = "relative";
        this.container.appendChild(this.svg);
        this.drawings = [];
        this.activeTool = null;
        this.currentDrawing = null;

        this.setupEventListeners();
    }

    setupEventListeners() {
        document.getElementById('line-tool').onclick = () => this.setTool('line');
        document.getElementById('pointer-tool').onclick = () => this.setTool('pointer');
        document.getElementById('clear-btn').onclick = () => this.clearDrawings();
        document.getElementById('undo-btn').onclick = () => this.undoLastDrawing();
        document.getElementById('submit-btn').onclick = () => this.submitDrawings();

        this.container.onmousedown = (e) => this.startDrawing(e);
        this.container.onmousemove = (e) => this.draw(e);
        this.container.onmouseup = () => this.stopDrawing();
    }

    setTool(tool) { this.activeTool = tool; }

    startDrawing(e) {
        if (!this.activeTool) return;
        const rect = this.container.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        if (this.activeTool === 'line') {
            this.currentDrawing = { type: 'line', coordinates: [{ x, y }] };
        } else if (this.activeTool === 'pointer') {
            this.drawings.push({ type: 'pointer', coordinates: { x, y } });
            this.renderDrawings();
        }
    }

    draw(e) {
        if (!this.currentDrawing || this.activeTool !== 'line') return;
        const rect = this.container.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        this.currentDrawing.coordinates[1] = { x, y };
        this.renderDrawings();
    }

    stopDrawing() {
        if (this.currentDrawing) {
            this.drawings.push(this.currentDrawing);
            this.currentDrawing = null;
            this.renderDrawings();
        }
    }

    renderDrawings() {
        this.svg.innerHTML = '';
        this.drawings.forEach(d => {
            if (d.type === 'line') {
                const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
                line.setAttribute("x1", d.coordinates[0].x);
                line.setAttribute("y1", d.coordinates[0].y);
                line.setAttribute("x2", d.coordinates[1].x);
                line.setAttribute("y2", d.coordinates[1].y);
                line.setAttribute("stroke", "red");
                line.setAttribute("stroke-width", "2");
                this.svg.appendChild(line);
            } else if (d.type === 'pointer') {
                const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                circle.setAttribute("cx", d.coordinates.x);
                circle.setAttribute("cy", d.coordinates.y);
                circle.setAttribute("r", "5");
                circle.setAttribute("fill", "blue");
                this.svg.appendChild(circle);
            }
        });
    }

    clearDrawings() { this.drawings = []; this.renderDrawings(); }
    undoLastDrawing() { this.drawings.pop(); this.renderDrawings(); }

    submitDrawings() {
        fetch('/charting_exam/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ examType: 'swing_analysis', drawings: this.drawings })
        })
        .then(response => response.json())
        .then(data => alert(data.message));
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const drawingTools = new DrawingTools(window.chartInstance, 'chart-container');
});