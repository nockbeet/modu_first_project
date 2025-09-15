import hashlib
import uuid
from typing import Optional
from models import User

# 메모리에 저장하는 '가짜 데이터베이스'
users = {}              # 사용자 정보 저장소
user_sessions = {}       # 로그인 세션 저장소
next_user_id = 1        # 다음에 만들 사용자의 ID 번호

# 비밀번호를 암호화하는 함수
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# 비밀번호가 맞는지 확인하는 함수
def verify_password(input_password: str, saved_encoded_password: str) -> bool:
    # input_password: 입력한 비밀번호, saved_encoded_password: 저장되어 있는 암호화 비밀번호
    input_password_encoded = hash_password(input_password)  # 입력한 비밀번호 암호화
    return input_password_encoded == saved_encoded_password # 저장된 암호화 비밀번호와 같은지 확인

# 새 사용자를 만드는 함수
def create_user(username: str, password: str) -> dict:
    global next_user_id
    
    # 이미 같은 이름의 사용자가 있는지 확인
    if username in users:
        return {
            "success": False,
            "message": "이미 존재하는 사용자입니다."
        }
    
    # 새 사용자 정보 만들기
    new_user = User(
        id=next_user_id,
        username=username,
        hashed_password=hash_password(password)
    )
    
    # 데이터베이스에 저장
    users[username] = new_user
    next_user_id += 1
    
    return {"success": True, "user": new_user}

# 로그인 시도 함수
def authenticate_user(username: str, password: str) -> Optional[dict]:
    
    # 사용자명 확인
    if username not in users:
        return None     # 사용자명이 db에 없음
    
    # 저장된 사용자 정보 가져오기
    user = users[username]
    
    # 비밀번호 확인
    if not verify_password(password, user.hashed_password):
        return None     # 틀린 비밀번호
    
    # 모든 검증 통과 시 user 반환
    return user

# 로그인 성공 시 세션 할당해주는 함수
def create_session(username: str) -> str:
    
    session_id = str(uuid.uuid4())  # 랜덤한 세션 ID 생성
    user_sessions[session_id] = username    # 세션과 사용자 연결
    return session_id

# 세션 ID 확인 후 어떤 사용자인지 확인하는 함수
def get_current_user(session_id: str) -> Optional[dict]:
    # 세션 ID 확인
    if session_id not in user_sessions:
        return None     # 유효하지 않은 세션
    
    # 사용자명 찾기
    username = user_sessions[session_id]
    
    # 사용자 정보 반환
    return users.get(username)

# 로그아웃하는 함수
def logout_user(session_id: str):
    
    if session_id in user_sessions:
        del user_sessions[session_id]   # 세션 삭제    