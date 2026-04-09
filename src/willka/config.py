"""Configuración centralizada para el pipeline WILLKA."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PipelineConfig:
    """Configuración del pipeline de transcripción."""

    # Directorios
    input_dir: Path = Path("data/input")
    stems_dir: Path = Path("data/stems")
    midi_dir: Path = Path("data/midi")
    output_dir: Path = Path("data/output")

    # Configuración Demucs
    demucs_model: str = "htdemucs_6s"
    device: str = "cuda"  # "cpu" como fallback

    # Configuración Basic Pitch
    onset_threshold: float = 0.4
    frame_threshold: float = 0.25
    minimum_note_length: float = 0.100
    minimum_frequency: float | None = 40.0  # Hz (rango contrabajo)
    maximum_frequency: float | None = 4200.0  # Hz (rango piccolo/violín agudo)

    # Configuración partitura
    tempo_bpm: int = 100
    title: str = "Desde Antofagasta a Tiahuanaco"
    composer: str = "Gonzalo Cayunao Erices (KayuNawel)"
    year: int = 2009

    # Configuración MuseScore
    musescore_path: str = "/usr/bin/mscore4"

    # Logging
    log_level: str = "INFO"

    def __post_init__(self) -> None:
        """Convierte strings a Paths después de la inicialización."""
        self.input_dir = Path(self.input_dir)
        self.stems_dir = Path(self.stems_dir)
        self.midi_dir = Path(self.midi_dir)
        self.output_dir = Path(self.output_dir)


# Metadatos de la obra según SDD
OBRA_METADATA: dict[str, str | int] = {
    "title": "Desde Antofagasta a Tiahuanaco",
    "composer": "Gonzalo Cayunao Erices (KayuNawel)",
    "year": 2009,
    "notes": "Mención Honrosa — Concurso Bicentenario de Chile, Antofagasta. "
    "Obra programática para orquesta juvenil basada en música típica "
    "del norte de Chile. Escala pentatónica. Énfasis en vientos y maderas.",
}

# Mapeo de stems a instrumentos según SDD
STEM_TO_INSTRUMENT: dict[str, list[str]] = {
    "other": ["Flute", "Oboe", "Clarinet", "Bassoon", "Horn", "Trumpet", "Trombone"],
    "guitar": ["Violin", "Viola", "Cello", "Contrabass"],
    "bass": ["Contrabass"],
    "piano": ["Harp", "Timpani"],
    "drums": ["Timpani", "Percussion"],
}
