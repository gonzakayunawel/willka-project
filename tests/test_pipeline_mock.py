"""Prueba del pipeline WILLKA con mocks para desarrollo."""

import logging
from pathlib import Path
import numpy as np
import soundfile as sf

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


def test_pipeline_with_mocks():
    """Prueba el pipeline completo con mocks."""
    logger.info("🧪 Probando pipeline WILLKA con mocks")

    from willka.config import PipelineConfig
    from willka.pipeline import TranscriptionPipeline

    # Configurar pipeline con mocks
    config = PipelineConfig()
    config.device = "cpu"
    config.stems_dir = Path("data/test_stems_mock")
    config.midi_dir = Path("data/test_midi_mock")
    config.output_dir = Path("data/test_output_mock")

    # Crear stems mock primero
    audio_path = Path("data/input/test_complex.wav")
    stems = create_mock_stems(audio_path, config.stems_dir)

    # Inicializar pipeline
    pipeline = TranscriptionPipeline(config)

    # Probar transcripción
    logger.info("\n🎹 Probando transcripción...")
    try:
        midis = pipeline.run_transcription_only(config.stems_dir)
        logger.info(f"✓ MIDIs generados: {len(midis)}")
        for stem_name, midi_path in midis.items():
            logger.info(f"  • {stem_name}: {midi_path}")
    except Exception as e:
        logger.error(f"❌ Error en transcripción: {e}")
        return False

    # Probar construcción de partitura
    logger.info("\n📄 Probando construcción de partitura...")
    try:
        musicxml_path = pipeline.run_build_only(config.midi_dir)
        logger.info(f"✓ Partitura construida: {musicxml_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Error en construcción: {e}")
        return False


def main():
    """Función principal."""
    logger.info("=" * 60)
    logger.info("🚀 Iniciando prueba de pipeline con mocks")
    logger.info("=" * 60)

    success = test_pipeline_with_mocks()

    logger.info("\n" + "=" * 60)
    if success:
        logger.info("✅ ¡Prueba completada exitosamente!")
        logger.info("\nArchivos generados:")
        logger.info(f"  • Stems: data/test_stems_mock/")
        logger.info(f"  • MIDIs: data/test_midi_mock/")
        logger.info(f"  • Partitura: data/test_output_mock/musicxml/")
    else:
        logger.info("❌ Prueba falló")

    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
