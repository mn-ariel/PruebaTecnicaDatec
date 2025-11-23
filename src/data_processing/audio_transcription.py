import logging
import os
from pathlib import Path
from typing import List

import pandas as pd
import whisper

from src.config import RAW_AUDIO_DIR, PROCESSED_DIR, TRANSCRIPTS_CSV

logger = logging.getLogger(__name__)


def list_wav_files(folder: Path) -> List[Path]:
    """
    Lista todos los archivos .wav en la carpeta indicada.

    Parámetros
    ----------
    folder : Path
        Carpeta donde se buscarán los audios.

    Retorna
    -------
    List[Path]
        Lista de rutas a archivos .wav.
    """
    if not folder.exists():
        # Mensaje claro si la carpeta no existe
        msg = f"La carpeta de audios no existe: {folder}"
        logger.error(msg)
        raise FileNotFoundError(msg)

    wav_files = [folder / f for f in os.listdir(folder) if f.endswith(".wav")]

    logger.info("Se encontraron %d archivos .wav en %s", len(wav_files), folder)
    return wav_files


def transcribe_audios(model_name: str = "base") -> Path:
    """
    Transcribe todos los audios .wav en RAW_AUDIO_DIR usando Whisper
    y guarda un CSV con las transcripciones.

    Parámetros
    ----------
    model_name : str
        Nombre del modelo de Whisper a usar (ej: 'tiny', 'base', 'small').

    Retorna
    -------
    Path
        Ruta al archivo CSV generado con las transcripciones.
    """
    # Asegurarse de que la carpeta de salida exista
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    audio_files = list_wav_files(RAW_AUDIO_DIR)
    if not audio_files:
        logger.warning("No se encontraron archivos .wav en %s", RAW_AUDIO_DIR)
        # Crear un CSV vacío para mantener consistencia de pipeline
        empty_df = pd.DataFrame(columns=["ID", "file_name", "transcript"])
        empty_df.to_csv(TRANSCRIPTS_CSV, index=False)
        return TRANSCRIPTS_CSV

    logger.info("Cargando modelo Whisper: %s", model_name)
    model = whisper.load_model(model_name)

    rows = []

    for audio_path in audio_files:
        logger.info("Transcribiendo archivo: %s", audio_path.name)
        # Se convierte a str porque Whisper espera una ruta como cadena
        result = model.transcribe(str(audio_path))

        rows.append(
            {
                "ID": str(audio_path),
                "file_name": audio_path.name,
                "transcript": result.get("text", ""),
            }
        )

    transcripts_df = pd.DataFrame(rows)
    transcripts_df.to_csv(TRANSCRIPTS_CSV, index=False)

    logger.info("Transcripciones guardadas en: %s", TRANSCRIPTS_CSV)
    return TRANSCRIPTS_CSV
