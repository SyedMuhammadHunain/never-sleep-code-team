import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', loadComponent: () => import('./home/home').then(m => m.Home) },
  { path: 'canvas', loadComponent: () => import('./workflow-canvas/workflow-canvas').then(m => m.WorkflowCanvas) }
];
