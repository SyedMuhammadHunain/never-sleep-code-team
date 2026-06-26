from typing import List
from pydantic import BaseModel


class FileToWrite(BaseModel):
    filename: str
    content: str


class AgentResponse(BaseModel):
    files_to_write: List[FileToWrite]
    clarifying_questions: List[str]
    message_to_user: str
