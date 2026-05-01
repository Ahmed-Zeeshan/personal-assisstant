export type Provider = 'anthropic'|'openai'|'gemini'|'ollama';

export interface AppConfig {
  provider: Provider;
  model: string;
  hotkey: string;
  allowed_roots: string[];
  ollama_base_url: string | null;
  has_secret?: boolean;
  available_models?: Record<Provider, string[]>;
  user_name: string | null;
  user_address_as: 'first_name' | 'full_name' | 'title' | 'none';
  user_title: string | null;
  respond_in?: string;
  voice: string;
  stt_language: string;
  avatar: string;
  audio_trigger?: string;
  wake_word?: string;
  wake_sensitivity?: number;
  available_voices?: { id: string; label: string; language: string; gender: string; engine: string; notes: string }[];
  available_stt_languages?: { code: string; label: string }[];
  available_avatars?: string[];
  /** BCP-47 locale code or "auto" */
  locale?: string;
  /** Display preferences */
  display_theme?: 'default' | 'hc';
  display_font_size?: 'small' | 'medium' | 'large' | 'xl';
  /** AI Act: whether the first-run disclosure has been acknowledged */
  transparency_acknowledged?: boolean;
  /** Used for direction detection when respond_in is "auto" */
  user_address_language?: string;
  /** First-run onboarding tour */
  onboarding_seen?: boolean;
}

export type HistoryItem = { speaker: 'user' | 'assistant'; text: string; ts?: string };

export type VAEvent =
  | { type: 'status';            value: 'idle'|'listening'|'thinking'|'speaking'|'error' }
  | { type: 'transcript';        speaker: 'user'|'assistant'; text: string; tool_call?: string }
  | { type: 'transcript_start';  speaker: 'user'|'assistant' }
  | { type: 'transcript_chunk';  text: string }
  | { type: 'transcript_end' }
  | { type: 'tool_invoked';      name: string }
  | { type: 'audio_level';       rms: number }
  | { type: 'config';            cfg: AppConfig }
  | { type: 'toast';             level: 'info'|'warn'|'error'; message: string }
  | { type: 'history_replay';    items: HistoryItem[] };
