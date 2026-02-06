"""
Free Attraction Recommendation System
Uses free public data sources instead of paid APIs
"""
import requests
import json
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class FreeAttractionScorer:
    """
    Free attraction scoring using public data sources
    No API keys needed!
    
    Data sources:
    1. Wikipedia API (free, no key needed)
    2. OpenStreetMap Nominatim (free, no key needed)
    3. Wikidata (free, no key needed)
    """
    
    def __init__(self):
        self.cache = {}
    
    def get_attractions_from_wikipedia(self, location: str) -> List[Dict]:
        """
        Get popular attractions from Wikipedia
        100% free, no API key needed
        """
        try:
            # Search Wikipedia for location
            search_url = "https://en.wikipedia.org/w/api.php"
            search_params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': f'tourist attractions in {location}',
                'srlimit': 10
            }
            
            response = requests.get(search_url, params=search_params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                attractions = []
                
                for result in data.get('query', {}).get('search', []):
                    title = result['title']
                    snippet = result['snippet']
                    
                    # Get page details
                    page_url = "https://en.wikipedia.org/w/api.php"
                    page_params = {
                        'action': 'query',
                        'format': 'json',
                        'titles': title,
                        'prop': 'extracts|pageimages',
                        'exintro': True,
                        'explaintext': True,
                        'pithumbsize': 300
                    }
                    
                    page_response = requests.get(page_url, params=page_params, timeout=10)
                    
                    if page_response.status_code == 200:
                        page_data = page_response.json()
                        pages = page_data.get('query', {}).get('pages', {})
                        
                        for page_id, page_info in pages.items():
                            attractions.append({
                                'name': page_info.get('title', title),
                                'description': page_info.get('extract', snippet)[:200] + '...',
                                'category': self._categorize_attraction(title, snippet),
                                'source': 'wikipedia',
                                'url': f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                            })
                
                return attractions[:10]
            
            return []
            
        except Exception as e:
            logger.error(f"Wikipedia API error: {e}")
            return []
    
    def get_attractions_from_osm(self, location: str) -> List[Dict]:
        """
        Get attractions from OpenStreetMap Nominatim
        100% free, no API key needed
        """
        try:
            # Geocode location first
            geocode_url = "https://nominatim.openstreetmap.org/search"
            geocode_params = {
                'q': location,
                'format': 'json',
                'limit': 1
            }
            
            headers = {
                'User-Agent': 'MyAgentBooking/1.0'  # Required by OSM
            }
            
            response = requests.get(geocode_url, params=geocode_params, 
                                   headers=headers, timeout=10)
            
            if response.status_code == 200:
                geo_data = response.json()
                
                if geo_data and len(geo_data) > 0:
                    lat = geo_data[0]['lat']
                    lon = geo_data[0]['lon']
                    
                    # Search for nearby attractions
                    # Using Overpass API (free OSM query service)
                    overpass_url = "https://overpass-api.de/api/interpreter"
                    
                    # Query for tourism attractions within 5km
                    overpass_query = f"""
                    [out:json];
                    (
                      node["tourism"](around:5000,{lat},{lon});
                      way["tourism"](around:5000,{lat},{lon});
                      relation["tourism"](around:5000,{lat},{lon});
                    );
                    out body;
                    """
                    
                    overpass_response = requests.post(
                        overpass_url, 
                        data={'data': overpass_query},
                        timeout=30
                    )
                    
                    if overpass_response.status_code == 200:
                        osm_data = overpass_response.json()
                        attractions = []
                        
                        for element in osm_data.get('elements', [])[:20]:
                            tags = element.get('tags', {})
                            name = tags.get('name')
                            
                            if name:
                                attractions.append({
                                    'name': name,
                                    'category': tags.get('tourism', 'attraction'),
                                    'description': tags.get('description', ''),
                                    'address': tags.get('addr:full', ''),
                                    'source': 'openstreetmap',
                                    'lat': element.get('lat'),
                                    'lon': element.get('lon')
                                })
                        
                        return attractions
            
            return []
            
        except Exception as e:
            logger.error(f"OpenStreetMap API error: {e}")
            return []
    
    def get_popular_attractions(self, destination: str, 
                               interests: List[str] = None) -> List[Dict]:
        """
        Get popular attractions using multiple free sources
        
        Args:
            destination: City or location
            interests: List of interest categories (optional)
            
        Returns:
            List of attractions with scores
        """
        # Check cache first
        cache_key = f"{destination}:{','.join(interests or [])}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        all_attractions = []
        
        # Get from Wikipedia (better for major attractions)
        wiki_attractions = self.get_attractions_from_wikipedia(destination)
        all_attractions.extend(wiki_attractions)
        
        # Get from OpenStreetMap (better for local spots)
        osm_attractions = self.get_attractions_from_osm(destination)
        all_attractions.extend(osm_attractions)
        
        # Remove duplicates by name
        seen_names = set()
        unique_attractions = []
        
        for attr in all_attractions:
            name_lower = attr['name'].lower()
            if name_lower not in seen_names:
                seen_names.add(name_lower)
                
                # Add mock scoring (in real app, could use view counts, etc.)
                attr['score'] = self._calculate_score(attr, interests)
                attr['rating'] = 4.5  # Mock rating
                attr['price_level'] = self._estimate_price_level(attr)
                
                unique_attractions.append(attr)
        
        # Sort by score
        unique_attractions.sort(key=lambda x: x['score'], reverse=True)
        
        # Cache results
        result = unique_attractions[:10]
        self.cache[cache_key] = result
        
        return result
    
    def _categorize_attraction(self, title: str, description: str) -> str:
        """Categorize attraction based on title and description"""
        text = (title + " " + description).lower()
        
        if any(word in text for word in ['museum', 'gallery', 'art']):
            return 'museum'
        elif any(word in text for word in ['temple', 'church', 'shrine', 'cathedral']):
            return 'religious'
        elif any(word in text for word in ['park', 'garden', 'nature']):
            return 'nature'
        elif any(word in text for word in ['market', 'shopping', 'mall']):
            return 'shopping'
        elif any(word in text for word in ['restaurant', 'food', 'cafe']):
            return 'food'
        elif any(word in text for word in ['tower', 'building', 'observation']):
            return 'landmark'
        else:
            return 'attraction'
    
    def _calculate_score(self, attraction: Dict, interests: List[str] = None) -> float:
        """Calculate attraction score (0-100)"""
        score = 50.0  # Base score
        
        # Boost score if matches interests
        if interests:
            category = attraction.get('category', '').lower()
            for interest in interests:
                if interest.lower() in category:
                    score += 20
        
        # Boost if from Wikipedia (usually more notable)
        if attraction.get('source') == 'wikipedia':
            score += 15
        
        # Boost if has description
        if attraction.get('description'):
            score += 10
        
        return min(100, score)
    
    def _estimate_price_level(self, attraction: Dict) -> str:
        """Estimate price level based on attraction type"""
        category = attraction.get('category', '').lower()
        
        free_categories = ['park', 'garden', 'temple', 'shrine', 'nature']
        budget_categories = ['market', 'museum']
        
        if any(cat in category for cat in free_categories):
            return '$'  # Free or cheap
        elif any(cat in category for cat in budget_categories):
            return '$$'  # Moderate
        else:
            return '$$$'  # Could be expensive


class SimpleAttractionRecommender:
    """
    Simple attraction recommender with pre-loaded data
    No API calls needed - works offline!
    """
    
    def __init__(self):
        # Pre-loaded popular attractions for major cities
        self.attractions_db = {
            'tokyo': [
                {'name': 'Senso-ji Temple', 'category': 'Historical', 'rating': 4.5, 
                 'price': '$', 'score': 95, 'description': 'Ancient Buddhist temple in Asakusa'},
                {'name': 'Tokyo Skytree', 'category': 'Landmark', 'rating': 4.3,
                 'price': '$$$', 'score': 90, 'description': 'Tallest structure in Japan'},
                {'name': 'Tsukiji Outer Market', 'category': 'Food', 'rating': 4.6,
                 'price': '$$', 'score': 92, 'description': 'Fresh seafood and street food'},
                {'name': 'Meiji Shrine', 'category': 'Religious', 'rating': 4.5,
                 'price': '$', 'score': 88, 'description': 'Peaceful Shinto shrine in forest'},
                {'name': 'Shibuya Crossing', 'category': 'Landmark', 'rating': 4.4,
                 'price': '$', 'score': 85, 'description': 'World\'s busiest pedestrian crossing'},
            ],
            'new york': [
                {'name': 'Central Park', 'category': 'Nature', 'rating': 4.7,
                 'price': '$', 'score': 98, 'description': 'Iconic urban park'},
                {'name': 'Statue of Liberty', 'category': 'Landmark', 'rating': 4.6,
                 'price': '$$', 'score': 95, 'description': 'Symbol of freedom'},
                {'name': 'Times Square', 'category': 'Landmark', 'rating': 4.5,
                 'price': '$', 'score': 90, 'description': 'Bright lights and energy'},
                {'name': 'Metropolitan Museum', 'category': 'Museum', 'rating': 4.8,
                 'price': '$$', 'score': 93, 'description': 'World-class art museum'},
                {'name': 'Brooklyn Bridge', 'category': 'Landmark', 'rating': 4.7,
                 'price': '$', 'score': 92, 'description': 'Historic suspension bridge'},
            ],
            'paris': [
                {'name': 'Eiffel Tower', 'category': 'Landmark', 'rating': 4.6,
                 'price': '$$$', 'score': 98, 'description': 'Iconic iron tower'},
                {'name': 'Louvre Museum', 'category': 'Museum', 'rating': 4.7,
                 'price': '$$', 'score': 96, 'description': 'World\'s largest art museum'},
                {'name': 'Notre-Dame', 'category': 'Religious', 'rating': 4.7,
                 'price': '$', 'score': 94, 'description': 'Gothic cathedral'},
                {'name': 'Arc de Triomphe', 'category': 'Landmark', 'rating': 4.6,
                 'price': '$$', 'score': 90, 'description': 'Triumphal arch monument'},
                {'name': 'Sacré-Cœur', 'category': 'Religious', 'rating': 4.6,
                 'price': '$', 'score': 88, 'description': 'Basilica with city views'},
            ],
            'london': [
                {'name': 'British Museum', 'category': 'Museum', 'rating': 4.7,
                 'price': '$', 'score': 96, 'description': 'World history museum'},
                {'name': 'Tower of London', 'category': 'Historical', 'rating': 4.6,
                 'price': '$$$', 'score': 94, 'description': 'Historic castle and fortress'},
                {'name': 'Big Ben', 'category': 'Landmark', 'rating': 4.6,
                 'price': '$', 'score': 92, 'description': 'Iconic clock tower'},
                {'name': 'London Eye', 'category': 'Landmark', 'rating': 4.5,
                 'price': '$$$', 'score': 88, 'description': 'Giant observation wheel'},
                {'name': 'Hyde Park', 'category': 'Nature', 'rating': 4.6,
                 'price': '$', 'score': 85, 'description': 'Large royal park'},
            ],
        }
    
    def get_recommendations(self, destination: str, interests: List[str] = None,
                          budget: str = 'medium') -> List[Dict]:
        """
        Get attraction recommendations from pre-loaded database
        
        Args:
            destination: City name
            interests: List of interests (culture, food, nature, etc.)
            budget: low, medium, or high
            
        Returns:
            List of recommended attractions
        """
        # Normalize destination
        dest_lower = destination.lower()
        
        # Try to find in database
        attractions = None
        for city_key in self.attractions_db:
            if city_key in dest_lower:
                attractions = self.attractions_db[city_key].copy()
                break
        
        if not attractions:
            # City not in database, try to fetch from free APIs
            free_scorer = FreeAttractionScorer()
            attractions = free_scorer.get_popular_attractions(destination, interests)
        
        if not attractions:
            return []
        
        # Filter by budget
        budget_map = {
            'low': ['$'],
            'medium': ['$', '$$'],
            'high': ['$', '$$', '$$$', '$$$$']
        }
        allowed_prices = budget_map.get(budget, ['$', '$$'])
        filtered = [a for a in attractions if a.get('price', '$') in allowed_prices]
        
        # Filter by interests if provided
        if interests:
            scored = []
            for attr in filtered:
                match_score = 0
                category_lower = attr.get('category', '').lower()
                for interest in interests:
                    if interest.lower() in category_lower:
                        match_score += 30
                
                attr['match_score'] = attr.get('score', 50) + match_score
                scored.append(attr)
            
            scored.sort(key=lambda x: x.get('match_score', 0), reverse=True)
            return scored[:10]
        
        return filtered[:10]


# Main interface - use this in your app
def get_attraction_recommendations(destination: str, 
                                  interests: List[str] = None,
                                  budget: str = 'medium',
                                  use_live_data: bool = True) -> List[Dict]:
    """
    Get attraction recommendations (100% FREE)
    
    Args:
        destination: City or location
        interests: List of interests like ['culture', 'food', 'nature']
        budget: 'low', 'medium', or 'high'
        use_live_data: If True, fetch from APIs; if False, use cached data only
        
    Returns:
        List of attractions with ratings and info
    """
    if use_live_data:
        # Try free APIs first
        scorer = FreeAttractionScorer()
        attractions = scorer.get_popular_attractions(destination, interests)
        
        if attractions:
            return attractions
    
    # Fallback to pre-loaded data
    recommender = SimpleAttractionRecommender()
    return recommender.get_recommendations(destination, interests, budget)


if __name__ == "__main__":
    # Test the system
    print("="*60)
    print("Testing Free Attraction Recommendation System")
    print("="*60)
    
    # Test with Tokyo
    print("\n📍 Testing Tokyo attractions...")
    attractions = get_attraction_recommendations(
        destination="Tokyo",
        interests=['culture', 'food'],
        budget='medium'
    )
    
    if attractions:
        print(f"\n✅ Found {len(attractions)} attractions:")
        for i, attr in enumerate(attractions[:5], 1):
            print(f"\n{i}. {attr['name']}")
            print(f"   Category: {attr.get('category', 'N/A')}")
            print(f"   Rating: {attr.get('rating', 'N/A')}/5")
            print(f"   Price: {attr.get('price', 'N/A')}")
            print(f"   Score: {attr.get('score', 'N/A')}")
            if attr.get('description'):
                print(f"   Info: {attr['description'][:80]}...")
    else:
        print("❌ No attractions found")
    
    print("\n" + "="*60)
    print("✅ 100% FREE - No API keys required!")
    print("="*60)
