# type: ignore

from typing import Optional, Union

from sqlalchemy.orm import Session, joinedload

from app_be.models.db_models import Chapter, Content, Topic


def get_all_chapters(db: Session, with_topics: bool = True) -> list[Chapter]:
    """
    Fetch all chapters, optionally with their associated topics.
    """
    query = db.query(Chapter)
    if with_topics:
        query = query.options(joinedload(Chapter.topics))
    return query.all()


def get_chapter_by_id(
    db: Session, chapter_id: int, with_topics: bool = False
) -> Optional[Chapter]:
    """
    Fetch a single Chapter by ID, optionally with its topics.
    """
    query = db.query(Chapter).filter(Chapter.id == chapter_id)
    if with_topics:
        query = query.options(joinedload(Chapter.topics))
    return query.first()


def get_all_topics(db: Session, with_content: bool = False) -> list[Topic]:
    """
    Fetch all topics, optionally with their associated content.
    """
    query = db.query(Topic)
    if with_content:
        query = query.options(joinedload(Topic.contents))
    return query.all()


def get_topic_by_id(
    db: Session, topic_id: int, with_content: bool = False
) -> Optional[Topic]:
    """
    Fetch a single topic by ID, optionally with its content.
    """
    query = db.query(Topic).filter(Topic.id == topic_id)
    if with_content:
        query = query.options(joinedload(Topic.contents))
    return query.first()


def get_content_for_topic(db: Session, topic_id: int) -> list[Content]:
    """
    Fetch all content items for a given topic.
    """
    return db.query(Content).filter(Content.topic_id == topic_id).all()


def get_content_by_id(db: Session, content_id: int) -> Optional[Content]:
    """
    Fetch a single content item by its ID.
    """
    return db.query(Content).filter(Content.id == content_id).first()


def search_topics_and_content(
    db: Session, query: str
) -> dict[str, list[Union[Topic, Content]]]:
    """
    Search for topics and content by a keyword in their name/title/description/text.
    """
    topics = (
        db.query(Topic)
        .filter(
            (Topic.name.ilike(f"%{query}%")) | (Topic.description.ilike(f"%{query}%"))
        )
        .all()
    )

    contents = (
        db.query(Content)
        .filter(
            (Content.title.ilike(f"%{query}%"))
            | (Content.text_content.ilike(f"%{query}%"))
        )
        .all()
    )

    return {"topics": topics, "contents": contents}
