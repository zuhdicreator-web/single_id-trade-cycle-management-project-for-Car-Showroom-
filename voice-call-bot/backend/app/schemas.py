from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class CustomerBase(BaseModel):
    single_id: str
    nik: str
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    kelurahan: Optional[str] = None
    kecamatan: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class VehicleBase(BaseModel):
    no_rangka: str
    no_polisi: Optional[str] = None
    model: str
    type_mobil: Optional[str] = None
    tgl_beli: Optional[datetime] = None
    cara_bayar: Optional[str] = None
    grouping: Optional[str] = "Regular"

class VehicleCreate(VehicleBase):
    customer_id: int

class Vehicle(VehicleBase):
    id: int
    customer_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ServiceHistoryBase(BaseModel):
    no_invoice: str
    service_date: datetime
    km: Optional[int] = 0
    repair_type: Optional[str] = None
    labor: float = 0
    part: float = 0
    oli: float = 0
    total: float = 0
    sa_name: Optional[str] = None

class ServiceHistoryCreate(ServiceHistoryBase):
    vehicle_id: int

class ServiceHistory(ServiceHistoryBase):
    id: int
    vehicle_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ServiceScheduleBase(BaseModel):
    scheduled_date: datetime
    scheduled_time: str
    service_type: str
    notes: Optional[str] = None

class ServiceScheduleCreate(ServiceScheduleBase):
    vehicle_id: int

class ServiceSchedule(ServiceScheduleBase):
    id: int
    vehicle_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CallHistoryBase(BaseModel):
    phone_number: str
    call_type: str
    conversation_summary: Optional[str] = None
    booking_confirmed: bool = False
    needs_callback: bool = False

class CallHistoryCreate(CallHistoryBase):
    customer_id: int
    schedule_id: Optional[int] = None

class CallHistory(CallHistoryBase):
    id: int
    customer_id: int
    schedule_id: Optional[int] = None
    call_sid: str
    call_status: str
    call_duration: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class CallRequest(BaseModel):
    customer_id: int
    call_type: str
    schedule_id: Optional[int] = None

class CallResponse(BaseModel):
    success: bool
    message: str
    call_sid: Optional[str] = None
    call_history_id: Optional[int] = None
