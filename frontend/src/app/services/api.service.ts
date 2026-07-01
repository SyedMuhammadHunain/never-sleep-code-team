import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface RunResponse {
  output: string;
  error: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private http = inject(HttpClient);
  private runUrl = 'http://localhost:8000/api/run';
  private workflowUrl = 'http://localhost:8000/api/workflow';

  runAgent(prompt: string): Observable<RunResponse> {
    return this.http.post<RunResponse>(this.runUrl, { prompt });
  }

  getWorkflowGraph(): Observable<{ nodes: any[], edges: any[] }> {
    return this.http.get<{ nodes: any[], edges: any[] }>(this.workflowUrl);
  }
}
