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
import { bus } from './state';
import { bridge } from './bridge';
import type { AppConfig } from './types';

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
const settings   = new Settings(document.body);
const toast      = new Toast(document.body);

let currentConfig: AppConfig | null = null;

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
composer.onSubmit((text) => { void bridge.sendText(text); });
composer.onRecord(() => { void bridge.startListening(); });
header.onSettingsClick(() => { if (currentConfig) settings.open(currentConfig); });
settings.onSave(async (cfg) => bridge.saveConfig(cfg as AppConfig));

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
