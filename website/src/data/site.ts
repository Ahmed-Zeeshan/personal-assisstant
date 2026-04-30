export const site = {
  brand: 'voice-assistant',
  repoUrl: 'https://github.com/Ahmed-Zeeshan/personal-assisstant',
  tagline: 'Talk to your computer.',
  subhead: 'A local-first voice assistant that opens apps, manages files, and sends email — driven by the LLM of your choice.',
  eyebrow: 'PHASE 1 · OPEN SOURCE · LOCAL-FIRST',
  navLinks: [
    { href: '#features', label: 'Features' },
    { href: '#install', label: 'Install' },
    { href: '#safety', label: 'Safety' },
  ],
  trust: {
    label: 'Powered by your choice of',
    providers: ['Claude', 'GPT', 'Gemini', 'Ollama'],
  },
  features: [
    { title: 'Voice in', body: 'Global hotkey + faster-whisper. 100% local — audio never leaves your machine.' },
    { title: 'LLM brain', body: 'Pluggable via LiteLLM: Anthropic Claude, OpenAI GPT, Google Gemini, or local Ollama.' },
    { title: 'Voice out', body: 'Piper TTS, fully local. No streaming, no cloud, no per-request cost.' },
    { title: 'File tools', body: 'Create, read, move, delete — scoped to directories you whitelist. Symlink escapes blocked.' },
    { title: 'System tools', body: 'Open URLs and launch desktop apps by name. Safe-by-default URL parsing.' },
    { title: 'Email', body: 'Send mail through Gmail with the gmail.send scope only. No read access ever requested.' },
  ],
  steps: [
    { title: 'Hotkey',     body: 'Press ctrl+shift+space.' },
    { title: 'Transcribe', body: 'faster-whisper, on-device.' },
    { title: 'Decide',     body: 'Your LLM picks a tool.' },
    { title: 'Act + Reply', body: 'Run the tool, speak the result.' },
  ],
  install: {
    macos:   { prereq: 'Requires Python 3.11+ and a microphone.', cmd: 'curl -fsSL https://personal-assisstant-gamma.vercel.app/install.sh | bash', run: 'voice-assistant', note: 'The installer asks for your LLM provider and API key. Default hotkey: ctrl+shift+space.' },
    linux:   { prereq: 'Requires Python 3.11+, portaudio, and espeak-ng.', cmd: 'curl -fsSL https://personal-assisstant-gamma.vercel.app/install.sh | bash', run: 'voice-assistant', note: 'The installer asks for your LLM provider and API key. Default hotkey: ctrl+shift+space.' },
    windows: { prereq: 'Requires Python 3.11+ and a microphone.', cmd: 'iwr -useb https://personal-assisstant-gamma.vercel.app/install.ps1 | iex', run: 'voice-assistant', note: 'The installer asks for your LLM provider and API key. Default hotkey: ctrl+shift+space.' },
  },
  safety: [
    { title: 'Path-scoped filesystem', body: 'Tools refuse paths outside your allowed_roots. Symlink and .. traversal blocked.' },
    { title: 'Destructive-op confirmation', body: 'Deletes and overwrites require explicit confirmation from the brain.' },
    { title: 'Delete rate limit', body: 'A configurable cap on deletes per minute prevents runaway loops.' },
    { title: 'Prompt-injection defence', body: 'The brain treats tool-returned data as untrusted — instructions inside file contents are ignored.' },
  ],
  faq: [
    { q: 'Is my voice sent to the cloud?', a: 'No. Speech-to-text runs locally via faster-whisper. Only the transcribed text is sent to the LLM you configure.' },
    { q: 'Which LLM should I use?',         a: 'Any of Claude, GPT, Gemini, or local Ollama. Pick by cost, capability, or privacy preference — they all support tool use.' },
    { q: 'Does it work offline?',           a: 'Audio in/out is fully local. The LLM brain needs network unless you run Ollama locally.' },
    { q: 'How do I revoke Gmail access?',   a: 'Visit your Google Account → Security → Third-party access and remove "voice-assistant", then delete the cached oauth-token.json.' },
    { q: 'How do I uninstall?',             a: 'Re-run the install command with --uninstall. It removes the venv and launcher symlink and asks before touching your config.' },
    { q: 'Why no mobile or web version?',   a: 'The product runs against your desktop apps and filesystem — that does not exist on mobile or the web.' },
  ],
  footer: {
    author: 'Zeeshan Ahmed',
    license: 'Private — not for redistribution.',
  },
};
