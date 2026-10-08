"""
setup_logger.py
Logging system for the entire tool.
"""

import logging
from pathlib import Path

_LOG_DIR: Path = Path(__file__).parent / "Logs"
_LOG_PATH: Path = _LOG_DIR / "GimbalMonitor_LOG.log"

def setupLogger(name: str) -> logging.Logger:
    """
    Execute for all files from rmGimbalMonitor_V2 root folder.
    In each .py file has been set "logger = logging.getLogger(__name__)".
    Each .py file has its own logger.
    """
    if not _LOG_DIR.is_dir(): # Checking the log folder. If it doesn't exist, create the folder "Log".
        _LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False # Disables sending logs to the root logger (Maya's logger)

    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)

    fileHandler = logging.FileHandler(_LOG_PATH, mode="w")
    fileHandler.setLevel(logging.DEBUG) # TODO Зміни перед релізом
    fileHandlerFormatter = logging.Formatter("%(levelname)s: %(filename)s: %(message)s")
    # fileHandlerFormatter = logging.Formatter('%(levelname)s: %(filename)s: %(message)s %(asctime)s',
    #                               datefmt='%d/%m/%Y %H:%M:%S')
    fileHandler.setFormatter(fileHandlerFormatter)
    logger.addHandler(fileHandler)

    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(logging.WARNING) # TODO Зміни перед релізом
    streamHandlerFormatter = logging.Formatter("%(levelname)s: %(message)s")
    streamHandler.setFormatter(streamHandlerFormatter)
    logger.addHandler(streamHandler)

    return logger