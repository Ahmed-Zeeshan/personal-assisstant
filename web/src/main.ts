import './style.css';
import { Background } from './components/Background';
import { Header } from './components/Header';
import { Avatar } from './components/Avatar';
import { ChatTranscript } from './components/ChatTranscript';
import { ListeningWave } from './components/ListeningWave';
import { Composer } from './components/Composer';
import { Settings } from './components/Settings';
import { Toast } from './components/Toast';
import { HistoryPanel } from './components/HistoryPanel';
import { TransparencyModal } from './components/TransparencyModal';
import { Onboarding } from './components/Onboarding';
import { bus } from './state';
import { bridge } from './bridge';
import type { AppConfig } from './types';
import { setLocale } from './i18n';

// ── Root layout ────────────────────────────────────────────────────────────
const root = document.getElementById('app')!;
root.className = 'va-app';
root.innerHTML = '';

// Animated gradient background (sits behind everything via position:fixed)
new Background(document.body);

// ── Layout shell ────────────────────────────────────────────────────────────
// Two-pane at ≥1024px: history sidebar on left, main content on right.
// Single column below 1024px.
const shell = document.createElement('div');
shell.className = 'va-shell';
root.appendChild(shell);

// Left pane: history panel (only rendered at ≥1024px via CSS)
const historyPanel = new HistoryPanel(shell);

// Right pane: main content
const main = document.createElement('div');
main.className = 'va-main';
shell.appendChild(main);

const header     = new Header(main);
const avatar     = new Avatar(main, 'aria');
const wave       = new ListeningWave(main);
const transcript = new ChatTranscript(main);
const composer   = new Composer(main);
const settings          = new Settings(document.body);
const toast             = new Toast(document.body);
const transparencyModal = new TransparencyModal(document.body);
const onboarding        = new Onboarding(document.body);

let currentConfig: AppConfig | null = null;

// ── RTL / language direction ────────────────────────────────────────────────
function setDirection(lang: string): void {
  const rtl = ['ur', 'ar', 'he', 'fa'].includes(lang);
  document.documentElement.dir = rtl ? 'rtl' : 'ltr';
  document.documentElement.lang = lang || 'en';
}

// ── Display preferences (high-contrast, font-size) ─────────────────────────
function applyDisplayPrefs(cfg: AppConfig): void {
  const html = document.documentElement;
  // High-contrast theme
  if (cfg.display_theme === 'hc') {
    html.setAttribute('data-theme', 'hc');
  } else {
    html.removeAttribute('data-theme');
  }
  // Font size
  const sizeMap: Record<string, string> = {
    small:  '87.5%',
    medium: '100%',
    large:  '112.5%',
    xl:     '125%',
  };
  html.style.fontSize = sizeMap[cfg.display_font_size ?? 'medium'] ?? '100%';
}

// ── Layout styles ───────────────────────────────────────────────────────────
(function injectLayoutStyles() {
  if (document.querySelector('#va-layout-style')) return;
  const s = document.createElement('style');
  s.id = 'va-layout-style';
  s.textContent = `
    #app.va-app {
      height: 100vh;
      width: 100%;
      display: flex;
      flex-direction: column;
      position: relative;
      z-index: 1;
    }
    .va-shell {
      display: flex;
      flex: 1;
      min-height: 0;
      overflow: hidden;
    }
    .va-main {
      display: flex;
      flex-direction: column;
      flex: 1;
      min-width: 0;
      min-height: 0;
    }
    /* At ≥1024px: history sidebar visible */
    @media (min-width: 1024px) {
      .va-shell { flex-direction: row; }
    }
  `;
  document.head.appendChild(s);
})();

// ── Event bus ───────────────────────────────────────────────────────────────
bus.on((e) => {
  switch (e.type) {
    case 'status':
      header.setStatus(e.value);
      avatar.setState(e.value);
      if (e.value === 'listening') {
        wave.show();
      } else {
        wave.hide();
      }
      break;
    case 'transcript':
      transcript.push({ speaker: e.speaker, text: e.text, tool_call: e.tool_call });
      break;
    case 'transcript_start':
      if (e.speaker === 'assistant') transcript.startAssistant();
      break;
    case 'transcript_chunk':
      transcript.appendAssistant(e.text);
      header.setStatus('speaking');
      avatar.setState('speaking');
      break;
    case 'transcript_end':
      transcript.endAssistant();
      break;
    case 'audio_level':
      avatar.setRms(e.rms);
      break;
    case 'config':
      currentConfig = e.cfg;
      avatar.setAvatar(currentConfig.avatar ?? 'aria');
      // i18n: pick locale
      {
        const cfgLocale = currentConfig.locale ?? 'auto';
        const resolvedLocale = cfgLocale === 'auto'
          ? (navigator.language?.split('-')[0] ?? 'en')
          : cfgLocale;
        setLocale(resolvedLocale);
        // RTL direction
        const dirLang = currentConfig.respond_in === 'auto'
          ? (currentConfig.user_address_language ?? resolvedLocale)
          : (currentConfig.respond_in ?? resolvedLocale);
        setDirection(dirLang);
      }
      // Display preferences
      applyDisplayPrefs(currentConfig);
      // AI Act first-run disclosure
      if (!currentConfig.transparency_acknowledged) {
        transparencyModal.show(currentConfig.provider, async () => {
          const acked: AppConfig = { ...currentConfig!, transparency_acknowledged: true };
          await bridge.saveConfig(acked);
          currentConfig = acked;
        });
      }
      // First-run onboarding tour
      if (!currentConfig.onboarding_seen) {
        onboarding.show(async () => {
          const seen: AppConfig = { ...currentConfig!, onboarding_seen: true };
          await bridge.saveConfig(seen);
          currentConfig = seen;
        });
      }
      break;
    case 'toast':
      toast.show(e.level, e.message);
      break;
    case 'history_replay':
      transcript.replayHistory(e.items);
      historyPanel.populate(e.items);
      break;
  }
});

// ── Wiring ───────────────────────────────────────────────────────────────────
composer.onSubmit(({ text, images }) => { void bridge.sendText(text, images.length > 0 ? images : undefined); });
composer.onRecord(() => { void bridge.startListening(); });
header.onSettingsClick(() => { if (currentConfig) settings.open(currentConfig); });
settings.onSave(async (cfg) => bridge.saveConfig(cfg as AppConfig));
settings.onShowOnboarding(() => {
  onboarding.show(async () => {
    if (currentConfig) {
      const seen: AppConfig = { ...currentConfig, onboarding_seen: true };
      await bridge.saveConfig(seen);
      currentConfig = seen;
    }
  });
});

// ── Keyboard shortcuts ───────────────────────────────────────────────────────
document.addEventListener('keydown', (e) => {
  const target = e.target as HTMLElement;
  const inForm = target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT');

  if ((e.metaKey || e.ctrlKey) && e.key === ',') {
    e.preventDefault();
    if (currentConfig) settings.open(currentConfig);
    return;
  }
  if (e.key === 'Escape') {
    settings.close();
    return;
  }
  if (inForm) return;
  if (e.key === '/') {
    e.preventDefault();
    document.querySelector<HTMLTextAreaElement>('footer [data-input]')?.focus();
    return;
  }
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault();
    document.querySelector<HTMLTextAreaElement>('footer [data-input]')?.focus();
    return;
  }
});
