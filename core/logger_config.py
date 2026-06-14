"""
Global logging configuration module.

Sets up the logging format and redirects log streams to both the console 
and rotating log files saved in a dedicated directory.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler


def setup_logging() -> None:
    """
    Configures the root logger with custom formatting, console output,
    and size-limited rotating log files.
    """
    # Create a logs directory in the root folder if it doesn't exist
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Define a clean, professional log format with line numbers
    log_format = (
        "[%(asctime)s] %(levelname)-8s [%(name)s:%(lineno)d] %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    # Set up RotatingFileHandler: 5MB max size per file, keep up to 3 backup files
    file_handler = RotatingFileHandler(
        filename=os.path.join(log_dir, "amosync.log"),
        maxBytes=5 * 1024 * 1024,  # 5 Megabytes
        backupCount=3,
        encoding="utf-8"
    )

    # Set up Console Handler
    console_handler = logging.StreamHandler(sys.stdout)

    # Configure the root logger
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[console_handler, file_handler]
    )

    # Suppress verbose logs from chatty libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)

    logging.info("Logging system successfully initialized in rotating files.")
