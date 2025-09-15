from fastapi import FastAPI, HTTPException, Depends, Cookie
from fastapi.responses import JSONResponse
from models import UserCreate, UserLogin, UserResponse, ChatRequest, ChatResponse, ChatMessage, ChatHistory
from auth import create_user, authenticate_user, create_session, get_current_user, logout_user
from typing import Optional, List, Dict
from chatgpt_api import chatgpt_service

# 🌐 웹사이트 만들기
app = FastAPI(title="MovieBot")

# ChatGPT 클라이언트
# chatgpt_client = chatgptAPIService()

# 메모리 가짜 DB: 사용자별 채팅 기록
# chat_histories = {}
chat_histories: dict[str, list[ChatMessage]] = {}

@app.get("/")
async def 홈페이지():
    """
    🏠 홈페이지 - 웹사이트에 처음 들어왔을 때 보는 페이지
    """
    return {"message": "안녕하세요! MovieBot을 사용하려면 로그인하세요! 🎉"}

@app.post("/register")
async def 회원가입(user_data: UserCreate):
    """
    ✍️ 회원가입 처리

    사용자가 보내는 정보:
    - username: 사용자명
    - password: 비밀번호
    """

    # 1️⃣ 새로운 사용자 만들기 시도
    result = create_user(
        username=user_data.username,
        password=user_data.password
    )

    # 2️⃣ 결과 확인
    if not result["success"]:
        # 실패했을 때 (예: 이미 존재하는 사용자명)
        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    # 3️⃣ 성공했을 때 - 비밀번호 빼고 정보 반환
    user_response = UserResponse(
        id=result["user"].id,
        username=result["user"].username,
        # 비밀번호는 절대 포함하지 않음!
    )

    return {
        "message": "🎉 회원가입이 완료되었습니다!",
        "user": user_response
    }

@app.post("/login")
async def 로그인(user_data: UserLogin):
    """
    🔑 로그인 처리

    과정:
    1. 사용자명과 비밀번호 확인
    2. 맞으면 "입장권(세션)" 발급
    3. 브라우저에 "입장권" 저장
    """

    # 1️⃣ 로그인 정보 확인
    user = authenticate_user(user_data.username, user_data.password)

    if not user:
        # 로그인 실패
        raise HTTPException(
            status_code=401,
            detail="❌ 사용자명 또는 비밀번호가 올바르지 않습니다"
        )

    # 2️⃣ 로그인 성공! 세션 만들기
    session_id = create_session(user_data.username)

    # 3️⃣ 응답 만들기
    response = JSONResponse({
        "message": "🎉 로그인 성공!",
        "user": {
            "id": user.id,
            "username": user.username
        }
    })

    # 4️⃣ 브라우저에 "입장권" 저장 (쿠키)
    response.set_cookie(
        key="session_id",           # 쿠키 이름
        value=session_id,           # 세션 ID
        httponly=True,              # 보안: JavaScript로 접근 불가
        max_age=3600                # 1시간 후 만료
    )

    return response

@app.get("/me")
async def 내정보보기(session_id: Optional[str] = Cookie(None)):
    """
    👤 현재 로그인한 사용자 정보 보기

    과정:
    1. 브라우저에서 "입장권" 확인
    2. "입장권"이 유효한지 검사
    3. 유효하면 사용자 정보 반환
    """

    # 1️⃣ 입장권(세션 ID) 확인
    if not session_id:
        raise HTTPException(
            status_code=401,
            detail="🚫 로그인이 필요합니다"
        )

    # 2️⃣ 입장권이 유효한지 확인
    user = get_current_user(session_id)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="🚫 유효하지 않은 세션입니다. 다시 로그인해주세요"
        )

    # 3️⃣ 사용자 정보 반환 (비밀번호 제외)
    return UserResponse(
        id=user.id,
        username=user.username
    )

@app.post("/logout")
async def 로그아웃(session_id: Optional[str] = Cookie(None)):
    """
    🚪 로그아웃 처리

    과정:
    1. "입장권" 회수 (세션 삭제)
    2. 브라우저에서도 "입장권" 삭제
    """

    # 1️⃣ 세션 삭제 (있다면)
    if session_id:
        logout_user(session_id)

    # 2️⃣ 응답 만들기
    response = JSONResponse({"message": "👋 로그아웃되었습니다"})

    # 3️⃣ 브라우저에서 쿠키 삭제
    response.delete_cookie("session_id")

    return response

@app.get("/users")
async def 전체사용자목록():
    """
    📋 등록된 모든 사용자 목록 (테스트용)

    ⚠️ 실제 서비스에서는 관리자만 볼 수 있어야 함!
    """
    from auth import users

    return {
        "총_사용자_수": len(users),
        "사용자_목록": [
            {
                "id": user.id,
                "username": user.username
                # 비밀번호는 절대 포함 안 함!
            }
            for user in users.values()
        ]
    }

# 🚀 서버 실행 코드
# if __name__ == "__main__":
#     import uvicorn
#     print("🌐 서버를 시작합니다...")
#     print("📱 브라우저에서 http://localhost:8000 으로 접속하세요!")
#     print("📖 API 문서는 http://localhost:8000/docs 에서 확인하세요!")
#     uvicorn.run(app, host="0.0.0.0", port=8000)

# ChatGPT 영화 질문 (단일 질문-답변)
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    
    username = current_user["username"]
    
    # system 메시지 없으면 기본값 추가
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    
    if not any(msg["role"] == "system" for msg in messages):
        messages.insert(0, {
            "role": "system",
            "content": "You are MovieBot, a helpful assistant that summarizes movies and recommends similar films."
        })
    
    # ChatGPT API 호출
    response_data = await chatgpt_service.ask_movie_info(messages)
    
    ai_message = response_data["choices"][0]["message"]["content"]
    usage_info = response_data["usage"]
    
    # 사용자별 채팅 기록에 저장
    if username not in chat_histories:
        chat_histories[username] = []
    chat_histories[username].extend(request.messages)
    chat_histories[username].append(ChatMessage(role="assistant", content=ai_message))
    
    return ChatResponse(response=ai_message, usage=usage_info)
        
    
@app.get("/chat/history")
async def chat_history(current_user: dict = Depends(get_current_user)):
    """
    현재 로그인한 사용자의 채팅 기록 확인
    """
    username = current_user["username"]
    return ChatHistory(username=username, messages=chat_histories.get(username, []))