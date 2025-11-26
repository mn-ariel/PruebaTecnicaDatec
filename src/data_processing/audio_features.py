import logging
from pathlib import Path

import librosa
import pandas as pd

from src.config import RAW_AUDIO_DIR

logger = logging.getLogger(__name__)


def add_audio_duration(transcripts_path: Path) -> Path:
    """
    Agrega una columna duration_seconds al CSV de transcripciones
    a partir de los .wav en RAW_AUDIO_DIR.
    """
    df = pd.read_csv(transcripts_path)

    durations: list[float | None] = []

    for _, row in df.iterrows():
        # Usa ID si viene con ruta completa sino usamos RAW_AUDIO_DIR / file_name
        audio_path = Path(str(row.get("ID", "")))
        if not audio_path.is_absolute() or not audio_path.exists():
            audio_path = RAW_AUDIO_DIR / str(row["file_name"])

        try:
            y, sr = librosa.load(audio_path, sr=None)
            dur = len(y) / sr
        except Exception as exc:
            logger.warning("No se pudo leer audio %s: %s", audio_path, exc)
            dur = None

        durations.append(dur)

    df["duration_seconds"] = durations
    df.to_csv(transcripts_path, index=False)
    logger.info("Duración de audio agregada a: %s", transcripts_path)
    return transcripts_path
