"""Módulo 4: Exportación de partituras usando MuseScore 4 CLI (mock)."""

import logging
import subprocess
import shutil
from pathlib import Path


from .exceptions import ScoreExportError

logger = logging.getLogger(__name__)


class ScoreExporter:
    """Exportador de partituras usando MuseScore 4 CLI."""

    def __init__(self, musescore_path: str | None = None) -> None:
        """
        Inicializa el exportador de partituras.

        Args:
            musescore_path: Ruta al ejecutable de MuseScore 4
        """
        self.musescore_path = musescore_path or "/usr/bin/mscore4"
        self._check_musescore_installation()

        logger.info(
            f"Inicializando ScoreExporter con MuseScore en: {self.musescore_path}"
        )

    def _check_musescore_installation(self) -> bool:
        """Verifica si MuseScore 4 está instalado y accesible."""
        if shutil.which(self.musescore_path) is None:
            logger.warning(f"MuseScore 4 no encontrado en: {self.musescore_path}")
            logger.warning("Se usará modo mock para exportación")
            self.mock_mode = True
            return False

        try:
            # Probar ejecución básica
            result = subprocess.run(
                [self.musescore_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                logger.info(f"MuseScore 4 detectado: {result.stdout.strip()}")
                self.mock_mode = False
                return True
            else:
                logger.warning(f"MuseScore 4 encontrado pero falló: {result.stderr}")
                self.mock_mode = True
                return False

        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.warning(f"Error al verificar MuseScore 4: {e}")
            self.mock_mode = True
            return False

    def to_pdf(self, musicxml_path: Path, output_path: Path) -> Path:
        """
        Genera PDF de partitura completa.

        Args:
            musicxml_path: Ruta al archivo MusicXML
            output_path: Ruta de salida para el PDF

        Returns:
            Ruta al archivo PDF generado
        """
        logger.info(f"Generando PDF desde: {musicxml_path}")

        if self.mock_mode:
            return self._mock_export_pdf(musicxml_path, output_path)

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            cmd = [self.musescore_path, "-o", str(output_path), str(musicxml_path)]

            logger.debug(f"Ejecutando comando: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,  # Timeout de 30 segundos
            )

            if result.returncode == 0:
                logger.info(f"PDF generado exitosamente: {output_path}")
                return output_path
            else:
                logger.error(f"Error generando PDF: {result.stderr}")
                raise RuntimeError(f"Error de MuseScore: {result.stderr}")

        except subprocess.TimeoutExpired:
            logger.error("Timeout al generar PDF")
            raise
        except (OSError, RuntimeError) as e:
            logger.error(f"Error de sistema generando PDF: {e}")
            raise ScoreExportError(f"Error exportando PDF: {e}") from e

    def to_parts(self, musicxml_path: Path, output_dir: Path) -> list[Path]:
        """
        Genera PDF de parte individual por instrumento.

        Args:
            musicxml_path: Ruta al archivo MusicXML
            output_dir: Directorio de salida para las partes

        Returns:
            Lista de rutas a los archivos PDF generados
        """
        logger.info(f"Generando partes individuales desde: {musicxml_path}")

        if self.mock_mode:
            return self._mock_export_parts(musicxml_path, output_dir)

        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            # MuseScore 4 no tiene opción nativa para exportar partes individuales
            # directamente desde CLI. Una alternativa es:
            # 1. Exportar el MusicXML completo
            # 2. Usar music21 para separar partes
            # 3. Exportar cada parte individualmente

            logger.warning(
                "Exportación de partes individuales no implementada completamente"
            )
            logger.warning("Se requiere implementación adicional con music21")

            # Por ahora, solo exportamos el score completo
            main_pdf = output_dir / "score_completo.pdf"
            self.to_pdf(musicxml_path, main_pdf)

            return [main_pdf]

        except (OSError, RuntimeError) as e:
            logger.error(f"Error de sistema generando partes: {e}")
            raise ScoreExportError(f"Error exportando partes: {e}") from e

    def to_png(self, musicxml_path: Path, output_dir: Path) -> list[Path]:
        """
        Genera imágenes PNG por página (para previsualización).

        Args:
            musicxml_path: Ruta al archivo MusicXML
            output_dir: Directorio de salida para las imágenes

        Returns:
            Lista de rutas a los archivos PNG generados
        """
        logger.info(f"Generando imágenes PNG desde: {musicxml_path}")

        if self.mock_mode:
            return self._mock_export_png(musicxml_path, output_dir)

        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            # MuseScore 4 CLI para exportar PNG
            output_pattern = str(output_dir / "page_%d.png")

            cmd = [self.musescore_path, "-o", output_pattern, str(musicxml_path)]

            logger.debug(f"Ejecutando comando: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                # Encontrar archivos PNG generados
                png_files = list(output_dir.glob("page_*.png"))
                logger.info(f"PNGs generados: {len(png_files)} archivos")
                return png_files
            else:
                logger.error(f"Error generando PNGs: {result.stderr}")
                raise RuntimeError(f"Error de MuseScore: {result.stderr}")

        except (OSError, RuntimeError) as e:
            logger.error(f"Error de sistema generando PNGs: {e}")
            raise ScoreExportError(f"Error exportando PNGs: {e}") from e

    # Métodos mock para cuando MuseScore no está disponible
    def _mock_export_pdf(self, musicxml_path: Path, output_path: Path) -> Path:
        """Mock para exportación de PDF."""
        logger.warning("MODO MOCK: Simulando exportación de PDF")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Crear un archivo PDF dummy
        with open(output_path, "w") as f:
            f.write(f"%PDF-1.4\n% Mock PDF generated by WILLKA\n")
            f.write(f"% Source: {musicxml_path}\n")
            f.write(f"% This is a mock PDF. Install MuseScore 4 for real export.\n")

        logger.info(f"Mock PDF creado: {output_path}")
        return output_path

    def _mock_export_parts(self, musicxml_path: Path, output_dir: Path) -> list[Path]:
        """Mock para exportación de partes individuales."""
        logger.warning("MODO MOCK: Simulando exportación de partes individuales")

        output_dir.mkdir(parents=True, exist_ok=True)

        # Partes de ejemplo basadas en STEM_TO_INSTRUMENT
        parts = [
            "Flute",
            "Oboe",
            "Clarinet",
            "Bassoon",
            "Horn",
            "Trumpet",
            "Trombone",
            "Violin",
            "Viola",
            "Cello",
            "Contrabass",
            "Harp",
            "Timpani",
            "Percussion",
        ]

        generated_files = []
        for part_name in parts:
            part_path = output_dir / f"{part_name.lower()}.pdf"
            with open(part_path, "w") as f:
                f.write(f"%PDF-1.4\n% Mock part for: {part_name}\n")
                f.write(f"% Source: {musicxml_path}\n")

            generated_files.append(part_path)

        logger.info(f"Mock parts creados: {len(generated_files)} archivos")
        return generated_files

    def _mock_export_png(self, musicxml_path: Path, output_dir: Path) -> list[Path]:
        """Mock para exportación de PNG."""
        logger.warning("MODO MOCK: Simulando exportación de PNG")

        output_dir.mkdir(parents=True, exist_ok=True)

        # Crear algunos PNGs dummy
        png_files = []
        for i in range(1, 4):  # 3 páginas de ejemplo
            png_path = output_dir / f"page_{i}.png"
            with open(png_path, "w") as f:
                f.write(f"Mock PNG page {i}\n")
                f.write(f"Source: {musicxml_path}\n")

            png_files.append(png_path)

        logger.info(f"Mock PNGs creados: {len(png_files)} archivos")
        return png_files

    def get_installation_instructions(self) -> str:
        """Devuelve instrucciones para instalar MuseScore 4."""
        instructions = """
        MuseScore 4 no está instalado o no es accesible.
        
        Para instalar MuseScore 4 en Ubuntu/Debian:
        
        1. Agregar el repositorio oficial:
           sudo apt install software-properties-common
           sudo add-apt-repository ppa:mscore-ubuntu/mscore4-stable
           sudo apt update
        
        2. Instalar MuseScore 4:
           sudo apt install musescore4
        
        3. Verificar instalación:
           mscore4 --version
        
        En WSL2, también necesitarás un servidor X11 para la interfaz gráfica.
        """
        return instructions
