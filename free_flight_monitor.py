"""
Free Flight Monitoring System
Uses multiple FREE APIs for real-time flight tracking:
1. AviationStack (Free tier: 100 requests/month)
2. FlightRadar24 (Scraping - Free)
3. FlightAware (Limited free tier)
4. AeroDataBox (Free tier: 150 requests/day)
"""
import os
import time
import threading
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import logging
import json
from dataclasses import dataclass
import schedule

logger = logging.getLogger(__name__)


@dataclass
class FlightStatus:
    """Flight status information"""
    flight_number: str
    airline: str
    status: str  # scheduled, active, landed, cancelled, incident, diverted
    scheduled_departure: str
    actual_departure: Optional[str]
    scheduled_arrival: str
    actual_arrival: Optional[str]
    departure_airport: str
    arrival_airport: str
    departure_gate: Optional[str]
    arrival_gate: Optional[str]
    delay_minutes: int
    last_updated: str
    aircraft_type: Optional[str] = None
    flight_date: Optional[str] = None


class AviationStackAPI:
    """
    AviationStack - FREE Tier
    100 API calls/month free
    Sign up: https://aviationstack.com/
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('AVIATIONSTACK_API_KEY')
        self.base_url = "http://api.aviationstack.com/v1"
        
    def get_flight_status(self, flight_number: str) -> Optional[FlightStatus]:
        """Get flight status from AviationStack"""
        if not self.api_key:
            logger.warning("AviationStack API key not configured")
            return None
        
        try:
            url = f"{self.base_url}/flights"
            params = {
                'access_key': self.api_key,
                'flight_iata': flight_number,
                'limit': 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('data') and len(data['data']) > 0:
                    flight = data['data'][0]
                    
                    # Calculate delay
                    delay_minutes = 0
                    if flight.get('departure', {}).get('delay'):
                        delay_minutes = flight['departure']['delay']
                    
                    # Determine status
                    status = flight.get('flight_status', 'scheduled')
                    
                    return FlightStatus(
                        flight_number=flight_number,
                        airline=flight.get('airline', {}).get('name', 'Unknown'),
                        status=status,
                        scheduled_departure=flight.get('departure', {}).get('scheduled', ''),
                        actual_departure=flight.get('departure', {}).get('actual'),
                        scheduled_arrival=flight.get('arrival', {}).get('scheduled', ''),
                        actual_arrival=flight.get('arrival', {}).get('actual'),
                        departure_airport=flight.get('departure', {}).get('iata', ''),
                        arrival_airport=flight.get('arrival', {}).get('iata', ''),
                        departure_gate=flight.get('departure', {}).get('gate'),
                        arrival_gate=flight.get('arrival', {}).get('gate'),
                        delay_minutes=delay_minutes,
                        last_updated=datetime.now().isoformat(),
                        aircraft_type=flight.get('aircraft', {}).get('iata'),
                        flight_date=flight.get('flight_date')
                    )
            
            logger.warning(f"AviationStack API returned status {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"AviationStack API error: {e}")
            return None


class AeroDataBoxAPI:
    """
    AeroDataBox - FREE Tier
    150 requests/day free via RapidAPI
    Sign up: https://rapidapi.com/aedbx-aedbx/api/aerodatabox
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('RAPIDAPI_KEY')
        self.base_url = "https://aerodatabox.p.rapidapi.com"
        
    def get_flight_status(self, flight_number: str, date: str = None) -> Optional[FlightStatus]:
        """Get flight status from AeroDataBox"""
        if not self.api_key:
            logger.warning("RapidAPI key not configured")
            return None
        
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            # Extract airline code and flight number
            airline_code = flight_number[:2]
            flight_num = flight_number[2:]
            
            url = f"{self.base_url}/flights/number/{airline_code}{flight_num}/{date}"
            
            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data and len(data) > 0:
                    flight = data[0]
                    
                    departure = flight.get('departure', {})
                    arrival = flight.get('arrival', {})
                    
                    # Calculate delay
                    delay_minutes = 0
                    if departure.get('revisedTime') and departure.get('scheduledTime'):
                        scheduled = datetime.fromisoformat(departure['scheduledTime']['utc'].replace('Z', '+00:00'))
                        actual = datetime.fromisoformat(departure['revisedTime']['utc'].replace('Z', '+00:00'))
                        delay_minutes = int((actual - scheduled).total_seconds() / 60)
                    
                    # Determine status
                    status = 'scheduled'
                    if flight.get('status'):
                        status = flight['status'].lower()
                    
                    return FlightStatus(
                        flight_number=flight_number,
                        airline=flight.get('airline', {}).get('name', 'Unknown'),
                        status=status,
                        scheduled_departure=departure.get('scheduledTime', {}).get('local', ''),
                        actual_departure=departure.get('actualTime', {}).get('local'),
                        scheduled_arrival=arrival.get('scheduledTime', {}).get('local', ''),
                        actual_arrival=arrival.get('actualTime', {}).get('local'),
                        departure_airport=departure.get('airport', {}).get('iata', ''),
                        arrival_airport=arrival.get('airport', {}).get('iata', ''),
                        departure_gate=departure.get('gate'),
                        arrival_gate=arrival.get('gate'),
                        delay_minutes=delay_minutes,
                        last_updated=datetime.now().isoformat(),
                        aircraft_type=flight.get('aircraft', {}).get('model'),
                        flight_date=date
                    )
            
            logger.warning(f"AeroDataBox API returned status {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"AeroDataBox API error: {e}")
            return None


class FlightRadarScraper:
    """
    FlightRadar24 Web Scraping - FREE
    No API key needed, but should be used sparingly
    """
    
    def __init__(self):
        self.base_url = "https://www.flightradar24.com"
        
    def get_flight_status(self, flight_number: str) -> Optional[FlightStatus]:
        """Scrape flight status from FlightRadar24"""
        try:
            # Use FlightRadar24's data API (limited free access)
            url = f"https://data-live.flightradar24.com/zones/fcgi/feed.js"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Search for flight in data
                for key, value in data.items():
                    if isinstance(value, list) and len(value) > 13:
                        if value[13] and flight_number in str(value[13]):
                            # Found flight - parse data
                            # Note: This is simplified - real implementation needs more parsing
                            logger.info(f"Found flight {flight_number} in FlightRadar24 data")
                            
                            return FlightStatus(
                                flight_number=flight_number,
                                airline=value[18] if len(value) > 18 else 'Unknown',
                                status='active',
                                scheduled_departure='',
                                actual_departure=None,
                                scheduled_arrival='',
                                actual_arrival=None,
                                departure_airport=value[11] if len(value) > 11 else '',
                                arrival_airport=value[12] if len(value) > 12 else '',
                                departure_gate=None,
                                arrival_gate=None,
                                delay_minutes=0,
                                last_updated=datetime.now().isoformat(),
                                aircraft_type=value[8] if len(value) > 8 else None
                            )
            
            return None
            
        except Exception as e:
            logger.error(f"FlightRadar24 scraping error: {e}")
            return None


class FlightMonitor:
    """
    Multi-source flight monitor with free API fallback chain
    
    Priority order:
    1. AeroDataBox (150/day)
    2. AviationStack (100/month)
    3. FlightRadar24 Scraping (unlimited but rate-limited)
    """
    
    def __init__(self):
        """Initialize with all free APIs"""
        self.aerodatabox = AeroDataBoxAPI()
        self.aviationstack = AviationStackAPI()
        self.flightradar = FlightRadarScraper()
        
        self.monitored_flights = {}  # flight_number -> callback
        self.last_status = {}  # flight_number -> FlightStatus
        
        # Track API usage to avoid hitting limits
        self.api_calls_today = {
            'aerodatabox': 0,
            'aviationstack': 0,
            'flightradar': 0
        }
        self.last_reset = datetime.now().date()
    
    def _reset_daily_counters(self):
        """Reset API call counters if new day"""
        today = datetime.now().date()
        if today > self.last_reset:
            self.api_calls_today = {k: 0 for k in self.api_calls_today}
            self.last_reset = today
            logger.info("Reset daily API call counters")
    
    def get_flight_status(self, flight_number: str, 
                         date: Optional[str] = None) -> Optional[FlightStatus]:
        """
        Get flight status with multi-source fallback
        
        Uses free tier limits intelligently:
        - AeroDataBox: 150/day
        - AviationStack: 100/month (≈3/day average)
        - FlightRadar24: Unlimited scraping (but slow)
        """
        self._reset_daily_counters()
        
        # Try AeroDataBox first (best free tier)
        if self.api_calls_today['aerodatabox'] < 140:  # Leave buffer
            logger.info(f"Trying AeroDataBox for {flight_number}")
            status = self.aerodatabox.get_flight_status(flight_number, date)
            if status:
                self.api_calls_today['aerodatabox'] += 1
                logger.info(f"✓ AeroDataBox success ({self.api_calls_today['aerodatabox']}/150)")
                return status
        
        # Try AviationStack (limited)
        if self.api_calls_today['aviationstack'] < 3:  # Conservative daily limit
            logger.info(f"Trying AviationStack for {flight_number}")
            status = self.aviationstack.get_flight_status(flight_number)
            if status:
                self.api_calls_today['aviationstack'] += 1
                logger.info(f"✓ AviationStack success ({self.api_calls_today['aviationstack']}/3)")
                return status
        
        # Fallback to FlightRadar24 scraping
        logger.info(f"Trying FlightRadar24 for {flight_number}")
        status = self.flightradar.get_flight_status(flight_number)
        if status:
            self.api_calls_today['flightradar'] += 1
            logger.info(f"✓ FlightRadar24 success")
            return status
        
        logger.warning(f"All APIs failed for {flight_number}")
        return None
    
    def add_flight(self, flight_number: str, callback: Callable[[FlightStatus], None],
                   flight_date: Optional[str] = None):
        """
        Add flight to monitoring list
        
        Args:
            flight_number: Flight number (e.g., "UA123")
            callback: Function to call when status changes
            flight_date: Flight date (YYYY-MM-DD)
        """
        self.monitored_flights[flight_number] = {
            'callback': callback,
            'date': flight_date or datetime.now().strftime("%Y-%m-%d")
        }
        logger.info(f"Added flight {flight_number} to monitoring")
    
    def remove_flight(self, flight_number: str):
        """Remove flight from monitoring"""
        if flight_number in self.monitored_flights:
            del self.monitored_flights[flight_number]
            if flight_number in self.last_status:
                del self.last_status[flight_number]
            logger.info(f"Removed flight {flight_number} from monitoring")
    
    def check_status_changes(self):
        """Check all monitored flights for status changes"""
        for flight_number, data in self.monitored_flights.items():
            try:
                callback = data['callback']
                flight_date = data['date']
                
                current_status = self.get_flight_status(flight_number, flight_date)
                
                if current_status:
                    last = self.last_status.get(flight_number)
                    
                    # Check if status changed
                    if last is None or self._has_status_changed(last, current_status):
                        logger.info(f"Status changed for {flight_number}: {current_status.status}")
                        callback(current_status)
                        self.last_status[flight_number] = current_status
                
                # Rate limiting - wait between flights
                time.sleep(2)
                        
            except Exception as e:
                logger.error(f"Error checking flight {flight_number}: {e}")
    
    def _has_status_changed(self, old: FlightStatus, new: FlightStatus) -> bool:
        """Check if flight status has meaningfully changed"""
        return (
            old.status != new.status or
            old.delay_minutes != new.delay_minutes or
            old.departure_gate != new.departure_gate or
            old.arrival_gate != new.arrival_gate or
            abs(old.delay_minutes - new.delay_minutes) >= 15  # 15+ min change
        )
    
    def get_api_usage_stats(self) -> Dict:
        """Get current API usage statistics"""
        return {
            'date': self.last_reset.isoformat(),
            'aerodatabox': {
                'used': self.api_calls_today['aerodatabox'],
                'limit': 150,
                'remaining': 150 - self.api_calls_today['aerodatabox']
            },
            'aviationstack': {
                'used': self.api_calls_today['aviationstack'],
                'daily_limit': 3,
                'monthly_limit': 100,
                'remaining': 3 - self.api_calls_today['aviationstack']
            },
            'flightradar': {
                'used': self.api_calls_today['flightradar'],
                'limit': 'unlimited (rate-limited)'
            }
        }


class WeatherMonitor:
    """
    FREE Weather API - OpenWeatherMap
    Free tier: 1000 calls/day
    Sign up: https://openweathermap.org/api
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENWEATHER_API_KEY')
        self.base_url = "http://api.openweathermap.org/data/2.5"
    
    def get_weather_forecast(self, location: str, days: int = 7) -> List[Dict]:
        """Get weather forecast for location"""
        if not self.api_key:
            logger.warning("OpenWeatherMap API key not configured")
            return []
        
        try:
            # Get city coordinates first
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct"
            geo_params = {
                'q': location,
                'limit': 1,
                'appid': self.api_key
            }
            
            geo_response = requests.get(geo_url, params=geo_params, timeout=10)
            
            if geo_response.status_code == 200:
                geo_data = geo_response.json()
                if geo_data and len(geo_data) > 0:
                    lat = geo_data[0]['lat']
                    lon = geo_data[0]['lon']
                    
                    # Get forecast
                    forecast_url = f"{self.base_url}/forecast"
                    forecast_params = {
                        'lat': lat,
                        'lon': lon,
                        'appid': self.api_key,
                        'units': 'metric'
                    }
                    
                    forecast_response = requests.get(forecast_url, params=forecast_params, timeout=10)
                    
                    if forecast_response.status_code == 200:
                        forecast_data = forecast_response.json()
                        
                        # Parse forecast
                        forecasts = []
                        for item in forecast_data.get('list', [])[:days*8]:  # 3-hour intervals
                            forecasts.append({
                                'date': item['dt_txt'],
                                'temp': item['main']['temp'],
                                'conditions': item['weather'][0]['description'],
                                'precipitation': item.get('rain', {}).get('3h', 0),
                                'alerts': []
                            })
                        
                        return forecasts
            
            return []
            
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return []
    
    def check_severe_weather(self, location: str) -> List[Dict]:
        """Check for severe weather alerts"""
        # OpenWeatherMap free tier doesn't include alerts
        # Would need to upgrade or use another service
        return []


# Keep the TripMonitoringAgent class from original implementation
# Import it or copy here...

if __name__ == "__main__":
    # Test the free APIs
    print("=" * 50)
    print("Testing FREE Flight Monitoring APIs")
    print("=" * 50)
    
    monitor = FlightMonitor()
    
    # Test flight (use a real recent flight number)
    test_flight = "UA2013"  # Example United flight
    
    print(f"\nChecking flight: {test_flight}")
    print("-" * 50)
    
    status = monitor.get_flight_status(test_flight)
    
    if status:
        print(f"✓ Flight found!")
        print(f"  Airline: {status.airline}")
        print(f"  Status: {status.status}")
        print(f"  Route: {status.departure_airport} → {status.arrival_airport}")
        print(f"  Scheduled Departure: {status.scheduled_departure}")
        print(f"  Delay: {status.delay_minutes} minutes")
    else:
        print(f"✗ Flight not found or all APIs failed")
    
    print("\n" + "=" * 50)
    print("API Usage Statistics")
    print("=" * 50)
    stats = monitor.get_api_usage_stats()
    for api, data in stats.items():
        if api != 'date':
            print(f"\n{api.upper()}:")
            if isinstance(data, dict):
                for key, value in data.items():
                    print(f"  {key}: {value}")
