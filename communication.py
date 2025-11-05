"""
Communication system for form distribution and reminders
"""
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
import schedule
import time
import threading
from twilio.rest import Client

from models import Patient, Appointment, Reminder, ReminderType
from database import DatabaseManager
from config import Config

class EmailService:
    """Enhanced email service for sending forms and reminders with automation"""
    
    def __init__(self):
        self.smtp_server = Config.SMTP_SERVER
        self.smtp_port = Config.SMTP_PORT
        self.email_username = Config.EMAIL_USERNAME
        self.email_password = Config.EMAIL_PASSWORD
        self.email_log_file = "data/email_log.txt"
        os.makedirs("data", exist_ok=True)
        
        # Email templates
        self.templates = {
            'appointment_confirmation': self._get_appointment_confirmation_template(),
            'appointment_reminder': self._get_appointment_reminder_template(),
            'intake_forms': self._get_intake_forms_template(),
            'cancellation': self._get_cancellation_template(),
            'reschedule': self._get_reschedule_template()
        }
    
    def _get_appointment_confirmation_template(self) -> str:
        """Get appointment confirmation email template"""
        return """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                <h2 style="color: #2c3e50; text-align: center;">Appointment Confirmation</h2>
                <p>Dear {patient_name},</p>
                
                <p>Your appointment has been successfully scheduled:</p>
                
                <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <ul style="list-style: none; padding: 0;">
                        <li><strong>Appointment ID:</strong> {appointment_id}</li>
                        <li><strong>Date:</strong> {appointment_date}</li>
                        <li><strong>Time:</strong> {appointment_time}</li>
                        <li><strong>Duration:</strong> {duration} minutes</li>
                    </ul>
                </div>
                
                <p><strong>Important Reminders:</strong></p>
                <ul>
                    <li>Please arrive 15 minutes early for your appointment</li>
                    <li>Bring a valid ID and insurance card</li>
                    <li>Complete any intake forms before your visit</li>
                </ul>
                
                <p>If you need to reschedule or cancel, please contact us at least 24 hours in advance.</p>
                
                <p style="margin-top: 30px;">Best regards,<br>
                <strong>Medical Scheduling Team</strong></p>
            </div>
        </body>
        </html>
        """
    
    def _get_appointment_reminder_template(self) -> str:
        """Get appointment reminder email template"""
        return """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #fff3cd; padding: 20px; border-radius: 10px; border-left: 5px solid #ffc107;">
                <h2 style="color: #856404; text-align: center;">Appointment Reminder</h2>
                <p>Dear {patient_name},</p>
                
                <p>This is a friendly reminder about your upcoming appointment:</p>
                
                <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <ul style="list-style: none; padding: 0;">
                        <li><strong>Appointment ID:</strong> {appointment_id}</li>
                        <li><strong>Date:</strong> {appointment_date}</li>
                        <li><strong>Time:</strong> {appointment_time}</li>
                        <li><strong>Duration:</strong> {duration} minutes</li>
                    </ul>
                </div>
                
                <p><strong>Please confirm your attendance by replying to this email or calling us.</strong></p>
                
                <p>If you need to reschedule or cancel, please contact us as soon as possible.</p>
                
                <p style="margin-top: 30px;">Best regards,<br>
                <strong>Medical Scheduling Team</strong></p>
            </div>
        </body>
        </html>
        """
    
    def _get_intake_forms_template(self) -> str:
        """Get intake forms email template"""
        return """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #d1ecf1; padding: 20px; border-radius: 10px; border-left: 5px solid #17a2b8;">
                <h2 style="color: #0c5460; text-align: center;">Patient Intake Forms</h2>
                <p>Dear {patient_name},</p>
                
                <p>Please find attached the intake forms for your upcoming appointment on <strong>{appointment_date}</strong> at <strong>{appointment_time}</strong>.</p>
                
                <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <p><strong>Required Actions:</strong></p>
                    <ol>
                        <li>Complete the "New Patient Intake Form.pdf"</li>
                        <li>Review and complete any additional forms</li>
                        <li>Email completed forms back to us at least 24 hours before your appointment</li>
                    </ol>
                </div>
                
                <p><strong>Important:</strong> The personalized form contains your appointment details and specific instructions for completing the intake process.</p>
                
                <p>If you have any questions about the forms, please don't hesitate to contact us.</p>
                
                <p style="margin-top: 30px;">Best regards,<br>
                <strong>Medical Scheduling Team</strong></p>
            </div>
        </body>
        </html>
        """
    
    def _get_cancellation_template(self) -> str:
        """Get cancellation email template"""
        return """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8d7da; padding: 20px; border-radius: 10px; border-left: 5px solid #dc3545;">
                <h2 style="color: #721c24; text-align: center;">Appointment Cancellation</h2>
                <p>Dear {patient_name},</p>
                
                <p>We have received your request to cancel the following appointment:</p>
                
                <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <ul style="list-style: none; padding: 0;">
                        <li><strong>Appointment ID:</strong> {appointment_id}</li>
                        <li><strong>Date:</strong> {appointment_date}</li>
                        <li><strong>Time:</strong> {appointment_time}</li>
                    </ul>
                </div>
                
                <p>Your appointment has been cancelled. If you need to reschedule, please contact us at your earliest convenience.</p>
                
                <p style="margin-top: 30px;">Best regards,<br>
                <strong>Medical Scheduling Team</strong></p>
            </div>
        </body>
        </html>
        """
    
    def _get_reschedule_template(self) -> str:
        """Get reschedule email template"""
        return """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #d4edda; padding: 20px; border-radius: 10px; border-left: 5px solid #28a745;">
                <h2 style="color: #155724; text-align: center;">Appointment Rescheduled</h2>
                <p>Dear {patient_name},</p>
                
                <p>Your appointment has been successfully rescheduled:</p>
                
                <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <p><strong>Previous Appointment:</strong></p>
                    <ul style="list-style: none; padding: 0;">
                        <li><strong>Date:</strong> {old_date}</li>
                        <li><strong>Time:</strong> {old_time}</li>
                    </ul>
                    
                    <p><strong>New Appointment:</strong></p>
                    <ul style="list-style: none; padding: 0;">
                        <li><strong>Appointment ID:</strong> {appointment_id}</li>
                        <li><strong>Date:</strong> {appointment_date}</li>
                        <li><strong>Time:</strong> {appointment_time}</li>
                        <li><strong>Duration:</strong> {duration} minutes</li>
                    </ul>
                </div>
                
                <p>Please update your calendar with the new appointment time.</p>
                
                <p style="margin-top: 30px;">Best regards,<br>
                <strong>Medical Scheduling Team</strong></p>
            </div>
        </body>
        </html>
        """
    
    def send_email(self, to_email: str, subject: str, body: str, attachments: List[str] = None) -> bool:
        """Send real email with optional attachments"""
        try:
            # Check if email credentials are configured
            if not self.email_username or not self.email_password or self.email_username == "your_email@gmail.com":
                print("⚠️ Email credentials not configured, logging email to file")
                self._log_email_to_file(to_email, subject, body, attachments)
                return True
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'html'))
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(file_path)}'
                        )
                        msg.attach(part)
            
            # Send real email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_username, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_username, to_email, text)
            server.quit()
            
            print(f"✅ REAL EMAIL sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            # Log the failed email attempt
            self._log_email_to_file(to_email, subject, body, attachments, error=str(e))
            return False
    
    def _log_email_to_file(self, to_email: str, subject: str, body: str, attachments: List[str] = None, error: str = None):
        """Log email to file for debugging"""
        try:
            email_log_file = "data/email_log.txt"
            os.makedirs("data", exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"""
[{timestamp}] EMAIL {'(FAILED)' if error else '(SIMULATED)'}
To: {to_email}
Subject: {subject}
Body: {body[:200]}...
Attachments: {attachments if attachments else 'None'}
{'Error: ' + error if error else ''}
{'='*50}
"""
            
            with open(email_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
        except Exception as e:
            print(f"Error logging email: {e}")
    
    def send_appointment_confirmation(self, patient: Patient, appointment: Appointment) -> bool:
        """Send appointment confirmation email using template"""
        # Send email to any address (including example addresses for demo)
        print(f"📧 Sending appointment confirmation to: {patient.email}")
        
        subject = f"Appointment Confirmation - {appointment.id}"
        
        # Use template with patient and appointment data
        body = self.templates['appointment_confirmation'].format(
            patient_name=f"{patient.first_name} {patient.last_name}",
            appointment_id=appointment.id,
            appointment_date=appointment.appointment_date,
            appointment_time=appointment.appointment_time,
            duration=appointment.duration
        )
        
        return self.send_email(patient.email, subject, body)
    
    def _is_example_email(self, email: str) -> bool:
        """Check if email is an example/test email"""
        if not email:
            return True
        example_domains = ["example.com", "test.com", "demo.com", "sample.com", "yourdomain.com"]
        return any(domain in email.lower() for domain in example_domains)
    
    def send_appointment_reminder(self, patient: Patient, appointment: Appointment, reminder_type: str = "general") -> bool:
        """Send appointment reminder email using template"""
        subject = f"Appointment Reminder - {appointment.id}"
        
        body = self.templates['appointment_reminder'].format(
            patient_name=f"{patient.first_name} {patient.last_name}",
            appointment_id=appointment.id,
            appointment_date=appointment.appointment_date,
            appointment_time=appointment.appointment_time,
            duration=appointment.duration
        )
        
        return self.send_email(patient.email, subject, body)
    
    def send_cancellation_notification(self, patient: Patient, appointment: Appointment) -> bool:
        """Send appointment cancellation email using template"""
        subject = f"Appointment Cancelled - {appointment.id}"
        
        body = self.templates['cancellation'].format(
            patient_name=f"{patient.first_name} {patient.last_name}",
            appointment_id=appointment.id,
            appointment_date=appointment.appointment_date,
            appointment_time=appointment.appointment_time
        )
        
        return self.send_email(patient.email, subject, body)
    
    def send_reschedule_notification(self, patient: Patient, old_appointment: Appointment, new_appointment: Appointment) -> bool:
        """Send appointment reschedule email using template"""
        subject = f"Appointment Rescheduled - {new_appointment.id}"
        
        body = self.templates['reschedule'].format(
            patient_name=f"{patient.first_name} {patient.last_name}",
            appointment_id=new_appointment.id,
            old_date=old_appointment.appointment_date,
            old_time=old_appointment.appointment_time,
            appointment_date=new_appointment.appointment_date,
            appointment_time=new_appointment.appointment_time,
            duration=new_appointment.duration
        )
        
        return self.send_email(patient.email, subject, body)
    
    def send_appointment_reminder_email(self, patient: Patient, appointment: Appointment, reminder_type: ReminderType) -> bool:
        """Send appointment reminder email with specific actions"""
        if reminder_type == ReminderType.INITIAL:
            # 1st Reminder: Confirmation of appointment
            subject = f"📅 Appointment Confirmation - {appointment.id}"
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                    <h2 style="color: #2c3e50;">📅 Appointment Confirmation</h2>
                    <p>Dear {patient.first_name} {patient.last_name},</p>
                    
                    <p>Your appointment is scheduled for:</p>
                    <ul style="background-color: white; padding: 15px; border-radius: 5px;">
                        <li><strong>📅 Date:</strong> {appointment.appointment_date}</li>
                        <li><strong>⏰ Time:</strong> {appointment.appointment_time}</li>
                        <li><strong>🆔 Appointment ID:</strong> {appointment.id}</li>
                    </ul>
                    
                    <p><strong>Please confirm your attendance by replying to this email.</strong></p>
                    
                    <p>Best regards,<br>
                    Medical Scheduling Team</p>
                </div>
            </body>
            </html>
            """
        elif reminder_type == ReminderType.FORM_CHECK:
            # 2nd Reminder: Have they filled the forms?
            subject = f"📋 Form Completion Check - {appointment.id}"
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #fff3cd; padding: 20px; border-radius: 10px; border-left: 5px solid #ffc107;">
                    <h2 style="color: #856404;">📋 Form Completion Check</h2>
                    <p>Dear {patient.first_name} {patient.last_name},</p>
                    
                    <p>Your appointment is <strong>tomorrow at {appointment.appointment_time}</strong>.</p>
                    
                    <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                        <h3>❓ Have you completed your intake forms?</h3>
                        <p>Please reply to this email:</p>
                        <ul>
                            <li><strong>✅ YES</strong> - if forms are completed</li>
                            <li><strong>❌ NO</strong> - if forms are not completed</li>
                        </ul>
                    </div>
                    
                    <p>Best regards,<br>
                    Medical Scheduling Team</p>
                </div>
            </body>
            </html>
            """
        elif reminder_type == ReminderType.CONFIRMATION:
            # 3rd Reminder: Confirmation or cancellation with reason
            subject = f"🔔 Final Confirmation - {appointment.id}"
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #d1ecf1; padding: 20px; border-radius: 10px; border-left: 5px solid #17a2b8;">
                    <h2 style="color: #0c5460;">🔔 Final Confirmation</h2>
                    <p>Dear {patient.first_name} {patient.last_name},</p>
                    
                    <p>Your appointment is <strong>in 1 hour at {appointment.appointment_time}</strong>.</p>
                    
                    <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                        <h3>Please reply to this email:</h3>
                        <ul>
                            <li><strong>✅ CONFIRM</strong> - if you're coming</li>
                            <li><strong>❌ CANCEL</strong> - if you need to cancel (please mention reason)</li>
                        </ul>
                    </div>
                    
                    <p>Best regards,<br>
                    Medical Scheduling Team</p>
                </div>
            </body>
            </html>
            """
        else:
            subject = f"Appointment Reminder - {appointment.id}"
            body = f"Reminder: You have an appointment on {appointment.appointment_date} at {appointment.appointment_time}."
        
        return self.send_email(patient.email, subject, body)
    
    def send_intake_forms(self, patient: Patient, appointment: Appointment) -> bool:
        """Send intake forms after appointment confirmation using template"""
        # Send email to any address (including example addresses for demo)
        print(f"📧 Sending intake forms to: {patient.email}")
        
        subject = f"Intake Forms - Appointment {appointment.id}"
        
        # Use template with patient and appointment data
        body = self.templates['intake_forms'].format(
            patient_name=f"{patient.first_name} {patient.last_name}",
            appointment_date=appointment.appointment_date,
            appointment_time=appointment.appointment_time
        )
        
        # Create sample intake forms
        form_paths = self._create_sample_forms(patient, appointment)
        
        return self.send_email(patient.email, subject, body, form_paths)
    
    def send_bulk_emails(self, recipients: List[Dict[str, str]], template_type: str, subject: str, **template_data) -> Dict[str, bool]:
        """Send bulk emails using templates"""
        results = {}
        
        for recipient in recipients:
            email = recipient.get('email')
            name = recipient.get('name', 'Unknown')
            
            if email and template_type in self.templates:
                # Format template with recipient-specific data
                template_data['patient_name'] = name
                body = self.templates[template_type].format(**template_data)
                
                success = self.send_email(email, subject, body)
                results[f"{name} ({email})"] = success
            else:
                results[f"{name} (No email or invalid template)"] = False
        
        return results
    
    def _create_sample_forms(self, patient: Patient, appointment: Appointment) -> List[str]:
        """Create intake forms using the provided PDF template"""
        forms_dir = "data/forms"
        os.makedirs(forms_dir, exist_ok=True)
        
        form_paths = []
        
        # Use the provided PDF template
        pdf_template_path = "New Patient Intake Form.pdf"
        if os.path.exists(pdf_template_path):
            # Copy the PDF template to the forms directory with appointment-specific naming
            import shutil
            patient_form_path = os.path.join(forms_dir, f"patient_intake_{appointment.id}_{patient.last_name}.pdf")
            shutil.copy2(pdf_template_path, patient_form_path)
            form_paths.append(patient_form_path)
            
            # Also create a personalized version with patient information
            self._create_personalized_form(patient, appointment, forms_dir, form_paths)
        else:
            # Fallback to basic text forms if PDF template not found
            form_paths.extend(self._create_fallback_forms(patient, appointment, forms_dir))
        
        return form_paths
    
    def _create_personalized_form(self, patient: Patient, appointment: Appointment, forms_dir: str, form_paths: List[str]):
        """Create a personalized form with patient information"""
        # Create a personalized intake form with patient details
        personalized_form = f"""
        PERSONALIZED PATIENT INTAKE FORM
        
        Patient Information:
        Name: {patient.first_name} {patient.last_name}
        Date of Birth: {patient.date_of_birth}
        Phone: {patient.phone}
        Email: {patient.email}
        Address: {patient.address}
        
        Appointment Details:
        Appointment ID: {appointment.id}
        Date: {appointment.appointment_date}
        Time: {appointment.appointment_time}
        Duration: {appointment.duration} minutes
        
        Emergency Contact:
        Name: {patient.emergency_contact}
        Phone: {patient.emergency_phone}
        
        Instructions:
        1. Please complete the attached "New Patient Intake Form.pdf"
        2. Bring the completed form to your appointment
        3. If you have any questions, contact us at least 24 hours before your appointment
        
        Thank you for choosing our medical services!
        """
        
        personalized_form_path = os.path.join(forms_dir, f"personalized_intake_{appointment.id}.txt")
        with open(personalized_form_path, 'w') as f:
            f.write(personalized_form)
        form_paths.append(personalized_form_path)
    
    def _create_fallback_forms(self, patient: Patient, appointment: Appointment, forms_dir: str) -> List[str]:
        """Create fallback text forms if PDF template is not available"""
        form_paths = []
        
        # Medical History Form
        medical_history_form = f"""
        MEDICAL HISTORY FORM
        
        Patient Information:
        Name: {patient.first_name} {patient.last_name}
        Date of Birth: {patient.date_of_birth}
        Phone: {patient.phone}
        Email: {patient.email}
        
        Appointment Details:
        Appointment ID: {appointment.id}
        Date: {appointment.appointment_date}
        Time: {appointment.appointment_time}
        
        Medical History:
        [ ] Diabetes
        [ ] Hypertension
        [ ] Heart Disease
        [ ] Asthma
        [ ] Allergies: ________________
        [ ] Current Medications: ________________
        [ ] Previous Surgeries: ________________
        
        Emergency Contact:
        Name: {patient.emergency_contact}
        Phone: {patient.emergency_phone}
        
        Signature: ________________ Date: ________________
        """
        
        medical_form_path = os.path.join(forms_dir, f"medical_history_{appointment.id}.txt")
        with open(medical_form_path, 'w') as f:
            f.write(medical_history_form)
        form_paths.append(medical_form_path)
        
        # Insurance Information Form
        insurance_form = f"""
        INSURANCE INFORMATION FORM
        
        Patient Information:
        Name: {patient.first_name} {patient.last_name}
        Date of Birth: {patient.date_of_birth}
        
        Insurance Information:
        Primary Insurance Carrier: ________________
        Member ID: ________________
        Group Number: ________________
        Policy Holder Name: ________________
        Relationship to Patient: ________________
        
        Secondary Insurance (if applicable):
        Carrier: ________________
        Member ID: ________________
        Group Number: ________________
        
        Authorization:
        I authorize the release of medical information necessary to process insurance claims.
        
        Signature: ________________ Date: ________________
        """
        
        insurance_form_path = os.path.join(forms_dir, f"insurance_{appointment.id}.txt")
        with open(insurance_form_path, 'w') as f:
            f.write(insurance_form)
        form_paths.append(insurance_form_path)
        
        return form_paths

class SMSService:
    """Enhanced SMS service using Twilio with webhook support"""
    
    def __init__(self):
        self.sms_log_file = "data/sms_log.txt"
        os.makedirs("data", exist_ok=True)
        
        # Twilio configuration
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER", "")
        self.webhook_url = os.getenv("TWILIO_WEBHOOK_URL", "")
        
        # Initialize Twilio client if credentials are available
        if self.account_sid and self.auth_token and self.from_number:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                self.twilio_enabled = True
                print("✅ Twilio SMS service initialized successfully")
                self._verify_twilio_setup()
            except Exception as e:
                print(f"❌ Twilio initialization failed: {e}")
                self.twilio_enabled = False
        else:
            print("⚠️ Twilio credentials not found, using file-based SMS simulation")
            self.twilio_enabled = False
    
    def _verify_twilio_setup(self):
        """Verify Twilio account and phone number"""
        try:
            # Verify account
            account = self.client.api.accounts(self.account_sid).fetch()
            print(f"✅ Twilio Account verified: {account.friendly_name}")
            
            # Verify phone number
            incoming_phone_numbers = self.client.incoming_phone_numbers.list()
            phone_verified = any(num.phone_number == self.from_number for num in incoming_phone_numbers)
            
            if phone_verified:
                print(f"✅ Twilio phone number verified: {self.from_number}")
            else:
                print(f"⚠️ Phone number {self.from_number} not found in your Twilio account")
                
        except Exception as e:
            print(f"⚠️ Twilio verification failed: {e}")
    
    def _is_example_phone(self, phone: str) -> bool:
        """Check if phone number is an example/test number"""
        if not phone:
            return True
        # Check for common example/test patterns
        example_patterns = ["555-", "123-", "000-", "999-", "555.", "123.", "000.", "999."]
        phone_clean = phone.replace("+", "").replace("-", "").replace(".", "").replace(" ", "")
        return (any(pattern.replace("-", "").replace(".", "") in phone_clean for pattern in example_patterns) or
                len(phone_clean) < 10 or
                phone_clean.startswith("555") or
                phone_clean.startswith("123"))
    
    def send_bulk_sms(self, recipients: List[Dict[str, str]], message: str) -> Dict[str, bool]:
        """Send SMS to multiple recipients"""
        results = {}
        
        for recipient in recipients:
            phone = recipient.get('phone')
            name = recipient.get('name', 'Unknown')
            
            if phone:
                success = self.send_sms(phone, message)
                results[f"{name} ({phone})"] = success
            else:
                results[f"{name} (No phone)"] = False
        
        return results
    
    def send_sms(self, phone_number: str, message: str) -> bool:
        """Send real SMS via Twilio or fallback to file logging"""
        try:
            # Check if phone number is an example/test number
            if self._is_example_phone(phone_number):
                print(f"⚠️ Skipping SMS to example number: {phone_number}")
                print(f"   SMS content would be: {message}")
                return True  # Return True to indicate "success" for testing
            
            # Format phone number for Twilio (handle international numbers properly)
            if not phone_number.startswith('+'):
                if phone_number.startswith('1') and len(phone_number) == 11:
                    phone_number = f"+{phone_number}"
                elif len(phone_number) == 10:
                    phone_number = f"+1{phone_number}"
                else:
                    phone_number = f"+1{phone_number}"
            else:
                # Already has +, but ensure it's properly formatted
                # Remove any non-digit characters except +
                clean_phone = ''.join(c for c in phone_number if c.isdigit() or c == '+')
                if clean_phone.startswith('+91') and len(clean_phone) == 13:
                    # Indian number: +91XXXXXXXXXX
                    phone_number = clean_phone
                elif clean_phone.startswith('+1') and len(clean_phone) == 12:
                    # US number: +1XXXXXXXXXX
                    phone_number = clean_phone
                else:
                    # For other international numbers, keep as is
                    phone_number = clean_phone
            
            if self.twilio_enabled:
                try:
                    # Send real SMS via Twilio
                    message_obj = self.client.messages.create(
                        body=message,
                        from_=self.from_number,
                        to=phone_number
                    )
                    
                    # Log the real SMS
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log_entry = f"[{timestamp}] REAL SMS to {phone_number}: {message} (SID: {message_obj.sid})\n"
                    
                    with open(self.sms_log_file, 'a', encoding='utf-8') as f:
                        f.write(log_entry)
                    
                    print(f"✅ REAL SMS sent to {phone_number}: {message}")
                    return True
                    
                except Exception as twilio_error:
                    # Handle Twilio limitations gracefully
                    error_msg = str(twilio_error)
                    if "daily messages limit" in error_msg or "unverified" in error_msg or "same number" in error_msg:
                        print(f"⚠️ Twilio limitation: {error_msg}")
                        print(f"📝 Logging SMS to file instead: {message}")
                        
                        # Log to file as fallback
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        log_entry = f"[{timestamp}] SIMULATED SMS (Twilio limit) to {phone_number}: {message}\n"
                        
                        with open(self.sms_log_file, 'a', encoding='utf-8') as f:
                            f.write(log_entry)
                        
                        return True  # Return True to indicate "success" for demo purposes
                    else:
                        raise twilio_error
            else:
                # Fallback to file logging
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_entry = f"[{timestamp}] SIMULATED SMS to {phone_number}: {message}\n"
                
                with open(self.sms_log_file, 'a', encoding='utf-8') as f:
                    f.write(log_entry)
                
                print(f"📝 SIMULATED SMS to {phone_number}: {message}")
                return True
            
        except Exception as e:
            print(f"❌ Error sending SMS: {e}")
            # Still log the attempt
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] FAILED SMS to {phone_number}: {message} (Error: {e})\n"
            
            with open(self.sms_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            
            return False
    
    def send_appointment_reminder(self, patient: Patient, appointment: Appointment, reminder_type: ReminderType) -> bool:
        """Send appointment reminder SMS with specific actions"""
        if reminder_type == ReminderType.INITIAL:
            # 1st Reminder: Confirmation of appointment
            message = f"APPOINTMENT CONFIRMATION\n\nDear {patient.first_name},\n\nYour appointment is scheduled for:\nDate: {appointment.appointment_date}\nTime: {appointment.appointment_time}\n\nPlease confirm your attendance by replying to this message.\n\nThank you!"
        elif reminder_type == ReminderType.FORM_CHECK:
            # 2nd Reminder: Have they filled the forms?
            message = f"FORM COMPLETION CHECK\n\nDear {patient.first_name},\n\nYour appointment is tomorrow at {appointment.appointment_time}.\n\nHave you completed your intake forms?\n\nPlease reply:\nYES - if forms are completed\nNO - if forms are not completed\n\nThank you!"
        elif reminder_type == ReminderType.CONFIRMATION:
            # 3rd Reminder: Confirmation or cancellation with reason
            message = f"FINAL CONFIRMATION\n\nDear {patient.first_name},\n\nYour appointment is in 1 hour at {appointment.appointment_time}.\n\nPlease reply:\nCONFIRM - if you're coming\nCANCEL - if you need to cancel (please mention reason)\n\nThank you!"
        else:
            message = f"Reminder: You have an appointment on {appointment.appointment_date} at {appointment.appointment_time}."
        
        return self.send_sms(patient.phone, message)

class ReminderScheduler:
    """Scheduler for automated reminders"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.email_service = EmailService()
        self.sms_service = SMSService()
        self.running = False
    
    def start_scheduler(self):
        """Start the reminder scheduler"""
        self.running = True
        
        # Schedule reminder checks every hour
        schedule.every().hour.do(self._check_and_send_reminders)
        
        # Run scheduler in background thread
        scheduler_thread = threading.Thread(target=self._run_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()
        
        print("Reminder scheduler started")
    
    def stop_scheduler(self):
        """Stop the reminder scheduler"""
        self.running = False
        print("Reminder scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _check_and_send_reminders(self):
        """Check for due reminders and send them"""
        try:
            reminders = self.db.load_reminders()
            current_time = datetime.now()
            
            for reminder_data in reminders:
                if not reminder_data['sent']:
                    scheduled_time = datetime.fromisoformat(reminder_data['scheduled_time'])
                    
                    # Check if reminder is due (within 5 minutes of scheduled time)
                    if abs((current_time - scheduled_time).total_seconds()) <= 300:  # 5 minutes
                        self._send_reminder(reminder_data)
                        
        except Exception as e:
            print(f"Error checking reminders: {e}")
    
    def _send_reminder(self, reminder_data: Dict[str, Any]):
        """Send a specific reminder"""
        try:
            # Get patient and appointment information
            patients = self.db.load_patients()
            appointments = self.db.load_appointments()
            
            patient = next((p for p in patients if p.id == reminder_data['patient_id']), None)
            appointment_data = next((a for a in appointments if a['id'] == reminder_data['appointment_id']), None)
            
            if not patient or not appointment_data:
                print(f"Could not find patient or appointment for reminder {reminder_data['id']}")
                return
            
            # Create appointment object
            appointment = Appointment(
                id=appointment_data['id'],
                patient_id=appointment_data['patient_id'],
                doctor_id=appointment_data['doctor_id'],
                appointment_date=datetime.strptime(appointment_data['appointment_date'], '%Y-%m-%d').date(),
                appointment_time=appointment_data['appointment_time'],
                duration=appointment_data['duration'],
                status=appointment_data['status']
            )
            
            # Send SMS reminder
            reminder_type = ReminderType(reminder_data['reminder_type'])
            sms_success = self.sms_service.send_appointment_reminder(patient, appointment, reminder_type)
            
            # Send email reminder for initial reminder
            email_success = True
            if reminder_type == ReminderType.INITIAL:
                email_success = self.email_service.send_appointment_confirmation(patient, appointment)
            
            # Mark reminder as sent
            if sms_success or email_success:
                self._mark_reminder_sent(reminder_data['id'])
                
        except Exception as e:
            print(f"Error sending reminder {reminder_data['id']}: {e}")
    
    def _mark_reminder_sent(self, reminder_id: str):
        """Mark a reminder as sent"""
        try:
            reminders = self.db.load_reminders()
            
            for reminder in reminders:
                if reminder['id'] == reminder_id:
                    reminder['sent'] = True
                    break
            
            with open(Config.REMINDERS_JSON, 'w') as f:
                json.dump(reminders, f, indent=2)
                
        except Exception as e:
            print(f"Error marking reminder as sent: {e}")
    
    def process_reminder_response(self, phone_number: str, response: str) -> str:
        """Process response to reminder SMS"""
        try:
            # Find the most recent unsent reminder for this phone number
            reminders = self.db.load_reminders()
            patients = self.db.load_patients()
            
            # Find patient by phone
            patient = next((p for p in patients if p.phone == phone_number), None)
            if not patient:
                return "Patient not found"
            
            # Find recent reminder
            recent_reminder = None
            for reminder in reminders:
                if (reminder['patient_id'] == patient.id and 
                    not reminder['sent'] and 
                    reminder['response'] is None):
                    recent_reminder = reminder
                    break
            
            if not recent_reminder:
                return "No pending reminders found"
            
            # Process response
            response_upper = response.upper()
            
            if "YES" in response_upper or "CONFIRM" in response_upper:
                recent_reminder['response'] = "confirmed"
                message = "Thank you for confirming your appointment. We look forward to seeing you!"
            elif "NO" in response_upper or "CANCEL" in response_upper:
                recent_reminder['response'] = "cancelled"
                message = "We're sorry you need to cancel. Please call us to reschedule."
            else:
                recent_reminder['response'] = response
                message = "Thank you for your response. We'll review it and get back to you."
            
            # Save updated reminder
            with open(Config.REMINDERS_JSON, 'w') as f:
                json.dump(reminders, f, indent=2)
            
            return message
            
        except Exception as e:
            print(f"Error processing reminder response: {e}")
            return "Error processing your response. Please try again."
    
    def handle_webhook(self, webhook_data: Dict[str, Any]) -> str:
        """Handle incoming webhook from Twilio"""
        try:
            from_number = webhook_data.get('From', '')
            message_body = webhook_data.get('Body', '')
            
            print(f"Received webhook from {from_number}: {message_body}")
            
            # Process the SMS response
            response_message = self.process_reminder_response(from_number, message_body)
            
            # Send response back via SMS
            self.send_sms(from_number, response_message)
            
            return response_message
            
        except Exception as e:
            print(f"Error handling webhook: {e}")
            return "Error processing webhook"

class CommunicationManager:
    """Enhanced communication manager with automation features"""
    
    def __init__(self):
        self.email_service = EmailService()
        self.sms_service = SMSService()
        self.reminder_scheduler = ReminderScheduler()
        self.db = DatabaseManager()
    
    def send_appointment_confirmation(self, patient: Patient, appointment: Appointment) -> Dict[str, bool]:
        """Send appointment confirmation via both email and SMS"""
        results = {}
        
        # Send email confirmation
        email_success = self.email_service.send_appointment_confirmation(patient, appointment)
        results['email'] = email_success
        
        # Send SMS confirmation
        sms_message = f"Appointment confirmed for {appointment.appointment_date} at {appointment.appointment_time}. Check your email for details."
        sms_success = self.sms_service.send_sms(patient.phone, sms_message)
        results['sms'] = sms_success
        
        return results
    
    def send_intake_forms(self, patient: Patient, appointment: Appointment) -> bool:
        """Send intake forms via email"""
        return self.email_service.send_intake_forms(patient, appointment)
    
    def send_appointment_reminder(self, patient: Patient, appointment: Appointment, reminder_type: str = "general") -> Dict[str, bool]:
        """Send appointment reminder via both email and SMS"""
        results = {}
        
        # Send email reminder
        email_success = self.email_service.send_appointment_reminder(patient, appointment, reminder_type)
        results['email'] = email_success
        
        # Send SMS reminder
        sms_success = self.sms_service.send_appointment_reminder(patient, appointment, ReminderType.INITIAL)
        results['sms'] = sms_success
        
        return results
    
    def send_cancellation_notification(self, patient: Patient, appointment: Appointment) -> Dict[str, bool]:
        """Send cancellation notification via both email and SMS"""
        results = {}
        
        # Send email notification
        email_success = self.email_service.send_cancellation_notification(patient, appointment)
        results['email'] = email_success
        
        # Send SMS notification
        sms_message = f"Your appointment on {appointment.appointment_date} at {appointment.appointment_time} has been cancelled. Contact us to reschedule."
        sms_success = self.sms_service.send_sms(patient.phone, sms_message)
        results['sms'] = sms_success
        
        return results
    
    def send_reschedule_notification(self, patient: Patient, old_appointment: Appointment, new_appointment: Appointment) -> Dict[str, bool]:
        """Send reschedule notification via both email and SMS"""
        results = {}
        
        # Send email notification
        email_success = self.email_service.send_reschedule_notification(patient, old_appointment, new_appointment)
        results['email'] = email_success
        
        # Send SMS notification
        sms_message = f"Your appointment has been rescheduled to {new_appointment.appointment_date} at {new_appointment.appointment_time}. Check your email for details."
        sms_success = self.sms_service.send_sms(patient.phone, sms_message)
        results['sms'] = sms_success
        
        return results
    
    def send_bulk_notifications(self, recipients: List[Dict[str, str]], message_type: str, **kwargs) -> Dict[str, Dict[str, bool]]:
        """Send bulk notifications to multiple recipients"""
        results = {}
        
        for recipient in recipients:
            name = recipient.get('name', 'Unknown')
            email = recipient.get('email', '')
            phone = recipient.get('phone', '')
            
            recipient_results = {}
            
            # Send email if available
            if email and message_type in self.email_service.templates:
                email_success = self.email_service.send_email(
                    email, 
                    f"Medical Update - {name}",
                    self.email_service.templates[message_type].format(**kwargs)
                )
                recipient_results['email'] = email_success
            
            # Send SMS if available
            if phone:
                sms_message = kwargs.get('sms_message', 'Medical appointment update. Check your email for details.')
                sms_success = self.sms_service.send_sms(phone, sms_message)
                recipient_results['sms'] = sms_success
            
            results[f"{name} ({email})"] = recipient_results
        
        return results
    
    def start_reminder_system(self):
        """Start the reminder system"""
        self.reminder_scheduler.start_scheduler()
    
    def stop_reminder_system(self):
        """Stop the reminder system"""
        self.reminder_scheduler.stop_scheduler()
    
    def process_sms_response(self, phone_number: str, message: str) -> str:
        """Process SMS response"""
        return self.reminder_scheduler.process_reminder_response(phone_number, message)
    
    def handle_webhook(self, webhook_data: Dict[str, Any]) -> str:
        """Handle incoming webhook from Twilio"""
        return self.reminder_scheduler.handle_webhook(webhook_data)
    
    def get_communication_status(self) -> Dict[str, Any]:
        """Get status of communication services"""
        return {
            'email_service': {
                'configured': bool(self.email_service.email_username and self.email_service.email_password),
                'smtp_server': self.email_service.smtp_server,
                'smtp_port': self.email_service.smtp_port
            },
            'sms_service': {
                'twilio_enabled': self.sms_service.twilio_enabled,
                'from_number': self.sms_service.from_number,
                'account_verified': bool(self.sms_service.account_sid and self.sms_service.auth_token)
            },
            'reminder_scheduler': {
                'running': self.reminder_scheduler.running
            }
        }
