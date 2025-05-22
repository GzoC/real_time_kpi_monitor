"""Script para probar el cálculo de KPIs."""
from datetime import datetime, timedelta
from src.processing.kpi_engine import KPIEngine

def test_kpis():
    """Prueba el cálculo de KPIs con datos de los últimos 5 minutos."""
    engine = KPIEngine()
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=5)
    
    print("\nCalculando KPIs para los últimos 5 minutos...")
    print(f"Periodo: {start_time} a {end_time}")
    
    oee = engine.calculate_oee(start_time, end_time)
    print(f"\nOEE calculado: {oee:.2%}")
    
if __name__ == "__main__":
    test_kpis()
