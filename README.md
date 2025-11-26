# Proyecto de Análisis de Audios y Exploración Técnica

Este repositorio contiene un pipeline para procesar audios de llamadas, transcribirlos mediante Whisper, y generar un conjunto de datos limpio para análisis exploratorio, visualizaciones y posteriores modelos de NLP.

Para que la transcripción funcione correctamente, es necesario instalar FFmpeg. A continuación se muestran las instrucciones completas.

---

# Instalación de FFmpeg

Whisper depende de FFmpeg para poder cargar, decodificar y procesar archivos de audio. Si FFmpeg no está instalado, la transcripción fallará con errores como:
`FileNotFoundError: [WinError 2] The system cannot find the file specified`.

A continuación se detallan los pasos de instalación en Windows y macOS.

---

# Windows — Instalación de FFmpeg

Importante: abrir PowerShell en modo Administrador.
(Clic derecho sobre PowerShell → "Run as Administrator").

1. Ejecutar el siguiente comando para instalar FFmpeg usando winget:

```powershell
winget install --id Gyan.FFmpeg.Essentials -e
```

2. Cerrar completamente PowerShell.

3. Abrir una nueva ventana de PowerShell (esta ya no necesita modo administrador).

4. Verificar si FFmpeg fue instalado correctamente ejecutando:

```powershell
ffmpeg -version
```

Si el comando devuelve información similar a:

```
ffmpeg version 8.x.x ...
```

entonces FFmpeg está instalado correctamente y Whisper podrá transcribir audios sin errores.

---

# macOS — Instalación de FFmpeg

Requiere tener Homebrew instalado.
Si no tienes Homebrew: https://brew.sh

1. Instalar FFmpeg con:

```bash
brew install ffmpeg
```

2. Verificar la instalación:

```bash
ffmpeg -version
```

Si aparece algo como:

```
ffmpeg version 6.x.x ...
```

entonces FFmpeg está instalado correctamente.

---

# Verificación manual

Ejecutar:

```bash
ffmpeg -version
```

Si el sistema reconoce el comando y muestra la versión instalada, Whisper ya puede cargar y procesar los archivos de audio.

---

# Estructura del proyecto

```
project/
│
├── data/
│   ├── raw/
│   │   └── audios_llamadas/
│   └── processed/
│       └── transcripts.csv
│
├── notebooks/
│   └── 01_eda_calls.ipynb
│
├── src/
│   ├── config.py
│   └── data_processing/
│       ├── audio_transcription.py
│       ├── text_cleaning.py
│       ├── run_processing.py
│       └── utils.py
│
├── main.py
├── requirements.txt
└── README.md
```

---

# Instalación de dependencias del proyecto

Crear un entorno virtual:

```bash
python -m venv .venv
```

Activarlo:

Windows:
```powershell
.venv\Scripts\activate
```

macOS / Linux:
```bash
source .venv/bin/activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

---

# Ejecución del pipeline

Para procesar los audios y generar las transcripciones ejecutar:

```bash
python main.py
```

El archivo final se guardará en:

```
data/processed/transcripts.csv
```

---

# Contacto

Este repositorio está diseñado como una base para exploración técnica de valor a partir de audios.
Para consultas adicionales se pueden revisar los módulos en `src/` o los notebooks en la carpeta `notebooks/`.
