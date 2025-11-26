import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from src.config import CLEANED_TRANSCRIPTS_CSV, PROCESSED_DIR
from src.llm.call_analysis import analyze_call_text

logger = logging.getLogger(__name__)


def enrich_calls_with_llm(
    input_path: Optional[Path] = None,
    output_filename: str = "calls_enriched_llm.csv",
    model: str = "gpt-4.1-mini",
    max_calls: Optional[int] = None,
) -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    source = input_path if input_path is not None else CLEANED_TRANSCRIPTS_CSV

    if not Path(source).exists():
        msg = f"Cleaned transcripts file not found: {source}"
        logger.error(msg)
        raise FileNotFoundError(msg)

    logger.info("Loading cleaned transcripts from: %s", source)
    df = pd.read_csv(source)

    if "cleaned_transcript" not in df.columns:
        msg = "Column 'cleaned_transcript' not found in dataframe."
        logger.error(msg)
        raise ValueError(msg)

    df["cleaned_transcript"] = df["cleaned_transcript"].fillna("")

    if max_calls is not None:
        df = df.head(max_calls)
        logger.info("Limiting LLM enrichment to first %d calls.", max_calls)

    # Definimos todas las claves desde el inicio
    llm_results = {
        "sentiment": [],
        "call_type": [],
        "summary": [],

        "sentiment_start": [],
        "sentiment_end": [],
        "has_risk_phrases": [],
        "risk_phrases": [],
        "complexity_score": [],

        "prompt_tokens": [],
        "completion_tokens": [],
        "total_tokens": [],
    }

    for idx, row in df.iterrows():
        transcript = row["cleaned_transcript"]
        logger.info("Analyzing call %d...", idx)

        try:
            result = analyze_call_text(transcript=transcript, model=model)
        except Exception as exc:
            logger.error("Error analyzing call %d: %s", idx, exc)
            result = {
                "sentiment": "neutral",
                "call_type": "other",
                "summary": "",
                "sentiment_start": None,
                "sentiment_end": None,
                "has_risk_phrases": False,
                "risk_phrases": [],
                "complexity_score": None,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }

        # Campos base
        llm_results["sentiment"].append(result.get("sentiment"))
        llm_results["call_type"].append(result.get("call_type"))
        llm_results["summary"].append(result.get("summary"))

        # Campos enriquecidos
        llm_results["sentiment_start"].append(result.get("sentiment_start"))
        llm_results["sentiment_end"].append(result.get("sentiment_end"))
        llm_results["has_risk_phrases"].append(result.get("has_risk_phrases", False))
        llm_results["risk_phrases"].append(result.get("risk_phrases", []))
        llm_results["complexity_score"].append(result.get("complexity_score"))

        # Tokens
        llm_results["prompt_tokens"].append(result.get("prompt_tokens", 0))
        llm_results["completion_tokens"].append(result.get("completion_tokens", 0))
        llm_results["total_tokens"].append(result.get("total_tokens", 0))

    for col, values in llm_results.items():
        df[col] = values

    output_path = PROCESSED_DIR / output_filename
    df.to_csv(output_path, index=False)

    logger.info("LLM-enriched calls saved to: %s", output_path)
    logger.info("Total tokens used: %d", int(df["total_tokens"].sum()))

    return output_path
