from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    single_id = Column(String, unique=True, index=True)
    nik = Column(String, index=True)
    name = Column(String, index=True)
    phone = Column(String)
    address = Column(Text)
    kelurahan = Column(String)
    kecamatan = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    vehicles = relationship("Vehicle", back_populates="customer")
    calls = relationship("CallHistory", back_populates="customer")

class Vehicle(Base):
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    no_rangka = Column(String, unique=True, index=True)
    no_polisi = Column(String, index=True)
    model = Column(String)
    type_mobil = Column(String)
    tgl_beli = Column(DateTime)
    cara_bayar = Column(String)
    grouping = Column(String)  # Regular, GBSB, T-CARE, etc
    created_at = Column(DateTime, default=datetime.utcnow)
    
    customer = relationship("Customer", back_populates="vehicles")
    service_history = relationship("ServiceHistory", back_populates="vehicle")
    service_schedules = relationship("ServiceSchedule", back_populates="vehicle")

class ServiceHistory(Base):
    __tablename__ = "service_history"
    
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    no_invoice = Column(String, unique=True, index=True)
    service_date = Column(DateTime)
    km = Column(Integer)
    repair_type = Column(String)
    labor = Column(Float, default=0)
    part = Column(Float, default=0)
    oli = Column(Float, default=0)
    total = Column(Float, default=0)
    sa_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    vehicle = relationship("Vehicle", back_populates="service_history")

class ServiceSchedule(Base):
    __tablename__ = "service_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    scheduled_date = Column(DateTime)
    scheduled_time = Column(String)
    service_type = Column(String)  # Regular, Reminder, Booking
    status = Column(String, default="scheduled")  # scheduled, completed, cancelled, no_answer
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    vehicle = relationship("Vehicle", back_populates="service_schedules")
    calls = relationship("CallHistory", back_populates="schedule")

class CallHistory(Base):
    __tablename__ = "call_history"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    schedule_id = Column(Integer, ForeignKey("service_schedules.id"), nullable=True)
    call_sid = Column(String, unique=True, index=True)
    phone_number = Column(String)
    call_type = Column(String)  # reminder, booking, follow_up
    call_status = Column(String)  # initiated, ringing, in-progress, completed, failed, busy, no-answer
    call_duration = Column(Integer, default=0)
    conversation_summary = Column(Text)
    booking_confirmed = Column(Boolean, default=False)
    needs_callback = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    customer = relationship("Customer", back_populates="calls")
    schedule = relationship("ServiceSchedule", back_populates="calls")
