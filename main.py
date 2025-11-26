# main.py
import logging
from pathlib import Path

import pandas as pd  # 👈 nuevo

from src.config import CLEANED_TRANSCRIPTS_CSV, PROCESSED_DIR
from src.data_processing.run_processing import run_processing
from src.data_processing.llm_enrichment import enrich_calls_with_llm
from src.reporting.call_analytics import generate_call_analytics


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


if __name__ == "__main__":
    configure_logging()
    logger = logging.getLogger(__name__)

    enriched_csv = PROCESSED_DIR / "calls_enriched_llm.csv"
    summary_csv = PROCESSED_DIR / "calls_analytics_summary.csv"
    prioritized_csv = PROCESSED_DIR / "calls_prioritized.csv"

    # Audio -> texto + duración + limpieza (con check)
    need_processing = True

    if CLEANED_TRANSCRIPTS_CSV.exists():
        try:
            sample = pd.read_csv(CLEANED_TRANSCRIPTS_CSV, nrows=5)
            if "duration_seconds" in sample.columns:
                need_processing = False
                logger.info(
                    "Usando cleaned_transcripts existente con duration_seconds: %s",
                    CLEANED_TRANSCRIPTS_CSV,
                )
            else:
                logger.info(
                    "cleaned_transcripts.csv existe pero SIN duration_seconds. "
                    "Reconstruyendo transcripciones..."
                )
        except Exception as exc:
            logger.warning(
                "No se pudo leer cleaned_transcripts.csv, se reconstruirá. Error: %s",
                exc,
            )

    if need_processing:
        logger.info("Iniciando pipeline de procesamiento de datos (audio -> texto)...")
        run_processing()  # Whisper + duración + limpieza
        logger.info("Etapa de transcripción y limpieza completada.")

    # Enriquecimiento con LLM
    if enriched_csv.exists():
        logger.info(
            "Archivo enriquecido con LLM ya existe (%s). "
            "Saltando etapa de enriquecimiento.",
            enriched_csv,
        )
    else:
        logger.info("Iniciando etapa de enriquecimiento con LLM...")
        enrich_calls_with_llm(
            input_path=CLEANED_TRANSCRIPTS_CSV,
            output_filename=enriched_csv.name,
            max_calls=None,
            model="gpt-4.1-mini",
        )
        logger.info("Etapa de enriquecimiento con LLM completada.")

    # Analitica y priorizacion
    if summary_csv.exists() and prioritized_csv.exists():
        logger.info(
            "Archivos de analítica y priorización ya existen (%s, %s). "
            "Saltando etapa de analítica.",
            summary_csv,
            prioritized_csv,
        )
    else:
        logger.info("Iniciando etapa de analítica y priorización...")
        summary_path, prioritized_path = generate_call_analytics(
            enriched_path=enriched_csv,
            summary_filename=summary_csv.name,
            prioritized_filename=prioritized_csv.name,
        )
        logger.info("Etapa de analítica completada.")
        logger.info("Resumen de analítica: %s", summary_path)
        logger.info("Llamadas priorizadas: %s", prioritized_path)

    logger.info("Pipeline finalizado.")
