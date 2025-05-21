"""FastAPI service for handling alerts."""
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from ..db.database import SessionLocal
from ..db.models import Alert, KPIValue

app = FastAPI(title="KPI Monitor Alert Service")

class AlertCreate(BaseModel):
    kpi_id: int
    severity: str
    message: str

class AlertResponse(BaseModel):
    id: int
    kpi_id: int
    severity: str
    message: str
    timestamp: datetime
    acknowledged: int

    class Config:
        from_attributes = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/alerts/", response_model=AlertResponse)
async def create_alert(alert: AlertCreate, db: Session = Depends(get_db)):
    """Create a new alert."""
    db_alert = Alert(**alert.dict())
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
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.acknowledged = 1
    db.commit()
    return {"message": "Alert acknowledged"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
