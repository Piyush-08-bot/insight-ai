/**
 * INsight CLI — Persistent Configuration
 *
 * Uses `conf` to store user preferences (theme, model, host)
 * across sessions in ~/.config/insight-ai/config.json
 */
import Conf from 'conf';
import type { AppConfig, ThemeName } from './types.js';
declare const config: Conf<AppConfig>;
export declare function getConfig(): AppConfig;
export declare function setConfig(updates: Partial<AppConfig>): void;
export declare function setTheme(theme: ThemeName): void;
export declare function setModel(model: string): void;
export declare function setLastProject(projectPath: string): void;
export { config };
//# sourceMappingURL=config.d.ts.map