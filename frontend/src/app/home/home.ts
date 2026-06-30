import { Component, signal } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './home.html',
  styleUrls: ['./home.css']
})
export class Home {
  prompt = signal('');

  constructor(private router: Router) {}

  submitPrompt() {
    if (!this.prompt().trim()) return;
    // Redirect to canvas page and pass the prompt
    this.router.navigate(['/canvas'], { state: { prompt: this.prompt() } });
  }
}
