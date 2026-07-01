import { Component, EventEmitter, Output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-prompt',
  imports: [FormsModule],
  template: `
    <div class="prompt-container">
      <textarea
        [(ngModel)]="promptText"
        placeholder="Enter your graph flow prompt here... (e.g., Generate a flow for checking emails)"
        rows="4">
      </textarea>
      <div class="actions">
        <button (click)="onRun()" [disabled]="!promptText() || isRunning()">
          @if (isRunning()) {
            <span class="spinner"></span> Running...
          } @else {
            Run Flow
          }
        </button>
      </div>
    </div>
  `,
  styles: [`
    .prompt-container {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 12px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      backdrop-filter: blur(10px);
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    textarea {
      width: 100%;
      background: rgba(0, 0, 0, 0.2);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      color: #fff;
      padding: 12px;
      font-family: 'Inter', sans-serif;
      font-size: 14px;
      resize: vertical;
      outline: none;
      transition: border-color 0.3s;
    }
    textarea:focus {
      border-color: #8a2be2;
    }
    .actions {
      display: flex;
      justify-content: flex-end;
    }
    button {
      background: linear-gradient(135deg, #8a2be2, #4b0082);
      color: white;
      border: none;
      padding: 10px 24px;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    button:hover:not([disabled]) {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(138, 43, 226, 0.4);
    }
    button[disabled] {
      opacity: 0.6;
      cursor: not-allowed;
    }
    .spinner {
      width: 16px;
      height: 16px;
      border: 2px solid rgba(255,255,255,0.3);
      border-top-color: #fff;
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  `]
})
export class PromptComponent {
  promptText = signal('');
  isRunning = signal(false);

  @Output() run = new EventEmitter<string>();

  onRun() {
    if (this.promptText()) {
      this.run.emit(this.promptText());
    }
  }

  setRunning(state: boolean) {
    this.isRunning.set(state);
  }
}
