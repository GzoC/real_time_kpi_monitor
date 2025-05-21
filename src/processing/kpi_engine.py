"""KPI calculation engine."""
from loguru import logger
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import func

from ..db.database import SessionLocal
from ..db.models import SensorReading, KPIValue

class KPIEngine:
    def __init__(self):
        self.db = SessionLocal()
        
    def calculate_oee(self, start_time: datetime, end_time: datetime) -> float:
        """Calculate Overall Equipment Effectiveness (OEE)."""
        try:
            # Get relevant sensor readings
            availability = self._calculate_availability(start_time, end_time)
            performance = self._calculate_performance(start_time, end_time)
            quality = self._calculate_quality(start_time, end_time)
            
            oee = availability * performance * quality
            
            # Save KPI value
            kpi = KPIValue(
                kpi_name="OEE",
                value=oee,
                timestamp=end_time,
                status=self._get_status(oee, 0.85, 0.75)  # thresholds
            )
            
            self.db.add(kpi)
            self.db.commit()
            
            return oee
            
        except Exception as e:
            logger.error(f"Error calculating OEE: {str(e)}")
            return 0.0
            
    def _calculate_availability(self, start_time: datetime, end_time: datetime) -> float:
        """Calculate availability component of OEE."""
        # Example implementation
        return 0.95
        
    def _calculate_performance(self, start_time: datetime, end_time: datetime) -> float:
        """Calculate performance component of OEE."""
        # Example implementation
        return 0.90
        
    def _calculate_quality(self, start_time: datetime, end_time: datetime) -> float:
        """Calculate quality component of OEE."""
        # Example implementation
        return 0.98
        
    def _get_status(self, value: float, warning_threshold: float, critical_threshold: float) -> str:
        """Determine KPI status based on thresholds."""
        if value >= warning_threshold:
            return "normal"
        elif value >= critical_threshold:
            return "warning"
        else:
            return "critical"
