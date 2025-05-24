"""FastAPI service for handling alerts."""
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text, update
from typing import List
from pydantic import BaseModel, ConfigDict
from datetime import datetime, UTC

from ..db.database import SessionLocal
from ..db.models import Alert, KPIValue

app = FastAPI(title="KPI Monitor Alert Service")

class AlertCreate(BaseModel):
    kpi_name: str
    severity: str
    message: str

class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    kpi_name: str
    severity: str
    message: str
    time: datetime
    acknowledged: int

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/alerts/", response_model=AlertResponse)
async def create_alert(alert: AlertCreate, db: Session = Depends(get_db)):
    """Create a new alert."""
    db_alert = Alert(
        kpi_name=alert.kpi_name,
        severity=alert.severity,
        message=alert.message,
        time=datetime.now(UTC),
        acknowledged=0
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert

@app.get("/alerts/", response_model=List[AlertResponse])
async def get_alerts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all alerts."""
    alerts = db.query(Alert).offset(skip).limit(limit).all()
    return alerts

@app.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Acknowledge an alert."""
    try:
        # Obtener la alerta primero para asegurar que existe
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
            
        # Actualizar el campo acknowledged
        alert.acknowledged = 1
        
        # Commitar la transacción
        db.commit()
        db.refresh(alert)
        
        return {"message": "Alert acknowledged", "alert_id": alert_id}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error acknowledging alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
