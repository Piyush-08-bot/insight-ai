/**
 * INsight CLI — Theme System
 *
 * 3 premium themes: forest (hero), light, aurora
 * Every color in the UI flows through this system — no hardcoded colors.
 */
import type { Theme, ThemeName } from './types.js';
declare const forest: Theme;
declare const light: Theme;
declare const aurora: Theme;
declare const themes: Record<ThemeName, Theme>;
/**
 * Get a theme by name
 */
export declare function getTheme(name: ThemeName): Theme;
/**
 * Get all available theme names
 */
export declare function getThemeNames(): ThemeName[];
/**
 * Hook-like function: read current theme from config
 */
export declare function useTheme(): Theme;
export { forest, light, aurora };
export default themes;
//# sourceMappingURL=theme.d.ts.map