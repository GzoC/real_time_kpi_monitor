"""Database models for the KPI monitor."""
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base

class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, index=True)
    value = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    unit = Column(String)
    
class KPIValue(Base):
    __tablename__ = "kpi_values"
    
    id = Column(Integer, primary_key=True, index=True)
    kpi_name = Column(String, index=True)
    value = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String)  # 'normal', 'warning', 'critical'

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    kpi_id = Column(Integer, ForeignKey("kpi_values.id"))
    severity = Column(String)  # 'warning', 'critical'
    message = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    acknowledged = Column(Integer, default=0)  # 0=no, 1=yes
    
    kpi = relationship("KPIValue")
