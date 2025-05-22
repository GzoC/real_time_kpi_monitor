"""KPI Monitor package initialization."""
import sys
import os
from loguru import logger

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Configure logger
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logger.add("logs/kpi_monitor.log", rotation="500 MB", level=LOG_LEVEL)
