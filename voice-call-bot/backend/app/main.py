from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from dotenv import load_dotenv

from app import models, schemas, crud
from app.database import engine, get_db
from app.voice_agent import VoiceAgent

load_dotenv()

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Voice Call Bot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Voice Agent
voice_agent = VoiceAgent()

# Store conversation context (in production, use Redis or similar)
conversation_contexts = {}

@app.get("/")
def read_root():
    return {
        "message": "Voice Call Bot API",
        "version": "1.0.0",
        "status": "running"
    }

# Customer Endpoints
@app.get("/api/customers", response_model=List[schemas.Customer])
def list_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    customers = crud.get_customers(db, skip=skip, limit=limit)
    return customers

@app.get("/api/customers/search")
def search_customers(q: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    customers = crud.search_customers(db, query=q, skip=skip, limit=limit)
    return customers

@app.get("/api/customers/{customer_id}", response_model=schemas.Customer)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = crud.get_customer(db, customer_id=customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@app.post("/api/customers", response_model=schemas.Customer)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    db_customer = crud.get_customer_by_single_id(db, single_id=customer.single_id)
    if db_customer:
        raise HTTPException(status_code=400, detail="Customer already exists")
    return crud.create_customer(db, customer=customer)

# Vehicle Endpoints
@app.get("/api/vehicles/{vehicle_id}", response_model=schemas.Vehicle)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = crud.get_vehicle(db, vehicle_id=vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@app.get("/api/customers/{customer_id}/vehicles", response_model=List[schemas.Vehicle])
def get_customer_vehicles(customer_id: int, db: Session = Depends(get_db)):
    vehicles = crud.get_vehicles_by_customer(db, customer_id=customer_id)
    return vehicles

@app.post("/api/vehicles", response_model=schemas.Vehicle)
def create_vehicle(vehicle: schemas.VehicleCreate, db: Session = Depends(get_db)):
    db_vehicle = crud.get_vehicle_by_no_rangka(db, no_rangka=vehicle.no_rangka)
    if db_vehicle:
        raise HTTPException(status_code=400, detail="Vehicle already exists")
    return crud.create_vehicle(db, vehicle=vehicle)

# Service History Endpoints
@app.get("/api/vehicles/{vehicle_id}/service-history", response_model=List[schemas.ServiceHistory])
def get_vehicle_service_history(vehicle_id: int, skip: int = 0, limit: int = 50, 
                                db: Session = Depends(get_db)):
    history = crud.get_service_history(db, vehicle_id=vehicle_id, skip=skip, limit=limit)
    return history

@app.post("/api/service-history", response_model=schemas.ServiceHistory)
def create_service_history(service: schemas.ServiceHistoryCreate, db: Session = Depends(get_db)):
    return crud.create_service_history(db, service=service)

# Service Schedule Endpoints
@app.get("/api/schedules", response_model=List[schemas.ServiceSchedule])
def list_schedules(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    schedules = crud.get_pending_schedules(db, skip=skip, limit=limit)
    return schedules

@app.get("/api/vehicles/{vehicle_id}/schedules", response_model=List[schemas.ServiceSchedule])
def get_vehicle_schedules(vehicle_id: int, db: Session = Depends(get_db)):
    schedules = crud.get_schedules_by_vehicle(db, vehicle_id=vehicle_id)
    return schedules

@app.post("/api/schedules", response_model=schemas.ServiceSchedule)
def create_schedule(schedule: schemas.ServiceScheduleCreate, db: Session = Depends(get_db)):
    return crud.create_service_schedule(db, schedule=schedule)

@app.put("/api/schedules/{schedule_id}/status")
def update_schedule_status(schedule_id: int, status: str, db: Session = Depends(get_db)):
    schedule = crud.update_schedule_status(db, schedule_id=schedule_id, status=status)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule

# Call History Endpoints
@app.get("/api/calls", response_model=List[schemas.CallHistory])
def list_calls(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    calls = crud.get_recent_calls(db, skip=skip, limit=limit)
    return calls

@app.get("/api/customers/{customer_id}/calls", response_model=List[schemas.CallHistory])
def get_customer_calls(customer_id: int, skip: int = 0, limit: int = 50, 
                      db: Session = Depends(get_db)):
    calls = crud.get_calls_by_customer(db, customer_id=customer_id, skip=skip, limit=limit)
    return calls

# Voice Call Endpoints
@app.post("/api/calls/initiate", response_model=schemas.CallResponse)
def initiate_call(call_request: schemas.CallRequest, db: Session = Depends(get_db)):
    """
    Initiate outbound call to customer
    """
    # Get customer details
    customer = crud.get_customer(db, customer_id=call_request.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if not customer.phone:
        raise HTTPException(status_code=400, detail="Customer has no phone number")
    
    # Get customer's vehicle
    vehicles = crud.get_vehicles_by_customer(db, customer_id=customer.id)
    if not vehicles:
        raise HTTPException(status_code=400, detail="Customer has no vehicles")
    
    vehicle = vehicles[0]  # Use first vehicle
    
    # Get last service date
    last_service = crud.get_last_service(db, vehicle_id=vehicle.id)
    last_service_date = last_service.service_date.strftime("%d %B %Y") if last_service else "belum pernah"
    
    # Create call
    result = voice_agent.create_call(
        to_number=customer.phone,
        customer_name=customer.name,
        vehicle_model=vehicle.model,
        call_type=call_request.call_type,
        last_service_date=last_service_date
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to create call"))
    
    # Save call history
    call_history = schemas.CallHistoryCreate(
        customer_id=customer.id,
        schedule_id=call_request.schedule_id,
        phone_number=customer.phone,
        call_type=call_request.call_type
    )
    
    db_call = crud.create_call_history(db, call=call_history, call_sid=result["call_sid"])
    
    # Store context for conversation
    conversation_contexts[result["call_sid"]] = {
        "customer_id": customer.id,
        "customer_name": customer.name,
        "vehicle_id": vehicle.id,
        "vehicle_model": vehicle.model,
        "call_type": call_request.call_type,
        "last_service_date": last_service_date,
        "conversation_history": []
    }
    
    return schemas.CallResponse(
        success=True,
        message="Call initiated successfully",
        call_sid=result["call_sid"],
        call_history_id=db_call.id
    )

@app.post("/api/voice/handle")
async def handle_voice(request: Request, db: Session = Depends(get_db)):
    """
    Handle incoming voice call - initial greeting
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    
    # Get context
    context = conversation_contexts.get(call_sid, {})
    
    if not context:
        # No context, end call
        response = voice_agent.create_twiml_response(
            "Maaf, terjadi kesalahan sistem. Silakan hubungi kami kembali.",
            gather=False
        )
        return Response(content=response, media_type="application/xml")
    
    # Generate greeting
    greeting = voice_agent.generate_greeting(
        customer_name=context["customer_name"],
        vehicle_model=context["vehicle_model"],
        call_type=context["call_type"],
        last_service_date=context.get("last_service_date")
    )
    
    # Create TwiML response with speech recognition
    response = voice_agent.create_twiml_response(greeting, gather=True)
    
    return Response(content=response, media_type="application/xml")

@app.post("/api/voice/process")
async def process_voice(request: Request, db: Session = Depends(get_db)):
    """
    Process customer speech input
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    speech_result = form_data.get("SpeechResult", "")
    
    # Get context
    context = conversation_contexts.get(call_sid, {})
    
    if not context:
        response = voice_agent.create_twiml_response(
            "Maaf, terjadi kesalahan. Terima kasih.",
            gather=False
        )
        return Response(content=response, media_type="application/xml")
    
    # Process response with AI
    ai_result = voice_agent.handle_response(speech_result, context)
    
    # Update context
    context["conversation_history"] = ai_result.get("conversation_history", [])
    conversation_contexts[call_sid] = context
    
    # Update call history
    summary = f"Intent: {ai_result.get('intent', 'unknown')}\n"
    summary += f"Customer said: {speech_result}\n"
    summary += f"Bot replied: {ai_result.get('message', '')}"
    
    crud.update_call_summary(
        db,
        call_sid=call_sid,
        summary=summary,
        booking_confirmed=ai_result.get("booking_confirmed", False),
        needs_callback=ai_result.get("needs_followup", False)
    )
    
    # If booking confirmed, create schedule
    if ai_result.get("booking_confirmed") and ai_result.get("scheduled_date"):
        from datetime import datetime
        schedule = schemas.ServiceScheduleCreate(
            vehicle_id=context["vehicle_id"],
            scheduled_date=datetime.fromisoformat(ai_result["scheduled_date"]),
            scheduled_time=ai_result.get("scheduled_time", "09:00"),
            service_type="booking",
            notes=f"Booked via voice call {call_sid}"
        )
        crud.create_service_schedule(db, schedule=schedule)
    
    # Create response
    gather = ai_result.get("needs_followup", True)
    response = voice_agent.create_twiml_response(ai_result["message"], gather=gather)
    
    return Response(content=response, media_type="application/xml")

@app.post("/api/voice/status")
async def voice_status(request: Request, db: Session = Depends(get_db)):
    """
    Handle call status updates from Twilio
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    call_status = form_data.get("CallStatus")
    call_duration = int(form_data.get("CallDuration", 0))
    
    # Update call status in database
    crud.update_call_status(db, call_sid=call_sid, status=call_status, duration=call_duration)
    
    # Clean up context if call completed
    if call_status in ["completed", "failed", "no-answer", "busy"]:
        conversation_contexts.pop(call_sid, None)
    
    return {"status": "ok"}

# Analytics Endpoint
@app.get("/api/analytics/calls")
def get_call_analytics(db: Session = Depends(get_db)):
    """
    Get call statistics and analytics
    """
    stats = crud.get_call_statistics(db)
    return stats

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", 8000)),
        reload=os.getenv("DEBUG", "True") == "True"
    )
