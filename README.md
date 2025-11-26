# Proyecto de Analisis de Audios y Exploracion Tecnica

Este repositorio contiene un pipeline completo para procesar audios de llamadas, transcribirlos con Whisper, limpiar el texto, enriquecer las llamadas con un modelo LLM, y generar un dataset final para analisis, dashboards y pruebas con modelos NLP.

El flujo completo se ejecuta desde `main.py`.

---

# Instalacion de FFmpeg

Whisper necesita FFmpeg para decodificar audios.  
Si FFmpeg no esta instalado, la transcripcion fallara.

## Windows

Abrir PowerShell como Administrador.

Instalar FFmpeg:

```powershell
winget install --id Gyan.FFmpeg.Essentials -e
```

Verificar:

```powershell
ffmpeg -version
```

## macOS

Se requiere Homebrew (https://brew.sh)

Instalar FFmpeg:

```bash
brew install ffmpeg
```

Verificar:

```bash
ffmpeg -version
```

---

# Crear entorno virtual

Cada usuario debe crear su propio entorno.

```bash
python -m venv .venv
```

Activar:

Windows:

```powershell
.venv\Scripts\activate
```

macOS / Linux:

```bash
source .venv/bin/activate
```

---

# Instalar dependencias

```bash
pip install -r requirements.txt
```

---

# Archivo .env

Crear un archivo `.env` en la raiz del proyecto:

```
OPENAI_API_KEY=tu_api_key_aqui
```

La clave de API sera enviada por correo.  
Cada usuario debe colocarla manualmente.

---

# Estructura del proyecto

```
project/
│
├── data/
│   ├── raw/
│   │   └── audios_llamadas/
│   └── processed/
│       ├── transcripts_clean.csv
│       ├── calls_enriched_llm.csv
│       ├── calls_analytics_summary.csv
│       └── calls_prioritized.csv
│
├── dashboard/
│   └── call_dashboard.py
│
├── notebooks/
│   └── 01_eda_calls.ipynb
│
├── src/
│   ├── config.py
│   ├── data_processing/
│   │   ├── audio_transcription.py
│   │   ├── text_cleaning.py
│   │   ├── llm_enrichment.py
│   │   ├── run_processing.py
│   │   └── utils.py
│   ├── reporting/
│   │   └── call_analytics.py
│
├── main.py
├── requirements.txt
└── README.md
```

---

# Flujo del pipeline

El pipeline consiste en 3 etapas principales:

## 1. Transcripcion y limpieza
Procesa los audios de `data/raw/audios_llamadas`, transcribe con Whisper, limpia el texto y genera `transcripts_clean.csv`.

## 2. Enriquecimiento con LLM
El modelo LLM genera:
- sentiment  
- sentiment_start  
- sentiment_end  
- call_type  
- summary  
- risk_phrases  
- has_risk_phrases  
- complexity_score  
- total_tokens  

Salida: `calls_enriched_llm.csv`

## 3. Analitica y priorizacion
Conteos de sentimiento, flujo emocional, riesgo, complejidad y priorizacion.

Salida:
- `calls_analytics_summary.csv`
- `calls_prioritized.csv`

---

# Correr el pipeline

```bash
python main.py
```

---

# Dashboard interactivo

```bash
streamlit run dashboard/call_dashboard.py
```

Incluye:
- Distribuciones de sentimiento, tipo y prioridad  
- Mapa de calor  
- Complejidad  
- Tokens  
- Llamadas con riesgo  
- Top llamadas complejas  
- Tabla filtrada  

---

# Notas finales

- Cada usuario debe usar su propio API key en `.env`
- El pipeline es modular y ampliable
