import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './app.html',
  styleUrls: ['./app.css']
})
export class App {
  title = 'never-sleep-code-team-frontend';
  prompt = signal('');
  output = signal<string | null>(null);
  loading = signal(false);
  error = signal<string | null>(null);

  constructor(private http: HttpClient) {}

  submitPrompt() {
    if (!this.prompt().trim()) return;

    this.loading.set(true);
    this.output.set(null);
    this.error.set(null);
    console.log(this.prompt());
    this.http.post<{output: string, error: string}>('http://localhost:8000/api/run', { prompt: this.prompt() })
      .subscribe({
        next: (res) => {
          console.log("This is response: ", res);
          this.output.set(res.output);
          if (res.error) {
             this.error.set(res.error);
          }
          this.loading.set(false);
        },
        error: (err) => {
          this.error.set('Failed to connect to backend: ' + err.message);
          this.loading.set(false);
        }
      });
  }
}
