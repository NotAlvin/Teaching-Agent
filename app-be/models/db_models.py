# type: ignore

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)

    # Relationships
    topics = relationship("Topic", back_populates="chapter")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, default="")
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True)
    chapter_order = Column(Integer, default=0)

    # Relationships
    chapter = relationship("Chapter", back_populates="topics")
    contents = relationship("Content", back_populates="topic")
    questions = relationship("Question", back_populates="topic")


class Content(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content_type = Column(
        Enum("lesson", "example", "theorem", "definition", "proof", name="content_type")
    )
    text_content = Column(Text)
    latex_content = Column(Text, nullable=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), index=True)
    order_index = Column(Integer, default=0)

    # Relationships
    topic = relationship("Topic", back_populates="contents")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    latex_content = Column(Text, nullable=True)
    question_type = Column(Enum("multiple_choice", "open_ended", name="question_type"))
    difficulty = Column(Enum("easy", "medium", "hard", name="difficulty"))
    topic_id = Column(Integer, ForeignKey("topics.id"))

    # Relationships
    topic = relationship("Topic", back_populates="questions")
    answers = relationship("Answer", back_populates="question")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    latex_content = Column(Text, nullable=True)
    is_correct = Column(Boolean, default=False)
    explanation = Column(Text, nullable=True)
    question_id = Column(Integer, ForeignKey("questions.id"))

    # Relationships
    question = relationship("Question", back_populates="answers")


class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"))
    score = Column(Float)
    time_spent = Column(Integer)  # in seconds
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    topic_name = Column(String)  # Denormalized for easier querying
    difficulty = Column(String)

    # Relationships
    user = relationship("User")
    topic = relationship("Topic")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    score = Column(Float, nullable=True)

    # Relationships
    user = relationship("User")
    answers = relationship("UserAnswer", back_populates="quiz_attempt")


class UserAnswer(Base):
    __tablename__ = "user_answers"

    id = Column(Integer, primary_key=True, index=True)
    quiz_attempt_id = Column(Integer, ForeignKey("quiz_attempts.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    selected_answer_id = Column(Integer, ForeignKey("answers.id"))
    is_correct = Column(Boolean)
    time_taken = Column(Integer, nullable=True)  # in seconds

    # Relationships
    quiz_attempt = relationship("QuizAttempt", back_populates="answers")
    question = relationship("Question")
    selected_answer = relationship("Answer")


class KnowledgeGap(Base):
    __tablename__ = "knowledge_gaps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"))
    identified_at = Column(DateTime(timezone=True), server_default=func.now())
    confidence_level = Column(Float)  # 0-1 scale
    meta_data = Column(JSON, nullable=True)  # Additional gap details

    # Relationships
    user = relationship("User")
    topic = relationship("Topic")
