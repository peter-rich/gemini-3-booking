"""
Budget tracking and attraction scoring system
"""
import requests
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BudgetBreakdown:
    """Budget breakdown by category"""
    flights: float = 0.0
    hotels: float = 0.0
    transportation: float = 0.0
    food: float = 0.0
    activities: float = 0.0
    miscellaneous: float = 0.0
    
    @property
    def total(self) -> float:
        return (self.flights + self.hotels + self.transportation + 
                self.food + self.activities + self.miscellaneous)
    
    def to_dict(self) -> Dict:
        return {
            'flights': self.flights,
            'hotels': self.hotels,
            'transportation': self.transportation,
            'food': self.food,
            'activities': self.activities,
            'miscellaneous': self.miscellaneous,
            'total': self.total
        }


class BudgetTracker:
    """Track and manage trip budgets"""
    
    def __init__(self, total_budget: float):
        self.total_budget = total_budget
        self.breakdown = BudgetBreakdown()
        self.warnings_sent = []
    
    def add_expense(self, category: str, amount: float):
        """Add expense to budget tracking"""
        if hasattr(self.breakdown, category):
            current = getattr(self.breakdown, category)
            setattr(self.breakdown, category, current + amount)
        else:
            self.breakdown.miscellaneous += amount
    
    def get_budget_status(self) -> Dict:
        """Get current budget status"""
        used = self.breakdown.total
        remaining = self.total_budget - used
        percentage = (used / self.total_budget * 100) if self.total_budget > 0 else 0
        
        # Determine alert level
        alert_level = "safe"
        if percentage >= 100:
            alert_level = "critical"
        elif percentage >= 90:
            alert_level = "warning"
        elif percentage >= 75:
            alert_level = "caution"
        
        return {
            'total_budget': self.total_budget,
            'used': used,
            'remaining': remaining,
            'percentage': percentage,
            'alert_level': alert_level,
            'breakdown': self.breakdown.to_dict()
        }
    
    def should_send_alert(self, threshold: float = 75.0) -> bool:
        """Check if budget alert should be sent"""
        status = self.get_budget_status()
        percentage = status['percentage']
        
        # Send alerts at 75%, 90%, and 100%
        alert_thresholds = [75, 90, 100]
        for threshold in alert_thresholds:
            if percentage >= threshold and threshold not in self.warnings_sent:
                self.warnings_sent.append(threshold)
                return True
        return False
    
    def parse_price_from_action(self, action: Dict) -> Tuple[str, float]:
        """Extract category and price from action item"""
        action_type = action.get('type', 'miscellaneous')
        price_str = action.get('price', '$0')
        
        # Parse price string (e.g., "$1,234.56" -> 1234.56)
        try:
            price = float(price_str.replace('$', '').replace(',', '').replace('USD', '').strip())
        except (ValueError, AttributeError):
            price = 0.0
        
        # Map action type to category
        category_map = {
            'flight': 'flights',
            'hotel': 'hotels',
            'taxi': 'transportation',
            'restaurant': 'food',
            'activity': 'activities'
        }
        
        category = category_map.get(action_type, 'miscellaneous')
        return category, price


class AttractionScorer:
    """Score and recommend attractions using FREE data sources"""
    
    def __init__(self):
        # Use free data sources instead of paid APIs
        from free_attractions import FreeAttractionScorer, SimpleAttractionRecommender
        self.free_scorer = FreeAttractionScorer()
        self.simple_recommender = SimpleAttractionRecommender()
    
    def get_attraction_score(self, location: str, attraction_name: str) -> Optional[Dict]:
        """
        Get attraction score and details using free sources
        
        Returns:
            Dict with rating, reviews, popularity, and recommendations
        """
        # Try to find in our database or fetch from free APIs
        attractions = self.free_scorer.get_popular_attractions(location)
        
        for attr in attractions:
            if attraction_name.lower() in attr['name'].lower():
                return {
                    'rating': attr.get('rating', 4.5),
                    'total_reviews': 'N/A',  # Not available from free sources
                    'popularity_rank': attractions.index(attr) + 1,
                    'category': attr.get('category', 'Attraction'),
                    'avg_visit_duration': 90,  # Estimated
                    'best_time': 'Morning',
                    'price_level': attr.get('price', '$$'),
                    'highlights': [attr.get('description', '')[:100]],
                    'tips': ['Check opening hours', 'Book tickets in advance'],
                    'source': attr.get('source', 'free_data')
                }
        
        # Return default if not found
        return None
    
    def recommend_attractions(self, destination: str, interests: List[str], 
                             budget: str = 'medium') -> List[Dict]:
        """
        Recommend top attractions using FREE sources
        
        Args:
            destination: City or region
            interests: List of interest categories (culture, food, nature, etc.)
            budget: low, medium, or high
            
        Returns:
            List of recommended attractions with scores
        """
        # Use simple recommender for known cities
        attractions = self.simple_recommender.get_recommendations(
            destination, interests, budget
        )
        
        # If not found, try free APIs
        if not attractions:
            attractions = self.free_scorer.get_popular_attractions(
                destination, interests
            )
        
        return attractions
    
    def get_google_places_details(self, place_name: str, location: str) -> Optional[Dict]:
        """
        Get place details - uses free sources instead of Google Places API
        """
        # Use free Wikipedia/OSM data instead
        return None
    
    def integrate_with_itinerary(self, itinerary: Dict, 
                                 add_scores: bool = True) -> Dict:
        """
        Enhance itinerary with attraction scores and recommendations
        Uses FREE data sources only
        
        Args:
            itinerary: Parsed trip itinerary JSON
            add_scores: Whether to add attraction scores
            
        Returns:
            Enhanced itinerary with scores and recommendations
        """
        if not add_scores:
            return itinerary
        
        destination = itinerary.get('meta', {}).get('destination_city', '')
        
        # Add scores to existing activities
        for action in itinerary.get('actions', []):
            if action.get('type') == 'activity':
                activity_name = action.get('title', '')
                score_data = self.get_attraction_score(destination, activity_name)
                if score_data:
                    action['attraction_score'] = score_data
        
        return itinerary


class ConferenceDetector:
    """Detect and handle conference/meeting trips"""
    
    @staticmethod
    def is_conference_trip(query: str, actions: List[Dict]) -> bool:
        """Detect if trip is for a conference or meeting"""
        conference_keywords = [
            'conference', 'summit', 'meeting', 'convention', 
            'symposium', 'expo', 'business trip', 'workshop',
            'seminar', 'event'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in conference_keywords)
    
    @staticmethod
    def extract_conference_details(query: str) -> Dict:
        """Extract conference details from query"""
        import re
        
        details = {
            'is_conference': False,
            'conference_name': None,
            'venue': None,
            'dates': []
        }
        
        # Look for conference name patterns
        # e.g., "attending AWS re:Invent" or "going to Google I/O"
        conference_pattern = r'(?:attending|going to|at)\s+([A-Z][A-Za-z0-9\s:\/]+?)(?:\s+in|\s+at|$)'
        match = re.search(conference_pattern, query)
        if match:
            details['conference_name'] = match.group(1).strip()
            details['is_conference'] = True
        
        return details
    
    @staticmethod
    def create_conference_schedule(conference_details: Dict, 
                                   trip_dates: Tuple[str, str]) -> List[Dict]:
        """
        Create conference schedule blocks
        
        Returns:
            List of calendar events for conference activities
        """
        schedule = []
        
        # Typical conference schedule
        schedule_template = [
            {
                'title': 'Conference Registration',
                'time': '08:00',
                'duration': 60,
                'day': 0
            },
            {
                'title': 'Opening Keynote',
                'time': '09:00',
                'duration': 90,
                'day': 0
            },
            {
                'title': 'Morning Sessions',
                'time': '10:30',
                'duration': 180,
                'day': 0
            },
            {
                'title': 'Lunch & Networking',
                'time': '12:30',
                'duration': 90,
                'day': 0
            },
            {
                'title': 'Afternoon Sessions',
                'time': '14:00',
                'duration': 180,
                'day': 0
            },
            {
                'title': 'Evening Networking Event',
                'time': '18:00',
                'duration': 120,
                'day': 0
            }
        ]
        
        # Add conference name to events
        conf_name = conference_details.get('conference_name', 'Conference')
        for event in schedule_template:
            event['title'] = f"{conf_name} - {event['title']}"
            schedule.append(event)
        
        return schedule


# Utility functions
def calculate_daily_budget(total_budget: float, num_days: int, 
                          fixed_costs: float = 0) -> float:
    """Calculate recommended daily spending budget"""
    remaining = total_budget - fixed_costs
    return remaining / num_days if num_days > 0 else 0


def suggest_budget_adjustments(budget_status: Dict) -> List[str]:
    """Suggest ways to stay within budget"""
    suggestions = []
    
    percentage = budget_status['percentage']
    breakdown = budget_status['breakdown']
    
    if percentage > 80:
        # Find highest expense category
        categories = {k: v for k, v in breakdown.items() if k != 'total' and v > 0}
        if categories:
            highest_cat = max(categories, key=categories.get)
            
            suggestions_map = {
                'hotels': [
                    "Consider switching to a budget hotel or hostel",
                    "Look for hotels further from city center",
                    "Check for last-minute deals"
                ],
                'flights': [
                    "Search for flights with connections instead of direct",
                    "Try alternative airports nearby",
                    "Be flexible with travel dates"
                ],
                'food': [
                    "Try local street food and markets",
                    "Cook some meals if hotel has kitchen",
                    "Look for lunch specials instead of dinner"
                ],
                'activities': [
                    "Focus on free attractions and walking tours",
                    "Look for city passes with discounts",
                    "Visit museums on free admission days"
                ]
            }
            
            suggestions = suggestions_map.get(highest_cat, [
                "Review all expenses and cut non-essentials",
                "Look for package deals and discounts"
            ])
    
    return suggestions
