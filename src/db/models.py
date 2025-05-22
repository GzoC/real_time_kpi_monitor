"""Database models for the KPI monitor."""
from sqlalchemy import Column, Integer, Float, String, TIMESTAMP, text
from datetime import datetime

from .database import Base

class SensorReading(Base):
    __tablename__ = "sensor_readings"

    time = Column(TIMESTAMP(timezone=True), primary_key=True, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    sensor_id = Column(String, primary_key=True, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    
class KPIValue(Base):
    __tablename__ = "kpi_values"
    
    time = Column(TIMESTAMP(timezone=True), primary_key=True, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    kpi_name = Column(String, primary_key=True, nullable=False)
    value = Column(Float, nullable=False)
    status = Column(String, nullable=False)  # 'normal', 'warning', 'critical'

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    kpi_name = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # 'warning', 'critical'
    message = Column(String, nullable=False)
    acknowledged = Column(Integer, nullable=False, default=0)  # 0=no, 1=yes
