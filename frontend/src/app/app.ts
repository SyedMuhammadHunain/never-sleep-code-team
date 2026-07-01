import { Component, ViewChild, signal, OnInit } from '@angular/core';
import { PromptComponent } from './components/prompt/prompt.component';
import { GraphComponent } from './components/graph/graph.component';
import { ApiService, RunResponse } from './services/api.service';
import { Node, Edge } from '@swimlane/ngx-graph';

@Component({
  selector: 'app-root',
  imports: [PromptComponent, GraphComponent],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit {
  @ViewChild(PromptComponent) promptComponent!: PromptComponent;

  nodes = signal<Node[]>([]);
  edges = signal<Edge[]>([]);
  status = signal<'Idle' | 'Running' | 'Completed' | 'Failed'>('Idle');

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.apiService.getWorkflowGraph().subscribe({
      next: (res) => {
        const graphNodes: Node[] = res.nodes.map(n => ({
          id: n.id,
          label: n.label,
          dimension: { width: Math.max(120, n.label.length * 10), height: 40 }
        }));
        const graphEdges: Edge[] = res.edges.map(e => ({
          id: e.id,
          source: e.source,
          target: e.target,
          label: e.label
        }));
        this.nodes.set(graphNodes);
        this.edges.set(graphEdges);
      },
      error: (err) => console.error('Failed to load workflow graph:', err)
    });
  }

  onRun(prompt: string) {
    this.promptComponent.setRunning(true);
    this.status.set('Running');

    this.apiService.runAgent(prompt).subscribe({
      next: (res: RunResponse) => {
        console.log('Result:', res);
        this.promptComponent.setRunning(false);
        this.status.set('Completed');
      },
      error: (err) => {
        console.error('Error:', err);
        this.promptComponent.setRunning(false);
        this.status.set('Failed');
      }
    });
  }
}
