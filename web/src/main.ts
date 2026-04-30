import './style.css';
import { Header } from './components/Header';
import { Transcript } from './components/Transcript';
import { Composer } from './components/Composer';
import { Orb } from './components/Orb';

const root = document.getElementById('app')!;
root.className = 'h-screen flex flex-col';
root.innerHTML = '';

const header = new Header(root);
const orb = new Orb(root);
const transcript = new Transcript(root);
const composer = new Composer(root);

// Restrict transcript to a max height so the orb stays centered
const transcriptEl = root.children[2] as HTMLElement;
transcriptEl.classList.remove('flex-1');
transcriptEl.classList.add('max-h-48', 'shrink-0');

composer.onSubmit((text) => {
  transcript.push({ speaker: 'user', text });
  orb.setState('thinking');
  setTimeout(() => orb.setState('idle'), 800);  // demo only; replaced by bridge events later
});
composer.onRecord(() => orb.setState('listening'));
header.onSettingsClick(() => console.log('settings'));
