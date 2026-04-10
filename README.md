# WILLKA 🎵

<!-- Language Selector -->
<div align="center">
  <a href="#español">🇪🇸 Español</a> | 
  <a href="#english">🇬🇧 English</a>
</div>

---

<a name="español"></a>
## 🇪🇸 Español

**WILLKA** — *sagrado* en aymara. Lo que merece ser preservado.

Pipeline de transcripción musical automatizado: **Audio → MIDI → Partitura orquestal**

### 🎯 Objetivo

Recuperar partituras orquestales a partir de archivos de audio MP3, produciendo como salida final archivos en formato MusicXML y PDF listos para edición en MuseScore 4.

### 🚀 Características

- **Separación instrumental**: Usa Demucs para separar audio en stems instrumentales
- **Transcripción automática**: Basic Pitch para convertir audio a MIDI
- **Ensamblaje orquestal**: music21 para construir partituras completas
- **Exportación profesional**: MuseScore 4 para generar PDF y partes individuales
- **Interfaz CLI**: Comandos intuitivos con Typer y Rich para feedback visual

### 📁 Estructura del Proyecto

```
willka/
├── data/
│   ├── input/           # Archivos de audio de entrada
│   ├── stems/           # Stems separados (WAV)
│   ├── midi/            # Archivos MIDI generados
│   └── output/
│       ├── musicxml/    # Partituras MusicXML
│       ├── pdf/         # PDF de partitura
│       └── partes/      # Partes individuales por instrumento
├── src/willka/
│   ├── config.py        # Configuración centralizada
│   ├── stem_separator.py # Módulo 1: Demucs
│   ├── transcriber.py   # Módulo 2: Basic Pitch
│   ├── score_builder.py # Módulo 3: music21
│   ├── exporter.py      # Módulo 4: MuseScore CLI
│   ├── pipeline.py      # Módulo 5: Orquestador principal
│   └── cli.py           # Interfaz de línea de comandos
└── tests/               # Pruebas unitarias
```

### 🛠️ Instalación

#### Requisitos previos
- Python 3.11+
- `uv` (gestor de paquetes moderno)
- MuseScore 4 (opcional, para exportación real)

#### Instalación rápida

```bash
# 1. Clonar repositorio
git clone <repo-url>
cd willka

# 2. Crear entorno virtual e instalar dependencias
uv venv .venv
source .venv/bin/activate
uv sync

# 3. Instalar en modo desarrollo
uv pip install -e .

# 4. Verificar instalación
willka check
```

#### Instalar MuseScore 4 (recomendado)

```bash
# Ubuntu/Debian
sudo apt install software-properties-common
sudo add-apt-repository ppa:mscore-ubuntu/mscore4-stable
sudo apt update
sudo apt install musescore4

# Verificar instalación
mscore4 --version
```

### 🎮 Uso

#### Comandos principales

```bash
# Pipeline completo
willka run audio.mp3 --device cuda --output resultados/

# Solo separación de stems
willka stems audio.mp3 --output stems/ --device cpu

# Solo transcripción a MIDI
willka transcribe stems/ --output midi/ --onset 0.4 --frame 0.25

# Solo construcción de partitura
willka build midi/ --output partitura/ --title "Mi Obra" --composer "Yo"

# Verificar sistema
willka check
```

#### Ejemplo completo

```bash
# 1. Probar con audio de ejemplo
willka run data/input/test_complex.wav --device cpu

# 2. Ver resultados
ls -la data/output/
```

### 🔧 Configuración

La configuración se maneja a través de:
- Valores por defecto en `src/willka/config.py`
- Opciones de línea de comandos
- Archivo de configuración TOML (próximamente)

#### Parámetros clave de transcripción

```python
# Optimizados para música orquestal
onset_threshold = 0.4      # Vientos tienen ataques suaves
frame_threshold = 0.25     # Notas largas de cuerdas
minimum_note_length = 0.100 # Evitar notas fantasma
frequency_range = 40-4200 Hz # Rango orquestal completo
```

### 🧪 Testing

```bash
# Pruebas básicas
python test_basic.py

# Prueba completa con mocks
python test_complete_mock.py

# Prueba de pipeline real (requiere ffmpeg)
willka stems data/input/test_complex.wav --device cpu
```

### 📊 Flujo de procesamiento

```
INPUT: audio.mp3
        │
        ▼
STEMS: drums.wav, bass.wav, piano.wav, guitar.wav, other.wav
        │
        ▼
MIDI: drums.mid, bass.mid, piano.mid, guitar.mid, other.mid
        │
        ▼
PARTITURA: obra.xml (MusicXML)
        │
        ▼
SALIDA: obra.pdf, partes/*.pdf, png/*.png
```

### 🎼 Mapeo de instrumentos

Cada stem se mapea a familias instrumentales:

| Stem | Instrumentos |
|------|--------------|
| `other` | Vientos madera y metal |
| `guitar` | Cuerdas (violines, violas, cellos, contrabajos) |
| `bass` | Contrabajos |
| `piano` | Arpa, timbales |
| `drums` | Percusión orquestal |

### ⚠️ Limitaciones conocidas

1. **Demucs requiere ffmpeg/ffprobe** para algunos formatos de audio
2. **Basic Pitch** puede tener problemas con audio complejo
3. **MuseScore 4** debe estar instalado para exportación real
4. **Music21** tiene problemas de importación con algunos instrumentos
5. **GPU requerida** para procesamiento rápido de audio largo

### 🚧 Trabajo futuro

- [ ] Integración con Klangio API
- [ ] Interfaz web con Streamlit
- [ ] Fine-tuning para música andina
- [ ] Exportación a LilyPond
- [ ] Cuantización armónica pentatónica

### 📄 Licencia

MIT

### 👥 Autores

- **Gonzalo Cayunao Erices (KayuNawel)** - Desarrollo inicial
- Basado en el SDD "Pipeline de Transcripción Musical" (2026-03-30)

### 🙏 Agradecimientos

- **Meta AI** por Demucs
- **Spotify** por Basic Pitch
- **MIT** por music21
- **MuseScore** por MuseScore 4

---

*Proyecto WILLKA — Recuperando la música que merece ser preservada*

---

<a name="english"></a>
## 🇬🇧 English

**WILLKA** — *sacred* in Aymara. What deserves to be preserved.

Automated music transcription pipeline: **Audio → MIDI → Orchestral Score**

### 🎯 Objective

Recover orchestral scores from MP3 audio files, producing final output in MusicXML and PDF formats ready for editing in MuseScore 4.

### 🚀 Features

- **Instrument separation**: Uses Demucs to separate audio into instrumental stems
- **Automatic transcription**: Basic Pitch to convert audio to MIDI
- **Orchestral assembly**: music21 to build complete scores
- **Professional export**: MuseScore 4 to generate PDF and individual parts
- **CLI interface**: Intuitive commands with Typer and Rich for visual feedback

### 📁 Project Structure

```
willka/
├── data/
│   ├── input/           # Input audio files
│   ├── stems/           # Separated stems (WAV)
│   ├── midi/            # Generated MIDI files
│   └── output/
│       ├── musicxml/    # MusicXML scores
│       ├── pdf/         # Score PDFs
│       └── parts/       # Individual instrument parts
├── src/willka/
│   ├── config.py        # Centralized configuration
│   ├── stem_separator.py # Module 1: Demucs
│   ├── transcriber.py   # Module 2: Basic Pitch
│   ├── score_builder.py # Module 3: music21
│   ├── exporter.py      # Module 4: MuseScore CLI
│   ├── pipeline.py      # Module 5: Main orchestrator
│   └── cli.py           # Command line interface
└── tests/               # Unit tests
```

### 🛠️ Installation

#### Prerequisites
- Python 3.11+
- `uv` (modern package manager)
- MuseScore 4 (optional, for real export)

#### Quick Installation

```bash
# 1. Clone repository
git clone <repo-url>
cd willka

# 2. Create virtual environment and install dependencies
uv venv .venv
source .venv/bin/activate
uv sync

# 3. Install in development mode
uv pip install -e .

# 4. Verify installation
willka check
```

#### Install MuseScore 4 (recommended)

```bash
# Ubuntu/Debian
sudo apt install software-properties-common
sudo add-apt-repository ppa:mscore-ubuntu/mscore4-stable
sudo apt update
sudo apt install musescore4

# Verify installation
mscore4 --version
```

### 🎮 Usage

#### Main Commands

```bash
# Complete pipeline
willka run audio.mp3 --device cuda --output results/

# Only stem separation
willka stems audio.mp3 --output stems/ --device cpu

# Only transcription to MIDI
willka transcribe stems/ --output midi/ --onset 0.4 --frame 0.25

# Only score building
willka build midi/ --output score/ --title "My Work" --composer "Me"

# System check
willka check
```

#### Complete Example

```bash
# 1. Test with example audio
willka run data/input/test_complex.wav --device cpu

# 2. Check results
ls -la data/output/
```

### 🔧 Configuration

Configuration is managed through:
- Default values in `src/willka/config.py`
- Command line options
- TOML configuration file (coming soon)

#### Key Transcription Parameters

```python
# Optimized for orchestral music
onset_threshold = 0.4      # Winds have soft attacks
frame_threshold = 0.25     # Long string notes
minimum_note_length = 0.100 # Avoid ghost notes
frequency_range = 40-4200 Hz # Complete orchestral range
```

### 🧪 Testing

```bash
# Basic tests
python test_basic.py

# Complete test with mocks
python test_complete_mock.py

# Real pipeline test (requires ffmpeg)
willka stems data/input/test_complex.wav --device cpu
```

### 📊 Processing Flow

```
INPUT: audio.mp3
        │
        ▼
STEMS: drums.wav, bass.wav, piano.wav, guitar.wav, other.wav
        │
        ▼
MIDI: drums.mid, bass.mid, piano.mid, guitar.mid, other.mid
        │
        ▼
SCORE: work.xml (MusicXML)
        │
        ▼
OUTPUT: work.pdf, parts/*.pdf, png/*.png
```

### 🎼 Instrument Mapping

Each stem is mapped to instrumental families:

| Stem | Instruments |
|------|--------------|
| `other` | Woodwinds and brass |
| `guitar` | Strings (violins, violas, cellos, double basses) |
| `bass` | Double basses |
| `piano` | Harp, timpani |
| `drums` | Orchestral percussion |

### ⚠️ Known Limitations

1. **Demucs requires ffmpeg/ffprobe** for some audio formats
2. **Basic Pitch** may have issues with complex audio
3. **MuseScore 4** must be installed for real export
4. **Music21** has import issues with some instruments
5. **GPU required** for fast processing of long audio

### 🚧 Future Work

- [ ] Integration with Klangio API
- [ ] Web interface with Streamlit
- [ ] Fine-tuning for Andean music
- [ ] Export to LilyPond
- [ ] Pentatonic harmonic quantization

### 📄 License

MIT

### 👥 Authors

- **Gonzalo Cayunao Erices (KayuNawel)** - Initial development
- Based on SDD "Music Transcription Pipeline" (2026-03-30)

### 🙏 Acknowledgments

- **Meta AI** for Demucs
- **Spotify** for Basic Pitch
- **MIT** for music21
- **MuseScore** for MuseScore 4

---

*WILLKA Project — Recovering music that deserves to be preserved*

---

<div align="center">
  <a href="#español">⬆️ Volver al Español</a> | 
  <a href="#english">⬆️ Back to English</a>
</div>