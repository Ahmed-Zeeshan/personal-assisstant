import { bus } from './state';
import type { AppConfig, VAEvent } from './types';

declare global {
  interface Window {
    pywebview: {
      api: {
        start_listening(): Promise<void>;
        stop_listening():  Promise<void>;
        send_text(text: string): Promise<void>;
        get_config(): Promise<AppConfig>;
        save_config(cfg: AppConfig & { _secret?: string }): Promise<{ok: boolean; errors?: string[]}>;
        quit(): Promise<void>;
      };
    };
    va: {
      emit(event: VAEvent): void;
    };
  }
}

// Python pushes events here: window.va.emit(...).
window.va = {
  emit: (event: VAEvent) => bus.emit(event),
};

const hasPy = (): boolean => typeof window !== 'undefined' && typeof window.pywebview !== 'undefined';

export const bridge = {
  startListening: async () => hasPy() ? window.pywebview.api.start_listening() : void 0,
  stopListening:  async () => hasPy() ? window.pywebview.api.stop_listening()  : void 0,
  sendText:       async (text: string) => hasPy() ? window.pywebview.api.send_text(text) : void 0,
  getConfig:      async (): Promise<AppConfig> => hasPy()
    ? window.pywebview.api.get_config()
    : ({ provider: 'anthropic', model: 'claude-sonnet-4-6', hotkey: 'ctrl+shift+space', allowed_roots: ['~'], ollama_base_url: null } as AppConfig),
  saveConfig:     async (cfg: AppConfig & { _secret?: string }) => hasPy()
    ? window.pywebview.api.save_config(cfg)
    : ({ ok: true } as const),
  quit:           async () => hasPy() ? window.pywebview.api.quit() : void 0,
};

// Tell Python that the page is ready, in case it wants to push an initial config.
if (hasPy()) {
  // pywebview readiness — pywebviewready DOM event fires when window.pywebview is injected
  document.addEventListener('pywebviewready', () => {
    void bridge.getConfig().then((cfg) => bus.emit({ type: 'config', cfg }));
  });
} else {
  // Browser dev: push a fake config after a tick.
  setTimeout(async () => {
    const cfg = await bridge.getConfig();
    bus.emit({ type: 'config', cfg });
  }, 100);
}
