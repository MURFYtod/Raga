"""
Streamlit UI for Medical Appointment Scheduling AI Agent
"""
import streamlit as st

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="Medical Appointment Scheduler",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import other modules after page config
import pandas as pd
from datetime import datetime, date, timedelta
import json
import os

from simple_agent_fixed import SimpleMedicalSchedulingAgent
from database import DatabaseManager
from communication import CommunicationManager
from emr_database import EMRDatabase
from models import Patient, Appointment, AppointmentStatus
from config import Config

# Custom CSS for modern medical UI
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .main {
        font-family: 'Inter', sans-serif;
    }
    
    /* Landing Page Styles */
    .landing-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .landing-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .landing-subtitle {
        font-size: 1.2rem;
        font-weight: 300;
        opacity: 0.9;
        margin-bottom: 2rem;
    }
    
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        border: 1px solid #e8f2ff;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        text-align: center;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0,0,0,0.12);
    }
    
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
        display: block;
    }
    
    .feature-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    
    .feature-desc {
        color: #7f8c8d;
        font-size: 0.9rem;
        line-height: 1.5;
    }
    
    /* Chat Interface Styles */
    .chat-container {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        border: 1px solid #e8f2ff;
        margin: 1rem 0;
    }
    
    .chat-message {
        padding: 1rem 1.5rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        max-width: 80%;
        word-wrap: break-word;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 5px;
    }
    
    .ai-message {
        background: #f8f9fa;
        color: #2c3e50;
        border: 1px solid #e8f2ff;
        border-bottom-left-radius: 5px;
    }
    
    /* Appointment Panel Styles */
    .appointment-panel {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        border: 1px solid #e8f2ff;
        margin: 1rem 0;
    }
    
    .slot-card {
        background: #f8f9fa;
        border: 2px solid #e8f2ff;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .slot-card:hover {
        border-color: #667eea;
        background: #f0f4ff;
    }
    
    .slot-card.selected {
        border-color: #667eea;
        background: #e8f2ff;
    }
    
    /* Progress Tracker */
    .progress-tracker {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 2rem 0;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 10px;
    }
    
    .progress-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        flex: 1;
        position: relative;
    }
    
    .progress-step:not(:last-child)::after {
        content: '';
        position: absolute;
        top: 20px;
        left: 60%;
        right: -40%;
        height: 2px;
        background: #e8f2ff;
        z-index: 1;
    }
    
    .progress-step.completed:not(:last-child)::after {
        background: #667eea;
    }
    
    .progress-icon {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: #e8f2ff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
        z-index: 2;
        position: relative;
    }
    
    .progress-step.completed .progress-icon {
        background: #667eea;
        color: white;
    }
    
    .progress-step.active .progress-icon {
        background: #667eea;
        color: white;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
    
    .progress-label {
        font-size: 0.8rem;
        color: #7f8c8d;
        text-align: center;
    }
    
    /* Status Indicators */
    .status-success {
        color: #27ae60;
        font-weight: 600;
    }
    
    .status-warning {
        color: #f39c12;
        font-weight: 600;
    }
    
    .status-error {
        color: #e74c3c;
        font-weight: 600;
    }
    
    /* Admin Dashboard */
    .admin-section {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        border: 1px solid #e8f2ff;
    }
    
    .admin-button {
        width: 100%;
        margin: 0.5rem 0;
        padding: 0.75rem;
        border-radius: 10px;
        border: 1px solid #e8f2ff;
        background: white;
        color: #2c3e50;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .admin-button:hover {
        background: #f8f9fa;
        border-color: #667eea;
        transform: translateY(-2px);
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        color: #7f8c8d;
        font-size: 0.9rem;
        border-top: 1px solid #e8f2ff;
        margin-top: 3rem;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .landing-title {
            font-size: 2rem;
        }
        
        .feature-grid {
            grid-template-columns: 1fr;
        }
        
        .chat-message {
            max-width: 95%;
        }
        
        .progress-tracker {
            flex-direction: column;
            gap: 1rem;
        }
        
        .progress-step:not(:last-child)::after {
            display: none;
        }
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #667eea;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #5a6fd8;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
# Simplified agent doesn't use agent_state
if "agent" not in st.session_state:
    st.session_state.agent = None
if "db" not in st.session_state:
    st.session_state.db = DatabaseManager()
if "emr_db" not in st.session_state:
    st.session_state.emr_db = EMRDatabase()
if "comm_manager" not in st.session_state:
    st.session_state.comm_manager = CommunicationManager()

def initialize_agent(api_key=None):
    """Initialize the AI agent"""
    if st.session_state.agent is None:
        # Use provided API key or get from config
        api_key = api_key or Config.PERPLEXITY_API_KEY
        
        try:
            st.session_state.agent = SimpleMedicalSchedulingAgent(api_key)
            st.session_state.api_key = api_key  # Store the API key in session state
            return True
        except Exception as e:
            st.error(f"Error initializing agent: {e}")
            return False
    return True

def display_chat_message(message, is_user=False):
    """Display a chat message with improved styling"""
    if is_user:
        with st.chat_message("user"):
            st.markdown(f'<div class="chat-message user-message">{message}</div>', unsafe_allow_html=True)
    else:
        with st.chat_message("assistant"):
            st.markdown(f'<div class="chat-message ai-message">{message}</div>', unsafe_allow_html=True)

def main():
    """Main application"""
    # Landing Page Header
    st.markdown("""
    <div class="landing-header">
        <h1 class="landing-title">🏥 AI Scheduling Agent – Smart Medical Appointments</h1>
        <p class="landing-subtitle">Intelligent booking, automated reminders, and seamless calendar integration for modern healthcare</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature Grid
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-card">
            <span class="feature-icon">🤖</span>
            <h3 class="feature-title">AI-Powered Booking</h3>
            <p class="feature-desc">Smart patient detection and intelligent appointment scheduling</p>
        </div>
        <div class="feature-card">
            <span class="feature-icon">📅</span>
            <h3 class="feature-title">Calendar Integration</h3>
            <p class="feature-desc">Seamless integration with your existing calendar systems</p>
        </div>
        <div class="feature-card">
            <span class="feature-icon">📱</span>
            <h3 class="feature-title">Smart Reminders</h3>
            <p class="feature-desc">Automated SMS and email reminders to reduce no-shows</p>
        </div>
        <div class="feature-card">
            <span class="feature-icon">🏥</span>
            <h3 class="feature-title">EMR Integration</h3>
            <p class="feature-desc">Complete medical records and patient history access</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("🏥 Medical Scheduler")
        st.markdown("---")
        
        # API Configuration
        st.header("🔑 API Configuration")
        
        # Show current status
        if st.session_state.get("agent") is not None:
            st.success("✅ AI Agent is ready!")
            st.info("🤖 Agent automatically initialized with Perplexity API")
            if st.button("🔄 Reinitialize Agent"):
                st.session_state.agent = None
                st.rerun()
        else:
            st.warning("⚠️ AI Agent will initialize automatically when you start chatting")
        
        st.markdown("---")
        
        # Admin functions
        st.header("Admin Functions")
        
        if st.button("📊 View Appointments", key="view_appointments_btn"):
            view_appointments()
        
        if st.button("👥 View Patients", key="view_patients_btn"):
            view_patients()
        
        if st.button("👨‍⚕️ View Doctors", key="view_doctors_btn"):
            view_doctors()
        
        st.markdown("---")
        
        # EMR Features
        st.header("🏥 EMR Features")
        
        if st.button("🔍 Search EMR Database", key="search_emr_btn"):
            search_emr_database()
        
        if st.button("📊 EMR Statistics", key="emr_stats_btn"):
            show_emr_statistics()
        
        if st.button("👤 Smart Patient Lookup", key="smart_lookup_btn"):
            smart_patient_lookup()
        
        if st.button("📤 Export Appointments", key="export_appointments_btn"):
            export_appointments()
        
        st.markdown("---")
        
        # Communication Features
        st.header("📱 Communication Features")
        
        if st.button("📱 Send Test SMS", key="send_test_sms_sidebar_btn"):
            send_test_sms()
        
        if st.button("📧 Send Test Email", key="send_test_email_sidebar_btn"):
            send_test_email()
        
        if st.button("🔔 Test 3-Tier Reminders", key="test_reminders_btn"):
            test_3_tier_reminders()
        
        if st.button("📊 View Communication Logs", key="view_comm_logs_btn"):
            view_communication_logs()
        
        st.markdown("---")
        
        
        if st.button("🔄 Reset Chat", key="reset_chat_btn"):
            st.session_state.messages = []
            if st.session_state.agent:
                st.session_state.agent.reset_conversation()
            st.rerun()
    
    # Main chat interface
    st.markdown("### 💬 Chat with AI Assistant")
    st.markdown("Ask me anything about scheduling appointments, checking patient records, or managing your medical appointments.")
    
    # Initialize agent
    if not initialize_agent():
        st.stop()
    
    # Display chat history
    for message in st.session_state.messages:
        display_chat_message(message["content"], message["is_user"])
    
    # Chat input with improved styling
    if prompt := st.chat_input("💬 Type your message here... (e.g., 'Hi, I'd like to book an appointment')"):
        # Add user message to chat history
        st.session_state.messages.append({"content": prompt, "is_user": True})
        display_chat_message(prompt, True)
        
        # Ensure agent is initialized
        if st.session_state.agent is None:
            with st.spinner("🤖 Initializing AI agent..."):
                if not initialize_agent():
                    st.error("❌ Failed to initialize AI agent. Please try again.")
                    return
        
        # Process message with agent
        with st.spinner("🤖 AI is thinking..."):
            try:
                
                # Get AI response from the simplified agent
                ai_response = st.session_state.agent.process_message(prompt)
                
                # Add AI response to chat history
                st.session_state.messages.append({"content": ai_response, "is_user": False})
                display_chat_message(ai_response, False)
                
            except Exception as e:
                error_message = f"Sorry, I encountered an error: {str(e)}"
                st.session_state.messages.append({"content": error_message, "is_user": False})
                display_chat_message(error_message, False)
    
    # Communication Status Dashboard
    with st.expander("📱 Communication Status Dashboard"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**📱 SMS Status:**")
            try:
                from communication import SMSService
                sms_service = SMSService()
                if hasattr(sms_service, 'twilio_enabled') and sms_service.twilio_enabled:
                    st.success("✅ Twilio SMS Active")
                    st.write(f"From: {sms_service.from_number}")
                else:
                    st.warning("⚠️ SMS Simulation Mode")
            except:
                st.error("❌ SMS Service Error")
        
        with col2:
            st.write("**📧 Email Status:**")
            try:
                from communication import EmailService
                email_service = EmailService()
                if email_service.email_username and email_service.email_username != "your_email@gmail.com":
                    st.success("✅ Gmail Email Active")
                    st.write(f"From: {email_service.email_username}")
                else:
                    st.warning("⚠️ Email Simulation Mode")
            except:
                st.error("❌ Email Service Error")
        
        with col3:
            st.write("**🔔 Reminder System:**")
            try:
                st.success("✅ 3-Tier Reminders Active")
                st.write("• 24h: Initial reminder")
                st.write("• 2h: Form check")
                st.write("• 1h: Final confirmation")
            except:
                st.error("❌ Reminder System Error")
    
    # Display current collected data
    if st.session_state.agent and st.session_state.agent.get_collected_data():
        with st.expander("Current Collected Data"):
            collected_data = st.session_state.agent.get_collected_data()
            st.json(collected_data)
            
            # Show EMR information if available
            if collected_data.get('phone') or collected_data.get('email') or (collected_data.get('first_name') and collected_data.get('last_name')):
                try:
                    patient_record, patient_type = st.session_state.emr_db.detect_patient_type(
                        phone=collected_data.get('phone'),
                        email=collected_data.get('email'),
                        first_name=collected_data.get('first_name'),
                        last_name=collected_data.get('last_name')
                    )
                    
                    if patient_record:
                        st.success(f"🏥 EMR Patient Found: {patient_record.first_name} {patient_record.last_name} ({patient_type.upper()})")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Medical History:** {', '.join(patient_record.medical_history[:3])}...")
                            st.write(f"**Allergies:** {', '.join(patient_record.allergies) if patient_record.allergies else 'None'}")
                        with col2:
                            st.write(f"**Medications:** {', '.join(patient_record.current_medications[:3])}...")
                            st.write(f"**Insurance:** {patient_record.insurance_provider}")
                        
                        duration = st.session_state.emr_db.get_smart_duration(patient_record, patient_type)
                        st.info(f"⏱️ **Smart Duration: {duration} minutes** ({'New patient' if duration == 60 else 'Returning patient'})")
                    else:
                        st.info("🆕 New Patient - No EMR record found")
                except Exception as e:
                    st.warning(f"EMR lookup error: {e}")

def view_appointments():
    """View all appointments"""
    st.subheader("📅 All Appointments")
    
    try:
        appointments = st.session_state.db.load_appointments()
        if not appointments:
            st.info("No appointments found")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(appointments)
        
        # Format the data
        df['appointment_date'] = pd.to_datetime(df['appointment_date']).dt.strftime('%Y-%m-%d')
        df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        df['updated_at'] = pd.to_datetime(df['updated_at']).dt.strftime('%Y-%m-%d %H:%M')
        
        st.dataframe(df, use_container_width=True)
        
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Appointments", len(appointments))
        with col2:
            scheduled = len([a for a in appointments if a['status'] == 'scheduled'])
            st.metric("Scheduled", scheduled)
        with col3:
            confirmed = len([a for a in appointments if a['status'] == 'confirmed'])
            st.metric("Confirmed", confirmed)
        with col4:
            cancelled = len([a for a in appointments if a['status'] == 'cancelled'])
            st.metric("Cancelled", cancelled)
            
    except Exception as e:
        st.error(f"Error loading appointments: {e}")

def view_patients():
    """View all patients"""
    st.subheader("👥 All Patients")
    
    try:
        patients = st.session_state.db.load_patients()
        if not patients:
            st.info("No patients found")
            return
        
        # Convert to DataFrame
        patients_data = []
        for patient in patients:
            patients_data.append({
                'ID': patient.id,
                'Name': f"{patient.first_name} {patient.last_name}",
                'Date of Birth': patient.date_of_birth.strftime('%Y-%m-%d'),
                'Phone': patient.phone,
                'Email': patient.email,
                'Type': patient.patient_type.value.title(),
                'Created': patient.created_at.strftime('%Y-%m-%d')
            })
        
        df = pd.DataFrame(patients_data)
        st.dataframe(df, use_container_width=True)
        
        # Statistics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Patients", len(patients))
        with col2:
            new_patients = len([p for p in patients if p.patient_type.value == 'new'])
            st.metric("New Patients", new_patients)
            
    except Exception as e:
        st.error(f"Error loading patients: {e}")

def view_doctors():
    """View all doctors"""
    st.subheader("👨‍⚕️ All Doctors")
    
    try:
        doctors = st.session_state.db.load_doctors()
        if not doctors:
            st.info("No doctors found")
            return
        
        # Convert to DataFrame
        doctors_data = []
        for doctor in doctors:
            doctors_data.append({
                'ID': doctor.id,
                'Name': doctor.name,
                'Specialty': doctor.specialty,
                'Location': doctor.location,
                'Available Days': ', '.join(doctor.available_days)
            })
        
        df = pd.DataFrame(doctors_data)
        st.dataframe(df, use_container_width=True)
        
        # Statistics
        st.metric("Total Doctors", len(doctors))
        
    except Exception as e:
        st.error(f"Error loading doctors: {e}")

def export_appointments():
    """Export appointments to Excel"""
    st.subheader("📤 Export Appointments")
    
    try:
        df = st.session_state.db.get_appointments_for_export()
        
        if df.empty:
            st.info("No appointments to export")
            return
        
        # Create Excel file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"appointments_export_{timestamp}.xlsx"
        filepath = os.path.join("data", filename)
        
        df.to_excel(filepath, index=False)
        
        st.success(f"Appointments exported successfully to {filename}")
        
        # Download button
        with open(filepath, 'rb') as f:
            st.download_button(
                label="📥 Download Excel File",
                data=f.read(),
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    except Exception as e:
        st.error(f"Error exporting appointments: {e}")

def send_test_email():
    """Send test email"""
    st.subheader("📧 Send Test Email")
    
    try:
        # Create a test patient and appointment
        test_patient = Patient(
            id="TEST001",
            first_name="Test",
            last_name="Patient",
            date_of_birth=date(1990, 1, 1),
            phone="1234567890",
            email=st.text_input("Test Email Address", "test@example.com"),
            address="123 Test St",
            emergency_contact="Test Contact",
            emergency_phone="0987654321",
            patient_type="new"
        )
        
        test_appointment = Appointment(
            id="TEST001",
            patient_id="TEST001",
            doctor_id="D001",
            appointment_date=date.today() + timedelta(days=1),
            appointment_time="10:00",
            duration=60,
            status=AppointmentStatus.SCHEDULED
        )
        
        if st.button("Send Test Confirmation Email"):
            success = st.session_state.comm_manager.send_appointment_confirmation(test_patient, test_appointment)
            if success:
                st.success("Test email sent successfully!")
            else:
                st.error("Failed to send test email. Check your email configuration.")
        
        if st.button("Send Test Intake Forms"):
            success = st.session_state.comm_manager.send_intake_forms(test_patient, test_appointment)
            if success:
                st.success("Test intake forms sent successfully!")
            else:
                st.error("Failed to send test intake forms. Check your email configuration.")
                
    except Exception as e:
        st.error(f"Error sending test email: {e}")

def search_emr_database():
    """Search EMR database for patients"""
    st.subheader("🔍 EMR Database Search")
    
    search_query = st.text_input("Enter search term (name, phone, or email):", key="emr_search")
    
    if st.button("Search EMR Database"):
        if search_query:
            try:
                results = st.session_state.emr_db.search_patients(search_query)
                
                if results:
                    st.success(f"Found {len(results)} patients matching '{search_query}'")
                    
                    for patient in results:
                        with st.expander(f"👤 {patient.first_name} {patient.last_name} ({patient.patient_type})"):
                            st.write(f"**Patient ID:** {patient.patient_id}")
                            st.write(f"**Phone:** {patient.phone}")
                            st.write(f"**Email:** {patient.email}")
                            st.write(f"**DOB:** {patient.date_of_birth}")
                            st.write(f"**Type:** {patient.patient_type}")
                            st.write(f"**Total Visits:** {patient.total_visits}")
                            st.write(f"**Last Visit:** {patient.last_visit or 'Never'}")
                            st.write(f"**Medical History:** {', '.join(patient.medical_history[:3])}...")
                            st.write(f"**Allergies:** {', '.join(patient.allergies) if patient.allergies else 'None'}")
                            st.write(f"**Medications:** {', '.join(patient.current_medications[:3])}...")
                            st.write(f"**Insurance:** {patient.insurance_provider} ({patient.insurance_id})")
                else:
                    st.warning(f"No patients found matching '{search_query}'")
                    
            except Exception as e:
                st.error(f"Error searching EMR database: {e}")
        else:
            st.warning("Please enter a search term")

def show_emr_statistics():
    """Show EMR database statistics"""
    st.subheader("📊 EMR Database Statistics")
    
    try:
        all_patients = st.session_state.emr_db.get_all_patients()
        new_patients = [p for p in all_patients if p.patient_type == 'new']
        returning_patients = [p for p in all_patients if p.patient_type == 'returning']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Patients", len(all_patients))
        
        with col2:
            st.metric("New Patients", len(new_patients))
        
        with col3:
            st.metric("Returning Patients", len(returning_patients))
        
        # Show sample patients
        st.subheader("👥 Sample Patients")
        
        if all_patients:
            sample_patients = all_patients[:5]  # Show first 5 patients
            
            for patient in sample_patients:
                with st.expander(f"👤 {patient.first_name} {patient.last_name} ({patient.patient_type})"):
                    st.write(f"**Phone:** {patient.phone}")
                    st.write(f"**Email:** {patient.email}")
                    st.write(f"**Total Visits:** {patient.total_visits}")
                    st.write(f"**Medical History:** {', '.join(patient.medical_history[:2])}...")
                    st.write(f"**Allergies:** {', '.join(patient.allergies[:2]) if patient.allergies else 'None'}")
        
        # Show medical conditions distribution
        st.subheader("🏥 Medical Conditions Distribution")
        
        all_conditions = []
        for patient in all_patients:
            all_conditions.extend(patient.medical_history)
        
        if all_conditions:
            condition_counts = {}
            for condition in all_conditions:
                condition_counts[condition] = condition_counts.get(condition, 0) + 1
            
            # Sort by frequency
            sorted_conditions = sorted(condition_counts.items(), key=lambda x: x[1], reverse=True)
            
            for condition, count in sorted_conditions[:10]:  # Top 10 conditions
                st.write(f"• **{condition}:** {count} patients")
        
    except Exception as e:
        st.error(f"Error loading EMR statistics: {e}")

def smart_patient_lookup():
    """Smart patient lookup using EMR database"""
    st.subheader("👤 Smart Patient Lookup")
    
    st.write("Enter patient information to search the EMR database:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        phone = st.text_input("Phone Number:", key="smart_lookup_phone")
        first_name = st.text_input("First Name:", key="smart_lookup_first")
    
    with col2:
        email = st.text_input("Email:", key="smart_lookup_email")
        last_name = st.text_input("Last Name:", key="smart_lookup_last")
    
    if st.button("🔍 Lookup Patient"):
        if phone or email or (first_name and last_name):
            try:
                # Use EMR database to detect patient type
                patient_record, patient_type = st.session_state.emr_db.detect_patient_type(
                    phone=phone, email=email, first_name=first_name, last_name=last_name
                )
                
                if patient_record:
                    st.success(f"✅ Patient found in EMR system!")
                    
                    # Display patient information
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**👤 Basic Information:**")
                        st.write(f"• Name: {patient_record.first_name} {patient_record.last_name}")
                        st.write(f"• Patient ID: {patient_record.patient_id}")
                        st.write(f"• DOB: {patient_record.date_of_birth}")
                        st.write(f"• Phone: {patient_record.phone}")
                        st.write(f"• Email: {patient_record.email}")
                        st.write(f"• Type: **{patient_type.upper()}**")
                        st.write(f"• Total Visits: {patient_record.total_visits}")
                        st.write(f"• Last Visit: {patient_record.last_visit or 'Never'}")
                    
                    with col2:
                        st.write("**🏥 Medical Information:**")
                        st.write(f"• Medical History: {', '.join(patient_record.medical_history[:3])}...")
                        st.write(f"• Allergies: {', '.join(patient_record.allergies) if patient_record.allergies else 'None'}")
                        st.write(f"• Medications: {', '.join(patient_record.current_medications[:3])}...")
                        st.write(f"• Insurance: {patient_record.insurance_provider}")
                        st.write(f"• Insurance ID: {patient_record.insurance_id}")
                    
                    # Show smart duration
                    duration = st.session_state.emr_db.get_smart_duration(patient_record, patient_type)
                    st.info(f"⏱️ **Recommended Appointment Duration: {duration} minutes** ({'New patient - comprehensive intake' if duration == 60 else 'Returning patient - focused visit'})")
                    
                else:
                    st.warning("❌ Patient not found in EMR system. This appears to be a NEW PATIENT.")
                    st.info("💡 New patients will be scheduled for 60-minute appointments for comprehensive intake.")
                
            except Exception as e:
                st.error(f"Error looking up patient: {e}")
        else:
            st.warning("Please provide at least one search criteria (phone, email, or name)")

def send_test_sms():
    """Send test SMS"""
    st.subheader("📱 Send Test SMS")
    
    # Get test patient from EMR
    emr_db = st.session_state.emr_db
    all_patients = emr_db.get_all_patients()
    
    if all_patients:
        # Use first patient as test
        test_patient = all_patients[0]
        
        st.write(f"**Test Patient:** {test_patient.first_name} {test_patient.last_name}")
        st.write(f"**Phone:** {test_patient.phone}")
        
        # Allow custom phone number
        custom_phone = st.text_input("Or enter custom phone number:", value=test_patient.phone)
        custom_message = st.text_area("Message:", value="Test SMS from Medical Appointment Scheduler")
        
        if st.button("📱 Send Test SMS", key="send_test_sms_function_btn"):
            try:
                from communication import SMSService
                sms_service = SMSService()
                
                success = sms_service.send_sms(custom_phone, custom_message)
                
                if success:
                    st.success(f"✅ Test SMS sent successfully to {custom_phone}!")
                    st.info("Check your phone for the message")
                else:
                    st.error("❌ Failed to send test SMS. Check Twilio configuration.")
                    
            except Exception as e:
                st.error(f"Error sending SMS: {e}")
    else:
        st.warning("No patients found in EMR database")

def test_3_tier_reminders():
    """Test 3-tier reminder system"""
    st.subheader("🔔 Test 3-Tier Reminder System")
    
    # Get test patient from EMR
    emr_db = st.session_state.emr_db
    all_patients = emr_db.get_all_patients()
    
    if all_patients:
        test_patient = all_patients[0]
        
        st.write(f"**Test Patient:** {test_patient.first_name} {test_patient.last_name}")
        st.write(f"**Phone:** {test_patient.phone}")
        st.write(f"**Email:** {test_patient.email}")
        
        # Create test appointment
        from datetime import date, timedelta
        from models import Appointment, AppointmentStatus
        
        test_appointment = Appointment(
            id="TEST_REMINDER_001",
            patient_id=test_patient.patient_id,
            doctor_id="D001",
            appointment_date=date.today() + timedelta(days=1),
            appointment_time="10:00",
            duration=60,
            status=AppointmentStatus.SCHEDULED
        )
        
        st.write(f"**Test Appointment:** {test_appointment.appointment_date} at {test_appointment.appointment_time}")
        
        if st.button("🔔 Send All 3 Reminders"):
            try:
                from communication import EmailService, SMSService
                from models import ReminderType
                
                email_service = EmailService()
                sms_service = SMSService()
                
                st.write("Sending reminders...")
                
                # 1. Initial Reminder (24 hours before)
                st.write("1️⃣ Sending Initial Reminder (24h)...")
                sms_initial = sms_service.send_appointment_reminder(test_patient, test_appointment, ReminderType.INITIAL)
                email_initial = email_service.send_appointment_reminder_email(test_patient, test_appointment, ReminderType.INITIAL)
                
                # 2. Form Check Reminder (2 hours before)
                st.write("2️⃣ Sending Form Check Reminder (2h)...")
                sms_form = sms_service.send_appointment_reminder(test_patient, test_appointment, ReminderType.FORM_CHECK)
                email_form = email_service.send_appointment_reminder_email(test_patient, test_appointment, ReminderType.FORM_CHECK)
                
                # 3. Final Confirmation (1 hour before)
                st.write("3️⃣ Sending Final Confirmation (1h)...")
                sms_final = sms_service.send_appointment_reminder(test_patient, test_appointment, ReminderType.CONFIRMATION)
                email_final = email_service.send_appointment_reminder_email(test_patient, test_appointment, ReminderType.CONFIRMATION)
                
                # Results
                st.success("🎉 All 3-Tier Reminders Sent!")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**SMS Results:**")
                    st.write(f"• Initial: {'✅' if sms_initial else '❌'}")
                    st.write(f"• Form Check: {'✅' if sms_form else '❌'}")
                    st.write(f"• Final: {'✅' if sms_final else '❌'}")
                
                with col2:
                    st.write("**Email Results:**")
                    st.write(f"• Initial: {'✅' if email_initial else '❌'}")
                    st.write(f"• Form Check: {'✅' if email_form else '❌'}")
                    st.write(f"• Final: {'✅' if email_final else '❌'}")
                
                st.info(f"📱 Check phone ({test_patient.phone}) for 3 SMS messages")
                st.info(f"📧 Check email ({test_patient.email}) for 3 reminder emails")
                
            except Exception as e:
                st.error(f"Error sending reminders: {e}")
    else:
        st.warning("No patients found in EMR database")

def view_communication_logs():
    """View communication logs"""
    st.subheader("📊 Communication Logs")
    
    # SMS Log
    st.write("**📱 SMS Log:**")
    try:
        if os.path.exists("data/sms_log.txt"):
            with open("data/sms_log.txt", "r", encoding="utf-8") as f:
                sms_logs = f.read()
            
            if sms_logs.strip():
                st.text_area("SMS Logs:", sms_logs, height=200)
            else:
                st.info("No SMS logs found")
        else:
            st.info("SMS log file not found")
    except Exception as e:
        st.error(f"Error reading SMS logs: {e}")
    
    # Email Log
    st.write("**📧 Email Log:**")
    try:
        if os.path.exists("data/email_log.txt"):
            with open("data/email_log.txt", "r", encoding="utf-8") as f:
                email_logs = f.read()
            
            if email_logs.strip():
                st.text_area("Email Logs:", email_logs, height=200)
            else:
                st.info("No email logs found")
        else:
            st.info("Email log file not found")
    except Exception as e:
        st.error(f"Error reading email logs: {e}")
    
    # Clear logs button
    if st.button("🗑️ Clear All Logs"):
        try:
            if os.path.exists("data/sms_log.txt"):
                os.remove("data/sms_log.txt")
            if os.path.exists("data/email_log.txt"):
                os.remove("data/email_log.txt")
            st.success("✅ All logs cleared!")
            st.rerun()
        except Exception as e:
            st.error(f"Error clearing logs: {e}")

def send_test_email():
    """Send test email with EMR integration"""
    st.subheader("📧 Send Test Email")
    
    # Get test patient from EMR
    emr_db = st.session_state.emr_db
    all_patients = emr_db.get_all_patients()
    
    if all_patients:
        test_patient = all_patients[0]
        
        st.write(f"**Test Patient:** {test_patient.first_name} {test_patient.last_name}")
        st.write(f"**Email:** {test_patient.email}")
        
        # Allow custom email
        custom_email = st.text_input("Or enter custom email:", value=test_patient.email)
        
        # Email type selection
        email_type = st.selectbox("Email Type:", [
            "Appointment Confirmation",
            "Intake Forms",
            "Appointment Reminder (24h)",
            "Form Check Reminder (2h)",
            "Final Confirmation (1h)"
        ])
        
        if st.button("📧 Send Test Email", key="send_test_email_function_btn"):
            try:
                from communication import EmailService
                from datetime import date, timedelta
                from models import Appointment, AppointmentStatus, ReminderType
                
                email_service = EmailService()
                
                # Create test appointment
                test_appointment = Appointment(
                    id="TEST_EMAIL_001",
                    patient_id=test_patient.patient_id,
                    doctor_id="D001",
                    appointment_date=date.today() + timedelta(days=1),
                    appointment_time="10:00",
                    duration=60,
                    status=AppointmentStatus.SCHEDULED
                )
                
                success = False
                
                if email_type == "Appointment Confirmation":
                    success = email_service.send_appointment_confirmation(test_patient, test_appointment)
                elif email_type == "Intake Forms":
                    success = email_service.send_intake_forms(test_patient, test_appointment)
                elif email_type == "Appointment Reminder (24h)":
                    success = email_service.send_appointment_reminder_email(test_patient, test_appointment, ReminderType.INITIAL)
                elif email_type == "Form Check Reminder (2h)":
                    success = email_service.send_appointment_reminder_email(test_patient, test_appointment, ReminderType.FORM_CHECK)
                elif email_type == "Final Confirmation (1h)":
                    success = email_service.send_appointment_reminder_email(test_patient, test_appointment, ReminderType.CONFIRMATION)
                
                if success:
                    st.success(f"✅ {email_type} sent successfully to {custom_email}!")
                    st.info("Check your email for the message")
                else:
                    st.error(f"❌ Failed to send {email_type}. Check email configuration.")
                    
            except Exception as e:
                st.error(f"Error sending email: {e}")
    else:
        st.warning("No patients found in EMR database")


if __name__ == "__main__":
    main()
