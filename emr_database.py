#!/usr/bin/env python3
"""
EMR (Electronic Medical Records) Database System
Handles patient records, medical history, and appointment tracking
"""

import sqlite3
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import hashlib
import random
from faker import Faker

fake = Faker()

@dataclass
class PatientRecord:
    """Patient medical record"""
    patient_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    phone: str
    email: str
    address: str
    emergency_contact: str
    emergency_phone: str
    insurance_provider: str
    insurance_id: str
    medical_history: List[str]
    allergies: List[str]
    current_medications: List[str]
    last_visit: Optional[date]
    total_visits: int
    patient_type: str  # 'new' or 'returning'
    created_at: datetime
    updated_at: datetime

@dataclass
class AppointmentRecord:
    """Appointment record in EMR"""
    appointment_id: str
    patient_id: str
    doctor_id: str
    appointment_date: date
    appointment_time: str
    duration: int
    status: str
    reason: str
    notes: str
    created_at: datetime

class EMRDatabase:
    """EMR Database Manager"""
    
    def __init__(self, db_path: str = "data/emr_database.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the EMR database with tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Patients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                patient_id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                date_of_birth DATE NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                address TEXT NOT NULL,
                emergency_contact TEXT NOT NULL,
                emergency_phone TEXT NOT NULL,
                insurance_provider TEXT,
                insurance_id TEXT,
                medical_history TEXT,  -- JSON array
                allergies TEXT,        -- JSON array
                current_medications TEXT,  -- JSON array
                last_visit DATE,
                total_visits INTEGER DEFAULT 0,
                patient_type TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Appointments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                appointment_id TEXT PRIMARY KEY,
                patient_id TEXT NOT NULL,
                doctor_id TEXT NOT NULL,
                appointment_date DATE NOT NULL,
                appointment_time TEXT NOT NULL,
                duration INTEGER NOT NULL,
                status TEXT DEFAULT 'scheduled',
                reason TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
            )
        ''')
        
        # Medical visits table (for tracking visit history)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medical_visits (
                visit_id TEXT PRIMARY KEY,
                patient_id TEXT NOT NULL,
                appointment_id TEXT,
                visit_date DATE NOT NULL,
                doctor_id TEXT NOT NULL,
                diagnosis TEXT,
                treatment TEXT,
                prescription TEXT,
                follow_up_required BOOLEAN DEFAULT FALSE,
                follow_up_date DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id),
                FOREIGN KEY (appointment_id) REFERENCES appointments (appointment_id)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_patients_phone ON patients(phone)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_patients_email ON patients(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_visits_patient ON medical_visits(patient_id)')
        
        conn.commit()
        conn.close()
    
    def add_patient(self, patient: PatientRecord) -> bool:
        """Add a new patient to the EMR database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO patients (
                    patient_id, first_name, last_name, date_of_birth, phone, email,
                    address, emergency_contact, emergency_phone, insurance_provider,
                    insurance_id, medical_history, allergies, current_medications,
                    last_visit, total_visits, patient_type, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                patient.patient_id, patient.first_name, patient.last_name,
                patient.date_of_birth, patient.phone, patient.email,
                patient.address, patient.emergency_contact, patient.emergency_phone,
                patient.insurance_provider, patient.insurance_id,
                json.dumps(patient.medical_history),
                json.dumps(patient.allergies),
                json.dumps(patient.current_medications),
                patient.last_visit, patient.total_visits, patient.patient_type,
                patient.created_at, patient.updated_at
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding patient: {e}")
            return False
    
    def get_patient_by_phone(self, phone: str) -> Optional[PatientRecord]:
        """Get patient by phone number"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM patients WHERE phone = ?', (phone,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return self._row_to_patient_record(row)
            return None
        except Exception as e:
            print(f"Error getting patient by phone: {e}")
            return None
    
    def get_patient_by_email(self, email: str) -> Optional[PatientRecord]:
        """Get patient by email"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM patients WHERE email = ?', (email,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return self._row_to_patient_record(row)
            return None
        except Exception as e:
            print(f"Error getting patient by email: {e}")
            return None
    
    def get_patient_by_name(self, first_name: str, last_name: str) -> Optional[PatientRecord]:
        """Get patient by name"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM patients WHERE first_name = ? AND last_name = ?', 
                         (first_name, last_name))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return self._row_to_patient_record(row)
            return None
        except Exception as e:
            print(f"Error getting patient by name: {e}")
            return None
    
    def update_patient_visit(self, patient_id: str, visit_date: date) -> bool:
        """Update patient's visit information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update last visit and increment total visits
            cursor.execute('''
                UPDATE patients 
                SET last_visit = ?, total_visits = total_visits + 1, 
                    patient_type = 'returning', updated_at = CURRENT_TIMESTAMP
                WHERE patient_id = ?
            ''', (visit_date, patient_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating patient visit: {e}")
            return False
    
    def add_appointment(self, appointment: AppointmentRecord) -> bool:
        """Add appointment to EMR database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO appointments (
                    appointment_id, patient_id, doctor_id, appointment_date,
                    appointment_time, duration, status, reason, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                appointment.appointment_id, appointment.patient_id, appointment.doctor_id,
                appointment.appointment_date, appointment.appointment_time,
                appointment.duration, appointment.status, appointment.reason,
                appointment.notes, appointment.created_at
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding appointment: {e}")
            return False
    
    def get_patient_appointments(self, patient_id: str) -> List[AppointmentRecord]:
        """Get all appointments for a patient"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM appointments 
                WHERE patient_id = ? 
                ORDER BY appointment_date DESC, appointment_time DESC
            ''', (patient_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [self._row_to_appointment_record(row) for row in rows]
        except Exception as e:
            print(f"Error getting patient appointments: {e}")
            return []
    
    def detect_patient_type(self, phone: str = None, email: str = None, 
                          first_name: str = None, last_name: str = None) -> Tuple[Optional[PatientRecord], str]:
        """
        Detect if patient is new or returning based on EMR database
        Returns: (PatientRecord or None, 'new' or 'returning')
        """
        patient = None
        
        # Try to find patient by phone first
        if phone:
            patient = self.get_patient_by_phone(phone)
        
        # Try email if not found by phone
        if not patient and email:
            patient = self.get_patient_by_email(email)
        
        # Try name if not found by phone or email
        if not patient and first_name and last_name:
            patient = self.get_patient_by_name(first_name, last_name)
        
        if patient:
            # Patient exists in EMR - check if they have previous visits
            if patient.total_visits > 0:
                return patient, 'returning'
            else:
                return patient, 'new'
        else:
            # Patient not found in EMR - they are new
            return None, 'new'
    
    def get_smart_duration(self, patient_record: Optional[PatientRecord], patient_type: str) -> int:
        """
        Get smart appointment duration based on patient type and EMR data
        Returns: 60 for new patients, 30 for returning patients
        """
        if patient_type == 'new' or not patient_record or patient_record.total_visits == 0:
            return 60  # New patient - 60 minutes
        else:
            return 30  # Returning patient - 30 minutes
    
    def _row_to_patient_record(self, row) -> PatientRecord:
        """Convert database row to PatientRecord object"""
        return PatientRecord(
            patient_id=row[0],
            first_name=row[1],
            last_name=row[2],
            date_of_birth=datetime.strptime(row[3], '%Y-%m-%d').date(),
            phone=row[4],
            email=row[5],
            address=row[6],
            emergency_contact=row[7],
            emergency_phone=row[8],
            insurance_provider=row[9],
            insurance_id=row[10],
            medical_history=json.loads(row[11]) if row[11] else [],
            allergies=json.loads(row[12]) if row[12] else [],
            current_medications=json.loads(row[13]) if row[13] else [],
            last_visit=datetime.strptime(row[14], '%Y-%m-%d').date() if row[14] else None,
            total_visits=row[15],
            patient_type=row[16],
            created_at=datetime.fromisoformat(row[17]),
            updated_at=datetime.fromisoformat(row[18])
        )
    
    def _row_to_appointment_record(self, row) -> AppointmentRecord:
        """Convert database row to AppointmentRecord object"""
        return AppointmentRecord(
            appointment_id=row[0],
            patient_id=row[1],
            doctor_id=row[2],
            appointment_date=datetime.strptime(row[3], '%Y-%m-%d').date(),
            appointment_time=row[4],
            duration=row[5],
            status=row[6],
            reason=row[7],
            notes=row[8],
            created_at=datetime.fromisoformat(row[9])
        )
    
    def get_all_patients(self) -> List[PatientRecord]:
        """Get all patients from EMR database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM patients ORDER BY created_at DESC')
            rows = cursor.fetchall()
            conn.close()
            
            return [self._row_to_patient_record(row) for row in rows]
        except Exception as e:
            print(f"Error getting all patients: {e}")
            return []
    
    def search_patients(self, query: str) -> List[PatientRecord]:
        """Search patients by name, phone, or email"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            search_term = f"%{query}%"
            cursor.execute('''
                SELECT * FROM patients 
                WHERE first_name LIKE ? OR last_name LIKE ? OR phone LIKE ? OR email LIKE ?
                ORDER BY last_name, first_name
            ''', (search_term, search_term, search_term, search_term))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [self._row_to_patient_record(row) for row in rows]
        except Exception as e:
            print(f"Error searching patients: {e}")
            return []

class EMRDataGenerator:
    """Generate synthetic EMR data"""
    
    def __init__(self):
        self.fake = Faker()
        self.medical_conditions = [
            "Hypertension", "Diabetes Type 2", "High Cholesterol", "Asthma",
            "Arthritis", "Migraine", "Anxiety", "Depression", "Sleep Apnea",
            "GERD", "Allergic Rhinitis", "Back Pain", "Knee Pain", "Chest Pain",
            "Headache", "Fatigue", "Insomnia", "Irritable Bowel Syndrome"
        ]
        
        self.allergies = [
            "Penicillin", "Sulfa drugs", "Latex", "Shellfish", "Nuts",
            "Dairy", "Pollen", "Dust mites", "Cats", "Dogs", "Mold",
            "Aspirin", "Ibuprofen", "Codeine", "Morphine"
        ]
        
        self.medications = [
            "Metformin", "Lisinopril", "Atorvastatin", "Metoprolol",
            "Omeprazole", "Albuterol", "Sertraline", "Loratadine",
            "Ibuprofen", "Acetaminophen", "Warfarin", "Furosemide",
            "Amlodipine", "Losartan", "Simvastatin", "Prednisone"
        ]
        
        self.insurance_providers = [
            "Blue Cross Blue Shield", "Aetna", "Cigna", "UnitedHealthcare",
            "Kaiser Permanente", "Humana", "Anthem", "Medicare",
            "Medicaid", "Tricare", "AARP", "Oscar Health"
        ]
    
    def generate_patient_record(self, patient_id: str) -> PatientRecord:
        """Generate a synthetic patient record"""
        first_name = self.fake.first_name()
        last_name = self.fake.last_name()
        birth_date = self.fake.date_of_birth(minimum_age=18, maximum_age=80)
        
        # Generate medical history (2-5 conditions)
        num_conditions = random.randint(2, 5)
        medical_history = random.sample(self.medical_conditions, num_conditions)
        
        # Generate allergies (0-3 allergies)
        num_allergies = random.randint(0, 3)
        allergies = random.sample(self.allergies, num_allergies) if num_allergies > 0 else []
        
        # Generate current medications (1-4 medications)
        num_meds = random.randint(1, 4)
        current_medications = random.sample(self.medications, num_meds)
        
        # Determine if patient is new or returning (70% returning, 30% new)
        is_returning = random.random() < 0.7
        total_visits = random.randint(1, 15) if is_returning else 0
        last_visit = self.fake.date_between(start_date='-2y', end_date='-1d') if is_returning else None
        
        return PatientRecord(
            patient_id=patient_id,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=birth_date,
            phone=self.fake.phone_number()[:10],  # Ensure 10 digits
            email=self.fake.email(),
            address=self.fake.address(),
            emergency_contact=f"{self.fake.first_name()} {self.fake.last_name()}",
            emergency_phone=self.fake.phone_number()[:10],
            insurance_provider=random.choice(self.insurance_providers),
            insurance_id=self.fake.bothify(text='#########'),
            medical_history=medical_history,
            allergies=allergies,
            current_medications=current_medications,
            last_visit=last_visit,
            total_visits=total_visits,
            patient_type='returning' if is_returning else 'new',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def generate_appointment_record(self, patient_id: str, appointment_id: str) -> AppointmentRecord:
        """Generate a synthetic appointment record"""
        appointment_date = self.fake.date_between(start_date='-6m', end_date='+1m')
        appointment_time = random.choice(['09:00', '10:00', '11:00', '14:00', '15:00', '16:00'])
        
        reasons = [
            "Annual checkup", "Follow-up visit", "New symptoms", "Prescription refill",
            "Lab results review", "Specialist consultation", "Vaccination",
            "Chronic condition management", "Preventive care", "Emergency visit"
        ]
        
        return AppointmentRecord(
            appointment_id=appointment_id,
            patient_id=patient_id,
            doctor_id=random.choice(['D001', 'D002', 'D003', 'D004', 'D005']),
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            duration=random.choice([30, 60]),  # Will be updated based on patient type
            status=random.choice(['completed', 'scheduled', 'cancelled']),
            reason=random.choice(reasons),
            notes=self.fake.text(max_nb_chars=200),
            created_at=datetime.now()
        )
    
    def populate_emr_database(self, num_patients: int = 50) -> bool:
        """Populate EMR database with synthetic data"""
        try:
            emr_db = EMRDatabase()
            
            print(f"Generating {num_patients} synthetic patients...")
            
            for i in range(num_patients):
                patient_id = f"EMR_{i+1:03d}"
                patient = self.generate_patient_record(patient_id)
                
                # Add patient to database
                emr_db.add_patient(patient)
                
                # Generate 1-3 appointments for returning patients
                if patient.patient_type == 'returning':
                    num_appointments = random.randint(1, 3)
                    for j in range(num_appointments):
                        appointment_id = f"APT_{patient_id}_{j+1}"
                        appointment = self.generate_appointment_record(patient_id, appointment_id)
                        
                        # Update duration based on patient type
                        appointment.duration = emr_db.get_smart_duration(patient, patient.patient_type)
                        
                        emr_db.add_appointment(appointment)
            
            print(f"✅ Successfully populated EMR database with {num_patients} patients")
            return True
            
        except Exception as e:
            print(f"❌ Error populating EMR database: {e}")
            return False

if __name__ == "__main__":
    # Generate synthetic EMR data
    generator = EMRDataGenerator()
    generator.populate_emr_database(50)
    
    # Test the EMR database
    emr_db = EMRDatabase()
    
    print("\n🔍 Testing EMR Database:")
    print("=" * 50)
    
    # Test patient detection
    test_phone = "5551234567"
    patient, patient_type = emr_db.detect_patient_type(phone=test_phone)
    
    if patient:
        print(f"Found patient: {patient.first_name} {patient.last_name}")
        print(f"Patient type: {patient_type}")
        print(f"Total visits: {patient.total_visits}")
        print(f"Smart duration: {emr_db.get_smart_duration(patient, patient_type)} minutes")
    else:
        print(f"No patient found with phone: {test_phone}")
    
    # Show database statistics
    all_patients = emr_db.get_all_patients()
    new_patients = [p for p in all_patients if p.patient_type == 'new']
    returning_patients = [p for p in all_patients if p.patient_type == 'returning']
    
    print(f"\n📊 Database Statistics:")
    print(f"Total patients: {len(all_patients)}")
    print(f"New patients: {len(new_patients)}")
    print(f"Returning patients: {len(returning_patients)}")
