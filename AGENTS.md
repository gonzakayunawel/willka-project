# Agent Guidance for WILLKA

## Project Overview
- Python 3.11+ project using `uv` package manager
- Pipeline de transcripción musical: Audio → MIDI → Partitura orquestal
- Transformado de `pt-project` (Streamlit) a `willka` (procesamiento de audio)

## Key Commands
- **Pipeline completo**: `willka run <audio.mp3> --device cpu`
- **Solo stems**: `willka stems <audio.mp3> --output stems/`
- **Solo transcripción**: `willka transcribe <stems_dir> --output midi/`
- **Solo partitura**: `willka build <midi_dir> --output partitura/`
- **Verificar sistema**: `willka check`
- **Sync dependencies**: `uv sync`
- **Instalar desarrollo**: `uv pip install -e .`

## Development Notes
- Virtual environment: `.venv/` (Python 3.11.15)
- Package manager: `uv` (no pip/venv)
- Python version: 3.11+ (`.python-version` file)
- Dependencias pesadas: PyTorch, TensorFlow, Demucs, music21
- MuseScore 4 requerido para exportación real (modo mock disponible)

## Project Structure
```
src/willka/
├── config.py           # Configuración centralizada
├── stem_separator.py   # Módulo 1: Demucs (separación stems)
├── transcriber.py      # Módulo 2: Basic Pitch (audio→MIDI)
├── score_builder.py    # Módulo 3: music21 (ensamblaje partitura)
├── exporter.py         # Módulo 4: MuseScore CLI (exportación)
├── pipeline.py         # Módulo 5: Orquestador principal
└── cli.py              # Interfaz CLI con Typer
```

## Important Constraints
1. **GPU recomendada** - Demucs y Basic Pitch son intensivos
2. **ffmpeg/ffprobe requerido** - Para procesamiento de audio
3. **MuseScore 4 opcional** - Modo mock disponible
4. **Audio WAV preferido** - Evita problemas con ffprobe
5. **Music21 tiene bugs** - Algunos instrumentos no se importan correctamente

## Testing
- `python test_basic.py` - Pruebas básicas de importación
- `python test_complete_mock.py` - Pipeline completo con mocks
- Los tests reales requieren ffmpeg instalado

## Known Issues
1. **Demucs + ffprobe**: Error si ffprobe no está instalado
2. **Basic Pitch API**: La función `predict` cambió en versión 0.4.0
3. **Music21 imports**: `FrenchHorn` y otros instrumentos causan errores
4. **Soundfile write**: Problemas con algunos formatos WAV

## When Adding Features
- Usar `uv add` para nuevas dependencias
- Mantener compatibilidad con CPU (fallback de CUDA)
- Probar con `python test_basic.py` primero
- Documentar requisitos adicionales (ej: ffmpeg)