from fastapi import FastAPI, HTTPException, Cookie, Body
from fastapi.responses import JSONResponse, RedirectResponse
from models import UserCreate, UserLogin, UserResponse, ChatMessage
from auth import create_user, authenticate_user, create_session, get_current_user, logout_user
from typing import Optional, List
from chatgpt_api import chatgptAPIService

import os
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# 🌐 웹사이트 만들기
app = FastAPI(title="MovieBot")

# static front 폴더 경로 계산
FRONT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../front"))
# print("Static path:", FRONT_DIR)  # 👈 경로 확인용 출력
# mount static files
app.mount("/static", StaticFiles(directory=FRONT_DIR), name="static")

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ChatGPT 클라이언트
chatgpt_client = chatgptAPIService()

# 메모리 가짜 DB: 사용자별 채팅 기록
chat_histories = {}
# chat_histories: dict[str, list[ChatMessage]] = {}

# @app.get("/")
# async def 홈페이지():
#     """
#     🏠 홈페이지 - 웹사이트에 처음 들어왔을 때 보는 페이지
#     """
#     return {"message": "안녕하세요! MovieBot을 사용하려면 로그인하세요! 🎉"}

# --- 루트 접속 시 로그인 화면으로 리디렉트 ---
@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/static/login.html")

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

# ChatGPT 영화 질문 (단일 질문-답변)
@app.post("/chat")
async def chat(messages: List[ChatMessage] = Body(...), session_id: Optional[str] = Cookie(None)):
    
    try:
        reply = await chatgpt_client.ask_movie_info(messages)
        
        
        # assistant 응답 메시지 추가
        messages.append(ChatMessage(role="assistant", content=reply))
        # 세션 저장
        if session_id:
            chat_histories.setdefault(session_id, []).extend(messages)
        
        return {"assistant_reply": reply, "updated_messages": messages}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # user = get_current_user(session_id) if session_id else None
    # if not user:
    #     raise HTTPException(status_code=401, detail="🚫 로그인이 필요합니다")
    
    # username = user.username
    
    # # 사용자별 채팅 기록 초기화
    # if username not in chat_histories:
    #     chat_histories[username] = []
        
    # # ChatGPT API에 보낼 메시지 배열 생성
    # messages = [{"role": "system", "content": "You are MovieBot, a helpful assistant that summarizes movies and recommends similar films."}]
    
    # # 이전 대화 기록 + 이번 요청 메시지 포함
    # for msg in chat_histories[username]:
    #     role = "user" if msg.sender == "user" else "assistant"
    #     messages.append({"role": role, "content": msg.message})
    
    # print(messages)
    
    # # API 호출
    # reply = await chatgpt_client.ask_movie_info(messages)
    
    # # 대화 기록 업데이트
    # for msg in request.messages:
    #     chat_histories[username].append(ChatMessage(sender="user", message=msg.message))
    # chat_histories[username].append(ChatMessage(sender="ai", message=reply))
    
    # return {"assistant_reply": reply, "history_length": len(chat_histories[username])}
    
    # -----------------------------------------------------------------
    # 메시지 기록 변환
    # for msg in messages:
    #     chat_histories[username].append(ChatMessage(sender=msg["role"], message=msg["content"]))
    
    # # 대화 기록에 추가
    # chat_histories[username].append(ChatMessage(sender="ai", message=reply))
    
    # return {
    #     "assistant_reply": reply,
    #     "history_length": len(chat_histories[username])
    # }
    
@app.get("/chat/history")
async def chat_history(session_id: Optional[str] = Cookie(None)):
    """
    현재 로그인한 사용자의 채팅 기록 확인
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="세션 ID가 필요합니다.")
    
    return {"history": chat_histories.get(session_id, [])}
    
    # user = get_current_user(session_id) if session_id else None
    # if not user:
    #     raise HTTPException(status_code=401, detail="🚫 로그인이 필요합니다")
    
    # username = user.username
    # history = chat_histories.get(username, [])
    
    # # ChatMessage 객체를 dict 형태로 변환
    # return {"history": [msg.model_dump() for msg in history]}