"""WILLKA - Pipeline de transcripción musical: MP3 → MIDI → Partitura orquestal"""

__version__ = "1.0.0"
__author__ = "Gonzalo Cayunao Erices"
__email__ = "kayunawel@example.com"

# Exportar la app CLI
from .cli import app

__all__ = ["app", "__version__"]
