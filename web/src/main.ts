import './style.css';
import { Header } from './components/Header';
import { Orb }    from './components/Orb';
import { Transcript } from './components/Transcript';
import { Composer } from './components/Composer';
import { Settings } from './components/Settings';
import { Toast } from './components/Toast';
import { bus } from './state';
import { bridge } from './bridge';
import type { AppConfig } from './types';

const root = document.getElementById('app')!;
root.className = 'h-screen flex flex-col';
root.innerHTML = '';

const header     = new Header(root);
const orb        = new Orb(root);
const transcript = new Transcript(root);
const composer   = new Composer(root);
const settings   = new Settings(document.body);
const toast      = new Toast(document.body);

// Constrain transcript so the orb keeps the visual lead
const transcriptEl = root.children[2] as HTMLElement;
transcriptEl.classList.remove('flex-1');
transcriptEl.classList.add('max-h-48', 'shrink-0');

let currentConfig: AppConfig | null = null;

bus.on((e) => {
  switch (e.type) {
    case 'status':
      header.setStatus(e.value);
      orb.setState(e.value);
      break;
    case 'transcript':
      transcript.push({ speaker: e.speaker, text: e.text, tool_call: e.tool_call });
      break;
    case 'transcript_start':
      if (e.speaker === 'assistant') transcript.startAssistant();
      break;
    case 'transcript_chunk':
      transcript.appendAssistant(e.text);
      // First chunk: flip orb to speaking-ish state
      if (header) header.setStatus('speaking');
      orb.setState('speaking');
      break;
    case 'transcript_end':
      transcript.endAssistant();
      break;
    case 'audio_level':
      orb.setRms(e.rms);
      break;
    case 'config':
      currentConfig = e.cfg;
      break;
    case 'toast':
      toast.show(e.level, e.message);
      break;
    case 'history_replay':
      transcript.replayHistory(e.items);
      break;
  }
});

composer.onSubmit((text) => { void bridge.sendText(text); });
composer.onRecord(() => { void bridge.startListening(); });
header.onSettingsClick(() => { if (currentConfig) settings.open(currentConfig); });
settings.onSave(async (cfg) => bridge.saveConfig(cfg as AppConfig));

function composerInput(): HTMLInputElement | null {
  return document.querySelector<HTMLInputElement>('footer [data-input]');
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  const target = e.target as HTMLElement;
  const inForm = target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT');

  // Cmd/Ctrl + , → open settings
  if ((e.metaKey || e.ctrlKey) && e.key === ',') {
    e.preventDefault();
    if (currentConfig) settings.open(currentConfig);
    return;
  }
  // Esc → close settings
  if (e.key === 'Escape') {
    settings.close();
    return;
  }
  if (inForm) return;
  // / → focus composer
  if (e.key === '/') {
    e.preventDefault();
    composerInput()?.focus();
    return;
  }
  // Cmd/Ctrl + K → focus composer
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault();
    composerInput()?.focus();
    return;
  }
});
