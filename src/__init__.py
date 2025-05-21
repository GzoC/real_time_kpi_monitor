"""
Real-time KPI Monitor - Main package initialization
"""
from loguru import logger
import os

# Configure logger
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logger.add("logs/kpi_monitor.log", rotation="500 MB", level=LOG_LEVEL)
