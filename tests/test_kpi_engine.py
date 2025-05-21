"""Test KPI calculation engine."""
import pytest
from datetime import datetime, timedelta
from src.processing.kpi_engine import KPIEngine
from src.db.models import SensorReading, KPIValue

def test_oee_calculation(test_db):
    """Test OEE calculation."""
    # Create test data
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)
    
    # Initialize KPI engine
    engine = KPIEngine()
    engine.db = test_db
    
    # Calculate OEE
    oee = engine.calculate_oee(start_time, end_time)
    
    # Basic validation
    assert isinstance(oee, float)
    assert 0 <= oee <= 1
    
    # Check if KPI value was saved
    kpi = test_db.query(KPIValue).filter(KPIValue.kpi_name == "OEE").first()
    assert kpi is not None
    assert kpi.value == oee
