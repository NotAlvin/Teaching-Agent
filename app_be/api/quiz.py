# type: ignore

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app_be.database.db import get_db
from app_be.models.schemas import (
    Question,
    QuizRequest,
)
from app_be.services import content_service, llm_service

router = APIRouter()


@router.post("/quizzes/generate", response_model=list[Question])
def generate_quiz(quiz_req: QuizRequest, db: Session = Depends(get_db)):
    """Generate a quiz for a specific topic with optional difficulty level"""
    # Verify that the topic exists
    topic = content_service.get_topic_by_id(db, quiz_req.topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Get questions for the topic with optional difficulty filter
    questions = llm_service.get_questions_for_topic(
        db,
        topic_id=quiz_req.topic_id,
        difficulty=quiz_req.difficulty,
        limit=quiz_req.question_count,
    )

    # If no questions found, raise an error
    if not questions:
        raise HTTPException(
            status_code=404,
            detail=f"""
            No questions found for topic ID {quiz_req.topic_id}
            with difficulty {quiz_req.difficulty}
            """,
        )

    return questions


# @router.post("/quizzes/submit", response_model=QuizResult,
# status_code=status.HTTP_201_CREATED)
# def submit_quiz(quiz_attempt: QuizAttemptCreate, db: Session = Depends(get_db)):
#     """Submit a quiz attempt with answers"""
#     # Verify user exists
#     user = user_service.get_user(db, user_id=quiz_attempt.user_id)
#     if user is None:
#         raise HTTPException(status_code=404, detail="User not found")

#     # Create quiz attempt
#     db_quiz_attempt = QuizAttempt(
#         user_id=quiz_attempt.user_id,
#         started_at=datetime.now(),
#         completed_at=datetime.now()
#     )
#     db.add(db_quiz_attempt)
#     db.flush()  # Get the ID without committing

#     # Process each answer
#     correct_count = 0
#     total_answers = len(quiz_attempt.answers)

#     for answer_req in quiz_attempt.answers:
#         # Get the question and correct answer
#         question = content_service.get_question_by_id(db, answer_req.question_id)
#         if question is None:
#             continue

#         # Find selected answer and check if it's correct
#         selected_answer = next(
#             (a for a in question.answers if a.id == answer_req.selected_answer_id),
#             None
#         )

#         is_correct = False
#         explanation = None

#         if selected_answer:
#             is_correct = selected_answer.is_correct
#             explanation = selected_answer.explanation

#             # Create QuizAnswer record
#             db_answer = AnswerBase(
#                 quiz_attempt_id=db_quiz_attempt.id,
#                 question_id=answer_req.question_id,
#                 selected_answer_id=answer_req.selected_answer_id,
#                 is_correct=is_correct,
#                 time_taken=answer_req.time_taken
#             )
#             db.add(db_answer)

#             if is_correct:
#                 correct_count += 1

#     # Calculate score (percentage)
#     score = 0.0
#     if total_answers > 0:
#         score = correct_count / total_answers

#     # Update quiz attempt with score
#     db_quiz_
