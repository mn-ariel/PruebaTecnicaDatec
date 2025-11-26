import sys
from pathlib import Path
from typing import Tuple

import altair as alt
import pandas as pd
import streamlit as st

# Rutas y carga de datos
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from src.config import PROCESSED_DIR  # noqa: E402


@st.cache_data
def load_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    calls_path = PROCESSED_DIR / "calls_prioritized.csv"
    summary_path = PROCESSED_DIR / "calls_analytics_summary.csv"

    df_calls = pd.read_csv(calls_path)
    df_summary = pd.read_csv(summary_path)

    return df_calls, df_summary


# Helpers
def _to_bool_series(series: pd.Series) -> pd.Series:
    """Convierte una columna a booleano de forma robusta."""
    if series.dtype == bool:
        return series
    return series.astype(str).str.lower().isin(["true", "1", "yes"])


def main() -> None:
    st.set_page_config(
        page_title="Dashboard de análisis de llamadas",
        layout="wide",
    )

    st.title("Dashboard de análisis de llamadas de Call Center")

    df_calls, df_summary = load_data()

    # Asegurar tipos básicos
    if "has_risk_phrases" in df_calls.columns:
        df_calls["has_risk_phrases"] = _to_bool_series(df_calls["has_risk_phrases"])

    # SIDEBAR – Filtros globales
    st.sidebar.header("Filtros")

    # Filtro por sentimiento
    sentiments = sorted(df_calls["sentiment"].dropna().unique().tolist())
    selected_sentiments = st.sidebar.multiselect(
        "Sentimiento",
        options=sentiments,
        default=sentiments,
    )

    # Filtro por tipo de llamada
    call_types = sorted(df_calls["call_type"].dropna().unique().tolist())
    selected_call_types = st.sidebar.multiselect(
        "Tipo de llamada",
        options=call_types,
        default=call_types,
    )

    # Filtro por prioridad
    priorities = sorted(df_calls["priority"].dropna().unique().tolist())
    selected_priorities = st.sidebar.multiselect(
        "Prioridad",
        options=priorities,
        default=priorities,
    )

    # Filtro: solo llamadas con frases de riesgo
    only_risky = False
    if "has_risk_phrases" in df_calls.columns:
        only_risky = st.sidebar.checkbox(
            "Solo llamadas con frases de riesgo", value=False
        )

    # Filtro de complejidad
    complexity_min = complexity_max = None
    if (
        "complexity_score" in df_calls.columns
        and df_calls["complexity_score"].notna().any()
    ):
        min_c = int(df_calls["complexity_score"].min())
        max_c = int(df_calls["complexity_score"].max())
        complexity_min, complexity_max = st.sidebar.slider(
            "Rango de puntaje de complejidad",
            min_value=min_c,
            max_value=max_c,
            value=(min_c, max_c),
        )

    # Aplicar filtros
    df_filtered = df_calls.copy()

    if selected_sentiments:
        df_filtered = df_filtered[df_filtered["sentiment"].isin(selected_sentiments)]

    if selected_call_types:
        df_filtered = df_filtered[df_filtered["call_type"].isin(selected_call_types)]

    if selected_priorities:
        df_filtered = df_filtered[df_filtered["priority"].isin(selected_priorities)]

    if only_risky and "has_risk_phrases" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["has_risk_phrases"]]

    if (
        complexity_min is not None
        and complexity_max is not None
        and "complexity_score" in df_filtered.columns
    ):
        df_filtered = df_filtered[
            (df_filtered["complexity_score"] >= complexity_min)
            & (df_filtered["complexity_score"] <= complexity_max)
        ]

    st.caption(f"{len(df_filtered)} llamadas después de aplicar filtros")

    # KPIs basicos y avanzados
    total_calls = len(df_filtered)
    high_priority = (df_filtered["priority"] == "high").sum()
    negative_complaints = (
        (df_filtered["sentiment"] == "negative")
        & (df_filtered["call_type"] == "complaint")
    ).sum()

    avg_duration_min = None
    if (
        "duration_seconds" in df_filtered.columns
        and df_filtered["duration_seconds"].notna().any()
    ):
        avg_duration_min = df_filtered["duration_seconds"].mean() / 60

    risk_rate = None
    if "has_risk_phrases" in df_filtered.columns and total_calls > 0:
        risk_rate = df_filtered["has_risk_phrases"].mean() * 100

    improved_rate = worsened_rate = None
    if {"sentiment_start", "sentiment_end"}.issubset(df_filtered.columns) and total_calls > 0:
        improved = (df_filtered["sentiment_start"] == "negative") & (
            df_filtered["sentiment_end"].isin(["neutral", "positive"])
        )
        worsened = (df_filtered["sentiment_start"].isin(["neutral", "positive"])) & (
            df_filtered["sentiment_end"] == "negative"
        )
        improved_rate = improved.mean() * 100
        worsened_rate = worsened.mean() * 100

    avg_complexity = None
    if (
        "complexity_score" in df_filtered.columns
        and df_filtered["complexity_score"].notna().any()
    ):
        avg_complexity = df_filtered["complexity_score"].mean()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de llamadas", total_calls)
    col2.metric("Llamadas de alta prioridad", int(high_priority))
    col3.metric("Reclamos negativos", int(negative_complaints))

    col4, col5, col6 = st.columns(3)
    col4.metric(
        "Duración promedio (min)",
        f"{avg_duration_min:.1f}" if avg_duration_min is not None else "N/A",
    )
    col5.metric(
        "% de llamadas con frases de riesgo",
        f"{risk_rate:.1f}%" if risk_rate is not None else "N/A",
    )
    col6.metric(
        "Mejora vs empeora",
        f"{improved_rate:.1f}% / {worsened_rate:.1f}%"
        if improved_rate is not None and worsened_rate is not None
        else "N/A",
    )

    st.markdown("---")

    # Distribuciones básicas – 3 gráficas en una fila
    st.subheader("Distribuciones básicas")

    col_a, col_b, col_c = st.columns(3)

    # Distribución de sentimiento
    with col_a:
        st.markdown("**Distribución de sentimiento**")
        if total_calls > 0:
            sentiment_counts = (
                df_filtered["sentiment"]
                .fillna("null")
                .value_counts()
                .reset_index()
            )
            sentiment_counts.columns = ["sentiment", "n_calls"]

            chart_sentiment = (
                alt.Chart(sentiment_counts, width=260, height=220)
                .mark_bar()
                .encode(
                    x=alt.X("sentiment:N", title="Sentimiento"),
                    y=alt.Y("n_calls:Q", title="Cantidad"),
                    tooltip=["sentiment", "n_calls"],
                )
            )
            st.altair_chart(chart_sentiment, use_container_width=True)
        else:
            st.info("No hay datos para la distribución de sentimiento.")

    # Distribución por tipo de llamada
    with col_b:
        st.markdown("**Distribución por tipo de llamada**")
        if total_calls > 0:
            call_type_counts = (
                df_filtered["call_type"]
                .fillna("null")
                .value_counts()
                .reset_index()
            )
            call_type_counts.columns = ["call_type", "n_calls"]

            chart_ct = (
                alt.Chart(call_type_counts, width=260, height=220)
                .mark_bar()
                .encode(
                    x=alt.X("call_type:N", title="Tipo de llamada"),
                    y=alt.Y("n_calls:Q", title="Cantidad"),
                    tooltip=["call_type", "n_calls"],
                )
            )
            st.altair_chart(chart_ct, use_container_width=True)
        else:
            st.info("No hay datos para tipos de llamada.")

    # Distribución de prioridad
    with col_c:
        st.markdown("**Distribución de prioridad**")
        if total_calls > 0:
            priority_counts = (
                df_filtered["priority"]
                .fillna("null")
                .value_counts()
                .reset_index()
            )
            priority_counts.columns = ["priority", "n_calls"]

            chart_prio = (
                alt.Chart(priority_counts, width=260, height=220)
                .mark_bar()
                .encode(
                    x=alt.X("priority:N", title="Prioridad"),
                    y=alt.Y("n_calls:Q", title="Cantidad"),
                    tooltip=["priority", "n_calls"],
                )
            )
            st.altair_chart(chart_prio, use_container_width=True)
        else:
            st.info("No hay datos para prioridades.")

    st.markdown("---")

    # Heatmap Sentiment × Call type
    st.subheader("Mapa de calor: Sentimiento vs Tipo de llamada")

    if total_calls > 0:
        pivot = (
            df_filtered.pivot_table(
                index="sentiment",
                columns="call_type",
                values="summary",
                aggfunc="count",
                fill_value=0,
            )
            .reset_index()
            .melt(id_vars="sentiment", var_name="call_type", value_name="count")
        )

        col_left, col_center, col_right = st.columns([1, 2, 1])

        with col_center:
            heatmap = (
                alt.Chart(pivot, width=410, height=370)   
                .mark_rect()
                .encode(
                    x=alt.X("call_type:N", title="Tipo de llamada"),
                    y=alt.Y("sentiment:N", title="Sentimiento"),
                    color=alt.Color("count:Q", title="Cantidad", scale=alt.Scale(scheme="blues")),
                    tooltip=["sentiment", "call_type", "count"],
                )
            )

            st.altair_chart(heatmap, use_container_width=False)

    else:
        st.info("No hay datos para el mapa de calor con los filtros actuales.")


    st.markdown("---")

    # Complejidad y costo (tokens)
    st.subheader("Complejidad y costo (tokens)")

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.markdown("**Distribución del puntaje de complejidad**")
        if (
            "complexity_score" in df_filtered.columns
            and df_filtered["complexity_score"].notna().any()
        ):
            comp_counts = (
                df_filtered["complexity_score"]
                .value_counts()
                .reset_index()
            )
            comp_counts.columns = ["complexity_score", "n_calls"]

            comp_chart = (
                alt.Chart(comp_counts, width=320, height=220)
                .mark_bar()
                .encode(
                    x=alt.X("complexity_score:Q", title="Puntaje de complejidad"),
                    y=alt.Y("n_calls:Q", title="Cantidad"),
                    tooltip=["complexity_score", "n_calls"],
                )
            )
            st.altair_chart(comp_chart, use_container_width=True)
        else:
            st.info("No hay datos de puntaje de complejidad.")

    with col_c2:
        st.markdown("**Distribución de tokens totales**")
        if (
            "total_tokens" in df_filtered.columns
            and df_filtered["total_tokens"].notna().any()
        ):
            token_chart = (
                alt.Chart(df_filtered, width=320, height=220)
                .mark_bar()
                .encode(
                    x=alt.X(
                        "total_tokens:Q",
                        bin=alt.Bin(maxbins=20),
                        title="Tokens totales",
                    ),
                    y=alt.Y("count():Q", title="Cantidad"),
                    tooltip=[alt.Tooltip("count():Q", title="Llamadas")],
                )
            )
            st.altair_chart(token_chart, use_container_width=True)
        else:
            st.info("No hay datos de uso de tokens.")

    st.markdown("---")

    # Resumen global (df_summary)
    st.subheader("Resumen analítico global")

    key_metrics = df_summary[
        df_summary["metric"].isin(["global", "sentiment_flow", "risk_phrases"])
    ].copy()

    st.dataframe(key_metrics.reset_index(drop=True), use_container_width=True)

    st.markdown("---")

    # Llamadas más complejas y de mayor riesgo
    st.subheader("Llamadas destacadas")

    col_t1, col_t2 = st.columns(2)

    with col_t1:
        st.markdown("**Top 10 llamadas más complejas**")
        if (
            "complexity_score" in df_calls.columns
            and df_calls["complexity_score"].notna().any()
        ):
            top_complex = (
                df_calls.sort_values("complexity_score", ascending=False)
                .head(10)[
                    [
                        "file_name",
                        "sentiment",
                        "call_type",
                        "priority",
                        "complexity_score",
                        "summary",
                    ]
                ]
            )
            st.dataframe(top_complex.reset_index(drop=True), use_container_width=True)
        else:
            st.info("No hay datos de complejidad para ordenar llamadas.")

    with col_t2:
        st.markdown("**Llamadas con frases de riesgo**")
        if (
            "has_risk_phrases" in df_calls.columns
            and df_calls["has_risk_phrases"].any()
        ):
            risky_calls = df_calls[df_calls["has_risk_phrases"]].copy()
            risky_calls = risky_calls[
                [
                    "file_name",
                    "sentiment",
                    "call_type",
                    "priority",
                    "risk_phrases",
                    "summary",
                ]
            ]
            st.dataframe(risky_calls.reset_index(drop=True), use_container_width=True)
        else:
            st.info("No se detectaron llamadas con frases de riesgo.")

    st.markdown("---")

    # Detalle de llamadas filtradas
    st.subheader("Detalle de llamadas (con filtros aplicados)")

    if total_calls > 0:
        detail_cols = [
            "file_name",
            "sentiment",
            "call_type",
            "priority",
            "complexity_score",
            "has_risk_phrases",
            "summary",
        ]
        existing_cols = [c for c in detail_cols if c in df_filtered.columns]

        st.dataframe(
            df_filtered[existing_cols].reset_index(drop=True),
            use_container_width=True,
        )
    else:
        st.info("No hay llamadas con los filtros actuales.")


if __name__ == "__main__":
    main()
