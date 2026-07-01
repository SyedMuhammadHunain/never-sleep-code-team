import { Component, ChangeDetectionStrategy } from '@angular/core';

@Component({
  selector: 'app-skeleton',
  standalone: true,
  template: `
    <div class="skeleton-container" aria-busy="true" aria-label="Loading content">
      <div class="skeleton-card">
        <div class="skeleton-header">
          <div class="skeleton-circle"></div>
          <div class="skeleton-line title"></div>
        </div>
        <div class="skeleton-content">
          <div class="skeleton-line"></div>
          <div class="skeleton-line"></div>
          <div class="skeleton-line short"></div>
        </div>
      </div>
      <div class="skeleton-card">
        <div class="skeleton-header">
          <div class="skeleton-circle"></div>
          <div class="skeleton-line title"></div>
        </div>
        <div class="skeleton-content">
          <div class="skeleton-line"></div>
          <div class="skeleton-line short"></div>
        </div>
      </div>
      <div class="skeleton-card">
        <div class="skeleton-header">
          <div class="skeleton-circle"></div>
          <div class="skeleton-line title"></div>
        </div>
        <div class="skeleton-content">
          <div class="skeleton-line"></div>
          <div class="skeleton-line"></div>
          <div class="skeleton-line"></div>
          <div class="skeleton-line short"></div>
        </div>
      </div>
    </div>
  `,
  styles: `
    .skeleton-container {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-4);
      width: 100%;
      max-width: 600px;
      margin: 0 auto;
      padding: var(--spacing-6);
    }

    .skeleton-card {
      background-color: var(--color-bg-surface);
      border: 1px solid var(--color-border);
      border-radius: 12px;
      padding: var(--spacing-4);
      display: flex;
      flex-direction: column;
      gap: var(--spacing-4);
    }

    .skeleton-header {
      display: flex;
      align-items: center;
      gap: var(--spacing-3);
    }

    .skeleton-content {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-2);
    }

    .skeleton-circle, .skeleton-line {
      background: linear-gradient(
        90deg,
        var(--color-bg-surface-hover) 25%,
        var(--color-border) 50%,
        var(--color-bg-surface-hover) 75%
      );
      background-size: 200% 100%;
      animation: pulse 1.5s ease-in-out infinite;
      border-radius: 4px;
    }

    .skeleton-circle {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      flex-shrink: 0;
    }

    .skeleton-line {
      height: 12px;
      width: 100%;
    }

    .skeleton-line.title {
      width: 40%;
      height: 16px;
    }

    .skeleton-line.short {
      width: 70%;
    }

    @keyframes pulse {
      0% { background-position: 200% 0; }
      100% { background-position: -200% 0; }
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class SkeletonComponent {}
