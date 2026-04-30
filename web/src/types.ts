export type Provider = 'anthropic'|'openai'|'gemini'|'ollama';

export interface AppConfig {
  provider: Provider;
  model: string;
  hotkey: string;
  allowed_roots: string[];
  ollama_base_url: string | null;
  has_secret?: boolean;
  available_models?: Record<Provider, string[]>;
}

export type VAEvent =
  | { type: 'status';      value: 'idle'|'listening'|'thinking'|'speaking'|'error' }
  | { type: 'transcript';  speaker: 'user'|'assistant'; text: string; tool_call?: string }
  | { type: 'audio_level'; rms: number }
  | { type: 'config';      cfg: AppConfig }
  | { type: 'toast';       level: 'info'|'warn'|'error'; message: string };
