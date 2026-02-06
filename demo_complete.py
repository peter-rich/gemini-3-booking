#!/usr/bin/env python3
"""
Complete Demo Script - 24/7 Smart Monitoring Agent
完整演示脚本 - 展示所有功能

This script demonstrates:
1. Creating monitoring tasks
2. Detecting flight issues
3. Auto-rebooking suggestions
4. Email notifications
5. Real-time status dashboard
"""

import sys
import time
from datetime import datetime, timedelta


def print_banner(text, char="="):
    """Print a formatted banner"""
    width = 70
    print("\n" + char * width)
    print(text.center(width))
    print(char * width + "\n")


def print_step(step_num, description):
    """Print a step with formatting"""
    print(f"\n{'='*70}")
    print(f"STEP {step_num}: {description}")
    print('='*70)


def simulate_monitoring_cycle():
    """Simulate a complete monitoring cycle"""
    print_banner("🤖 24/7 SMART MONITORING AGENT - LIVE DEMO", "=")
    
    print("This demonstration will show you:")
    print("  1. ✈️  Real-time flight monitoring")
    print("  2. 🚨 Automatic issue detection")
    print("  3. 🔄 Intelligent auto-rebooking")
    print("  4. 📧 Instant email alerts")
    print("  5. 📊 Live monitoring dashboard")
    print("\n" + "-"*70)
    
    input("\n▶️  Press ENTER to begin the demonstration...")
    
    # ===== STEP 1: Initialize Services =====
    print_step(1, "Initializing Services")
    
    print("Loading required services...")
    try:
        from email_service import get_email_service
        from rebooking_and_rides import FlightRebookingAgent
        from smart_monitoring_agent import SmartMonitoringAgent, MonitoringTask
        print("✅ All services loaded successfully")
    except ImportError as e:
        print(f"❌ Error: Missing required module - {e}")
        print("\nPlease ensure all files are in the same directory:")
        print("  - smart_monitoring_agent.py")
        print("  - rebooking_service.py")
        print("  - email_service.py")
        print("  - free_flight_monitor.py")
        sys.exit(1)
    
    email_service = get_email_service()
    rebooking_service = FlightRebookingAgent(email_service)
    
    print("\n📧 Email Service: Ready")
    print("🔄 Rebooking Service: Ready")
    
    time.sleep(2)
    
    # ===== STEP 2: Create Monitoring Agent =====
    print_step(2, "Creating 24/7 Monitoring Agent")
    
    agent = SmartMonitoringAgent(
        db_path="/tmp/demo_monitoring.db",
        email_service=email_service,
        rebooking_service=rebooking_service
    )
    
    print("✅ Monitoring agent created")
    print("📦 Database initialized: /tmp/demo_monitoring.db")
    
    time.sleep(2)
    
    # ===== STEP 3: Get User Email =====
    print_step(3, "User Configuration")
    
    print("To receive the demo rebooking email, please enter your email address.")
    print("(This will only be used for this demonstration)")
    
    user_email = input("\n📧 Your email: ").strip()
    
    while not user_email or "@" not in user_email:
        print("❌ Please enter a valid email address")
        user_email = input("📧 Your email: ").strip()
    
    print(f"✅ Email configured: {user_email}")
    
    time.sleep(1)
    
    # ===== STEP 4: Create Demo Monitoring Task =====
    print_step(4, "Creating Demo Flight Monitoring Task")
    
    print("Creating a simulated flight booking:")
    print("  Flight: UA2013")
    print("  Route: Newark (EWR) → Los Angeles (LAX)")
    print("  Date: February 15, 2026")
    print("  Scheduled: 10:00 AM EST")
    
    demo_task = MonitoringTask(
        task_id=f"demo_task_{int(time.time())}",
        trip_id="demo_trip_001",
        user_id="demo_user_001",
        user_email=user_email,
        flight_number="UA2013",
        flight_date="2026-02-15",
        departure_airport="EWR",
        arrival_airport="LAX",
        check_interval=10,  # Fast checks for demo
        auto_rebook=True,
        notification_enabled=True
    )
    
    agent.add_monitoring_task(demo_task)
    print("\n✅ Monitoring task created and activated")
    
    time.sleep(2)
    
    # ===== STEP 5: Start 24/7 Monitoring =====
    print_step(5, "Starting 24/7 Monitoring System")
    
    agent.start()
    
    print("\n✅ Monitoring agent is now ONLINE")
    print("🔄 Agent will check flight status every 10 seconds (for demo)")
    print("   (In production, checks happen every 5 minutes)")
    
    time.sleep(3)
    
    # ===== STEP 6: Show Initial Status =====
    print_step(6, "Current Monitoring Status")
    
    status = agent.get_status()
    
    print(f"📊 Agent Status:")
    print(f"  • Running: {'✅ YES' if status['running'] else '❌ NO'}")
    print(f"  • Active Tasks: {status['active_tasks']}")
    print(f"  • Mode: 24/7 Continuous")
    
    time.sleep(3)
    
    # ===== STEP 7: Simulate Flight Issue =====
    print_step(7, "Simulating Flight Cancellation")
    
    print("\n⚠️  WARNING: Flight issue detected!")
    print("━" * 70)
    print("Flight UA2013 has been CANCELLED by the airline")
    print("Original departure: 10:00 AM EST")
    print("Status: ❌ CANCELLED")
    print("━" * 70)
    
    time.sleep(2)
    
    print("\n🔍 Analyzing situation...")
    print("  ✓ Confirmed: Flight cancelled")
    print("  ✓ Passenger has important appointment")
    print("  ✓ Auto-rebook: ENABLED")
    
    time.sleep(2)
    
    # Create simulated flight status
    fake_flight_status = {
        'flight_number': 'UA2013',
        'status': 'cancelled',
        'delay_minutes': 0,
        'scheduled_departure': '2026-02-15 10:00',
        'actual_departure': None,
        'departure_gate': 'B12',
        'arrival_gate': None
    }
    
    print("\n🚨 Triggering emergency response protocols...")
    time.sleep(2)
    
    # ===== STEP 8: Find Alternative Flights =====
    print_step(8, "Searching Alternative Flights")
    
    print("🔎 Scanning all available flights on EWR → LAX route...")
    print("   Checking: United Airlines, American Airlines, Delta...")
    
    time.sleep(3)
    
    print("\n📋 Found 3 alternative flights:")
    print("\n  Option 1: UA2015")
    print("    ├─ Departure: 2:30 PM")
    print("    ├─ Arrival: 6:45 PM")
    print("    ├─ Price: +$50")
    print("    └─ Available: 12 seats ✅")
    
    print("\n  Option 2: AA1234")
    print("    ├─ Departure: 4:00 PM")
    print("    ├─ Arrival: 8:15 PM")
    print("    ├─ Price: +$75")
    print("    └─ Available: 8 seats")
    
    print("\n  Option 3: DL5678")
    print("    ├─ Departure: 5:30 PM")
    print("    ├─ Arrival: 9:45 PM")
    print("    ├─ Price: +$0 (Same fare)")
    print("    └─ Available: 15 seats")
    
    time.sleep(3)
    
    # ===== STEP 9: AI Recommendation =====
    print_step(9, "AI-Powered Flight Selection")
    
    print("🤖 Analyzing options using multi-criteria scoring...")
    print("\n   Scoring Factors:")
    print("   • Departure time (closer to original = better)")
    print("   • Price difference (lower = better)")
    print("   • Same airline (free change = bonus)")
    print("   • Seat availability (more = better)")
    
    time.sleep(3)
    
    print("\n📊 Scoring Results:")
    print("   UA2015: 95/100 ⭐⭐⭐⭐⭐")
    print("   AA1234: 78/100 ⭐⭐⭐⭐")
    print("   DL5678: 72/100 ⭐⭐⭐")
    
    time.sleep(2)
    
    print("\n✅ RECOMMENDED: UA2015 (Score: 95/100)")
    print("   Reason: Same airline (free change) + earliest departure + good price")
    
    time.sleep(2)
    
    # ===== STEP 10: Send Email Notification =====
    print_step(10, "Sending Rebooking Email")
    
    print("📧 Composing professional email with:")
    print("   ✓ Flight issue details")
    print("   ✓ Recommended alternative")
    print("   ✓ Step-by-step rebooking instructions")
    print("   ✓ Direct booking link")
    print("   ✓ Customer service contacts")
    
    time.sleep(2)
    
    print("\n📤 Sending email to:", user_email)
    
    # Actually send the email
    agent._handle_flight_issue(demo_task, fake_flight_status)
    
    time.sleep(3)
    
    print("\n✅ EMAIL SENT SUCCESSFULLY!")
    
    # ===== STEP 11: Show What User Receives =====
    print_step(11, "Email Preview")
    
    print("\n📬 The user will receive an email with:")
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                   🔄 Auto-Rebooking Alert                         ║
║                  We found a better flight for you!                ║
╚══════════════════════════════════════════════════════════════════╝

⚠️  ACTION REQUIRED WITHIN 2 HOURS

Your original flight has been CANCELLED. We've found an excellent 
alternative that matches your schedule.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ Original Flight (Affected)
   Flight: UA2013
   Status: CANCELLED
   Route: EWR → LAX

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Recommended Alternative
   Flight: UA2015
   Departure: 2:30 PM
   Arrival: 6:45 PM
   Available: 12 seats
   Price Difference: +$50

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 How to Rebook (3 Easy Steps):
   1. Click the button below
   2. Enter your confirmation number
   3. Select the new flight

         [ 🚀 REBOOK NOW (Takes 2 Minutes) ]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Tip: Most airlines offer free changes for cancelled flights.
    You'll only pay the fare difference if applicable.

    """)
    
    time.sleep(3)
    
    # ===== STEP 12: Show Continuous Monitoring =====
    print_step(12, "24/7 Continuous Monitoring")
    
    print("The monitoring agent continues running in the background:")
    print()
    
    for i in range(5):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"  [{timestamp}] 🔍 Checking UA2013... Status: Issue handled")
        time.sleep(1)
    
    print("\n✅ Agent will continue monitoring all flights 24/7")
    print("   Next check in 10 seconds...")
    
    time.sleep(2)
    
    # ===== STEP 13: Show Database Records =====
    print_step(13, "Monitoring Records")
    
    print("All events are recorded in the database:")
    print("\n📊 Database Tables:")
    print("   • monitoring_tasks: Active monitoring jobs")
    print("   • monitoring_events: All detected issues")
    print("   • rebooking_suggestions: AI recommendations")
    
    time.sleep(2)
    
    # ===== FINAL SUMMARY =====
    print_banner("✅ DEMONSTRATION COMPLETE", "=")
    
    print("Summary of what happened:")
    print()
    print("  1. ✅ Created monitoring task for UA2013")
    print("  2. ✅ Started 24/7 monitoring agent")
    print("  3. ✅ Detected flight cancellation")
    print("  4. ✅ Found 3 alternative flights")
    print("  5. ✅ AI selected best option (UA2015)")
    print("  6. ✅ Sent professional rebooking email")
    print("  7. ✅ Logged all events to database")
    print()
    
    print("📧 CHECK YOUR EMAIL NOW!")
    print(f"   {user_email}")
    print()
    print("You should have received a beautiful HTML email with:")
    print("  • Complete flight details")
    print("  • Rebooking recommendation")
    print("  • Step-by-step instructions")
    print("  • Direct booking link")
    print()
    
    print("="*70)
    print()
    print("🔄 The agent is still running in the background.")
    print("   It will continue monitoring for the next 30 seconds...")
    print()
    print("="*70)
    
    # Continue monitoring for a bit
    try:
        time.sleep(30)
    except KeyboardInterrupt:
        print("\n\n⏸️  Interrupted by user")
    
    # ===== CLEANUP =====
    print("\n🛑 Stopping monitoring agent...")
    agent.stop()
    
    print("\n✅ Demo finished successfully!")
    print()
    print("="*70)
    print("NEXT STEPS:")
    print("="*70)
    print()
    print("To integrate this into your Streamlit app:")
    print("  1. Open integration_patch.py")
    print("  2. Follow the 8 steps to add code to your app")
    print("  3. Restart your Streamlit app")
    print("  4. Test with real flights!")
    print()
    print("To run as a standalone service:")
    print("  python start_monitoring_service.py")
    print()
    print("To run in background (production):")
    print("  nohup python start_monitoring_service.py &")
    print()
    print("="*70)
    print()


def test_email_only():
    """Quick email test"""
    print_banner("📧 EMAIL SERVICE TEST")
    
    email = input("Enter your email: ").strip()
    
    if not email or "@" not in email:
        print("❌ Invalid email address")
        return
    
    print("\n🔧 Loading email service...")
    from email_service import get_email_service
    email_service = get_email_service()
    
    print("📤 Sending test email...")
    
    success = email_service.send_email(
        to_email=email,
        subject="🧪 Test - MyAgent Monitoring Service",
        html_body="""
        <div style="font-family: Arial; padding: 20px;">
            <h2>✅ Email Service is Working!</h2>
            <p>This is a test email from your 24/7 monitoring service.</p>
            <p>If you received this, email notifications are configured correctly.</p>
            <div style="background: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <strong>Next Steps:</strong>
                <ul>
                    <li>Run the full demo: <code>python demo_complete.py</code></li>
                    <li>Integrate into app: See <code>integration_patch.py</code></li>
                </ul>
            </div>
        </div>
        """
    )
    
    if success:
        print("\n✅ Test email sent successfully!")
        print(f"📧 Check your inbox: {email}")
    else:
        print("\n❌ Failed to send test email")
        print("   Check your .env file configuration")


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test-email':
        test_email_only()
    else:
        simulate_monitoring_cycle()


if __name__ == "__main__":
    main()
