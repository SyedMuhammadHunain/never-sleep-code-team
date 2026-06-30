import { Component, ElementRef, ViewChild, signal, computed, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';

@Component({
  selector: 'app-workflow-canvas',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './workflow-canvas.html',
  styleUrls: ['./workflow-canvas.css']
})
export class WorkflowCanvas implements AfterViewInit {
  @ViewChild('canvasContainer') canvasContainer!: ElementRef;

  prompt = signal('');
  output = signal<string | null>(null);
  loading = signal(false);
  error = signal<string | null>(null);

  // Canvas State
  scale = signal(1);
  translateX = signal(0);
  translateY = signal(0);
  isDragging = false;
  lastMouseX = 0;
  lastMouseY = 0;

  nodes = signal([
    { id: '1', title: 'START', x: 400, y: 100 },
    { id: '2', title: 'Parse Task', x: 400, y: 300 },
    { id: '3', title: 'Generate Code', x: 400, y: 500 }
  ]);

  edges = signal([
    { from: '1', to: '2' },
    { from: '2', to: '3' }
  ]);

  transformStyle = computed(() =>
    `translate(${this.translateX()}px, ${this.translateY()}px) scale(${this.scale()})`
  );

  constructor(private http: HttpClient, private router: Router) {
    const nav = this.router.getCurrentNavigation();
    if (nav?.extras.state?.['prompt']) {
      this.prompt.set(nav.extras.state['prompt']);
      // Start processing right away
      this.submitPrompt();
    }
  }

  ngAfterViewInit() {}

  onWheel(event: WheelEvent) {
    event.preventDefault();
    const zoomSensitivity = 0.001;
    const delta = -event.deltaY * zoomSensitivity;
    const newScale = Math.min(Math.max(0.1, this.scale() + delta), 3);
    this.scale.set(newScale);
  }

  onMouseDown(event: MouseEvent) {
    this.isDragging = true;
    this.lastMouseX = event.clientX;
    this.lastMouseY = event.clientY;
  }

  onMouseMove(event: MouseEvent) {
    if (!this.isDragging) return;
    const dx = event.clientX - this.lastMouseX;
    const dy = event.clientY - this.lastMouseY;
    this.translateX.update(x => x + dx);
    this.translateY.update(y => y + dy);
    this.lastMouseX = event.clientX;
    this.lastMouseY = event.clientY;
  }

  onMouseUp() {
    this.isDragging = false;
  }

  onMouseLeave() {
    this.isDragging = false;
  }

  submitPrompt() {
    if (!this.prompt().trim()) return;
    this.loading.set(true);
    this.output.set(null);
    this.error.set(null);
    this.http.post<{output: string, error: string}>('http://localhost:8000/api/run', { prompt: this.prompt() })
      .subscribe({
        next: (res) => {
          this.output.set(res.output);
          if (res.error) this.error.set(res.error);
          this.loading.set(false);
          // Show dynamic completion
          this.nodes.update(n => [...n, { id: '4', title: 'Execution Complete', x: 400, y: 700 }]);
          this.edges.update(e => [...e, { from: '3', to: '4' }]);
        },
        error: (err) => {
          this.error.set('Failed to connect to backend: ' + err.message);
          this.loading.set(false);
        }
      });
  }
}
