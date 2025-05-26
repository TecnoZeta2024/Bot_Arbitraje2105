import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
    Configura el sistema de logging para la aplicación.
    Los logs se escribirán en un archivo rotatorio y en la consola.
    """
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "mcp_server.log")

    # Configuración del logger principal
    logger = logging.getLogger("mcp_server")
    logger.setLevel(logging.INFO) # Nivel de logging por defecto

    # Formato del log
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Handler para archivo rotatorio
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Configurar logging para librerías de terceros (opcional)
    logging.getLogger("uvicorn").handlers = [file_handler, console_handler]
    logging.getLogger("uvicorn.access").handlers = [file_handler, console_handler]
    logging.getLogger("fastapi").handlers = [file_handler, console_handler]

    logger.info("Sistema de logging configurado.")

if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger("mcp_server")
    logger.debug("Este es un mensaje de depuración.")
    logger.info("Este es un mensaje de información.")
    logger.warning("Este es un mensaje de advertencia.")
    logger.error("Este es un mensaje de error.")
    logger.critical("Este es un mensaje crítico.")
