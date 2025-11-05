"""
Configuration settings for the Medical Appointment Scheduling AI Agent
"""
import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
try:
    load_dotenv()
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")
    print("Using default environment variables")

class Config:
    # Helper method to get secrets from Streamlit or environment
    @staticmethod
    def get_secret(key: str, default: str = "") -> str:
        """Get secret from Streamlit secrets or environment variable"""
        try:
            # Try Streamlit secrets first (for deployed apps)
            if hasattr(st, 'secrets') and key in st.secrets:
                return st.secrets[key]
        except:
            pass
        
        # Fallback to environment variables
        return os.getenv(key, default)
    
    # AI Model Configuration
    OPENAI_API_KEY = get_secret("OPENAI_API_KEY", "your_openai_api_key_here")
    PERPLEXITY_API_KEY = get_secret("PERPLEXITY_API_KEY", "your_perplexity_api_key_here")
    
    
    # Email Configuration
    SMTP_SERVER = get_secret("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(get_secret("SMTP_PORT", "587"))
    EMAIL_USERNAME = get_secret("EMAIL_USERNAME", "your_email@gmail.com")
    EMAIL_PASSWORD = get_secret("EMAIL_PASSWORD", "your_app_password")
    
    # SMS Configuration (Twilio)
    TWILIO_ACCOUNT_SID = get_secret("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = get_secret("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER = get_secret("TWILIO_PHONE_NUMBER", "")
    TWILIO_WEBHOOK_URL = get_secret("TWILIO_WEBHOOK_URL", "")
    
    # Webhook Configuration
    WEBHOOK_PORT = int(get_secret("WEBHOOK_PORT", "5000"))
    
    # Application Configuration
    DEBUG = get_secret("DEBUG", "True").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # File Paths
    DATA_DIR = "data"
    PATIENTS_CSV = os.path.join(DATA_DIR, "patients.csv")
    DOCTORS_SCHEDULE = os.path.join(DATA_DIR, "doctors_schedule.xlsx")
    APPOINTMENTS_JSON = os.path.join(DATA_DIR, "appointments.json")
    REMINDERS_JSON = os.path.join(DATA_DIR, "reminders.json")
    
    # Business Rules
    NEW_PATIENT_DURATION = 60  # minutes
    RETURNING_PATIENT_DURATION = 30  # minutes
    REMINDER_HOURS = [24, 2, 1]  # hours before appointment
    
    # Calendar Settings
    WORKING_HOURS_START = 9  # 9 AM
    WORKING_HOURS_END = 17   # 5 PM
    LUNCH_BREAK_START = 12   # 12 PM
    LUNCH_BREAK_END = 13     # 1 PM
