/**
 * App — Root component that routes to Chat, Analyze, or Setup.
 */
import React from 'react';
interface Props {
    command: string;
    args: string[];
    flags: {
        provider?: string;
        model?: string;
        persistDir?: string;
        fileTypes?: string;
        embedding?: string;
        output?: string;
        demo?: boolean;
        theme?: string;
    };
}
export declare function App({ command, args, flags }: Props): React.ReactElement;
export {};
//# sourceMappingURL=App.d.ts.map