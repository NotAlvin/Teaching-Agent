# type: ignore
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app_be.models.db_models import (
    Answer,
    KnowledgeGap,
    Question,
    QuizAttempt,
    Topic,
    UserProgress,
)
from app_be.models.schemas import (
    KnowledgeGapCreate,
    QuizResult,
    UserProgressCreate,
)
from app_be.services import content_service


def get_user_progress(
    db: Session, user_id: int, topic_id: Optional[int] = None
) -> List[UserProgress]:
    """Get all progress records for a user, optionally filtered by topic"""
    query = db.query(UserProgress).filter(UserProgress.user_id == user_id)

    if topic_id is not None:
        query = query.filter(UserProgress.topic_id == topic_id)

    return query.order_by(desc(UserProgress.completed_at)).all()


def create_progress(db: Session, progress: UserProgressCreate) -> UserProgress:
    """Create a new progress entry for a user"""
    db_progress = UserProgress(
        user_id=progress.user_id,
        topic_id=progress.topic_id,
        score=progress.score,
        time_spent=progress.time_spent,
        completed_at=datetime.now(),
        difficulty=progress.difficulty,
    )

    # Get topic name if not provided
    if progress.topic_name is None:
        topic = content_service.get_topic_by_id(db, progress.topic_id)
        if topic:
            db_progress.topic_name = topic.name
    else:
        db_progress.topic_name = progress.topic_name

    db.add(db_progress)
    db.commit()
    db.refresh(db_progress)
    return db_progress


def get_knowledge_gaps(db: Session, user_id: int) -> List[KnowledgeGap]:
    """Get identified knowledge gaps for a user"""
    return (
        db.query(KnowledgeGap)
        .filter(KnowledgeGap.user_id == user_id)
        .order_by(KnowledgeGap.confidence_level)  # Sort by lowest confidence first
        .all()
    )


def create_knowledge_gap(db: Session, gap: KnowledgeGapCreate) -> KnowledgeGap:
    """Record a new knowledge gap for a user"""
    db_gap = KnowledgeGap(
        user_id=gap.user_id,
        topic_id=gap.topic_id,
        confidence_level=gap.confidence_level,
        meta_data=gap.meta_data,
        identified_at=datetime.now(),
    )

    db.add(db_gap)
    db.commit()
    db.refresh(db_gap)
    return db_gap


def get_quiz_attempts(
    db: Session, user_id: int, topic_id: Optional[int] = None
) -> List[QuizAttempt]:
    """Get quiz attempts for a user, optionally filtered by topic"""
    query = db.query(QuizAttempt).filter(QuizAttempt.user_id == user_id)

    if topic_id is not None:
        # Join with Answer and Question to filter by topic_id
        query = (
            query.join(Answer, QuizAttempt.id == Answer.quiz_attempt_id)
            .join(Question, Answer.question_id == Question.id)
            .filter(Question.topic_id == topic_id)
            .distinct()
        )

    return query.order_by(desc(QuizAttempt.started_at)).all()


def get_quiz_result(db: Session, attempt_id: int) -> Optional[QuizResult]:
    """Get detailed results for a specific quiz attempt"""
    # Get the quiz attempt with answers
    quiz_attempt = (
        db.query(QuizAttempt)
        .options(joinedload(QuizAttempt.answers).joinedload(Answer.question))
        .options(joinedload(QuizAttempt.answers).joinedload(Answer.selected_answer))
        .filter(QuizAttempt.id == attempt_id)
        .first()
    )

    if quiz_attempt is None:
        return None

    # Convert to schema
    quiz_attempt_schema = QuizAttempt.from_orm(quiz_attempt)

    # Identify knowledge gaps from this quiz
    topic_ids = set()
    knowledge_gaps = []

    for answer in quiz_attempt.answers:
        if not answer.is_correct:
            topic_id = answer.question.topic_id
            topic_ids.add(topic_id)

            # Get topic info
            topic = content_service.get_topic_by_id(db, topic_id)

            knowledge_gaps.append(
                {
                    "topic_id": topic_id,
                    "topic_name": topic.name if topic else "Unknown",
                    "question_id": answer.question_id,
                    "question_text": answer.question.text,
                    "correct_answer": get_correct_answer_text(db, answer.question_id),
                }
            )

    # Generate recommendations based on knowledge gaps
    recommendations = []
    for topic_id in topic_ids:
        topic = content_service.get_topic_by_id(db, topic_id)
        if topic:
            # Find related content for review
            contents = content_service.get_content_for_topic(db, topic_id)

            recommendation = {
                "topic_id": topic_id,
                "topic_name": topic.name,
                "recommendation_type": "review",
                "content_ids": [content.id for content in contents],
                "content_titles": [content.title for content in contents],
            }
            recommendations.append(recommendation)

    return QuizResult(
        quiz_attempt=quiz_attempt_schema,
        knowledge_gaps=knowledge_gaps,
        recommendations=recommendations,
    )


def get_curriculum_summary(db: Session, user_id: int) -> Dict[str, Any]:
    """Get overall curriculum progress statistics for a user"""
    # Get all chapters and topics
    chapters = content_service.get_all_chapters(db, with_topics=True)

    # Get user progress by topic
    progress_entries = get_user_progress(db, user_id)

    # Map topics to progress
    topic_progress = {}
    for entry in progress_entries:
        if (
            entry.topic_id not in topic_progress
            or entry.completed_at > topic_progress[entry.topic_id]["completed_at"]
        ):
            topic_progress[entry.topic_id] = {
                "score": entry.score,
                "completed_at": entry.completed_at,
            }

    # Organize by chapter
    results = {"overall_progress": 0.0, "chapters": []}

    total_topics = 0
    completed_topics = 0

    for chapter in chapters:
        chapter_info = {
            "chapter_id": chapter.id,
            "chapter_title": chapter.title,
            "progress": 0.0,
            "topics": [],
        }

        chapter_topics = 0
        chapter_completed = 0

        for topic in chapter.topics:
            progress_info = topic_progress.get(topic.topic_id, None)
            is_completed = progress_info is not None and progress_info["score"] >= 0.7

            topic_info = {
                "topic_id": topic.topic_id,
                "topic_name": topic.name,
                "completed": is_completed,
                "score": progress_info["score"] if progress_info else 0.0,
                "completed_at": (
                    progress_info["completed_at"] if progress_info else None
                ),
            }

            chapter_info["topics"].append(topic_info)
            chapter_topics += 1
            if is_completed:
                chapter_completed += 1

            total_topics += 1
            if is_completed:
                completed_topics += 1

        # Calculate chapter progress
        if chapter_topics > 0:
            chapter_info["progress"] = chapter_completed / chapter_topics

        results["chapters"].append(chapter_info)

    # Calculate overall progress
    if total_topics > 0:
        results["overall_progress"] = completed_topics / total_topics

    return results


def generate_recommendations(db: Session, user_id: int) -> Dict[str, Any]:
    """Generate personalized learning recommendations for a user"""
    # Get knowledge gaps
    gaps = get_knowledge_gaps(db, user_id)

    # Get progress summary
    progress_summary = get_curriculum_summary(db, user_id)

    # Find topics that need attention (low scores or not completed)
    topics_to_review = []
    next_topics = []

    for chapter in progress_summary["chapters"]:
        chapter_topics = chapter["topics"]

        # Sort topics by chapter_order
        chapter_topics.sort(
            key=lambda t: next(
                (
                    topic.chapter_order
                    for topic in content_service.get_chapter_by_id(
                        db, chapter["chapter_id"]
                    ).topics
                    if topic.topic_id == t["topic_id"]
                ),
                0,
            )
        )

        found_incomplete = False
        for topic in chapter_topics:
            if not topic["completed"]:
                if not found_incomplete:
                    next_topics.append(
                        {
                            "chapter_id": chapter["chapter_id"],
                            "chapter_title": chapter["chapter_title"],
                            "topic_id": topic["topic_id"],
                            "topic_name": topic["topic_name"],
                        }
                    )
                    found_incomplete = True
            elif topic["score"] < 0.8:  # Topics with low scores need review
                topics_to_review.append(
                    {
                        "chapter_id": chapter["chapter_id"],
                        "chapter_title": chapter["chapter_title"],
                        "topic_id": topic["topic_id"],
                        "topic_name": topic["topic_name"],
                        "score": topic["score"],
                    }
                )

    # Generate recommendations
    recommendations = {
        "next_topics": next_topics[:3],  # Top 3 next topics
        "review_topics": topics_to_review[:5],  # Top 5 topics to review
        "knowledge_gaps": [
            {
                "topic_id": gap.topic_id,
                "topic_name": db.query(Topic)
                .filter(Topic.topic_id == gap.topic_id)
                .first()
                .name,
                "confidence_level": gap.confidence_level,
            }
            for gap in gaps[:5]  # Top 5 knowledge gaps
        ],
        "learning_path": generate_learning_path(db, user_id, progress_summary),
    }

    return recommendations


def generate_learning_path(
    db: Session, user_id: int, progress_summary: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate a personalized learning path based on user progress"""
    learning_path = []

    # Get all chapters with topics sorted by order
    chapters = content_service.get_all_chapters(db, with_topics=True)

    for chapter in chapters:
        # Sort topics by order
        topics = sorted(chapter.topics, key=lambda t: t.chapter_order)

        for topic in topics:
            # Find if the topic is completed based on progress_summary
            topic_progress = next(
                (
                    t
                    for c in progress_summary["chapters"]
                    for t in c["topics"]
                    if t["topic_id"] == topic.topic_id
                ),
                {"completed": False, "score": 0.0},
            )

            topic_status = "completed" if topic_progress["completed"] else "not_started"
            if topic_progress["score"] > 0 and not topic_progress["completed"]:
                topic_status = "in_progress"

            learning_path.append(
                {
                    "chapter_id": chapter.id,
                    "chapter_title": chapter.title,
                    "topic_id": topic.topic_id,
                    "topic_name": topic.name,
                    "status": topic_status,
                    "score": topic_progress["score"],
                }
            )

    return learning_path


def get_correct_answer_text(db: Session, question_id: int) -> str:
    """Get the text of the correct answer for a question"""
    correct_answer = (
        db.query(Answer)
        .filter(Answer.question_id == question_id, Answer.is_correct is True)
        .first()
    )

    return correct_answer.text if correct_answer else "No correct answer found"
