#!/usr/bin/env python3
"""
Data setup script for Streamlit Cloud deployment
Creates necessary data files and directories
"""

import os
import pandas as pd
from datetime import datetime, date, timedelta
import json
from faker import Faker

def create_data_directory():
    """Create data directory if it doesn't exist"""
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/forms", exist_ok=True)
    print("✅ Created data directories")

def create_sample_patients():
    """Create sample patient data"""
    fake = Faker()
    
    patients_data = []
    for i in range(10):  # Create 10 sample patients
        patient = {
            'id': f'P{str(i+1).zfill(3)}',
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'date_of_birth': fake.date_of_birth(minimum_age=18, maximum_age=80),
            'phone': fake.phone_number()[:10],  # Keep it simple
            'email': fake.email(),
            'address': fake.address(),
            'emergency_contact': fake.name(),
            'emergency_phone': fake.phone_number()[:10],
            'patient_type': fake.random_element(elements=('new', 'returning')),
            'created_at': datetime.now().isoformat()
        }
        patients_data.append(patient)
    
    # Save to CSV
    df = pd.DataFrame(patients_data)
    df.to_csv("data/patients.csv", index=False)
    print("✅ Created sample patients data")

def create_sample_doctors():
    """Create sample doctor schedule data"""
    doctors_data = {
        'Doctor': ['Dr. Smith', 'Dr. Johnson', 'Dr. Williams', 'Dr. Brown'],
        'Specialty': ['General Medicine', 'Cardiology', 'Dermatology', 'Orthopedics'],
        'Location': ['Main Clinic', 'Main Clinic', 'Branch Office', 'Main Clinic'],
        'Monday': ['9:00-17:00', '9:00-17:00', '9:00-17:00', '9:00-17:00'],
        'Tuesday': ['9:00-17:00', '9:00-17:00', '9:00-17:00', '9:00-17:00'],
        'Wednesday': ['9:00-17:00', '9:00-17:00', '9:00-17:00', '9:00-17:00'],
        'Thursday': ['9:00-17:00', '9:00-17:00', '9:00-17:00', '9:00-17:00'],
        'Friday': ['9:00-17:00', '9:00-17:00', '9:00-17:00', '9:00-17:00'],
        'Saturday': ['9:00-13:00', 'Closed', '9:00-13:00', 'Closed'],
        'Sunday': ['Closed', 'Closed', 'Closed', 'Closed']
    }
    
    df = pd.DataFrame(doctors_data)
    df.to_excel("data/doctors_schedule.xlsx", index=False)
    print("✅ Created sample doctors schedule")

def create_sample_appointments():
    """Create sample appointment data"""
    appointments = []
    for i in range(5):  # Create 5 sample appointments
        appointment = {
            'id': f'APT{str(i+1).zfill(3)}',
            'patient_id': f'P{str(i+1).zfill(3)}',
            'doctor_id': f'D{str((i%4)+1).zfill(3)}',
            'appointment_date': (date.today() + timedelta(days=i+1)).isoformat(),
            'appointment_time': f'{9+i}:00',
            'duration': 60 if i % 2 == 0 else 30,
            'status': 'scheduled',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        appointments.append(appointment)
    
    with open("data/appointments.json", "w") as f:
        json.dump(appointments, f, indent=2)
    print("✅ Created sample appointments data")

def create_sample_reminders():
    """Create sample reminder data"""
    reminders = []
    for i in range(3):  # Create 3 sample reminders
        reminder = {
            'id': f'REM{str(i+1).zfill(3)}',
            'patient_id': f'P{str(i+1).zfill(3)}',
            'appointment_id': f'APT{str(i+1).zfill(3)}',
            'reminder_type': 'initial',
            'scheduled_time': (datetime.now() + timedelta(hours=i+1)).isoformat(),
            'sent': False,
            'response': None,
            'created_at': datetime.now().isoformat()
        }
        reminders.append(reminder)
    
    with open("data/reminders.json", "w") as f:
        json.dump(reminders, f, indent=2)
    print("✅ Created sample reminders data")

def create_log_files():
    """Create empty log files"""
    log_files = ["email_log.txt", "sms_log.txt"]
    for log_file in log_files:
        with open(f"data/{log_file}", "w") as f:
            f.write(f"# {log_file} - Medical Scheduling Agent\n")
            f.write(f"# Created: {datetime.now().isoformat()}\n\n")
        print(f"✅ Created {log_file}")

def main():
    """Main setup function"""
    print("🚀 Setting up data for Medical Scheduling Agent...")
    
    try:
        create_data_directory()
        create_sample_patients()
        create_sample_doctors()
        create_sample_appointments()
        create_sample_reminders()
        create_log_files()
        
        print("\n🎉 Data setup completed successfully!")
        print("📁 All data files created in the 'data/' directory")
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        raise

if __name__ == "__main__":
    main()
