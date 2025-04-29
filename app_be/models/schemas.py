# type: ignore

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, EmailStr


# -------- ENUMS --------
class ContentType(str, Enum):
    lesson = "lesson"
    example = "example"
    theorem = "theorem"
    definition = "definition"
    proof = "proof"


class DifficultyLevel(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class QuestionType(str, Enum):
    multiple_choice = "multiple_choice"
    open_ended = "open_ended"


# -------- USER SCHEMAS --------
class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None


class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# -------- CHAPTER SCHEMAS --------
class ChapterBase(BaseModel):
    title: str
    description: Optional[str] = None


class ChapterCreate(ChapterBase):
    pass


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class ChapterOut(ChapterBase):
    id: int

    class Config:
        from_attributes = True


# -------- TOPIC SCHEMAS --------
class TopicBase(BaseModel):
    name: str
    description: Optional[str] = ""
    chapter_order: Optional[int] = 0
    chapter_id: Optional[int] = None


class TopicCreate(TopicBase):
    pass


class TopicUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    chapter_order: Optional[int] = None
    chapter_id: Optional[int] = None


class TopicOut(TopicBase):
    id: int

    class Config:
        from_attributes = True


# -------- CONTENT SCHEMAS --------
class ContentBase(BaseModel):
    title: str
    content_type: ContentType
    text_content: str
    latex_content: Optional[str] = None
    topic_id: int
    chapter_order: Optional[int] = 0


class ContentCreate(ContentBase):
    pass


class ContentUpdate(BaseModel):
    title: Optional[str] = None
    content_type: Optional[ContentType] = None
    text_content: Optional[str] = None
    latex_content: Optional[str] = None
    topic_id: Optional[int] = None
    chapter_order: Optional[int] = None


class ContentOut(ContentBase):
    id: int

    class Config:
        from_attributes = True


# -------- ANSWER SCHEMAS --------
class AnswerBase(BaseModel):
    text: str
    latex_content: Optional[str] = None
    is_correct: bool = False
    explanation: Optional[str] = None


class AnswerCreate(AnswerBase):
    pass


class AnswerUpdate(BaseModel):
    text: Optional[str] = None
    latex_content: Optional[str] = None
    is_correct: Optional[bool] = None
    explanation: Optional[str] = None


class AnswerInDB(AnswerBase):
    id: int
    question_id: int

    class Config:
        from_attributes = True


class Answer(AnswerInDB):
    pass


# -------- QUESTION SCHEMAS --------
class QuestionBase(BaseModel):
    text: str
    latex_content: Optional[str] = None
    question_type: QuestionType
    difficulty: DifficultyLevel
    topic_id: int


class QuestionCreate(QuestionBase):
    answers: list[AnswerCreate]


class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    latex_content: Optional[str] = None
    question_type: Optional[QuestionType] = None
    difficulty: Optional[DifficultyLevel] = None
    topic_id: Optional[int] = None


class QuestionInDB(QuestionBase):
    id: int

    class Config:
        from_attributes = True


class Question(QuestionInDB):
    answers: list[Answer] = []
    topic: Optional[TopicOut] = None


# -------- TOPIC FULL VIEW --------
class Topic(TopicOut):
    contents: list[ContentOut] = []
    questions: list[Question] = []
    chapter: Optional[ChapterOut] = None


# -------- CHAPTER FULL VIEW --------
class Chapter(ChapterOut):
    topics: list[Topic] = []


# -------- USER PROGRESS SCHEMAS --------
class UserProgressBase(BaseModel):
    user_id: int
    topic_id: int
    score: float
    time_spent: Optional[int] = None
    topic_name: Optional[str] = None
    difficulty: Optional[str] = None


class UserProgressCreate(UserProgressBase):
    pass


class UserProgressInDB(UserProgressBase):
    id: int
    completed_at: datetime

    class Config:
        from_attributes = True


class UserProgress(UserProgressInDB):
    user: Optional[UserOut] = None
    topic: Optional[TopicOut] = None


# -------- QUIZ SCHEMAS --------
class UserAnswerRequest(BaseModel):
    question_id: int
    selected_answer_id: int
    time_taken: Optional[int] = None


class UserAnswerResponse(UserAnswerRequest):
    is_correct: bool
    explanation: Optional[str] = None


class QuizRequest(BaseModel):
    topic_id: int
    difficulty: Optional[DifficultyLevel] = None
    question_count: Optional[int] = 5


class QuizAttemptCreate(BaseModel):
    user_id: int
    answers: list[UserAnswerRequest]


class QuizAttemptInDB(BaseModel):
    id: int
    user_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    score: Optional[float] = None

    class Config:
        from_attributes = True


class QuizAttempt(QuizAttemptInDB):
    answers: list[UserAnswerResponse] = []
    user: Optional[UserOut] = None


class QuizResult(BaseModel):
    quiz_attempt: QuizAttempt
    knowledge_gaps: list[dict[str, Any]] = []
    recommendations: list[dict[str, Any]] = []


# -------- KNOWLEDGE GAP SCHEMAS --------
class KnowledgeGapBase(BaseModel):
    user_id: int
    topic_id: int
    confidence_level: float
    meta_data: Optional[dict[str, Any]] = None


class KnowledgeGapCreate(KnowledgeGapBase):
    pass


class KnowledgeGapInDB(KnowledgeGapBase):
    id: int
    identified_at: datetime

    class Config:
        from_attributes = True


class KnowledgeGap(KnowledgeGapInDB):
    user: Optional[UserOut] = None
    topic: Optional[TopicOut] = None


# -------- FINAL: RESOLVE FORWARD REFS --------
Chapter.model_rebuild()
Topic.model_rebuild()
ContentOut.model_rebuild()
Question.model_rebuild()
