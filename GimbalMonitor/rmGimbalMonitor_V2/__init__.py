"""
__init__.py for rmGimbalMonitor_V2
Executes before all main files.
"""
from maya import cmds
from .logger_setup import setupLogger

logger = setupLogger(__name__)

logger.info(f"Log file created, {cmds.about(ctime=True)}")
logger.info(f"Maya version: {cmds.about(installedVersion=True)}")
logger.info(f"Qt version: {cmds.about(qtVersion=True)}")
logger.info(f"Connection to the Internet: {cmds.about(connected=True)}")
logger.info(f"Operating System: {cmds.about(operatingSystem=True)}")
