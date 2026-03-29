/**
 * CommandPalette — Slash-command popup with live filtering.
 */
import React from 'react';
import type { Command } from '../types.js';
interface Props {
    commands: Command[];
    filter: string;
    selectedIndex: number;
    onSelect: (cmd: Command) => void;
    onClose: () => void;
}
export declare function CommandPalette({ commands, filter, selectedIndex, onSelect, onClose }: Props): React.ReactElement;
export {};
//# sourceMappingURL=CommandPalette.d.ts.map