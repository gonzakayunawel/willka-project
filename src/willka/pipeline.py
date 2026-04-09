"""Módulo 5: Orquestador principal del pipeline WILLKA."""

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Mapping

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from .config import PipelineConfig
from .stem_separator import StemSeparator
from .transcriber import AudioTranscriber
from .score_builder import ScoreBuilder
from .exporter import ScoreExporter
from .exceptions import WillkaError

# Import para type hints
from music21 import stream

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class PipelineResult:
    """Resultado de la ejecución del pipeline."""

    success: bool
    stems: dict[str, Path]
    midis: dict[str, Path]
    musicxml_path: Path | None
    pdf_path: Path | None
    parts_dir: Path | None
    elapsed_seconds: float
    errors: list[str]


class TranscriptionPipeline:
    """Pipeline principal de transcripción musical."""

    def __init__(self, config: PipelineConfig | None = None) -> None:
        """
        Inicializa el pipeline de transcripción.

        Args:
            config: Configuración del pipeline (None para usar valores por defecto)
        """
        self.config = config or PipelineConfig()
        self._setup_logging()

        logger.info("Inicializando TranscriptionPipeline")
        logger.info(f"Configuración: {self.config}")

        # Inicializar módulos
        self.stem_separator = StemSeparator(
            model=self.config.demucs_model,
            device=self.config.device,
        )

        self.transcriber = AudioTranscriber(
            onset_threshold=self.config.onset_threshold,
            frame_threshold=self.config.frame_threshold,
            minimum_note_length=self.config.minimum_note_length,
            minimum_frequency=self.config.minimum_frequency,
            maximum_frequency=self.config.maximum_frequency,
        )

        self.score_builder = ScoreBuilder(
            title=self.config.title,
            composer=self.config.composer,
            tempo_bpm=self.config.tempo_bpm,
            year=self.config.year,
        )

        self.exporter = ScoreExporter(
            musescore_path=self.config.musescore_path,
        )

        logger.info("Módulos inicializados exitosamente")

    def _setup_logging(self) -> None:
        """Configura el sistema de logging."""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()),
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(rich_tracebacks=True)],
        )

    def run(self, input_audio: Path) -> PipelineResult:
        """
        Ejecuta el pipeline completo.

        Args:
            input_audio: Ruta al archivo de audio de entrada

        Returns:
            PipelineResult con rutas de todos los archivos generados
            y métricas de ejecución.
        """
        start_time = time.time()
        errors = []

        console.print("[bold blue]🚀 Iniciando pipeline WILLKA[/bold blue]")
        console.print(f"📁 Entrada: {input_audio}")

        # Validar archivo de entrada
        if not self._validate_input(input_audio):
            errors.append(f"Archivo de entrada inválido: {input_audio}")
            return PipelineResult(
                success=False,
                stems={},
                midis={},
                musicxml_path=None,
                pdf_path=None,
                parts_dir=None,
                elapsed_seconds=time.time() - start_time,
                errors=errors,
            )

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                # Etapa 1: Separación de stems
                task1 = progress.add_task("[cyan]Separando stems...", total=None)
                stems = self._run_stem_separation(input_audio)
                progress.update(
                    task1, completed=1, description="[green]✓ Stems separados"
                )

                # Etapa 2: Transcripción MIDI
                task2 = progress.add_task("[cyan]Transcribiendo a MIDI...", total=None)
                midis = self._run_transcription(stems)
                progress.update(
                    task2, completed=1, description="[green]✓ MIDIs generados"
                )

                # Etapa 3: Construcción de partitura
                task3 = progress.add_task("[cyan]Construyendo partitura...", total=None)
                score, musicxml_path = self._run_score_building(midis)
                progress.update(
                    task3, completed=1, description="[green]✓ Partitura construida"
                )

                # Etapa 4: Exportación
                task4 = progress.add_task("[cyan]Exportando resultados...", total=None)
                pdf_path, parts_dir = self._run_export(musicxml_path)
                progress.update(
                    task4, completed=1, description="[green]✓ Resultados exportados"
                )

            elapsed_time = time.time() - start_time

            console.print(
                f"\n[bold green]✅ Pipeline completado en {elapsed_time:.2f} segundos[/bold green]"
            )
            self._print_summary(stems, midis, musicxml_path, pdf_path, parts_dir)

            return PipelineResult(
                success=True,
                stems=stems,
                midis=midis,
                musicxml_path=musicxml_path,
                pdf_path=pdf_path,
                parts_dir=parts_dir,
                elapsed_seconds=elapsed_time,
                errors=errors,
            )

        except WillkaError as e:
            elapsed_time = time.time() - start_time
            error_msg = f"Error en el pipeline: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

            console.print(
                f"\n[bold red]❌ Pipeline falló después de {elapsed_time:.2f} segundos[/bold red]"
            )
            console.print(f"[red]Error: {str(e)}[/red]")
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = f"Error inesperado en el pipeline: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

            console.print(
                f"\n[bold red]❌ Pipeline falló después de {elapsed_time:.2f} segundos[/bold red]"
            )
            console.print(f"[red]Error inesperado: {str(e)}[/red]")

            return PipelineResult(
                success=False,
                stems={},
                midis={},
                musicxml_path=None,
                pdf_path=None,
                parts_dir=None,
                elapsed_seconds=elapsed_time,
                errors=errors,
            )

    def _validate_input(self, input_audio: Path) -> bool:
        """Valida el archivo de entrada."""
        if not input_audio.exists():
            logger.error(f"Archivo no encontrado: {input_audio}")
            return False

        if input_audio.stat().st_size == 0:
            logger.error(f"Archivo vacío: {input_audio}")
            return False

        # Verificar extensión
        valid_extensions = {".mp3", ".wav", ".flac", ".ogg", ".m4a"}
        if input_audio.suffix.lower() not in valid_extensions:
            logger.warning(
                f"Extensión no común: {input_audio.suffix}. "
                f"Extensiones soportadas: {valid_extensions}"
            )

        logger.info(
            f"Archivo de entrada válido: {input_audio} "
            f"({input_audio.stat().st_size / 1024 / 1024:.2f} MB)"
        )
        return True

    def _run_stem_separation(self, input_audio: Path) -> dict[str, Path]:
        """Ejecuta la etapa 1: Separación de stems."""
        console.print(
            "\n[bold cyan]🎵 Etapa 1: Separación de stems instrumentales[/bold cyan]"
        )

        # Información del dispositivo
        device_info = self.stem_separator.get_device_info()
        console.print(f"  Dispositivo: {device_info['device']}")
        if device_info["device"] == "cuda":
            console.print(f"  GPU: {device_info.get('device_name', 'N/A')}")

        # Separar stems
        stems = self.stem_separator.separate(input_audio, self.config.stems_dir)

        console.print(f"  [green]✓ {len(stems)} stems generados:[/green]")
        for stem_name, stem_path in stems.items():
            console.print(f"    • {stem_name}: {stem_path}")

        return stems

    def _run_transcription(self, stems: Mapping[str, Path]) -> dict[str, Path]:
        """Ejecuta la etapa 2: Transcripción a MIDI."""
        console.print("\n[bold cyan]🎹 Etapa 2: Transcripción audio → MIDI[/bold cyan]")
        onset = self.config.onset_threshold
        frame = self.config.frame_threshold
        console.print(f"  Parámetros: onset={onset}, frame={frame}")

        midis = self.transcriber.transcribe_all(stems, self.config.midi_dir)

        console.print(f"  [green]✓ {len(midis)} archivos MIDI generados:[/green]")
        for stem_name, midi_path in midis.items():
            stats = self.transcriber.get_transcription_stats(midi_path)
            if stats:
                console.print(
                    f"    • {stem_name}: {midi_path} ({stats['total_notes']} notas)"
                )

        return midis

    def _run_score_building(
        self, midis: Mapping[str, Path]
    ) -> tuple[stream.Score, Path]:
        """Ejecuta la etapa 3: Construcción de partitura."""
        console.print(
            "\n[bold cyan]📄 Etapa 3: Construcción de partitura orquestal[/bold cyan]"
        )
        console.print(f"  Obra: {self.config.title}")
        console.print(f"  Compositor: {self.config.composer}")

        # Construir score
        score = self.score_builder.build(midis)

        # Exportar MusicXML
        musicxml_dir = self.config.output_dir / "musicxml"
        musicxml_path = (
            musicxml_dir / f"{self.config.title.lower().replace(' ', '_')}.xml"
        )
        self.score_builder.export_musicxml(score, musicxml_path)

        # Exportar MIDI unificado
        midi_merged_path = self.config.output_dir / "midi" / "score_completo.mid"
        self.score_builder.export_midi_merged(score, midi_merged_path)

        console.print(
            f"  [green]✓ Partitura construida: {len(score.parts)} partes[/green]"
        )
        console.print(f"  [green]✓ MusicXML exportado: {musicxml_path}[/green]")
        console.print(f"  [green]✓ MIDI unificado: {midi_merged_path}[/green]")

        return score, musicxml_path

    def _run_export(self, musicxml_path: Path) -> tuple[Path, Path]:
        """Ejecuta la etapa 4: Exportación de resultados."""
        console.print("\n[bold cyan]📤 Etapa 4: Exportación de resultados[/bold cyan]")

        # Exportar PDF
        pdf_dir = self.config.output_dir / "pdf"
        pdf_path = pdf_dir / f"{self.config.title.lower().replace(' ', '_')}.pdf"
        self.exporter.to_pdf(musicxml_path, pdf_path)

        # Exportar partes individuales
        parts_dir = self.config.output_dir / "partes"
        parts = self.exporter.to_parts(musicxml_path, parts_dir)

        # Exportar PNGs para previsualización
        png_dir = self.config.output_dir / "png"
        pngs = self.exporter.to_png(musicxml_path, png_dir)

        console.print(f"  [green]✓ PDF generado: {pdf_path}[/green]")
        console.print(
            f"  [green]✓ Partes individuales: {len(parts)} archivos en {parts_dir}[/green]"
        )
        console.print(
            f"  [green]✓ Previsualizaciones PNG: {len(pngs)} imágenes en {png_dir}[/green]"
        )

        if self.exporter.mock_mode:
            console.print(
                "[yellow]⚠  Nota: MuseScore 4 no está instalado. "
                "Se usó modo mock para exportación.[/yellow]"
            )
            console.print(
                "[yellow]   Instale MuseScore 4 para exportación real de partituras.[/yellow]"
            )

        return pdf_path, parts_dir

    def _print_summary(
        self,
        stems: Mapping[str, Path],
        midis: Mapping[str, Path],
        musicxml_path: Path | None,
        pdf_path: Path | None,
        parts_dir: Path | None,
    ) -> None:
        """Imprime un resumen de los resultados."""
        console.print("\n[bold]📊 Resumen de resultados:[/bold]")
        console.print(f"  • Stems generados: {len(stems)}")
        console.print(f"  • Archivos MIDI: {len(midis)}")
        console.print(f"  • Partitura MusicXML: {musicxml_path}")
        console.print(f"  • PDF de partitura: {pdf_path}")
        console.print(f"  • Partes individuales: {parts_dir}")

        # Mostrar estructura de archivos
        console.print("\n[bold]📁 Estructura de archivos generados:[/bold]")
        for dir_path in [
            self.config.stems_dir,
            self.config.midi_dir,
            self.config.output_dir,
        ]:
            if dir_path.exists():
                console.print(f"  {dir_path}/")
                for item in sorted(dir_path.rglob("*")):
                    if item.is_file():
                        rel_path = item.relative_to(dir_path)
                        console.print(f"    ├── {rel_path}")

    def run_stems_only(self, input_audio: Path) -> dict[str, Path]:
        """Ejecuta solo la separación de stems."""
        console.print("[bold cyan]🎵 Ejecutando solo separación de stems[/bold cyan]")
        return self._run_stem_separation(input_audio)

    def run_transcription_only(self, stems_dir: Path) -> dict[str, Path]:
        """Ejecuta solo la transcripción de stems existentes."""
        console.print("[bold cyan]🎹 Ejecutando solo transcripción[/bold cyan]")

        # Encontrar stems en el directorio
        stems = {}
        for stem_file in stems_dir.glob("*.wav"):
            stem_name = stem_file.stem
            if stem_name in ["drums", "bass", "piano", "guitar", "other"]:
                stems[stem_name] = stem_file

        if not stems:
            raise ValueError(f"No se encontraron stems en {stems_dir}")

        return self._run_transcription(stems)

    def run_build_only(self, midi_dir: Path) -> Path:
        """Ejecuta solo la construcción de partitura desde MIDIs existentes."""
        console.print(
            "[bold cyan]📄 Ejecutando solo construcción de partitura[/bold cyan]"
        )

        # Encontrar MIDIs en el directorio
        midis = {}
        for midi_file in midi_dir.glob("*.mid"):
            stem_name = midi_file.stem
            if stem_name in ["drums", "bass", "piano", "guitar", "other"]:
                midis[stem_name] = midi_file

        if not midis:
            raise ValueError(f"No se encontraron archivos MIDI en {midi_dir}")

        score, musicxml_path = self._run_score_building(midis)
        return musicxml_path
