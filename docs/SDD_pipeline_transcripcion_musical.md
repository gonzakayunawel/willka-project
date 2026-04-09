# Software Design Document (SDD)
## Proyecto WILLKA
### Pipeline de Transcripción Musical: Audio → MIDI → Partitura
### Recuperación de "Desde Antofagasta a Tiahuanaco" (KayuNawel, 2009)

> **WILLKA** — *sagrado* en aymara. Lo que merece ser preservado.

---

**Nombre clave:** WILLKA  
**Versión:** 1.0.0  
**Fecha:** 2026-03-30  
**Autor:** Gonzalo Cayunao Erices (KayuNawel)  
**Estado:** Borrador — listo para implementación con Claude Code  

---

## 1. Introducción

### 1.1 Propósito
Este documento describe el diseño de software del pipeline de transcripción musical automatizado denominado **`audio2score`**. Su objetivo es recuperar la partitura orquestal de la obra "Desde Antofagasta a Tiahuanaco" a partir de un archivo de audio MP3 (renderizado originalmente en Cubase con instrumentación MIDI), produciendo como salida final archivos en formato MusicXML y PDF de partitura lista para edición en MuseScore 4.

### 1.2 Alcance
El sistema cubre tres etapas principales:
1. **Separación de stems** instrumentales desde el audio mixto.
2. **Transcripción automática** de cada stem a formato MIDI, usando modelos de IA.
3. **Conversión y ensamblaje** de los archivos MIDI en una partitura orquestal (MusicXML / PDF).

El sistema está diseñado para ejecutarse en entorno **WSL2 Ubuntu 24.04** sobre hardware con GPU NVIDIA (RTX 5060), aprovechando aceleración CUDA donde sea posible.

### 1.3 Definiciones y Acrónimos

| Término | Definición |
|---|---|
| AMT | Automatic Music Transcription |
| MIDI | Musical Instrument Digital Interface |
| MusicXML | Formato estándar de intercambio de partituras digitales |
| Stem | Pista de audio aislada por familia instrumental |
| SDD | Software Design Document |
| WSL2 | Windows Subsystem for Linux 2 |
| CQT | Constant-Q Transform |

### 1.4 Referencias
- Bittner et al. (2022). *A Lightweight Instrument-Agnostic Model for Polyphonic Note Transcription*. ICASSP 2022.
- Défossez et al. (2021). *Music Source Separation in the Waveform Domain*. Meta AI (Demucs).
- Cuthbert & Ariza (2010). *music21: A Toolkit for Computer-Aided Musicology*. MIT.
- Hawthorne et al. (2018). *Onsets and Frames: Dual-Objective Piano Transcription*. Google Magenta.

---

## 2. Descripción General del Sistema

### 2.1 Contexto
El archivo de entrada es `kayunawel_desde-antofagasta-a-tiahuanaco.mp3`, una renderización MIDI de una obra orquestal compuesta en Cubase circa 2009. Al ser una fuente MIDI renderizada (no grabación acústica), las notas son precisas y limpias, lo que favorece significativamente la precisión de los modelos de transcripción automática.

La obra tiene las siguientes características musicales relevantes para el pipeline:
- Formato: Orquesta juvenil.
- Escala predominante: Pentatónica (influencia andina/aymara).
- Familias instrumentales: Vientos madera, vientos metal, cuerdas, percusión.
- Énfasis rítmico nortino complejo.
- Duración estimada: ~5-8 minutos.

### 2.2 Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                      ENTRADA                                │
│          kayunawel_desde-antofagasta-a-tiahuanaco.mp3       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               ETAPA 1: SEPARACIÓN DE STEMS                  │
│                    Demucs (Meta AI)                         │
│          htdemucs_6s — 6 stems instrumentales               │
└──────┬──────────┬──────────┬──────────┬──────────┬──────────┘
       │          │          │          │          │
     drums     bass       piano      guitar     other
       │          │          │          │          │
       └──────────┴──────────┴──────────┴──────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│             ETAPA 2: TRANSCRIPCIÓN AUDIO → MIDI             │
│         Basic Pitch (Spotify) — modelo ICASSP 2022          │
│         Magenta Onsets & Frames (fallback/validación)       │
│              Salida: un archivo .mid por stem               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│             ETAPA 3: ENSAMBLAJE → PARTITURA                 │
│              music21 (MIT) — MIDI → MusicXML                │
│         MuseScore 4 CLI — MusicXML → PDF partitura          │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                       SALIDA                                │
│   partitura_completa.xml  |  partitura_completa.pdf         │
│   partes_individuales/    |  midis_por_stem/                │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Restricciones del Sistema
- Sistema operativo: Ubuntu 24.04 (WSL2).
- Python: 3.11+ gestionado con `uv`.
- GPU: NVIDIA RTX 5060 con soporte CUDA 12.x.
- MuseScore 4 debe estar instalado y accesible desde CLI.
- El archivo de entrada no debe superar 50 MB (el MP3 actual es ~7 MB, dentro del límite).

---

## 3. Diseño de Módulos

### 3.1 Estructura del Proyecto

```
willka/
├── pyproject.toml
├── README.md
├── .env.example
├── data/
│   ├── input/
│   │   └── kayunawel_desde-antofagasta-a-tiahuanaco.mp3
│   ├── stems/                  # salida Demucs
│   ├── midi/                   # salida Basic Pitch
│   └── output/
│       ├── musicxml/
│       ├── pdf/
│       └── partes/
├── src/
│   └── willka/
│       ├── __init__.py
│       ├── config.py           # configuración centralizada
│       ├── stem_separator.py   # Módulo 1: Demucs
│       ├── transcriber.py      # Módulo 2: Basic Pitch / Magenta
│       ├── score_builder.py    # Módulo 3: music21
│       ├── exporter.py         # Módulo 4: MuseScore CLI
│       └── pipeline.py         # Orquestador principal
├── tests/
│   ├── test_stem_separator.py
│   ├── test_transcriber.py
│   └── test_score_builder.py
└── notebooks/
    └── exploracion_stems.ipynb
```

### 3.2 Módulo 1 — `stem_separator.py`

**Responsabilidad:** Separar el audio mixto en stems instrumentales usando Demucs.

**Dependencias:**
```
demucs>=4.0.0
torch>=2.0.0
torchaudio>=2.0.0
```

**Interfaz pública:**
```python
class StemSeparator:
    def __init__(self, model: str = "htdemucs_6s", device: str = "cuda"):
        ...

    def separate(self, audio_path: Path, output_dir: Path) -> dict[str, Path]:
        """
        Separa el audio en stems.

        Args:
            audio_path: Ruta al archivo MP3/WAV de entrada.
            output_dir: Directorio donde se guardan los stems.

        Returns:
            Diccionario {nombre_stem: ruta_archivo_wav}
            Ej: {"drums": Path("stems/drums.wav"), "other": Path("stems/other.wav")}
        """
```

**Stems esperados (modelo htdemucs_6s):**
- `drums` → Percusión
- `bass` → Línea de bajo / contrabajos
- `piano` → Teclados / arpa / instrumentos melódicos de percusión
- `guitar` → Cuerdas (violines, violas, cellos — mapeados aquí)
- `vocals` → No aplica para esta obra (se descarta)
- `other` → Vientos madera y metal

**Notas de diseño:**
- Usar `device="cuda"` si CUDA disponible, `"cpu"` como fallback.
- Loggear tiempo de separación por stem.
- El stem `vocals` se descarta automáticamente para esta obra.

---

### 3.3 Módulo 2 — `transcriber.py`

**Responsabilidad:** Convertir cada stem WAV a archivo MIDI usando Basic Pitch como motor primario y Magenta como validación opcional.

**Dependencias:**
```
basic-pitch>=0.3.0
pretty_midi>=0.2.10
numpy>=1.24.0
```

**Interfaz pública:**
```python
class AudioTranscriber:
    def __init__(
        self,
        onset_threshold: float = 0.5,
        frame_threshold: float = 0.3,
        minimum_note_length: float = 0.058,
        minimum_frequency: float | None = None,
        maximum_frequency: float | None = None,
    ):
        ...

    def transcribe(self, stem_path: Path, output_path: Path) -> Path:
        """
        Transcribe un archivo WAV monocanal a MIDI.

        Args:
            stem_path: Ruta al stem WAV.
            output_path: Ruta de salida para el archivo .mid.

        Returns:
            Ruta al archivo MIDI generado.
        """

    def transcribe_all(
        self, stems: dict[str, Path], output_dir: Path
    ) -> dict[str, Path]:
        """
        Transcribe todos los stems en paralelo.

        Returns:
            Diccionario {nombre_stem: ruta_midi}
        """
```

**Parámetros de ajuste fino para música orquestal:**
| Parámetro | Valor recomendado | Justificación |
|---|---|---|
| `onset_threshold` | 0.4 | Vientos tienen ataques suaves |
| `frame_threshold` | 0.25 | Notas largas de cuerdas |
| `minimum_note_length` | 0.100 | Evitar notas fantasma en cuerdas |
| `minimum_frequency` | 40 Hz | Rango contrabajo |
| `maximum_frequency` | 4200 Hz | Rango piccolo/violín agudo |

**Notas de diseño:**
- Procesar stems en paralelo usando `concurrent.futures.ThreadPoolExecutor`.
- Guardar también el CSV de note events para análisis posterior.
- Escala pentatónica esperada: aplicar post-procesamiento opcional de quantización armónica.

---

### 3.4 Módulo 3 — `score_builder.py`

**Responsabilidad:** Ensamblar los archivos MIDI individuales en una partitura orquestal usando music21, asignando cada stem a su familia instrumental correcta.

**Dependencias:**
```
music21>=9.0.0
```

**Mapeo de stems a instrumentos:**
```python
STEM_TO_INSTRUMENT = {
    "other":  ["Flute", "Oboe", "Clarinet", "Bassoon", "Horn", "Trumpet", "Trombone"],
    "guitar": ["Violin", "Viola", "Cello", "Contrabass"],
    "bass":   ["Contrabass"],
    "piano":  ["Harp", "Timpani"],
    "drums":  ["Timpani", "Percussion"],
}
```

**Interfaz pública:**
```python
class ScoreBuilder:
    def __init__(self, title: str, composer: str, tempo: int = 100):
        ...

    def build(self, midi_files: dict[str, Path]) -> music21.stream.Score:
        """
        Construye un Score de music21 a partir de los MIDIs por stem.

        Args:
            midi_files: Diccionario {nombre_stem: ruta_midi}

        Returns:
            Objeto Score de music21 listo para exportar.
        """

    def set_metadata(
        self,
        title: str,
        composer: str,
        year: int,
        notes: str = ""
    ) -> None:
        """Agrega metadatos a la partitura."""

    def export_musicxml(self, score: music21.stream.Score, output_path: Path) -> Path:
        """Exporta la partitura a MusicXML."""

    def export_midi_merged(self, score: music21.stream.Score, output_path: Path) -> Path:
        """Exporta MIDI unificado de toda la partitura."""
```

**Metadatos de la obra:**
```python
OBRA_METADATA = {
    "title":    "Desde Antofagasta a Tiahuanaco",
    "composer": "Gonzalo Cayunao Erices (KayuNawel)",
    "year":     2009,
    "notes":    "Mención Honrosa — Concurso Bicentenario de Chile, Antofagasta. "
                "Obra programática para orquesta juvenil basada en música típica "
                "del norte de Chile. Escala pentatónica. Énfasis en vientos y maderas.",
}
```

---

### 3.5 Módulo 4 — `exporter.py`

**Responsabilidad:** Generar los archivos de salida finales (PDF de partitura completa, partes individuales por instrumento) usando MuseScore 4 CLI.

**Dependencias:**
```
subprocess (stdlib)
musescore4 >= 4.0 (instalado en sistema)
```

**Interfaz pública:**
```python
class ScoreExporter:
    def __init__(self, musescore_path: str = "/usr/bin/mscore4"):
        ...

    def to_pdf(self, musicxml_path: Path, output_path: Path) -> Path:
        """Genera PDF de partitura completa."""

    def to_parts(self, musicxml_path: Path, output_dir: Path) -> list[Path]:
        """Genera PDF de parte individual por instrumento."""

    def to_png(self, musicxml_path: Path, output_dir: Path) -> list[Path]:
        """Genera imágenes PNG por página (para previsualización)."""
```

---

### 3.6 Módulo 5 — `pipeline.py`

**Responsabilidad:** Orquestar la ejecución secuencial de todos los módulos, con logging, manejo de errores y reporte de progreso.

**Interfaz pública:**
```python
class TranscriptionPipeline:
    def __init__(self, config: PipelineConfig):
        ...

    def run(self, input_audio: Path) -> PipelineResult:
        """
        Ejecuta el pipeline completo.

        Etapas:
          1. Validación del archivo de entrada.
          2. Separación de stems (Demucs).
          3. Transcripción MIDI por stem (Basic Pitch).
          4. Construcción de partitura (music21).
          5. Exportación PDF y partes (MuseScore CLI).

        Returns:
            PipelineResult con rutas de todos los archivos generados
            y métricas de ejecución.
        """
```

**Dataclasses de configuración:**
```python
@dataclass
class PipelineConfig:
    input_dir:       Path = Path("data/input")
    stems_dir:       Path = Path("data/stems")
    midi_dir:        Path = Path("data/midi")
    output_dir:      Path = Path("data/output")
    demucs_model:    str  = "htdemucs_6s"
    device:          str  = "cuda"          # "cpu" como fallback
    onset_threshold: float = 0.4
    frame_threshold: float = 0.25
    tempo_bpm:       int  = 100
    musescore_path:  str  = "/usr/bin/mscore4"
    log_level:       str  = "INFO"

@dataclass
class PipelineResult:
    success:        bool
    stems:          dict[str, Path]
    midis:          dict[str, Path]
    musicxml_path:  Path
    pdf_path:       Path
    parts_dir:      Path
    elapsed_seconds: float
    errors:         list[str]
```

---

## 4. Dependencias y Entorno

### 4.1 `pyproject.toml`
```toml
[project]
name = "willka"
version = "1.0.0"
description = "WILLKA — Pipeline de transcripción musical: MP3 → MIDI → Partitura orquestal"
authors = [{ name = "Gonzalo Cayunao Erices", email = "kayunawel@example.com" }]
requires-python = ">=3.11"

dependencies = [
    "demucs>=4.0.0",
    "basic-pitch>=0.3.0",
    "music21>=9.0.0",
    "pretty_midi>=0.2.10",
    "torch>=2.0.0",
    "torchaudio>=2.0.0",
    "numpy>=1.24.0",
    "librosa>=0.10.0",
    "soundfile>=0.12.0",
    "rich>=13.0.0",       # logging con color y progress bars
    "typer>=0.9.0",       # CLI
    "pydantic>=2.0.0",    # validación de configuración
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov",
    "jupyter",
    "matplotlib",
]

[project.scripts]
willka = "willka.pipeline:app"
```

### 4.2 Instalación del entorno (WSL2 Ubuntu 24.04)
```bash
# 1. Crear entorno con uv
uv venv .venv --python 3.11
source .venv/bin/activate

# 2. Instalar dependencias
uv pip install -e ".[dev]"

# 3. Instalar PyTorch con soporte CUDA 12.x
uv pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# 4. Instalar MuseScore 4
sudo apt install musescore4

# 5. Verificar instalación
audio2score --version
```

### 4.3 Workaround libexpat (conocido en este entorno)
```bash
# Agregar al .bashrc / activación del entorno
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libexpat.so.1
```

---

## 5. Interfaz de Línea de Comandos (CLI)

```bash
# Uso básico — ejecutar pipeline completo
willka run data/input/kayunawel_desde-antofagasta-a-tiahuanaco.mp3

# Ejecutar solo separación de stems
willka stems data/input/kayunawel.mp3 --output data/stems/

# Ejecutar solo transcripción (desde stems ya generados)
willka transcribe data/stems/ --output data/midi/

# Ejecutar solo generación de partitura (desde MIDIs ya generados)
willka build data/midi/ --title "Desde Antofagasta a Tiahuanaco" --composer "KayuNawel"

# Opciones globales
willka run audio.mp3 --device cpu        # forzar CPU
willka run audio.mp3 --no-gpu            # alias de --device cpu
willka run audio.mp3 --log-level DEBUG   # verbose
willka run audio.mp3 --config config.toml
```

---

## 6. Flujo de Datos Detallado

```
INPUT: kayunawel_desde-antofagasta-a-tiahuanaco.mp3
       │
       │  [Validación: formato, duración, bitrate]
       │
       ▼
STEMS: data/stems/
       ├── drums.wav       → Percusión orquestal
       ├── bass.wav        → Contrabajos / línea grave
       ├── piano.wav       → Arpa / celesta / instrumentos melódicos
       ├── guitar.wav      → Familia de cuerdas (violines, violas, cellos)
       ├── other.wav       → Vientos madera y metal (protagonistas de la obra)
       └── vocals.wav      → DESCARTADO (no aplica)
       │
       │  [Basic Pitch — un proceso por stem en paralelo]
       │
       ▼
MIDI:  data/midi/
       ├── drums.mid
       ├── bass.mid
       ├── piano.mid
       ├── guitar.mid
       └── other.mid
       │
       │  [music21 — ensamblaje + metadatos + cuantización]
       │
       ▼
XML:   data/output/musicxml/
       └── desde_antofagasta_a_tiahuanaco.xml
       │
       │  [MuseScore 4 CLI]
       │
       ▼
PDF:   data/output/pdf/
       ├── desde_antofagasta_a_tiahuanaco_full_score.pdf
       └── partes/
           ├── flute.pdf
           ├── oboe.pdf
           ├── clarinet.pdf
           ├── trumpet.pdf
           ├── violin_I.pdf
           └── ...
```

---

## 7. Manejo de Errores

| Situación | Comportamiento esperado |
|---|---|
| Archivo de entrada no encontrado | `FileNotFoundError` con mensaje descriptivo, abort pipeline |
| CUDA no disponible | Warning + fallback automático a CPU |
| Stem vacío (silencio total) | Skip con warning, continuar con otros stems |
| Basic Pitch falla en un stem | Retry con Magenta como fallback |
| MuseScore no instalado | Error claro con instrucción de instalación |
| MusicXML malformado | Guardar MIDI y notificar al usuario para revisión manual |
| `libexpat` conflict (WSL2) | Detectar y aplicar `LD_PRELOAD` automáticamente |

---

## 8. Testing

### 8.1 Estrategia
- **Unit tests:** Cada módulo por separado con archivos WAV/MIDI de prueba cortos (~5 segundos).
- **Integration test:** Pipeline completo con el MP3 real.
- **Validación musical:** Revisión manual de la partitura generada en MuseScore 4.

### 8.2 Estructura de tests
```bash
tests/
├── fixtures/
│   ├── test_audio.wav          # 5s de audio sintético
│   ├── test_stem.wav           # stem de prueba
│   └── test.mid                # MIDI de referencia
├── test_stem_separator.py
├── test_transcriber.py
├── test_score_builder.py
└── test_pipeline.py
```

### 8.3 Comando de ejecución
```bash
pytest tests/ -v --cov=src/willka --cov-report=html
```

---

## 9. Limitaciones Conocidas y Trabajo Futuro

### 9.1 Limitaciones de la versión 1.0
- Basic Pitch funciona mejor con una sola fuente instrumental por stem. La separación con Demucs puede no ser perfecta para orquesta densa.
- La asignación automática de instrumentos es aproximada. La partitura generada requerirá **revisión manual en MuseScore 4**, especialmente en:
  - Definición exacta de compases y figuras rítmicas (el paso MIDI→MusicXML es con pérdida).
  - Dinámicas y articulaciones (no recuperables desde MIDI).
  - Asignación de partes individuales dentro de cada familia.
- La escala pentatónica puede generar artefactos en la cuantización automática de notas.

### 9.2 Mejoras futuras (v1.1+)
- Agregar cuantización armónica configurable para escala pentatónica.
- Integrar API de Klangio como motor alternativo para stems complejos.
- Interfaz web con Gradio o Streamlit para uso sin CLI.
- Exportación a formato LilyPond para tipografía musical de mayor calidad.
- Fine-tuning del modelo Basic Pitch con dataset de música andina.

---

## 10. Notas para Claude Code

Al implementar este proyecto, considerar:

1. **Entorno:** WSL2 Ubuntu 24.04, Python 3.11 via `uv`, GPU RTX 5060 CUDA 12.x.
2. **Workaround obligatorio:** Aplicar `LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libexpat.so.1` al iniciar.
3. **Archivo de entrada disponible:** `kayunawel_desde-antofagasta-a-tiahuanaco.mp3` (~7 MB, MIDI renderizado en Cubase).
4. **Fuente MIDI renderizada:** La calidad de transcripción será superior a audio acústico. Aprovechar esto ajustando los thresholds de Basic Pitch hacia valores más agresivos.
5. **Prioridad de implementación:** `stem_separator.py` → `transcriber.py` → `score_builder.py` → `exporter.py` → `pipeline.py`.
6. **Tests primero:** Implementar al menos `test_transcriber.py` antes de correr el pipeline completo sobre el archivo real.

---

*Proyecto WILLKA — Documento generado como especificación base para implementación con Claude Code.*  
*Versión 1.0.0 — 2026-03-30*
