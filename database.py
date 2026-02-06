"""
Database models and user management system
"""
import sqlite3
import hashlib
import secrets
import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class User:
    """User data model"""
    id: int
    email: str
    password_hash: str
    full_name: str
    home_location: str
    preferred_airports: str  # JSON array
    created_at: str
    last_login: Optional[str] = None


@dataclass
class TripHistory:
    """Trip history data model"""
    id: int
    user_id: int
    trip_name: str
    destination: str
    depart_date: str
    return_date: str
    budget: float
    actual_cost: float
    status: str  # planned, ongoing, completed, cancelled
    itinerary_json: str  # Full JSON payload
    created_at: str
    updated_at: str


@dataclass
class MonitoringAlert:
    """Real-time monitoring alert"""
    id: int
    trip_id: int
    alert_type: str  # flight_delay, price_change, weather, event
    severity: str  # low, medium, high, critical
    message: str
    action_required: bool
    created_at: str
    resolved: bool


class Database:
    """Database handler for user and trip management"""
    
    def __init__(self, db_path: str = "travel_agent.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            home_location TEXT DEFAULT 'Piscataway, NJ',
            preferred_airports TEXT DEFAULT '["EWR", "JFK"]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
        """)
        
        # Trip history table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS trip_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            trip_name TEXT NOT NULL,
            destination TEXT NOT NULL,
            depart_date TEXT NOT NULL,
            return_date TEXT NOT NULL,
            budget REAL DEFAULT 0,
            actual_cost REAL DEFAULT 0,
            status TEXT DEFAULT 'planned',
            itinerary_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        
        # Monitoring alerts table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitoring_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id INTEGER NOT NULL,
            alert_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL,
            action_required BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (trip_id) REFERENCES trip_history (id)
        )
        """)
        
        # User preferences table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id INTEGER PRIMARY KEY,
            budget_alerts BOOLEAN DEFAULT TRUE,
            price_monitoring BOOLEAN DEFAULT TRUE,
            weather_alerts BOOLEAN DEFAULT TRUE,
            notification_email TEXT,
            preferred_currency TEXT DEFAULT 'USD',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, email: str, password: str, full_name: str, 
                    home_location: str = "Piscataway, NJ") -> Optional[int]:
        """Create new user account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            password_hash = self.hash_password(password)
            cursor.execute("""
            INSERT INTO users (email, password_hash, full_name, home_location)
            VALUES (?, ?, ?, ?)
            """, (email, password_hash, full_name, home_location))
            
            user_id = cursor.lastrowid
            
            # Create default preferences
            cursor.execute("""
            INSERT INTO user_preferences (user_id, notification_email)
            VALUES (?, ?)
            """, (user_id, email))
            
            conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user login"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        cursor.execute("""
        SELECT * FROM users WHERE email = ? AND password_hash = ?
        """, (email, password_hash))
        
        row = cursor.fetchone()
        if row:
            # Update last login
            cursor.execute("""
            UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            """, (row['id'],))
            conn.commit()
            
            user = User(
                id=row['id'],
                email=row['email'],
                password_hash=row['password_hash'],
                full_name=row['full_name'],
                home_location=row['home_location'],
                preferred_airports=row['preferred_airports'],
                created_at=row['created_at'],
                last_login=row['last_login']
            )
            conn.close()
            return user
        
        conn.close()
        return None
    
    def save_trip(self, user_id: int, trip_name: str, destination: str,
                  depart_date: str, return_date: str, budget: float,
                  itinerary_json: str) -> int:
        """Save trip to history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO trip_history 
        (user_id, trip_name, destination, depart_date, return_date, budget, itinerary_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, trip_name, destination, depart_date, return_date, budget, itinerary_json))
        
        trip_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return trip_id
    
    def get_user_trips(self, user_id: int, status: Optional[str] = None) -> List[Dict]:
        """Get all trips for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
            SELECT * FROM trip_history 
            WHERE user_id = ? AND status = ?
            ORDER BY created_at DESC
            """, (user_id, status))
        else:
            cursor.execute("""
            SELECT * FROM trip_history 
            WHERE user_id = ?
            ORDER BY created_at DESC
            """, (user_id,))
        
        trips = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return trips
    
    def update_trip_cost(self, trip_id: int, actual_cost: float):
        """Update actual trip cost"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE trip_history 
        SET actual_cost = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (actual_cost, trip_id))
        
        conn.commit()
        conn.close()
    
    def create_alert(self, trip_id: int, alert_type: str, severity: str,
                     message: str, action_required: bool = False) -> int:
        """Create monitoring alert"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO monitoring_alerts 
        (trip_id, alert_type, severity, message, action_required)
        VALUES (?, ?, ?, ?, ?)
        """, (trip_id, alert_type, severity, message, action_required))
        
        alert_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return alert_id
    
    def get_unresolved_alerts(self, trip_id: int) -> List[Dict]:
        """Get unresolved alerts for a trip"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT * FROM monitoring_alerts 
        WHERE trip_id = ? AND resolved = FALSE
        ORDER BY created_at DESC
        """, (trip_id,))
        
        alerts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return alerts
    
    def resolve_alert(self, alert_id: int):
        """Mark alert as resolved"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE monitoring_alerts 
        SET resolved = TRUE
        WHERE id = ?
        """, (alert_id,))
        
        conn.commit()
        conn.close()


# Singleton instance
_db_instance = None

def get_database() -> Database:
    """Get singleton database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
