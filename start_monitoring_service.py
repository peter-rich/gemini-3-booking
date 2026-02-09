#!/usr/bin/env python3
"""
Start 24/7 Smart Monitoring Agent as Background Service
启动24/7智能监控代理后台服务

Usage:
    python start_monitoring_service.py              # Start in foreground
    nohup python start_monitoring_service.py &      # Start in background
    python start_monitoring_service.py --demo       # Run demo mode
"""

import sys
import argparse
import signal
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitoring_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def signal_handler(sig, frame):
    """Handle shutdown signals"""
    print("\n\n🛑 Received shutdown signal...")
    print("   Stopping monitoring agent gracefully...")
    if 'agent' in globals():
        agent.stop()
    print("✅ Service stopped successfully")
    sys.exit(0)


def start_service():
    """Start the monitoring service"""
    print("\n" + "="*70)
    print("🚀 MYAGENT BOOKING - 24/7 SMART MONITORING SERVICE")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Status: Initializing...")
    print("="*70 + "\n")
    
    # Initialize services
    logger.info("Loading services...")
    from email_service import get_email_service
    from rebooking_service import FlightRebookingAgent
    from smart_monitoring_agent import SmartMonitoringAgent
    
    email_service = get_email_service()
    rebooking_service = FlightRebookingAgent(email_service)
    
    # Create monitoring agent
    global agent
    agent = SmartMonitoringAgent(
        db_path="/tmp/monitoring.db",
        email_service=email_service,
        rebooking_service=rebooking_service
    )
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start monitoring
    agent.start()
    
    print("\n✅ Service is now running 24/7")
    print("📡 Monitoring active flights for delays, cancellations, and rebooking opportunities")
    print("📧 Email alerts will be sent automatically when issues are detected")
    print("🔄 Auto-rebooking suggestions will be generated when needed")
    print("\nPress Ctrl+C to stop the service\n")
    print("="*70 + "\n")
    
    # Keep the main thread alive
    try:
        while True:
            import time
            time.sleep(60)
            
            # Print status every hour
            status = agent.get_status()
            if datetime.now().minute == 0:  # Every hour
                logger.info(f"Status: Running={status['running']}, Tasks={status['active_tasks']}")
    
    except KeyboardInterrupt:
        signal_handler(None, None)


def run_demo():
    """Run demo mode"""
    from smart_monitoring_agent import run_demo
    run_demo()


def main():
    parser = argparse.ArgumentParser(
        description='24/7 Smart Monitoring Service for MyAgent Booking'
    )
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run in demo mode (simulates a flight cancellation and rebooking)'
    )
    parser.add_argument(
        '--test-email',
        type=str,
        help='Test email notifications (provide your email)'
    )
    
    args = parser.parse_args()
    
    if args.demo:
        run_demo()
    elif args.test_email:
        # Test email functionality
        print(f"\n📧 Testing email to: {args.test_email}")
        from email_service import get_email_service
        email_service = get_email_service()
        
        success = email_service.send_email(
            to_email=args.test_email,
            subject="🧪 Test Email - MyAgent Monitoring Service",
            html_body="""
            <h2>✅ Email Service is Working!</h2>
            <p>This is a test email from your 24/7 monitoring service.</p>
            <p>If you received this, email notifications are configured correctly.</p>
            """
        )
        
        if success:
            print("✅ Test email sent successfully!")
        else:
            print("❌ Failed to send test email. Check your email service configuration.")
    else:
        start_service()


if __name__ == "__main__":
    main()
