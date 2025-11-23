from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_AUDIO_DIR = DATA_DIR / "raw" / "audios_llamadas"
PROCESSED_DIR = DATA_DIR / "processed"
TRANSCRIPTS_CSV = PROCESSED_DIR / "call_transcripts.csv"
CLEANED_TRANSCRIPTS_CSV = PROCESSED_DIR / "cleaned_transcripts.csv"
