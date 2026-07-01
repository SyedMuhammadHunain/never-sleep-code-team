import { Component, Input } from '@angular/core';
import { NgxGraphModule, Node, Edge } from '@swimlane/ngx-graph';

@Component({
  selector: 'app-graph',
  imports: [NgxGraphModule],
  template: `
    <div class="graph-wrapper" aria-label="Workflow graph visualization">
      @if (nodes.length > 0) {
        <ngx-graph
          class="chart-container"
          [nodes]="nodes"
          [links]="links"
          [autoZoom]="true"
          [autoCenter]="true"
          layout="dagre">

          <ng-template #nodeTemplate let-node>
            <svg:g class="node">
              <svg:rect
                [attr.width]="node.dimension.width"
                [attr.height]="node.dimension.height"
                [attr.fill]="getColor(node.label)"
                rx="6" ry="6" />
              <svg:text alignment-baseline="central" [attr.x]="12" [attr.y]="node.dimension.height / 2" fill="var(--color-bg-base)" font-family="inherit" font-size="0.875rem" font-weight="500">
                {{node.label}}
              </svg:text>
            </svg:g>
          </ng-template>

          <ng-template #linkTemplate let-link>
            <svg:g class="edge">
              <svg:path class="line" stroke-width="2" marker-end="url(#arrow)"></svg:path>
            </svg:g>
          </ng-template>

          <ng-template #defsTemplate>
            <svg:marker id="arrow" viewBox="0 -5 10 10" refX="8" refY="0" markerWidth="6" markerHeight="6" orient="auto">
              <svg:path d="M0,-5L10,0L0,5" class="arrow-head"/>
            </svg:marker>
          </ng-template>
        </ngx-graph>
      } @else {
        <div class="empty-state" role="status" aria-label="No graph data">
          <svg aria-hidden="true" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="opacity: 0.5; margin-bottom: 12px;">
            <circle cx="18" cy="5" r="3"></circle>
            <circle cx="6" cy="12" r="3"></circle>
            <circle cx="18" cy="19" r="3"></circle>
            <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
            <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
          </svg>
          <h3 style="margin: 0 0 4px 0; font-size: 1rem; color: var(--color-text-primary);">No workflow generated</h3>
          <p style="margin: 0; font-size: 0.875rem; color: var(--color-text-secondary);">Enter a prompt to generate and visualize a workflow graph.</p>
        </div>
      }
    </div>
  `,
  styles: [`
    .graph-wrapper {
      width: 100%;
      height: 100%;
      position: absolute;
      top: 0;
      left: 0;
      display: flex;
      justify-content: center;
      align-items: center;
      background-color: var(--color-bg-base);
    }
    ::ng-deep .ngx-graph {
      width: 100% !important;
      height: 100% !important;
    }
    .line { stroke: var(--color-border-focus); fill: none; opacity: 0.6; }
    .arrow-head { fill: var(--color-border-focus); opacity: 0.6; }
    .node rect { stroke: var(--color-border); stroke-width: 1px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .empty-state {
      color: var(--color-text-secondary);
      border: 2px dashed var(--color-border);
      padding: var(--spacing-8);
      border-radius: 8px;
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
      max-width: 320px;
    }
  `]
})
export class GraphComponent {
  @Input() nodes: Node[] = [];
  @Input() links: Edge[] = [];

  getColor(label: string): string {
    // Return a solid semantic color instead of bright AI aesthetic purple
    if (label === 'user') return 'var(--color-brand-hover)';
    if (label.includes('workflow')) return 'var(--color-brand)';
    return 'var(--color-text-secondary)';
  }
}
