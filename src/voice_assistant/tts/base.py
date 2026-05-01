"""Speaker abstract base class. Each engine implements `speak(text)`."""
from __future__ import annotations
from abc import ABC, abstractmethod


class Speaker(ABC):
    @abstractmethod
    def speak(self, text: str) -> None:
        """Synthesise and play `text`. Blocks until playback finishes."""
        raise NotImplementedError
