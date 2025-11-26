import logging
from pathlib import Path

from src.data_processing.audio_transcription import transcribe_audios
from src.data_processing.text_cleaning import clean_transcripts
from src.data_processing.audio_features import add_audio_duration  # 👈 NUEVO

logger = logging.getLogger(__name__)


def run_processing(model_name: str = "base") -> None:
    logger.info("Iniciando etapa de transcripción de audios...")
    transcripts_path: Path = transcribe_audios(model_name=model_name)

    logger.info("Agregando duración de audio...")
    add_audio_duration(transcripts_path)  # 👈 AQUÍ

    logger.info("Iniciando etapa de limpieza de transcripciones...")
    cleaned_path: Path = clean_transcripts(transcripts_path)

    logger.info("Procesamiento completo.")
    logger.info("Archivo de transcripciones: %s", transcripts_path)
    logger.info("Archivo de transcripciones limpias: %s", cleaned_path)
