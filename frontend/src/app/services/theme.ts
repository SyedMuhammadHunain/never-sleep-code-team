import { Injectable, signal, computed, effect } from '@angular/core';

export type Theme = 'light' | 'dark' | 'system';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private readonly THEME_KEY = 'app-theme-preference';

  // The user's explicitly selected theme
  readonly themePreference = signal<Theme>('system');

  // The resolved active theme based on preference and system OS setting
  readonly activeTheme = computed(() => {
    const pref = this.themePreference();
    if (pref === 'system') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return pref;
  });

  constructor() {
    // Load from local storage on init
    const saved = localStorage.getItem(this.THEME_KEY) as Theme;
    if (saved && ['light', 'dark', 'system'].includes(saved)) {
      this.themePreference.set(saved);
    } else {
      this.themePreference.set('system');
    }

    // Effect to apply the theme to the body
    effect(() => {
      const isDark = this.activeTheme() === 'dark';
      if (isDark) {
        document.body.classList.add('dark');
      } else {
        document.body.classList.remove('dark');
      }
    });

    // Listen for system theme changes if set to system
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (this.themePreference() === 'system') {
        // Trigger a recomputation by briefly flipping and restoring
        this.themePreference.set('system');
      }
    });
  }

  setTheme(theme: Theme) {
    this.themePreference.set(theme);
    localStorage.setItem(this.THEME_KEY, theme);
  }
}
