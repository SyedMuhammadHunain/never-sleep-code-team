import { Routes } from '@angular/router';
import { Home } from './home/home';
import { WorkflowCanvas } from './workflow-canvas/workflow-canvas';

export const routes: Routes = [
  { path: '', component: Home },
  { path: 'canvas', component: WorkflowCanvas }
];
