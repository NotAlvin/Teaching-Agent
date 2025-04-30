# type: ignore

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app_be.database.db import get_db
from app_be.models.schemas import (
    UserCreate,
)
from app_be.models.schemas import UserOut as UserSchema
from app_be.models.schemas import (
    UserProgress,
    UserProgressCreate,
    UserUpdate,
)
from app_be.services import progress_service, user_service

router = APIRouter()


# User management endpoints
@router.post("/users/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = user_service.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    return user_service.create_user(db=db, user=user)


@router.get("/users/", response_model=list[UserSchema])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = user_service.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/users/{user_id}", response_model=UserSchema)
def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = user_service.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.put("/users/{user_id}", response_model=UserSchema)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = user_service.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user_service.update_user(db=db, user_id=user_id, user=user)


@router.get("/users/{user_id}/progress", response_model=list[UserProgress])
def get_user_progress(
    user_id: int, topic_id: Optional[int] = None, db: Session = Depends(get_db)
):
    """Get all progress records for a user, optionally filtered by topic"""
    user = user_service.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return progress_service.get_user_progress(db=db, user_id=user_id, topic_id=topic_id)


# User progress endpoints
@router.post(
    "/users/{user_id}/progress",
    response_model=UserProgress,
    status_code=status.HTTP_201_CREATED,
)
def record_user_progress(
    user_id: int, progress: UserProgressCreate, db: Session = Depends(get_db)
):
    """Record a new progress entry for a user"""
    user = user_service.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Ensure the user_id in the path matches the one in the request body
    if progress.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID in path must match user ID in request body",
        )

    return progress_service.create_progress(db=db, progress=progress)


@router.get("/users/{user_id}/curriculum-progress", response_model=dict)
def get_curriculum_progress(user_id: int, db: Session = Depends(get_db)):
    """Get overall curriculum progress statistics for a user"""
    user = user_service.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return progress_service.get_curriculum_summary(db=db, user_id=user_id)


# # -------- Question and Answer endpoints --------
# @router.get("/users/{user_id}/questions", response_model=List[Question])
# def get_user_questions(
#     user_id: int,
#     topic_id: Optional[int] = None,
#     difficulty: Optional[str] = None,
#     db: Session = Depends(get_db)
# ):
#     """Get questions for user filtered by topic and/or difficulty"""
#     user = user_service.get_user(db, user_id=user_id)
#     if user is None:
#         raise HTTPException(status_code=404, detail="User not found")

#     return progress_service.get_questions_for_user(
#         db=db,
#         user_id=user_id,
#         topic_id=topic_id,
#         difficulty=difficulty
#     )

# @router.post("/users/{user_id}/submit-answer", response_model=UserAnswerResponse)
# def submit_user_answer(
#     user_id: int,
#     answer: UserAnswerRequest,
#     db: Session = Depends(get_db)
# ):
#     """Submit an answer to a question and get feedback"""
#     user = user_service.get_user(db, user_id=user_id)
#     if user is None:
#         raise HTTPException(status_code=404, detail="User not found")

#     # The logic should validate the selected_answer_id,
#     # question_id match and compute correctness
#     return progress_service.evaluate_user_answer(
#         db=db,
#         user_id=user_id,
#         answer=answer
#     )

# # Knowledge Gaps endpoints
# @router.get("/users/{user_id}/knowledge-gaps", response_model=list[KnowledgeGap])
# def get_knowledge_gaps(user_id: int, db: Session = Depends(get_db)):
#     """Get identified knowledge gaps for a user"""
#     user = user_service.get_user(db, user_id=user_id)
#     if user is None:
#         raise HTTPException(status_code=404, detail="User not found")

#     return progress_service.get_knowledge_gaps(db=db, user_id=user_id)

# @router.post("/users/{user_id}/knowledge-gaps",
#               response_model=KnowledgeGap,
#               status_code=status.HTTP_201_CREATED)
# def record_knowledge_gap(
#     user_id: int,
#     gap: KnowledgeGapCreate,
#     db: Session = Depends(get_db)
# ):
#     """Record a new knowledge gap for a user"""
#     user = user_service.get_user(db, user_id=user_id)
#     if user is None:
#         raise HTTPException(status_code=404, detail="User not found")

#     # Ensure the user_id in the path matches the one in the request body
#     if gap.user_id != user_id:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="User ID in path must match user ID in request body"
#         )

#     return progress_service.create_knowledge_gap(db=db, gap=gap)

# # Quiz Attempts endpoints
# @router.get("/users/{user_id}/quiz-attempts", response_model=list[QuizAttempt])
# def get_quiz_attempts(
#     user_id: int,
#     topic_id: Optional[int] = None,
#     db: Session = Depends(get_db)
# ):
#     """Get quiz attempts for a user, optionally filtered by topic"""
#     user = user_service.get_user(db, user_id=user_id)
#     if user is None:
#         raise HTTPException(status_code=404, detail="User not found")

#     return progress_service.get_quiz_attempts(
#         db=db,
#         user_id=user_id,
#         topic_id=topic_id
#     )

# @router.get("/users/{user_id}/quiz-attempts/{attempt_id}", response_model=QuizResult)
# def get_quiz_result(
#     user_id: int,
#     attempt_id: int,
#     db: Session = Depends(get_db)
# ):
#     """Get detailed results for a specific quiz attempt"""
#     user = user_service.get_user(db, user_id=user_id)
#     if user is None:
#         raise HTTPException(status_code=404, detail="User not found")

#     result = progress_service.get_quiz_result(db=db, attempt_id=attempt_id)
#     if result is None:
#         raise HTTPException(status_code=404, detail="Quiz attempt not found")

#     # Verify that the quiz attempt belongs to the specified user
#     if result.quiz_attempt.user_id != user_id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Access denied to this quiz attempt"
#         )

#     return result

# @router.get("/users/{user_id}/recommendations", response_model=dict)
# def get_learning_recommendations(user_id: int, db: Session = Depends(get_db)):
#     """
#       Get personalized learning recommendations
#       based on user progress and knowledge gaps
#     """
#     user = user_service.get_user(db, user_id=user_id)
#     if user is None:
#         raise HTTPException(status_code=404, detail="User not found")

#     return progress_service.generate_recommendations(db=db, user_id=user_id)
