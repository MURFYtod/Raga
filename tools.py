"""
LangChain tools for the Medical Appointment Scheduling AI Agent
"""
from langchain.tools import BaseTool
from typing import Optional, Type, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, date, timedelta
import re
import uuid

from database import DatabaseManager
from emr_database import EMRDatabase
from models import Patient, PatientType, Doctor, Appointment, AppointmentStatus, Insurance, Reminder, ReminderType
from config import Config

class PatientLookupInput(BaseModel):
    """Input for patient lookup tool"""
    first_name: str = Field(description="Patient's first name")
    last_name: str = Field(description="Patient's last name")
    date_of_birth: str = Field(description="Patient's date of birth in YYYY-MM-DD format")
    phone: Optional[str] = Field(default=None, description="Patient's phone number (optional)")

class SmartPatientLookupInput(BaseModel):
    """Input for smart patient lookup using EMR database"""
    phone: Optional[str] = Field(default=None, description="Patient's phone number")
    email: Optional[str] = Field(default=None, description="Patient's email address")
    first_name: Optional[str] = Field(default=None, description="Patient's first name")
    last_name: Optional[str] = Field(default=None, description="Patient's last name")

class PatientLookupTool(BaseTool):
    """Tool to lookup existing patients in the database"""
    name = "patient_lookup"
    description = "Look up an existing patient by name and date of birth. Returns patient information if found, None if new patient."
    args_schema: Type[BaseModel] = PatientLookupInput
    
    def __init__(self):
        super().__init__()
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self, first_name: str, last_name: str, date_of_birth: str, phone: Optional[str] = None) -> str:
        try:
            # Parse date
            dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            
            # Get database manager
            db = DatabaseManager()
            
            # Try to find patient by name and DOB first
            patient = db.find_patient_by_name_dob(first_name, last_name, dob)
            
            # If not found and phone provided, try phone lookup
            if not patient and phone:
                patient = db.find_patient_by_phone(phone)
            
            if patient:
                return f"EXISTING_PATIENT: {patient.id}|{patient.first_name}|{patient.last_name}|{patient.patient_type.value}|{patient.phone}|{patient.email}"
            else:
                return "NEW_PATIENT"
                
        except Exception as e:
            return f"ERROR: {str(e)}"

class AddPatientInput(BaseModel):
    """Input for adding new patient tool"""
    first_name: str = Field(description="Patient's first name")
    last_name: str = Field(description="Patient's last name")
    date_of_birth: str = Field(description="Patient's date of birth in YYYY-MM-DD format")
    phone: str = Field(description="Patient's phone number")
    email: str = Field(description="Patient's email address")
    address: str = Field(description="Patient's address")
    emergency_contact: str = Field(description="Emergency contact name")
    emergency_phone: str = Field(description="Emergency contact phone")

class AddPatientTool(BaseTool):
    """Tool to add a new patient to the database"""
    name = "add_patient"
    description = "Add a new patient to the database. Use this when patient lookup returns NEW_PATIENT."
    args_schema: Type[BaseModel] = AddPatientInput
    
    def __init__(self):
        super().__init__()
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self, first_name: str, last_name: str, date_of_birth: str, phone: str, 
             email: str, address: str, emergency_contact: str, emergency_phone: str) -> str:
        try:
            # Get database manager
            db = DatabaseManager()
            
            # Generate patient ID
            patients = db.load_patients()
            patient_id = f"P{str(len(patients) + 1).zfill(4)}"
            
            # Parse date
            dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            
            # Create patient object
            patient = Patient(
                id=patient_id,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=dob,
                phone=phone,
                email=email,
                address=address,
                emergency_contact=emergency_contact,
                emergency_phone=emergency_phone,
                patient_type=PatientType.NEW
            )
            
            # Add to database
            success = db.add_new_patient(patient)
            
            if success:
                return f"SUCCESS: Patient {patient_id} added successfully"
            else:
                return "ERROR: Failed to add patient - may already exist"
                
        except Exception as e:
            return f"ERROR: {str(e)}"

class GetDoctorsInput(BaseModel):
    """Input for getting doctors tool"""
    specialty: Optional[str] = Field(default=None, description="Filter by specialty (optional)")
    location: Optional[str] = Field(default=None, description="Filter by location (optional)")

class GetDoctorsTool(BaseTool):
    """Tool to get available doctors"""
    name = "get_doctors"
    description = "Get list of available doctors, optionally filtered by specialty or location"
    args_schema: Type[BaseModel] = GetDoctorsInput
    
    def __init__(self):
        super().__init__()
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self, specialty: Optional[str] = None, location: Optional[str] = None) -> str:
        try:
            # Get database manager
            db = DatabaseManager()
            
            doctors = db.load_doctors()
            
            # Apply filters
            if specialty:
                doctors = [d for d in doctors if specialty.lower() in d.specialty.lower()]
            
            if location:
                doctors = [d for d in doctors if location.lower() in d.location.lower()]
            
            if not doctors:
                return "NO_DOCTORS_FOUND"
            
            # Format response
            doctor_list = []
            for doctor in doctors:
                doctor_list.append(f"{doctor.id}|{doctor.name}|{doctor.specialty}|{doctor.location}")
            
            return "|".join(doctor_list)
            
        except Exception as e:
            return f"ERROR: {str(e)}"

class GetAvailableSlotsInput(BaseModel):
    """Input for getting available slots tool"""
    doctor_id: str = Field(description="Doctor ID")
    appointment_date: str = Field(description="Appointment date in YYYY-MM-DD format")
    duration: int = Field(description="Appointment duration in minutes (30 for returning, 60 for new)")

class GetAvailableSlotsTool(BaseTool):
    """Tool to get available time slots for a doctor"""
    name = "get_available_slots"
    description = "Get available time slots for a specific doctor on a specific date"
    args_schema: Type[BaseModel] = GetAvailableSlotsInput
    
    def __init__(self):
        super().__init__()
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self, doctor_id: str, appointment_date: str, duration: int) -> str:
        try:
            # Parse date
            apt_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            
            # Get database manager
            db = DatabaseManager()
            
            # Get available slots
            slots = db.get_available_slots(doctor_id, apt_date, duration)
            
            if not slots:
                return "NO_SLOTS_AVAILABLE"
            
            return "|".join(slots)
            
        except Exception as e:
            return f"ERROR: {str(e)}"

class BookAppointmentInput(BaseModel):
    """Input for booking appointment tool"""
    patient_id: str = Field(description="Patient ID")
    doctor_id: str = Field(description="Doctor ID")
    appointment_date: str = Field(description="Appointment date in YYYY-MM-DD format")
    appointment_time: str = Field(description="Appointment time in HH:MM format")
    duration: int = Field(description="Appointment duration in minutes")
    insurance_carrier: Optional[str] = Field(default=None, description="Insurance carrier")
    insurance_member_id: Optional[str] = Field(default=None, description="Insurance member ID")
    insurance_group: Optional[str] = Field(default=None, description="Insurance group number")

class BookAppointmentTool(BaseTool):
    """Tool to book an appointment"""
    name = "book_appointment"
    description = "Book an appointment for a patient with a doctor"
    args_schema: Type[BaseModel] = BookAppointmentInput
    
    def __init__(self):
        super().__init__()
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self, patient_id: str, doctor_id: str, appointment_date: str, 
             appointment_time: str, duration: int, insurance_carrier: Optional[str] = None,
             insurance_member_id: Optional[str] = None, insurance_group: Optional[str] = None) -> str:
        try:
            # Get database manager
            db = DatabaseManager()
            
            # Generate appointment ID
            appointments = db.load_appointments()
            appointment_id = f"APT{str(len(appointments) + 1).zfill(4)}"
            
            # Parse date
            apt_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            
            # Create insurance object if provided
            insurance = None
            if insurance_carrier and insurance_member_id:
                insurance = Insurance(
                    carrier=insurance_carrier,
                    member_id=insurance_member_id,
                    group_number=insurance_group,
                    policy_holder_name="",  # Will be filled later
                    relationship_to_patient="Self"
                )
            
            # Create appointment object
            appointment = Appointment(
                id=appointment_id,
                patient_id=patient_id,
                doctor_id=doctor_id,
                appointment_date=apt_date,
                appointment_time=appointment_time,
                duration=duration,
                status=AppointmentStatus.SCHEDULED,
                insurance=insurance
            )
            
            # Save appointment
            success = db.save_appointment(appointment)
            
            if success:
                return f"SUCCESS: Appointment {appointment_id} booked successfully"
            else:
                return "ERROR: Failed to book appointment"
                
        except Exception as e:
            return f"ERROR: {str(e)}"

class ScheduleRemindersInput(BaseModel):
    """Input for scheduling reminders tool"""
    appointment_id: str = Field(description="Appointment ID")
    patient_id: str = Field(description="Patient ID")
    appointment_date: str = Field(description="Appointment date in YYYY-MM-DD format")
    appointment_time: str = Field(description="Appointment time in HH:MM format")

class ScheduleRemindersTool(BaseTool):
    """Tool to schedule reminder notifications"""
    name = "schedule_reminders"
    description = "Schedule reminder notifications for an appointment"
    args_schema: Type[BaseModel] = ScheduleRemindersInput
    
    def __init__(self):
        super().__init__()
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self, appointment_id: str, patient_id: str, appointment_date: str, appointment_time: str) -> str:
        try:
            # Parse appointment datetime
            apt_datetime = datetime.strptime(f"{appointment_date} {appointment_time}", '%Y-%m-%d %H:%M')
            
            # Get database manager
            db = DatabaseManager()
            
            # Schedule reminders
            reminder_types = [ReminderType.INITIAL, ReminderType.FORM_CHECK, ReminderType.CONFIRMATION]
            reminder_hours = Config.REMINDER_HOURS
            
            for i, (reminder_type, hours_before) in enumerate(zip(reminder_types, reminder_hours)):
                reminder_id = f"REM{appointment_id.replace('APT', '')}{i+1}"
                scheduled_time = apt_datetime - timedelta(hours=hours_before)
                
                reminder = Reminder(
                    id=reminder_id,
                    appointment_id=appointment_id,
                    patient_id=patient_id,
                    reminder_type=reminder_type,
                    scheduled_time=scheduled_time
                )
                
                db.save_reminder(reminder)
            
            return f"SUCCESS: 3 reminders scheduled for appointment {appointment_id}"
            
        except Exception as e:
            return f"ERROR: {str(e)}"

class ExportAppointmentsTool(BaseTool):
    """Tool to export appointments to Excel"""
    name = "export_appointments"
    description = "Export all appointments to Excel file for admin review"
    args_schema: Type[BaseModel] = BaseModel  # No input needed
    
    def __init__(self):
        super().__init__()
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self) -> str:
        try:
            # Get database manager
            db = DatabaseManager()
            
            # Get appointments data
            df = db.get_appointments_for_export()
            
            # Save to Excel
            export_file = f"data/appointments_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(export_file, index=False)
            
            return f"SUCCESS: Appointments exported to {export_file}"
            
        except Exception as e:
            return f"ERROR: {str(e)}"

class SmartPatientLookupTool(BaseTool):
    """Smart tool for looking up patient information using EMR database"""
    name = "smart_patient_lookup"
    description = "Look up patient information using EMR database with automatic new vs returning detection"
    args_schema: Type[BaseModel] = SmartPatientLookupInput
    
    def __init__(self):
        super().__init__()
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self, phone: Optional[str] = None, email: Optional[str] = None, 
             first_name: Optional[str] = None, last_name: Optional[str] = None) -> str:
        """Look up patient information using EMR database"""
        try:
            emr_db = EMRDatabase()
            
            # Use EMR database to detect patient type and get full record
            patient_record, patient_type = emr_db.detect_patient_type(
                phone=phone, email=email, first_name=first_name, last_name=last_name
            )
            
            if patient_record:
                # Patient found in EMR
                medical_info = f"Medical History: {', '.join(patient_record.medical_history[:3])}..." if patient_record.medical_history else "No medical history"
                allergies_info = f"Allergies: {', '.join(patient_record.allergies)}" if patient_record.allergies else "No known allergies"
                medications_info = f"Current Medications: {', '.join(patient_record.current_medications)}" if patient_record.current_medications else "No current medications"
                
                return f"""✅ PATIENT FOUND IN EMR SYSTEM:
                
👤 Name: {patient_record.first_name} {patient_record.last_name}
🆔 Patient ID: {patient_record.patient_id}
📅 DOB: {patient_record.date_of_birth}
📱 Phone: {patient_record.phone}
📧 Email: {patient_record.email}
🏥 Patient Type: {patient_type.upper()}
📊 Total Visits: {patient_record.total_visits}
📅 Last Visit: {patient_record.last_visit or 'Never'}
⏱️ Appointment Duration: {emr_db.get_smart_duration(patient_record, patient_type)} minutes

🏥 MEDICAL INFORMATION:
{medical_info}
{allergies_info}
{medications_info}

💊 Insurance: {patient_record.insurance_provider} (ID: {patient_record.insurance_id})"""
            else:
                return f"❌ Patient not found in EMR system. This appears to be a NEW PATIENT."
            
        except Exception as e:
            return f"Error looking up patient in EMR: {str(e)}"

class SmartSchedulingTool(BaseTool):
    """Smart scheduling tool that automatically determines appointment duration based on EMR data"""
    name = "smart_scheduling"
    description = "Schedule appointment with automatic duration detection (60min for new, 30min for returning patients)"
    args_schema: Type[BaseModel] = PatientLookupInput
    
    def __init__(self):
        super().__init__()
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self, first_name: str, last_name: str, date_of_birth: str, phone: Optional[str] = None) -> str:
        """Smart scheduling with automatic duration detection"""
        try:
            emr_db = EMRDatabase()
            
            # Detect patient type using EMR database
            patient_record, patient_type = emr_db.detect_patient_type(
                phone=phone, first_name=first_name, last_name=last_name
            )
            
            # Get smart duration based on patient type
            duration = emr_db.get_smart_duration(patient_record, patient_type)
            
            # Get available slots for tomorrow
            tomorrow = date.today() + timedelta(days=1)
            db = DatabaseManager()
            
            # Get available slots for different doctors
            doctors = ["D001", "D002", "D003", "D004", "D005"]
            suitable_slots = []
            
            for doctor_id in doctors:
                try:
                    slots = db.get_available_slots(doctor_id, tomorrow.strftime('%Y-%m-%d'), duration)
                    for slot in slots:
                        suitable_slots.append({
                            'date': tomorrow.strftime('%Y-%m-%d'),
                            'time': slot,
                            'doctor_id': doctor_id,
                            'doctor_name': f"Dr. {doctor_id}"
                        })
                except:
                    # If specific doctor doesn't have slots, continue
                    continue
            
            if not suitable_slots:
                return f"No available slots for {duration}-minute appointment on {tomorrow.strftime('%Y-%m-%d')}"
            
            # Format available slots
            slots_info = []
            for slot in suitable_slots[:5]:  # Show first 5 slots
                slots_info.append(f"📅 {slot['date']} at {slot['time']} ({slot['doctor_name']})")
            
            return f"""🎯 SMART SCHEDULING RESULT:
            
👤 Patient: {first_name} {last_name}
🏥 Patient Type: {patient_type.upper()}
⏱️ Recommended Duration: {duration} minutes
📱 Phone: {phone or 'Not provided'}

📅 AVAILABLE SLOTS:
{chr(10).join(slots_info)}

💡 The system automatically detected this as a {patient_type} patient and assigned {duration} minutes for the appointment."""
            
        except Exception as e:
            return f"Error in smart scheduling: {str(e)}"


def get_all_tools():
    """Get all available tools"""
    return [
        PatientLookupTool(),
        SmartPatientLookupTool(),
        SmartSchedulingTool(),
        AddPatientTool(),
        GetDoctorsTool(),
        GetAvailableSlotsTool(),
        BookAppointmentTool(),
        ScheduleRemindersTool(),
        ExportAppointmentsTool(),
    ]
