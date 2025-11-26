import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from src.config import PROCESSED_DIR

logger = logging.getLogger(__name__)


def _compute_priority(sentiment, call_type) -> str:
    if not isinstance(sentiment, str):
        sentiment = ""
    if not isinstance(call_type, str):
        call_type = ""

    sentiment = sentiment.lower()
    call_type = call_type.lower()

    if sentiment == "negative" and call_type == "complaint":
        return "high"
    if sentiment in {"negative", "neutral"} and call_type in {"complaint", "support"}:
        return "medium"
    return "low"


def generate_call_analytics(
    enriched_path: Optional[Path] = None,
    summary_filename: str = "calls_analytics_summary.csv",
    prioritized_filename: str = "calls_prioritized.csv",
) -> tuple[Path, Path]:
    """
    Lee el CSV enriquecido por LLM, genera métricas agregadas y una tabla
    priorizada de llamadas.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    source = (
        enriched_path
        if enriched_path is not None
        else PROCESSED_DIR / "calls_enriched_llm.csv"
    )

    if not Path(source).exists():
        msg = f"LLM-enriched file not found: {source}"
        logger.error(msg)
        raise FileNotFoundError(msg)

    logger.info("Loading LLM-enriched calls from: %s", source)
    df = pd.read_csv(source)

    required_cols = {"sentiment", "call_type", "summary"}
    missing = required_cols - set(df.columns)
    if missing:
        msg = f"Missing required columns in enriched data: {missing}"
        logger.error(msg)
        raise ValueError(msg)

    # Definir prioridad por llamada
    logger.info("Computing priority for each call...")
    df["priority"] = [
        _compute_priority(s, t)
        for s, t in zip(df["sentiment"], df["call_type"])
    ]

    # KPIs A NIVEL GLOBAL
    global_rows: list[dict] = []
    if "duration_seconds" in df.columns:
        avg_duration = df["duration_seconds"].mean()
        global_rows.append(
            {
                "metric": "global",
                "category": "avg_duration_seconds",
                "count": len(df),
                "percentage": round(float(avg_duration), 2),  
            }
        )

    if "sentiment_start" in df.columns and "sentiment_end" in df.columns:
        improved = (df["sentiment_start"] == "negative") & (
            df["sentiment_end"].isin(["neutral", "positive"])
        )
        worsened = (df["sentiment_start"].isin(["neutral", "positive"])) & (
            df["sentiment_end"] == "negative"
        )

        improved_rate = improved.mean() * 100
        worsened_rate = worsened.mean() * 100

        global_rows.append(
            {
                "metric": "sentiment_flow",
                "category": "negative_to_neutral_or_positive",
                "count": int(improved.sum()),
                "percentage": round(float(improved_rate), 2),
            }
        )

        global_rows.append(
            {
                "metric": "sentiment_flow",
                "category": "neutral_or_positive_to_negative",
                "count": int(worsened.sum()),
                "percentage": round(float(worsened_rate), 2),
            }
        )

    # % llamadas con frases de riesgo
    if "has_risk_phrases" in df.columns:
        risky = df["has_risk_phrases"] == True  # noqa: E712
        risky_rate = risky.mean() * 100
        global_rows.append(
            {
                "metric": "risk_phrases",
                "category": "calls_with_risk_phrases",
                "count": int(risky.sum()),
                "percentage": round(float(risky_rate), 2),
            }
        )

    # complejidad promedio
    if "complexity_score" in df.columns:
        avg_complexity = df["complexity_score"].mean()
        global_rows.append(
            {
                "metric": "global",
                "category": "avg_complexity_score",
                "count": len(df),
                "percentage": round(float(avg_complexity), 2),
            }
        )

    # metricas agregadas clásicas
    logger.info("Computing aggregate analytics...")

    sentiment_counts = df["sentiment"].value_counts(dropna=False)
    call_type_counts = df["call_type"].value_counts(dropna=False)
    priority_counts = df["priority"].value_counts(dropna=False)

    sentiment_pct = (sentiment_counts / len(df) * 100).round(2)
    call_type_pct = (call_type_counts / len(df) * 100).round(2)
    priority_pct = (priority_counts / len(df) * 100).round(2)

    # tabla cruzada sentimiento x tipo de llamada
    crosstab = pd.crosstab(df["sentiment"], df["call_type"])

    # armar un unico DataFrame resumen “plano”
    summary_rows: list[dict] = []

    summary_rows.extend(global_rows)

    for sentiment, count in sentiment_counts.items():
        summary_rows.append(
            {
                "metric": "sentiment",
                "category": sentiment,
                "count": int(count),
                "percentage": float(sentiment_pct[sentiment]),
            }
        )

    for ctype, count in call_type_counts.items():
        summary_rows.append(
            {
                "metric": "call_type",
                "category": ctype,
                "count": int(count),
                "percentage": float(call_type_pct[ctype]),
            }
        )

    for prio, count in priority_counts.items():
        summary_rows.append(
            {
                "metric": "priority",
                "category": prio,
                "count": int(count),
                "percentage": float(priority_pct[prio]),
            }
        )

    # añadir info de la tabla cruzada
    for sentiment in crosstab.index:
        for ctype in crosstab.columns:
            summary_rows.append(
                {
                    "metric": "sentiment_x_call_type",
                    "category": f"{sentiment}__{ctype}",
                    "count": int(crosstab.loc[sentiment, ctype]),
                    "percentage": float(
                        (crosstab.loc[sentiment, ctype] / len(df) * 100).round(2)
                    ),
                }
            )

    summary_df = pd.DataFrame(summary_rows)

    # outputs
    summary_path = PROCESSED_DIR / summary_filename
    prioritized_path = PROCESSED_DIR / prioritized_filename

    summary_df.to_csv(summary_path, index=False)
    df.to_csv(prioritized_path, index=False)

    logger.info("Analytics summary saved to: %s", summary_path)
    logger.info("Prioritized calls saved to: %s", prioritized_path)

    return summary_path, prioritized_path
