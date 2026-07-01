import { Component, Input } from '@angular/core';
import { NgxGraphModule, Node, Edge } from '@swimlane/ngx-graph';

@Component({
  selector: 'app-graph',
  imports: [NgxGraphModule],
  template: `
    <div class="graph-wrapper">
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
                rx="8" ry="8" />
              <svg:text alignment-baseline="central" [attr.x]="15" [attr.y]="node.dimension.height / 2" fill="#fff" font-family="Inter" font-size="14" font-weight="500">
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
        <div class="empty-state">
          Loading Workflow Graph...
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
    }
    ::ng-deep .ngx-graph {
      width: 100% !important;
      height: 100% !important;
    }
    .line { stroke: #bbaaff; fill: none; opacity: 0.6; }
    .arrow-head { fill: #bbaaff; opacity: 0.6; }
    .node rect { stroke: rgba(255, 255, 255, 0.1); stroke-width: 1px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .empty-state {
      color: rgba(255, 255, 255, 0.4);
      font-weight: 500;
      border: 2px dashed rgba(255, 255, 255, 0.1);
      padding: 40px;
      border-radius: 16px;
      text-align: center;
      max-width: 400px;
    }
  `]
})
export class GraphComponent {
  @Input() nodes: Node[] = [];
  @Input() links: Edge[] = [];

  getColor(label: string): string {
    if (label === 'user') return '#4b0082';
    if (label.includes('workflow')) return '#8a2be2';
    return '#6a5acd';
  }
}
