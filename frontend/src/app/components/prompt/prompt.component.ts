import { Component, EventEmitter, Output, signal, ChangeDetectionStrategy } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-prompt',
  imports: [FormsModule],
  template: `
    <div class="prompt-wrapper">
      <div class="prompt-container">
        <label for="prompt-input" class="sr-only">Graph flow prompt</label>
        <div class="input-group">
          <input
            type="text"
            id="prompt-input"
            [(ngModel)]="promptText"
            (keyup.enter)="onRun()"
            placeholder="Enter your graph flow prompt here... (e.g., Generate a flow for checking emails)"
            autocomplete="off"
          />
          <button class="run-button" (click)="onRun()" [disabled]="!promptText() || isRunning()" aria-label="Run Flow">
            @if (isRunning()) {
              <span class="spinner" aria-hidden="true"></span>
            } @else {
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
            }
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .prompt-wrapper {
      position: fixed;
      bottom: var(--spacing-8);
      left: 50%;
      transform: translateX(-50%);
      width: 100%;
      max-width: 768px;
      padding: 0 var(--spacing-4);
      z-index: 50;
      box-sizing: border-box;
      pointer-events: none;
    }

    .prompt-container {
      background-color: var(--color-bg-surface);
      border: 1px solid var(--color-border);
      border-radius: 24px;
      padding: var(--spacing-2) var(--spacing-2) var(--spacing-2) var(--spacing-4);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
      pointer-events: auto;
      transition: box-shadow 0.2s ease;
    }

    .prompt-container:focus-within {
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15), 0 0 0 2px var(--color-brand-alpha, rgba(var(--color-brand-rgb), 0.2));
      border-color: var(--color-brand);
    }

    .input-group {
      display: flex;
      align-items: center;
      gap: var(--spacing-2);
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

    input {
      flex: 1;
      background: transparent;
      border: none;
      color: var(--color-text-primary);
      padding: var(--spacing-2) 0;
      font-family: inherit;
      font-size: 1rem;
      outline: none;
      min-width: 0;
    }

    input::placeholder {
      color: var(--color-text-secondary);
    }

    .run-button {
      background-color: var(--color-brand);
      color: white;
      border: none;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: transform 0.1s ease, background-color 0.2s ease;
      flex-shrink: 0;
    }

    .run-button:hover:not([disabled]) {
      background-color: var(--color-brand-hover);
      transform: scale(1.05);
    }

    .run-button:active:not([disabled]) {
      transform: scale(0.95);
    }

    .run-button[disabled] {
      background-color: var(--color-bg-surface-hover);
      color: var(--color-text-secondary);
      cursor: not-allowed;
    }

    .spinner {
      width: 1.25rem;
      height: 1.25rem;
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-top-color: currentColor;
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush
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
