"""Módulo 3: Ensamblaje de partitura orquestal usando music21."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from music21 import converter, instrument, metadata, note, stream, tempo

from .config import OBRA_METADATA, STEM_TO_INSTRUMENT

logger = logging.getLogger(__name__)


class ScoreBuilder:
    """Constructor de partitura orquestal a partir de archivos MIDI."""

    def __init__(
        self,
        title: Optional[str] = None,
        composer: Optional[str] = None,
        tempo_bpm: int = 100,
        year: Optional[int] = None,
        notes: Optional[str] = None,
    ):
        """
        Inicializa el constructor de partitura.

        Args:
            title: Título de la obra
            composer: Compositor
            tempo_bpm: Tempo en beats por minuto
            year: Año de composición
            notes: Notas adicionales
        """
        self.title = title or OBRA_METADATA["title"]
        self.composer = composer or OBRA_METADATA["composer"]
        self.tempo_bpm = tempo_bpm
        self.year = year or OBRA_METADATA["year"]
        self.notes = notes or OBRA_METADATA.get("notes", "")

        logger.info(f"Inicializando ScoreBuilder para: {self.title}")
        logger.info(f"  Compositor: {self.composer}")
        logger.info(f"  Tempo: {tempo_bpm} BPM")
        logger.info(f"  Año: {self.year}")

    def build(self, midi_files: Dict[str, Path]) -> stream.Score:
        """
        Construye un Score de music21 a partir de los MIDIs por stem.

        Args:
            midi_files: Diccionario {nombre_stem: ruta_midi}

        Returns:
            Objeto Score de music21 listo para exportar.
        """
        logger.info(
            f"Construyendo partitura a partir de {len(midi_files)} archivos MIDI"
        )

        # Crear score principal
        score = stream.Score()

        # Agregar metadatos
        self._add_metadata(score)

        # Procesar cada stem
        for stem_name, midi_path in midi_files.items():
            if stem_name not in STEM_TO_INSTRUMENT:
                logger.warning(
                    f"Stem '{stem_name}' no tiene mapeo de instrumentos, omitiendo"
                )
                continue

            logger.info(f"Procesando stem: {stem_name}")
            self._add_stem_to_score(score, stem_name, midi_path)

        # Ajustar tempo global
        self._set_tempo(score)

        logger.info(f"Partitura construida: {len(score.parts)} partes")
        return score

    def _add_metadata(self, score: stream.Score) -> None:
        """Agrega metadatos a la partitura."""
        md = metadata.Metadata()
        md.title = self.title
        md.composer = self.composer
        md.date = str(self.year)

        if self.notes:
            # Agregar notas como comentario
            comment = note.Unpitched()
            comment.lyric = self.notes
            # Nota: en music21, los metadatos extensos se manejan mejor en el encabezado

        score.insert(0, md)
        logger.debug("Metadatos agregados a la partitura")

    def _add_stem_to_score(
        self, score: stream.Score, stem_name: str, midi_path: Path
    ) -> None:
        """
        Agrega un stem MIDI a la partitura con los instrumentos apropiados.

        Args:
            score: Score de music21
            stem_name: Nombre del stem (ej: "other", "guitar")
            midi_path: Ruta al archivo MIDI
        """
        try:
            # Cargar MIDI
            midi_stream = converter.parse(str(midi_path))
            logger.debug(f"MIDI cargado: {midi_path}")

            # Obtener instrumentos para este stem
            instrument_names = STEM_TO_INSTRUMENT.get(stem_name, [])
            if not instrument_names:
                logger.warning(f"No hay instrumentos definidos para stem '{stem_name}'")
                return

            # Crear una parte por instrumento
            for instr_name in instrument_names:
                part = self._create_instrument_part(instr_name, midi_stream)
                if part:
                    score.append(part)
                    logger.debug(
                        f"Parte '{instr_name}' agregada para stem '{stem_name}'"
                    )

        except Exception as e:
            logger.error(f"Error procesando stem '{stem_name}' ({midi_path}): {e}")

    def _create_instrument_part(
        self, instrument_name: str, midi_stream: stream.Stream
    ) -> Optional[stream.Part]:
        """
        Crea una parte de instrumento a partir de un stream MIDI.

        Args:
            instrument_name: Nombre del instrumento
            midi_stream: Stream MIDI de entrada

        Returns:
            Parte de instrumento o None si hay error
        """
        try:
            # Crear instrumento music21
            music21_instrument = self._get_music21_instrument(instrument_name)
            if not music21_instrument:
                logger.warning(f"Instrumento no soportado: {instrument_name}")
                return None

            # Crear parte
            part = stream.Part()
            part.insert(0, music21_instrument)

            # Copiar notas del MIDI (simplificado - en producción se necesitaría
            # un mapeo más sofisticado de las pistas MIDI)
            for element in midi_stream.recurse():
                if isinstance(element, (note.Note, note.Rest, note.Chord)):
                    part.append(element)

            # Ajustar transposición si es necesario
            self._adjust_transposition(part, instrument_name)

            return part

        except Exception as e:
            logger.error(f"Error creando parte para {instrument_name}: {e}")
            return None

    def _get_music21_instrument(self, instrument_name: str):
        """Obtiene objeto instrument de music21 por nombre."""
        instrument_map = {
            # Vientos madera
            "Flute": instrument.Flute,
            "Oboe": instrument.Oboe,
            "Clarinet": instrument.Clarinet,
            "Bassoon": instrument.Bassoon,
            # Vientos metal
            "Horn": instrument.FrenchHorn,
            "Trumpet": instrument.Trumpet,
            "Trombone": instrument.Trombone,
            # Cuerdas
            "Violin": instrument.Violin,
            "Viola": instrument.Viola,
            "Cello": instrument.Violoncello,
            "Contrabass": instrument.Contrabass,
            # Percusión
            "Harp": instrument.Harp,
            "Timpani": instrument.Timpani,
            "Percussion": instrument.Percussion,
        }

        instr_class = instrument_map.get(instrument_name)
        if instr_class:
            return instr_class()

        return None

    def _adjust_transposition(self, part: stream.Part, instrument_name: str) -> None:
        """Ajusta transposición para instrumentos transpositores."""
        # Mapeo de transposiciones comunes (en semitonos)
        transpositions = {
            "Clarinet": -2,  # Clarinet in Bb
            "Trumpet": -2,  # Trumpet in Bb
            "Horn": -7,  # Horn in F
        }

        transposition = transpositions.get(instrument_name)
        if transposition:
            for element in part.recurse():
                if isinstance(element, note.Note):
                    element.pitch.transpose(transposition, inPlace=True)
                elif isinstance(element, note.Chord):
                    for pitch in element.pitches:
                        pitch.transpose(transposition, inPlace=True)

            logger.debug(
                f"Transposición aplicada: {instrument_name} ({transposition} semitonos)"
            )

    def _set_tempo(self, score: stream.Score) -> None:
        """Establece el tempo global de la partitura."""
        metronome = tempo.MetronomeMark(number=self.tempo_bpm)

        # Insertar en la primera parte
        if score.parts:
            score.parts[0].insert(0, metronome)
            logger.debug(f"Tempo establecido: {self.tempo_bpm} BPM")

    def export_musicxml(self, score: stream.Score, output_path: Path) -> Path:
        """
        Exporta la partitura a MusicXML.

        Args:
            score: Score de music21
            output_path: Ruta de salida

        Returns:
            Ruta al archivo MusicXML generado
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            score.write("musicxml", fp=str(output_path))
            logger.info(f"MusicXML exportado: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error exportando MusicXML: {e}")
            raise

    def export_midi_merged(self, score: stream.Score, output_path: Path) -> Path:
        """
        Exporta MIDI unificado de toda la partitura.

        Args:
            score: Score de music21
            output_path: Ruta de salida

        Returns:
            Ruta al archivo MIDI generado
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            score.write("midi", fp=str(output_path))
            logger.info(f"MIDI unificado exportado: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error exportando MIDI unificado: {e}")
            raise
