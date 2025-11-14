from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from app import models, schemas

# Customer CRUD
def get_customer(db: Session, customer_id: int):
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()

def get_customer_by_single_id(db: Session, single_id: str):
    return db.query(models.Customer).filter(models.Customer.single_id == single_id).first()

def get_customers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Customer).offset(skip).limit(limit).all()

def create_customer(db: Session, customer: schemas.CustomerCreate):
    db_customer = models.Customer(**customer.dict())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

def search_customers(db: Session, query: str, skip: int = 0, limit: int = 100):
    return db.query(models.Customer).filter(
        (models.Customer.name.contains(query)) |
        (models.Customer.phone.contains(query)) |
        (models.Customer.single_id.contains(query))
    ).offset(skip).limit(limit).all()

# Vehicle CRUD
def get_vehicle(db: Session, vehicle_id: int):
    return db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()

def get_vehicle_by_no_rangka(db: Session, no_rangka: str):
    return db.query(models.Vehicle).filter(models.Vehicle.no_rangka == no_rangka).first()

def get_vehicles_by_customer(db: Session, customer_id: int):
    return db.query(models.Vehicle).filter(models.Vehicle.customer_id == customer_id).all()

def create_vehicle(db: Session, vehicle: schemas.VehicleCreate):
    db_vehicle = models.Vehicle(**vehicle.dict())
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

# Service History CRUD
def get_service_history(db: Session, vehicle_id: int, skip: int = 0, limit: int = 50):
    return db.query(models.ServiceHistory).filter(
        models.ServiceHistory.vehicle_id == vehicle_id
    ).order_by(desc(models.ServiceHistory.service_date)).offset(skip).limit(limit).all()

def get_last_service(db: Session, vehicle_id: int):
    return db.query(models.ServiceHistory).filter(
        models.ServiceHistory.vehicle_id == vehicle_id
    ).order_by(desc(models.ServiceHistory.service_date)).first()

def create_service_history(db: Session, service: schemas.ServiceHistoryCreate):
    db_service = models.ServiceHistory(**service.dict())
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

# Service Schedule CRUD
def get_service_schedule(db: Session, schedule_id: int):
    return db.query(models.ServiceSchedule).filter(models.ServiceSchedule.id == schedule_id).first()

def get_schedules_by_vehicle(db: Session, vehicle_id: int):
    return db.query(models.ServiceSchedule).filter(
        models.ServiceSchedule.vehicle_id == vehicle_id
    ).order_by(desc(models.ServiceSchedule.scheduled_date)).all()

def get_pending_schedules(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ServiceSchedule).filter(
        models.ServiceSchedule.status == "scheduled"
    ).order_by(models.ServiceSchedule.scheduled_date).offset(skip).limit(limit).all()

def create_service_schedule(db: Session, schedule: schemas.ServiceScheduleCreate):
    db_schedule = models.ServiceSchedule(**schedule.dict())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

def update_schedule_status(db: Session, schedule_id: int, status: str):
    db_schedule = get_service_schedule(db, schedule_id)
    if db_schedule:
        db_schedule.status = status
        db_schedule.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_schedule)
    return db_schedule

# Call History CRUD
def get_call_history(db: Session, call_id: int):
    return db.query(models.CallHistory).filter(models.CallHistory.id == call_id).first()

def get_calls_by_customer(db: Session, customer_id: int, skip: int = 0, limit: int = 50):
    return db.query(models.CallHistory).filter(
        models.CallHistory.customer_id == customer_id
    ).order_by(desc(models.CallHistory.created_at)).offset(skip).limit(limit).all()

def get_recent_calls(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.CallHistory).order_by(
        desc(models.CallHistory.created_at)
    ).offset(skip).limit(limit).all()

def create_call_history(db: Session, call: schemas.CallHistoryCreate, call_sid: str):
    db_call = models.CallHistory(
        **call.dict(),
        call_sid=call_sid,
        call_status="initiated"
    )
    db.add(db_call)
    db.commit()
    db.refresh(db_call)
    return db_call

def update_call_status(db: Session, call_sid: str, status: str, duration: int = 0):
    db_call = db.query(models.CallHistory).filter(models.CallHistory.call_sid == call_sid).first()
    if db_call:
        db_call.call_status = status
        db_call.call_duration = duration
        if status in ["completed", "failed", "no-answer", "busy"]:
            db_call.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(db_call)
    return db_call

def update_call_summary(db: Session, call_sid: str, summary: str, 
                       booking_confirmed: bool = False, needs_callback: bool = False):
    db_call = db.query(models.CallHistory).filter(models.CallHistory.call_sid == call_sid).first()
    if db_call:
        db_call.conversation_summary = summary
        db_call.booking_confirmed = booking_confirmed
        db_call.needs_callback = needs_callback
        db.commit()
        db.refresh(db_call)
    return db_call

# Analytics
def get_call_statistics(db: Session):
    total_calls = db.query(models.CallHistory).count()
    completed_calls = db.query(models.CallHistory).filter(
        models.CallHistory.call_status == "completed"
    ).count()
    confirmed_bookings = db.query(models.CallHistory).filter(
        models.CallHistory.booking_confirmed == True
    ).count()
    
    return {
        "total_calls": total_calls,
        "completed_calls": completed_calls,
        "confirmed_bookings": confirmed_bookings,
        "success_rate": (confirmed_bookings / total_calls * 100) if total_calls > 0 else 0
    }
