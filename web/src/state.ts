import type { VAEvent } from './types';

type Listener = (e: VAEvent) => void;

class Bus {
  private listeners: Listener[] = [];
  emit(e: VAEvent): void { for (const l of this.listeners) l(e); }
  on(l: Listener): () => void {
    this.listeners.push(l);
    return () => { this.listeners = this.listeners.filter(x => x !== l); };
  }
}

export const bus = new Bus();
