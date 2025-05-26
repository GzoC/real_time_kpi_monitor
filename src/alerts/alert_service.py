"""FastAPI service for handling alerts."""
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text, update
from typing import List
from pydantic import BaseModel, ConfigDict
from datetime import datetime, timezone # Changed UTC import

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
        time=datetime.now(timezone.utc), # Changed UTC to timezone.utc
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
        # Use ORM to update the alert
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert.acknowledged = 1
        db.add(alert) # Add to session before commit, though for update it might not be strictly needed if already persistent
        db.commit()
        db.refresh(alert) # Refresh to get the updated state from DB
            
        return {"message": "Alert acknowledged", "alert_id": alert_id, "acknowledged_status": alert.acknowledged}
        
    except HTTPException: # Re-raise HTTPException instances directly
        raise
    except Exception as e:
        db.rollback()
        # Log the error for debugging: logger.error(f"Unhandled error in acknowledge_alert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
