# Medical Appointment Scheduling AI Agent

A comprehensive AI-powered medical appointment scheduling system built with LangChain, Perplexity LLM, and Streamlit. This system automates patient booking, reduces no-shows, and streamlines clinic operations.

## 🏥 Features

### Core Features (MVP-1)
- **Patient Greeting & Data Collection**: Natural language processing to collect patient information
- **Patient Lookup**: Database integration to identify new vs returning patients
- **Smart Scheduling**: 60min for new patients, 30min for returning patients
- **Calendar Integration**: Real-time availability checking and slot booking
- **Insurance Collection**: Structured data capture for insurance information
- **Appointment Confirmation**: Excel export and confirmation generation
- **Form Distribution**: Automated email delivery of intake forms
- **Reminder System**: 3 automated reminders with confirmation tracking

### Technical Features
- **Perplexity LLM Integration**: Pre-configured API for natural language processing
- **EMR Database System**: 50 synthetic patients with automatic lookup
- **Communication System**: Real email and SMS with Twilio integration
- **Web Interface**: Streamlit-based chatbot interface with auto-initialization
- **Admin Dashboard**: View patients, doctors, appointments, and exports

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Perplexity API key (pre-configured)
- Email account for SMTP (optional, for email notifications)
- Twilio account (optional, for SMS notifications)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd medical-scheduling-agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Generate sample data**
   ```bash
   python generate_data.py
   ```

4. **Configure communication (optional)**
   ```bash
   # Run the quick setup script
   python quick_setup.py
   ```
   Or manually set environment variables:
   ```bash
   # Create .env file or set environment variables
   export PERPLEXITY_API_KEY="your_perplexity_api_key_here"  # Pre-configured
   export EMAIL_USERNAME="your_email@gmail.com"
   export EMAIL_PASSWORD="your_app_password"
   export TWILIO_ACCOUNT_SID="your_twilio_sid"
   export TWILIO_AUTH_TOKEN="your_twilio_token"
   export TWILIO_PHONE_NUMBER="+1234567890"
   ```

5. **Run the application**
   ```bash
   python -m streamlit run app.py --server.port 8501
   ```

6. **Access the web interface**
   - Open your browser to `http://localhost:8501`
   - No API key needed - Perplexity is pre-configured!
   - Start chatting with the AI agent immediately!

## 📁 Project Structure

```
medical-scheduling-agent/
├── app.py                           # Streamlit web interface
├── simple_agent_fixed.py           # Main AI agent (Perplexity-powered)
├── agent.py                        # Full LangGraph AI agent (advanced)
├── tools.py                        # LangChain tools
├── database.py                     # Database operations
├── emr_database.py                 # EMR database with patient lookup
├── communication.py                # Email/SMS services with Twilio
├── models.py                       # Pydantic data models
├── config.py                       # Configuration settings
├── perplexity_integration.py       # Perplexity LLM integration
├── webhook_handler.py              # Twilio webhook handler
├── quick_setup.py                  # Quick configuration setup
├── generate_data.py                # Synthetic data generation
├── demo.py                         # Demo script
├── requirements.txt                # Python dependencies
├── TECHNICAL_APPROACH_DOCUMENT.md  # Technical documentation
├── COMMUNICATION_SETUP.md          # Communication setup guide
├── README.md                       # Main documentation
└── data/                           # Data directory
    ├── patients.csv               # Patient database
    ├── doctors_schedule.xlsx      # Doctor schedules
    ├── appointments.json          # Appointment records
    ├── reminders.json             # Reminder records
    ├── email_log.txt              # Email communication log
    ├── sms_log.txt                # SMS communication log
    └── forms/                     # Generated intake forms
```

## 🤖 Usage

### Web Interface
1. **Start the app**: `python -m streamlit run app.py --server.port 8501`
2. **No setup needed**: Perplexity API is pre-configured!
3. **Chat with AI**: Type messages to interact with the scheduling agent
4. **Admin functions**: Use sidebar buttons to view data and exports

### Demo Script
```bash
python demo.py
```

### API Usage
```python
from simple_agent_fixed import SimpleMedicalSchedulingAgent

# Initialize agent (Perplexity API is pre-configured)
agent = SimpleMedicalSchedulingAgent()

# Process messages
result = agent.process_message("Hi, I'd like to schedule an appointment")
```

## 🔧 Configuration

### Environment Variables
- `PERPLEXITY_API_KEY`: Your Perplexity API key (pre-configured)
- `EMAIL_USERNAME`: SMTP username for email notifications
- `EMAIL_PASSWORD`: SMTP password for email notifications
- `TWILIO_ACCOUNT_SID`: Twilio Account SID for SMS
- `TWILIO_AUTH_TOKEN`: Twilio Auth Token for SMS
- `TWILIO_PHONE_NUMBER`: Twilio phone number for SMS
- `SMTP_SERVER`: SMTP server (default: smtp.gmail.com)
- `SMTP_PORT`: SMTP port (default: 587)

### Business Rules
- New patients: 60-minute appointments
- Returning patients: 30-minute appointments
- Working hours: 9 AM - 5 PM
- Lunch break: 12 PM - 1 PM
- Reminders: 24h, 2h, and 1h before appointment

## 📊 Data Management

### Patient Database
- CSV format with 50 synthetic patients
- Includes demographics, contact info, and patient type
- Supports new patient registration

### Doctor Schedules
- Excel format with availability matrices
- Multiple specialties and locations
- Time slot management

### Appointments
- JSON format for real-time updates
- Status tracking (scheduled, confirmed, cancelled)
- Insurance information storage

## 📧 Communication System

### Email Notifications
- Appointment confirmations
- Intake form distribution
- Automated reminders

### SMS Reminders (Simulated)
- 3-stage reminder system
- Response tracking
- Confirmation/cancellation handling

## 🧪 Testing

### Run Demo
```bash
python demo.py
```

### Test Individual Components
```python
# Test database operations
from database import DatabaseManager
db = DatabaseManager()
patients = db.load_patients()

# Test communication
from communication import CommunicationManager
comm = CommunicationManager()
```

## 📈 Business Impact

This system addresses key healthcare operational challenges:
- **Reduces no-shows**: Automated reminders and confirmations
- **Streamlines scheduling**: AI-powered conversation flow
- **Improves data accuracy**: Structured data collection
- **Enhances patient experience**: 24/7 availability and natural language interaction

## 🔒 Security & Privacy

- **Local data storage**: No external API calls for sensitive data
- **Input validation**: Comprehensive validation and sanitization
- **Access control**: Simple authentication for admin functions
- **Data privacy**: HIPAA-compliant data handling practices

## 🚧 Future Enhancements

- **Database integration**: Migrate to PostgreSQL/MySQL
- **Real SMS integration**: Twilio or similar service
- **Advanced NLP**: Better intent recognition and entity extraction
- **Multi-language support**: Internationalization
- **Mobile app**: React Native or Flutter app
- **Analytics dashboard**: Appointment metrics and insights

## 📝 Technical Approach

See `technical_approach.md` for detailed technical documentation including:
- Architecture overview
- Framework choice justification
- Integration strategy
- Key technical decisions
- Challenges and solutions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For questions or issues:
1. Check the documentation
2. Run the demo script
3. Review the technical approach document
4. Open an issue on GitHub

## 🎯 Success Metrics

- ✅ Functional demo with complete patient booking workflow
- ✅ Data accuracy with correct patient classification and scheduling
- ✅ Integration success with Excel exports and calendar management
- ✅ Clean, documented, and executable codebase
- ✅ Natural conversation flow with error handling
- ✅ Complete business logic implementation

---

**Built with ❤️ for healthcare innovation**
