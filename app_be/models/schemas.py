from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, EmailStr


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


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None


class UserInDB(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True


class User(UserInDB):
    pass


# Chapter schemas
class ChapterBase(BaseModel):
    title: str
    description: Optional[str] = None


class ChapterCreate(ChapterBase):
    pass


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class ChapterInDB(ChapterBase):
    id: int

    class Config:
        orm_mode = True


class Chapter(ChapterInDB):
    topics: list["Topic"] = []


# Topic schemas
class TopicBase(BaseModel):
    name: str
    description: Optional[str] = ""
    chapter_order: Optional[int] = 0
    chapter_id: Optional[int] = None  # Added to reference Chapter


class TopicCreate(TopicBase):
    pass


class TopicUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    chapter_order: Optional[int] = None
    chapter_id: Optional[int] = None


class TopicInDB(TopicBase):
    topic_id: int

    class Config:
        orm_mode = True


class Topic(TopicInDB):
    contents: list["Content"] = []
    questions: list["Question"] = []
    chapter: Optional[ChapterInDB] = None  # Reference to the chapter


# Content schemas
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


class ContentInDB(ContentBase):
    topic_id: int  # Changed to match SQLAlchemy model

    class Config:
        orm_mode = True


class Content(ContentInDB):
    topic: Optional[TopicInDB] = None


# Answer schemas
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
        orm_mode = True


class Answer(AnswerInDB):
    pass


# Question schemas
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
        orm_mode = True


class Question(QuestionInDB):
    answers: list[Answer] = []
    topic: Optional[TopicInDB] = None


# UserProgress schemas
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
        orm_mode = True


class UserProgress(UserProgressInDB):
    user: Optional[User] = None
    topic: Optional[TopicInDB] = None


# Quiz schemas
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
        orm_mode = True


class QuizAttempt(QuizAttemptInDB):
    answers: list[UserAnswerResponse] = []
    user: Optional[User] = None


class QuizResult(BaseModel):
    quiz_attempt: QuizAttempt
    knowledge_gaps: list[dict[str, Any]] = []
    recommendations: list[dict[str, Any]] = []


# Knowledge gap schemas
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
        orm_mode = True


class KnowledgeGap(KnowledgeGapInDB):
    user: Optional[User] = None
    topic: Optional[TopicInDB] = None


# Update forward references
Chapter.model_rebuild()
Topic.model_rebuild()
Content.model_rebuild()
Question.model_rebuild()
