import httpx
from fastapi import HTTPException

API_URL = "https://dev.wenivops.co.kr/services/openai-api"

class chatgptAPIService:
    """
    MovieBot 전용 ChatGPT 비동기 API 클라이언트
    """
    
    def __init__(self, api_url: str = API_URL):
        self.api_url = api_url
        
    # 영화 정보 조회
    async def ask_movie_info(self, messages: list[dict]) -> str:
        """
        user_message: 사용자가 입력한 질문
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    API_URL,
                    json=messages,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException:
                raise HTTPException(status_code=408, detail="API 요청 시간이 초과되었습니다")
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=e.response.status_code, detail=f"API 오류: {e}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

chatgpt_service = chatgptAPIService()
        
        