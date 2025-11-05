"""
Database operations for the Medical Appointment Scheduling AI Agent
"""
import pandas as pd
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from models import Patient, Doctor, Appointment, AppointmentStatus, Insurance, Reminder, ReminderType
from config import Config
import os

class DatabaseManager:
    """Manages all database operations for the medical scheduling system"""
    
    def __init__(self):
        self.patients_csv = Config.PATIENTS_CSV
        self.doctors_excel = Config.DOCTORS_SCHEDULE
        self.appointments_json = Config.APPOINTMENTS_JSON
        self.reminders_json = Config.REMINDERS_JSON
        
        # Ensure data directory exists
        os.makedirs(Config.DATA_DIR, exist_ok=True)
    
    def load_patients(self) -> List[Patient]:
        """Load all patients from CSV"""
        if not os.path.exists(self.patients_csv):
            return []
        
        df = pd.read_csv(self.patients_csv)
        patients = []
        
        for _, row in df.iterrows():
            try:
                patient = Patient(
                    id=row['id'],
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    date_of_birth=datetime.strptime(row['date_of_birth'], '%Y-%m-%d').date(),
                    phone=str(row['phone']),
                    email=row['email'],
                    address=row['address'],
                    emergency_contact=row['emergency_contact'],
                    emergency_phone=str(row['emergency_phone']),
                    patient_type=row['patient_type'],
                    created_at=datetime.fromisoformat(row['created_at'])
                )
                patients.append(patient)
            except Exception as e:
                print(f"Error loading patient {row.get('id', 'unknown')}: {e}")
                continue
        
        return patients
    
    def find_patient_by_name_dob(self, first_name: str, last_name: str, date_of_birth: date) -> Optional[Patient]:
        """Find patient by name and date of birth"""
        patients = self.load_patients()
        
        for patient in patients:
            if (patient.first_name.lower() == first_name.lower() and 
                patient.last_name.lower() == last_name.lower() and 
                patient.date_of_birth == date_of_birth):
                return patient
        
        return None
    
    def find_patient_by_phone(self, phone: str) -> Optional[Patient]:
        """Find patient by phone number"""
        patients = self.load_patients()
        
        # Clean phone number (remove non-digits)
        clean_phone = ''.join(filter(str.isdigit, phone))
        
        for patient in patients:
            if patient.phone == clean_phone:
                return patient
        
        return None
    
    def add_new_patient(self, patient: Patient) -> bool:
        """Add a new patient to the database"""
        try:
            # Load existing patients
            patients = self.load_patients()
            
            # Check if patient already exists
            existing = self.find_patient_by_name_dob(
                patient.first_name, 
                patient.last_name, 
                patient.date_of_birth
            )
            
            if existing:
                return False  # Patient already exists
            
            # Add new patient
            patients.append(patient)
            
            # Save to CSV
            patients_data = []
            for p in patients:
                patients_data.append({
                    'id': p.id,
                    'first_name': p.first_name,
                    'last_name': p.last_name,
                    'date_of_birth': p.date_of_birth.strftime('%Y-%m-%d'),
                    'phone': p.phone,
                    'email': p.email,
                    'address': p.address,
                    'emergency_contact': p.emergency_contact,
                    'emergency_phone': p.emergency_phone,
                    'patient_type': p.patient_type.value,
                    'created_at': p.created_at.isoformat()
                })
            
            df = pd.DataFrame(patients_data)
            df.to_csv(self.patients_csv, index=False)
            return True
            
        except Exception as e:
            print(f"Error adding patient: {e}")
            return False
    
    def load_doctors(self) -> List[Doctor]:
        """Load all doctors from Excel"""
        if not os.path.exists(self.doctors_excel):
            return []
        
        try:
            # Load doctor information
            df_doctors = pd.read_excel(self.doctors_excel, sheet_name='Doctors')
            df_schedule = pd.read_excel(self.doctors_excel, sheet_name='Schedule')
            
            doctors = []
            
            for _, row in df_doctors.iterrows():
                # Get schedule for this doctor
                doctor_schedule = df_schedule[df_schedule['doctor_id'] == row['id']]
                
                available_days = []
                available_hours = {}
                
                for _, schedule_row in doctor_schedule.iterrows():
                    day = schedule_row['day']
                    hour = schedule_row['hour']
                    
                    if day not in available_days:
                        available_days.append(day)
                        available_hours[day] = []
                    
                    if schedule_row['available']:
                        available_hours[day].append(hour)
                
                doctor = Doctor(
                    id=row['id'],
                    name=row['name'],
                    specialty=row['specialty'],
                    location=row['location'],
                    available_days=available_days,
                    available_hours=available_hours
                )
                doctors.append(doctor)
            
            return doctors
            
        except Exception as e:
            print(f"Error loading doctors: {e}")
            return []
    
    def get_available_slots(self, doctor_id: str, appointment_date: date, duration: int) -> List[str]:
        """Get available time slots for a doctor on a specific date"""
        doctors = self.load_doctors()
        appointments = self.load_appointments()
        
        # Find the doctor
        doctor = None
        for d in doctors:
            if d.id == doctor_id:
                doctor = d
                break
        
        if not doctor:
            return []
        
        # Get day name
        day_name = appointment_date.strftime("%A")
        
        if day_name not in doctor.available_days:
            return []
        
        # Get available hours for this day
        available_hours = doctor.available_hours.get(day_name, [])
        
        # Filter out lunch break
        available_hours = [h for h in available_hours if not (Config.LUNCH_BREAK_START <= h < Config.LUNCH_BREAK_END)]
        
        # Get existing appointments for this doctor on this date
        existing_appointments = [
            apt for apt in appointments 
            if apt['doctor_id'] == doctor_id and 
            datetime.strptime(apt['appointment_date'], '%Y-%m-%d').date() == appointment_date
        ]
        
        # Convert existing appointments to time slots
        booked_slots = set()
        for apt in existing_appointments:
            start_hour = int(apt['appointment_time'].split(':')[0])
            apt_duration = apt['duration']
            
            # Mark all slots for this appointment as booked
            for i in range(apt_duration // 30):  # 30-minute slots
                booked_slots.add(start_hour + i * 0.5)
        
        # Find available slots
        available_slots = []
        for hour in available_hours:
            # Check if we can fit the appointment duration
            can_fit = True
            slots_needed = duration / 30  # Convert to 30-minute slots
            
            for i in range(int(slots_needed)):
                slot_time = hour + i * 0.5
                if slot_time in booked_slots:
                    can_fit = False
                    break
                
                # Check if slot is within working hours
                if slot_time < Config.WORKING_HOURS_START or slot_time >= Config.WORKING_HOURS_END:
                    can_fit = False
                    break
            
            if can_fit:
                available_slots.append(f"{int(hour):02d}:00")
        
        return available_slots
    
    def load_appointments(self) -> List[Dict[str, Any]]:
        """Load all appointments from JSON"""
        if not os.path.exists(self.appointments_json):
            return []
        
        try:
            with open(self.appointments_json, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading appointments: {e}")
            return []
    
    def save_appointment(self, appointment: Appointment) -> bool:
        """Save a new appointment"""
        try:
            appointments = self.load_appointments()
            
            appointment_data = {
                'id': appointment.id,
                'patient_id': appointment.patient_id,
                'doctor_id': appointment.doctor_id,
                'appointment_date': appointment.appointment_date.strftime('%Y-%m-%d'),
                'appointment_time': appointment.appointment_time,
                'duration': appointment.duration,
                'status': appointment.status.value,
                'notes': appointment.notes,
                'created_at': appointment.created_at.isoformat(),
                'updated_at': appointment.updated_at.isoformat()
            }
            
            appointments.append(appointment_data)
            
            with open(self.appointments_json, 'w') as f:
                json.dump(appointments, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving appointment: {e}")
            return False
    
    def update_appointment_status(self, appointment_id: str, status: AppointmentStatus) -> bool:
        """Update appointment status"""
        try:
            appointments = self.load_appointments()
            
            for apt in appointments:
                if apt['id'] == appointment_id:
                    apt['status'] = status.value
                    apt['updated_at'] = datetime.now().isoformat()
                    break
            else:
                return False  # Appointment not found
            
            with open(self.appointments_json, 'w') as f:
                json.dump(appointments, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error updating appointment status: {e}")
            return False
    
    def load_reminders(self) -> List[Dict[str, Any]]:
        """Load all reminders from JSON"""
        if not os.path.exists(self.reminders_json):
            return []
        
        try:
            with open(self.reminders_json, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading reminders: {e}")
            return []
    
    def save_reminder(self, reminder: Reminder) -> bool:
        """Save a new reminder"""
        try:
            reminders = self.load_reminders()
            
            reminder_data = {
                'id': reminder.id,
                'appointment_id': reminder.appointment_id,
                'patient_id': reminder.patient_id,
                'reminder_type': reminder.reminder_type.value,
                'scheduled_time': reminder.scheduled_time.isoformat(),
                'sent': reminder.sent,
                'response': reminder.response,
                'created_at': reminder.created_at.isoformat()
            }
            
            reminders.append(reminder_data)
            
            with open(self.reminders_json, 'w') as f:
                json.dump(reminders, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving reminder: {e}")
            return False
    
    def get_appointments_for_export(self) -> pd.DataFrame:
        """Get all appointments formatted for Excel export"""
        appointments = self.load_appointments()
        patients = self.load_patients()
        doctors = self.load_doctors()
        
        # Create patient lookup
        patient_lookup = {p.id: p for p in patients}
        doctor_lookup = {d.id: d for d in doctors}
        
        export_data = []
        for apt in appointments:
            patient = patient_lookup.get(apt['patient_id'])
            doctor = doctor_lookup.get(apt['doctor_id'])
            
            if patient and doctor:
                export_data.append({
                    'Appointment ID': apt['id'],
                    'Patient Name': f"{patient.first_name} {patient.last_name}",
                    'Patient Phone': patient.phone,
                    'Patient Email': patient.email,
                    'Patient Type': patient.patient_type.value.title(),
                    'Doctor Name': doctor.name,
                    'Doctor Specialty': doctor.specialty,
                    'Location': doctor.location,
                    'Appointment Date': apt['appointment_date'],
                    'Appointment Time': apt['appointment_time'],
                    'Duration (minutes)': apt['duration'],
                    'Status': apt['status'].title(),
                    'Created At': apt['created_at'],
                    'Updated At': apt['updated_at']
                })
        
        return pd.DataFrame(export_data)
