#!/bin/bash

# ==============================================
# MyAgent Booking - Deployment & Testing Script
# ==============================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}==================================="
echo -e "MyAgent Booking Deployment Script"
echo -e "===================================${NC}\n"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Step 1: Check prerequisites
echo -e "${YELLOW}[1/7] Checking prerequisites...${NC}"

if ! command_exists python3; then
    print_error "Python 3 is not installed"
    exit 1
fi
print_status "Python 3 installed"

if ! command_exists pip3; then
    print_error "pip3 is not installed"
    exit 1
fi
print_status "pip3 installed"

# Step 2: Create virtual environment
echo -e "\n${YELLOW}[2/7] Setting up virtual environment...${NC}"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
print_status "Virtual environment activated"

# Step 3: Install dependencies
echo -e "\n${YELLOW}[3/7] Installing dependencies...${NC}"

pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
print_status "Dependencies installed"

# Step 4: Check environment variables
echo -e "\n${YELLOW}[4/7] Checking environment configuration...${NC}"

if [ ! -f ".env" ]; then
    print_warning ".env file not found"
    echo "Creating from template..."
    cp .env.example .env
    print_status ".env file created - Please configure it with your API keys"
    print_warning "Edit .env file before proceeding"
    exit 0
fi
print_status ".env file found"

# Check critical environment variables
source .env

if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your_gemini_api_key_here" ]; then
    print_error "GOOGLE_API_KEY not configured in .env"
    exit 1
fi
print_status "Gemini API key configured"

if [ -z "$SENDER_EMAIL" ] || [ "$SENDER_EMAIL" = "your_brevo_login@smtp-brevo.com" ]; then
    print_warning "Email service not configured (optional)"
else
    print_status "Email service configured"
fi

# Step 5: Initialize database
echo -e "\n${YELLOW}[5/7] Initializing database...${NC}"

python3 << EOF
from database import get_database
db = get_database()
print("Database initialized successfully")
EOF

if [ $? -eq 0 ]; then
    print_status "Database initialized"
else
    print_error "Database initialization failed"
    exit 1
fi

# Step 6: Run tests
echo -e "\n${YELLOW}[6/7] Running tests...${NC}"

python3 << EOF
import sys

# Test imports
try:
    
    from database import get_database
    from email_service import get_email_service
    from budget_and_scoring import BudgetTracker, AttractionScorer
    from monitoring_agent import get_monitoring_agent
    print("✓ All modules imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Test database
try:
    db = get_database()
    # Create test user
    user_id = db.create_user(
        email="test@test.com",
        password="testpassword123",
        full_name="Test User",
        home_location="Test Location"
    )
    if user_id:
        # Authenticate
        user = db.authenticate_user("test@test.com", "testpassword123")
        if user:
            print("✓ Database operations working")
        else:
            print("✗ Authentication failed")
            sys.exit(1)
    else:
        # User might already exist, try to authenticate
        user = db.authenticate_user("test@test.com", "testpassword123")
        if user:
            print("✓ Database operations working (test user exists)")
        else:
            print("✗ Test user creation/authentication failed")
            sys.exit(1)
except Exception as e:
    print(f"✗ Database test failed: {e}")
    sys.exit(1)

# Test budget tracker
try:
    tracker = BudgetTracker(1000.0)
    tracker.add_expense('flights', 500.0)
    status = tracker.get_budget_status()
    assert status['percentage'] == 50.0, "Budget calculation incorrect"
    print("✓ Budget tracker working")
except Exception as e:
    print(f"✗ Budget tracker test failed: {e}")
    sys.exit(1)

# Test Gemini agent initialization
try:
    from agent import TravelAgent
    agent2 = TravelAgent()
    print("✓ Gemini agent initialized")
except Exception as e:
    print(f"✗ Gemini agent initialization failed: {e}")
    print("  Make sure GOOGLE_API_KEY is correctly set in .env")
    sys.exit(1)

print("\n✅ All tests passed!")
EOF

if [ $? -eq 0 ]; then
    print_status "All tests passed"
else
    print_error "Tests failed"
    exit 1
fi

# Step 7: Start application
echo -e "\n${YELLOW}[7/7] Starting application...${NC}"

echo -e "\n${GREEN}==================================="
echo -e "Setup completed successfully! 🎉"
echo -e "===================================${NC}\n"

echo -e "Starting Streamlit app...\n"
echo -e "${YELLOW}Available apps:${NC}"
echo -e "  1. Enhanced app: ${GREEN}streamlit run app_enhanced.py${NC}"
echo -e "  2. Original app: ${GREEN}streamlit run app.py${NC}\n"

read -p "Which app would you like to run? (1/2) [1]: " choice
choice=${choice:-1}

if [ "$choice" = "1" ]; then
    nohup streamlit run app_premium_with_auth.py --server.address 0.0.0.0 --server.port 8051 --server.headless true&
elif [ "$choice" = "2" ]; then
    nohup streamlit run app.py --server.address 0.0.0.0 --server.port 8051 --server.headless true&
else
    echo -e "${RED}Invalid choice${NC}"
    exit 1
fi
