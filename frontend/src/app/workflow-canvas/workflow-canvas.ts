import { Component, ChangeDetectionStrategy, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatCardModule } from '@angular/material/card';
import { VflowComponent, NodeHtmlTemplateDirective, HandleComponent, createNodes, createEdges } from 'ngx-vflow';

@Component({
  selector: 'app-workflow-canvas',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatInputModule,
    MatFormFieldModule,
    MatProgressSpinnerModule,
    MatCardModule,
    VflowComponent,
    NodeHtmlTemplateDirective,
    HandleComponent
  ],
  templateUrl: './workflow-canvas.html',
  styleUrls: ['./workflow-canvas.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WorkflowCanvas {
  prompt = signal('');
  output = signal<string | null>(null);
  loading = signal(false);
  error = signal<string | null>(null);

  // Canvas State using ngx-vflow
  nodes = signal(createNodes([
    { id: '1', type: 'html-template', point: { x: 300, y: 100 }, width: 220, height: 110, data: { title: 'START' } },
    { id: '2', type: 'html-template', point: { x: 300, y: 250 }, width: 220, height: 110, data: { title: 'Parse Task' } },
    { id: '3', type: 'html-template', point: { x: 300, y: 400 }, width: 220, height: 110, data: { title: 'Generate Code' } }
  ]));

  edges = signal(createEdges([
    { id: 'e1', source: '1', target: '2' },
    { id: 'e2', source: '2', target: '3' }
  ]));

  constructor(private http: HttpClient, private router: Router) {
    const nav = this.router.getCurrentNavigation();
    if (nav?.extras.state?.['prompt']) {
      this.prompt.set(nav.extras.state['prompt']);
      // Start processing right away
      this.submitPrompt();
    }
  }

  submitPrompt() {
    if (!this.prompt().trim()) return;
    this.loading.set(true);
    this.output.set(null);
    this.error.set(null);

    this.http.post<{output: string, error: string}>('http://localhost:8000/api/run', { prompt: this.prompt() })
      .subscribe({
        next: (res) => {
          if (res.error) {
            this.error.set(res.error);
          } else {
            this.output.set(res.output);
          }
          this.loading.set(false);
          // Show dynamic completion node
          this.nodes.update(n => [
            ...n,
            ...createNodes([{ id: '4', type: 'html-template', point: { x: 300, y: 550 }, width: 220, height: 110, data: { title: 'Execution Complete' } }])
          ]);
          this.edges.update(e => [
            ...e,
            ...createEdges([{ id: 'e3', source: '3', target: '4' }])
          ]);
        },
        error: (err) => {
          this.error.set('Failed to connect to backend: ' + err.message);
          this.loading.set(false);
        }
      });
  }
}
