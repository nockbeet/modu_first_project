from pydantic import BaseModel
from typing import List
# from datetime import datetime

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
    role: str  # "system" | "user" | "assistant"
    content: str

# class ChatHistory(BaseModel):
#     user_id: int
#     messages: List[ChatMessage]
