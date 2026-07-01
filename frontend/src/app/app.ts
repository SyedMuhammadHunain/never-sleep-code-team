import { Component, ViewChild, signal, OnInit, ChangeDetectionStrategy } from '@angular/core';
import { PromptComponent } from './components/prompt/prompt.component';
import { GraphComponent } from './components/graph/graph.component';
import { ThemeToggle } from './components/theme-toggle/theme-toggle';
import { ToastComponent } from './components/toast/toast';
import { SkeletonComponent } from './components/skeleton/skeleton';
import { ToastService } from './services/toast';
import { ApiService, RunResponse } from './services/api.service';
import { Node, Edge } from '@swimlane/ngx-graph';

@Component({
  selector: 'app-root',
  imports: [PromptComponent, GraphComponent, ThemeToggle, ToastComponent, SkeletonComponent],
  templateUrl: './app.html',
  styleUrl: './app.css',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class App implements OnInit {
  @ViewChild(PromptComponent) promptComponent!: PromptComponent;

  nodes = signal<Node[]>([]);
  edges = signal<Edge[]>([]);
  status = signal<'Idle' | 'Running' | 'Completed' | 'Failed'>('Idle');

  constructor(private apiService: ApiService, private toastService: ToastService) {}

  private cachedGraph: any = null;

  ngOnInit() {
    this.apiService.getWorkflowGraph().subscribe({
      next: (res) => {
        this.cachedGraph = res;
        this.setGraphData(res);
      },
      error: (err) => {
        console.error('Failed to load workflow graph:', err);
        this.toastService.show('Failed to load workflow graph', 'error');
      }
    });
  }

  private setGraphData(res: any) {
    const graphNodes: Node[] = res.nodes.map((n: any) => ({
      id: n.id,
      label: n.label,
      dimension: { width: Math.max(120, n.label.length * 10), height: 40 },
      data: { active: false }
    }));
    const graphEdges: Edge[] = res.edges.map((e: any) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      label: e.label
    }));
    this.nodes.set(graphNodes);
    this.edges.set(graphEdges);
  }

  private activeNodeInterval: any;

  onRun(prompt: string) {
    this.promptComponent.setRunning(true);
    this.status.set('Running');

    // Clear nodes to show skeleton loader (Phase 4)
    this.nodes.set([]);
    this.edges.set([]);

    // Simulate delay for "generation" to show skeleton, then show graph
    setTimeout(() => {
      if (this.cachedGraph) {
        this.setGraphData(this.cachedGraph);
      }

      // Simulate active nodes running one by one (Phase 5)
      let activeIdx = 0;
      this.activeNodeInterval = setInterval(() => {
        const currentNodes = this.nodes();
        if (currentNodes.length > 0) {
          const updatedNodes = currentNodes.map((n, i) => ({
            ...n,
            data: { active: i === activeIdx }
          }));
          this.nodes.set(updatedNodes);
          activeIdx = (activeIdx + 1) % updatedNodes.length;
        }
      }, 1000);
    }, 2000);

    this.apiService.runAgent(prompt).subscribe({
      next: (res: RunResponse) => {
        console.log('Result:', res);
        clearInterval(this.activeNodeInterval);
        this.clearActiveNodes();
        this.promptComponent.setRunning(false);
        this.status.set('Completed');
        this.toastService.show('Workflow completed successfully', 'success');
      },
      error: (err) => {
        console.error('Error:', err);
        clearInterval(this.activeNodeInterval);
        this.clearActiveNodes();
        this.promptComponent.setRunning(false);
        this.status.set('Failed');
        this.toastService.show('Workflow failed to run', 'error');
      }
    });
  }

  private clearActiveNodes() {
    const updatedNodes = this.nodes().map(n => ({
      ...n,
      data: { active: false }
    }));
    this.nodes.set(updatedNodes);
  }
}
