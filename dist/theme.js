/**
 * INsight CLI — Theme System
 *
 * 3 premium themes: forest (hero), light, aurora
 * Every color in the UI flows through this system — no hardcoded colors.
 */
import chalk from 'chalk';
import { getConfig } from './config.js';
// ─── Forest Theme (Hero Identity) ──────────────────────────────
// Green-on-black — the signature INsight look
const forest = {
    name: 'forest',
    primary: chalk.rgb(154, 232, 97),
    secondary: chalk.rgb(110, 231, 183),
    dim: chalk.rgb(74, 85, 104),
    success: chalk.rgb(72, 199, 142),
    error: chalk.rgb(252, 129, 129),
    warning: chalk.rgb(251, 191, 36),
    info: chalk.rgb(147, 197, 253),
    code: chalk.rgb(199, 210, 254),
    border: chalk.rgb(55, 65, 81),
    primaryHex: '#9ae861',
    secondaryHex: '#6ee7b7',
    dimHex: '#4a5568',
    successHex: '#48c78e',
    errorHex: '#fc8181',
    warningHex: '#fbbf24',
    infoHex: '#93c5fd',
    borderHex: '#374151',
};
// ─── Light Theme ───────────────────────────────────────────────
// Clean, professional day mode
const light = {
    name: 'light',
    primary: chalk.rgb(37, 99, 235),
    secondary: chalk.rgb(124, 58, 237),
    dim: chalk.rgb(156, 163, 175),
    success: chalk.rgb(22, 163, 74),
    error: chalk.rgb(220, 38, 38),
    warning: chalk.rgb(217, 119, 6),
    info: chalk.rgb(59, 130, 246),
    code: chalk.rgb(79, 70, 229),
    border: chalk.rgb(209, 213, 219),
    primaryHex: '#2563eb',
    secondaryHex: '#7c3aed',
    dimHex: '#9ca3af',
    successHex: '#16a34a',
    errorHex: '#dc2626',
    warningHex: '#d97706',
    infoHex: '#3b82f6',
    borderHex: '#d1d5db',
};
// ─── Aurora Theme ──────────────────────────────────────────────
// Vibrant neon — cyberpunk aesthetic
const aurora = {
    name: 'aurora',
    primary: chalk.rgb(167, 139, 250),
    secondary: chalk.rgb(244, 114, 182),
    dim: chalk.rgb(100, 116, 139),
    success: chalk.rgb(52, 211, 153),
    error: chalk.rgb(251, 113, 133),
    warning: chalk.rgb(253, 224, 71),
    info: chalk.rgb(103, 232, 249),
    code: chalk.rgb(196, 181, 253),
    border: chalk.rgb(71, 85, 105),
    primaryHex: '#a78bfa',
    secondaryHex: '#f472b6',
    dimHex: '#64748b',
    successHex: '#34d399',
    errorHex: '#fb7185',
    warningHex: '#fde047',
    infoHex: '#67e8f9',
    borderHex: '#475569',
};
// ─── Theme Registry ────────────────────────────────────────────
const themes = { forest, light, aurora };
/**
 * Get a theme by name
 */
export function getTheme(name) {
    return themes[name] || themes.forest;
}
/**
 * Get all available theme names
 */
export function getThemeNames() {
    return Object.keys(themes);
}
/**
 * Hook-like function: read current theme from config
 */
export function useTheme() {
    const config = getConfig();
    return getTheme(config.theme);
}
export { forest, light, aurora };
export default themes;
//# sourceMappingURL=theme.js.map