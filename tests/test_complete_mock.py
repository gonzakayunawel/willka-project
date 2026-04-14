"""Prueba completa del pipeline WILLKA con todos los mocks."""

import logging
from pathlib import Path
import numpy as np
import soundfile as sf
import pretty_midi

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_mock_stems(audio_path: Path, output_dir: Path) -> dict:
    """Crea stems mock para pruebas."""
    logger.info(f"Creando stems mock para: {audio_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Cargar audio original
    audio, sr = sf.read(str(audio_path))
    if len(audio.shape) > 1:
        audio = np.mean(audio, axis=1)

    # Crear stems mock (simplificados)
    stems = {
        "drums": audio * 0.3 + np.random.normal(0, 0.01, len(audio)),
        "bass": audio * 0.2 + np.sin(2 * np.pi * 100 * np.arange(len(audio)) / sr),
        "piano": audio * 0.25 + np.sin(2 * np.pi * 440 * np.arange(len(audio)) / sr),
        "guitar": audio * 0.15 + np.sin(2 * np.pi * 330 * np.arange(len(audio)) / sr),
        "other": audio * 0.1 + np.sin(2 * np.pi * 880 * np.arange(len(audio)) / sr),
    }

    # Guardar stems
    stem_paths = {}
    for stem_name, stem_audio in stems.items():
        output_path = output_dir / f"{stem_name}.wav"
        sf.write(str(output_path), stem_audio, sr)
        stem_paths[stem_name] = output_path
        logger.info(f"  Stem mock creado: {stem_name} -> {output_path}")

    return stem_paths


def create_mock_midis(stem_paths: dict, output_dir: Path) -> dict:
    """Crea MIDIs mock para pruebas."""
    logger.info("Creando MIDIs mock...")

    output_dir.mkdir(parents=True, exist_ok=True)
    midi_paths = {}

    for stem_name, stem_path in stem_paths.items():
        # Crear MIDI mock
        midi = pretty_midi.PrettyMIDI()

        # Crear instrumento
        instrument = pretty_midi.Instrument(program=0)  # Piano

        # Agregar algunas notas mock
        audio, sr = sf.read(str(stem_path))
        duration = len(audio) / sr

        # Notas básicas según el stem
        if stem_name == "piano":
            notes = [(60, 0.5, 1.0), (64, 1.5, 2.0), (67, 2.5, 3.0)]  # Do, Mi, Sol
        elif stem_name == "guitar":
            notes = [(55, 0.0, 1.0), (59, 1.0, 2.0), (62, 2.0, 3.0)]  # Sol, Si, Re
        elif stem_name == "bass":
            notes = [(36, 0.0, 2.0), (40, 2.0, 4.0)]  # Do grave, Mi grave
        elif stem_name == "drums":
            # Percusión (nota 36 = kick drum)
            notes = [(36, 0.0, 0.1), (36, 1.0, 1.1), (36, 2.0, 2.1)]
        else:  # other
            notes = [(72, 0.0, 1.5), (76, 1.5, 3.0)]  # Do agudo, Mi agudo

        for pitch, start, end in notes:
            note = pretty_midi.Note(
                velocity=100,
                pitch=pitch,
                start=min(start, duration - 0.1),
                end=min(end, duration),
            )
            instrument.notes.append(note)

        midi.instruments.append(instrument)

        # Guardar MIDI
        output_path = output_dir / f"{stem_name}.mid"
        midi.write(str(output_path))
        midi_paths[stem_name] = output_path
        logger.info(
            f"  MIDI mock creado: {stem_name} -> {output_path} ({len(instrument.notes)} notas)"
        )

    return midi_paths


def test_complete_pipeline():
    """Prueba el pipeline completo con mocks."""
    logger.info("🧪 Probando pipeline WILLKA completo con mocks")

    # Crear directorios de prueba
    test_dir = Path("data/test_complete")
    stems_dir = test_dir / "stems"
    midi_dir = test_dir / "midi"
    output_dir = test_dir / "output"

    # Paso 1: Crear stems mock
    audio_path = Path("data/input/test_complex.wav")
    stem_paths = create_mock_stems(audio_path, stems_dir)

    # Paso 2: Crear MIDIs mock
    midi_paths = create_mock_midis(stem_paths, midi_dir)

    # Paso 3: Probar construcción de partitura
    logger.info("\n📄 Probando construcción de partitura...")
    try:
        from willka.config import PipelineConfig
        from willka.score_builder import ScoreBuilder

        config = PipelineConfig()
        config.title = "Obra de Prueba"
        config.composer = "Compositor de Prueba"
        config.tempo_bpm = 120

        score_builder = ScoreBuilder(
            title=config.title,
            composer=config.composer,
            tempo_bpm=config.tempo_bpm,
            year=2024,
        )

        # Construir partitura
        score = score_builder.build(midi_paths)

        # Exportar MusicXML
        musicxml_dir = output_dir / "musicxml"
        musicxml_path = musicxml_dir / "partitura_prueba.xml"
        score_builder.export_musicxml(score, musicxml_path)

        # Exportar MIDI unificado
        midi_merged_path = output_dir / "midi" / "partitura_completa.mid"
        score_builder.export_midi_merged(score, midi_merged_path)

        logger.info(f"✓ Partitura construida: {len(score.parts)} partes")
        logger.info(f"✓ MusicXML exportado: {musicxml_path}")
        logger.info(f"✓ MIDI unificado: {midi_merged_path}")

        # Paso 4: Probar exportación (mock)
        logger.info("\n📤 Probando exportación...")
        from willka.exporter import ScoreExporter

        exporter = ScoreExporter()

        # Exportar PDF (mock)
        pdf_dir = output_dir / "pdf"
        pdf_path = pdf_dir / "partitura_prueba.pdf"
        exporter.to_pdf(musicxml_path, pdf_path)

        # Exportar partes (mock)
        parts_dir = output_dir / "partes"
        parts = exporter.to_parts(musicxml_path, parts_dir)

        # Exportar PNGs (mock)
        png_dir = output_dir / "png"
        pngs = exporter.to_png(musicxml_path, png_dir)

        logger.info(f"✓ PDF generado (mock): {pdf_path}")
        logger.info(f"✓ Partes individuales: {len(parts)} archivos")
        logger.info(f"✓ Previsualizaciones PNG: {len(pngs)} imágenes")

        return True

    except Exception as e:
        logger.error(f"❌ Error en pipeline: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Función principal."""
    logger.info("=" * 60)
    logger.info("🚀 Iniciando prueba completa de pipeline con mocks")
    logger.info("=" * 60)

    success = test_complete_pipeline()

    logger.info("\n" + "=" * 60)
    if success:
        logger.info("✅ ¡Prueba completada exitosamente!")
        logger.info("\n🎯 WILLKA está funcionando correctamente con:")
        logger.info("  1. Generación de stems (mock)")
        logger.info("  2. Transcripción a MIDI (mock)")
        logger.info("  3. Construcción de partitura (real)")
        logger.info("  4. Exportación de resultados (mock)")

        logger.info("\n📁 Archivos generados en: data/test_complete/")
        logger.info("  Para probar con audio real:")
        logger.info("    willka run <tu_audio.mp3> --device cpu")

    else:
        logger.info("❌ Prueba falló")

    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
