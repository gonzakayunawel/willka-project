"""Módulo 1: Separación de stems instrumentales usando Demucs."""

import logging
import time
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import torch
from demucs import pretrained
from demucs.apply import apply_model

logger = logging.getLogger(__name__)


class StemSeparator:
    """Separador de stems instrumentales usando Demucs."""

    def __init__(self, model: str = "htdemucs_6s", device: Optional[str] = None):
        """
        Inicializa el separador de stems.

        Args:
            model: Nombre del modelo Demucs a usar (default: "htdemucs_6s")
            device: Dispositivo a usar ("cuda", "cpu", o None para auto-detección)
        """
        self.model_name = model

        # Auto-detección de dispositivo
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        logger.info(
            f"Inicializando StemSeparator con modelo {model} en dispositivo {self.device}"
        )

        # Cargar modelo
        try:
            self.model = pretrained.get_model(model)
            self.model.to(self.device)
            logger.info(f"Modelo {model} cargado exitosamente")
        except Exception as e:
            logger.error(f"Error al cargar modelo {model}: {e}")
            raise

        # Stems esperados para htdemucs_6s
        self.expected_stems = ["drums", "bass", "piano", "guitar", "vocals", "other"]

        # Mapeo de stems a descripciones
        self.stem_descriptions = {
            "drums": "Percusión orquestal",
            "bass": "Línea de bajo / contrabajos",
            "piano": "Teclados / arpa / instrumentos melódicos de percusión",
            "guitar": "Cuerdas (violines, violas, cellos)",
            "vocals": "Voces (se descarta para esta obra)",
            "other": "Vientos madera y metal",
        }

    def separate(self, audio_path: Path, output_dir: Path) -> Dict[str, Path]:
        """
        Separa el audio en stems instrumentales.

        Args:
            audio_path: Ruta al archivo MP3/WAV de entrada.
            output_dir: Directorio donde se guardan los stems.

        Returns:
            Diccionario {nombre_stem: ruta_archivo_wav}
            Ej: {"drums": Path("stems/drums.wav"), "other": Path("stems/other.wav")}
        """
        logger.info(f"Iniciando separación de stems para: {audio_path}")
        start_time = time.time()

        # Crear directorio de salida si no existe
        output_dir.mkdir(parents=True, exist_ok=True)

        # Cargar audio usando soundfile (evita dependencia de ffprobe)
        try:
            logger.info(f"Cargando audio: {audio_path}")
            import soundfile as sf
            import torch

            # Cargar con soundfile
            audio, orig_sr = sf.read(str(audio_path))

            # Convertir a mono si es necesario
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)

            # Convertir a tensor de PyTorch
            audio_tensor = torch.from_numpy(audio.astype(np.float32))

            # Remuestrear si es necesario
            if orig_sr != self.model.samplerate:
                from demucs.utils import resample_audio

                audio_tensor = resample_audio(
                    audio_tensor, orig_sr, self.model.samplerate
                )

            # Asegurar dimensiones correctas [channels, samples]
            if audio_tensor.dim() == 1:
                audio_tensor = audio_tensor.unsqueeze(0)

            # Asegurar número correcto de canales
            if audio_tensor.shape[0] != self.model.audio_channels:
                if self.model.audio_channels == 1:
                    audio_tensor = audio_tensor.mean(dim=0, keepdim=True)
                else:
                    audio_tensor = audio_tensor.repeat(self.model.audio_channels, 1)

            wav = audio_tensor.to(self.device)
            logger.info(
                f"Audio cargado: {wav.shape[1] / self.model.samplerate:.2f} segundos, {wav.shape[0]} canales"
            )
        except Exception as e:
            logger.error(f"Error al cargar audio {audio_path}: {e}")
            raise

        # Separar stems
        try:
            logger.info("Separando stems...")
            with torch.no_grad():
                sources = apply_model(
                    self.model,
                    wav[None],
                    device=self.device,
                    shifts=1,
                    split=True,
                    overlap=0.25,
                    progress=True,
                )[0]

            # Guardar cada stem
            stem_paths = {}
            for idx, stem_name in enumerate(self.expected_stems):
                stem_audio = sources[idx].cpu()

                # Descarta el stem de vocals para esta obra
                if stem_name == "vocals":
                    logger.info(
                        f"Descartando stem '{stem_name}' (no aplica para esta obra)"
                    )
                    continue

                # Guardar stem usando soundfile
                output_path = output_dir / f"{stem_name}.wav"
                try:
                    import soundfile as sf

                    # Convertir a numpy y asegurar formato correcto
                    stem_np = stem_audio.numpy()
                    if stem_np.ndim > 1:
                        stem_np = stem_np.squeeze()

                    sf.write(str(output_path), stem_np, self.model.samplerate)
                    stem_paths[stem_name] = output_path
                    logger.info(f"Stem '{stem_name}' guardado: {output_path}")
                    logger.debug(f"  Descripción: {self.stem_descriptions[stem_name]}")
                except Exception as e:
                    logger.error(f"Error al guardar stem '{stem_name}': {e}")
                    raise

        except Exception as e:
            logger.error(f"Error durante la separación de stems: {e}")
            raise

        elapsed_time = time.time() - start_time
        logger.info(f"Separación de stems completada en {elapsed_time:.2f} segundos")
        logger.info(f"Stems generados: {list(stem_paths.keys())}")

        return stem_paths

    def get_device_info(self) -> Dict[str, str]:
        """Obtiene información del dispositivo."""
        info = {
            "device": self.device,
            "model": self.model_name,
        }

        if self.device == "cuda":
            info.update(
                {
                    "cuda_available": str(torch.cuda.is_available()),
                    "cuda_device_count": str(torch.cuda.device_count()),
                    "current_device": str(torch.cuda.current_device()),
                    "device_name": torch.cuda.get_device_name(0)
                    if torch.cuda.device_count() > 0
                    else "N/A",
                }
            )

        return info
