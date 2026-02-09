# 🚀 MyAgent Booking - AI-Powered Travel Planning System

## Demo
My Agent Booking(https://www.myagentbooking.com/)

Race page(https://devpost.com/software/my-agent-booking)
A complete, production-ready travel planning system with AI-powered itinerary generation, real-time flight monitoring, budget tracking, and automated email notifications.

## ✨ Core Features

### 🎯 **1. Intelligent Travel Planning**
- Multi-airport flight comparison (EWR, JFK)
- 3-tier hotel recommendations (budget/comfort/luxury)
- Ground transportation estimates
- Structured JSON output for automation

### 👤 **2. User Management**
- Secure authentication with password hashing
- Personal trip history
- Customizable home location and preferences
- SQLite database for persistent storage

### 💰 **3. Budget Tracking**
- Real-time budget monitoring
- Category-wise breakdown (flights, hotels, food, activities)
- Alert system at 75%, 90%, and 100% thresholds
- Smart budget adjustment suggestions

### ⭐ **4. Attraction Scoring**
- Integration-ready for TripAdvisor API
- Attraction recommendations based on interests
- Rating and popularity data
- Visit duration and timing suggestions

### 🎤 **5. Conference Trip Detection**
- Automatic detection of business/conference trips
- Pre-built conference schedule templates
- Integration with event calendars

### 🛡️ **6. 24/7 Real-Time Monitoring**
- Flight status tracking (delays, cancellations, gate changes)
- Weather alerts for destinations
- Price drop notifications
- **External flight tracking** - Monitor flights booked outside the system

### 📧 **7. Email Notifications (Brevo SMTP)**
- Professional itinerary emails with PDF/ICS attachments
- Flight alert notifications
- Budget warnings
- Beautiful HTML templates

### 📄 **8. Export Capabilities**
- Professional PDF itineraries with booking links
- iCalendar (.ics) files for calendar apps
- One-click email delivery

## 🏗️ System Architecture

```
myagent-booking/
├── agent.py                  # Gemini AI travel agent
├── app_enhanced.py           # Main Streamlit application
├── database.py               # SQLite database & user management
├── email_service.py          # Brevo SMTP email service
├── budget_and_scoring.py     # Budget tracking & attraction scoring
├── monitoring_agent.py       # 24/7 flight monitoring system
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables
└── README.md                 # This file
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
git clone <your-repo-url>
cd myagent-booking

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file in the project root:

```env
# Gemini API (for AI agent)
GOOGLE_API_KEY=your_gemini_api_key_here

# Brevo SMTP Configuration
SMTP_PORT=587
SENDER_EMAIL=your_brevo_login@smtp-brevo.com
SENDER_PASSWORD=your_brevo_smtp_key
EMAIL_USE_TLS=True

# Email Settings
EMAIL_FROM=noreply@myagentbooking.com
EMAIL_FROM_NAME=MyAgent Booking
EMAIL_REPLY_TO=support@myagentbooking.com

# Optional: Flight Tracking APIs
FLIGHTAWARE_API_KEY=your_key_here
AVIATIONSTACK_API_KEY=your_key_here

# Optional: Attraction APIs
TRIPADVISOR_API_KEY=your_key_here
GOOGLE_PLACES_API_KEY=your_key_here
```

### 3. Run the Application

```bash
# Run enhanced version with all features
bash deploy.sh

```

Visit `http://localhost:8501` in your browser.

## 📚 Feature Details

### User Authentication System

```python
# Create new user
user_id = db.create_user(
    email="user@example.com",
    password="secure_password",
    full_name="John Doe",
    home_location="Piscataway, NJ"
)

# Authenticate user
user = db.authenticate_user("user@example.com", "password")
if user:
    print(f"Welcome {user.full_name}!")
```

### Budget Tracking

```python
# Initialize budget tracker
tracker = BudgetTracker(total_budget=3000.0)

# Add expenses
tracker.add_expense('flights', 1200.0)
tracker.add_expense('hotels', 800.0)
tracker.add_expense('food', 300.0)

# Check status
status = tracker.get_budget_status()
print(f"Used: ${status['used']:.2f} ({status['percentage']:.1f}%)")
print(f"Alert Level: {status['alert_level']}")

# Get suggestions if over budget
if status['alert_level'] in ['warning', 'critical']:
    suggestions = suggest_budget_adjustments(status)
    for suggestion in suggestions:
        print(f"💡 {suggestion}")
```

### Real-Time Flight Monitoring

```python
# Initialize monitoring agent
monitoring_agent = get_monitoring_agent(db, email_service)

# Start background monitoring
monitoring_agent.start_background_monitoring()

# Monitor a trip
monitoring_agent.start_monitoring(trip_id=123)

# Add external flight (booked outside system)
monitoring_agent.add_external_flight(
    trip_id=123,
    flight_number="UA456",
    flight_date="2025-03-15",
    user_email="user@example.com"
)

# Stop monitoring
monitoring_agent.stop_monitoring(trip_id=123)
```

### Email Notifications

```python
# Send itinerary email
email_service.send_itinerary_email(
    to_email="user@example.com",
    user_name="John Doe",
    trip_name="Tokyo Adventure",
    destination="Tokyo, Japan",
    depart_date="2025-03-15",
    return_date="2025-03-20",
    pdf_content=pdf_bytes,
    ics_content=ics_bytes
)

# Send flight alert
email_service.send_flight_alert(
    to_email="user@example.com",
    user_name="John Doe",
    alert_type="warning",
    flight_info={
        'flight_number': 'UA123',
        'route': 'EWR → NRT',
        'scheduled_time': '2025-03-15T10:00:00',
        'updated_time': '2025-03-15T11:30:00'
    },
    message="Flight UA123 delayed by 90 minutes"
)

# Send budget alert
email_service.send_budget_alert(
    to_email="user@example.com",
    user_name="John Doe",
    trip_name="Tokyo Adventure",
    budget=3000.0,
    current_cost=2800.0,
    over_budget=False
)
```

### Conference Trip Detection

```python
# Detect conference trip
query = "Plan a trip to SF for AWS re:Invent Dec 1-5"
is_conference = ConferenceDetector.is_conference_trip(query, [])
print(f"Conference trip: {is_conference}")  # True

# Extract conference details
details = ConferenceDetector.extract_conference_details(query)
print(f"Conference: {details['conference_name']}")  # "AWS re:Invent"

# Create schedule
schedule = ConferenceDetector.create_conference_schedule(
    conference_details=details,
    trip_dates=("2025-12-01", "2025-12-05")
)
```

### Attraction Scoring

```python
# Initialize scorer
scorer = AttractionScorer()

# Get attraction details
score_data = scorer.get_attraction_score(
    location="Tokyo",
    attraction_name="Senso-ji Temple"
)
print(f"Rating: {score_data['rating']}/5")
print(f"Reviews: {score_data['total_reviews']}")
print(f"Best time: {score_data['best_time']}")

# Get recommendations
attractions = scorer.recommend_attractions(
    destination="Tokyo",
    interests=['culture', 'food', 'nature'],
    budget='medium'
)
for attr in attractions:
    print(f"{attr['name']} - Score: {attr['score']}")
```

## 🔧 Configuration

### Database

The system uses SQLite for persistence. On first run, it automatically creates:
- `travel_agent.db` - Main database file
- Tables: users, trip_history, monitoring_alerts, user_preferences

### Email Service (Brevo)

1. Sign up at [Brevo](https://www.brevo.com/)
2. Get your SMTP credentials from Settings → SMTP & API
3. Add to `.env` file
4. The system handles:
   - TLS encryption
   - HTML email formatting
   - File attachments (PDF, ICS)
   - Email templates

### Flight Monitoring APIs (Optional)

For production deployment, integrate with:

1. **FlightAware API** (Recommended)
   - Sign up: https://flightaware.com/commercial/flightxml/
   - Add `FLIGHTAWARE_API_KEY` to `.env`

2. **AviationStack API** (Backup)
   - Sign up: https://aviationstack.com/
   - Add `AVIATIONSTACK_API_KEY` to `.env`

3. **FlightStats API** (Alternative)
   - Sign up: https://www.flightstats.com/
   - Add API key to `.env`

### Attraction Data APIs (Optional)

1. **TripAdvisor Content API**
   - Sign up for TripAdvisor developer account
   - Add `TRIPADVISOR_API_KEY` to `.env`

2. **Google Places API**
   - Enable in Google Cloud Console
   - Add `GOOGLE_PLACES_API_KEY` to `.env`

## 🔒 Security Features

- ✅ Password hashing with SHA-256
- ✅ No hardcoded API keys
- ✅ Environment variable configuration
- ✅ Secure SMTP with TLS
- ✅ SQL injection prevention with parameterized queries
- ✅ Session management
- ✅ User authentication and authorization

## 📊 Monitoring Dashboard

The monitoring agent provides:

- **Flight Status**: Every 5 minutes
- **Weather Updates**: Every hour
- **Price Changes**: Every 6 hours
- **Email Alerts**: Automatic for critical events

Alert Severity Levels:
- 🟢 **Low**: Information updates
- 🟡 **Medium**: Minor delays (15-30 min)
- 🟠 **High**: Major delays (60+ min)
- 🔴 **Critical**: Cancellations, major disruptions

## 🚀 Production Deployment

### Using Streamlit Cloud

1. Push code to GitHub
2. Connect to [Streamlit Cloud](https://streamlit.io/cloud)
3. Add secrets in dashboard (from `.env`)
4. Deploy!

### Using Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "app_enhanced.py", "--server.port=8501"]
```

```bash
docker build -t myagent-booking .
docker run -p 8501:8501 --env-file .env myagent-booking
```

### Using Heroku

```bash
# Install Heroku CLI
heroku create myagent-booking

# Add buildpack
heroku buildpacks:set heroku/python

# Set environment variables
heroku config:set $(cat .env | sed '/^#/d;/^$/d')

# Deploy
git push heroku main
```

## 🧪 Testing

```python
# Test database
from database import get_database
db = get_database()
user_id = db.create_user("test@test.com", "password123", "Test User")
user = db.authenticate_user("test@test.com", "password123")
assert user is not None

# Test email service
from email_service import get_email_service
email = get_email_service()
# Make sure SMTP credentials are in .env first!

# Test budget tracker
from budget_and_scoring import BudgetTracker
tracker = BudgetTracker(1000.0)
tracker.add_expense('flights', 500.0)
status = tracker.get_budget_status()
assert status['percentage'] == 50.0

# Test monitoring agent
from monitoring_agent import get_monitoring_agent
agent = get_monitoring_agent(db, email)
agent.start_background_monitoring()
# Agent now running in background thread
```

## 📝 TODO / Roadmap

- [ ] Integration with real flight tracking APIs
- [ ] TripAdvisor API integration
- [ ] Google Calendar sync
- [ ] Mobile app (React Native)
- [ ] Multi-currency support
- [ ] Group trip planning
- [ ] Travel insurance recommendations
- [ ] Visa requirement checker
- [ ] Loyalty program integration
- [ ] AI-powered travel recommendations based on history

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🆘 Support

For issues or questions:
- Email: support@myagentbooking.com
- GitHub Issues: [Create an issue](your-repo-url/issues)

## 🙏 Acknowledgments

- Powered by Google Gemini AI
- Email service by Brevo
- PDF generation with ReportLab
- Built with Streamlit

---

**Made with ❤️ for travelers worldwide**
