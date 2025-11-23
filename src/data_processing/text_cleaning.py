import logging
import re
from pathlib import Path
from typing import Any

import contractions
import pandas as pd

from src.config import TRANSCRIPTS_CSV, CLEANED_TRANSCRIPTS_CSV, PROCESSED_DIR

logger = logging.getLogger(__name__)


def minimal_clean(text: Any) -> str:
    """
    Aplica una limpieza mínima al texto manteniendo información útil
    para análisis posterior (sentimientos, temas, etc.).

    Reglas:
    - Expande contracciones en inglés (I'm -> I am).
    - Normaliza espacios en blanco.
    - Elimina caracteres raros, pero mantiene puntuación básica.

    Parámetros
    ----------
    text : Any
        Texto original.

    Retorna
    -------
    str
        Texto limpiado.
    """
    if not isinstance(text, str) or pd.isna(text):
        return ""

    # Expandir contracciones (no, I'm, you're, etc.)
    text = contractions.fix(text)

    # Quitar espacios repetidos
    text = " ".join(text.split())

    # Mantener letras, números y puntuación básica
    text = re.sub(r"[^a-zA-Z0-9\s.,!?\'-]", "", text)

    return text


def clean_transcripts(transcripts_path: Path | None = None) -> Path:
    """
    Carga el CSV de transcripciones, aplica limpieza de texto
    y guarda un nuevo CSV con la columna 'cleaned_transcript'.

    Parámetros
    ----------
    transcripts_path : Path | None
        Ruta al CSV de transcripciones. Si es None, se usa TRANSCRIPTS_CSV.

    Retorna
    -------
    Path
        Ruta al CSV con las transcripciones limpiadas.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    path = transcripts_path if transcripts_path is not None else TRANSCRIPTS_CSV

    if not Path(path).exists():
        msg = f"No se encontró el archivo de transcripciones: {path}"
        logger.error(msg)
        raise FileNotFoundError(msg)

    logger.info("Cargando transcripciones desde: %s", path)
    df = pd.read_csv(path)

    if "transcript" not in df.columns:
        msg = f"No se encontró la columna 'transcript' en {path}"
        logger.error(msg)
        raise ValueError(msg)

    # Rellenar nulos para evitar errores en la función de limpieza
    df["transcript"] = df["transcript"].fillna("")

    logger.info("Aplicando limpieza mínima de texto a %d filas", len(df))
    df["cleaned_transcript"] = df["transcript"].apply(minimal_clean)

    # Mantener columnas útiles: ID, file_name (si existen) y cleaned_transcript
    keep_columns = []
    for col in ["ID", "file_name", "transcript", "cleaned_transcript"]:
        if col in df.columns:
            keep_columns.append(col)

    cleaned_df = df[keep_columns].copy()
    cleaned_df.to_csv(CLEANED_TRANSCRIPTS_CSV, index=False)

    logger.info("Transcripciones limpiadas guardadas en: %s", CLEANED_TRANSCRIPTS_CSV)
    return CLEANED_TRANSCRIPTS_CSV
