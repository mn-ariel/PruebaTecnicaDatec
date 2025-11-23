import logging

from src.data_processing.run_processing import run_processing


def configure_logging() -> None:
    """
    Configura el sistema de logging para toda la aplicación.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


if __name__ == "__main__":
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Iniciando pipeline de procesamiento de datos...")
    run_processing()
    logger.info("Pipeline finalizado.")
