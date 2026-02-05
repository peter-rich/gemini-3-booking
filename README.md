# gemini-3-booking
## Setting
### Install Google latest Gemini 3 SDK
`pip install -U google-genai`

### install the front-end app
`pip install streamlit`

### protect your api key
`pip install python-dotenv`

### .env setting
`
SMTP_PORT=587
SENDER_EMAIL=a1afbb001@smtp-brevo.com
SENDER_PASSWORD=your@Pass@key
EMAIL_USE_TLS=True

EMAIL_FROM=noreply@myagentbooking.com
EMAIL_FROM_NAME=MyAgent Booking
EMAIL_REPLY_TO=support@myagentbooking.com

`
### Run
`python3 -m streamlit run app.py`

