import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';

export interface RunResponse {
  output: string;
  error: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private http = inject(HttpClient);
  private workflowUrl = 'http://localhost:8000/api/workflow';
  private ws: WebSocket | null = null;
  public messages$ = new Subject<any>();

  runAgent(prompt: string) {
    if (this.ws) {
      this.ws.close();
    }
    this.ws = new WebSocket('ws://localhost:8000/api/ws/run');

    this.ws.onopen = () => {
      this.ws?.send(JSON.stringify({ prompt }));
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.messages$.next(data);
    };

    this.ws.onerror = (error) => {
      this.messages$.error(error);
    };

    this.ws.onclose = () => {
      this.messages$.complete();
      // Recreate subject for next run
      this.messages$ = new Subject<any>();
    };
  }

  sendInput(text: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'input', data: text }));
    }
  }

  getWorkflowGraph(): Observable<{ nodes: any[], edges: any[] }> {
    return this.http.get<{ nodes: any[], edges: any[] }>(this.workflowUrl);
  }
}
