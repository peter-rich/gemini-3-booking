import os
from google import genai
from google.genai import types

class GeminiTravelAgent:
    def __init__(self):
        self.client = genai.Client(api_key="AIzaSyB3yK6BJU2qvxy-58KBe_YyUziWWrFaqao")
        self.model_id = "gemini-3-flash-preview"

    def chat(self, user_message, history=[]):
        # Configure Gemini 3's advanced reasoning and search grounding
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_level=types.ThinkingLevel.HIGH  # Deep planning mode
            ),
            tools=[types.Tool(google_search=types.GoogleSearch())], # Real-time web data
            temperature=1.0  # Gemini 3 is optimized for 1.0 reasoning
        )

        # Start or continue the grounded session
        chat_session = self.client.chats.create(
            model=self.model_id,
            config=config,
            history=history
        )
        
        response = chat_session.send_message(user_message)
        return response
