/**
 * INsight CLI — Persistent Configuration
 *
 * Uses `conf` to store user preferences (theme, model, host)
 * across sessions in ~/.config/insight-ai/config.json
 */
import Conf from 'conf';
const defaults = {
    theme: 'forest',
    model: 'qwen2.5-coder:latest',
    ollamaHost: 'http://localhost:11434',
};
const config = new Conf({
    projectName: 'insight-ai',
    defaults,
});
export function getConfig() {
    return {
        theme: config.get('theme'),
        model: config.get('model'),
        ollamaHost: config.get('ollamaHost'),
        lastProject: config.get('lastProject'),
    };
}
export function setConfig(updates) {
    for (const [key, value] of Object.entries(updates)) {
        if (value !== undefined) {
            config.set(key, value);
        }
    }
}
export function setTheme(theme) {
    config.set('theme', theme);
}
export function setModel(model) {
    config.set('model', model);
}
export function setLastProject(projectPath) {
    config.set('lastProject', projectPath);
}
export { config };
//# sourceMappingURL=config.js.map