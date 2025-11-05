"""
Simplified Medical Appointment Scheduling AI Agent - Fixed for Perplexity API
"""
import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
import re

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from perplexity_integration import PerplexityLLM

from models import Patient, PatientType, Insurance, Appointment, AppointmentStatus
from database import DatabaseManager
from tools import get_all_tools
from emr_database import EMRDatabase
from config import Config

class SimpleMedicalSchedulingAgent:
    """Simplified Medical Appointment Scheduling AI Agent"""
    
    def __init__(self, api_key: str = None):
        # Use the provided API key or the hardcoded one
        api_key = api_key 
        
        # Try Perplexity first, fallback to OpenAI if needed
        if api_key and api_key != "your_perplexity_api_key_here":
            self.llm = PerplexityLLM(api_key=api_key)
            self.llm_type = "perplexity"
        else:
            # Fallback to OpenAI if Perplexity not available
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                api_key=Config.OPENAI_API_KEY,
                temperature=0.1
            )
            self.llm_type = "openai"
        
        self.db = DatabaseManager()
        self.emr_db = EMRDatabase()
        self.tools = get_all_tools()
        self.tool_lookup = {tool.name: tool for tool in self.tools}
        
        # Conversation state
        self.conversation_history = []
        self.current_step = "greeting"
        self.collected_data = {}
        
        # System prompt
        self.system_prompt = """You are a medical appointment scheduling AI assistant following MVP-1 requirements.

        CORE FEATURES (MVP-1):
        1. Patient Greeting: Collect name, DOB, Phone, Email, doctor, location
        2. Patient Lookup: Search EMR, automatically detect new vs returning patient
        3. Smart Scheduling: 60min (new) vs 30min (returning) - auto-assign based on EMR
        4. Calendar Integration: Show available slots
        5. Insurance Collection: Capture carrier, member ID, group
        6. Appointment Confirmation: Export to Excel, send confirmations
        7. Form Distribution: Email intake forms after confirmation
        8. Reminder System: 3 automated reminders with specific actions

        WORKFLOW:
        1. Greet and collect: Name, DOB, Phone, Email, Doctor preference, Location
        2. Use smart_patient_lookup to automatically detect new vs returning
        3. Use smart_scheduling to auto-assign duration (60min new, 30min returning)
        4. Show available calendar slots
        5. Collect insurance: Carrier, Member ID, Group
        6. Book the appointment
        7. Send immediate email and SMS confirmations
        8. Export to Excel automatically
        9. Send intake forms immediately
        10. Schedule 3-tier reminders automatically

        RULES:
        - NEVER ask if patient is new or returning - detect automatically from EMR
        - ALWAYS collect insurance details (carrier, member ID, group) - this is MANDATORY
        - Auto-assign appointment duration based on EMR detection
        - Be direct and professional
        - Follow MVP-1 requirements exactly
        - When asking for insurance, be very clear: "I need your insurance information: Insurance Carrier, Member ID, and Group Number"
        - Don't proceed with booking until ALL information is collected including insurance"""
    
    def process_message(self, message: str) -> str:
        """Process a user message and return AI response"""
        try:
            # Add user message to conversation history
            self.conversation_history.append(HumanMessage(content=message))
            
            # Process the response to extract information and update state first
            self._extract_information(message)
            
            # Check if we have complete booking info and should trigger booking immediately
            if self._has_complete_booking_info():
                # Show EMR lookup process
                emr_lookup_result = self._perform_emr_lookup()
                booking_result = self._handle_appointment_booking()
                return f"✅ Perfect! I have all your information. Let me check our records and book your appointment now.\n\n{emr_lookup_result}\n\n{booking_result}"
            
            # Check if we have basic info to show available slots (only if not selecting appointment)
            
            # Build messages for API call
            messages = [SystemMessage(content=self.system_prompt)]
            
            # Add conversation history (ensuring proper alternation)
            for msg in self.conversation_history:
                messages.append(msg)
            
            # Get AI response with fallback
            try:
                # Try API call
                response = self.llm.invoke(messages)
                ai_message = response.content if hasattr(response, 'content') else str(response)
                
                # Check if the response contains tool usage requests
                ai_message = self._check_and_execute_tools(ai_message, message)
                
            except Exception as api_error:
                # Fallback to a simple rule-based response if API fails
                ai_message = self._get_fallback_response(message)
                print(f"API Error, using fallback: {api_error}")
            
            # Add AI response to conversation history
            self.conversation_history.append(AIMessage(content=ai_message))
            
            return ai_message
            
        except Exception as e:
            # Always return a response, even if there's an error
            error_message = f"I'm here to help you schedule an appointment. Please provide: Name, DOB, Phone, Email, Doctor preference, and Location."
            self.conversation_history.append(AIMessage(content=error_message))
            return error_message
    
    def _check_and_execute_tools(self, ai_message: str, user_message: str) -> str:
        """Check if the user message requires tool execution and execute if needed"""
        message_lower = user_message.lower()
        
        
        # Check for export requests
        if any(word in message_lower for word in ["export", "excel", "download"]):
            export_result = self._handle_export_request()
            return f"{ai_message}\n\n{export_result}"
        
        # Check for reminder requests
        elif any(word in message_lower for word in ["reminder", "remind", "notification", "send reminder"]):
            reminder_result = self._handle_reminder_request()
            return f"{ai_message}\n\n{reminder_result}"
        
        # Check for booking requests
        elif any(word in message_lower for word in ["book", "schedule", "appointment", "confirm"]):
            booking_result = self._handle_appointment_booking()
            return f"{ai_message}\n\n{booking_result}"
        
        # Auto-trigger booking if we have enough information
        elif self._has_complete_booking_info():
            booking_result = self._handle_appointment_booking()
            return f"{ai_message}\n\n{booking_result}"
        
        return ai_message
    
    def _has_complete_booking_info(self) -> bool:
        """Check if we have enough information to automatically book an appointment"""
        # MVP-1 requirements: Name, DOB, Phone, Email, Doctor preference, Location, Selected Slot, Insurance
        required_fields = ["first_name", "date_of_birth", "phone", "email", "doctor_preference", "location", "selected_slot", "insurance_carrier"]
        return all(self.collected_data.get(field) for field in required_fields)
    
    def _perform_emr_lookup(self) -> str:
        """Perform EMR lookup and return user-friendly result"""
        try:
            # Get phone and email from collected data
            phone = self.collected_data.get("phone")
            email = self.collected_data.get("email")
            first_name = self.collected_data.get("first_name")
            last_name = self.collected_data.get("last_name", "Patient")
            
            # Perform EMR lookup
            patient_record, patient_type = self.emr_db.detect_patient_type(
                phone=phone, email=email, 
                first_name=first_name,
                last_name=last_name
            )
            
            # Get smart duration
            duration = self.emr_db.get_smart_duration(patient_record, patient_type)
            
            # Format result for user
            if patient_record:
                return f"🔍 **EMR Lookup Complete:**\nFound existing patient record for {patient_record.get('first_name', '')} {patient_record.get('last_name', '')}\n✅ **Patient Type:** {patient_type.title()}\n📅 **Appointment Duration:** {duration} minutes"
            else:
                return f"🔍 **EMR Lookup Complete:**\nNo existing record found in our system\n✅ **Patient Type:** {patient_type.title()}\n📅 **Appointment Duration:** {duration} minutes"
                
        except Exception as e:
            return f"⚠️ EMR lookup completed with default settings (60 minutes for new patient)"
    
    
    
    def _get_fallback_response(self, message: str) -> str:
        """Provide a fallback response when API is unavailable"""
        message_lower = message.lower()
        
        # FIRST: Extract information and check if we have complete booking info
        self._extract_information(message)
        if self._has_complete_booking_info():
            booking_result = self._handle_appointment_booking()
            return f"✅ Perfect! I have all your information. Let me book your appointment now.\n\n{booking_result}"
        
        # Check for tool usage requests
        if any(word in message_lower for word in ["export", "excel", "download"]):
            return self._handle_export_request()
        
        elif any(word in message_lower for word in ["reminder", "remind", "notification"]):
            return self._handle_reminder_request()
        
        elif any(word in message_lower for word in ["book", "schedule", "appointment"]):
            return self._handle_appointment_booking()
        
        
        # Check if we have basic info but need to show available slots
        if (self.collected_data.get("first_name") and 
            self.collected_data.get("date_of_birth") and 
            self.collected_data.get("phone") and 
            self.collected_data.get("email") and 
            self.collected_data.get("doctor_preference") and 
            self.collected_data.get("location") and 
            not self.collected_data.get("selected_slot")):
            return self._show_available_slots()
        
        # Check if we have most information but missing insurance
        if (self.collected_data.get("first_name") and 
            self.collected_data.get("date_of_birth") and 
            self.collected_data.get("phone") and 
            self.collected_data.get("email") and 
            self.collected_data.get("doctor_preference") and 
            self.collected_data.get("location") and 
            self.collected_data.get("selected_slot") and
            not self.collected_data.get("insurance_carrier")):
            return "✅ Perfect! I have all your basic information and selected time slot.\n\n📋 **INSURANCE INFORMATION REQUIRED:**\nI need your insurance details to complete the booking:\n• Insurance Carrier (e.g., Blue Cross, Aetna, Cigna)\n• Member ID\n• Group Number\n\nPlease provide all three pieces of information so I can book your appointment and send confirmations."
        
        # Check if this is a repetitive greeting (prevent loops)
        if len(self.conversation_history) > 2:
            # If we've had multiple exchanges, be more specific
            if any(word in message_lower for word in ["hello", "hi", "hey", "start"]):
                return "I'm still here to help! What information do you need to provide next?"
        
        # Check if we have complete booking info and should trigger booking immediately
        if self._has_complete_booking_info():
            booking_result = self._handle_appointment_booking()
            return f"✅ Perfect! I have all your information. Let me book your appointment now.\n\n{booking_result}"
        
        
        # MVP-1 compliant responses
        elif any(word in message_lower for word in ["hello", "hi", "hey", "start"]):
            return "🏥 **Welcome to Medical Appointment Scheduling!**\n\nI'll help you book an appointment quickly. Here's what I need:\n\n**📋 REQUIRED INFORMATION:**\n• Full name\n• Date of birth\n• Phone number\n• Email address\n• Doctor preference\n• Location preference\n• **Insurance details** (Carrier, Member ID, Group Number)\n\nPlease start by providing your name and date of birth."
        
        elif any(word in message_lower for word in ["name", "i'm", "i am", "my name"]):
            if not self.collected_data.get("first_name"):
                return "Thank you. I need: DOB, Phone, Email, Doctor preference, and Location."
            else:
                return "I have your name. What other information do you need to provide?"
        
        elif any(word in message_lower for word in ["birth", "born", "dob"]):
            if not self.collected_data.get("date_of_birth"):
                return "Got it. Need: Phone, Email, Doctor preference, and Location."
            else:
                return "I have your DOB. What other information do you need to provide?"
        
        elif any(word in message_lower for word in ["phone", "number", "call", "mobile"]):
            if not self.collected_data.get("phone"):
                return "Thanks. Need: Email, Doctor preference, and Location."
            else:
                return "I have your phone number. What other information do you need to provide?"
        
        elif any(word in message_lower for word in ["email", "mail", "@"]):
            if not self.collected_data.get("email"):
                return "Good. Need: Doctor preference and Location."
            else:
                return "I have your email. What other information do you need to provide?"
        
        elif any(word in message_lower for word in ["doctor", "physician", "specialist"]):
            if not self.collected_data.get("doctor_preference"):
                return "Thanks. Just need your Location."
            else:
                return "I have your doctor preference. What other information do you need to provide?"
        
        elif any(word in message_lower for word in ["location", "address", "city", "where"]):
            if not self.collected_data.get("location"):
                return "Perfect! Now I need your insurance details: Carrier, Member ID, and Group number."
            else:
                return "I have your location. Now I need your insurance details: Carrier, Member ID, and Group number."
        
        
        
        # Handle slot selection
        elif any(word in message_lower for word in ["select", "choose", "pick", "slot", "time", "9:", "10:", "11:", "2:", "3:", "4:", "5:", "am", "pm", "morning", "afternoon", "evening"]) and self.collected_data.get("doctor_preference") and self.collected_data.get("location"):
            # Extract slot selection from message
            selected_slot = self._extract_slot_selection(message)
            if selected_slot:
                self.collected_data["selected_slot"] = selected_slot
                return f"✅ Great! You've selected: {selected_slot}\n\nNow I need your insurance information: Carrier, Member ID, and Group number."
            else:
                return "I need you to specify which time slot you'd like. Please tell me the exact time (e.g., '9:00 AM' or '2:00 PM')."
        
        elif any(word in message_lower for word in ["insurance", "coverage", "payment"]):
            if not self.collected_data.get("insurance_carrier"):
                return "I need your insurance details: Carrier, Member ID, and Group number. Once you provide this, I'll automatically book your appointment and send confirmations."
            else:
                return "I have your insurance information. Let me book your appointment now!"
        
        elif any(word in message_lower for word in ["wait", "moment", "retrieve", "slots", "looking", "searching"]):
            # Handle the case where system is looking up records
            if self._has_complete_booking_info():
                booking_result = self._handle_appointment_booking()
                return f"✅ I've found your records and scheduled your appointment!\n\n{booking_result}"
            else:
                return "I'm checking our system for available slots. Please provide your insurance details to complete the booking."
        
        else:
            # Check what information we still need
            missing_info = []
            if not self.collected_data.get("first_name"):
                missing_info.append("Name")
            if not self.collected_data.get("date_of_birth"):
                missing_info.append("DOB")
            if not self.collected_data.get("phone"):
                missing_info.append("Phone")
            if not self.collected_data.get("email"):
                missing_info.append("Email")
            if not self.collected_data.get("doctor_preference"):
                missing_info.append("Doctor preference")
            if not self.collected_data.get("location"):
                missing_info.append("Location")
            if not self.collected_data.get("insurance_carrier"):
                missing_info.append("Insurance details (Carrier, Member ID, Group)")
            
            if missing_info:
                if len(missing_info) == 1 and "Insurance details" in missing_info[0]:
                    return "Perfect! I have all your basic information. Now I need your insurance details: Carrier, Member ID, and Group number. Once you provide this, I'll automatically book your appointment and send confirmations."
                else:
                    return f"I still need: {', '.join(missing_info)}. Please provide the missing information."
            else:
                return "I have all your information! Let me book your appointment now."
    
    def _handle_export_request(self) -> str:
        """Handle Excel export requests"""
        try:
            export_tool = self.tool_lookup.get("export_appointments")
            if export_tool:
                result = export_tool._run()
                if result.startswith("SUCCESS"):
                    return "✅ Your appointment has been exported to Excel successfully! The file has been saved to the data directory."
                else:
                    return f"❌ There was an issue exporting to Excel: {result}"
            else:
                return "❌ Export tool not available. Please try again later."
        except Exception as e:
            return f"❌ Error exporting to Excel: {str(e)}"
    
    def _handle_reminder_request(self) -> str:
        """Handle reminder scheduling requests"""
        try:
            # Check if we have enough data to schedule reminders
            if not self.collected_data.get("first_name") or not self.collected_data.get("date_of_birth"):
                return "I need your name and appointment date to schedule reminders. Please provide your full name and when you'd like to schedule your appointment."
            
            # Create a test appointment for reminder scheduling
            from datetime import date, timedelta
            from models import Patient, Appointment, AppointmentStatus
            
            # Create patient object
            patient = Patient(
                id="TEMP001",
                first_name=self.collected_data.get("first_name", "Patient"),
                last_name=self.collected_data.get("last_name", "Name"),
                date_of_birth=date.today() - timedelta(days=365*30),  # Default age
                phone=self.collected_data.get("phone", "555-000-0000"),
                email=self.collected_data.get("email", "patient@example.com"),
                address="123 Main St",
                emergency_contact="Emergency Contact",
                emergency_phone="555-000-0001",
                patient_type="new"
            )
            
            # Create appointment object
            appointment = Appointment(
                id="APT001",
                patient_id="TEMP001",
                doctor_id="D001",
                appointment_date=date.today() + timedelta(days=1),
                appointment_time="10:00",
                duration=60,
                status=AppointmentStatus.SCHEDULED
            )
            
            # Schedule reminders
            reminder_tool = self.tool_lookup.get("schedule_reminders")
            if reminder_tool:
                result = reminder_tool._run(
                    appointment_id="APT001",
                    patient_id="TEMP001",
                    appointment_date="2025-09-04",
                    appointment_time="10:00"
                )
                if result.startswith("SUCCESS"):
                    return "✅ Reminders have been scheduled successfully! You'll receive SMS reminders 24 hours, 2 hours, and 1 hour before your appointment."
                else:
                    return f"❌ There was an issue scheduling reminders: {result}"
            else:
                return "❌ Reminder tool not available. Please try again later."
        except Exception as e:
            return f"❌ Error scheduling reminders: {str(e)}"
    
    def _handle_appointment_booking(self) -> str:
        """Handle appointment booking requests"""
        try:
            # Check if we have enough data
            required_fields = ["first_name", "date_of_birth", "phone"]
            missing_fields = [field for field in required_fields if not self.collected_data.get(field)]
            
            if missing_fields:
                return f"I need more information to book your appointment. Please provide: {', '.join(missing_fields)}"
            
            # Create patient and appointment
            from datetime import date, timedelta
            from models import Patient, Appointment, AppointmentStatus
            
            # Get email and phone from collected data
            email = self.collected_data.get("email")
            phone = self.collected_data.get("phone")
            
            # Replace example emails/phones with real ones if needed
            if email and "example" in email.lower():
                email = "shrivastavasaksham04@gmail.com"  # Use real email for testing
            if phone and "555" in phone:
                phone = "+919826145342"  # Use real phone for testing
            
            # Generate unique patient ID
            existing_patients = self.db.load_patients()
            patient_id = f"P{str(len(existing_patients) + 1).zfill(4)}"
            
            # Parse date of birth
            try:
                if "-" in self.collected_data.get("date_of_birth", ""):
                    dob = datetime.strptime(self.collected_data.get("date_of_birth"), '%Y-%m-%d').date()
                elif "/" in self.collected_data.get("date_of_birth", ""):
                    dob = datetime.strptime(self.collected_data.get("date_of_birth"), '%m/%d/%Y').date()
                else:
                    dob = date.today() - timedelta(days=365*30)  # Default age
            except:
                dob = date.today() - timedelta(days=365*30)  # Default age
            
            # Determine patient type using EMR
            print(f"🔍 EMR Lookup: Checking patient records for {self.collected_data.get('first_name')} {self.collected_data.get('last_name', 'Patient')}")
            print(f"   Phone: {phone}")
            print(f"   Email: {email}")
            
            patient_record, patient_type = self.emr_db.detect_patient_type(
                phone=phone, email=email, 
                first_name=self.collected_data.get("first_name"),
                last_name=self.collected_data.get("last_name", "Patient")
            )
            
            print(f"✅ EMR Result: Patient classified as '{patient_type}'")
            if patient_record:
                print(f"   Found existing record: {patient_record.get('first_name', '')} {patient_record.get('last_name', '')}")
            else:
                print(f"   No existing record found - new patient")
            
            # Get smart duration
            duration = self.emr_db.get_smart_duration(patient_record, patient_type)
            print(f"📅 Smart Scheduling: Assigned {duration} minutes ({'new patient' if patient_type == 'new' else 'returning patient'})")
            
            patient = Patient(
                id=patient_id,
                first_name=self.collected_data.get("first_name"),
                last_name=self.collected_data.get("last_name", "Patient"),
                date_of_birth=dob,
                phone=phone,
                email=self.collected_data.get("email", "patient@example.com"),
                address="123 Main St",
                emergency_contact="Emergency Contact",
                emergency_phone="555-000-0001",
                patient_type=patient_type
            )
            
            # Add patient to database
            self.db.add_new_patient(patient)
            
            # Generate unique appointment ID
            existing_appointments = self.db.load_appointments()
            appointment_id = f"APT{str(len(existing_appointments) + 1).zfill(4)}"
            
            appointment = Appointment(
                id=appointment_id,
                patient_id=patient_id,
                doctor_id="D001",
                appointment_date=date.today() + timedelta(days=1),
                appointment_time="10:00",
                duration=duration,
                status=AppointmentStatus.SCHEDULED
            )
            
            # Book appointment
            book_tool = self.tool_lookup.get("book_appointment")
            if book_tool:
                result = book_tool._run(
                    patient_id=patient_id,
                    doctor_id="D001",
                    appointment_date=appointment.appointment_date.strftime('%Y-%m-%d'),
                    appointment_time=appointment.appointment_time,
                    duration=duration,
                    insurance_carrier=self.collected_data.get("insurance_carrier"),
                    insurance_member_id=self.collected_data.get("member_id"),
                    insurance_group=self.collected_data.get("group_number")
                )
                if result.startswith("SUCCESS"):
                    # Send immediate communications (SMS + Email)
                    communication_result = self._send_immediate_communications(patient, appointment)
                    
                    # Automatically export to Excel after successful booking
                    export_result = self._handle_export_request()
                    
                    # Automatically schedule reminders after successful booking
                    reminder_result = self._handle_reminder_request()
                    
                    return f"""✅ Your appointment has been booked successfully! 

📱 **IMMEDIATE COMMUNICATIONS SENT:**
{communication_result}

📊 **AUTOMATIC ACTIONS COMPLETED:**
{export_result}

🔔 **REMINDER SYSTEM ACTIVATED:**
{reminder_result}"""
                else:
                    return f"❌ There was an issue booking your appointment: {result}"
            else:
                return "❌ Booking tool not available. Please try again later."
        except Exception as e:
            return f"❌ Error booking appointment: {str(e)}"
    
    def _send_immediate_communications(self, patient, appointment) -> str:
        """Send immediate SMS and email after appointment confirmation"""
        try:
            from communication import EmailService, SMSService
            
            print(f"🔍 DEBUG: Sending communications to {patient.email} and {patient.phone}")
            
            # Send immediate communications
            email_service = EmailService()
            sms_service = SMSService()
            
            # Send confirmation email
            print("📧 Sending confirmation email...")
            email_success = email_service.send_appointment_confirmation(patient, appointment)
            print(f"📧 Email result: {email_success}")
            
            # Send confirmation SMS
            print("📱 Sending confirmation SMS...")
            sms_message = f"Appointment confirmed for {appointment.appointment_date} at {appointment.appointment_time}. Confirmation email sent."
            sms_success = sms_service.send_sms(patient.phone, sms_message)
            print(f"📱 SMS result: {sms_success}")
            
            # Send intake forms
            print("📋 Sending intake forms...")
            forms_success = email_service.send_intake_forms(patient, appointment)
            print(f"📋 Forms result: {forms_success}")
            
            results = []
            if email_success:
                results.append("✅ Confirmation email sent")
            if sms_success:
                results.append("✅ Confirmation SMS sent")
            if forms_success:
                results.append("✅ Intake forms sent")
            
            return "\n".join(results) if results else "⚠️ Some communications failed to send"
            
        except Exception as e:
            return f"❌ Error sending communications: {str(e)}"
    
    def _extract_information(self, user_message: str):
        """Extract information from user message and update state"""
        message_lower = user_message.lower()
        
        # Check if this is a comma-separated format (like "Name, DOB, Phone, Email, Doctor, Location")
        if "," in user_message and user_message.count(",") >= 4:
            parts = [part.strip() for part in user_message.split(",")]
            if len(parts) >= 6:
                # Extract from comma-separated format
                self.collected_data["first_name"] = parts[0].split()[0] if parts[0] else ""
                self.collected_data["last_name"] = parts[0].split()[-1] if len(parts[0].split()) > 1 else ""
                self.collected_data["date_of_birth"] = parts[1] if parts[1] else ""
                
                # Extract phone from parts[2]
                phone_part = parts[2] if parts[2] else ""
                phone_match = re.search(r'(\+?\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4})', phone_part)
                if phone_match:
                    self.collected_data["phone"] = re.sub(r'[^\d]', '', phone_match.group(1))
                
                # Extract email from parts[3]
                email_part = parts[3] if parts[3] else ""
                if "@" in email_part:
                    self.collected_data["email"] = email_part
                
                self.collected_data["doctor_preference"] = parts[4] if parts[4] else ""
                self.collected_data["location"] = parts[5] if parts[5] else ""
                return  # Skip individual extraction if we found comma-separated format
        
        # Handle special case where phone and email are in same field without comma
        # Pattern: "Name, DOB, Phone Email, Doctor, Location"
        if "," in user_message and user_message.count(",") >= 4:
            parts = [part.strip() for part in user_message.split(",")]
            if len(parts) >= 5:
                # Check if parts[2] contains both phone and email
                phone_email_part = parts[2] if parts[2] else ""
                if "@" in phone_email_part and re.search(r'\d', phone_email_part):
                    # Extract from this special format
                    self.collected_data["first_name"] = parts[0].split()[0] if parts[0] else ""
                    self.collected_data["last_name"] = parts[0].split()[-1] if len(parts[0].split()) > 1 else ""
                    self.collected_data["date_of_birth"] = parts[1] if parts[1] else ""
                    
                    # Extract phone and email from the combined field
                    phone_match = re.search(r'(\+?\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4})', phone_email_part)
                    if phone_match:
                        self.collected_data["phone"] = re.sub(r'[^\d]', '', phone_match.group(1))
                    
                    email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', phone_email_part)
                    if email_match:
                        self.collected_data["email"] = email_match.group(1)
                    
                    self.collected_data["doctor_preference"] = parts[3] if parts[3] else ""
                    self.collected_data["location"] = parts[4] if parts[4] else ""
                    return  # Skip individual extraction if we found this special format
        
        # Handle case where phone and email are in same field with comma but no space
        # Pattern: "Name, DOB, Phone,Email, Doctor, Location"
        if "," in user_message and user_message.count(",") >= 4:
            parts = [part.strip() for part in user_message.split(",")]
            if len(parts) >= 6:
                # Check if parts[2] and parts[3] are phone and email but parts[2] might contain email too
                phone_part = parts[2] if parts[2] else ""
                email_part = parts[3] if parts[3] else ""
                
                # If phone_part contains email, extract both from it
                if "@" in phone_part and re.search(r'\d', phone_part):
                    phone_match = re.search(r'(\+?\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4})', phone_part)
                    if phone_match:
                        self.collected_data["phone"] = re.sub(r'[^\d]', '', phone_match.group(1))
                    
                    email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', phone_part)
                    if email_match:
                        self.collected_data["email"] = email_match.group(1)
                else:
                    # Normal case - phone in parts[2], email in parts[3]
                    phone_match = re.search(r'(\+?\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4})', phone_part)
                    if phone_match:
                        self.collected_data["phone"] = re.sub(r'[^\d]', '', phone_match.group(1))
                    
                    # Extract email from email_part
                    if "@" in email_part:
                        self.collected_data["email"] = email_part
                    elif "@" in phone_part:
                        # Email might be in phone_part even if no digits
                        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', phone_part)
                        if email_match:
                            self.collected_data["email"] = email_match.group(1)
                
                # Extract other fields
                self.collected_data["first_name"] = parts[0].split()[0] if parts[0] else ""
                self.collected_data["last_name"] = parts[0].split()[-1] if len(parts[0].split()) > 1 else ""
                self.collected_data["date_of_birth"] = parts[1] if parts[1] else ""
                self.collected_data["doctor_preference"] = parts[4] if parts[4] else ""
                self.collected_data["location"] = parts[5] if parts[5] else ""
                
                # Ensure email is extracted
                if not self.collected_data.get("email") and "@" in email_part:
                    self.collected_data["email"] = email_part
                
                return  # Skip individual extraction if we found this format
        
        # Extract name
        if "my name is" in message_lower or "i'm" in message_lower:
            name_match = re.search(r"(?:my name is|i'm|i am)\s+([a-zA-Z\s]+)", user_message, re.IGNORECASE)
            if name_match:
                full_name = name_match.group(1).strip()
                name_parts = full_name.split()
                if len(name_parts) >= 2:
                    self.collected_data["first_name"] = name_parts[0]
                    self.collected_data["last_name"] = name_parts[-1]
        
        # Extract date of birth
        dob_patterns = [
            r"(\d{4}-\d{2}-\d{2})",
            r"(\d{1,2}/\d{1,2}/\d{4})",
            r"(\d{1,2}-\d{1,2}-\d{4})"
        ]
        for pattern in dob_patterns:
            dob_match = re.search(pattern, user_message)
            if dob_match:
                self.collected_data["date_of_birth"] = dob_match.group(1)
                break
        
        # Extract year of birth (for "born in 1990" patterns)
        if "born in" in message_lower:
            year_match = re.search(r"born in (\d{4})", message_lower)
            if year_match:
                year = year_match.group(1)
                # Convert to approximate date of birth
                self.collected_data["date_of_birth"] = f"{year}-01-01"
        
        # Extract phone number
        phone_match = re.search(r"(\d{3}[-.]?\d{3}[-.]?\d{4})", user_message)
        if phone_match:
            phone = re.sub(r'[^\d]', '', phone_match.group(1))
            if len(phone) == 10:
                self.collected_data["phone"] = phone
        
        # Extract email
        email_match = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", user_message)
        if email_match and not self.collected_data.get("email"):
            self.collected_data["email"] = email_match.group(1)
        
        # Extract doctor preference
        if "doctor" in message_lower or "dr." in message_lower or "physician" in message_lower:
            doctor_match = re.search(r"(?:doctor|dr\.?|physician)\s+([a-zA-Z\s]+)", user_message, re.IGNORECASE)
            if doctor_match:
                self.collected_data["doctor_preference"] = doctor_match.group(1).strip()
        
        # Extract location
        location_keywords = ["in", "from", "location", "city", "address"]
        for keyword in location_keywords:
            if keyword in message_lower:
                # Simple location extraction - look for common city names or "in [location]"
                location_match = re.search(rf"{keyword}\s+([a-zA-Z\s]+)", user_message, re.IGNORECASE)
                if location_match:
                    self.collected_data["location"] = location_match.group(1).strip()
                    break
        
        # Extract insurance information - improved pattern matching
        if "carrier" in message_lower or "insurance" in message_lower or "aetna" in message_lower or "blue cross" in message_lower or "cigna" in message_lower or "humana" in message_lower:
            if "blue cross" in message_lower or "bcbs" in message_lower:
                self.collected_data["insurance_carrier"] = "Blue Cross Blue Shield"
            elif "aetna" in message_lower:
                self.collected_data["insurance_carrier"] = "Aetna"
            elif "cigna" in message_lower:
                self.collected_data["insurance_carrier"] = "Cigna"
            elif "humana" in message_lower:
                self.collected_data["insurance_carrier"] = "Humana"
        
        # Extract member ID - improved patterns to handle various formats
        member_id_patterns = [
            r"member\s*id[:\s]*([a-zA-Z0-9]+)",
            r"member\s*id[:\s]*([a-zA-Z0-9]+)",
            r"member\s*id[:\s]*([a-zA-Z0-9]+)",
            r"id[:\s]*([a-zA-Z0-9]+)",  # Just "ID: ABC123456789"
            r"([a-zA-Z0-9]{8,})"  # Any alphanumeric string 8+ chars
        ]
        for pattern in member_id_patterns:
            member_id_match = re.search(pattern, message_lower)
            if member_id_match:
                self.collected_data["member_id"] = member_id_match.group(1)
                break
        
        # Extract group number - improved patterns
        group_patterns = [
            r"group\s*number[:\s]*(\d+)",
            r"group[:\s]*(\d+)",
            r"group\s*(\d+)",
            r"number[:\s]*(\d{6,})"  # Just "Number: 654321"
        ]
        for pattern in group_patterns:
            group_match = re.search(pattern, message_lower)
            if group_match:
                self.collected_data["group_number"] = group_match.group(1)
                break
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history in a format suitable for display"""
        history = []
        for msg in self.conversation_history:
            if isinstance(msg, HumanMessage):
                history.append({"content": msg.content, "is_user": True})
            elif isinstance(msg, AIMessage):
                history.append({"content": msg.content, "is_user": False})
        return history
    
    def reset_conversation(self):
        """Reset the conversation state"""
        self.conversation_history = []
        self.current_step = "greeting"
        self.collected_data = {}
    
    def get_conversation_state(self):
        """Get current conversation state for debugging"""
        return {
            "conversation_length": len(self.conversation_history),
            "current_step": self.current_step,
            "collected_data": self.collected_data,
            "has_complete_info": self._has_complete_booking_info()
        }
    
    def get_collected_data(self) -> Dict[str, Any]:
        """Get the collected patient data"""
        return self.collected_data.copy()
    
    def set_collected_data(self, data: Dict[str, Any]):
        """Set collected patient data"""
        self.collected_data.update(data)
    
    def _show_available_slots(self) -> str:
        """Show available appointment slots"""
        from datetime import datetime, timedelta
        
        # Generate available slots for the next 7 days
        today = datetime.now().date()
        slots = []
        
        for i in range(7):
            current_date = today + timedelta(days=i)
            if current_date.weekday() < 5:  # Monday to Friday
                # Morning slots
                for hour in [9, 10, 11]:
                    slot_time = datetime(current_date.year, current_date.month, current_date.day, hour, 0)
                    slots.append({
                        "date": current_date.strftime("%A, %B %d"),
                        "time": slot_time.strftime("%I:%M %p"),
                        "slot_id": f"slot_{i}_{hour}"
                    })
                # Afternoon slots
                for hour in [14, 15, 16]:
                    slot_time = datetime(current_date.year, current_date.month, current_date.day, hour, 0)
                    slots.append({
                        "date": current_date.strftime("%A, %B %d"),
                        "time": slot_time.strftime("%I:%M %p"),
                        "slot_id": f"slot_{i}_{hour}"
                    })
        
        if not slots:
            return "No available slots found. Please contact us directly to schedule your appointment."
        
        # Format the response
        response = "📅 **Available Appointment Slots:**\n\n"
        
        # Group slots by date
        slots_by_date = {}
        for slot in slots:
            date = slot["date"]
            if date not in slots_by_date:
                slots_by_date[date] = []
            slots_by_date[date].append(slot)
        
        # Display slots by date
        for date in sorted(slots_by_date.keys()):
            response += f"**{date}:**\n"
            for slot in slots_by_date[date]:
                response += f"  • {slot['time']} (Slot ID: {slot['slot_id']})\n"
            response += "\n"
        
        response += "Please select a time slot by telling me the time (e.g., '9:00 AM' or '2:00 PM') or the slot ID."
        
        return response
    
    def _extract_slot_selection(self, message: str) -> str:
        """Extract slot selection from user message"""
        import re
        from datetime import datetime
        
        # Look for time patterns like "9:00 AM", "2:30 PM", etc.
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)',
            r'(\d{1,2}):(\d{2})',
            r'(\d{1,2})\s*(AM|PM|am|pm)',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(0)
        
        # Look for slot ID patterns
        slot_id_pattern = r'slot_\d+_\d+'
        slot_match = re.search(slot_id_pattern, message.lower())
        if slot_match:
            return slot_match.group(0)
        
        # Look for common time expressions
        time_expressions = {
            'morning': '9:00 AM',
            'afternoon': '2:00 PM', 
            'evening': '4:00 PM',
            'first slot': '9:00 AM',
            'second slot': '10:00 AM',
            'third slot': '11:00 AM',
            'lunch time': '12:00 PM',
            'after lunch': '2:00 PM',
            'last slot': '4:00 PM'
        }
        
        message_lower = message.lower()
        for expr, time in time_expressions.items():
            if expr in message_lower:
                return time
        
        return None
    
