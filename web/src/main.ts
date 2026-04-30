import './style.css';
import { Header } from './components/Header';
import { Transcript } from './components/Transcript';
import { Composer } from './components/Composer';

const root = document.getElementById('app')!;
root.className = 'h-screen flex flex-col';
root.innerHTML = '';

const header = new Header(root);
const transcript = new Transcript(root);
const composer = new Composer(root);

composer.onSubmit((text) => transcript.push({ speaker: 'user', text }));
composer.onRecord(() => header.setStatus('listening'));
header.onSettingsClick(() => console.log('settings'));
