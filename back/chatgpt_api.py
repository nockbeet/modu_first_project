import httpx
from typing import List
from models import ChatMessage

API_URL = "https://dev.wenivops.co.kr/services/openai-api"

class chatgptAPIService:
    """
    MovieBot 전용 ChatGPT 비동기 API 클라이언트
    """
    
    def __init__(self, api_url: str = API_URL):
        self.api_url = api_url
        
    # 영화 정보 조회
    async def ask_movie_info(self, messages: List[ChatMessage]) -> str:
        """
        user_message: 사용자가 입력한 질문
        """
        # messages = [
        #     {
        #         "role": "system",
        #         "content": "You are MovieBot, a helpful assistant that summarizes movies and recommends similar films."
        #     },
        #     {
        #         "role": "user",
        #         "content": user_message
        #     }
        # ]
        
        payload = [msg.dict() for msg in messages]
        headers = {"Content-Type": "application/json"}
        
        async with httpx.AsyncClient() as client:
            # print("api_url:", self.api_url)
            # print("messages:", messages)
            # print("headers:", headers)
            response = await client.post(self.api_url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status() # HTTP 에러 시 예외 발생
            data = response.json()  # API에서 반환한 JSON 응답을 파이썬 dict로 변환
            
        return data["choices"][0]["message"]["content"]
        # return data
        
        