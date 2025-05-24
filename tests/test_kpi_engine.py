"""Test KPI calculation engine."""
import pytest
from datetime import datetime, timedelta, UTC
from src.processing.kpi_engine import KPIEngine
from src.db.models import SensorReading, KPIValue

def test_oee_calculation(test_db):
    """Test OEE calculation."""
    # Create test data
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=1)
    
    # Crear lecturas de prueba para el periodo
    readings = [
        # Estado de la máquina (1 = corriendo, 0 = detenida)
        SensorReading(
            time=start_time + timedelta(minutes=i),
            sensor_id="STATUS001",
            value=1 if i < 45 else 0,  # 75% disponibilidad
            unit="status"
        ) for i in range(60)
    ] + [
        # Velocidad de producción (90% rendimiento)
        SensorReading(
            time=start_time + timedelta(minutes=i),
            sensor_id="SPEED001",
            value=90.0,
            unit="units/hour"
        ) for i in range(60)
    ] + [
        # Calidad del producto (98% calidad)
        SensorReading(
            time=start_time + timedelta(minutes=i),
            sensor_id="QUALITY001",
            value=0.98,
            unit="ratio"
        ) for i in range(60)
    ]
    
    # Agregar datos a la base de datos
    for reading in readings:
        test_db.add(reading)
    test_db.commit()
    
    # Initialize KPI engine
    engine = KPIEngine()
    engine.db = test_db
    
    # Calculate OEE
    oee = engine.calculate_oee(start_time, end_time)
    
    # Basic validation
    assert isinstance(oee, float)
    assert 0 <= oee <= 1
    
    # El OEE esperado es aproximadamente: 0.75 * 0.90 * 0.98 = 0.66 (66%)
    assert 0.65 <= oee <= 0.67
    
    # Check if KPI value was saved
    kpi = test_db.query(KPIValue).filter(KPIValue.kpi_name == "OEE").first()
    assert kpi is not None
    assert kpi.value == oee
    assert kpi.status in ["normal", "warning", "critical"]
