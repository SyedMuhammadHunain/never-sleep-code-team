from typing import List

from pydantic import BaseModel, Field


class FileToWrite(BaseModel):
    filename: str
    content: str


class AgentResponse(BaseModel):
    files_to_write: List[FileToWrite] = Field(default_factory=list)
    clarifying_questions: List[str] = Field(default_factory=list)
    message_to_user: str = ""
    has_more_tasks: bool = Field(
        default=True,
        description="Set to False only when all tasks in the implementation plan are fully complete.",
    )
