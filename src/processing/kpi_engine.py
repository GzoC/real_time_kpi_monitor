"""KPI calculation engine."""
from loguru import logger
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import func, and_

from ..db.database import SessionLocal
from ..db.models import SensorReading, KPIValue, Alert

class KPIEngine:
    def __init__(self):
        self.db = SessionLocal()
        # Configuración de umbrales para los KPIs
        self.thresholds = {
            "OEE": {"warning": 0.85, "critical": 0.75},
            "availability": {"warning": 0.90, "critical": 0.80},
            "performance": {"warning": 0.95, "critical": 0.85},
            "quality": {"warning": 0.98, "critical": 0.95}
        }
        
    def calculate_oee(self, start_time: datetime, end_time: datetime) -> float:
        """Calcula el Overall Equipment Effectiveness (OEE)."""
        try:
            # Calcula los componentes
            availability = self._calculate_availability(start_time, end_time)
            performance = self._calculate_performance(start_time, end_time)
            quality = self._calculate_quality(start_time, end_time)
            
            # OEE es el producto de sus tres componentes
            oee = availability * performance * quality
            
            # Guarda los valores de KPI individuales
            self._save_kpi_value("availability", availability, end_time)
            self._save_kpi_value("performance", performance, end_time)
            self._save_kpi_value("quality", quality, end_time)
            self._save_kpi_value("OEE", oee, end_time)
            
            # Verifica si necesitamos generar alertas
            self._check_and_create_alert("OEE", oee, end_time)
            
            return oee
            
        except Exception as e:
            logger.error(f"Error calculando OEE: {str(e)}")
            self._create_alert("error", "Error en cálculo de OEE", str(e))
            return 0.0

    def _calculate_availability(self, start_time: datetime, end_time: datetime) -> float:
        """Calcula el componente de disponibilidad del OEE."""
        try:            # Obtiene las lecturas del sensor de estado de la máquina
            running_count = self.db.query(func.count(SensorReading.time)).filter(
                and_(
                    SensorReading.sensor_id == "STATUS001",
                    SensorReading.time.between(start_time, end_time),
                    SensorReading.value >= 1
                )
            ).scalar() or 0
            
            total_count = self.db.query(func.count(SensorReading.time)).filter(
                and_(
                    SensorReading.sensor_id == "STATUS001",
                    SensorReading.time.between(start_time, end_time)
                )
            ).scalar() or 0
            
            if total_count == 0:
                return 1.0  # Si no hay datos, asumimos 100% disponibilidad
              # Calcula la disponibilidad basada en el tiempo de operación
            availability = running_count / total_count
            return min(max(availability, 0.0), 1.0)  # Limita entre 0 y 1
            
        except Exception as e:
            logger.error(f"Error calculando disponibilidad: {str(e)}")
            return 0.0

    def _calculate_performance(self, start_time: datetime, end_time: datetime) -> float:
        """Calcula el componente de rendimiento del OEE."""
        try:            # Obtiene la velocidad promedio del sensor
            avg_speed = self.db.query(func.avg(SensorReading.value)).filter(
                and_(
                    SensorReading.sensor_id == "SPEED001",
                    SensorReading.time.between(start_time, end_time)
                )
            ).scalar() or 0.0
            
            if avg_speed == 0.0:
                return 1.0  # Si no hay datos, asumimos 100% rendimiento
            
            # Velocidad ideal de la máquina (unidades/hora)
            ideal_speed = 100.0
            
            # Calcula el rendimiento basado en la velocidad real vs ideal
            performance = float(avg_speed) / ideal_speed
            return min(max(performance, 0.0), 1.0)  # Limita entre 0 y 1
            
        except Exception as e:
            logger.error(f"Error calculando rendimiento: {str(e)}")
            return 0.0

    def _calculate_quality(self, start_time: datetime, end_time: datetime) -> float:
        """Calcula el componente de calidad del OEE."""
        try:            # Obtiene el conteo de productos buenos y total
            good_products = self.db.query(func.count(SensorReading.time)).filter(
                and_(
                    SensorReading.sensor_id == "QUALITY001",
                    SensorReading.time.between(start_time, end_time),
                    SensorReading.value >= 0.95  # threshold de calidad
                )
            ).scalar() or 0
            
            total_products = self.db.query(func.count(SensorReading.time)).filter(
                and_(
                    SensorReading.sensor_id == "QUALITY001",
                    SensorReading.time.between(start_time, end_time)
                )
            ).scalar() or 0
            
            if total_products == 0:
                return 1.0  # Si no hay datos, asumimos 100% calidad
            
            # Calcula la tasa de calidad
            quality = float(good_products) / float(total_products)
            return min(max(quality, 0.0), 1.0)  # Limita entre 0 y 1
            
        except Exception as e:
            logger.error(f"Error calculando calidad: {str(e)}")
            return 0.0

    def _save_kpi_value(self, kpi_name: str, value: float, timestamp: datetime):
        """Guarda un valor de KPI en la base de datos."""
        try:
            status = self._get_status(value, 
                                    self.thresholds[kpi_name]["warning"],
                                    self.thresholds[kpi_name]["critical"])
            
            kpi = KPIValue(
                time=timestamp,
                kpi_name=kpi_name,
                value=value,
                status=status
            )
            
            self.db.add(kpi)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error guardando valor de KPI {kpi_name}: {str(e)}")
            self.db.rollback()

    def _get_status(self, value: float, warning_threshold: float, critical_threshold: float) -> str:
        """Determina el estado del KPI basado en umbrales."""
        if value >= warning_threshold:
            return "normal"
        elif value >= critical_threshold:
            return "warning"
        else:
            return "critical"

    def _check_and_create_alert(self, kpi_name: str, value: float, timestamp: datetime):
        """Verifica si se necesita crear una alerta basada en el valor del KPI."""
        status = self._get_status(value, 
                                self.thresholds[kpi_name]["warning"],
                                self.thresholds[kpi_name]["critical"])
        
        if status != "normal":
            severity = status
            message = f"KPI {kpi_name} en estado {status} (valor: {value:.2%})"
            self._create_alert(severity, kpi_name, message)

    def _create_alert(self, severity: str, kpi_name: str, message: str):
        """Crea una nueva alerta en la base de datos."""
        try:
            alert = Alert(
                time=datetime.utcnow(),
                kpi_name=kpi_name,
                severity=severity,
                message=message,
                acknowledged=0
            )
            
            self.db.add(alert)
            self.db.commit()
            logger.warning(f"Alerta creada: {message}")
            
        except Exception as e:
            logger.error(f"Error creando alerta: {str(e)}")
            self.db.rollback()
