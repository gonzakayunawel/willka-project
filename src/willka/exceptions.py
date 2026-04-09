"""Excepciones personalizadas para el pipeline WILLKA."""


class WillkaError(Exception):
    """Excepción base para todos los errores de WILLKA."""

    pass


class AudioProcessingError(WillkaError):
    """Error procesando archivos de audio."""

    pass


class ModelError(WillkaError):
    """Error cargando o ejecutando modelos de ML."""

    pass


class TranscriptionError(WillkaError):
    """Error durante la transcripción de audio a MIDI."""

    pass


class ScoreBuildingError(WillkaError):
    """Error construyendo la partitura."""

    pass


class ScoreExportError(WillkaError):
    """Error exportando la partitura."""

    pass


class ConfigurationError(WillkaError):
    """Error en la configuración del pipeline."""

    pass


class FileValidationError(WillkaError):
    """Error validando archivos de entrada."""

    pass


class DeviceError(WillkaError):
    """Error relacionado con dispositivos (CPU/GPU)."""

    pass
