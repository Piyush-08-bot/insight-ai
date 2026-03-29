/**
 * INsight CLI — Persistent Configuration
 *
 * Uses `conf` to store user preferences (theme, model, host)
 * across sessions in ~/.config/insight-ai/config.json
 */

import Conf from 'conf';
import type { AppConfig, ThemeName } from './types.js';

const defaults: AppConfig = {
  theme: 'forest',
  model: 'qwen2.5-coder:latest',
  ollamaHost: 'http://localhost:11434',
};

const config = new Conf<AppConfig>({
  projectName: 'insight-ai',
  defaults,
});

export function getConfig(): AppConfig {
  return {
    theme: config.get('theme') as ThemeName,
    model: config.get('model'),
    ollamaHost: config.get('ollamaHost'),
    lastProject: config.get('lastProject'),
  };
}

export function setConfig(updates: Partial<AppConfig>): void {
  for (const [key, value] of Object.entries(updates)) {
    if (value !== undefined) {
      config.set(key as keyof AppConfig, value);
    }
  }
}

export function setTheme(theme: ThemeName): void {
  config.set('theme', theme);
}

export function setModel(model: string): void {
  config.set('model', model);
}

export function setLastProject(projectPath: string): void {
  config.set('lastProject', projectPath);
}

export { config };
