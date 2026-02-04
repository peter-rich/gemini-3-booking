import os
from google import genai
from google.genai import types

class TravelAgent:
    def __init__(self):
        # 自动从环境变量加载 GEMINI_API_KEY
        self.client = genai.Client(api_key="AIzaSyB3yK6BJU2qvxy-58KBe_YyUziWWrFaqao")
        self.model_id = "gemini-3-flash-preview"

    def plan_trip(self, user_query):
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.HIGH),
            tools=[types.Tool(google_search=types.GoogleSearch())],
            system_instruction=(
                "你是一个订票专家。你必须严格遵守以下格式回复：\n"
                "1. 首先提供详细的文字行程规划。\n"
                "2. 在最后，必须提供一个 JSON 数组（List），不能是单个对象。\n"
                "格式必须是：```json\n[\n  {\"type\": \"机票\", \"title\": \"...\", \"price\": \"...\", \"link\": \"...\"}\n]\n```\n"
                "确保 link 是包含 EWR/JFK 和 HND/NRT 参数的深度链接。"
            )
        )   
        chat = self.client.chats.create(model=self.model_id, config=config)

        # 发送请求并获取响应
        try:
            response = chat.send_message(user_query)
            return response
        except Exception as e:
            raise Exception(f"智能体执行失败: {str(e)}")

    def extract_thought_process(self, response):
        """
        可选：如果你想在 UI 里显示智能体的思考过程，可以调用这个方法。
        """
        thoughts = [part.text for part in response.candidates[0].content.parts if part.thought]
        return "\n".join(thoughts)
