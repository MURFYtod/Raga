"""
Data models for the Medical Appointment Scheduling AI Agent
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
import re

class PatientType(str, Enum):
    NEW = "new"
    RETURNING = "returning"

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class ReminderType(str, Enum):
    INITIAL = "initial"
    FORM_CHECK = "form_check"
    CONFIRMATION = "confirmation"

class Patient(BaseModel):
    """Patient information model"""
    id: str
    first_name: str
    last_name: str
    date_of_birth: date
    phone: str
    email: str
    address: str
    emergency_contact: str
    emergency_phone: str
    patient_type: PatientType
    created_at: datetime = Field(default_factory=datetime.now)
    
    @validator('phone')
    def validate_phone(cls, v):
        # Remove all non-digit characters
        phone_digits = re.sub(r'\D', '', v)
        if len(phone_digits) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return v  # Return original format for international numbers
    
    @validator('email')
    def validate_email(cls, v):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()

class Insurance(BaseModel):
    """Insurance information model"""
    carrier: str
    member_id: str
    group_number: Optional[str] = None
    policy_holder_name: str
    relationship_to_patient: str

class Doctor(BaseModel):
    """Doctor information model"""
    id: str
    name: str
    specialty: str
    location: str
    available_days: List[str]  # ['Monday', 'Tuesday', etc.]
    available_hours: Dict[str, List[int]]  # {'Monday': [9, 10, 11, ...]}

class Appointment(BaseModel):
    """Appointment model"""
    id: str
    patient_id: str
    doctor_id: str
    appointment_date: date
    appointment_time: str  # "HH:MM" format
    duration: int  # minutes
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    insurance: Optional[Insurance] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @validator('appointment_time')
    def validate_time_format(cls, v):
        time_pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
        if not re.match(time_pattern, v):
            raise ValueError('Time must be in HH:MM format')
        return v

class Reminder(BaseModel):
    """Reminder model"""
    id: str
    appointment_id: str
    patient_id: str
    reminder_type: ReminderType
    scheduled_time: datetime
    sent: bool = False
    response: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class ConversationState(BaseModel):
    """State model for LangGraph conversation"""
    patient_info: Optional[Patient] = None
    doctor_preference: Optional[str] = None
    location_preference: Optional[str] = None
    insurance_info: Optional[Insurance] = None
    appointment: Optional[Appointment] = None
    current_step: str = "greeting"
    collected_data: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    messages: List[str] = Field(default_factory=list)
