"""Módulo 2: Transcripción de audio a MIDI usando Basic Pitch."""

import concurrent.futures
import csv
import logging
import time
from pathlib import Path
from typing import Any

import numpy as np
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH
from basic_pitch.note_creation import model_output_to_notes
import pretty_midi
import soundfile as sf

from .exceptions import TranscriptionError, AudioProcessingError, ModelError

logger = logging.getLogger(__name__)


class AudioTranscriber:
    """Transcriptor de audio a MIDI usando Basic Pitch."""

    def __init__(
        self,
        onset_threshold: float = 0.5,
        frame_threshold: float = 0.3,
        minimum_note_length: float = 0.058,
        minimum_frequency: float | None = None,
        maximum_frequency: float | None = None,
        model_path: Path | None = None,
    ) -> None:
        """
        Inicializa el transcriptor de audio.

        Args:
            onset_threshold: Umbral para detección de onsets (0-1)
            frame_threshold: Umbral para detección de frames (0-1)
            minimum_note_length: Longitud mínima de nota en segundos
            minimum_frequency: Frecuencia mínima en Hz (None para auto)
            maximum_frequency: Frecuencia máxima en Hz (None para auto)
            model_path: Ruta al modelo Basic Pitch (None para usar el predeterminado)
        """
        self.onset_threshold = onset_threshold
        self.frame_threshold = frame_threshold
        self.minimum_note_length = minimum_note_length
        self.minimum_frequency = minimum_frequency
        self.maximum_frequency = maximum_frequency
        self.model_path = model_path or ICASSP_2022_MODEL_PATH

        logger.info(f"Inicializando AudioTranscriber con:")
        logger.info(f"  onset_threshold: {onset_threshold}")
        logger.info(f"  frame_threshold: {frame_threshold}")
        logger.info(f"  minimum_note_length: {minimum_note_length}")
        logger.info(f"  frequency_range: {minimum_frequency}-{maximum_frequency} Hz")

    def transcribe(self, stem_path: Path, output_path: Path) -> Path:
        """
        Transcribe un archivo WAV monocanal a MIDI.

        Args:
            stem_path: Ruta al stem WAV.
            output_path: Ruta de salida para el archivo .mid.

        Returns:
            Ruta al archivo MIDI generado.
        """
        logger.info(f"Transcribiendo stem: {stem_path}")
        start_time = time.time()

        try:
            # Cargar audio
            audio, sample_rate = sf.read(str(stem_path))

            # Convertir a mono si es estéreo
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)
                logger.debug(f"Audio convertido a mono: {audio.shape}")

            logger.debug(f"Audio cargado: {len(audio)} muestras, {sample_rate} Hz")

            # Transcripción con Basic Pitch
            logger.info("Ejecutando modelo Basic Pitch...")
            model_output, midi_data, note_events = predict(
                audio_path=None,
                audio=audio,
                sample_rate=sample_rate,
                onset_threshold=self.onset_threshold,
                frame_threshold=self.frame_threshold,
                minimum_note_length=self.minimum_note_length,
                minimum_frequency=self.minimum_frequency,
                maximum_frequency=self.maximum_frequency,
                multiple_pitch_bends=False,
                melodia_trick=True,
                debug=False,
                model_or_model_path=self.model_path,
            )

            # Guardar MIDI
            output_path.parent.mkdir(parents=True, exist_ok=True)
            midi_data.write(str(output_path))
            logger.info(f"MIDI guardado: {output_path}")

            # Guardar eventos de notas como CSV para análisis
            csv_path = output_path.with_suffix(".csv")
            self._save_note_events_csv(note_events, csv_path)
            logger.info(f"Eventos de notas guardados: {csv_path}")

            # Estadísticas
            num_notes = len(note_events)
            elapsed_time = time.time() - start_time
            logger.info(
                f"Transcripción completada: {num_notes} notas en {elapsed_time:.2f} segundos"
            )

            return output_path

        except (FileNotFoundError, PermissionError) as e:
            logger.error(f"Error de archivo transcribiendo {stem_path}: {e}")
            raise AudioProcessingError(
                f"No se pudo acceder al archivo {stem_path}: {e}"
            ) from e
        except (ValueError, RuntimeError) as e:
            logger.error(f"Error de procesamiento transcribiendo {stem_path}: {e}")
            raise TranscriptionError(
                f"Error en la transcripción de {stem_path}: {e}"
            ) from e

    def transcribe_all(
        self, stems: dict[str, Path], output_dir: Path, max_workers: int = 4
    ) -> dict[str, Path]:
        """
        Transcribe todos los stems en paralelo.

        Args:
            stems: Diccionario {nombre_stem: ruta_wav}
            output_dir: Directorio de salida para archivos MIDI
            max_workers: Número máximo de workers para procesamiento paralelo

        Returns:
            Diccionario {nombre_stem: ruta_midi}
        """
        logger.info(
            f"Transcribiendo {len(stems)} stems en paralelo (max_workers={max_workers})"
        )
        start_time = time.time()

        output_dir.mkdir(parents=True, exist_ok=True)
        midi_files = {}

        # Función para procesar un stem
        def process_stem(stem_name: str, stem_path: Path) -> tuple[str, Path]:
            output_path = output_dir / f"{stem_name}.mid"
            try:
                self.transcribe(stem_path, output_path)
                return stem_name, output_path
            except Exception as e:
                logger.error(f"Error procesando stem {stem_name}: {e}")
                # Re-lanzar la excepción para que sea manejada por el futuro
                raise

        # Procesamiento paralelo
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Crear futures
            futures = {
                executor.submit(process_stem, stem_name, stem_path): stem_name
                for stem_name, stem_path in stems.items()
            }

            # Recolectar resultados
            for future in concurrent.futures.as_completed(futures):
                stem_name = futures[future]
                try:
                    stem_name, midi_path = future.result()
                    midi_files[stem_name] = midi_path
                    logger.info(f"Stem '{stem_name}' transcrito exitosamente")
                except Exception as e:
                    logger.error(f"Error en futuro para stem '{stem_name}': {e}")
                    # Continuar con otros stems, no re-lanzar aquí

        elapsed_time = time.time() - start_time
        logger.info(
            f"Transcripción de todos los stems completada en {elapsed_time:.2f} segundos"
        )

        return midi_files

    def _save_note_events_csv(self, note_events: list[dict], csv_path: Path) -> None:
        """Guarda eventos de notas como CSV."""
        if not note_events:
            logger.warning("No hay eventos de notas para guardar")
            return

        fieldnames = ["start_time", "end_time", "pitch", "velocity", "confidence"]

        with open(csv_path, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for event in note_events:
                writer.writerow(
                    {
                        "start_time": event["start_time"],
                        "end_time": event["end_time"],
                        "pitch": event["pitch"],
                        "velocity": event["amplitude"],
                        "confidence": event["confidence"],
                    }
                )

        logger.debug(f"CSV guardado con {len(note_events)} eventos")

    def get_transcription_stats(self, midi_path: Path) -> dict[str, Any]:
        """
        Obtiene estadísticas de un archivo MIDI transcrito.

        Args:
            midi_path: Ruta al archivo MIDI

        Returns:
            Diccionario con estadísticas
        """
        try:
            midi_data = pretty_midi.PrettyMIDI(str(midi_path))

            stats = {
                "path": str(midi_path),
                "duration": midi_data.get_end_time(),
                "instruments": len(midi_data.instruments),
                "total_notes": 0,
                "note_range": {"min": 127, "max": 0},
                "avg_velocity": 0,
            }

            total_velocity = 0
            for instrument in midi_data.instruments:
                stats["total_notes"] += len(instrument.notes)

                for note in instrument.notes:
                    stats["note_range"]["min"] = min(
                        stats["note_range"]["min"], note.pitch
                    )
                    stats["note_range"]["max"] = max(
                        stats["note_range"]["max"], note.pitch
                    )
                    total_velocity += note.velocity

            if stats["total_notes"] > 0:
                stats["avg_velocity"] = total_velocity / stats["total_notes"]

            return stats

        except (FileNotFoundError, PermissionError) as e:
            logger.error(
                f"Error de archivo obteniendo estadísticas de {midi_path}: {e}"
            )
            return {}
        except (ValueError, RuntimeError) as e:
            logger.error(
                f"Error de procesamiento obteniendo estadísticas de {midi_path}: {e}"
            )
            return {}
