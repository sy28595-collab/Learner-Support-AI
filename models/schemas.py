from pydantic import BaseModel, Field
from typing import Literal


# 1. Individual Message
class Message(BaseModel):
    sender: Literal["learner", "agent"]
    message: str = Field(min_length=1)


# 2. Expected Summary
class ExpectedSummary(BaseModel):
    issue: str
    steps_tried: list[str]
    current_status: str
    unresolved_questions: list[str]
    next_action: str


# 3. Complete Conversation
class Conversation(BaseModel):
    thread_id: str
    learner_id: str
    created_at: str
    messages: list[Message] = Field(min_length=1)
    expected_summary: ExpectedSummary

class HandoverSummary(BaseModel):
    issue: str
    steps_tried: list[str]
    current_status: str
    unresolved_questions: list[str]
    next_action: str