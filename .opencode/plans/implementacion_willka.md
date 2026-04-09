# Plan de Implementación: Proyecto WILLKA

## Análisis de Situación Actual

**Proyecto actual:** `pt_project` (Python 3.13+, Streamlit, estructura mínima)
**Objetivo:** Implementar `WILLKA` según SDD (pipeline de transcripción musical MP3→MIDI→partitura)

**Conclusión:** `pt_project` y `WILLKA` son proyectos diferentes. Se recomienda:
1. Transformar `pt_project` en `WILLKA` (cambio de propósito)
2. Mantener configuración base (uv, Python 3.13+)
3. Reemplazar completamente dependencias y estructura

---

## Fase 1: Preparación del Entorno (Día 1)

### 1.1 Actualizar configuración del proyecto
- [ ] Renombrar proyecto en `pyproject.toml`: `pt-project` → `willka`
- [ ] Actualizar versión: `0.1.0` → `1.0.0`
- [ ] Actualizar descripción: "Add your description here" → "WILLKA — Pipeline de transcripción musical: MP3 → MIDI → Partitura orquestal"
- [ ] Actualizar autores
- [ ] Ajustar `requires-python`: `>=3.13` → `>=3.11` (o mantener 3.13+ si compatible)

### 1.2 Reestructurar directorios
- [ ] Crear estructura base:
  ```
  data/
    input/           # Archivo MP3 de entrada
    stems/           # Stems separados (WAV)
    midi/            # Archivos MIDI generados
    output/
      musicxml/      # Partitura MusicXML
      pdf/           # PDF de partitura
      partes/        # Partes individuales por instrumento
  src/
    willka/          # Módulos del pipeline
  tests/
    fixtures/        # Archivos de prueba
  notebooks/         # Notebooks de exploración
  ```

### 1.3 Obtener archivo de audio de entrada
- [ ] Localizar `kayunawel_desde-antofagasta-a-tiahuanaco.mp3` (~7 MB)
- [ ] Colocar en `data/input/`
- [ ] Si no disponible, usar archivo de prueba alternativo (5-10 segundos de audio sintético)

---

## Fase 2: Dependencias y Entorno (Día 1-2)

### 2.1 Actualizar `pyproject.toml`
- [ ] Eliminar dependencia `streamlit>=1.56.0`
- [ ] Agregar dependencias principales del SDD:
  ```toml
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
  ```
- [ ] Agregar dependencias de desarrollo
- [ ] Configurar scripts CLI: `willka = "willka.pipeline:app"`

### 2.2 Instalación específica de PyTorch con CUDA
- [ ] Instalar PyTorch con soporte CUDA 12.x:
  ```bash
  uv pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
  ```

### 2.3 Instalar MuseScore 4 (requerimiento del sistema)
- [ ] Verificar si MuseScore 4 está instalado: `which mscore4`
- [ ] Instalar si no existe: `sudo apt install musescore4`
- [ ] Verificar acceso desde CLI

### 2.4 Configurar workaround libexpat (WSL2)
- [ ] Agregar al entorno: `export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libexpat.so.1`
- [ ] Documentar en README

---

## Fase 3: Implementación de Módulos (Días 2-5)

### 3.1 Módulo 1: `stem_separator.py` (Día 2)
- [ ] Implementar clase `StemSeparator` según interfaz del SDD
- [ ] Integrar Demucs con soporte CUDA/CPU
- [ ] Manejar stems: drums, bass, piano, guitar, other, vocals (descartar)
- [ ] Agregar logging y medición de tiempo
- [ ] Crear test básico con audio sintético

### 3.2 Módulo 2: `transcriber.py` (Día 3)
- [ ] Implementar clase `AudioTranscriber` según SDD
- [ ] Integrar Basic Pitch con parámetros optimizados para música orquestal:
  - `onset_threshold`: 0.4 (vientos ataques suaves)
  - `frame_threshold`: 0.25 (notas largas de cuerdas)
  - `minimum_note_length`: 0.100 (evitar notas fantasma)
  - Rango frecuencia: 40-4200 Hz
- [ ] Procesamiento paralelo de stems
- [ ] Guardar CSV de note events para análisis
- [ ] Crear test con stem de prueba

### 3.3 Módulo 3: `score_builder.py` (Día 4)
- [ ] Implementar clase `ScoreBuilder` según SDD
- [ ] Definir mapeo STEM_TO_INSTRUMENT:
  ```python
  STEM_TO_INSTRUMENT = {
      "other":  ["Flute", "Oboe", "Clarinet", "Bassoon", "Horn", "Trumpet", "Trombone"],
      "guitar": ["Violin", "Viola", "Cello", "Contrabass"],
      "bass":   ["Contrabass"],
      "piano":  ["Harp", "Timpani"],
      "drums":  ["Timpani", "Percussion"],
  }
  ```
- [ ] Configurar metadatos de la obra
- [ ] Implementar exportación MusicXML
- [ ] Crear test con MIDI de prueba

### 3.4 Módulo 4: `exporter.py` (Día 4)
- [ ] Implementar clase `ScoreExporter`
- [ ] Integrar MuseScore 4 CLI para:
  - Generar PDF de partitura completa
  - Generar partes individuales por instrumento
  - Generar PNG para previsualización
- [ ] Manejar errores de MuseScore no instalado
- [ ] Crear test mockeando MuseScore

### 3.5 Módulo 5: `pipeline.py` (Día 5)
- [ ] Implementar clase `TranscriptionPipeline`
- [ ] Definir dataclasses `PipelineConfig` y `PipelineResult`
- [ ] Orquestar ejecución secuencial:
  1. Validación entrada
  2. Separación stems (Demucs)
  3. Transcripción MIDI (Basic Pitch)
  4. Construcción partitura (music21)
  5. Exportación PDF (MuseScore)
- [ ] Implementar logging detallado con Rich
- [ ] Manejo robusto de errores

---

## Fase 4: CLI y Configuración (Día 5)

### 4.1 Interfaz de línea de comandos
- [ ] Implementar CLI con Typer según SDD:
  ```bash
  # Comandos principales
  willka run <audio.mp3>          # Pipeline completo
  willka stems <audio.mp3>        # Solo separación
  willka transcribe <stems_dir>   # Solo transcripción
  willka build <midi_dir>         # Solo construcción partitura
  
  # Opciones
  --device cpu/gpu
  --config config.toml
  --log-level DEBUG/INFO/WARNING
  ```

### 4.2 Sistema de configuración
- [ ] Implementar configuración con Pydantic
- [ ] Soporte para archivo `config.toml`
- [ ] Variables de entorno para rutas sensibles

### 4.3 Logging y reportes
- [ ] Integrar Rich para output colorido
- [ ] Progress bars para operaciones largas
- [ ] Reporte final con métricas y rutas de archivos

---

## Fase 5: Testing y Validación (Día 6)

### 5.1 Tests unitarios
- [ ] `test_stem_separator.py`: Demucs con audio sintético
- [ ] `test_transcriber.py`: Basic Pitch con stem de prueba
- [ ] `test_score_builder.py`: music21 con MIDI de referencia
- [ ] `test_exporter.py`: Mock de MuseScore CLI
- [ ] `test_pipeline.py`: Pipeline con archivos de prueba

### 5.2 Fixtures de prueba
- [ ] Crear `tests/fixtures/`:
  - `test_audio.wav` (5s sintético)
  - `test_stem.wav` (stem de prueba)
  - `test.mid` (MIDI de referencia)
  - `test_config.toml` (configuración de prueba)

### 5.3 Test de integración
- [ ] Ejecutar pipeline completo con archivo de prueba pequeño
- [ ] Validar salidas: stems, MIDIs, MusicXML, PDF
- [ ] Medir tiempo de ejecución

### 5.4 Validación musical (manual)
- [ ] Ejecutar pipeline con archivo real (si disponible)
- [ ] Abrir partitura generada en MuseScore 4
- [ ] Verificar:
  - Asignación correcta de instrumentos
  - Notas y ritmos precisos
  - Estructura de compases
  - Metadatos de la obra

---

## Fase 6: Documentación y Despliegue (Día 7)

### 6.1 Documentación
- [ ] Actualizar `README.md` con:
  - Descripción del proyecto
  - Instalación paso a paso
  - Uso de CLI con ejemplos
  - Ejemplo de configuración
  - Troubleshooting (especialmente WSL2)
- [ ] Documentar en `AGENTS.md` comandos clave y restricciones
- [ ] Crear `CONTRIBUTING.md` si aplica

### 6.2 Scripts de instalación
- [ ] Crear `install.sh` para configuración automática
- [ ] Script para verificar requisitos: CUDA, MuseScore, dependencias

### 6.3 Ejemplos y demostración
- [ ] Crear `notebooks/exploracion_stems.ipynb` para análisis
- [ ] Ejemplo de configuración `config.example.toml`
- [ ] Script de demostración con audio de ejemplo

---

## Orden de Implementación Crítico

1. **Primero tests** → Implementar `test_transcriber.py` antes de ejecutar pipeline completo
2. **Módulo por módulo** en orden del SDD:
   - `stem_separator.py` (Demucs)
   - `transcriber.py` (Basic Pitch)
   - `score_builder.py` (music21)
   - `exporter.py` (MuseScore)
   - `pipeline.py` (orquestador)
3. **Validación incremental** después de cada módulo
4. **Pipeline completo** solo cuando todos los módulos estén probados

---

## Riesgos y Mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| CUDA no disponible en entorno | Fallback automático a CPU, warning claro |
| MuseScore 4 no instalado | Verificación al inicio, instrucciones de instalación |
| Archivo de entrada no disponible | Usar archivo de prueba sintético para desarrollo |
| Demucs requiere mucho RAM/GPU | Opción `--device cpu`, procesar por chunks |
| Basic Pitch impreciso con orquesta densa | Ajustar parámetros, considerar Magenta como fallback |
| Conflictos libexpat en WSL2 | Workaround documentado, detección automática |

---

## Métricas de Éxito

1. **Funcional**: Pipeline ejecuta completamente sin errores
2. **Calidad**: Partitura generada es editable en MuseScore 4
3. **Rendimiento**: < 30 minutos para archivo de 5-8 minutos (con GPU)
4. **Usabilidad**: CLI intuitiva con buen feedback
5. **Robustez**: Manejo adecuado de errores y fallbacks

---

## Recursos Necesarios

1. **Hardware**: GPU NVIDIA RTX 5060 con CUDA 12.x
2. **Software**: 
   - WSL2 Ubuntu 24.04
   - Python 3.11+ (compatible con 3.13)
   - MuseScore 4 instalado
3. **Datos**: Archivo MP3 `kayunawel_desde-antofagasta-a-tiahuanaco.mp3` o alternativo
4. **Tiempo**: 7 días de desarrollo (estimado)

---

## Notas Especiales para Implementación

1. **Priorizar calidad sobre velocidad**: Mejor transcripción precisa que rápida
2. **Logging detallado**: Crucial para debugging de procesos largos
3. **Paralelización**: Procesar stems en paralelo cuando sea posible
4. **Música pentatónica**: Considerar en post-procesamiento de notas
5. **Revisión manual esperada**: La partitura requerirá ajustes en MuseScore

---

*Plan basado en SDD v1.0.0 — 2026-03-30*
*Duración estimada: 7 días de desarrollo*
*Prioridad: Implementación modular con testing incremental*