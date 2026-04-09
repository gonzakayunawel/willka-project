"""Interfaz de línea de comandos para WILLKA."""

import sys
from pathlib import Path


import typer
from rich.console import Console

from .config import PipelineConfig
from .pipeline import TranscriptionPipeline
from .exceptions import WillkaError

app = typer.Typer(
    name="willka",
    help="WILLKA — Pipeline de transcripción musical: MP3 → MIDI → Partitura orquestal",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Callback para mostrar la versión."""
    if value:
        from . import __version__

        console.print(f"WILLKA v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Mostrar versión y salir",
    ),
) -> None:
    """WILLKA — Pipeline de transcripción musical."""
    pass


@app.command()
def run(
    audio_file: Path = typer.Argument(
        ...,
        help="Ruta al archivo de audio (MP3, WAV, etc.)",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    config_file: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Ruta al archivo de configuración TOML",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    device: str = typer.Option(
        "auto",
        "--device",
        "-d",
        help="Dispositivo a usar: 'cuda', 'cpu', o 'auto' para detección automática",
    ),
    output_dir: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Directorio de salida (sobrescribe configuración)",
    ),
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        "-l",
        help="Nivel de logging: DEBUG, INFO, WARNING, ERROR",
    ),
) -> None:
    """
    Ejecuta el pipeline completo de transcripción.

    Ejemplo:
        willka run audio.mp3 --device cuda --output resultados/
    """
    console.print("[bold blue]🚀 Ejecutando pipeline WILLKA completo[/bold blue]")

    # Cargar configuración
    config = PipelineConfig()

    # Aplicar opciones de línea de comandos
    if device != "auto":
        config.device = device

    if output_dir:
        config.output_dir = output_dir
        # Actualizar directorios dependientes
        config.stems_dir = output_dir / "stems"
        config.midi_dir = output_dir / "midi"

    config.log_level = log_level.upper()

    # Crear y ejecutar pipeline
    pipeline = TranscriptionPipeline(config)
    result = pipeline.run(audio_file)

    if result.success:
        console.print("[bold green]✅ Pipeline completado exitosamente[/bold green]")
        typer.Exit(0)
    else:
        console.print("[bold red]❌ Pipeline falló[/bold red]")
        for error in result.errors:
            console.print(f"[red]  Error: {error}[/red]")
        typer.Exit(1)


@app.command()
def stems(
    audio_file: Path = typer.Argument(
        ...,
        help="Ruta al archivo de audio",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output_dir: Path = typer.Option(
        Path("data/stems"),
        "--output",
        "-o",
        help="Directorio de salida para los stems",
    ),
    device: str = typer.Option(
        "auto",
        "--device",
        "-d",
        help="Dispositivo a usar: 'cuda', 'cpu', o 'auto'",
    ),
    model: str = typer.Option(
        "htdemucs_6s",
        "--model",
        "-m",
        help="Modelo Demucs a usar",
    ),
) -> None:
    """
    Ejecuta solo la separación de stems.

    Ejemplo:
        willka stems audio.mp3 --output stems/ --device cuda
    """
    console.print("[bold cyan]🎵 Ejecutando separación de stems[/bold cyan]")

    config = PipelineConfig()
    config.device = device if device != "auto" else config.device
    config.demucs_model = model
    config.stems_dir = output_dir

    pipeline = TranscriptionPipeline(config)

    try:
        stems = pipeline.run_stems_only(audio_file)
        console.print(f"[green]✓ {len(stems)} stems generados en: {output_dir}[/green]")
        for stem_name, stem_path in stems.items():
            console.print(f"  • {stem_name}: {stem_path}")
    except WillkaError as e:
        console.print(f"[red]❌ Error de WILLKA: {e}[/red]")
        typer.Exit(1)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        console.print(f"[red]❌ Error inesperado: {e}[/red]")
        typer.Exit(1)


@app.command()
def transcribe(
    stems_dir: Path = typer.Argument(
        ...,
        help="Directorio con los stems WAV",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
    output_dir: Path = typer.Option(
        Path("data/midi"),
        "--output",
        "-o",
        help="Directorio de salida para los archivos MIDI",
    ),
    onset_threshold: float = typer.Option(
        0.4,
        "--onset",
        help="Umbral para detección de onsets (0-1)",
    ),
    frame_threshold: float = typer.Option(
        0.25,
        "--frame",
        help="Umbral para detección de frames (0-1)",
    ),
) -> None:
    """
    Ejecuta solo la transcripción de stems a MIDI.

    Ejemplo:
        willka transcribe stems/ --output midi/ --onset 0.4 --frame 0.25
    """
    console.print("[bold cyan]🎹 Ejecutando transcripción a MIDI[/bold cyan]")

    config = PipelineConfig()
    config.onset_threshold = onset_threshold
    config.frame_threshold = frame_threshold
    config.midi_dir = output_dir

    pipeline = TranscriptionPipeline(config)

    try:
        midis = pipeline.run_transcription_only(stems_dir)
        console.print(
            f"[green]✓ {len(midis)} archivos MIDI generados en: {output_dir}[/green]"
        )
        for stem_name, midi_path in midis.items():
            console.print(f"  • {stem_name}: {midi_path}")
    except WillkaError as e:
        console.print(f"[red]❌ Error de WILLKA: {e}[/red]")
        typer.Exit(1)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        console.print(f"[red]❌ Error inesperado: {e}[/red]")
        typer.Exit(1)


@app.command()
def build(
    midi_dir: Path = typer.Argument(
        ...,
        help="Directorio con los archivos MIDI",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
    output_dir: Path = typer.Option(
        Path("data/output"),
        "--output",
        "-o",
        help="Directorio de salida para la partitura",
    ),
    title: str = typer.Option(
        "Desde Antofagasta a Tiahuanaco",
        "--title",
        "-t",
        help="Título de la obra",
    ),
    composer: str = typer.Option(
        "Gonzalo Cayunao Erices (KayuNawel)",
        "--composer",
        "-c",
        help="Nombre del compositor",
    ),
    tempo: int = typer.Option(
        100,
        "--tempo",
        help="Tempo en beats por minuto",
    ),
) -> None:
    """
    Ejecuta solo la construcción de partitura desde MIDIs.

    Ejemplo:
        willka build midi/ --output partitura/ --title "Mi Obra" --composer "Yo"
    """
    console.print("[bold cyan]📄 Ejecutando construcción de partitura[/bold cyan]")

    config = PipelineConfig()
    config.title = title
    config.composer = composer
    config.tempo_bpm = tempo
    config.output_dir = output_dir

    pipeline = TranscriptionPipeline(config)

    try:
        musicxml_path = pipeline.run_build_only(midi_dir)
        console.print(f"[green]✓ Partitura construida: {musicxml_path}[/green]")

        # Mostrar ubicaciones esperadas
        pdf_path = output_dir / "pdf" / f"{title.lower().replace(' ', '_')}.pdf"
        parts_dir = output_dir / "partes"

        console.print(f"[green]✓ PDF esperado: {pdf_path}[/green]")
        console.print(f"[green]✓ Partes individuales: {parts_dir}[/green]")

    except WillkaError as e:
        console.print(f"[red]❌ Error de WILLKA: {e}[/red]")
        typer.Exit(1)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        console.print(f"[red]❌ Error inesperado: {e}[/red]")
        typer.Exit(1)


@app.command()
def check() -> None:
    """
    Verifica las dependencias y configuración del sistema.

    Ejemplo:
        willka check
    """
    console.print("[bold blue]🔍 Verificando sistema WILLKA[/bold blue]")

    # Verificar Python
    console.print("\n[bold]Python:[/bold]")
    console.print(f"  Versión: {sys.version}")

    # Verificar PyTorch y CUDA
    console.print("\n[bold]PyTorch y CUDA:[/bold]")
    try:
        import torch

        console.print(f"  PyTorch versión: {torch.__version__}")
        console.print(f"  CUDA disponible: {torch.cuda.is_available()}")

        if torch.cuda.is_available():
            console.print(f"  Dispositivo CUDA: {torch.cuda.get_device_name(0)}")
            console.print(
                f"  Memoria GPU: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB"
            )
        else:
            console.print("  [yellow]⚠  CUDA no disponible, usando CPU[/yellow]")
    except ImportError:
        console.print("  [red]❌ PyTorch no instalado[/red]")

    # Verificar MuseScore
    console.print("\n[bold]MuseScore 4:[/bold]")
    from .exporter import ScoreExporter

    exporter = ScoreExporter()
    if exporter.mock_mode:
        console.print("  [yellow]⚠  MuseScore 4 no encontrado[/yellow]")
        console.print("  [yellow]   Se usará modo mock para exportación[/yellow]")
    else:
        console.print("  [green]✓ MuseScore 4 disponible[/green]")

    # Verificar otros módulos clave
    console.print("\n[bold]Módulos principales:[/bold]")
    modules = ["demucs", "basic_pitch", "music21", "pretty_midi", "librosa"]

    for module_name in modules:
        try:
            __import__(module_name)
            console.print(f"  [green]✓ {module_name}[/green]")
        except ImportError:
            console.print(f"  [red]❌ {module_name} no instalado[/red]")

    console.print("\n[bold]🎯 Sistema listo para WILLKA[/bold]")


if __name__ == "__main__":
    app()
