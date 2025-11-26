import logging
import os
from pathlib import Path
from typing import List, Optional

import pandas as pd
import whisper

from src.config import RAW_AUDIO_DIR, PROCESSED_DIR, TRANSCRIPTS_CSV

logger = logging.getLogger(__name__)


def list_wav_files(folder: Path) -> List[Path]:
    if not folder.exists():
        # Mensaje claro si la carpeta no existe
        msg = f"La carpeta de audios no existe: {folder}"
        logger.error(msg)
        raise FileNotFoundError(msg)

    wav_files = sorted(
        [folder / f for f in os.listdir(folder) if f.endswith(".wav")]
    )

    logger.info("Se encontraron %d archivos .wav en %s", len(wav_files), folder)
    return wav_files


def transcribe_audios(
    model_name: str = "base",
    language: Optional[str] = None,
) -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    audio_files = list_wav_files(RAW_AUDIO_DIR)
    if not audio_files:
        logger.warning("No se encontraron archivos .wav en %s", RAW_AUDIO_DIR)
        # Crea un CSV vacio para mantener consistencia en el pipeline
        empty_df = pd.DataFrame(columns=["ID", "file_name", "transcript"])
        empty_df.to_csv(TRANSCRIPTS_CSV, index=False)
        return TRANSCRIPTS_CSV

    logger.info("Cargando modelo Whisper: %s", model_name)
    model = whisper.load_model(model_name)

    rows = []
    success_count = 0
    error_count = 0

    for audio_path in audio_files:
        logger.info("Transcribiendo archivo: %s", audio_path.name)

        try:
            transcribe_kwargs = {}
            if language is not None:
                transcribe_kwargs["language"] = language

            result = model.transcribe(str(audio_path), **transcribe_kwargs)
            text = result.get("text", "").strip()
            success_count += 1

        except Exception as exc:
            logger.error(
                "Error transcribiendo %s: %s", audio_path.name, exc
            )
            text = ""
            error_count += 1

        rows.append(
            {
                "ID": str(audio_path),
                "file_name": audio_path.name,
                "transcript": text,
            }
        )

    transcripts_df = pd.DataFrame(rows)
    transcripts_df.to_csv(TRANSCRIPTS_CSV, index=False)

    logger.info(
        "Transcripciones guardadas en: %s (ok: %d, errores: %d)",
        TRANSCRIPTS_CSV,
        success_count,
        error_count,
    )
    return TRANSCRIPTS_CSV
