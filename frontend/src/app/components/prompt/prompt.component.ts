import { Component, EventEmitter, Output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-prompt',
  imports: [FormsModule],
  template: `
    <div class="prompt-container">
      <label for="prompt-input" class="sr-only">Graph flow prompt</label>
      <textarea
        id="prompt-input"
        [(ngModel)]="promptText"
        placeholder="Enter your graph flow prompt here... (e.g., Generate a flow for checking emails)"
        rows="4">
      </textarea>
      <div class="actions">
        <button (click)="onRun()" [disabled]="!promptText() || isRunning()" aria-live="polite">
          @if (isRunning()) {
            <span class="spinner" aria-hidden="true"></span> <span class="sr-only">Running...</span>
          } @else {
            Run Flow
          }
        </button>
      </div>
    </div>
  `,
  styles: [`
    .prompt-container {
      background-color: var(--color-bg-base);
      border: 1px solid var(--color-border);
      border-radius: 12px;
      padding: var(--spacing-4);
      display: flex;
      flex-direction: column;
      gap: var(--spacing-3);
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
    }

    .sr-only {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }

    textarea {
      width: 100%;
      background-color: var(--color-bg-surface-hover);
      border: 1px solid var(--color-border);
      border-radius: 8px;
      color: var(--color-text-primary);
      padding: var(--spacing-3);
      font-family: inherit;
      font-size: 0.875rem;
      resize: vertical;
      outline: none;
      transition: border-color 0.2s ease-in-out;
      box-sizing: border-box;
    }

    textarea:focus {
      border-color: var(--color-brand);
    }

    textarea::placeholder {
      color: var(--color-text-secondary);
    }

    .actions {
      display: flex;
      justify-content: flex-end;
    }

    button {
      background-color: var(--color-brand);
      color: white;
      border: 1px solid transparent;
      padding: var(--spacing-2) var(--spacing-4);
      border-radius: 6px;
      font-weight: 500;
      font-size: 0.875rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: var(--spacing-2);
      transition: background-color 0.2s ease-in-out;
      min-width: 100px;
    }

    button:hover:not([disabled]) {
      background-color: var(--color-brand-hover);
    }

    button[disabled] {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .spinner {
      width: 1rem;
      height: 1rem;
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-top-color: currentColor;
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
