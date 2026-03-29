/**
 * INsight CLI — Type Definitions
 */

// ─── Theme Types ───────────────────────────────────────────────

export type ThemeName = 'forest' | 'light' | 'aurora';

export interface Theme {
  name: ThemeName;
  primary: (text: string) => string;
  secondary: (text: string) => string;
  dim: (text: string) => string;
  success: (text: string) => string;
  error: (text: string) => string;
  warning: (text: string) => string;
  info: (text: string) => string;
  code: (text: string) => string;
  border: (text: string) => string;
  // Raw hex values for Ink color props
  primaryHex: string;
  secondaryHex: string;
  dimHex: string;
  successHex: string;
  errorHex: string;
  warningHex: string;
  infoHex: string;
  borderHex: string;
}

// ─── Message Types ─────────────────────────────────────────────

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  subSteps?: SubStep[];
  isStreaming?: boolean;
  elapsed?: number;
  timestamp: Date;
}

export interface SubStep {
  label: string;
  status: 'pending' | 'active' | 'done' | 'error';
}

// ─── Config Types ──────────────────────────────────────────────

export interface AppConfig {
  theme: ThemeName;
  model: string;
  ollamaHost: string;
  lastProject?: string;
}

// ─── Command Types ─────────────────────────────────────────────

export interface Command {
  name: string;
  args?: string;
  description: string;
  action: () => void;
}

// ─── CLI Argument Types ────────────────────────────────────────

export interface CLIFlags {
  provider: string;
  model: string;
  persistDir: string;
  fileTypes: string;
  embedding: string;
  output: string;
  demo: boolean;
  theme: string;
}

// ─── Python Bridge Types ───────────────────────────────────────

export interface StreamChunk {
  token?: string;
  status?: string;
  sources?: string[];
  session_id?: string;
  final?: boolean;
  answer?: string;
  error?: string;
}

export interface AnalyzeProgress {
  status: string;
  file?: string;
  progress?: number;
  total?: number;
  done?: boolean;
  stats?: {
    documents: number;
    chunks: number;
    elapsed: number;
  };
}
