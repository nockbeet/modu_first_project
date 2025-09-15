from pydantic import BaseModel
from typing import List, Dict

# 1. User 관련 모델


class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class User(BaseModel):
    id: int
    username: str
    hashed_password: str


class UserResponse(BaseModel):
    id: int
    username: str


# Chat 관련 모델
class ChatMessage(BaseModel):
    # id: int
    role: str  # "system" | "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]  # multi-turn 메시지 배열

class ChatResponse(BaseModel):
    response: str
    usage: Dict

class ChatHistory(BaseModel):
    username: int
    messages: List[ChatMessage]
