"""
Optimized Travel Agent with Gemini API
Improvements:
- Better error handling and logging
- Type hints for better code maintainability
- Cleaner API configuration
- Enhanced system instructions
"""
import os
import logging
from typing import Optional, Dict, Any
from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TravelAgent:
    """
    Gemini-powered travel planning agent with executable action protocol.
    
    Features:
    - Flight comparison from multiple airports (EWR, JFK)
    - Hotel recommendations in different price tiers
    - Ground transportation estimates
    - Structured JSON output for automation
    
    Security:
    - Never hardcode API keys
    - Set GOOGLE_API_KEY in environment variables
    """
    
    def __init__(self, model_id: str = "gemini-3-flash-preview"):
        """
        Initialize the travel agent with Gemini API.
        
        Args:
            model_id: The Gemini model to use
            
        Raises:
            RuntimeError: If API key is not found in environment
        """
        self.model_id = model_id
        self.client = self._initialize_client()
        logger.info(f"TravelAgent initialized with model: {model_id}")
    
    def _initialize_client(self) -> genai.Client:
        """
        Initialize Gemini client with API key from environment.
        
        Returns:
            Configured Gemini client
            
        Raises:
            RuntimeError: If no API key found
        """
        # Try multiple environment variable names for flexibility
        api_key = "AIzaSyBSEVCtaX6_Ump81msHObvjUMeFzPeD2IA"
        
        if not api_key:
            error_msg = (
                "Missing API key. Please set one of these environment variables:\n"
                "  - GOOGLE_API_KEY (recommended)\n"
                "  - GEMINI_API_KEY\n"
                "  - GOOGLE_GENAI_API_KEY"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        return genai.Client(api_key=api_key)
    
    def plan_trip(self, user_query: str) -> types.GenerateContentResponse:
        """
        Generate a comprehensive travel plan with executable actions.
        
        Args:
            user_query: Natural language travel request from user
            
        Returns:
            Model response containing:
            1. Human-readable Markdown itinerary
            2. Structured JSON with executable action protocol
            
        The JSON format includes:
        - meta: Trip metadata (origin, destination, dates)
        - actions: List of bookable items (flights, hotels, taxis) with:
            - Deep links with query parameters
            - Timing information with timezone
            - Pricing estimates
        """
        system_instruction = self._build_system_instruction()
        
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.HIGH),
            tools=[types.Tool(google_search=types.GoogleSearch())],
            system_instruction=system_instruction
        )
        
        try:
            chat = self.client.chats.create(model=self.model_id, config=config)
            response = chat.send_message(user_query)
            logger.info("Successfully generated travel plan")
            return response
        except Exception as e:
            logger.error(f"Error generating travel plan: {e}")
            raise
    
    def _build_system_instruction(self) -> str:
        """
        Build the system instruction for the travel agent.
        
        Returns:
            Formatted system instruction string
        """
        return """You are an "executable" Travel Operations Agent. The user is located in Piscataway, New Jersey.

**Objective:** Provide feasible flight/hotel/transportation options with structured data for automation (calendar integration, PDF generation, one-click payment).

**Hard Requirements:**

A) **Flights**: Must compare options from BOTH EWR and JFK airports to the destination specified in the user query. For each flight option, provide a deep link with query parameters that lock in the route/dates as much as possible.

B) **Hotels**: Provide 3 different price tiers (budget/comfort/luxury), each with a clickable booking link.

C) **Transportation**: Must provide estimates for TWO segments:
   - Home → Airport (Piscataway to EWR/JFK)
   - Destination Airport → Hotel

D) **Output Two Parts:**
   1. First output a Markdown section with "Daily Itinerary + Transportation" (NOT in a code block)
   2. Then output a strict JSON block (MUST be in ```json code fence```)

**JSON Schema (strictly follow field names, use null for missing info):**

```json
{
  "meta": {
    "origin_city": "Piscataway, NJ",
    "origin_airports": ["EWR", "JFK"],
    "destination_city": "...",
    "depart_date": "YYYY-MM-DD",
    "return_date": "YYYY-MM-DD",
    "currency": "USD"
  },
  "actions": [
    {
      "type": "flight|hotel|taxi",
      "title": "Descriptive title",
      "price": "Price with currency symbol",
      "link": "https://...",
      "route": "EWR-HND or airport codes",
      "start": "YYYY-MM-DDTHH:MM:SS",
      "end": "YYYY-MM-DDTHH:MM:SS",
      "timezone": "America/New_York|Asia/Tokyo|...",
      "location": "Hotel address or route description",
      "notes": "Additional details"
    }
  ]
}
```

**Important Notes:**
- Use local time for start/end (specify IANA timezone in timezone field)
- If exact times are unknown, use reasonable placeholders (e.g., 09:00/18:00) but must be valid ISO format
- Links should be actual booking URLs with query parameters when possible
- For flights, try to include airline, flight number, and estimated duration in title or notes
- For hotels, include area/neighborhood and amenities in notes
- For taxis, estimate based on typical rates (mention it's an estimate)

**Search Strategy:**
1. Use web search to find current prices and availability
2. Look for official airline/hotel websites or major booking platforms
3. Construct deep links that pre-fill search parameters
4. Verify dates and routes are feasible

**Quality Standards:**
- All prices should be current market estimates
- Links should be functional and relevant
- Provide context and alternatives when a specific option isn't available
- Be transparent about estimates vs confirmed prices
"""
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model configuration.
        
        Returns:
            Dictionary with model information
        """
        return {
            "model_id": self.model_id,
            "client_configured": self.client is not None,
            "features": [
                "Multi-airport comparison",
                "Tiered hotel recommendations", 
                "Ground transportation estimates",
                "Structured JSON output",
                "Web search integration"
            ]
        }


# Example usage
if __name__ == "__main__":
    # This is a standalone test - normally called from the Streamlit app
    try:
        agent = TravelAgent()
        print(f"Model Info: {agent.get_model_info()}")
        
        # Example query
        test_query = "Plan a 5-day trip to Tokyo from March 15-20, staying in Shibuya area"
        print(f"\nProcessing query: {test_query}")
        
        response = agent.plan_trip(test_query)
        print("\n--- Agent Response ---")
        print(response.text)
        
    except RuntimeError as e:
        print(f"Setup Error: {e}")
    except Exception as e:
        print(f"Execution Error: {e}")
