"""Script de prueba básico para WILLKA."""

import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_imports():
    """Prueba que todos los módulos se pueden importar."""
    logger.info("Probando importaciones...")

    try:
        from willka import __version__

        logger.info(f"✓ WILLKA v{__version__}")

        from willka.stem_separator import StemSeparator

        logger.info("✓ StemSeparator importado")

        from willka.transcriber import AudioTranscriber

        logger.info("✓ AudioTranscriber importado")

        from willka.score_builder import ScoreBuilder

        logger.info("✓ ScoreBuilder importado")

        from willka.exporter import ScoreExporter

        logger.info("✓ ScoreExporter importado")

        from willka.pipeline import TranscriptionPipeline

        logger.info("✓ TranscriptionPipeline importado")

        from willka.cli import app

        logger.info("✓ CLI app importada")

        logger.info("✅ Todas las importaciones exitosas")
        return True

    except ImportError as e:
        logger.error(f"❌ Error de importación: {e}")
        return False


def test_config():
    """Prueba la configuración."""
    logger.info("Probando configuración...")

    try:
        from willka.config import PipelineConfig, OBRA_METADATA, STEM_TO_INSTRUMENT

        config = PipelineConfig()
        logger.info(f"✓ Configuración cargada: {config}")
        logger.info(f"✓ Metadatos de obra: {OBRA_METADATA['title']}")
        logger.info(f"✓ Mapeo de stems: {list(STEM_TO_INSTRUMENT.keys())}")

        logger.info("✅ Configuración probada exitosamente")
        return True

    except Exception as e:
        logger.error(f"❌ Error en configuración: {e}")
        return False


def test_audio_file():
    """Verifica que el archivo de audio de prueba existe."""
    logger.info("Verificando archivo de audio de prueba...")

    audio_path = Path("data/input/test_audio.wav")
    if audio_path.exists():
        logger.info(f"✓ Archivo de audio encontrado: {audio_path}")
        logger.info(f"  Tamaño: {audio_path.stat().st_size / 1024:.1f} KB")
        return True
    else:
        logger.error(f"❌ Archivo de audio no encontrado: {audio_path}")
        return False


def test_pipeline_initialization():
    """Prueba la inicialización del pipeline."""
    logger.info("Probando inicialización del pipeline...")

    try:
        from willka.config import PipelineConfig
        from willka.pipeline import TranscriptionPipeline

        config = PipelineConfig()
        config.device = "cpu"  # Forzar CPU para pruebas

        pipeline = TranscriptionPipeline(config)
        logger.info("✓ Pipeline inicializado exitosamente")

        # Verificar módulos internos
        logger.info(f"  StemSeparator: {type(pipeline.stem_separator).__name__}")
        logger.info(f"  AudioTranscriber: {type(pipeline.transcriber).__name__}")
        logger.info(f"  ScoreBuilder: {type(pipeline.score_builder).__name__}")
        logger.info(f"  ScoreExporter: {type(pipeline.exporter).__name__}")

        logger.info("✅ Pipeline probado exitosamente")
        return True

    except Exception as e:
        logger.error(f"❌ Error en pipeline: {e}")
        return False


def main():
    """Función principal de pruebas."""
    logger.info("=" * 60)
    logger.info("🧪 Ejecutando pruebas básicas de WILLKA")
    logger.info("=" * 60)

    tests = [
        ("Importaciones", test_imports),
        ("Configuración", test_config),
        ("Archivo de audio", test_audio_file),
        ("Pipeline", test_pipeline_initialization),
    ]

    results = []
    for test_name, test_func in tests:
        logger.info(f"\n🔬 {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ Excepción en {test_name}: {e}")
            results.append((test_name, False))

    # Resumen
    logger.info("\n" + "=" * 60)
    logger.info("📊 Resumen de pruebas:")
    logger.info("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        logger.info(f"{status} {test_name}")
        if result:
            passed += 1

    logger.info(f"\n🎯 Resultado: {passed}/{total} pruebas pasadas")

    if passed == total:
        logger.info("\n✨ ¡Todas las pruebas pasaron! WILLKA está listo.")
        logger.info("\nPara ejecutar el pipeline completo:")
        logger.info("  uv run willka run data/input/test_audio.wav --device cpu")
        logger.info("\nPara verificar el sistema:")
        logger.info("  uv run willka check")
    else:
        logger.warning("\n⚠  Algunas pruebas fallaron. Revisa los errores arriba.")

    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
