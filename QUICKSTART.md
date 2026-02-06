# 🚀 Quick Start Guide - MyAgent Booking

## 5-Minute Setup

### Step 1: Get Your API Keys (3 minutes)

#### Required: Gemini API
1. Visit https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

#### Required: Brevo Email (Free tier available)
1. Sign up at https://www.brevo.com/ (Free account - 300 emails/day)
2. Go to Settings → SMTP & API
3. Copy:
   - Login: `xxx@smtp-brevo.com`
   - SMTP key: `xsmtpsib-xxxxx...`

### Step 2: Install & Configure (2 minutes)

```bash
# Clone and setup
git clone <your-repo>
cd myagent-booking

# Copy environment template
cp .env.example .env

# Edit .env with your keys
nano .env  # or use any text editor
```

Add your keys to `.env`:
```env
GOOGLE_API_KEY=<your-gemini-key>
SENDER_EMAIL=<your-brevo-login>
SENDER_PASSWORD=<your-brevo-smtp-key>
```

### Step 3: Run Automated Setup

```bash
# One command to rule them all
bash deploy.sh
```

This script will:
- ✅ Check prerequisites
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Initialize database
- ✅ Run tests
- ✅ Start the app

That's it! Your app will open at `http://localhost:8501`

---

## First Time Usage

### 1. Create Account
- Click "Sign Up" tab
- Fill in your details
- Create account

### 2. Plan Your First Trip

**Example Query:**
```
Plan a 5-day trip to Tokyo from March 15-20, 2025. 
I want to stay in Shibuya area. Budget: $3000.
I'm interested in culture, food, and technology.
```

### 3. Get Your Results

You'll receive:
- ✈️ Flight options from EWR and JFK
- 🏨 Hotels in 3 price tiers
- 🚖 Transportation estimates
- ⭐ Top-rated attractions
- 📊 Budget breakdown
- 📅 Calendar file
- 📄 PDF itinerary

### 4. Enable Monitoring

Check "Enable 24/7 flight monitoring" to get:
- Real-time flight status updates
- Delay and gate change alerts
- Weather warnings
- Email notifications

---

## Feature Highlights

### 💰 Budget Tracking

Your budget is monitored in real-time:
- 🟢 **Safe**: < 75% used
- 🟡 **Caution**: 75-90% used  
- 🟠 **Warning**: 90-100% used
- 🔴 **Critical**: > 100% used

Get smart suggestions when approaching limits!

### 📧 Email Notifications

Automatic emails for:
- ✅ Complete itinerary (PDF + Calendar)
- ⚠️ Flight delays/cancellations
- 💰 Budget alerts
- 🌤️ Weather warnings

### 🛡️ External Flight Tracking

**Even if you booked elsewhere:**
1. Go to "Trip History"
2. Select your trip
3. Enter flight number (e.g., "UA123")
4. Click "Add to Monitoring"

Now you'll get alerts for that flight too!

### 🎤 Conference Trips

Automatically detects when you mention:
- Conference names (e.g., "AWS re:Invent")
- Business meetings
- Conventions or summits

And adds:
- Registration blocks
- Keynote schedules
- Networking events
- Session times

---

## Common Use Cases

### Business Trip
```
Plan a 3-day business trip to San Francisco for Google I/O 
from May 14-16. Need hotel near Moscone Center. Budget: $2500.
```

### Family Vacation
```
Plan a 7-day family vacation to Orlando from June 1-7. 
We want to visit Disney World and Universal Studios. 
Family of 4, budget: $5000.
```

### Weekend Getaway
```
Plan a quick weekend trip to Boston from Friday to Sunday. 
Interested in history and seafood. Budget: $800.
```

### International Trip
```
Plan a 10-day trip to Japan (Tokyo and Kyoto) from March 15-24.
Interested in temples, food, and shopping. Budget: $4000.
```

---

## Troubleshooting

### "Failed to generate plan"
- Check your GOOGLE_API_KEY is valid
- Ensure internet connection
- Try a simpler query first

### "Email not sent"
- Verify Brevo SMTP credentials in .env
- Check SENDER_EMAIL and SENDER_PASSWORD
- Ensure EMAIL_USE_TLS=True

### "Database error"
- Delete `travel_agent.db`
- Restart the app (will recreate)

### "No flights found"
- Be specific with dates and destination
- Check date format: "March 15-20" or "3/15 to 3/20"
- Try alternative airport codes

---

## Production Tips

### For Better Results
1. **Be Specific**: Include dates, locations, interests
2. **Mention Budget**: Helps AI tailor recommendations
3. **Add Context**: "Business trip" vs "vacation" matters
4. **Use Clear Dates**: "March 15-20" better than "next month"

### Security Best Practices
1. Never commit `.env` to git
2. Use strong passwords (8+ characters)
3. Enable 2FA on email service
4. Regular database backups

### Performance Optimization
1. Clear old trips from database periodically
2. Limit monitoring to active trips only
3. Use specific queries (faster responses)

---

## Need Help?

- 📧 Email: support@myagentbooking.com
- 📖 Full README: [README.md](README.md)
- 🐛 Report Issues: GitHub Issues
- 💬 Questions: GitHub Discussions

---

## What's Next?

1. ⭐ Star the repo
2. 🔄 Share with friends
3. 🚀 Deploy to Streamlit Cloud (free!)
4. 🛠️ Customize for your needs
5. 🤝 Contribute improvements

---

**Happy Travels! ✈️🌍**
